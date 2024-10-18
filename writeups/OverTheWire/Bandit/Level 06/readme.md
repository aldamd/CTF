# Level 6
> The password for the next level is stored in a file somewhere under the inhere directory and has all of the following properties:
> - human-readable
> - 1033 bytes in size
> - not executable

```shell
bandit5@bandit:~$ ls
inhere

bandit5@bandit:~$ cd inhere/

bandit5@bandit:~/inhere$ ls
maybehere00  maybehere03  maybehere06  maybehere09  maybehere12  maybehere15  maybehere18
maybehere01  maybehere04  maybehere07  maybehere10  maybehere13  maybehere16  maybehere19
maybehere02  maybehere05  maybehere08  maybehere11  maybehere14  maybehere17

bandit5@bandit:~/inhere$ find . -type f -readable -size 1033c ! -executable -exec cat {} \;
HWasnPhtq9AVKe0dmk45nxy20cvUa6EG

bandit5@bandit:~/inhere$ exit

$ ssh bandit6@bandit.labs.overthewire.org -p 2220
$ HWasnPhtq9AVKe0dmk45nxy20cvUa6EG
```
