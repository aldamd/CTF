# Level 33
> After all this git stuff, it’s time for another escape. Good luck!

To print all environment variables, you can use printenv.
Some common that are good to know are:
• TERM -  current terminal emulation
• HOME - the path to home directory of currently logged in user
• LANG - current locales settings
• PATH - directory list to be searched when executing commands
• PWD - pathname of the current working directory
• SHELL/0 - the path of the current user’s shell
• USER - currently logged-in user

```shell
WELCOME TO THE UPPERCASE SHELL
>> ls
sh: 1: LS: Permission denied
>> sh
sh: 1: SH: Permission denied
>> man
sh: 1: MAN: Permission denied
>> $path
sh: 1: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin: not found
>> $env
>> echo $env
sh: 1: ECHO: Permission denied
>> echo $TERM
sh: 1: ECHO: Permission denied
>> $TERM
sh: 1: xterm-256color: Permission denied
>> $HOME
sh: 1: /home/bandit32: Permission denied
>> $LANG
sh: 1: C.UTF-8: Permission denied
>> $PATH
sh: 1: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin: not found
>> $PWD
sh: 1: /home/bandit32: Permission denied
>> 0
sh: 1: 0: Permission denied
>> $0
$ ls
uppershell
$ bash

bandit33@bandit:~$ cat /etc/bandit_pass/bandit33
tQdtbs5D5i2vJwkO8mEyYEyTL8izoeJ0
```
