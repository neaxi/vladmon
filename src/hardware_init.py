from collections import namedtuple
from time import sleep

from machine import Pin, I2C, SoftI2C

import onewire, ds18x20
from ads1x15 import ADS1115
from sht3x import SHT31
from ssd1306 import SSD1306_I2C
from bh1750 import BH1750

import wifi_and_ntp

from oled import GFX

import config as CNFG
import log_setup

logger = log_setup.getLogger("hw_init")

Periph = namedtuple("Periph", ["id", "func", "friendly"])


class RelayControlled:
    def __init__(self, name, pin):
        self.name = name
        self.switch = pin
        self.enabled = False

    def on(self):
        logger.info(f"Turned on - {self.name}")
        self.enabled = True
        self.switch.value(0)

    def off(self):
        logger.info(f"Turned off - {self.name}")
        self.enabled = False
        self.switch.value(1)


class Pump(RelayControlled):
    def __init__(self, *args, **kwargs):
        super(Pump, self).__init__(*args, **kwargs)
        self.level_sensor = None
        self.cloud_allow = True

    def low_level(self):
        return self.level_sensor.value() == 1

    def on(self):
        if not self.low_level():
            super(Pump, self).on()
        else:
            logger.error("water too low; pump remains off")


class Fan(RelayControlled):
    def __init__(self, *args, **kwargs):
        super(Fan, self).__init__(*args, **kwargs)


class Light(RelayControlled):
    def __init__(self, *args, **kwargs):
        super(Light, self).__init__(*args, **kwargs)


def setup_i2c():
    return I2C(1, sda=Pin(CNFG.I2C_SDA), scl=Pin(CNFG.I2C_SCK), freq=CNFG.I2C_FREQ)


def setup_i2c_secondary():
    return SoftI2C(
        sda=Pin(CNFG.I2C_SEC_SDA), scl=Pin(CNFG.I2C_SEC_SCK), freq=CNFG.I2C_FREQ
    )


def setup_ads(i2c):
    return ADS1115(i2c, CNFG.ADS_ADDR, CNFG.ADS_GAIN)


def setup_lcd(i2c):
    lcd = SSD1306_I2C(CNFG.LCD_W, CNFG.LCD_H, i2c, 0x3C)
    lcd.fill(0)
    lcd.text("INIT", 40, 40, 1)
    lcd.show()
    return lcd


def setup_gfx(display):
    gfx = GFX(CNFG.LCD_W, CNFG.LCD_H, display.pixel)
    return gfx


def setup_bh1750(i2c):
    return BH1750(i2c)


def setup_onewire():
    bus = onewire.OneWire(Pin(CNFG.DS18_PIN))
    sensor = ds18x20.DS18X20(bus)
    logger.debug(f"DS18 devices: {sensor.scan()}")
    return sensor


def setup_sht3x(i2c):
    return SHT31(i2c)


def setup_relay():
    out = {}
    for name, no in CNFG.RELAY.items():
        out[name] = Pin(no, Pin.OUT)
        out[name].value(1)  # 1 = OFF
    return out


def setup_pump(relay):
    id = CNFG.R_ID_PUMP
    pump = Pump(name=id, pin=relay[id])
    pump.level_sensor = Pin(CNFG.WTR_LVL, Pin.IN, Pin.PULL_UP)
    return pump


def setup_fan(relay):
    id = CNFG.R_ID_FAN
    return Fan(name=id, pin=relay[id])


def setup_light(relay):
    id = CNFG.R_ID_LIGHT
    return Light(name=id, pin=relay[id])


# list of hardware and functions we want to init
DEV_I2C = [
    Periph("sht", setup_sht3x, "SHT3X"),
    Periph("lcd", setup_lcd, "SSD1306"),
    Periph("ads", setup_ads, "ADS1115"),
    Periph("bh1750", setup_bh1750, "BH1750"),
]

DEV = [
    Periph("ds18", setup_onewire, "DS18B"),
    Periph("relay", setup_relay, "Relay"),
]

DEV_REL = [
    Periph(CNFG.R_ID_PUMP, setup_pump, "Pump relay"),
    Periph(CNFG.R_ID_FAN, setup_fan, "Fan relay"),
    Periph(CNFG.R_ID_LIGHT, setup_light, "Light relay"),
]


class Initializer:
    def __init__(self):
        self.devices = {}

        self.i2c_devices = self.i2c_setup()
        self.init_all()

    def i2c_setup(self):
        # try to init I2C
        # I2C is a key, no I2C = death
        try:
            # create i2c interfaces and check what devices are visible
            self.devices["i2c"] = setup_i2c()
            self.devices["i2c_secondary"] = setup_i2c_secondary()
            i2c_dev = self.devices["i2c"].scan()
            i2c_dev += self.devices["i2c_secondary"].scan()

            logger.debug(f"Visible I2C addresses: {i2c_dev}")
            print("I2C OK - visible devices:")
            for dev in i2c_dev:
                print(f"  - 0x{dev} - {CNFG.I2C_LOOKUP[dev]}")
        except BaseException as err:
            logger.error(f"I2C setup failed: {err}")
            raise OSError("I2C not available")
        if not i2c_dev:
            logger.error(f"No I2C devices found")
            # raise OSError("I2C bus init failed")
        return i2c_dev

    def init_all(self):
        for device in DEV_I2C:
            # find I2C addr from config
            i2c_addr = 0
            for addr, name in CNFG.I2C_LOOKUP.items():
                if name in device.friendly:
                    i2c_addr = addr
            # if device not present, skip init
            if i2c_addr in self.i2c_devices:
                bus = self.devices["i2c"]
                if device.id == "lcd":
                    bus = self.devices["i2c_secondary"]
                self.devices[device.id] = self.init_periph(device, i2c=bus)
                if device.id == "lcd":
                    # if the device is not None, it happened before
                    if self.devices["lcd"]:
                        self.devices["gfx"] = setup_gfx(self.devices["lcd"])
            else:
                self.devices[device.id] = None
                logger.warn(
                    f"{device.friendly} not found on the I2C bus. Skipping init"
                )
            sleep(CNFG.T_BUS_DELAY)

        # unified init for relay and other peripherals with single except catch
        for device in DEV + DEV_REL:
            try:
                if device in DEV_REL:
                    self.devices[device.id] = self.init_periph(
                        device, self.devices["relay"]
                    )
                else:
                    self.devices[device.id] = self.init_periph(device)
            except OSError as e:
                logger.error(f"Init failed for {device}. Details: {e}")

        # init wifi and ntp
        logger.debug("Connecting wifi")
        self.devices["wifi"] = wifi_and_ntp.WifiScifi()
        self.devices["wifi"].attempt_connection(lcd=self.devices["lcd"])
        sleep(1)  # wait before NTP attempt
        self.devices["ntp"] = wifi_and_ntp.NtpSync()
        self.devices["ntp"].sync_ntp_time(self.devices["wifi"])

        sleep(1)
        del i2c_addr
        return self.devices

    def init_periph(self, device, i2c=None, relay=None):
        # attempt single device init
        fail = False
        result = None
        e_init = ""

        try:
            if i2c:

                result = device.func(i2c)
            elif relay:
                result = device.func(relay)
            else:
                result = device.func()
        except BaseException as err:
            fail = True
            e_init = err

        self.init_status(device, fail, e_init)
        sleep(0.5)
        del fail, e_init
        return result

    def init_status(self, device, fail=None, e_init=None):
        # inform user about init status
        msg = ""
        status = "FAIL"
        if fail:
            # msg = CNFG.MSG["init"](device.friendly, "FAIL")
            logger.warn(
                f"{device.friendly} failed on INIT. Exception details: {e_init}"
            )
        else:
            status = "OK"
            msg = CNFG.MSG["init"](device.friendly, status)
            logger.info(msg)

        try:
            if "lcd" in self.devices:
                if self.devices["lcd"]:
                    msg = CNFG.MSG_LCD["init"](device.friendly, status)
                    self.devices["lcd"].longtext(msg, CNFG.LCD_MAX_CHAR)
        except AttributeError as exc:
            logger.error(f"LCD issues - {exc}")
        del msg, status


if __name__ == "__main__":
    i = Initializer()
    print(i.devices)
