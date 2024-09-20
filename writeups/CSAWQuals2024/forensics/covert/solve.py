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
