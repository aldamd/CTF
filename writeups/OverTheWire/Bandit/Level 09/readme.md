# Level 9
> The password for the next level is stored in the file data.txt and is the only line of text that occurs only once

```shell
bandit8@bandit:~$ ls
data.txt

bandit8@bandit:~$ cat data.txt | sort | uniq -u
4CKMh1JI91bUIZZPXDqGanal4xvAg0JM

bandit8@bandit:~$ exit

$ ssh bandit9@bandit.labs.overthewire.org -p 2220
$ 4CKMh1JI91bUIZZPXDqGanal4xvAg0JM
```
