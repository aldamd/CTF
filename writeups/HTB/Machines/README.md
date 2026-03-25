## Linux

---

### Easy

| Easy Machine    | Categories                                                                                                                                   |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [[Lame]]        | SMB, FTP, CVE-2011-2523                                                                                                                      |
| [[Shocker]]     | feroxbuster, Shellshock (CVE-2014-6271)                                                                                                      |
| [[Bashed]]      | feroxbuster, phpbash.php, nopasswd                                                                                                           |
| [[Nibbles]]     | feroxbuster, file upload vulnerability, php webshell                                                                                         |
| [[Expressway]]  | UDP, ike-scan, psk-crack                                                                                                                     |
| [[Beep]]        | PBX, feroxbuster, sipvicious, swaks, LFI, SMTP, Webshell, Shellshock                                                                         |
| [[Sense]]       | pfSense, feroxbuster, command injection                                                                                                      |
| [[Valentine]]   | heartbleed, feroxbuster, openssl                                                                                                             |
| [[Dog]]         | feroxbuster, git-dumper, bee                                                                                                                 |
| [[Editor]]      | ffuf subdomain brute force, web RCE, netstat, ssh -L, netdata ndsudo privesc                                                                 |
| [[Titanic]]     | ffuf subdomain brute force, LFI, gitea, sqlite, ImageMagick, Arbitrary Code Execution                                                        |
| [[LinkVortex]]  | ffuf subdomain brute force, git-dumper, git, curl, arbitrary file read, TOCTOU                                                               |
| [[Editorial]]   | feroxbuster, burp, SSRF, ffuf internal port enumeration, git log, GitPython, RCE                                                             |
| [[BoardLight]]  | feroxbuster, ffuf subdomain brute force, burp, default credentials, php code injection, reused credentials, Enlightenment, command injection |
| [[Usage]]       | ffuf subdomain brute force, burp, sqlmap, php remote shell, hashcat, binary ninja                                                            |
| [[CozyHosting]] | springboot, command injection, psql, hashcat                                                                                                 |
| [[Busqueda]]    | searchor, python command injection, git, gitea, docker, path hijacking                                                                       |
| [[Keeper]]      | request tracker, keepass, CVE-2023-3278, keepass2john, hashcat, kpcli, putty                                                                 |
| [[Broker]]      | Apache ActiveMQ, OpenWire, sudo nginx, ssh-keygen, ld.so.preload                                                                             |
| [[Sau]]         | Requests-Basket, Maltrail, SSRF, Command Injection, sudo systemctl, sudo less                                                                |

### Medium

| Medium Machine | Categories                                                                                                                             |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| [[Cronos]]     | DNS, Zone Transfer, SQLi, CMDi, system crontab, php poisoning, MyS                                                                     |
| [[Haircut]]    | feroxbuster, command injection, php webshell, suid privesc, screen,                                                                    |
| [[Nineveh]]    | feroxbuster, SQLite, php type confusion, LFI, webshell, phpinfo, strings, binwalk, steg, port knocking, knockd, crontab, pspy, chkroot |
| [[SolidState]] | feroxbuster, SMTP, POP3, James, pspy, rbash sandbox                                                                                    |
| [[Monitored]]  | snmp, ffuf subdomain brute force, feroxbuster, API enumeration, sql injection, nagiosXI, symlink abuse, shell script appsec            |
| [[Builder]]    | jenkins, partial file read, hashcat, jenkins pipelines                                                                                 |

### Hard

| Hard Machine | Categories |
| ------------ | ---------- |
|              |            |

## Windows

---

### Easy

| Easy Machine | Categories                                                                                                            |
| ------------ | --------------------------------------------------------------------------------------------------------------------- |
| [[Blue]]     | SMB, Nmap Vulnerability Scan, Metasploit, Eternal Blue                                                                |
| [[Devel]]    | feroxbuster, ASPX, Watson, Windows Kernel Privesc                                                                     |
| [[Baby]]     | Active Directory, LDAP Enum, SeBackupPrivilege                                                                        |
| [[Fluffy]]   | Active Directory, bloodhound, certipy, bloodyAD, ESC16                                                                |
| [[Lock]]     | Gittea, Webshell, RDP, PDF24, CVE-2023-49147                                                                          |
| [[Cicada]]   | smb, ldap, bloodhound, SeBackupPrivilege                                                                              |
| [[Mailing]]  | LFI, smtp log poisoning, LFI to RCE, Windows Mail, Responder, hashcat, LibreOffice, SeImpersonatePrivilege, GodPotato |

### Medium

| Medium Machine    | Categories                                                                                                                                                  |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [[TombWatcher]]   | bloodhound, bloodyAD, certipy, powershell, targeted kerberoast, ReadGMSAPassword, ForceChangePassword, WriteOwner, Shadow Credential, AD Recycle Bin, ESC15 |
| [[TheFrizz]]      | PHP webshell, mysql, hashcat, recycling bin, kinit, kerberos SSH, Group Policy Owner Creator, SharpGPOAbuse                                                 |
| [[Administrator]] | Generic All, Force Password Change, Generic Write, DCSync, hashcat, secretsdump.py                                                                          |
| [[Certified]]     | bloodhound, bloodyad, certipy, WriteOwner, GenericWrite, GenericAll, ADCS, ESC9                                                                             |
| [[Manager]]       | smb, rid-bruteforce, mssql, xp_dirtree, certipy, ADCS, ESC7                                                                                                 |
