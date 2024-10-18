# Level 20
> To gain access to the next level, you should use the setuid binary in the homedirectory. Execute it without arguments to find out how to use it. The password for this level can be found in the usual place (/etc/bandit_pass), after you have used the setuid binary.

```shell
bandit19@bandit:~$ ls
bandit20-do

bandit19@bandit:~$ ls -lah bandit20-do 
-rwsr-x--- 1 bandit20 bandit19 15K Sep 19 07:08 bandit20-do

bandit19@bandit:~$ ./bandit20-do cat /etc/bandit_pass/bandit20
0qXahG8ZjOVMN9Ghs7iOWsCfZyXOUbYO

bandit19@bandit:~$ exit

$ ssh bandit20@bandit.labs.overthewire.org -p 2220
$ 0qXahG8ZjOVMN9Ghs7iOWsCfZyXOUbYO
```
