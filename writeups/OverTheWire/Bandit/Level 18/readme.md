# Level 18
> There are 2 files in the homedirectory: passwords.old and passwords.new. The password for the next level is in passwords.new and is the only line that has been changed between passwords.old and passwords.new

```shell
bandit17@bandit:~$ ls
passwords.new  passwords.old

bandit17@bandit:~$ diff passwords.old passwords.new
42c42
< ktfgBvpMzWKR5ENj26IbLGSblgUG9CzB
---
> x2gLTTjFwMOhQ8oWNbMN362QKxfRqGlO

bandit17@bandit:~$ exit

$ ssh bandit18@bandit.labs.overthewire.org -p 2220
$ x2gLTTjFwMOhQ8oWNbMN362QKxfRqGlO
[...]
Byebye !
Connection to bandit.labs.overthewire.org closed.
```

We'll deal with this later
