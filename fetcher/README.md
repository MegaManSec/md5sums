Setup/startup:

1. Set the `srcs` list at the top of the script to a list of valid addresses for the system

```bash
pip install -r requirements.txt
python3 fetcher.py
```

---

Example of calling the script with `curl`:

```
$ curl localhost:8080 \
	-H 'Content-Type: application/json' \
	--data \
	'{"urls": [
		"archive/debian/20240901T024950Z/pool/main/libd/libdrm/libdrm-amdgpu1_2.4.122-1_amd64.deb",
		"archive/debian/20120202T040408Z/pool/main/3/3dchess/3dchess_0.8.1-15_amd64.deb"
	]}'

{
  "archive/debian/20120202T040408Z/pool/main/3/3dchess/3dchess_0.8.1-15_amd64.deb": "6650875161c1ca7bd7dd7f6e48c4bcac  usr/games/3Dc\nf94894e3a6feeabe17b5e6ad71d6f655  usr/share/menu/3dchess\n2e78411b31ae44022e238059fad5b139  usr/share/doc/3dchess/3Dc-rules.html\nfcdc75f3d0d3802137d034028b1009ea  usr/share/doc/3dchess/changelog.gz\ned7616c853e841a8f6ee970dabd02f30  usr/share/doc/3dchess/README\n8e903954d757702f8790d9c7a529dc6d  usr/share/doc/3dchess/copyright\na299ce7452ccd2837ef5c0a14f64466b  usr/share/doc/3dchess/TODO\n0cad7237e93c3c47bf96bb03ee8c23ac  usr/share/doc/3dchess/changelog.Debian.gz\n2750302d8c9cd9ef54d01956570289c0  usr/share/doc/3dchess/ACKNOWLEDGEMENTS\n58c3a90ac129f3283aa510b124a6bed4  usr/share/man/man6/3Dc.6.gz\n90b2d22e8cbddee213f9f5918d767295  usr/share/applications/3dchess.desktop\n",
  "archive/debian/20240901T024950Z/pool/main/libd/libdrm/libdrm-amdgpu1_2.4.122-1_amd64.deb": "cd58a035a87dd88e0f5a1ae71e2cf87c  usr/lib/x86_64-linux-gnu/libdrm_amdgpu.so.1.0.0\n2b0a00e80612b08ba6ccc543eca9fd8f  usr/share/doc/libdrm-amdgpu1/changelog.Debian.gz\nf877b409d7f2dfcf6e3e2a139d19798c  usr/share/doc/libdrm-amdgpu1/copyright\n"
}
```

Errors are also retained in the response:

$ curl localhost:8080 \
	-H 'Content-Type: application/json' \
	--data \
	'{"urls": [
                "archive/debian/20240901T024950Z/pool/main/libd/libdrm/libdrm-amdgpu1_2.4.122-1_amd64.deb",
                "archive/debian/20120202T040408Z/pool/main/3/3dchess/3dchess_0.8.1-15_amd64.deb"
        ]}'

{
		"archive/debian/20120202T040408Z/pool/main/3/3dchess/3dchess_0.8.1-15_amd64.deb": "DEB_ERROR",
		"archive/debian/20240901T024950Z/pool/main/libd/libdrm/libdrm-amdgpu1_2.4.122-1_amd64.deb": "DEB_ERROR"
}


Due to a bug/vulnerability in snapshot.debian.org's rate-limiting, the speed and accuracy of results will be drastically increased by adding the following to `/etc/hosts`:

```
2001:630:206:4000:1a1a:0:c13e:ca1a      snapshot.debian.org
```
