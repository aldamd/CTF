# Level 16
> The password for the next level can be retrieved by submitting the password of the current level to port 30001 on localhost using SSL/TLS encryption.

```shell
bandit15@bandit:~$ cat /etc/bandit_pass/bandit15
8xCjnmgoKbGLhHFAZlGE5Tmu4M2tKJQo

bandit15@bandit:~$ openssl s_client -connect localhost:30001
CONNECTED(00000003)
[...]
read R BLOCK
8xCjnmgoKbGLhHFAZlGE5Tmu4M2tKJQo
Correct!
kSkvUpMQ7lBYyCM4GBPvCvT1BfWRy0Dx

bandit15@bandit:~$ exit

$ ssh bandit16@bandit.labs.overthewire.org -p 2220
$ kSkvUpMQ7lBYyCM4GBPvCvT1BfWRy0Dx
```
