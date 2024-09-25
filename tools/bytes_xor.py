def _stretch(a: bytes, newlen: int) -> bytes:
    new_a = []
    for idx in range(newlen):
        new_a.append(a[idx % len(a)])
    
    return bytes(new_a)

def _bytes_xor(a: bytes, b: bytes, quiet: bool=True, check_lens: bool=False, stretch: bool=False) -> bytes:
    if not quiet:
        print(f"{a}⊕  {b}")
    if check_lens and len(a) != len(b):
        raise ValueError("byte string lengths are unequal")
    if stretch:
        min_byte_len = min((len(a), len(b)))
        if min_byte_len == len(a):
            a = _stretch(a, len(b))
        else:
            b = _stretch(b, len(a))

    result = []
    for byte1, byte2 in zip(a, b):
        result.append(byte1 ^ byte2)

    return bytes(result)

def bytes_xor(*args: bytes, quiet: bool=True, check_lens: bool=False, stretch=False) -> bytes:
    if not len(args) > 0:
        raise ValueError("no byte strings passed in function argument")
    result = args[0]
    for arg in args[1:]:
        #keep XORing result and subsequent passed byte strings
        result = _bytes_xor(result, arg, quiet=quiet, check_lens=check_lens, stretch=stretch)
        if not quiet: print(f"{result=}")

    return result
