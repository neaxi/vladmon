WIFI_SSID = 'YOUR_SSID_HERE'
WIFI_PASSWD = 'WIFI_PWD'

THINGSPEAK_API_KEY = 'PRIVATE_API_KEY'
THINGSPEAK_URL = 'https://api.thingspeak.com/update?api_key=' + THINGSPEAK_API_KEY

# based on Wemos D1 R32
# switch pin order to reorder the devices
PINS_DHT = [16, 17, 25, 26]  # any
PINS_PHOTO = [35, 34, 36, 39] # analog inputs: [32..39] are valid ADC pins
PINS_INA = [21, 22]  # SDA = 21, SCL = 22

# INA219 setup ... needs R value from the PCB
SHUNT_OHMS = 0.1

# photo resistor setup
# set max value with full brightness here for correct percentage calculation
# defined as (raw_value / PHOTO_MAX) * 100
# ADC returns 0-4095 (12 bit)
PHOTO_MAX = 2048

# sleep time between measurement cycles in seconds
DUTY_CYCLE = 60
