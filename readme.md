![screenshot](/screenshots/screenshot_ballhandle_small.png)

This is a GRBL lathe controller, modified from https://github.com/Denvi/Candle

simple UI, works well with both small touch screen and large computer screen. Tested on Ubuntu 20.04 an 22.04, Raspberry Pi 3 and 4, Windows-10.

To compile on Ubuntu 
------------------------------
install Qt5 (Ubuntu 20.04)
```
sudo apt-get install build-essential 
sudo apt-get install qt5-default 
sudo apt-get install qtcreator
sudo apt-get install libqt5serialport5-dev libqt5serialport5
```

install Qt5 (Ubuntu 22.04)
```
sudo apt install -y qtcreator qtbase5-dev qt5-qmake cmake
sudo apt-get install build-essential
sudo apt-get install libqt5serialport5-dev libqt5serialport5
```

build and run (all Ubuntu versions)
```
git clone https://github.com/hjliaw/Candle-lathe.git
cd Candle-lathe/src
qmake candle.pro 
make
./Candle
```

Cross compile on Ubuntu for Raspberry Pi
-----------------------------------------
Runs very well on Raspberry Pi 3B with 7" touchscreen.  Will slow down dramatically if RPi is connected to an external 4K display, hence not recommended. If you want a large display (larger than my Sherline lathe), use a faster computer.

It's a bit slow to compile Qt even on RPi 4. Fortunately, with a little bit more work, one can cross-compile on a faster computer.

* see this excellent instructoins https://github.com/UvinduW/Cross-Compiling-Qt-for-Raspberry-Pi-4
* to eliminate the endless error message "raspberry qt could not queue drm page flip on screen hdmi1 (permission denied)", add the following to your .bashrc
```  
  export QT_QPA_EGLFS_ALWAYS_SET_MODE="1"
```  
* I run my RPi CNC controller without keyboard and mouse.  Hence no X11, but with the following added to /etc/rc.local to auto start on power up.
```
  (
    export QT_QPA_EGLFS_ALWAYS_SET_MODE="1"
    cd /home/pi/candle 
    ./Candle 2> /home/pi/cndl_err.log >> /home/pi/cndl_out.log &
  )
```

Alternatively, see [doc/rpi_img.md](doc/rpi_img.md) for downloading a pre-compiled SD image for RPi.

Generate g-code using GrblGru
-----------------------------
under construction
