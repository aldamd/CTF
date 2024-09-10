import base64 as b64
import numpy as np
from tqdm import tqdm

def single_byte_xor(input_str: str, flag_format: str, encoded: bool=True) -> None:
    if encoded:
        input_str = b64.b64decode(input_str)

    input_str_arr = np.array(list(input_str))
    input_str_arr = input_str_arr.reshape(1, -1)

    byte_arr = np.arange(256).reshape(-1, 1)

    xor_strings = np.bitwise_xor(byte_arr, input_str_arr)
    for i in tqdm(range(len(xor_strings))):
        xor_string = xor_strings[i]
        try:
            xor_string = ''.join([chr(byte) for byte in xor_string])
        except ValueError:
            continue
        if flag_format in xor_string:
            print(xor_string)
            break

if __name__ == "__main__":
    encoded_str = "IConIT0xdSoldit1GTJ2GTIudRkxdigidTQgMyoZMXY0KiIZdiAZJTQ/NjJ2Zzs="
    flag_format = "flag{"
    single_byte_xor(encoded_str, flag_format, encoded=True)
