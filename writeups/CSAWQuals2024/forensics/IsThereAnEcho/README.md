# Is There An Echo
> Maybe next time you should record your music in an acoustically treated space.

## Tools
- spek
- Audacity
- python3

## Method
We're given an audio file, 256.wav. The first thing we do is check metadata information with $exiftool which gives us nothing. 
We can check the spectrograph of the wav file with $spek to see if there are any hidden images

![256 wav](https://github.com/user-attachments/assets/258fdd69-7e9d-4c4b-bd58-d230547852c0)

Nothing. There's always our trusty $strings
```shell
> Q P D 
!	F	k	
	-	@	
cepstral domain single echo
```

Interesting. Looking up "cepstral domain single echo" points us to a couple scholarly articles that make references to audio watermarking and echo hiding.
Following up with echo hiding, we're directed to a useful [powerpoint by Jeff England](https://www.ee.columbia.edu/~ywang/MSS/Project/Jeff_England_Audio_Steganography.ppt).

### Echo Hiding Logic

To explain it as simply as possible, to echo hide data, the audio signal is divided into multiple windows. Two delays are chosen to encode the hidden data: one for a binary 0 and another for a binary 1.
I'm not too well-versed in audio signaling but an FIR filter is apparently utilized to delay the audio signal, the original signal is filtered through both binary one and binary zero filters, and a mixer
signal containing ramping functions is used for the encoding. But we're not too interested in the encoding, how do we break this apart?

The key in decoding the flag is to find the delay before the echo. In order to do that, we first need to find the "cepstrum" of the encoded signal which is a fancy term for taking the logarithm of the
estimated signal spectrum and computing the inverse Fourier transform. This challenge is dragging me, kicking and screaming, back into differential equations. 

Luckily, most of the hard work has already been done by the giants whose shoulders I'm making sore. The equation for calculating the cepstrum is as follows:

![image](https://github.com/user-attachments/assets/24aa4815-2253-4bee-9a0f-0552309ab187)

where $C$ is the cepstrum, $f(t)$ is the signal, $\log$ is the natural logarithm, $\mathcal F$ is the Fourier transform, and $\mathcal F^{-1}$ is the inverse Fourier transform.

To sum it all up we need to:
- Partition the signal data into little windows
- Compute the cepstrum of each window
- Determine if the binary 0 delay or the binary 1 delay is currently being used (which tells us if the data is encoded binary 0 or binary 1)
- Convert the decoded binary to ascii

The question now becomes: how do we determine the size for our segmented data, and what are the 0 and 1 delays? 
Given that the name of our wav file is 256, we can hope that 256 bits will be a good enough size for our signal data partitions.

### Solver Script

Before we go into finding the location of the delays, let's see how that information will fit into our python script:

```python3
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
```

In order to find the delays, we can analyze the audio file using Audacity's Frequency Analysis window and utilizing the Cepstrum algorithm:
![image](https://github.com/user-attachments/assets/0a12a42d-c851-490a-9acc-18e58f27106b)

As we can see, there are peaks about the 0.001 and 0.0012 second marks. 
In the above python code, we know that there are approximately 0.020833 milliseconds between each element of our partitioned array.
In order to find the index location of our juicy delays, we can simply do 

```shell
(0.0012 * 1000) / 0.020833
```

which gives us ~58, hence the for loop iterates until 59.

Running the python script, we get a variety of flag permutations but eventually one sticks!

csawctf{1nv3st_1n_s0undpr00f1ng}


