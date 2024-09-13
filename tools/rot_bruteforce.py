from sys import argv

def ROTBruteforce(string: str) -> None:
    ALPHABET_LEN = 26
    decrypted_strs = ""
    for i in range(ALPHABET_LEN):
        decrypted_str = ""
        for c in string:
            ord_c = ord(c)
            offset = -1
            if ord_c >= ord('a') and ord_c <= ord('z'):
                offset = ord('a')
            elif ord_c >= ord('A') and ord_c <= ord('Z'):
                offset = ord('A')
            
            if offset == -1:
                decrypted_str += c
            else:
                decrypted_str += chr(offset + ((ord_c - offset + i) % ALPHABET_LEN))

        decrypted_strs += f"{i: <4}{decrypted_str}"
        if i < ALPHABET_LEN - 1:
            decrypted_strs += "\n"

    print(decrypted_strs)

if __name__ == "__main__":
    args = argv
    if len(args) < 2:
        print("Invalid usage. Please supply a ROT encrypted string.")
    else:
        string = " ".join(args[1:])
        ROTBruteforce(string)
