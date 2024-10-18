# Level 1

```shell
leviathan1@gibson:~$ ls -lah
total 36K
drwxr-xr-x  2 root       root       4.0K Sep 19 07:07 .
drwxr-xr-x 83 root       root       4.0K Sep 19 07:09 ..
-rw-r--r--  1 root       root        220 Mar 31  2024 .bash_logout
-rw-r--r--  1 root       root       3.7K Mar 31  2024 .bashrc
-r-sr-x---  1 leviathan2 leviathan1  15K Sep 19 07:07 check
-rw-r--r--  1 root       root        807 Mar 31  2024 .profile

leviathan1@gibson:~$ ltrace ./check
__libc_start_main(0x80490ed, 1, 0xffffd494, 0 <unfinished ...>
printf("password: ")                                                                                                 = 10
getchar(0, 0, 0x786573, 0x646f67password: test
)                                                                                    = 116
getchar(0, 116, 0x786573, 0x646f67)                                                                                  = 101
getchar(0, 0x6574, 0x786573, 0x646f67)                                                                               = 115
strcmp("tes", "sex")                                                                                                 = 1
puts("Wrong password, Good Bye ..."Wrong password, Good Bye ...
)                                                                                 = 29
+++ exited (status 0) +++

leviathan1@gibson:~$ ./check
password: sex

$ cat /etc/leviathan_pass/leviathan2
NsN1HwFoyN

$ exit

leviathan1@gibson:~$ exit

$ ssh leviathan2@leviathan.labs.overthewire.org -p 2223
$ NsN1HwFoyN
```
