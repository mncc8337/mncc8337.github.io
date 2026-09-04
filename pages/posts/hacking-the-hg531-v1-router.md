---
title: Hacking the HG531 V1 router
description: Forcing an router to do something else is weird.
creation_date: 05 Sep 2026 01:13
---
Today I found an old gateway lying in my pile of trashs. It is a rebranded Huawei HG531 V1 that came with ISP's custom hardware (I think this is the one they gave to their subscribers for free when register for their services.). It can only handle 300mbps, and use ADSL instead of the modern FTTH. Despite being old, I can probably use it as an cheap and slow router by configuring via its web interface. But since I don't really need an router, I figured out that i should flash a custom firmware so that it could do something else (like [running GTA Vice City](https://www.youtube.com/watch?v=bcjuoEZg8rI) on it? Probably not possible but I might *find something else*).

Opening the case, I saw 5 holes that perfectly fit a row of 4 header pins, which I suspected to be UART (though UART needs only 4 pins, there are only 2 posibilities which are UART and JTAG; and JTAG required more than 5 pins so here we are). There is one left out pin, which my used to reset the board. Anyway, identifying UART pins is simple. First find the GND (check continuity with shield, big metal pads and so on)

The first thing to do is finding the original Huawei hardware. Most of these ISP free gateways come with locked down firmware, preventing us to do more advance stuff. The gateway seems popular in the arabic world, I can't understand most of the search result. However, there is a [github link](https://github.com/DarkWarrior0x/HG531-Fix) that lead me to a [google drive](https://drive.google.com/file/d/1KCeQnylt9tRnHTfVtvT9MlWepUiw959d/view) containing the *supposed* to be original firmware ([mirror](/posts/hacking-the-hg531-v1-router/HG531V1_Firmware.rar)). This archive seems to be taken from [an arabic forum](https://masrawysat.com/vb/showthread.php?s=c92b1c736311c5adae079638aba48360&t=3193037), though I can't verify because it required me to register an account in order to download the file. [^1]

There is also a [youtube video](https://www.youtube.com/watch?v=aEsYrvOd00Y) containing [a link](https://top4top.io/downloadf-1444me6um1-rar.html) to a firmware and a multicast flashing software (though the firmware version is differ from what I found on the github) ([mirror](/posts/hacking-the-hg531-v1-router/hg531tedta.rar)).
> notice: flashing a random firmware from the internet is risky, i am doing this with my own risk.

The firmware is easily flashed by using the "Firmware update" feature on its web interface. But there is a chance that I will brick my device because of corrupted firmware or anything like that, so I need to dump the current firmware first. Fortunately, the bootloader is not locked and you can open the boot commandline by spamming <kbd>escape</kbd> on the first few seconds of powering on. Use `help` and `info`, I got the firmware start address and firmware size, which is then used with the `d` command to dump all of them to the serial output.

After flashing the firmware, I did not notice any changes of the web interface or anything.

## Modding the firmware
The idea is simple:
- `binwalk` to see content of the bin and extract
- `firmware-mod-kit` to repack
binwalk result shows that it got a squashfs 3.0 image, and 2 LZMA images:
```sh
[mncc@laplap fpt-router-hacking ]$ binwalk huawei.bin

                            /home/mncc/Desktop/fpt-router-hacking/huawei.bin
---------------------------------------------------------------------------------------------------------
DECIMAL                            HEXADECIMAL                        DESCRIPTION
---------------------------------------------------------------------------------------------------------
24608                              0x6020                             LZMA compressed data, properties:
                                                                      0x5D, dictionary size: 33554432
                                                                      bytes, compressed size: 39898
                                                                      bytes, uncompressed size: 109576
                                                                      bytes
196608                             0x30000                            SquashFS file system, big endian,
                                                                      version: 3.0, compression:
                                                                      unknown, inode count: 195, block
                                                                      size: 65536, image size: 2090286
                                                                      bytes, created: 2014-08-20
                                                                      04:33:08
2289728                            0x22F040                           LZMA compressed data, properties:
                                                                      0x5D, dictionary size: 33554432
                                                                      bytes, compressed size: 1218728
                                                                      bytes, uncompressed size: 3906736
                                                                      bytes
---------------------------------------------------------------------------------------------------------

Analyzed 1 file for 85 file signatures (187 magic patterns) in 95.0 milliseconds
[mncc@laplap fpt-router-hacking ]$
```
Then I extract the 3 parts using `binwalk -e`. This is the content of the squasfs:
```sh
[mncc@laplap fpt-router-hacking ]$ tree extractions/huawei.bin.extracted/30000
extractions/huawei.bin.extracted/30000
└── squashfs-root
    ├── bin
    │   ├── adslcmd
    │   ├── adslctrl
    │   ├── ash -> busybox
...
    │   ├── startbsp
    │   ├── swapdev
...
    │   └── zebra
    ├── dev
    ├── etc
    │   ├── adsl
    │   ├── bootfile.txt
    │   ├── create_db.sql
    │   ├── defaultcfg.xml
    │   ├── dhcps2.leases -> /var/dhcp/dhcps/leasesF
    │   ├── dhcps.conf -> /var/dhcp/dhcps/config
    │   ├── dhcps.leases -> /var/dhcp/dhcps/leases
    │   ├── ethertypes
    │   ├── group -> /var/group
    │   ├── handy_dss_key
    │   ├── handy_rsa_key
    │   ├── inetd.conf
    │   ├── init.d
    │   │   └── rcS
    │   ├── inittab
    │   ├── passwd -> /var/passwd
    │   ├── profile
    │   ├── resolv.conf -> /var/dns/resolv.conf
    │   ├── root.pem
    │   ├── rsa_host_key
...
    │   └── wscd.conf
    ├── init -> bin/busybox
    ├── lib
    │   ├── ld-uClibc.so.0
...
    │   └── libz.so.1 -> libz.so
    ├── mnt
    ├── proc
    ├── sbin
    │   ├── arp -> ../bin/busybox
...
    │   └── vconfig -> ../bin/busybox
    ├── tmp
    ├── usr
    │   ├── bin
    │   │   ├── [ -> ../../bin/busybox
...
    │   │   └── wget -> ../../bin/busybox
    │   └── rtl8192su
    │       ├── AGC_TAB.txt
...
    │       └── rtl8192sfw.bin
    └── var
        └── Wireless

18 directories, 176 files
[mncc@laplap fpt-router-hacking ]$
```

There are some interesting files. `/etc/inittab` is [a config file for the init process](https://www.ibm.com/docs/en/aix/7.3.0?topic=files-inittab-file)
```sh
[mncc@laplap fpt-router-hacking ]$ cat extractions/huawei.bin.extracted/30000/squashfs-root/etc/inittab
::sysinit:/etc/init.d/rcS
::respawn:-/bin/sh

# tty2::askfirst:-/bin/sh
#::ctrlaltdel:/bin/umount -a -r

[mncc@laplap fpt-router-hacking ]$
```

By default the router run the `rcS` script and then respawn a login shell. Looking at `rcS` and `profile`
```sh
[mncc@laplap fpt-router-hacking ]$ cat extractions/huawei.bin.extracted/30000/squashfs-root/etc/init.d/rcS
#!/bin/sh
/bin/echo "rcs"
PATH=/sbin:/bin:/usr/bin:/usr/sbin
export PATH

echo "RCS DONE"

[mncc@laplap fpt-router-hacking ]$
```
```sh
[mncc@laplap fpt-router-hacking ]$ cat extractions/huawei.bin.extracted/30000/squashfs-root/etc/profile
# /etc/profile: system-wide .profile file for the Bourne shells

PATH=/bin:/sbin:/usr/bin
export PATH

swapdev
startbsp
echo 32  > /proc/sys/kernel/msgmni

test -e /bin/atserver && atserver &
test -e /bin/usbdiagd && usbdiagd &

 echo "Loading drivers and kernel modules... "
 echo > /var/dhcp/dhcps/leases
 echo > /var/dhcp/dhcps/leasesF
 ifconfig lo 127.0.0.1 netmask 255.0.0.0 broadcast 127.255.255.255 up

mknod /var/fuse c 10 229
chmod a+rw /var/fuse
#add for support chinese charset and ntfs fat ntfs filesystem
 test -e /lib/kernel/fs/fat/fat.ko && insmod /lib/kernel/fs/fat/fat.ko
 test -e /lib/kernel/fs/vfat/vfat.ko && insmod /lib/kernel/fs/vfat/vfat.ko
 test -e /lib/kernel/fs/ntfs/ntfs.ko && insmod /lib/kernel/fs/ntfs/ntfs.ko
 test -e /lib/kernel/fs/nls/nls_cp936.ko && insmod /lib/kernel/fs/nls/nls_cp936.ko



 test -e /lib/kernel/arch/mips/rt2880/lm.ko && insmod /lib/kernel/arch/mips/rt2880/lm.ko
 test -e /lib/kernel/arch/mips/rt2880/rt_timer.ko && insmod /lib/kernel/arch/mips/rt2880/rt_timer.ko
 test -e /lib/kernel/drivers/usb/serial/option.ko && insmod /lib/kernel/drivers/usb/serial/option.ko
 test -e /lib/kernel/fs/fuse/fuse.ko && insmod /lib/kernel/fs/fuse/fuse.ko
 test -e /lib/extra/dwc_otg.ko && insmod /lib/extra/dwc_otg.ko
 test -e /lib/extra/ralink_gdma.ko && insmod /lib/extra/ralink_gdma.ko
 test -e /lib/extra/rt2860v2_ap.ko && insmod /lib/extra/rt2860v2_ap.ko

mic

echo "Done"


[mncc@laplap fpt-router-hacking ]$
```
We can see that this router puts its init code in the `profile` script, then lauch a login shell so that the shell will run that script. Knowning that, I can just simply launch a shell in the end of `profile` and have the root access.

Before flashing, I need to know what is it flashing speed through the boot shell. Using a py script, I find out that the write speed using the `w` command in the boot shell is just 550bps, which mean if I want to write my roughly 2KB squashfs image, it would take 3800 seconds (too long). The main bottleneck is the 115200 default baudrate and the unecessary feedback of the command. The second option is the built in `xmodem` on the boot shell. However, the flash keep corrupting for some reason so I abandoned this idea.
So I choose to desolder the flash and hook it onto an external flasher instead.
The external flasher is an esp32s3 flashed with [esp32-serprog](https://github.com/thisiseth/esp32-serprog) so I can simply use [flashrom](https://www.flashrom.org/) without writing my own flasher.

The flash is a 4MB [MX25L3206E](https://www.alldatasheet.com/datasheet-pdf/pdf/575455/MCNIX/MX25L3206E.html).
![The 4 UART pins is visible above. From right to left: GND TX 3V3 unknown RX](/posts/hacking-the-hg531-v1-router/the-flash.avif)
![Flash pinout](/posts/hacking-the-hg531-v1-router/flash-pinout.avif)
![Pin description](/posts/hacking-the-hg531-v1-router/flash-pin-description.avif)
![Flashing rig](/posts/hacking-the-hg531-v1-router/flashing-rig.avif)
![A much more convenient rig that I use later](/posts/hacking-the-hg531-v1-router/stupid-rig.avif)

Reading is stable at 40M and writing is stable at 20M. I should have use thinner wires but it works.

#### First attempt
The first attempt was launching the new shell at `/dev/ttyS0` by modifying `/etc/inittab`
```sh
::sysinit:/etc/init.d/rcS
/dev/ttyS0::respawn:-/bin/sh
```
Well, it didn't work because the bootloader does check the checksum of the image, which I don't regenerate when repack the image.
```sh
Booting
Press 'ESC' to enter BOOT console...
 4M flash ================
Ext. phy is not found.
Listening Multicast upgrade packets....0
Decompress file... image check addr:0x9d030000 len 2093056
failed!
```
### Second attempt
That left me with the only obvious option is to modify the bootloader. But how can I know where is the bootloader? On x86 systems, it lies on the first sector of a disk drive, called the boot sector. So obviously I tried extracting the first 39898 bytes (which is the region before the fist LZMA image at 0x6020) and load it into Ghidra. And I was right. Knowing the CPU is a RTL8676, using MIPS big endian architecture, Ghidra successfully decompile it into somewhat recognizable C functions. I then copy those functions to a LLM (gemini in this case) to identify them and it works suprisingly well, it can recognize LZMA decompressing code and the UART init code, even with the dumb model.

Turns out it uses a 2-stage bootloader design: the first, minimal stage is used to decompress the second, larger stage (which is the LZMA image start at 0x6020) into RAM, then jumps to it. So I extract the second stage (which binwalk has decompressed) and load it to Ghidra. This one implements a freaking network stack, just for the xmodem/tfpt or wifi firmware loading logics (which waste me a bunch of time trying to find a meaningful function to modify).

![Most of these are network related functions](/posts/hacking-the-hg531-v1-router/ghidra-funcs.avif "Some identified functions")

Eventualy I found the function that used to verify the squashfs's checksum. Turns out who ever wrote this firmware, reuse the TCP checksum algorithm for the image checksum verification. The func run some logic, then return true if the checksum is correct, or false if incorrect. So I just replace a few line on the top to always return true and skip the checksum calculation.

Now I compress the modded stage 2 into a LZMA image, set uncompressed size (because my tool somehow set it to -1, which will not work because the stage 1 will use this to decompress the image), then put my patched stage2 bootloader and the patched squashfs there and reflash.

Well, it works!
```sh
Booting
Press 'ESC' to enter BOOT console...
 4M flash ================
Ext. phy is not found.
Listening Multicast upgrade packets....0
Decompress file... image check addr:0x9d030000 len 2093056
ok!
Linux version 2.6.21.5 (wangfeizhou@whg-29) (gcc version 4.4.7 (Realtek RSDK-1.5.9 Build 1184) ) #2 Wed Aug 20 12:28:16 CST 2014
CPU revision is: 0000dc01
Determined physical RAM map:
...
```
It completely bypass the check and decompress my modded squashfs then run linux! Except that my patched attempt of the squashfs failed.
```sh
...
All bugs added by David S. Miller <davem@redhat.com>
VFS: Mounted root (squashfs filesystem) readonly.
Freeing unused kernel memory: 124k freed
busybox init and set aff
init started: BusyBox vv1.9.1 (2014-08-20 12:30:05 CST)
starting pid 13, tty '': '/etc/init.d/rcS'
rcs
RCS DONE
Can't open /dev/ttyS0: No such file or directory
process '/bin/sh' (pid 16) exited. Scheduling it for restart.
Can't open /dev/ttyS0: No such file or directory
process '/bin/sh' (pid 17) exited. Scheduling it for restart.
Can't open /dev/ttyS0: No such file or directory
process '/bin/sh' (pid 18) exited. Scheduling it for restart.
Can't open /dev/ttyS0: No such file or directory
process '/bin/sh' (pid 19) exited. Scheduling it for restart.
Can't open /dev/ttyS0: No such file or directory
process '/bin/sh' (pid 20) exited. Scheduling it for restart.
Can't open /dev/ttyS0: No such file or directory
process '/bin/sh' (pid 21) exited. Scheduling it for restart.
Can't open /dev/ttyS0: No such file or directory
...
```
I know that the UART device is at `/dev/ttyS0` because in the boot log, it has something like this
```sh
...
squashfs: LZMA suppport for slax.org by jro
io scheduler noop registered (default)
Serial: 8250/16550 driver $Revision: 1.3 $ 1 ports, IRQ sharing disabled
netlog start
serial8250: ttyS0 at MMIO 0x0 (irq = 13) is a 16550A
PPP generic driver version 2.4.2
NET: Registered protocol family 24
IMQ starting with 3 devices...
...
```
Seems like the UART dev was deleted at that point. Later on, I kept the `/etc/inittab` intact and modify `/etc/profile` instead, since it always printing stuff on UART.

After multiple tries (including reinit /dev/ttyS0, redirecting stdin to /dev/ttyS0, virtually everything to send keystrokes to the router via UART), the solder pads of the flash gave up and shorted somewhere, making the whole system failed (the flash died too). And that is, the router turn into a mere brick, there is nothing I can done.

## The end
I should have tried starting a telnet session via `/etc/profile` (because the router would execute everything in it before the `mic` process start), but the router died before I did this. Anyway, I consider this project as a success since I technically can execute my own code on it, but not in a convenient way (modifying `/etc/profile`, then repack and reflash, which tooks a bunch of time and have a risk of damaging the solder pads, just like someone ha ha ha). If I ever do this again, I would have a better flashing rigs, not just wires everywhere like this one.

If anyone has this exact router model in hand, you can use this modded firmware I that I made and used to make better changes than mine, then you may acquire root access via UART or ethernet or something. Goodluck!
- [Modded stage 2, uncompressed](/posts/hacking-the-hg531-v1-router/bootloader-stage-2-patched.bin)
- [Modded firmware](/posts/hacking-the-hg531-v1-router/patched-2.bin)
- [The Ghidra project files](/posts/hacking-the-hg531-v1-router/ghidra.tar.gz)
- [The serial program to flash via the boot shell](/posts/hacking-the-hg531-v1-router/ser.py), generated via a LLM, audited and tested by me
- [original, ISP dumped firmware](/posts/hacking-the-hg531-v1-router/fpt.bin)
- [Huawei dumped firmware](/posts/hacking-the-hg531-v1-router/huawei.bin), this is the one I used for the modding process
- [Huawei upgrade firmware](/posts/hacking-the-hg531-v1-router/HG531V1_Firmware.rar), I used this to upgrade from the original ISP firmware
- [Multicast flashing software](/posts/hacking-the-hg531-v1-router/hg531tedta.rar)

The squashfs repacking was done by using the `build-firmware.sh` bundled with [firmware-mod-kit](https://github.com/rampageX/firmware-mod-kit) (you need to build it), modified so it does not delete the standalone repacked squashfs image, then use that standalone image to put it into the 4MB firmware using `dd`.

To access the gateway of the default firmware, you must install `socat` and run a proxy server so that a modern browser can access it. The router uses very old protocols that was deprecated by today. [^2]

The proxy can be run via this command
```sh
OPENSSL_CONF=legacy.conf socat TCP-LISTEN:8080,fork,reuseaddr OPENSSL:192.168.1.1:80,verify=0,cipher=DEFAULT:@SECLEVEL=0
```
And the content of `legacy.conf` is
```ini
openssl_conf = openssl_init

[openssl_init]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
Options = UnsafeLegacyRenegotiation
```

[^1]: This site looks so funny I busted laughing the f out, now I get the inspiration of those out of context arabic memes lmao, this site is so random looking

[^2]: Wild, in just 10 years and we have abandoned a bunch of network specification because of some security breachs, while some other, legacy protocols still lives up to today from the 1980s.
