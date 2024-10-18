# Level 8
> The password for the next level is stored in the file data.txt next to the word millionth

```shell
bandit7@bandit:~$ ls
data.txt

bandit7@bandit:~$ cat data.txt | grep millionth -B5 -A5
shuffler	9AEMWmCMG4YUUW6oa8RvmfinaQtdSx0J
forester's	T4RtlAIFC9sb7y6yzBGwDjwsOYgU8NxJ
Lilian	s9lUxPFDRQzV9xzPQYOVpwNGf6NI37zo
quark's	l9sURQrRace2eUz7VljAL7YIuybi8elz
conspirator	7SNeFn5yY0xgGhGZBRUjn548IGcy6I8P
millionth	dfwvzFQi4mU0wfNbFOe9RoWskMLg7eEc
bistros	0uUWlqktnXxl1SbHceHzB2L6LgzEBhER
wifeliest	I90cYhcx09Prp2ddfj5ngvnbdx157F6D
legionnaire	diL66wsns24U8uOZ4RmaqbD48aRnSVmX
Grenoble's	1MB4kpeF706AgORHdmsqEjFpNkTU6Bm7
reneging	rx6BWAUyx7X4BzuoEOEvdqNp3phCL9PU

bandit7@bandit:~$ exit

$ ssh bandit8@bandit.labs.overthewire.org -p 2220
$ dfwvzFQi4mU0wfNbFOe9RoWskMLg7eEc
```
