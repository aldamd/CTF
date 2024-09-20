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

    #key has length of 2, so let's brute force from 10 to 99
    for idx in range(10, 100):
        str_ = ""
        for ip_id_hex in ip_ids_hex:
            #convert hex str ip_id_hex to decimal number ip_id_dec
            ip_id_dec = int(ip_id_hex, 16)
            #we're working with factors of idx, ensure that ip_id is divisible by idx
            if ip_id_dec % idx == 0:
                str_ += chr(ip_id_dec // idx)
            else: continue
        if flag_format in str_: 
            print(str_)
            break
    
    return str_

if __name__ == "__main__":
    packets_of_interest = list(range(256, 306))
    flag_format = "csawctf{"
    keylog_file = "keys.log"
    flag = IPidTCPCovertChannel(packets_of_interest, flag_format, keylog_file=keylog_file)
