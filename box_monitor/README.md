# Simple environment monitoring
## Goal 
4 separate spaces next to each other. The ask was to monitor temperature, humidity and light level in each of them. Wattmeter measurements are added to see overall power consumption.

## HW
 - ESP32 on Wemos D1 R32 development board

 - 4x DHT22 - temperature and humidity
   - https://docs.micropython.org/en/latest/esp8266/tutorial/dht.html
   - could be replaced by BMP280, GY21 or similar ...cheaper, smaller, standard bus, more devices on one bus link
   - compare: http://www.kandrsmith.org/RJS/Misc/Hygrometers/calib_many.html

 - 4x photoresistors
   - connected to onboard ADC
   - https://micropython-on-esp8266-workshop.readthedocs.io/en/latest/advanced.html#analog-to-digital-converter
   - possibility to utilize external ADC like [PCF8591](https://gitlab.com/cediddi/micropython-pcf8591) to remove dependancy on built-in analog inputs, to transfer analog values over shorter distances and to reduce used input pins (4x analog-in vs 2x I2C)

 - INA219 voltage and current measurement
   - https://github.com/chrisb2/pyb_ina219

## SW
[ThingSpeak](https://thingspeak.com) platform was used for a demo, but essentially any platofrm with REST API will work. ThingSpeak limits API calls to 1 per 15 seconds, which is sufficient for demo purposes.  
 Current code supports data upload through GET (Why the platform enables to POST data through GET?). 
To get inspired about data uploads through MicroPython urequests.POST method check https://github.com/neaxi/upy_workshop/blob/master/api.py


## code / snippets
`wifi_and_ntp.py` - src: https://github.com/neaxi/upy_workshop  
`ina219.py` and `logging.py` - src: https://github.com/chrisb2/pyb_ina219

