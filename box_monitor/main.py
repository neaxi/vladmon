try:
    from config import PINS_DHT, PINS_PHOTO, PINS_INA, SHUNT_OHMS, THINGSPEAK_URL, PHOTO_MAX, DUTY_CYCLE
except:
    raise RuntimeError('Missing one of the configuration constants from ./config.py')

try:
    from ina219 import INA219
    from logging import WARNING
except:
    raise RuntimeError('Missing libraries for voltage/current measurements. Please download them from: https://github.com/chrisb2/pyb_ina219')

from machine import Pin, ADC, I2C
from time import sleep
from utime import localtime
from dht import DHT22

import network
import wifi_and_ntp

import urequests
import json


class Box_Monitor():
    def __init__(self):
        self.sensors_dht = []
        self.sensors_photo = []
        self.sensor_ina219 = None
        self.data = {}
     
     
    def __check_pins_from_user(self, input):
        # used for init functions to verify user provided a list
        if not isinstance(input, list):
            raise TypeError('Please provide list of pins')


    def init_dht(self, pins=None):
        self.__check_pins_from_user(pins)
        for pin in pins:
            self.sensors_dht.append(DHT22(Pin(pin)))


    def init_photo(self, pins=None):
        self.__check_pins_from_user(pins)
        for pin in pins:
            self.sensors_photo.append(ADC(Pin(pin)))


    def init_va(self, pins=None):
        self.__check_pins_from_user(pins)
        i2c = I2C(-1, sda=Pin(pins[0]), scl=Pin(pins[1]))  # SDA, SCL
        self.sensor_ina219 = INA219(SHUNT_OHMS, i2c, log_level=WARNING)
        self.sensor_ina219.configure()
        
        
    def measure_dhts(self):
        # obtain data from the sensors and round them to one decimal
        # if the sensor is not available, record zeroed values
        results = []
        for dht in self.sensors_dht:
            try:
                dht.measure()
                results.append((round(dht.temperature(), 1),
                                round(dht.humidity(), 1)))
            except:
                # zero values when reading the DHT fails
                results.append((0, 0))
        self.data['dht'] = results
        return results


    def measure_photo(self): 
        results = []
        for photo in self.sensors_photo:
            # get percents, rounded to 2 decimals 
            raw = photo.read()
            results.append(round((raw / PHOTO_MAX) * 100, 2))
        self.data['photo'] = results
        return results
    
    
    def measure_va(self):
        ''' queries INA219, returns mW '''
        self.data['ina'] = round(self.sensor_ina219.voltage() * self.sensor_ina219.current(), 1)
        return self.data['ina']


    def refresh_measurements(self):
        boxmon.measure_dhts()
        boxmon.measure_photo()
        boxmon.measure_va()


    def __api_get(self, url):
        resp = urequests.get(url)
        #print("request status:", str(resp.status_code), str(resp.reason))
        #print("Response - raw data:", resp.text)
        resp.close()
        return resp


    def data_api_write(self, counter=None):
        # data order in the ThingSpeak
        # wattmeter, photo 1, photo 2, photo 3, dht temp 1, dht hum1, dht temp 2, dht hum 2 
        payload = [self.data['ina'],
                   self.data['photo'][0], self.data['photo'][1], self.data['photo'][2],
                   self.data['dht'][0][0], self.data['dht'][0][1],
                   self.data['dht'][3][0], self.data['dht'][3][1]]
        
        values_string = ''.join(list(['&field{}={}'.format(i+1, val) for i, val in enumerate(payload)]))
        if counter and counter % 10 == 0:
            values_string += '&status=Successful API call streak: ' + str(counter)
        target_url = '{}{}'.format(THINGSPEAK_URL, values_string)

        status = self.__api_get(target_url)
        info = '{} - {}'.format(status.status_code, status.reason)
        
        del values_string
        return info
        
        
    def exception_poster(payload):
        __api_get(THINGSPEAK_URL, payload)



sta_if = network.WLAN(network.STA_IF)


boxmon = Box_Monitor()
boxmon.init_dht(pins=PINS_DHT)  # DHT22
boxmon.init_photo(pins=PINS_PHOTO)  # photoresistors
boxmon.init_va(pins=PINS_INA)   # ina219 

success_api_call_counter = 0
while True:
    # refresh data coming from all sensors
    boxmon.refresh_measurements() 
    #print(boxmon.measure_photo())
    #print(boxmon.measure_dhts())
    #print(boxmon.measure_va())
    
    # check if we have active wifi connection
    # if not, sleep and try again
    if not sta_if.isconnected():
        wifi_and_ntp.startup()
        if not sta_if.isconnected():
            print('Wi-Fi not available. Sensor data not sent.')
            sta_if.disconnect()  # prevent unnecessary automatic reconnect attempts  
            sleep(DUTY_CYCLE)
            continue
    
    # upload to cloud
    try:
        status = boxmon.data_api_write(success_api_call_counter)
    except Exception as e:
        boxmon.exception_poster(e)
        print(e)
        sleep(DUTY_CYCLE)
    
    # print result on the CLI 
    dt = localtime()
    dt = [str(d) for d in dt] # int to str for concat
    timestamp = '{} {}'.format('-'.join(dt[0:3]), ':'.join(dt[3:6]))
    print('{} | {} | {}'.format(timestamp, status, boxmon.data))
    
    success_api_call_counter += 1
    sleep(DUTY_CYCLE)

