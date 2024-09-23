import soundfile as sf
import numpy as np
from scipy import fft

def decode_binary(binary_arr: list[int]) -> str:
    """Takes the array of binary numbers and decodes them to an ASCII string"""
    string_bin = []
    binary_arr = np.array(binary_arr)
    binary_arr.resize(len(binary_arr) // 8, 8)
    for arr in binary_arr:
        string_bin.append("".join([str(i) for i in arr]))

    return "".join(chr(int(i, 2)) for i in string_bin)

def decode_echo(part: np.ndarray, delays: tuple[int, int]) -> int:
    """Calculates the wav file partition's cepstrum and determines if a 1 or a 0 is encoded"""
    cepstrum = fft.ifft(np.log(np.abs(fft.fft(part))))

    delay_0, delay_1 = delays
    if cepstrum[delay_0 + 1] > cepstrum[delay_1 + 1]:
        return 0
    else:
        return 1

def solve(filename: str, partitions: int, flag_format: str) -> None:
    #reads the audio file as an array of floats
    signal, freq = sf.read(filename)

    #partitions the signal into equal sized windows (the amount of which defines how many bits will be decoded)
    window_size = len(signal) // partitions #let's hope there's nothing important in that lost trailing window!
    partitioned_signal = signal[:partitions*window_size].reshape((partitions, window_size))

    #brute-force the 0 and 1 bit delays
    for delay_1 in range(54, 59):
        for delay_0 in range(delay_1):
            print(f"0-bit delay: {delay_0: >3} | 1-bit delay: {delay_1: >3}", end="\r")
            delays = (delay_0, delay_1)
            binary_arr = []
            for part in partitioned_signal:
                binary_arr.append(decode_echo(part, delays))
            decoded_str = decode_binary(binary_arr)
            if flag_format in decoded_str: print(decoded_str)

if __name__ == "__main__":
    #Getting context for our delays:
    #signal / (freq * partitions) -> ~0.350 sec for each partition
    #0.350 / window_size -> 0.020833 msec between each array element
    #every 48 or so elements in our array make up 1 msec

    filename = "256.wav"
    partitions = 256
    flag_format = "csawctf{"
    solve(filename, partitions, flag_format)
  
