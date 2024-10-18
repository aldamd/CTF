# Level 15
> The password for the next level can be retrieved by submitting the password of the current level to port 30000 on localhost.

```shell
bandit14@bandit:~$ cat /etc/bandit_pass/bandit14
MU4VWeTyJk8ROof1qqmcBPaLh7lDCPvS

bandit14@bandit:~$ nc localhost 30000
MU4VWeTyJk8ROof1qqmcBPaLh7lDCPvS
Correct!
8xCjnmgoKbGLhHFAZlGE5Tmu4M2tKJQo

^C

bandit14@bandit:~$ exit

$ ssh bandit15@bandit.labs.overthewire.org -p 2220
$ 8xCjnmgoKbGLhHFAZlGE5Tmu4M2tKJQo
```
