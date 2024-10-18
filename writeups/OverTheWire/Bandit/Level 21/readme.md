# Level 21
> There is a setuid binary in the homedirectory that does the following: it makes a connection to localhost on the port you specify as a commandline argument. It then reads a line of text from the connection and compares it to the password in the previous level (bandit20). If the password is correct, it will transmit the password for the next level (bandit21).

```shell
bandit20@bandit:~$ ls 
suconnect

bandit20@bandit:~$ ls -lah suconnect 
-rwsr-x--- 1 bandit21 bandit20 16K Sep 19 07:08 suconnect

bandit20@bandit:~$ echo 0qXahG8ZjOVMN9Ghs7iOWsCfZyXOUbYO | nc -lp 9999 &
[1] 2097061

bandit20@bandit:~$ ./suconnect 9999
Read: 0qXahG8ZjOVMN9Ghs7iOWsCfZyXOUbYO
Password matches, sending next password
EeoULMCra2q0dSkYj561DX7s1CpBuOBt
[1]+  Done                    echo 0qXahG8ZjOVMN9Ghs7iOWsCfZyXOUbYO | nc -lp 9999

bandit20@bandit:~$ exit

$ ssh bandit21@bandit.labs.overthewire.org -p 2220
$ EeoULMCra2q0dSkYj561DX7s1CpBuOBt
```
