# Diving into null
> Do you really know *nix?
## Tools
- ghidra
- ltrace
## Method
We start with a file called chal:
```shell
$ file chal 
chal: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked,
interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=cdd6291c1aee585a91dd6628aa7b3ac0ed815ae1,
for GNU/Linux 3.2.0, with debug_info, not stripped
```
not stripped!

Popping it open in Ghidra and zip zap zooming to the main function, we can immediately tell this was written in C++ with all that std::string nonsense. 
I did a fair bit of reverse engineering on this, here're the bountiful fruits of my labor: 

```c
undefined8 main(void)

{
  bool beginning_NE_end;
  char basic_ios_good;
  int comparison;
  allocator *allocator_ptr;
  char *char_ptr;
  ulong string_size;
  basic_ostream *ostream_ptr;
  long in_FS_OFFSET;
  int char_sum;
  int one;
  undefined8 str_beginning;
  undefined8 str_end;
  basic_string<> *local_278;
  undefined8 *str_end_addr;
  basic_string input [32];
  basic_string<> flag_buffer [535];
  allocator allocator_val;
  long canary_;
  
  canary_ = *(long *)(in_FS_OFFSET + 0x28);
  std::__cxx11::basic_string<>::basic_string();
  std::operator<<((basic_ostream *)std::cout,"Tell me what you know about *nix philosophies: ");
  std::operator>>((basic_istream *)std::cin,input);
  char_sum = 0;
  one = 1;
  while( true ) {
                    /* make sure input is more than 1 char */
    string_size = std::__cxx11::basic_string<>::size();
    if (string_size <= (ulong)(long)one) break;
    allocator_ptr = (allocator *)std::__cxx11::basic_string<>::operator[]((ulong)input);
    allocator_val = *allocator_ptr;
    str_end_addr = &str_end;
    std::__cxx11::basic_string<>::basic_string((initializer_list)flag_buffer,&allocator_val);
    std::__new_allocator<char>::~__new_allocator((__new_allocator<char> *)&str_end);
    /* who invited this guy */
    local_278 = flag_buffer;
    str_beginning = std::__cxx11::basic_string<>::begin();
    str_end = std::__cxx11::basic_string<>::end();
    while( true ) {
      /* check that we don't escape the string buffer? Iterator syntax garbage */
      beginning_NE_end =
           __gnu_cxx::operator!=((__normal_iterator *)&str_beginning,(__normal_iterator *)&str_end);
      if (!beginning_NE_end) break;
      char_ptr = (char *)__gnu_cxx::__normal_iterator<>::operator*
                                   ((__normal_iterator<> *)&str_beginning);
      char_sum = char_sum + *char_ptr;
      /* progress the iterator? Does so by incrementing the str_beginning address methinks */
      __gnu_cxx::__normal_iterator<>::operator++((__normal_iterator<> *)&str_beginning);
    }
    /* deconstructor? */
    std::__cxx11::basic_string<>::~basic_string(flag_buffer);
    one = one + 1;
  }
                    /* char_sum + -0x643 as the read address? */
  read(char_sum + -0x643,buf,0x20);
  comparison = strcmp("make every program a filter\n",buf);
                    /* check succeeded */
  if (comparison == 0) {
    /* load the flag.txt file (0x102055 is the memory address of "flag.txt" in the data section of the binary) */
    std::basic_ifstream<>::basic_ifstream((char *)flag_buffer,0x102055);
    basic_ios_good = std::basic_ios<>::good();
    /* the lengths C++ has to go to match a fraction of python's file.read() /j */
    if (basic_ios_good == '\0') {
      ostream_ptr = (basic_ostream *)
                    std::basic_ostream<>::operator<<((basic_ostream<> *)std::cout,std::endl<>);
      ostream_ptr = std::operator<<(ostream_ptr,"flag.txt: No such file or directory");
      std::basic_ostream<>::operator<<((basic_ostream<> *)ostream_ptr,std::endl<>);
      ostream_ptr = std::operator<<((basic_ostream *)std::cout,
                                    "If you\'re running this locally, then running it on the remote server should give you the flag!"
                                   );
      std::basic_ostream<>::operator<<((basic_ostream<> *)ostream_ptr,std::endl<>);
    }
    else {
      ostream_ptr = (basic_ostream *)
                    std::basic_ostream<>::operator<<((basic_ostream<> *)std::cout,std::endl<>);
      ostream_ptr = std::operator<<(ostream_ptr,"Welcome to pwning ^_^");
      std::basic_ostream<>::operator<<((basic_ostream<> *)ostream_ptr,std::endl<>);
      system("/bin/cat flag.txt");
    }
    std::basic_ifstream<>::~basic_ifstream((basic_ifstream<> *)flag_buffer);
  }
  else {
                    /* failed_check */
    ostream_ptr = std::operator<<((basic_ostream *)std::cout,
                                  "You still lack knowledge about *nix sorry");
    std::basic_ostream<>::operator<<((basic_ostream<> *)ostream_ptr,std::endl<>);
  }
  std::__cxx11::basic_string<>::~basic_string((basic_string<> *)input);
  if (canary_ != *(long *)(in_FS_OFFSET + 0x28)) {
                    /* WARNING: Subroutine does not return */
    __stack_chk_fail();
  }
  return 0;
}
```
a lot of it is C++ iterator and file stream logic, but the chunk we're really interested in is this one:
```c
    while( true ) {
      /* check that we don't escape the string buffer? Iterator syntax garbage */
      beginning_NE_end =
           __gnu_cxx::operator!=((__normal_iterator *)&str_beginning,(__normal_iterator *)&str_end);
      if (!beginning_NE_end) break;
      char_ptr = (char *)__gnu_cxx::__normal_iterator<>::operator*
                                   ((__normal_iterator<> *)&str_beginning);
      char_sum = char_sum + *char_ptr;
      /* increment the iterator? Does so by incrementing the str_beginning address methinks */
      __gnu_cxx::__normal_iterator<>::operator++((__normal_iterator<> *)&str_beginning);
    }
    /* deconstructor? */
    std::__cxx11::basic_string<>::~basic_string(flag_buffer);
    one = one + 1;
  }
                    /* char_sum + -0x643 as the read address? */
  read(char_sum + -0x643,buf,0x20);
  comparison = strcmp("make every program a filter\n",buf);
                    /* check succeeded */
  if (comparison == 0) {
    /* load the flag.txt file (0x102055 is the memory address of "flag.txt" in the data section of the binary) */
````
Understanding this bit requires knowledge of the C++ iterators, but long story short, the code takes our input 
and goes character-by-character adding them together; we're getting the running total (cumsum lol) of the characters in our input.

We then have a read() call on our running total - 0x643. The first argument in read() is the file descriptor, meaning that if we get it to 0, read will use standard input. 
Also notice the ```buf,0x20``` bit, it looks like only the first 0x20 (32) chars are considered.
We then have a strcmp() call with ```"make every program a filter\n"``` and our ```buf``` buffer.

The first 32 characters of our input, therefore, have to have a hex total of 0x643 (1603). We can throw together a fast and dirty python script to generate a bunch of valid strings:
```python3
from random import choice
from string import ascii_letters

goal = 0x643
valid_chars = list(ascii_letters) + list("0123456789")
valid_strs = []
while len(valid_strs) < 10:
    valid_str = ""
    cumsum = 0
    for _ in range(20):
        char = choice(valid_chars)
        cumsum += ord(char)
        valid_str += char
        if cumsum == goal:
            valid_strs.append(valid_str)
            break

print("\n".join(valid_strs))
```

```shell
$ python3 solve.py
DfZbUnHn7mxg7IlPMX
lsl6ykxfNqe0cmgu
oGyh57CypfqHlAXmN5
3gPHvUAeaw5FkyeIyB
0Xr7gX5QvfdglK4rfc
6LM2pNrJQVcalypgHY
nmsQKzGqxqU4mkcz
LRsIoRuUkBphE5OsTI
PJJ9nmUTXg6YILMgYnD
m12ljknf0vHtdYNXGR
```

let's pop one of these in the binary and see what happens:
```shell
$ ./chal 
Tell me what you know about *nix philosophies: m12ljknf0vHtdYNXGR
You still lack knowledge about *nix sorry
```
what the hell? I thought I had this one. I knew I should've hightailed it out when I saw the C++ syntax. Let's see what ltrace has to say about our input:

```shell
$ ltrace ./chal
[...]
_ZStrsIcSt11char_traitsIcESaIcEERSt13basic_istreamIT_T0_ES7_RNSt7__cxx1112basic_stringIS4_S5_T1_EE(0x55f2a1f951e0, 0x7ffee33f9760, 0x7f06e7811390,
1024Tell me what you know about *nix philosophies: m12ljknf0vHtdYNXGR
[...]
read(-109 <no return ...>
error: maximum array length seems negative
, "", 32)
```
All the garbage aside, it looks like when our input is "m12ljknf0vHtdYNXGR" we were off on our ```char_sum - 0x643``` by 109, or 'm'. 

Repeating the same for the string "DfZbUnHn7mxg7IlPMX" we end up being off by 68, or D.
Alright I think I know what's happening here, looks like the first letter of our input isn't being considered for the running total. 

Let's try this again with a garbage first character:
```shell
$ ./chal 
Tell me what you know about *nix philosophies: _m12ljknf0vHtdYNXGR
```
oh something new, looks like we're getting another prompt for input! Let's give it the strcmp value:
```shell
$ ./chal 
Tell me what you know about *nix philosophies: _m12ljknf0vHtdYNXGR
make every program a filter

Welcome to pwning ^_^
csawctf{-3v3ry7h1ng_15_4_f1l3}
```

Easy as that!
