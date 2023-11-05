from array import array
from micropython import const

LOG_LEVEL = const(20)  # 10 = DEBUG; 20 = INFO


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
TRG_SOIL = const(70)

# if atmospheric RH get over X %, turn on the fan
TRG_ATM = const(70)

# defines how many intervals has the trigger condition be met before taking action
TRG_COUNT = 6  # * T_MEAS = time interval in seconds

# ----------------------------------------
#                 WIFI / NETWORK
# ----------------------------------------
TIMEZONE_UTC_OFFSET = const(1)  #  1 = Central Europe / Prague

# dictionary of SSID & passwords to which we attempt connection
NETWORKS = {
    "wifi": "wifi_password"
    # "backup": "secondary_password"
}

DHCP_HOSTNAME = const("boxmon")
# how much seconds wait for WiFi to assign an IP
WIFI_CONNECT_TIMEOUT = const(10)
# how many times wifi attempts to reconnect before complete restart
RECONN_ATTEMPT = const(5)
# sec. used for API requests
HTTP_TIMEOUT = const(10)


# ----------------------------------------
#                 CLOUD
# ----------------------------------------
BLYNK_TOKEN = const("DnaWsgUe8xfC1Ig8Hfg4Am5wYgMZ65JY")
BLYNK_SINGLE_URL = (
    "http://fra1.blynk.cloud/external/api/{func}?token=%s&" % BLYNK_TOKEN
)  # fetching data over plain HTTP ... HTTPS was causing endless loop
BLYNK_BULK_URL = (
    "https://fra1.blynk.cloud/external/api/batch/update?token=%s&" % BLYNK_TOKEN
)
# blynk virtual pin mapping
BL_VPIN = {
    # light senser
    "BH1750": const(12),
    # soil humidity channels
    "ADS": [const(5), const(6), const(7), const(8)],
    # SHT3x atmospheric temp & humidity
    "SHT": [const(10), const(11)],
    # relay indicators
    "R_FAN": const(16),
    "R_LGHT": const(17),
    "R_PUMP": const(15),
    "EN_PUMP": const(14),
    # water level
    "WTR_LVL": const(13),
}

# the IDs double as virtual pins for blynk!
DS_IDS = {
    0: b"(\xf5Wv\xe0\x01<\xfc",  # ['0x28', '0xf5', '0x57', '0x76', '0xe0', '0x1', '0x3c', '0xfc']
    1: b"(\xac\xa4v\xe0\xff<\xe9",  # ['0x28', '0xac', '0xa4', '0x76', '0xe0', '0xff', '0x3c', '0xe9']
}

# ----------------------------------------
#                 TIMERS
# ----------------------------------------
T_MEAS = const(5)  # how often refresh data from sensors
T_LCD_FRAME = const(5)  # how long single LCD frame is displayed
T_RELAY = const(5)  # how often do we check in relay control loop
T_NETWORK_UPDATE = const(60)  # how often to push data to cloud
T_BUS_DELAY = const(
    0.2
)  # used for troubleshooting to slow down read operations from I2C

# ----------------------------------------
#                 SENSOR PINS
# ----------------------------------------

AUTOSTART = const(32)  # loop kill switch. stops after init if grounded

# DS18B - 1 pin .. mulitple sensors on a bus
DS18_PIN = const(33)

# relay - 4 pins
R_ID_FAN = const("fan")
R_ID_LIGHT = const("light")
R_ID_PUMP = const("pump")
RELAY = {R_ID_PUMP: const(19), R_ID_LIGHT: const(18), R_ID_FAN: const(5)}

# water level
WTR_LVL = const(13)

# ----------------------------------------
#                 I2C
# ----------------------------------------
I2C_SDA = const(21)
I2C_SCK = const(22)
# secondary software I2C for LCD
# in case the hardware I2C goes down
# as seen with SHT3X issues
I2C_SEC_SDA = const(14)
I2C_SEC_SCK = const(27)

I2C_FREQ = const(50000)
# I2C addresses + human names for peripherals
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
LCD_W = const(128)
LCD_H = const(64)
LCD_MAX_CHAR = const(16)

# ----------------------------------------
#                 ADS1115 - anything related to reading analog values from soil sensors
# ----------------------------------------
ADS_ADDR = const(0x48)  # 72
ADS_GAIN = const(0)
ADS_CHANNELS = const(4)
ADS_MAX = const(32767)
ADS_BUFFERSIZE = const(512)

ADS_ARRAY = array("h", (0 for _ in range(ADS_BUFFERSIZE)))
ADS_OFFSET = 0.0018  # balanced through calib spreadsheet

SOIL_MAX = int(3.7 / 5 * ADS_MAX)  # 3.7 V - submerged in water
SOIL_MIN = int(1.8 / 5 * ADS_MAX)  # 1.8 V - dry on the desk
SOIL_RANGE = SOIL_MAX - SOIL_MIN
SOIL_GROUNDED_INPUT_LEVEL = 100

# ----------------------------------------
#                 MESSAGE TEMPLATES
# ----------------------------------------
MSG = {
    "init": (lambda dev, status: f"init {dev} ... {status}"),
}

MSG_LCD = {
    "init": lambda dev, status: f"{'Initing':<16}  {dev:<14} ... {status}",
    "conn": lambda ssid, chars: f'{"SSID":<{chars}}{ssid:<{chars}}',
    # "offline": f"{'!'*16}!{' ' * 14}!!{'NETWORK':^14}!!{'OFFLINE':^14}!!{' ' * 14}!{'!'*16}",
    "offline": f"!!{'NETWORK':^12}!!!!{'OFFLINE':^12}!!{'-' * 16}",
}
