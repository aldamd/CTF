# stack4
## Tools
- gdb (gef)
## Recon
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
## Method
```
