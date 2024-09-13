from sys import argv

def railfenceEncrypt(message: str, num_rows: int, offset: int) -> str:
    rows = [""] * num_rows
    rev = False
    bounce = 0
    for i in range(len(message)):
        if not rev:
            current_idx = (i + bounce + offset) % num_rows
        else:
            current_idx = num_rows - 2 - ((i + bounce + offset) % num_rows)
        
        current_row = rows[current_idx]
        padding = " " * (i - len(current_row))
        rows[current_idx] = current_row + padding + message[i]

        if not rev and current_idx == num_rows - 1:
            rev = True
        elif rev and current_idx == 0:
            rev = False
            bounce += 2

    print("\n".join(rows))

    encrypted_str = ""
    for row in rows:
        encrypted_str += "".join(row.split())
    
    print("\n" + encrypted_str)
    return encrypted_str
        
if __name__ == "__main__":
    if len(argv) < 3 or len(argv) > 4:
        print("Usage: python3 railfence.py message num_rows [offset]")
    else:
        if len(argv) == 3:
            message, num_rows = argv[1:]
            offset = 0
        else:
            message, num_rows, offset = argv[1:]

        encrypted_str = railfenceEncrypt(message, int(num_rows), int(offset))
