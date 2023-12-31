# https://github.com/dvsu/Sensirion-SHT3X-MicroPython

from ubinascii import hexlify
from time import sleep
from machine import I2C


class SHT3X:
    def __init__(self, bus_obj: I2C, address: int):
        self.address = address
        self.bus = bus_obj

    def get_temperature_in_celsius(self, data: int) -> float:
        #   Temperature conversion formula (Celsius)
        #   T[C] = -45 + (175 * (raw_temp_data / (2^16 - 1)))
        return round(-45 + (175 * (data / ((2**16) - 1))), 2)

    def get_relative_humidity(self, data: int) -> float:
        #   Relative humidity conversion formula
        #   RH = 100 * (raw_humidity_data / (2^16 - 1))
        return round(100 * (data / ((2**16) - 1)), 2)

    def get_measurement(self) -> dict:

        try:
            sleep(0.05)
            from machine import Pin

            trigger = Pin(33, Pin.OUT)
            # trigger.on()
            self.bus.writeto(self.address, b"\x2c\x06")
            # trigger.off()
            sleep(0.05)
            trigger.on()
            data = hexlify(self.bus.readfrom(self.address, 6))
            trigger.off()
            temp_data = int(data[0:4], 16)
            humi_data = int(data[6:10], 16)
            sleep(0.05)

            return {
                "temp_celsius": self.get_temperature_in_celsius(temp_data),
                "humidity": self.get_relative_humidity(humi_data),
            }

        except Exception as e:
            # print("Failed to read temperature and humidity value")
            raise (e)


class SHT31(SHT3X):
    def __init__(self, bus_obj: I2C):
        self.sensor_name = "SHT31"
        super().__init__(bus_obj, address=68)  # 0x44
