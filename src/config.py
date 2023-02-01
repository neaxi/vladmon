from array import array

LOG_LEVEL = 10  # 10 = DEBUG; 20 = INFO

# ----------------------------------------
#                 WIFI / NETWORK
# ----------------------------------------
NETWORKS = {"IoT": "***REMOVED***"}
HTTP_TIMEOUT = 10  # sec
DHCP_HOSTNAME = "boxmon"
TIMEZONE_UTC_OFFSET = 1  #  1 = Central Europe / Prague
WIFI_CONNECT_TIMEOUT = 10
RECONN_ATTEMPT = 5  # how many times wifi attempts to reconnect before complete restart

# ----------------------------------------
#                 TRIGGERS
# ----------------------------------------

# when current time is between intervals, turn on the light
TRG_LIGHT = [
    ("8:00", "9:00"),
    ("11:00", "12:00"),
    ("15:35", "16:55"),
]

# if soil humidity gets below X %, turn on the pump
TRG_SOIL = 0

# if atmospheric RH get over X %, turn on the fan
TRG_ATM = 70

# ----------------------------------------
#                 CLOUD
# ----------------------------------------
BLYNK_TOKEN = "DnaWsgUe8xfC1Ig8Hfg4Am5wYgMZ65JY"
BLYNK_SINGLE_URL = (
    "http://fra1.blynk.cloud/external/api/{func}?token=%s&" % BLYNK_TOKEN
)  # fetching data over plain HTTP ... HTTPS was causing endless loop
BLYNK_BULK_URL = (
    "https://fra1.blynk.cloud/external/api/batch/update?token=%s&" % BLYNK_TOKEN
)
BL_VPIN = {
    "BH1750": 12,
    "ADS": [5, 6, 7, 8],
    "SHT": [10, 11],
    "R_FAN": 16,
    "R_LGHT": 17,
    "R_PUMP": 15,
    "EN_PUMP": 14,
    "WTR_LVL": 13,
}

# the IDs double as virtual pins for blynk!
DS_IDS = {
    0: b"(\xf5Wv\xe0\x01<\xfc",  # ['0x28', '0xf5', '0x57', '0x76', '0xe0', '0x1', '0x3c', '0xfc']
    1: b"(\xac\xa4v\xe0\xff<\xe9",  # ['0x28', '0xac', '0xa4', '0x76', '0xe0', '0xff', '0x3c', '0xe9']
}

# ----------------------------------------
#                 TIMERS
# ----------------------------------------
T_MEAS = 5  # how often refresh data from sensors
T_LCD_FRAME = 5  # how long single LCD frame is displayed
T_RELAY = 5  # how often do we check in relay control loop
T_NETWORK_UPDATE = 60  # how often to push data to cloud
T_BUS_DELAY = 0.2  # used for troubleshooting to slow down read operations from I2C

# ----------------------------------------
#                 PINS
# ----------------------------------------

AUTOSTART = 32  # stops execution after init if grounded

# DS18B - 1 pin .. mulitple sensors on a bus
DS18_PIN = 4


# relay - 4 pins
R_ID_FAN = "fan"
R_ID_LIGHT = "light"
R_ID_PUMP = "pump"
RELAY = {R_ID_PUMP: 19, R_ID_LIGHT: 18, R_ID_FAN: 5}

# water level
WTR_LVL = 13

# ----------------------------------------
#                 I2C
# ----------------------------------------
I2C_SDA = 21
I2C_SCK = 22
# secondary software I2C for LCD
# in case the hardware I2C goes down
# as seen with SHT3X issues
I2C_SEC_SDA = 14
I2C_SEC_SCK = 27

I2C_FREQ = 50000
I2C_LOOKUP = {
    35: "BH1750",
    60: "SSD1306",
    64: "INA3221",
    68: "SHT3X",
    69: "CJMCU-3001",
    72: "ADS1115",
}

# ----------------------------------------
#                 LCD
# ----------------------------------------
LCD_W = 128
LCD_H = 64
LCD_MAX_CHAR = 16

# ----------------------------------------
#                 ADS1115
# ----------------------------------------
ADS_ADDR = 0x48  # 72
ADS_GAIN = 0
ADS_CHANNELS = 4
ADS_MAX = 32767
ADS_BUFFERSIZE = const(512)
ADS_KEPT_VALUES = 5  # how many past measurements are we keeping

ADS_ARRAY = array("h", (0 for _ in range(ADS_BUFFERSIZE)))
ADS_OFFSET = 0.0018  # balanced through calib spreadsheet


MSG = {
    "init": (lambda dev, status: f"init {dev} ... {status}"),
}

MSG_LCD = {
    "init": lambda dev, status: f"{'Initing':<16}  {dev:<14} ... {status}",
    "conn": lambda ssid, chars: f'{"SSID":<{chars}}{ssid:<{chars}}',
    # "offline": f"{'!'*16}!{' ' * 14}!!{'NETWORK':^14}!!{'OFFLINE':^14}!!{' ' * 14}!{'!'*16}",
    "offline": f"!!{'NETWORK':^12}!!!!{'OFFLINE':^12}!!{'-' * 16}",
}
