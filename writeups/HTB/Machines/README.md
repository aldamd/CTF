## Linux

---

### Easy

| Easy Machine    | Categories                                                                                                                                   |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [Lame](Lame/Lame.md)        | SMB, FTP, CVE-2011-2523                                                                                                                      |
| [Shocker](Shocker/Shocker.md)     | feroxbuster, Shellshock (CVE-2014-6271)                                                                                                      |
| [Bashed](Bashed/Bashed.md)      | feroxbuster, phpbash.php, nopasswd                                                                                                           |
| [Nibbles](Nibbles/Nibbles.md)     | feroxbuster, file upload vulnerability, php webshell                                                                                         |
| [Expressway](Expressway/Expressway.md)  | UDP, ike-scan, psk-crack                                                                                                                     |
| [Beep](Beep/Beep.md)        | PBX, feroxbuster, sipvicious, swaks, LFI, SMTP, Webshell, Shellshock                                                                         |
| [Sense](Sense/Sense.md)       | pfSense, feroxbuster, command injection                                                                                                      |
| [Valentine](Valentine/Valentine.md)   | heartbleed, feroxbuster, openssl                                                                                                             |
| [Dog](Dog/Dog.md)         | feroxbuster, git-dumper, bee                                                                                                                 |
| [Editor](Editor/Editor.md)      | ffuf subdomain brute force, web RCE, netstat, ssh -L, netdata ndsudo privesc                                                                 |
| [Titanic](Titanic/Titanic.md)     | ffuf subdomain brute force, LFI, gitea, sqlite, ImageMagick, Arbitrary Code Execution                                                        |
| [LinkVortex](LinkVortex/LinkVortex.md)  | ffuf subdomain brute force, git-dumper, git, curl, arbitrary file read, TOCTOU                                                               |
| [Editorial](Editorial/Editorial.md)   | feroxbuster, burp, SSRF, ffuf internal port enumeration, git log, GitPython, RCE                                                             |
| [BoardLight](BoardLight/BoardLight.md)  | feroxbuster, ffuf subdomain brute force, burp, default credentials, php code injection, reused credentials, Enlightenment, command injection |
| [Usage](Usage/Usage.md)       | ffuf subdomain brute force, burp, sqlmap, php remote shell, hashcat, binary ninja                                                            |
| [CozyHosting](CozyHosting/CozyHosting.md) | springboot, command injection, psql, hashcat                                                                                                 |
| [Busqueda](Busqueda/Busqueda.md)    | searchor, python command injection, git, gitea, docker, path hijacking                                                                       |
| [Keeper](Keeper/Keeper.md)      | request tracker, keepass, CVE-2023-3278, keepass2john, hashcat, kpcli, putty                                                                 |
| [Broker](Broker/Broker.md)      | Apache ActiveMQ, OpenWire, sudo nginx, ssh-keygen, ld.so.preload                                                                             |
| [Sau](Sau/Sau.md)         | Requests-Basket, Maltrail, SSRF, Command Injection, sudo systemctl, sudo less                                                                |

### Medium

| Medium Machine | Categories                                                                                                                             |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| [Cronos](Cronos/Cronos.md)     | DNS, Zone Transfer, SQLi, CMDi, system crontab, php poisoning, MyS                                                                     |
| [Haircut](Haircut/Haircut.md)    | feroxbuster, command injection, php webshell, suid privesc, screen,                                                                    |
| [Nineveh](Nineveh/Nineveh.md)    | feroxbuster, SQLite, php type confusion, LFI, webshell, phpinfo, strings, binwalk, steg, port knocking, knockd, crontab, pspy, chkroot |
| [SolidState](SolidState/SolidState.md) | feroxbuster, SMTP, POP3, James, pspy, rbash sandbox                                                                                    |
| [Monitored](Monitored/Monitored.md)  | snmp, ffuf subdomain brute force, feroxbuster, API enumeration, sql injection, nagiosXI, symlink abuse, shell script appsec            |
| [Builder](Builder/Builder.md)    | jenkins, partial file read, hashcat, jenkins pipelines                                                                                 |

### Hard

| Hard Machine | Categories |
| ------------ | ---------- |
|              |            |

## Windows

---

### Easy

| Easy Machine | Categories                                                                                                            |
| ------------ | --------------------------------------------------------------------------------------------------------------------- |
| [Blue](Blue/Blue.md)     | SMB, Nmap Vulnerability Scan, Metasploit, Eternal Blue                                                                |
| [Devel](Devel/Devel.md)    | feroxbuster, ASPX, Watson, Windows Kernel Privesc                                                                     |
| [Baby](Baby/Baby.md)     | Active Directory, LDAP Enum, SeBackupPrivilege                                                                        |
| [Fluffy](Fluffy/Fluffy.md)   | Active Directory, bloodhound, certipy, bloodyAD, ESC16                                                                |
| [Lock](Lock/Lock.md)     | Gittea, Webshell, RDP, PDF24, CVE-2023-49147                                                                          |
| [Cicada](Cicada/Cicada.md)   | smb, ldap, bloodhound, SeBackupPrivilege                                                                              |
| [Mailing](Mailing/Mailing.md)  | LFI, smtp log poisoning, LFI to RCE, Windows Mail, Responder, hashcat, LibreOffice, SeImpersonatePrivilege, GodPotato |

### Medium

| Medium Machine    | Categories                                                                                                                                                  |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [TombWatcher](TombWatcher/TombWatcher.md)   | bloodhound, bloodyAD, certipy, powershell, targeted kerberoast, ReadGMSAPassword, ForceChangePassword, WriteOwner, Shadow Credential, AD Recycle Bin, ESC15 |
| [TheFrizz](TheFrizz/TheFrizz.md)      | PHP webshell, mysql, hashcat, recycling bin, kinit, kerberos SSH, Group Policy Owner Creator, SharpGPOAbuse                                                 |
| [Administrator](Administrator/Administrator.md) | Generic All, Force Password Change, Generic Write, DCSync, hashcat, secretsdump.py                                                                          |
| [Certified](Certified/Certified.md)     | bloodhound, bloodyad, certipy, WriteOwner, GenericWrite, GenericAll, ADCS, ESC9                                                                             |
| [Manager](Manager/Manager.md)       | smb, rid-bruteforce, mssql, xp_dirtree, certipy, ADCS, ESC7                                                                                                 |
