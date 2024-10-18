# Level 4
> The password for the next level is stored in a hidden file in the inhere directory.

```shell
$ ls
inhere

$ cd inhere/
$ ls

$ ls -lah
total 12K
drwxr-xr-x 2 root    root    4.0K Sep 19 07:08 .
drwxr-xr-x 3 root    root    4.0K Sep 19 07:08 ..
-rw-r----- 1 bandit4 bandit3   33 Sep 19 07:08 ...Hiding-From-You

$ cat ...Hiding-From-You 
2WmrDFRmJIq3IPxneAaMGhap0pFhF3NJ

$ exit

$ ssh bandit4@bandit.labs.overthewire.org -p 2220
$ 2WmrDFRmJIq3IPxneAaMGhap0pFhF3NJ
```
