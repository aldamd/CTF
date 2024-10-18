# Level 10
> The password for the next level is stored in the file data.txt in one of the few human-readable strings, preceded by several ‘=’ characters.

```shell
bandit9@bandit:~$ ls
data.txt

bandit9@bandit:~$ cat data.txt | grep ==
grep: (standard input): binary file matches

bandit9@bandit:~$ strings data.txt | grep ==
}========== the
3JprD========== passwordi
~fDV3========== is
D9========== FGUW5ilLVJrxX9kMYMmlN4MgbpfMiqey

bandit9@bandit:~$ exit

$ ssh bandit10@bandit.labs.overthewire.org -p 2220
$ FGUW5ilLVJrxX9kMYMmlN4MgbpfMiqey
```
