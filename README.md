# ESP32FlashWriter

<p align="center">
  <img width="682" height="420" src="https://github.com/sunbearc22/ESP32FlashWriter/blob/master/image/esp32flashwrite_GUI0.png">
</p>

An easy to use GUI that you can use to connect with your ESP32 devices and update its firmware. 

1. Simply plug in your device(s) via USB/Serial cable to your Linux OS computer and select your device port and the baud (default baud is 11520 bps). The port selection will trigger the connection. In the event your ESP32 becomes unplugged after it is connected, the GUI will notify you to replug and reselect your device port.  

2. To update your ESP32 firmware, simply click on the folder icon to select your new firmware, decide if you want to erase the entire flash or not, and then click **WRITE** to update your ESP32 firmware.

3. You can use your keyboard <kbd>Tab</kbd> key to toggle between the fields in the GUI. Pressing the <kbd>Return</kbd> key will select the field. To exit the selected field, press the <kbd>Esc</kbd> key. Scrolling within the **Port** and **Baud** fields can be done by pressing the <kbd>&#8593;</kbd> and <kbd> &#8595;</kbd> arrow keys. 

Try it. Appreciate your feedback(s). Do alert me on issue(s) with using it. Thank you.

## How to use it:
1. Clone or download this repository to your local machine.
2. Ensure softwares identified in [Software Prerequisities](https://github.com/sunbearc22/ESP32FlashWriter/blob/master/README.md#software-prerequisites) are installed. 
3. Execute esp32flashwriter:
   - Open a terminal, go to your downloaded repository directory and run `python3 esp32flashwriter_v4_2.py`, or
   - Run `esp32flashwriter_v4_2.py` via your integrated development environment (IDE) like python3-idle, PyCharm, etc...

## Firmwares that you can write to ESP32 Flash:
- [Micropython](https://micropython.org/download/), [ESP32](https://www.espressif.com/en/products/hardware/esp32/resources)

## OS Prerequisites:
- Linux
- Windows 10

## Software Prerequisites:
- python 3
- tkinter v8.6
- [esptool.py v2.6](https://github.com/espressif/esptool)
- [pyserial v3.4](https://github.com/pyserial/pyserial)

## Hardware Prerequisites:
- ESP32 module, ESP32 DevKits
- USB/Serial data connectors/cables
