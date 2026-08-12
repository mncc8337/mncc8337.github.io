---
title: Behaviour of each charge_types option on Lenovo IdeaPad
description: I investigated so you don't have to
creation_date: 10 Aug 2026 17:27
---
Recently I found out that the `conservation_mode` setting of `ideapad_acpi` has been deprecated.
```
ideapad_acpi VPC2004:00: conservation_mode attribute has been deprecated, see charge_types.
```
After some searches, I found out that `charge_types` is a setting of the battery acpi, and you can get all available type and the current one by catting the file.
```
[mncc@laplap ~ ]$ cat /sys/class/power_supply/BAT0/charge_types
Fast Standard [Long_Life]
[mncc@laplap ~ ]$
```
However, I have no idea what is the behaviour for each type, and I can't find any documentation about it. I decided to test it myself.

## Test procedure
On the Lenovo Vantage app on windows, there are 4 settings for Charging:
- Conservation mode: only start charging if battery percentage drops lower than 75% and only charge to 80% (this range seems to differ on different model). This was previously accessible on linux by writing to `/sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/conservation_mode` (it is still doable, but not recommended I think)
- Rapid charge: charge much faster while hibernating or shut down. On some models this can be [set on linux](https://wiki.archlinux.org/title/Lenovo_IdeaPad_5_Pro_14ACN6#Rapid_charge) by using `acpi_call` (can't test this properly, either because I'm too dumb or my model does not support it).
- Overnight battery charging: "Vantage will study daily charging patterns in order to charge your device from 80% to full right before y"ou use your computer in the morning.". I think this one needs the vantage app to work, so it will not work in linux (unless someone reverse engineer it to find all of the ACPI calls it makes).

So there are 3 binary parameters, thus 8 possible cases. Since this app loads saved settings on windows rather than reads the device state and I have no way to set options like rapid charge and overnight battery charging on linux, I need to boot to windows, set new settings, and then reboot to linux to see the effect.

## Test result
My laptop model is IdeaPad Slim 3 15IRH10 `83K1`. Here is the test result

|Conservation mode|Rapid charge|Overnight battery charging|`charge_types` value|
|-----------------|------------|--------------------------|-------------------|
|Disable          |Disable     |Disable                   |`Standard`         |
|Disable          |Disable     |Enable                    |`Standard`         |
|Disable          |Enable      |Disable                   |`Fast`             |
|Disable          |Enable      |Enable                    |`Fast`             |
|Enable           |Disable     |Disable                   |`Long_Life`        |
|Enable           |Disable     |Enable                    |`Long_Life`        |
|Enable           |Enable      |Disable                   |not possible       |
|Enable           |Enable      |Enable                    |not possible       |

It seems like `Fast` corresponds to Rapid charge, and `Long_Life` corresponds to Conservation mode. Setting the type to `Standard` will turn off both. Overnight battery charging seems to not related.
Because setting charge type to `Fast` will enable rapid charge, we now have an easier way to change charging mode to rapid charge without relying on `acpi_call`.
