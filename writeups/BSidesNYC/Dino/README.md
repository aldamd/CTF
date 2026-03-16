- This challenge had a bunch of really gross XOR and summation validation garbage stuff so I decided to use angr
	- If we let angr run as normal, it would explode through a lot of the symbolic execution so we had to leverage DFS
	- We could also pretty easily tell that the flag length had to be 14 bytes long
### solve
```python
#!/usr/bin/env python
# coding: utf-8
import angr
import claripy
import logging

logging.getLogger("angr.sim_manager").setLevel(logging.DEBUG)

exe = "./dino"
input_len = 14

p = angr.Project(exe, auto_load_libs=True)

flag_chars = [claripy.BVS("flag_%d" % i, 8) for i in range(input_len)]
flag = claripy.Concat(*flag_chars + [claripy.BVV(b"\n")])

st = p.factory.full_init_state(args=[exe], add_options=angr.options.unicorn, stdin=flag)

# constrain to ascii-only characters
for k in flag_chars:
    st.solver.add(k < 0x7F)
    st.solver.add(k > 0x20)

sm = p.factory.simulation_manager(st)
sm.use_technique(angr.exploration_techniques.DFS())
while sm.active:
    sm.run(n=20)
    if sm.deadended:
        for x in sm.deadended:
            if b"released" in x.posix.dumps(1):
                print(f"Winning input: {x.posix.dumps(0)}")
                exit()
        sm.drop(stash="deadended")
```


