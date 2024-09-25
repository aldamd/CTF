def _bytes_xor(a: bytes, b: bytes, quiet: bool=True, check_lens: bool=False, stretch: bool=False) -> bytes:
    if not quiet:
        print(f"{a}⊕  {b}")
    if check_lens and len(a) != len(b):
        raise ValueError("byte string lengths are unequal")
    result = []
    for byte1, byte2 in zip(a, b):
        result.append(byte1 ^ byte2)

    return bytes(result)

def bytes_xor(*args: bytes, quiet: bool=True, check_lens: bool=False) -> bytes:
    if not len(args) > 0:
        raise ValueError("no byte strings passed in function argument")
    result = args[0]
    for arg in args[1:]:
        #keep XORing result and subsequent passed byte strings
        result = _bytes_xor(result, arg, quiet=quiet, check_lens=check_lens)
        if not quiet: print(f"{result=}")

    return result

