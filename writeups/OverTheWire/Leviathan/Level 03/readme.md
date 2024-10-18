# Level 3

```shell
leviathan3@gibson:~$ ls -lah
total 40K
drwxr-xr-x  2 root       root       4.0K Sep 19 07:07 .
drwxr-xr-x 83 root       root       4.0K Sep 19 07:09 ..
-rw-r--r--  1 root       root        220 Mar 31  2024 .bash_logout
-rw-r--r--  1 root       root       3.7K Mar 31  2024 .bashrc
-r-sr-x---  1 leviathan4 leviathan3  18K Sep 19 07:07 level3
-rw-r--r--  1 root       root        807 Mar 31  2024 .profile

leviathan3@gibson:~$ ./level3 
Enter the password> shid
bzzzzzzzzap. WRONG

leviathan3@gibson:~$ ltrace ./level3 
__libc_start_main(0x80490ed, 1, 0xffffd494, 0 <unfinished ...>
strcmp("h0no33", "kakaka")                               = -1
printf("Enter the password> ")                           = 20
fgets(Enter the password> help
"help\n", 256, 0xf7fae5c0)                         = 0xffffd26c
strcmp("help\n", "snlprintf\n")                          = -1
puts("bzzzzzzzzap. WRONG"bzzzzzzzzap. WRONG
)                               = 19
+++ exited (status 0) +++

leviathan3@gibson:~$ ./level3
Enter the password> snlprintf
[You\'ve got shell]!

$ bash     

leviathan4@gibson:~$ cat /etc/leviathan_pass/leviathan4
WG1egElCvO

$ exit
leviathan4@gibson:~$ exit

$ ssh leviathan4@leviathan.labs.overthewire.org -p 2223
$ WG1egElCvO
```
