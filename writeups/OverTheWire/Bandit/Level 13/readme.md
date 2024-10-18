# Level 13
> The password for the next level is stored in the file data.txt, which is a hexdump of a file that has been repeatedly compressed. For this level it may be useful to create a directory under /tmp in which you can work. Use mkdir with a hard to guess directory name. Or better, use the command “mktemp -d”. Then copy the datafile using cp, and rename it using mv (read the manpages!)

```shell
bandit12@bandit:~$ cd $(mktemp -d)

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ cp ~/data.txt .

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ cat data.txt | head -n 1
00000000: 1f8b 0808 dfcd eb66 0203 6461 7461 322e  .......f..data2.
```

Here's a breakdown of the first few bytes:
- 1f 8b: The magic number for Gzip, indicating that this is a Gzip-compressed file.
- 08: Compression method (08 refers to the "deflate" compression algorithm used by Gzip).

```shell
bandit12@bandit:/tmp/tmp.okIsKk6VYG$ xxd -r data.txt > data.gz

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ gzip -d data.gz

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ ls
data  data.txt

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ file data
data: bzip2 compressed data, block size = 900k

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ bzip2 -d data
bzip2: Can\'t guess original name for data -- using data.out

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ ls
data.out  data.txt

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ file data.out
data.out: gzip compressed data, was "data4.bin", last modified: Thu Sep 19 07:08:15 2024, max compression, from Unix, original size modulo 2^32 20480

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ mv data.out data.gz && gzip -d data.gz
bandit12@bandit:/tmp/tmp.okIsKk6VYG$ ls
data  data.txt

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ file data
data: POSIX tar archive (GNU)

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ tar -xf data
bandit12@bandit:/tmp/tmp.okIsKk6VYG$ ls
data  data5.bin  data.txt

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ file data5.bin
data5.bin: POSIX tar archive (GNU)

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ tar -xf data5.bin
bandit12@bandit:/tmp/tmp.okIsKk6VYG$ ls
data  data5.bin  data6.bin  data.txt

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ file data6.bin
data6.bin: bzip2 compressed data, block size = 900k

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ bzip2 -d data6.bin
bzip2: Can\'t guess original name for data6.bin -- using data6.bin.out

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ ls
data  data5.bin  data6.bin.out  data.txt

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ file data6.bin.out
data6.bin.out: POSIX tar archive (GNU)

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ tar -xf data6.bin.out
bandit12@bandit:/tmp/tmp.okIsKk6VYG$ ls
data  data5.bin  data6.bin.out  data8.bin  data.txt

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ file data8.bin
data8.bin: gzip compressed data, was "data9.bin", last modified: Thu Sep 19 07:08:15 2024, max compression, from Unix, original size modulo 2^32 49

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ mv data8.bin data8.bin.gz && gzip -d data8.bin.gz
bandit12@bandit:/tmp/tmp.okIsKk6VYG$ ls
data  data5.bin  data6.bin.out  data8.bin  data.txt

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ file data8.bin 
data8.bin: ASCII text

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ cat data8.bin 
The password is FO5dwFsc0cbaIiH0h8J2eUks2vdTDwAn

bandit12@bandit:/tmp/tmp.okIsKk6VYG$ exit

$ ssh bandit13@bandit.labs.overthewire.org -p 2220
$ FO5dwFsc0cbaIiH0h8J2eUks2vdTDwAn
```
