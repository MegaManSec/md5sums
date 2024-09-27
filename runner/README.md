Startup/setup:

1. Create a MySQL database with the following:

```
CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    url VARCHAR(65535) NOT NULL
);

CREATE TABLE bad_urls (
    id SERIAL PRIMARY KEY,
    url VARCHAR(65535) NOT NULL
);

CREATE TABLE packages (
    id SERIAL PRIMARY KEY,
    package VARCHAR(65535) NOT NULL
);
```

2. Set the database details in `connection` variable in runner.py

3. Set the runner URL(s) in `fetcher` variable in `runner.py` corresponding to the address of the runner

4. Set a list of source network addresses in `srcs` variable in `runner.py` which can be used

5. Set the `letters` to all of the characters to parse for a category (a-z,A-Z,0-9,+- is good)

6. Make sure `fetcher.py` is running

7. `python3 runner.py`

---

You can run many instances of `runner.py` concurrently.

Due to a bug/vulnerability in snapshot.debian.org's rate-limiting, the speed and accuracy of results will be drastically increased by adding the following to `/etc/hosts`:

```
2001:630:206:4000:1a1a:0:c13e:ca1a	snapshot.debian.org
```
