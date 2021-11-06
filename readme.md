Candle-lathe
-------------
GRBL lathe controller, modified from https://github.com/Denvi/Candle

simple UI, works well with both small touch screen and large computer scren

To compile on Ubuntu (20.04)
------------------------------

- sudo apt-get install build-essential 
- sudo apt-get install qt5-default 
- sudo apt-get install qtcreator
- sudo apt-get install libqt5serialport5-dev libqt5serialport5

- cd src
- qmake candle.pro 
- make

- ./Candle

main screen 
---------------
![screenshot](/screenshots/screenshot_ballhandle_small.png)
