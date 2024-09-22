# ZipZipZip
> Brighten up at last with the flag

## Tools Used
- python3

## Method
We start with a zip file called challenge.zip. When we unzip it, we are left with another zip file called chunk_0.zip. 
Unzipping this leaves us with chunk_1.zip and chunk_0.txt. 
This format continues, unzipping the nested zip files and getting their associated text files, over and over and over. 

Inspecting the text files, each one contains around 5 characters. 
Given the sheer number of zip files and tiny text files (and that the original zip file was around 7.5MB), 
my intuition tells me we're going to have to unzip all these files and combine the contents of the text files.

After doing this too many times to admit, I decided to let python take care of this heavy lifting for me:

```python3
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
                remove(current_zip)
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
```

Finally, after unarchiving some 35,000 files, combining their bytes and decoding from base64, it looks like the final product is a PNG image:

![out](https://github.com/user-attachments/assets/ab21591d-51e1-49dd-9155-6b29daad2cbd)

If we look in the bottom right corner, we can see the flag! (yay no steg!)

csawctf{ez_r3cur5iv3ne55_right7?}
