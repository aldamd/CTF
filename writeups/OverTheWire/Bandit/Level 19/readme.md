# Level 19
> The password for the next level is stored in a file readme in the homedirectory. Unfortunately, someone has modified .bashrc to log you out when you log in with SSH.

```shell
$ ssh bandit18@bandit.labs.overthewire.org -p 2220 /bin/bash
$ x2gLTTjFwMOhQ8oWNbMN362QKxfRqGlO

ls
readme

cat readme
cGWpMaKXVwDUNgPAVJbWYuGHVn9zl3j8

exit

$ ssh bandit19@bandit.labs.overthewire.org -p 2220
$ cGWpMaKXVwDUNgPAVJbWYuGHVn9zl3j8
```
