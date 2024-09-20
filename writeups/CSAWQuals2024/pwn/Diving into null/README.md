# Diving into null
> Oops, I rm -rf 'ed my binaries

When we netcat into the challenge, we're automatically signed in as user groot. We immediately find out that, as the description alludes, we have jack squat for binaries. ls, cat, clear, none of them seem to work.

```sh
groot@diving-into-null:/$ ls
ls
bash: ls: command not found
groot@diving-into-null:/$ cat
cat
bash: cat: command not found
groot@diving-into-null:/$ clear
clear
bash: clear: command not found
```

None of them except echo, cd, pwd, and probably some other less useful ones. Luckily, echo can be used in place of ls in a pinch as follows:

```sh
groot@diving-into-null:/$ echo *
echo *
bin boot dev etc home lib lib64 media mnt opt proc root run sbin srv sys tmp usr var
```

If the author of this CTF is kind then the flag is likely to be in our home directory

```sh
groot@diving-into-null:/$ cd
cd
groot@diving-into-null:~$ echo *
echo *
*
```

That's unfortunate. Maybe it's a hidden file?

```sh
groot@diving-into-null:~$ echo .*
echo .*
.bash_history .bashrc .flag .profile
```

We love kind CTF authors. After doing some googling on how to use echo in place of cat, we came across this funky command which inevitably leads us to our flag!

```sh
groot@diving-into-null:~$ echo $(<.flag)
echo $(<.flag)
||||| ||| csawctf{penguins_are_just_birds_with_tuxedos} ||| |||||
```

Bada bing, our flag is csawctf{penguins_are_just_birds_with_tuxedos}
