# Level 30
> There is a git repository at ssh://bandit29-git@localhost/home/bandit29-git/repo via the port 2220. The password for the user bandit29-git is the same as for the user bandit29.
> Clone the repository and find the password for the next level.

```shell
bandit29@bandit:~$ cd $(mktemp -d)

bandit29@bandit:/tmp/tmp.XWVtzX455C$ git clone ssh://bandit29-git@localhost:2220/home/bandit29-git/repo
Cloning into 'repo'...
[...]

bandit29@bandit:/tmp/tmp.XWVtzX455C$ cd repo/
bandit29@bandit:/tmp/tmp.XWVtzX455C/repo$ ls
README.md

bandit29@bandit:/tmp/tmp.XWVtzX455C/repo$ cat README.md 
# Bandit Notes
Some notes for bandit30 of bandit.

## credentials

- username: bandit30
- password: <no passwords in production!>

bandit29@bandit:/tmp/tmp.XWVtzX455C/repo$ git branch -a
* master
  remotes/origin/HEAD -> origin/master
  remotes/origin/dev
  remotes/origin/master
  remotes/origin/sploits-dev

bandit29@bandit:/tmp/tmp.XWVtzX455C/repo$ git checkout dev
branch 'dev' set up to track 'origin/dev'.
Switched to a new branch 'dev'

bandit29@bandit:/tmp/tmp.XWVtzX455C/repo$ ls -lah
total 20K
drwxrwxr-x 4 bandit29 bandit29 4.0K Oct 18 03:52 .
drwx------ 3 bandit29 bandit29 4.0K Oct 18 03:51 ..
drwxrwxr-x 2 bandit29 bandit29 4.0K Oct 18 03:52 code
drwxrwxr-x 8 bandit29 bandit29 4.0K Oct 18 03:52 .git
-rw-rw-r-- 1 bandit29 bandit29  134 Oct 18 03:52 README.md

bandit29@bandit:/tmp/tmp.XWVtzX455C/repo$ cat README.md 
# Bandit Notes
Some notes for bandit30 of bandit.

## credentials

- username: bandit30
- password: qp30ex3VLz5MDG1n91YowTv4Q8l7CDZL

$ ssh bandit30@bandit.labs.overthewire.org -p 2220
$ qp30ex3VLz5MDG1n91YowTv4Q8l7CDZL
```
