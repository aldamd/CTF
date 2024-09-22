# I Like My Camera RAW
## Tools used
- gpg
- zsteg
- exiftool
- .RAF to .JPG

## Method
We're thrust into this challenge with 3 files, DSCF3911.RAF, message.txt.gpg, and secret.png. Below are my results using $file:
```shell
DSCF3911.RAF:    Fujifilm RAF raw image data, format version 0201, camera X-H1
message.txt.gpg: PGP symmetric key encrypted data - AES with 256-bit key salted & iterated - SHA256 .
secret.png:      PNG image data, 1200 x 1200, 8-bit/color RGB, non-interlaced
```

Using $gpg to decrypt the message prompts us for a password so I guess we'll table that for now.
Since we're working with a (secret.)png file my stegonography alarms are going off, so let's see what $zsteg has to say:

```shell
imagedata           .. text: "===,-,\t\t\t"
b1,bgr,lsb,xy       .. text: "m a big, bold ad, a flashy show,\nAbove a brick wall, red as a pale tomato.\nSpillin"
b3,g,lsb,xy         .. file: GLS_BINARY_MSB_FIRST
b4,g,msb,xy         .. file: GTA audio index data (SDT)
```

"[I']m a big, bold ad, a flashy show,
Above a brick wall, red as a pale tomato.
Spillin[...]"
Alright, I guess we're looking out for big, bold, red ads.

I looked into viewing the .RAF file but I couldn't natively open it and I didn't feel like downloading third party software or converting it to another format.
Instead I used an online .RAF to .JPG converter! They didn't ask for credit card information so this was a win:

![image](https://github.com/user-attachments/assets/78ea8829-2d9d-4d86-b8ec-d20f11de5f0c)

I guess that red billboard could be our "flashy show".
Let's see what else the file can tell us through metadata with $exiftool.
167 lines! The item that pops out most is:
```shell
Location Shown Sublocation      : 40.7043749, -73.9903311
```
Location data is always juicy! Let's see if we can reproduce this shot on google street view.

The answer was not really!! Don't get me wrong, it's a beautiful photo, but the combination of elevation changes and the filters gave my peanut brain a hard time trying to reproduce.
However, while virtually standing at the coordinates, I did see a building above the aforementioned "brick wall" that looks somewhat similar to the red shining building on the left in the photo.

So like a wild dog, I started running through the Google Streets™, chasing down the address of what looked to be the red shining building until I found 60 Water Street (I guess that could be our Spillin[...] hint). Some Google searching and a Wikipedia page later, I found a close-up shot of the advertisement above with a phone number.

Slapping the phone number into our password-protected pgp key seemed to do the trick!
```shell
gpg: AES256.CFB encrypted data
gpg: encrypted with 1 passphrase
csawctf{1_kN0w_Y0U_l1k3_1T_R4W}
```
