import time
import config as CNFG
from bh1750 import BH1750

import log_setup

logger = log_setup.getLogger("datastore")


def meas_ds18(ds_sensor) -> dict:
    out = {}
    try:
        ds_sensor.convert_temp()
    except:
        logger.error("DS18 - Failed to convert_temp")
        return out
    time.sleep_ms(750)
    for _, addr in CNFG.DS_IDS.items():
        try:
            out[addr] = ds_sensor.read_temp(addr)
        except Exception as exc:
            out[addr] = 0
            logger.error(f"DS18 {addr} - Failed to read_temp. {exc}")
    return out


def meas_sht3x(sht) -> dict:
    try:
        m = sht.get_measurement()
        return {"cels": m["temp_celsius"], "hum": m["humidity"]}
    except OSError as exc:
        logger.error(f"SHT3X - Failed to get_measurement. {exc}")
        return {"cels": 0, "hum": 0}


def meas_bh1750(bh) -> float:
    try:
        return int(bh.luminance(BH1750.ONCE_HIRES_1))
    except:
        logger.error("BH1750 - Failed to read luminance")
        return 0


def meas_ads1115(ads) -> list:
    out = []
    for channel in range(CNFG.ADS_CHANNELS):
        try:
            meas = ads.read(channel1=channel)
            if meas < CNFG.SOIL_GROUNDED_INPUT_LEVEL or meas > CNFG.SOIL_MAX:
                # anything below 100 is zero .. most likely grounded input
                # or above MAX level as MAX = no water
                out.append(0)
            else:
                # subtract the MIN value from measured to have a 0 reference
                # compute % out of the measurement using the soil sensor range instead of the ADC range
                # subtract the results from 100, because it's inverse: more water => lower voltage
                out.append(100 - int(((meas - CNFG.SOIL_MIN) / CNFG.SOIL_RANGE) * 100))
            del meas
        except Exception as exc:
            logger.error(f"ADS1115 - failed to read channel {channel}. {exc}")
            out.append(0)  # to prevent missing indexes
    return out


class Data:
    """data storage and interface to measurement methods"""

    def __init__(self):
        self.lcd_messages = []
        self.ds18 = {}
        self.sht = {}
        self.bh1750 = 0
        self.ads = []
        self.ads_avg = 0

    def lcd_store_frame(self, msg):
        self.lcd_messages.append(msg)

    def update_ds18(self, device):
        self.ds18 = meas_ds18(device)
        logger.debug(f"DS18: {self.ds18}")

    def update_sht3x(self, device):
        self.sht = meas_sht3x(device)
        logger.debug(f"SHT3X {self.sht}")

    def update_bh1750(self, device):
        self.bh1750 = meas_bh1750(device)
        logger.debug(f"BH1750 {self.bh1750}")

    def update_ads(self, device):
        self.ads = meas_ads1115(device)
        # compute average
        soil_hum = None
        if self.ads:
            # if the data exist, filter out zeros (grounded pins)
            soil_hum = [hum for hum in self.ads if hum >= 1]
            if not soil_hum:
                logger.warn(
                    "No soil humidity data available to calculate average value"
                )
            else:
                self.ads_avg = sum(soil_hum) / len(soil_hum)
        logger.debug(f"ADS1115 {self.ads}")
