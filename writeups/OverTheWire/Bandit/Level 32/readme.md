# Level 32
> There is a git repository at ssh://bandit31-git@localhost/home/bandit31-git/repo via the port 2220. The password for the user bandit31-git is the same as for the user bandit31.
> Clone the repository and find the password for the next level.

```shell
bandit31@bandit:~$ cd $(mktemp -d)
bandit31@bandit:/tmp/tmp.6KA5aSg6Lq$ git clone ssh://bandit31-git@localhost:2220/home/bandit31-git/repo
Cloning into 'repo'...
[...]

bandit31@bandit:/tmp/tmp.6KA5aSg6Lq$ cd repo/ && ls 
README.md
bandit31@bandit:/tmp/tmp.6KA5aSg6Lq/repo$ cat README.md 
This time your task is to push a file to the remote repository.

Details:
    File name: key.txt
    Content: 'May I come in?'
    Branch: master

bandit31@bandit:/tmp/tmp.6KA5aSg6Lq/repo$ echo "May I come in?" > key.txt

bandit31@bandit:/tmp/tmp.6KA5aSg6Lq/repo$ git add key.txt 
The following paths are ignored by one of your .gitignore files:
key.txt
hint: Use -f if you really want to add them.
hint: Turn this message off by running
hint: "git config advice.addIgnoredFile false"

bandit31@bandit:/tmp/tmp.6KA5aSg6Lq/repo$ git add -f key.txt

bandit31@bandit:/tmp/tmp.6KA5aSg6Lq/repo$ git commit -m "pretty please"

bandit31@bandit:/tmp/tmp.6KA5aSg6Lq/repo$ git push -u origin master
remote: ### Attempting to validate files... ####
remote: 
remote: .oOo.oOo.oOo.oOo.oOo.oOo.oOo.oOo.oOo.oOo.
remote: 
remote: Well done! Here is the password for the next level:
remote: 3O9RfhqyAlVBEZpVb6LYStshZoqoSx5K 
remote: 
remote: .oOo.oOo.oOo.oOo.oOo.oOo.oOo.oOo.oOo.oOo.
remote: 

$ ssh bandit32@bandit.labs.overthewire.org -p 2220
$ 3O9RfhqyAlVBEZpVb6LYStshZoqoSx5K
```


