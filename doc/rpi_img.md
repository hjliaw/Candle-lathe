rpicnc.img notes
----------------
Notes on downloading ready made Raspberry Pi image with Candle lathe mode


Download the .img file
----------------------
* Use the latest link shared with you to download the img file.  This is a huge (~8GB) file, so can not let Google keed old versions.  Any update requires deleting old file and upload the new one.
* Use a micro-SD card with at least 16GB storage.  
* Use Raspberry Pi imager https://www.raspberrypi.com/software/ to write the img file to SD card, select the downloaded .img as Custom
* Use Shift-Ctrl-X to enter "Advanced Options", and enter your WiFi information.  Not needed if you use wired Ethernet cable.
* You can also change the hostname and user password in "Advanced Options".  The default hostname is qtpi, because the GUI is based on Qt5.


Transfer g-code files with USB disk
-----------------------------------
The RPi is configured to automatically mount a USB disk starting at "/media/usb0". Yiu can save g-code to a USB drive, and select the g-code accordingly.

Transfer g-code files from Linux
--------------------------------
Besides scp or rsync by commandline, you can also enable Samba. 


Transfer g-code files from Windows
----------------------------------
Samba 1.0 was disabled by default due to security concerns. Shouldn't be a big deal for home network.  But if you do worry about this, you can learn about PowerShell, and use scp (secure copy) via command line for copying files from Windows to Raspberry Pi.

To enable Samba 1.0, open Control Panel, select Programs and Features, then Turn Windows features on or off. Go down the list and make sure SMB 1.0/CIFS file sharing is checked. Restart the computer.

After restart, if Raspberry Pi is connected to the network, you sould see a shared directory at "qtpi" (or your choice of host name), under the only available directory "gcodes".  My Windows machine took a long time (~1min) to scan the network, and took two rounds to successfully find "qtpi".

