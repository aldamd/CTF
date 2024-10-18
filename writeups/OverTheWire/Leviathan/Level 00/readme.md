# Level 0

```shell
leviathan0@gibson:~$ ls -lah
total 24K
drwxr-xr-x  3 root       root       4.0K Sep 19 07:07 .
drwxr-xr-x 83 root       root       4.0K Sep 19 07:09 ..
drwxr-x---  2 leviathan1 leviathan0 4.0K Sep 19 07:07 .backup
-rw-r--r--  1 root       root        220 Mar 31  2024 .bash_logout
-rw-r--r--  1 root       root       3.7K Mar 31  2024 .bashrc
-rw-r--r--  1 root       root        807 Mar 31  2024 .profile

leviathan0@gibson:~$ cd .backup/
leviathan0@gibson:~/.backup$ ls
bookmarks.html

leviathan0@gibson:~/.backup$ ls -lah
total 140K
drwxr-x--- 2 leviathan1 leviathan0 4.0K Sep 19 07:07 .
drwxr-xr-x 3 root       root       4.0K Sep 19 07:07 ..
-rw-r----- 1 leviathan1 leviathan0 131K Sep 19 07:07 bookmarks.html

leviathan0@gibson:~/.backup$ cat bookmarks.html | grep -i leviathan
<DT><A HREF="http://leviathan.labs.overthewire.org/passwordus.html |
This will be fixed later, the password for leviathan1 is 3QJ3TgzHDq"
ADD_DATE="1155384634" LAST_CHARSET="ISO-8859-1" ID="rdf:#$2wIU71">password to leviathan1</A>

leviathan0@gibson:~/.backup$ exit

$ ssh leviathan1@leviathan.labs.overthewire.org -p 2223
$ 3QJ3TgzHDq
```
