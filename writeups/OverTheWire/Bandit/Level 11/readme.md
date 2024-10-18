# Level 11
> The password for the next level is stored in the file data.txt, which contains base64 encoded data

```shell
bandit10@bandit:~$ ls
data.txt

bandit10@bandit:~$ cat data.txt 
VGhlIHBhc3N3b3JkIGlzIGR0UjE3M2ZaS2IwUlJzREZTR3NnMlJXbnBOVmozcVJyCg==

bandit10@bandit:~$ cat data.txt | base64 -d
The password is dtR173fZKb0RRsDFSGsg2RWnpNVj3qRr

bandit10@bandit:~$ exit

$ ssh bandit11@bandit.labs.overthewire.org -p 2220
$ dtR173fZKb0RRsDFSGsg2RWnpNVj3qRr
```
