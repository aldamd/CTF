from sys import argv

def vigenereEncrypt(plain_text: str, key: str) -> str:
    ALPHABET_LEN = 26

    encrypted_str = ""
    for i in range(len(plain_text)):
        plain_char = plain_text[i]
        key_char = key[i % len(key)]

        plain_ord = ord(plain_char)
        offset = -1
        if plain_ord >= ord('a') and plain_ord <= ord('z'):
            offset = ord('a')
        elif plain_ord >= ord('A') and plain_ord <= ord('Z'):
            offset = ord('A')

        if offset == -1:
            cipher_char = plain_char
        else:
            cipher_char = chr(offset + ((plain_ord + ord(key_char) - (2 * offset)) % ALPHABET_LEN))

        encrypted_str += cipher_char

    return encrypted_str

if __name__ == "__main__":
    if len(argv) != 3:
        print("Usage: python3 vigenere_cipher.py message key")
    else:
        plain_text, key = argv[1:]
        print(vigenereEncrypt(plain_text, key))
