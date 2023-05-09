![screenshot](/screenshots/screenshot_ballhandle_small.png)

GRBL lathe controller, modified from https://github.com/Denvi/Candle

Simple UI, works well with both small touch screen and large computer screen. Tested on Ubuntu 20.04 and 22.04, Raspberry Pi 3 and 4, Windows-10.

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

Compiling on Windows-10
-----------------------
Below is a brief description, not step by step instructions.  You may need other online resources about Qt5 on Windows-10.
Pre-compiled binary is available upon request.

	created Qt account
	install Qt5.15.2 and MinGW  (8GB, takes a long long time to dwonload)
	
	install MinGW according to
	https://www.ics.uci.edu/~pattis/common/handouts/mingweclipse/mingw.html
	note the PATH definition

	install git, then clone project from github (I did that in PowerShell, should be able to do this in MinGW)
	
	start Qt 5.15.2 (MinGW 8.1.0 32-bit) from Windows Start, (it's one of the options in Start->Qt folder)
	cd canle-lathe/src
	qmake candle.pro
	make
	
	takes a while to finish; afterwards, executable is release\Candle.exe  connect to COM4/115200 (your COM port number may be different)

Generate g-code using GrblGru
-----------------------------
There are a lot of online documents and videos about GrblGru.  This guide [GrblGru_lathe_guide](doc/grblgru_guide/GrblGru_lathe_guide.pdf) is for lathe only, in particularly for using with ezNC-2.
