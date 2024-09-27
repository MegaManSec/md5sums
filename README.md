# Debian Snapshot / Archive .deb Crawler

The purpose of this project was to download every `md5sums` file from the control archive of every officially published Debian package in history.

[https://snapshot.debian.org/](https://snapshot.debian.org/) can be used to retrieve every package in the history of the Debian package archive.

These packages can be partially downloaded to retrieve the control archive, which contains the `md5sums` file for the respective package.

I wrote two Python scripts:

1. [runner](/runner), which handles retrieving a _list_ of URLs to be downloaded from the Debian snapshot
2. [fetcher](/fetcher), which actually does the partial downloading of the `.deb` files and extracts the `md5sums` data for each file.

Individual READMEs are available for both of the scripts.

---

In the course of making this, I discovered two interesting things:

1. A vulnerability exists in Debian's snapshot archive which allows to bypass their rate-limiting,
2. It is possible to download only the first 132-bytes of a `.deb` file in order to determine the name and the size of the control archive which contains the `md5sums` file.

---

I also discovered some interesting packages which indicate that:

1. Invalid tar archives have been included in Debian's `.deb` packages before, which I could not decompress.
2. The `snapshot.debian.org` archive has some 'holes' in it, where the `.deb` files are either missing some bytes or are completely missing (despite being reported as being available).

---

More information about this can be found on my blog post: [https://joshua.hu/crawling-snapshot-debian-org-every-debian-package-rate-limit-bypass](https://joshua.hu/crawling-snapshot-debian-org-every-debian-package-rate-limit-bypass).

---

Due to a bug/vulnerability in snapshot.debian.org's rate-limiting, the speed and accuracy of results will be drastically increased by adding the following to `/etc/hosts`:

```
2001:630:206:4000:1a1a:0:c13e:ca1a      snapshot.debian.org
```
