# Level 28
> There is a git repository at ssh://bandit27-git@localhost/home/bandit27-git/repo via the port 2220. The password for the user bandit27-git is the same as for the user bandit27.
> Clone the repository and find the password for the next level.

```shell
bandit27@bandit:~$ mktemp -d
/tmp/tmp.HyQiuW1Joe

bandit27@bandit:~$ cd /tmp/tmp.HyQiuW1Joe
git clone ssh://bandit27-git@localhost:2220/home/bandit27-git/repo
Cloning into 'repo'...
[...]

bandit27@bandit:/tmp/tmp.HyQiuW1Joe$ ls
repo

bandit27@bandit:/tmp/tmp.HyQiuW1Joe$ ls repo/
README

bandit27@bandit:/tmp/tmp.HyQiuW1Joe$ cat repo/README 
The password to the next level is: Yz9IpL0sBcCeuG7m9uQFt8ZNpS4HZRcN

$ ssh bandit28@bandit.labs.overthewire.org -p 2220
$ Yz9IpL0sBcCeuG7m9uQFt8ZNpS4HZRcN
```
