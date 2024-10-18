# Level 7
> The password for the next level is stored somewhere on the server and has all of the following properties:
> - owned by user bandit7
> - owned by group bandit6
> - 33 bytes in size

```shell
bandit6@bandit:~$ find / -type f -user bandit7 -group bandit6 -size 33c -exec cat {} \; 2>/dev/null
morbNTDkSW6jIlUc0ymOdMaLnOlFVAaj

bandit6@bandit:~$ exit

$ ssh bandit7@bandit.labs.overthewire.org -p 2220
$ morbNTDkSW6jIlUc0ymOdMaLnOlFVAaj
```


