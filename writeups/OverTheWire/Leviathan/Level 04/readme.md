# Level 4

```shell
leviathan4@gibson:~$ ls -lah
total 24K
drwxr-xr-x  3 root root       4.0K Sep 19 07:07 .
drwxr-xr-x 83 root root       4.0K Sep 19 07:09 ..
-rw-r--r--  1 root root        220 Mar 31  2024 .bash_logout
-rw-r--r--  1 root root       3.7K Mar 31  2024 .bashrc
-rw-r--r--  1 root root        807 Mar 31  2024 .profile
dr-xr-x---  2 root leviathan4 4.0K Sep 19 07:07 .trash

leviathan4@gibson:~$ cd .trash/ && ls -lah
total 24K
dr-xr-x--- 2 root       leviathan4 4.0K Sep 19 07:07 .
drwxr-xr-x 3 root       root       4.0K Sep 19 07:07 ..
-r-sr-x--- 1 leviathan5 leviathan4  15K Sep 19 07:07 bin

leviathan4@gibson:~/.trash$ ./bin
00110000 01100100 01111001 01111000 01010100 00110111 01000110 00110100 01010001 01000100 00001010
```

![image](https://github.com/user-attachments/assets/7f579044-1a09-4685-aadb-74562feeec23)

```shell
leviathan4@gibson:~/.trash$ exit

$ ssh leviathan5@leviathan.labs.overthewire.org -p 2223
$ 0dyxT7F4QD
```
