# Level 31
> There is a git repository at ssh://bandit30-git@localhost/home/bandit30-git/repo via the port 2220. The password for the user bandit30-git is the same as for the user bandit30.
> Clone the repository and find the password for the next level.

```shell
bandit30@bandit:~$ cd $(mktemp -d)
bandit30@bandit:/tmp/tmp.OQSb671JCH$ git clone ssh://bandit30-git@localhost:2220/home/bandit30-git/repo
Cloning into 'repo'...
[...]

bandit30@bandit:/tmp/tmp.OQSb671JCH$ cd repo/ && ls -lah
total 16K
drwxrwxr-x 3 bandit30 bandit30 4.0K Oct 18 03:56 .
drwx------ 3 bandit30 bandit30 4.0K Oct 18 03:56 ..
drwxrwxr-x 8 bandit30 bandit30 4.0K Oct 18 03:56 .git
-rw-rw-r-- 1 bandit30 bandit30   30 Oct 18 03:56 README.md

bandit30@bandit:/tmp/tmp.OQSb671JCH/repo$ cat README.md 
just an epmty file... muahaha

bandit30@bandit:/tmp/tmp.OQSb671JCH/repo$ git log
commit acfc3c67816fc778c4aeb5893299451ca6d65a78 (HEAD -> master, origin/master, origin/HEAD)
Author: Ben Dover <noone@overthewire.org>
Date:   Thu Sep 19 07:08:44 2024 +0000

    initial commit of README.md

bandit30@bandit:/tmp/tmp.OQSb671JCH/repo$ git branch -a
* master
  remotes/origin/HEAD -> origin/master
  remotes/origin/master

bandit30@bandit:/tmp/tmp.OQSb671JCH/repo$ git tag
secret

bandit30@bandit:/tmp/tmp.OQSb671JCH/repo$ git show secret
fb5S2xb7bRyFmAvQYQGEqsbhVyJqhnDy

$ ssh bandit31@bandit.labs.overthewire.org -p 2220
$ fb5S2xb7bRyFmAvQYQGEqsbhVyJqhnDy
```
