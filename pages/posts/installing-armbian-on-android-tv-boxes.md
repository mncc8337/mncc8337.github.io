---
title: Installing Armbian on android tv boxes
description: A quick guide on how to install ophub-armbian on a tx3-mini.
creation_date: 07 Jun 2026 15:26
---
## Creating a boot device
1. Get the newest image [here](https://github.com/ophub/amlogic-s9xxx-armbian/releases). you can choose any version you like (noble, resolute, trixie, bookworm) but make sure that the cpu name matches (for me it is s905w and I'm using armbian noble)
2. Flash the file onto an sdcard (I'm using a 4GB one and it works great) using balena etcher.
3. Mount the BOOT partition of the sdcard then cd to it.
4. Copy `u-boot-s905x-s912.bin` and rename to `u-boot.ext`
5. Copy `extlinux/extlinux.conf.bak` and rename it to `extlinux/extlinux.conf`
6. Now check if the FDT field on `uEnv.txt` and `extlinux/extlinux.conf` are both `/dtb/amlogic/meson-gxl-s905w-tx3-mini.dtb`, if it is good then the boot media is complete.
>NOTE: If you don't want to deal with the hassle of making the front led interface works, edit `/dtb/amlogic/meson-gxl-s905w-tx3-mini.dtb` as stated on [Setting up the LED interface](#setting-up-the-led-interface) before installing.
## Booting
1. Get the circuit board out, locating a button on the board. many boards put this button on plain sights, but some put it behind the av jack, this is the boot mode button that let you select the boot mode, in this case it let you boot straight from the sd card instead of whatever builtin storage it has.
2. Connect the board to your router via the ethernet port.
3. While holding the reset button, plugging in the power supply, continuing holding the button for 10 seconds and release.
4. Wait for about 3-5 mins for it to completely boot (on the tx3-mini you can watch the light at the SPDIF port, when it is red then it is booting).
>NOTE: You may notice that the led interface is still showing `boot`, it is because armbian **doesn't setup the display driver automatically**, not because your device stucks at booting, so it is safe to continue.
## Connecting it to your pc
1. Install `arp-scan` or similar stuff to scan the local ip addresses.
2. Get all of your network adapter: `ip link`, remember the one that you are using
3. Scan for all ports on your adapter: `watch -n 1 -- sudo arp-scan --interface=<adapter name> 192.168.1.0/24`
4. Try ssh-ing to every address it shows, especially the one with the name `Unknown: locally administered` until it prompts you to type in the password (or the yes/no question, in that case type `yes` and it will ask you the password): `ssh -v root@<the address>`
5. Type in the default password `1234`
6. Now you are in the box! check everything you like (like extracting the android image) and run `armbian-install` and answer its questions then it is done.
>NOTE: To backup the original android image, run `armbian-ddbr`. If you forget that, but what to install it back, then search for it [here](https://github.com/ophub/kernel/releases/tag/tools), put it in your armbian installed sdcard, boot from it and use `dd` to write the image to the eMMC.
## Basic configuring
After rebooting from `armbian-install`,  run `apt-update && apt upgrade` to upgrade all packages.
### Update the timezone
`timedatectl set-timezone <your timezone>`
### Setting up the LED interface
The front led display wont work out-of-the-box, you need to configure it. Run `armbian-openvfd` and choose the correct device name. If it failed and looked this:
```
[ OPTIONS ] Please Input ID: 18
[ STEPS ] Enabling LED screen display...
[ INFO ] Using LED Profiles: /usr/share/openvfd/conf/tx3-mini.conf
[ INFO ] turn led usb on ...
/usr/sbin/armbian-openvfd: line 114: /sys/class/leds/openvfd/led_on: No such file or directory
[ INFO ] turn led colon on ...
/usr/sbin/armbian-openvfd: line 114: /sys/class/leds/openvfd/led_on: No such file or directory
[ INFO ] turn led eth on ...
/usr/sbin/armbian-openvfd: line 114: /sys/class/leds/openvfd/led_on: No such file or directory
[ INFO ] turn led wifi on ...
Open device failed.
: No such file or directory
/usr/sbin/armbian-openvfd: line 114: /sys/class/leds/openvfd/led_on: No such file or directory
[ SUCCESS ] LED display enabled!
```
Then edit your dtb as follow:
1. Create a backup: `dtc -I dtb -O dts /boot/dtb/amlogic/meson-gxl-s905w-tx3-mini.dtb > $HOME/tx3-mini.dts.bck`
2. Make a copy: `cp $HOME/tx3-mini.dts.bck $HOME/tx3-mini.dts && vim $HOME/tx3-mini.dts`
3. Add this `openvfd` section before the `__symbol__` section at the end of the file:
```
# on vim, press Gkk[{ to go to there (it's on the end of the file)
1973         __symbols__ {
1974                 hwrom_reserved = "/reserved-memory/hwrom@0";
....

# then insert this
# the syntax must be exactly the same else the device will brick it self
# and you will need to boot to the install media to fix
1973         openvfd {
1974                 compatible = "open,vfd";
1975                 dev_name = "openvfd";
1976                 status = "okay";
1977         };
1978
1979         __symbols__ {
1980                 hwrom_reserved = "/reserved-memory/hwrom@0";
....
```
4. Now load the new dtb and reboot: `dtc -I dts -O dtb $HOME/tx3-mini.dts -o /boot/dtb/amlogic/meson-gxl-s905w-tx3-mini.dtb && reboot`
5. If it booted successfully then just run `armbian-openvfd` again, it should success now
> NOTE: while `armbian-openvfd` is simple to use, it does not start any service, it instead daemonlize the service (use `cat /sbin/armbian-openvfd` to confirm), which is hard to moderate. To fix it, follow [Start on startup](#start-on-startup).
#### Start on startup
```
# execute the following command in the terminal to enable the openvfd service
sed -i 's|^#*openvfd_enable=.*|openvfd_enable="yes"|g' /etc/custom_service/start_service.sh
sed -i 's|^#*openvfd_boxid=.*|openvfd_boxid="15"|g' /etc/custom_service/start_service.sh
# some devices require restarting the OpenVFD service to clear 'BOOT' and related messages, not required though
sed -i 's|^#*openvfd_restart=.*|openvfd_restart="yes"|g' /etc/custom_service/start_service.sh
```
The solution above was [proposed by ophub](https://github.com/ophub/amlogic-s9xxx-armbian/blob/main/documents/led_screen_display_control.md). However, it run `vfdservice` as a daemon, not a systemd service, which is bad for moderation. To turn it into a service, create a service config:
```
# /etc/systemd/system/openvfd.service

[Unit]
Description=OpenVFD Display Service

[Service]
Type=simple
# correct your box model
ExecStart=/bin/sh /root/scripts/openvfd.sh tx3-mini.conf
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
```
# /root/scripts/openvfd.sh
#!/bin/sh

CONF_FILE="/usr/share/openvfd/conf/${1}"
VFD_SERVICE="/usr/share/openvfd/vfdservice"

if [ -s "${CONF_FILE}" ] && [ -x "${VFD_SERVICE}" ]; then
    . "${CONF_FILE}" 2>/dev/null
else
    echo "openvfd config file not found" >&2
    exit 1
fi

modprobe openvfd vfd_gpio_clk=${vfd_gpio_clk} \
    vfd_gpio_dat=${vfd_gpio_dat} \
    vfd_gpio_stb=${vfd_gpio_stb:-0,0,0xFF} \
    vfd_gpio0=${vfd_gpio0:-0,0,0xFF} \
    vfd_gpio1=${vfd_gpio1:-0,0,0xFF} \
    vfd_gpio2=${vfd_gpio2:-0,0,0xFF} \
    vfd_gpio3=${vfd_gpio3:-0,0,0xFF} \
    vfd_gpio_protocol=${vfd_gpio_protocol:-0,0} \
    vfd_chars=${vfd_chars} vfd_dot_bits=${vfd_dot_bits} \
    vfd_display_type=${vfd_display_type}

${VFD_SERVICE}
```
Enable it
```
systemctl daemon-reload
systemctl enable openvfd
```
Now you can start and stop it using
```
systemctl start openvfd
systemctl stop openvfd
```
#### LED states
`armbian-led-state` service have some bugs on my version `6.18.33-ophub` (08/06/2026) (it failed to start, see `systemctl status armbian-led-state`), also it is pretty useless (it save the LED states before quitting and restore after starting).
```
sudo systemctl disable armbian-led-state.service
sudo systemctl mask armbian-led-state.service
```
Now prevent `armbian-openvfd` to turn on all of function LEDs on load (skip this if you already turn `vfdservice` into a true service):
```
# /usr/sbin/armbian-openvfd
# comment these lines, they just turn on all the LED defined on
# the 'functions' variable in the config file
111     if [[ -n "${functions}" ]]; then
112         for func in ${functions}; do
113             echo -e "${INFO} turn led ${func} on ... "
114             echo "${func}" >/sys/class/leds/openvfd/led_on 2>/dev/null
115         done
116     fi
```
Now create a systemd service using this script to automatically enable individual LED upon corresponding function event:
```
# /root/scripts/openvfd-function-led.sh
#!/bin/sh

VFD_ON="/sys/class/leds/openvfd/led_on"
VFD_OFF="/sys/class/leds/openvfd/led_off"

# wait till openvfd.service is started
# yes, im too dumb to use systemd to do this
while [ ! -f "$VFD_ON" ] || [ ! -f "$VFD_OFF" ]; do
    count=$((count + 1))

    if [ "$count" -ge "60" ]; then
        echo "error, no openvfd driver."
        exit 1
    fi

    sleep 1
done

LAST_USB=-1
LAST_ETH=-1
LAST_WIFI=-1
LAST_PLAY_PAUSE=-1
LAST_ALARM=-1

while true; do
    # usb
    usb_count=$(lsusb | wc -l)
    real_usb=$((usb_count - 1))
    [ "$real_usb" -lt 0 ] && real_usb=0

    if [ "$real_usb" -gt 0 ]; then
        [ "$LAST_USB" != "1" ] && {
            echo "usb" > "$VFD_ON" 2>/dev/null
            LAST_USB=1
        }
    else
        [ "$LAST_USB" != "0" ] && {
            echo "usb" > "$VFD_OFF" 2>/dev/null
            LAST_USB=0
        }
    fi

    # ethernet
    eth_carrier=$(cat /sys/class/net/eth0/carrier 2>/dev/null)
    if [ "$eth_carrier" = "1" ]; then
        [ "$LAST_ETH" != "1" ] && {
            echo "eth" > "$VFD_ON" 2>/dev/null
            LAST_ETH=1
        }
    else
        [ "$LAST_ETH" != "0" ] && {
            echo "eth" > "$VFD_OFF" 2>/dev/null
            LAST_ETH=0
        }
    fi

    # wifi
    wifi_carrier=$(cat /sys/class/net/wlan0/carrier 2>/dev/null)
    if [ "$wifi_carrier" = "1" ]; then
        [ "$LAST_WIFI" != "1" ] && {
            echo "wifi" > "$VFD_ON" 2>/dev/null
            LAST_WIFI=1
        }
    else
        [ "$LAST_WIFI" != "0" ] && {
            echo "wifi" > "$VFD_OFF" 2>/dev/null
            LAST_WIFI=0
        }
    fi

    # you can add additional logic for 'alarm', 'play' and 'pause' here
    # NOTE: don't touch 'colon', it has been used by vfdservice already
    # here is my own

    # play/pause based on CPU load
    load=$(cat /proc/loadavg | awk '{print int($1)}')
    if [ "$load" -gt 1 ]; then
        [ "$LAST_PLAY_PAUSE" != "1" ] && {
            echo "play" > "$VFD_ON" 2>/dev/null
            echo "pause" > "$VFD_OFF" 2>/dev/null
            LAST_PLAY_PAUSE=1
        }
    else
        [ "$LAST_PLAY_PAUSE" != "0" ] && {
            echo "play" > "$VFD_OFF" 2>/dev/null
            echo "pause" > "$VFD_ON" 2>/dev/null
            LAST_PLAY_PAUSE=0
        }
    fi

    # alarm based on CPU temperature
    temp=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
    if [ "$temp" -gt 70000 ]; then
        [ "$LAST_ALARM" != "1" ] && {
            echo "alarm" > "$VFD_ON" 2>/dev/null
            LAST_ALARM=1
        }
    else
        [ "$LAST_ALARM" != "0" ] && {
            echo "alarm" > "$VFD_OFF" 2>/dev/null
            LAST_ALARM=0
        }
    fi

    sleep 1
done
```
```
# /etc/systemd/system/openvfd-function-led.service

[Unit]
Description=OpenVFD Function LED Service
After=network.target systemd-udevd.service openvfd.service
Wants=network.target systemd-udevd.service openvfd.service
BindsTo=openvfd.service

[Service]
Type=simple
ExceStartPre=/bin/sleep 5
ExecStart=/bin/sh /root/scripts/openvfd-function-led.sh
Restart=always
RestartSec=3

[Install]
WantedBy=openvfd.service
```
```
sudo systemctl daemon-reload
sudo systemctl enable openvfd-function-led.service
sudo systemctl start openvfd-function-led.service
sudo systemctl status openvfd-function-led.service
```
>NOTE: The system has already start a daemon process named `vfdservice` that would update the clock on the LED interface and blinking the colon. To turn this process into a service, see [Start on startup](#start-on-startup).
### Removing unnecessary drivers
You won't need all of the drivers on `/usr/lib/firmware/`, so it is the best to remove most of the heavy and unnecessary one.
First, blocks `armbian-firmware` from updating, which would reinstall all of the driver files:
```
sudo apt-mark hold armbian-firmware
```
Now plugging in all the peripherals that you might use, and run this to check which drivers are loaded:
```
sudo dmesg | grep -i firmware
```
The command will show all of the drivers that you would need. Now run this to remove the unnecessary one:
```
# be sure that you have ommited the one that was actually loaded
# this was the commands i ran on my tx3-mini, not a universal command for every
# one to blindy run.
# note that you can reinstall armbian-firmware (after unblocking it) to
# restore the folder.
# you may notice that most of the removed one are actually wifi and bluetooth
# drivers. that is because i will and will not use them on my box. all of other
# misc drivers are kept so that i can play with some weird peripherals later.
# other one that wasn't listed on the dmesg grep can be removed.
sudo rm -rf /usr/lib/firmware/{qcom,mediatek,rkwifi,aic8800,rtw*,brcm,ath*}
sudo rm -rf /usr/lib/firmware/updates/ath*
sudo rm -rf /usr/lib/firmware/{uwe5622,iwlwifi*,rtlwifi,rtl_bt,ap6*,ssv*}
sudo rm -rf /usr/lib/firmware/{rt*,RTL*,mt*,fw_bcm*,clm_bcm*,ti-con*,intel,nvram_ap*,rockchip,imx,cypress,qca,uwe*,bt_*}
```
The command above would give you about 700MiB of free space.
### Reclaiming GPU reserved ram
By default, linux will reserved 256MiB of ram for the mali GPU. If you connected a display to the box, that's fine. But if you don't, then it's a huge waste, when the system is already low on ram. Fortunately, reclaiming that 256MiB is easy. Todo that, open `/boot/uEnv.txt` and do the following:

- Remove the `video=...` flag, this will disable video declaration.
- Add this flag `cma=16M`, this will override the default kernel setting, forcing it to only reserve 16M for the GPU (we cannot set it to 0 because it will cause some problems for the kernel)
- Be sure to not edit anything else, else you will brick the kernel and will have to boot to another boot medium to undo the changes.
Now reboot and check `dmesg`, look for the line containing `cma`, tou should see that there are only 16M of ram reserved for GPU.
### External SATA III HDD connected via USB not recognized after reboot
If you can connect your HDD via USB when booted on linux, but not after restart, then the problem is at the u-boot initialization process. If you hook a UART adapter to the box and look at the boot log, you can see that at some lines before booting to linux:
```
...
card out
emmc/sd response timeout, cmd8, status=0x1ff2800
emmc/sd response timeout, cmd55, status=0x1ff2800
emmc/sd response timeout, cmd1, status=0x1ff2800
(Re)start USB...
USB0:   USB3.0 XHCI init start
Register 2000140 NbrPorts 2
Starting the controller
USB XHCI 1.00
scanning bus 0 for devices... XHCI timeout on event type 33... cannot recover.
Device not responding to set address.
Device not responding to set address.
WARN urb submitted to disabled ep
retry new usb device
XHCI timeout on event type 33... cannot recover.
Cannot allocate device context to get SLOT_ID
1 USB Device(s) found
       scanning usb for storage devices... 0 Storage Device(s) found
** Bad device usb 0 **
** Bad device usb 1 **
** Bad device usb 2 **
** Bad device usb 3 **
reading emmc_autoscript
831 bytes read in 3 ms (270.5 KiB/s)
## Executing script at 01020000
reading u-boot.emmc
...
```
You can see that because the HDD is too slow, u-boot failed to read the drive to see if there is any bootable images on the drive: `scanning bus 0 for devices... XHCI timeout on event type 33... cannot recover.`. Nonetheless, if you check `bootcmd` and `start_autoscript` (by spamming <kbd>Space</kbd> or <kbd>Enter</kbd> at booting) you can see that it runs `usb start` but never calls `usb stop` (which deinitializes the usb bus):
```
gxl_p281_v1#printenv bootcmd
bootcmd=run start_autoscript; run storeboot
gxl_p281_v1#printenv start_autoscript
start_autoscript=if mmcinfo; then run start_mmc_autoscript; fi; if usb start; then run start_usb_autoscript; fi; run start_emmc_autoscript
gxl_p281_v1#printenv start_usb_autoscript
start_usb_autoscript=for usbdev in 0 1 2 3; do if fatload usb ${usbdev} 1020000 s905_autoscript; then autoscr 1020000; fi; done
```
As a result, the USB device is left at a dirty usb state. Linux then tries to initialize it, and gets time out error `-110` and time expired `-62`
```
[    3.799274] usb 1-1: new high-speed USB device number 2 using xhci-hcd
[    9.129572] usb 1-1: device descriptor read/64, error -110
[   24.702861] usb 1-1: device descriptor read/64, error -110
[   24.929379] usb 1-1: new high-speed USB device number 3 using xhci-hcd
[   30.249521] usb 1-1: device descriptor read/64, error -110
[   45.822853] usb 1-1: device descriptor read/64, error -110
[   45.933758] usb usb1-port1: attempt power cycle
[   46.326050] usb 1-1: new high-speed USB device number 4 using xhci-hcd
[   51.466260] xhci-hcd xhci-hcd.2.auto: Timeout while waiting for setup device command
[   56.799561] xhci-hcd xhci-hcd.2.auto: Timeout while waiting for setup device command
[   57.012739] usb 1-1: device not accepting address 4, error -62
[   57.139386] usb 1-1: new high-speed USB device number 5 using xhci-hcd
[   62.346210] xhci-hcd xhci-hcd.2.auto: Timeout while waiting for setup device command
[   67.679627] xhci-hcd xhci-hcd.2.auto: Timeout while waiting for setup device command
[   67.892719] usb 1-1: device not accepting address 5, error -62
[   67.901881] usb usb1-port1: unable to enumerate USB device
```
So we need to prevent u-boot from initializing the usb (or at least deinitialize it after uses) or accessing the usb bus at all.
#### The hardware solution
This is my first attempt at solving this issue, and it is horrendously messy so you should look at [solution #2](#the-software-solution) for a cleaner setup.

The idea is that we could use a box's gpio that only turns after linux is booted to control the power of the device. If you watch closely, the SPDIF led of the box turns on at boot, and turns off after linux is booted (it is because that LED is controlled by the linux audio driver); that is the perfect behaviour for such a pin.
So I take off the plastic casing of the port and hook this driver circuit to it, then cut the VCC line of the usb wire to hook this driver to. And it works!
![A standard high side switching circuit with an extra NPN BJT at the middle to invert the switching behaviour.](/posts/installing-armbian-on-android-tx-boxes/sim.webm "A [falstad](https://www.falstad.com/circuit/circuitjs.html) simulation. This is a standard high-side switching circuit. The middle transistor is a NOT gate to invert the logic. The circuit blocks current from flowing from VIN to VOUT when SIG is higher than GND. 1.8v is the voltage measured at VIN of SPDIF LED when it lights up.")
![The implementation of the above simulation](/posts/installing-armbian-on-android-tx-boxes/circuit.avif "The circuit I built. It uses 2 [PN2222](https://www.alldatasheet.com/datasheet-pdf/view/356062/ONSEMI/PN2222.html) for NPN BJTs and a [AO3401](https://www.alldatasheet.com/datasheet-pdf/view/136085/AOSMD/AO3401.html) for the P-MOSFET, a 2k resistor to limit current at signal in pin, and 2 5k1 resistors for pull-ups.")
![The circuit in action. SIG is connected at VIN of the SPDIF LED, and VIN/VOUT splits VCC line of the USB wire. The circuit is isolated from the board via clear tapes.](/posts/installing-armbian-on-android-tx-boxes/circuit-in-action.avif)
```
...
[ 14.164527] lima d00c0000.gpu: mod rate = 24000000 [ 14.168782] lima d00c0000.gpu: error -ENODEV: _opp_set_regulators: no regulator (mali) found
[ 14.179298] [drm] Initialized lima 1.1.0 for d00c0000.gpu on minor 1
[ 14.210170] gx-sound-card sound: workaround: internal PCM chmap controls mapped to device 0
[ 14.400294] cfg80211: Loading compiled-in X.509 certificates for regulatory database [ 14.444076] Loaded X.509 cert 'sforshee: 00b28ddf47aef9cea7'
...
[ 15.208364] usb 1-1: New USB device strings: Mfr=2, Product=3, SerialNumber=1
[ 15.215470] usb 1-1: Product: G-DRIVE mobile USB-C
[ 15.220117] usb 1-1: Manufacturer: HGST
[ 15.223929] usb 1-1: SerialNumber: FF0175006061
[ 15.255335] scsi host0: uas
[ 15.259244] scsi 0:0:0:0: Direct-Access G-DRIVE mobile USB-C 0 PQ: 0 ANSI: 6
[ 15.301996] sd 0:0:0:0: [sda] 488397168 512-byte logical blocks: (250 GB/233 GiB)
[ 15.307241] sd 0:0:0:0: [sda] Write Protect is off
[ 15.311180] sd 0:0:0:0: [sda] Mode Sense: 43 00 00 00 [ 15.312204] sd 0:0:0:0: [sda] Write cache: enabled, read cache: enabled, doesn't support DPO or FUA
[ 15.320536] sd 0:0:0:0: [sda] Preferred minimum I/O size 512 bytes
[ 15.320574] sd 0:0:0:0: [sda] Optimal transfer size 33553920 bytes [ 15.426480] sda: sda1
[ 15.428542] sd 0:0:0:0: [sda] Attached SCSI disk
[ 21.818068] sd 0:0:0:0: Attached scsi generic sg0 type 0
...
```
The device is recognized after the audio driver `gx-sound-card` is loaded, which is the correct behaviour for this setup.
### The software solution
A much cleaner solution is just modify the u-boot's initialization process to do what we want. To do this you would need an UART adapter to communicate with the box doing the boot process (I used the same one [I made before](/posts/upgrading-an-usb-to-ttl-board)).
1. Upon powering the box, spam <kbd>Space</kbd> to enter the boot shell.
```
[mncc@laplap ~ ]$ picocom /dev/ttyUSB0 -b 115200
picocom v3.1

port is        : /dev/ttyUSB0
flowcontrol    : none
baudrate is    : 115200
parity is      : none
databits are   : 8
stopbits are   : 1
escape is      : C-a
local echo is  : no
noinit is      : no
noreset is     : no
hangup is      : no
nolock is      : no
send_cmd is    : sz -vv
receive_cmd is : rz -vv -E
imap is        :
omap is        :
emap is        : crcrlf,delbs,
logfile is     : none
initstring     : none
exit_after is  : not set
exit is        : no

Type [C-a] [C-h] to see available commands
Terminal ready
@GXL:BL1:9ac50e:bb16dc;FEAT:ADFC318C:0;POC:3;RCY:0;EMMC:0;READ:0;0.0;CHK:0;
TE: 282174
...
Usage:
irkey_update
InUsbBurn
noSof
Hit Enter or space or Ctrl+C key to stop autoboot -- :  0
gxl_p281_v1#
gxl_p281_v1#help
?       - alias for 'help'
...
```
2. Confirm that `bootcmd` and `start_autoscript` is the same as I shown you before.
```
gxl_p281_v1#printenv bootcmd
bootcmd=run start_autoscript; run storeboot
gxl_p281_v1#printenv start_autoscript
start_autoscript=if mmcinfo; then run start_mmc_autoscript; fi; if usb start; then run start_usb_autoscript; fi; run start_emmc_autoscript
gxl_p281_v1#printenv start_usb_autoscript
start_usb_autoscript=for usbdev in 0 1 2 3; do if fatload usb ${usbdev} 1020000 s905_autoscript; then autoscr 1020000; fi; done
```
3. Modify `start_autoscript` so that it will not touch any usb devices during boot.
```
gxl_p281_v1#setenv start_autoscript 'if mmcinfo; then run start_mmc_autoscript; fi; run start_emmc_autoscript'
gxl_p281_v1#saveenv
gxl_p281_v1#reset
```
4. Now it should boot without querying the drive.
```
...
time_out = f4240
ir init
irkey_update - irkey_update time_value

Usage:
irkey_update
Hit Enter or space or Ctrl+C key to stop autoboot -- :  0
card out
emmc/sd response timeout, cmd8, status=0x1ff2800
emmc/sd response timeout, cmd55, status=0x1ff2800
emmc/sd response timeout, cmd1, status=0x1ff2800
reading emmc_autoscript
831 bytes read in 3 ms (270.5 KiB/s)
## Executing script at 01020000
reading u-boot.emmc
** Unable to read file u-boot.emmc **
reading uEnv.txt
382 bytes read in 2 ms (186.5 KiB/s)
reading /zImage
42879488 bytes read in 1247 ms (32.8 MiB/s)
reading /uInitrd
17974960 bytes read in 502 ms (34.1 MiB/s)
reading /dtb/amlogic/meson-gxl-s905w-tx3-mini.dtb
41283 bytes read in 8 ms (4.9 MiB/s)
mac=06:41:80:80:39:80
[rsvmem] get fdtaddr NULL!
rsvmem - reserve memory

Usage:
rsvmem check                   - check reserved memory
rsvmem dump                    - dump reserved memory

rsvmem check failed
## Loading init Ramdisk from Legacy Image at 15000000 ...
   Image Name:   uInitrd
   Image Type:   AArch64 Linux RAMDisk Image (gzip compressed)
   Data Size:    17974896 Bytes = 17.1 MiB
   Load Address: 00000000
   Entry Point:  00000000
   Verifying Checksum ... OK
load dtb from 0x1000000 ......
      Amlogic multi-dtb tool
      Single dtb detected
## Flattened Device Tree blob at 01000000
   Booting using the fdt blob at 0x1000000
libfdt fdt_path_offset() returned FDT_ERR_NOTFOUND
[rsvmem] fdt get prop fail.
   Loading Ramdisk to 32d78000, end 33e9c670 ... OK
   Loading Device Tree to 000000001fff2000, end 000000001ffff142 ... OK
fdt_instaboot: no instaboot image

Starting kernel ...

uboot time: 5299552 us
[    0.000000] Booting Linux on physical CPU 0x0000000000 [0x410fd034]
...
[    3.808886] usb 1-1: new high-speed USB device number 2 using xhci-hcd
[    3.943823] usb 1-1: New USB device found, idVendor=4971, idProduct=8043, bcdDevice= 1.01
[    3.947790] usb 1-1: New USB device strings: Mfr=2, Product=3, SerialNumber=1
[    3.954855] usb 1-1: Product: G-DRIVE mobile USB-C
[    3.959584] usb 1-1: Manufacturer: HGST
[    3.963390] usb 1-1: SerialNumber: FF0175006061
[    3.974970] scsi host0: uas
[    3.977347] scsi 0:0:0:0: Direct-Access     G-DRIVE  mobile USB-C     0    PQ: 0 ANSI: 6
[    5.706707] sd 0:0:0:0: [sda] 488397168 512-byte logical blocks: (250 GB/233 GiB)
[    5.709804] sd 0:0:0:0: [sda] Write Protect is off
[    5.714700] sd 0:0:0:0: [sda] Write cache: enabled, read cache: enabled, doesn't support DPO or FUA
[    5.723383] sd 0:0:0:0: [sda] Preferred minimum I/O size 512 bytes
[    5.729227] sd 0:0:0:0: [sda] Optimal transfer size 33553920 bytes
[    5.915189]  sda: sda1
[    5.916429] sd 0:0:0:0: [sda] Attached SCSI disk
...
```
You can see that linux now recognized the drive and the boot time is also much faster.

Do note that now the box can not automatically boot onto any usb device unless you enter the shell and force it to do that.
