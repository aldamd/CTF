# The Triple Illusion
> Some things are hidden in plain sight. Use your knowledge of forensics and crypto to solve the challenge

## Tools
- zsteg
- cyberchef
- python3

## Method
When you see a .png file in a CTF, your success is in the hands of zsteg. I don't make the rules. Running $zsteg on the 3 given png files gives us the following (after some cleanup):
```shell
[.] datavsmetadata.png
meta Comment        .. text: " Can you crack my secret? Here's a list of numbers: See what they reveal. 0 0 0 0 0 0 0 0 15 23 23 4 7 0 22 23 29 25 0 18 10 12 0 7 23 2 17 18 21 16 0 0 0 0 0 28 7 16 17 16 6 17 11 0 1 0 21 23 4 24 0 0 0 0 0 0"
                    .. 
[.] hibiscus.png
b1,rgb,lsb,xy       .. text: "ekasemk{oiiik_axiu_xsu_gieiwem_moi_nmivrxks_tmklec_ypxz}"
                    .. 
[.] roses.png
b1,rgb,lsb,xy       .. text: "csawctf{heres_akey_now_decrypt_the_vigenere_cipher_text} "
```

Alright well it looks like we're dealing with a vigenere cipher (Caesar cipher on protein powder) and we're given both the key and the cipher text which saves us the trouble of doing statistical black magic.
Running our key and ciphertext through cyberchef we come out with the cleartext:

csawctf{heres_anew_key_decrypt_the_secretto_reveal_flag}

The challenge hints at using both forensics (stego) and crypto, and we're given a bunch of (what I assume to be) decimal numbers. It may or may not also be a coincidence that we're given 56 numbers and our newly decrypted key has 56 characters. Let's start with some xor'ing and pray we don't need to go further.

Cobbling together a quick python script:
```python3
nums = "0 0 0 0 0 0 0 0 15 23 23 4 7 0 22 23 29 25 0 18 10 12 0 7 23 2 17 18 21 16 0 0 0 0 0 28 7 16 17 16 6 17 11 0 1 0 21 23 4 24 0 0 0 0 0 0"
nums = [int(i) for i in nums.split()]
msg = r"csawctf{heres_anew_key_decrypt_the_secretto_reveal_flag}"

xor_msg = ""
for idx in range(len(nums)):
    xor_msg += chr(ord(msg[idx]) ^ nums[idx])

print(xor_msg)
```
we almost get the flag: csawctf{great_wyxn_you_cracked_the_obscured_secret_flag}.
Sometimes corruptions happen. With my insurmountable wordle experience, I'm able to deduce that wyxn should probably instead be "work" in this context. And with that, we get an acceptable flag!!

csawctf{great_work_you_cracked_the_obscured_secret_flag}
