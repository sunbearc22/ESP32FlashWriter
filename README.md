# ESP32FlashWriter

<p align="center">
  <img width="682" height="420" src="https://github.com/sunbearc22/ESP32FlashWriter/blob/master/image/esp32flashwrite_GUI.png">
</p>

An easy to use GUI that you can use to connect with your ESP32 devices and update its firmware. 

1. Simply plug in your device(s) via USB/Serial cable to your Linux OS computer and select your device port and the baud (default baud is 11520 bps). The port selection will trigger the connection. In the event your ESP32 becomes unplugged after it is connected, the GUI will notify you to replug and reselect your device port.  

2. To update your ESP32 firmware, simply click on the folder icon to select your new firmware, decide if you want to erase the entire flash or not, and then click **WRITE** to update your ESP32 firmware. 

Try it. Appreciate your feedback(s). Do alert me on issue(s) with using it. Thank you.

## How to use it:
1. Clone or download this repository to your local machine.
2. Open a terminal, go to your downloaded repository directory and run `python3 esp32flashwriter_v4_0.py`, or
3. Run `esp32flashwriter_v4_0.py` via your integrated development environment (IDE) like python3-idle, PyCharm, etc...

## OS Prerequisites:
- Linux 

## Software Prerequisites:
- python 3
- tkinter v8.6
- [esptool.py v2.6](https://github.com/espressif/esptool)
- [pyserial v3.4](https://github.com/pyserial/pyserial)

## Firmware
- [Micropython](https://micropython.org/download/), [ESP32](https://www.espressif.com/en/products/hardware/esp32/resources)

## Hardware Prerequisites:
- ESP32 module, ESP32 DevKits
- USB/Serial data connectors/cables
