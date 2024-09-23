# Is There An Echo
> Maybe next time you should record your music in an acoustically treated space.

## Tools
- spek

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

To explain it as simply as possible, to echo hide data, the audio signal is divided into multiple windows. Two delays are chosen to encode the hidden data: one for a binary 0 and another for a binary 1.
I'm not too well-versed in audio signaling but an FIR filter is apparently utilized to delay the audio signal, the original signal is filtered through both binary one and binary zero filters, and a mixer
signal containing ramping functions is used for the encoding. But we're not too interested in the encoding, how do we break this apart?

The key in decoding the flag is to find the delay before the echo. In order to do that, we first need to find the "cepstrum" of the encoded signal which is a fancy term for taking the logarithm of the
estimated signal spectrum and computing the inverse Fourier transform. This challenge is dragging me, kicking and screaming, back into differential equations. 

Luckily, most of the hard work has already been done by the giants whose shoulders I'm making sore. The equation for calculating the cepstrum is as follows:

![image](https://github.com/user-attachments/assets/24aa4815-2253-4bee-9a0f-0552309ab187)

where $C$ is the cepstrum, $f(t)$ is the signal, the $\mathcal F$ is the Fourier transform, and $\mathcal F^{-1}$ is the inverse Fourier transform.

To sum it all up we need to:
- Segment the signal data into little windows
- Compute the cepstrum of each window
- Determine if the binary 0 delay or the binary 1 delay is currently being used (which tells us if the data is encoded binary 0 or binary 1)
- Convert the decoded binary to ascii

The question now becomes how do we determine the size for our segmented data, and what are the 0 and 1 delays? 
Given that the name of our wav file is 256, we can hope that 256 bits will be a good enough size.
According to the aforementioned powerpoint, the max delay before the echo becomes perceivable is 1ms, so for now that will be our maximum.

Plugging this all into python:

```python3
print("Stop looking through the history, you're making me embarrassed!")
```


