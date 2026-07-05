---
title: Installing Armbian on android tv boxes
creation_date: 07 Jun 2026 15:26
---
# Installing Armbian on android tv boxes
07 Jun 2026 15:26  
This article will show you how to install ophub-armbian on a tx3-mini (or any supported device since the procedure is the same).
## Creating a boot device
1. Get the newest image [here](https://github.com/ophub/amlogic-s9xxx-armbian/releases). you can choose any version you like (noble, resolute, trixie, bookworm) but make sure that the cpu name matches (for me it is s905w and I'm using armbian noble)
2. Flash the file onto an sdcard (I'm using a 4GB one and it works great) using balena etcher.
3. Mount the BOOT partition of the sdcard then cd to it.
4. Copy `u-boot-s905x-s912.bin` and rename to `u-boot.ext`
5. Copy `extlinux/extlinux.conf.bak` and rename it to `extlinux/extlinux.conf`
6. Now check if the FDT field on `uEnv.txt` and `extlinux/extlinux.conf` are both `/dtb/amlogic/meson-gxl-s905w-tx3-mini.dtb`, if it is good then the boot media is complete.
>NOTE: If you don't want to deal with the hassle of making the front led interface works, edit `/dtb/amlogic/meson-gxl-s905w-tx3-mini.dtb` as stated on [#configuring the led driver] before installing.
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
### Set up the LED interface
The front led display wont work out-of-the-box, you need to configure it. Run `armbian-openvfd` and choose the correct device name. if it if failed and looked this:
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
# the syntax must be correct else the device will brick it self
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
> NOTE: while `armbian-openvfd` is simple to use, it does not start any service, it instead daemonlize the service (use `cat /sbin/armbian-openvfd` to confirm), which is hard to moderate. To fix it, follow [#Turn `vfdservice` to a service]
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
>NOTE: The system has already start a daemon process named `vfdservice` that would update the clock on the LED interface and blinking the colon. To turn this process into a service, see [#Turn `vfdservice` into a service].
### Configuring SSH
#### Creating a SSH key
On your pc:
1. Generate a key: `ssh-keygen -t ed25519 -C "<device name>"`
2. Push it to your device: `ssh-copy-id root@<device ip>`
On your device:
3. Disable logging in via password by `vim /etc/ssh/sshd_config` and changing these line to
```
PasswordAuthentication no
PermitRootLogin prohibit-password
PubkeyAuthentication yes
```
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
