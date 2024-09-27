import json
import os
import os.path
import re
import time
import random
import logging
import pymysql
import threading
from requests.adapters import HTTPAdapter, Retry
from requests_toolbelt.adapters import source
from bs4 import BeautifulSoup
import requests

connection = pymysql.connect(
    host='127.0.0.1',
    user='user',
    password='password',
    database='urls'
)

fetcher_urls = [
  "http://127.0.0.1:8080/"
]

srcs = [""] # List of network addresses, e.g. ["10.0.0.1", "10.0.0.2", ... ] or ["2603:c020:8010:977e:886c:1528:26c2:d3d7", ... 
random.shuffle(srcs)

letters = "abcdefghijkmnopqrstuvyxwz" #missing 'l'

def remove_ip(src):
  if src in srcs:
    srcs.remove(src)
    time.sleep(300) #1800
    srcs.append(src)

def t_remove_ip(src):
  manage_thread = threading.Thread(target=remove_ip, args=(src,))

  manage_thread.start()

def get_ip():
  while len(srcs) == 0:
    print("Zero addresses to use!")
    time.sleep(1800)

  ip = random.choice(srcs)
  return ip

def get_page(url):
  while True:
    session = requests.Session()
    src_ip = get_ip()

    session.verify = True
    src_ip_object = source.SourceAddressAdapter(src_ip) #, max_retries=1)
    session.mount('http://', src_ip_object)
    try:
      resp = session.get(url, timeout=45) # TODO: Error if this fails, and handle the case correctly by get_page callers.
      return resp
    except Exception as e:
      print(f"Removing {src_ip} from the pool temporarily due to {e}")
      session.close()
      t_remove_ip(src_ip)


def get_all_categories():
  resp = get_page('http://snapshot.debian.org')
  return re.findall(r'binary/\?cat=(['+letters+']+)', resp.text)

def process_all_versions(data):
  l_data = len(data)
  l_data_completed = l_data

  for result in data:
    ret_val = True
    name = result["name"]
    binary_version = result["binary_version"]

    binfile_url = f"http://snapshot.debian.org/mr/binary/{name}/{binary_version}/binfiles?fileinfo=1"
    with connection.cursor() as cursor:
      cursor.execute('SELECT url from urls WHERE url = %s', (binfile_url))
      result = cursor.fetchone()
      if result:
        continue

    with connection.cursor() as cursor:
      cursor.execute('SELECT url from bad_urls WHERE url = %s', (binfile_url))
      result = cursor.fetchone()
      if result:
        l_data_completed -= 1
        continue

    response = get_page(binfile_url)
    try:
      data = json.loads(response.content)
    except ValueError as e:
      print(f"Non-JSON value retrieved: {response.content} from {binfile_url}: {e}.")
      l_data_completed -= 1
      continue

    fileinfo = data["fileinfo"]

    urls = []

    for file in fileinfo:
      for file_data in fileinfo[file]:
        first_seen = file_data["first_seen"]
        path = file_data["path"]
        file_name = file_data["name"]
        archive_name = file_data["archive_name"]
        url = f"/archive/{archive_name}/{first_seen}{path}/{file_name}"
        urls.append(url)

    ret_val = get_hash(urls)

#    print(f"Finished handling package '{name}' version '{binary_version}': {ret_val}")
    with connection.cursor() as cursor:
      if ret_val:
        cursor.execute('INSERT INTO urls (url) VALUES (%s)', (binfile_url))
      else:
        cursor.execute('INSERT INTO bad_urls (url) VALUES (%s)', (binfile_url))
        l_data_completed -= 1
      connection.commit()

  return l_data - l_data_completed


def process_category(category):
  print(f"Beginning to process the category '{category}'")

  url = f"http://snapshot.debian.org/binary/?cat={category}"

  resp = get_page(url)
  soup = BeautifulSoup(resp.content, "html.parser")

  p_tag = soup.find("p")
  packages = p_tag.find_all("a")

  if not packages:
    print(f"Couldn't retrieve any packages for category '{category}': {resp}")
    return

  i = 0
  l_packages = len(packages)
  for package in packages:
    i += 1

    package_name = package.text
    package_url = f"http://snapshot.debian.org/mr/binary/{package_name}/"

    with connection.cursor() as cursor:
      cursor.execute('SELECT package from packages WHERE package = %s', (package_url))
      result = cursor.fetchone()
    if result:
      continue

    # Get a list of binaries for a package.
    resp = get_page(package_url)
    data = json.loads(resp.content)

    if "result" in data:
      print(f"[{i}/{l_packages}] Starting to handle package '{package.text}': {len(data['result'])}")
      processed_all_versions = process_all_versions(data["result"])
      if processed_all_versions == 0:
        with connection.cursor() as cursor:
          cursor.execute('INSERT INTO packages (package) VALUES (%s)', (package_url))
          connection.commit()
        print(f"\033[32m[{i}/{l_packages}] Finished handling package '{package.text}'\033[0m")  # Green color
      else:
        print(f"\033[31m[{i}/{l_packages}] Finished handling package '{package.text}': {processed_all_versions} unprocessed.\033[0m")  # Red color

def prepare_save_path(url):
  parts = url.split("/")
  parts.pop(3)  # Remove the third element
  updated_url = "/".join(parts)
  return f"./results{updated_url}.md5sums"


def get_hash(urls):
  for url in urls.copy():
    save_location = prepare_save_path(url)
    if os.path.isfile(save_location):
      urls.remove(url)

  if len(urls) == 0:
    return True


  data = json.dumps({"urls": urls})
  fetcher = random.choice(fetcher_urls)

  try:
    s = requests.Session()
    retries = Retry(read=3, total=3, backoff_factor=15)
    s.mount('http://', HTTPAdapter(max_retries=retries))
    response = s.post(fetcher, headers={'Content-Type': 'application/json'}, data=data, timeout=180)
  except Exception as e:
    print(f"Something went extremely wrong (probably timeout) for {urls} using {fetcher}: {e}.")
    return False

  if response.status_code != 200:
    print(f"Something went really wrong for {urls} using {fetcher}: {response.content}.")
    return False

  data = response.json()

  written = 0

  for url, md5sums_data in data.items():
    if md5sums_data == 'DEB_ERROR':
      continue
    if md5sums_data == 'CONTROL_ERROR':
      continue
    if md5sums_data == 'TAR_ERROR':
      continue

    save_location = prepare_save_path(url)
    os.makedirs(os.path.dirname(save_location), exist_ok=True)
    with open(save_location, 'wb') as f:
      written += 1
      if md5sums_data == 'TAR_EMPTY':
        continue
      else:
        f.write(md5sums_data.encode('utf-8'))

  print(f"\t\t\t{written}/{len(urls)} retrieved")

  return len(urls) == written

def run_concurrent_get_hash():
  categories = get_all_categories()

  random.shuffle(categories)
  for category in categories:
    process_category(category)


for _ in letters:
  try:
    run_concurrent_get_hash()

  except Exception as e:
    print(f"An error occurred: {str(e)}")
    print("Sleeping for 15 minutes...")
    connection.ping(reconnect=True)
    time.sleep(900)
