- This is a TLS CRIME challenge with a rot47 twist
- CRIME is a compression bug in TLS where if the user provides partial data that matches the web server, then it compresses the data and reflects such in the response size.
	- We can use this to sus out secret values from the web server, where if our guessed value is correct, the server responds with less data
### website contents
```
PZkgbg`3␙Hger␙^g`Z`^␙bg␙ma^␙\Zl^␙h_␙Z␙k^Ze␙^f^k`^g\r'␙Ghg&^ll^gmbZe␙nl^l␙h_␙ma^␙]blmk^ll␙lb`gZe␙Zk^␙Z␙\kbf^%␙Zg]␙Zee␙\kbf^l␙pbee␙[^␙mkZ\d^]␙]hpg␙Zg]␙i^kl^\nm^]␙bg␙ma^␙Fbedr␙PZr␙@ZeZqr␙M^kkZg␙Lnik^f^␙ 

BgbmbZmbg`␙l^
k^␙mkZglfbllbhg'''
>kkhk: AMMIL␙MkZglfbllbhg␙_Zbenk^
<Zimnk^]␙iZrehZ]3 FwMDAD72zk593N+XWnwQMAuR1QMQvhuSfZg8ye5iGCRuoIruUSuXR//XzUVrAb0QGh2fjgExttALFYljRa2TNJ6DqQ==


Rot 47 (offset 7):
Warning:␙Only␙engage␙in␙the␙case␙of␙a␙real␙emergency.␙Non-essential␙uses␙of␙the␙distress␙signal␙are␙a␙crime,␙and␙all␙crimes␙will␙be␙tracked␙down␙and␙persecuted␙in␙the␙Milky␙Way␙Galaxy␙Terran␙Supreme␙ 

Initiating␙se
re␙transmission...
ErrorA HTTPS␙Transmission␙failure
Captured␙payload: M~TKHK>9#r<@:U2_^u~XTH|Y8XTX}o|Zman?"l<pNJY|vPy|\Z|_Y66_#\]yHi7XNo9mqnL!{{HSM`sqYh9[UQ=KxXDD
```

### POST request response
```python
from base64 import b64decode as b64d

resp = "FwMDAD6fFMTxhXdAA+BCphJrw0jVVnlzqNVokmR6wsyonh0c6QEgiZKN15X0TUVbWWL2Sd2ay0BmKCmG2Ht8aRVPng=="
print(b64d(resp))
b'\x17\x03\x03\x00>\x9f\x14\xc4\xf1\x85w@\x03\xe0B\xa6\x12k\xc3H\xd5Vys\xa8\xd5h\x92dz\xc2\xcc\xa8\x9e\x1d\x1c\xe9\x01 \x89\x92\x8d\xd7\x95\xf4ME[Yb\xf6I\xdd\x9a\xcb@f()\x86\xd8{|i\x15O\x9e'
```

TLS records start with:
- **Content type (1 byte)**
	- `0x17` → Content type = **Application Data**    
- **Version (2 bytes)**
	- `0x03 0x03` → TLS version = **TLS 1.2**
	- **CRIME** attack is possible as TLS-level compression is enabled
- **Length (2 bytes)**
	- `0x00 0x3e` → Length = **62 bytes**
- **Payload (Length bytes)**

```python
#!/usr/bin/env python3

import requests
from base64 import b64decode as b64d


def post(data):
    data = {"data": data}
    r = requests.post(url, json=data)
    if r.status_code != 200:
        raise RuntimeError(f"Failed to retrieve {url} with {data}")
    ct_b64 = r.json()["ciphertext"]

    return b64d(ct_b64)


url = "http://localhost:21022/send"
known = "csawctf{"
known = "".join(chr(ord(c) - 7) for c in known)  
# once it's rot7'd itll become csawctf{
pad = "ç" * 10

guess = known
while True:
    for i in range(33, 127):  # printable chars
        payload = guess + chr(i) + pad
        control = guess + pad + chr(i)
		
        cmp_payload = post(payload)
        cmp_control = post(control)
		
        if len(cmp_control) > len(cmp_payload):
            guess += chr(i)
            print(f"Found {guess} | {''.join(chr(ord(c) + 7) for c in guess)}")
            break
    else:
        break
```
