import os
import os.path
import time
import io
import tarfile
import random
from flask import Flask, request, jsonify
import requests
from requests_toolbelt.adapters import source
import zstandard as zstd
import threading
import logging

srcs = []  # List of network addresses, e.g. ["10.0.0.1", "10.0.0.2", ... ] or ["2603:c020:8010:977e:886c:1528:26c2:d3d7", ... ]
sessions = []

for i in range(len(srcs)):
    sessions.append({
        'session': requests.Session(),
        'last_refresh_time': time.time(),
        'interface': srcs[i],
        'busy': False,
    })

total_requests = 0

session_lock = threading.Lock()

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route("/", methods=['POST'])
def get_md5sums_files():
    urls = request.get_json()["urls"]
    BASE_URL = "http://snapshot.debian.org"

    results = {}
    for url in urls:
        start = time.time()

        current_interface = decide_interface()
        deb_data = download_deb_file(sessions[current_interface]['session'], f"{BASE_URL}/{url}")
        sessions[current_interface]['busy'] = False

        end = time.time()

        if not deb_data:
            results[url] = "DEB_ERROR"
            print(f"{end-start} for {url}: {results[url]}")
            continue

        tar_data = extract_control_tar(deb_data)
        if not tar_data:
            results[url] = "CONTROL_ERROR"
            print(f"{end-start} for {url}: {results[url]}")
            continue

        tar_data.seek(0)

        md5sums_data = extract_md5sums_file(tar_data)
        if md5sums_data.decode("utf-8") in ("TAR_EMPTY", "TAR_ERROR"):
            print(f"{end-start} for {url}: {md5sums_data.decode('utf-8')}")
        else:
            print(f"{end-start} for {url}")
        results[url] = md5sums_data.decode("utf-8")

    return jsonify(results)

def decide_interface():
    global total_requests

    current_interface = total_requests % len(sessions)

    random.shuffle(sessions)

    # Use lock to prevent race condition when checking 'busy' and when starting to use a session
    with session_lock:
        refresh_session_if_needed(sessions[current_interface])

        while sessions[current_interface]['busy']:
            current_interface = (current_interface + 1) % len(sessions)
            refresh_session_if_needed(sessions[current_interface])

        total_requests += 1
        sessions[current_interface]['busy'] = True

    return current_interface

def refresh_session_if_needed(session_data):
    interface = session_data['interface']
    session = session_data['session']
    current_time = time.time()

    if current_time - session_data['last_refresh_time'] >= 600:
        session.close()
        session = requests.Session()
        session_data['busy'] = False
        session_data['last_refresh_time'] = time.time()

    session.verify = True

    src_ip = source.SourceAddressAdapter(interface, max_retries=1)
    session.mount('http://', src_ip)

def parse_string(s):
    e = len(s) - 1
    while e != -1 and s[e] == ' ':
        e = e - 1
    return s[0:e + 1]

def parse_num(s):
    return int(s)

def parse_oct(s):
    return int(s, 8)

def parse_header(s):
    return {
        'name': parse_string(s[0:16]),
        'date': parse_num(s[16:28]),
        'uid': parse_oct(s[28:34]),
        'gid': parse_oct(s[34:40]),
        'mode': parse_oct(s[40:48]),
        'size': parse_num(s[48:58]),
        'fmag': s[58:60]
    }

def download_deb_file(s, url):
    try:
        s.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/116.0",
            "Range": "bytes=%u-%u" % (72, 129),
        }
        response = s.get(url, timeout=15)

        if response.status_code not in [200, 206]:
            return False

        start = 132
        parsed_header = parse_header(response.content)
        end = parsed_header['size'] + start

        s.headers = {
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/116.0",
            "Range": "bytes=%u-%u" % (start, end),
        }
        response = s.get(url, timeout=45, allow_redirects=False)

        if response.status_code not in [200, 206]:
            return False

        return [parsed_header['name'].strip(), response.content]
    except Exception:
        return False

def extract_control_tar(deb_data):
    tar_data = deb_data[1]
    if deb_data[0] == b'control.tar.zst':  # tarfile does not support zstd, so unpack manually. not necessary for control.tar.gz or control.tar.xz
        dctx = zstd.ZstdDecompressor()
        stream_reader = dctx.stream_reader(deb_data[1])
        tar_data = stream_reader.read()
        stream_reader.close()

    if tar_data:
        tar_data = io.BytesIO(tar_data)

    return tar_data

def extract_md5sums_file(tar_data):
    md5sums_data = "TAR_ERROR".encode()
    try:
        with tarfile.open(fileobj=tar_data, mode='r:*') as tar:
            md5sums_data = "TAR_EMPTY".encode()
            for member in tar.getmembers():
                if member.name.endswith('md5sums'):
                    md5sums_data = tar.extractfile(member).read()
                    break
    except tarfile.TarError:
        pass

    return md5sums_data

if __name__ == "__main__":
    if len(srcs) == 0:
        print("Set a list of interface addresses in the script as the 'srcs' variable.")
        exit(1)

    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), threaded=True)
