# Level 26
> Logging in to bandit26 from bandit25 should be fairly easy… The shell for user bandit26 is not /bin/bash, but something else. Find out what it is, how it works and how to break out of it.

```shell
bandit25@bandit:~$ cat /etc/passwd | grep bandit26
bandit26:x:11026:11026:bandit level 26:/home/bandit26:/usr/bin/showtext

bandit25@bandit:~$ cat /usr/bin/showtext
#!/bin/sh

export TERM=linux

exec more ~/text.txt
exit 0
```

more is a shell command that allows the display of files in an interactive mode. Specifically, this interactive mode only works when the content of the file is too large to fully be displayed in the terminal window. One command that is allowed in the interactive mode is v. This command will open the file in the editor ‘vim’.

```shell
bandit25@bandit:~$ ls
bandit26.sshkey
```

We can copy over this ssh key to our local machine and change the file permissions to actually use it

```shell
$ chmod 700 bandit26.sshkey 
$ ll bandit26.sshkey 
-rwx------ 1 aldamd aldamd 1.7K Oct 17 23:18 bandit26.sshkey

$ ssh bandit26@bandit.labs.overthewire.org -p 2220 -i ./bandit26.sshkey
[...]
Connection to bandit.labs.overthewire.org closed.
```

The exit 0 part of the /usr/bin/showtext immediately closes us out of the shell. In order to fix this, we need to exploit a property of the $ more command

![image](https://github.com/user-attachments/assets/462b7a26-bcec-42d3-acd4-dd654f785096)

If we make the window real small, more stays active and doesn't close itself!

![image](https://github.com/user-attachments/assets/c11f6927-2a75-423a-8140-56a84f113182)

Now we can type ```v``` to enter vim mode, then ```:set shell=/bin/bash```, and then ```:shell```, and now we've popped a bash session!

```shell
bandit26@bandit:~$ ./bandit27-do cat /etc/bandit_pass/bandit27
upsNCc7vzaRDx6oZC6GiR6ERwe1MowGB

aldamd@deb-laptop:~$ ssh bandit27@bandit.labs.overthewire.org -p 2220
upsNCc7vzaRDx6oZC6GiR6ERwe1MowGB
```
