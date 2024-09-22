from zipfile import ZipFile
from os import remove
from base64 import b64decode #when in doubt try base64

def nestedUnzip(first_zip: str, file_ext_oi: str) -> None:
    with ZipFile(first_zip) as zf:
        zipfiles = [i for i in zf.namelist() if ".zip" in i]
        if zipfiles:
            zf.extract(zipfiles[0])
        else:
            exit(f"No zipfiles found in first zipfile: {first_zip}")

    current_zip = zipfiles[0]
    contents = b""
    file_count = 0
    while True:
        with ZipFile(current_zip) as zf:
            filenames = zf.namelist()
            zipfiles = [i for i in filenames if ".zip" in i]
            txtfiles = [i for i in filenames if file_ext_oi in i]
            for txtfile in txtfiles:
                file_count += 1
                print(txtfile, end="\r")
                with zf.open(txtfile) as tf:
                    contents += tf.read()

            if zipfiles:
                zf.extract(zipfiles[0])
                os.remove(current_zip)
                current_zip = zipfiles[0]
            else:
                break

    print(f"Found {file_count} {file_ext_oi} files")
    remove(current_zip)
    with open("outfile", "wb") as wb:
        wb.write(b64decode(contents))
    print("Contents written to 'outfile'")

if __name__ == "__main__":
    first_zip = "challenge.zip"
    file_ext_oi = ".txt" #file extension of interest
    nestedUnzip(first_zip, file_ext_oi)
    
