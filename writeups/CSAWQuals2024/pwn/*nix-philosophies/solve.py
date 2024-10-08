from random import choice
from string import ascii_letters

goal = 0x643
valid_chars = list(ascii_letters) + list("0123456789")
valid_strs = []
while len(valid_strs) < 10:
    valid_str = ""
    cumsum = 0
    for _ in range(20):
        char = choice(valid_chars)
        cumsum += ord(char)
        valid_str += char
        if cumsum == goal:
            valid_strs.append(valid_str)
            break

print("\n".join(valid_strs))
