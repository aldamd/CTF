# Level 27
> Good job getting a shell! Now hurry and grab the password for bandit27!

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
