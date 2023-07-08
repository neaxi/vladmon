import gc
import time
from machine import Pin, I2C, ADC, SPI

import uasyncio

import urequests

import log_setup

import config as CNFG
from hardware_init import Initializer
from datastore import Data as DS
import lcd

from blynk import BlApi

logger = log_setup.getLogger("main")

gc.enable()  # to make sure auto garbage collect is ON
gc.threshold(60000)  # if the app allocates more, trigger GC


def mem_cleanup():
    start = gc.mem_free()
    gc.collect()
    free = gc.mem_free()
    logger.debug(f"Freed {free - start} bytes of RAM. Current: {free}")
    del start, free


class Orchestrator:
    def __init__(self):
        """init hardware and datastore"""
        logger.info("Initing hardware")
        init = Initializer()
        self.hw = init.devices
        self.data = DS()
        logger.info("Initing cloud comm")
        self.cloud = BlApi()

    async def cr_measure(self):
        """measure oneshot sensors in periodic intervals"""
        while True:
            # DS18
            if self.hw["ds18"]:
                if len(self.hw["ds18"].scan()) > 0:
                    self.data.update_ds18(self.hw["ds18"])
                else:
                    logger.warn("No DS18 devices found. Skipping...")
            # BH1750
            time.sleep(CNFG.T_BUS_DELAY)
            if self.hw["bh1750"]:
                self.data.update_bh1750(self.hw["bh1750"])
            # SHT3X
            time.sleep(CNFG.T_BUS_DELAY)
            if self.hw["sht"]:
                self.data.update_sht3x(self.hw["sht"])
            # ADS
            time.sleep(CNFG.T_BUS_DELAY)
            if self.hw["ads"]:
                self.data.update_ads(self.hw["ads"])
            logger.info("Collection cycle - OK")
            await uasyncio.sleep(CNFG.T_MEAS)

    async def cr_lcd(self):
        while True:
            # prepare LCD frames; only if data are present
            self.data.lcd_messages.append(lcd.network_status(self.hw["wifi"].sta_if))
            if self.data.ds18 and self.data.bh1750:
                self.data.lcd_messages.append(
                    lcd.ds18_and_light(self.data.ds18, self.data.bh1750)
                )
            if self.data.sht:
                self.data.lcd_messages.append(lcd.sht(self.data.sht))
            if self.data.ads:
                self.data.lcd_messages.append(lcd.soil_humidity(self.data.ads))
            if self.hw["relay"]:
                self.data.lcd_messages.append(lcd.relay_states(self.hw["relay"]))

            # show them one by one
            while self.data.lcd_messages:
                msg = self.data.lcd_messages.pop()
                logger.debug(f"LCD msg: {msg}")
                try:
                    self.hw["lcd"].longtext(msg, CNFG.LCD_MAX_CHAR)
                    await uasyncio.sleep(CNFG.T_LCD_FRAME - 1)
                    # show "offline" msg for 1 sec
                    if not self.hw["wifi"].sta_if.isconnected():
                        lcd.network_error(self.hw["lcd"], self.hw["gfx"])
                    await uasyncio.sleep(1)

                except (OSError, AttributeError):
                    logger.error("Failed to display LCD text")
                    await uasyncio.sleep(CNFG.T_LCD_FRAME)

    async def cr_relays(self):
        while True:
            # soil humidity check - on/off pump
            if self.data.ads:
                avg = sum(self.data.ads) / len(self.data.ads)
                if avg < CNFG.TRG_SOIL:
                    logger.info(
                        f"Soil hum is below {CNFG.TRG_SOIL} % target ... {avg} %."
                    )
                    # if we are not turned on yet
                    if not self.hw[CNFG.R_ID_PUMP].enabled:
                        # if cloud settings allow us to be turned on
                        if self.hw[CNFG.R_ID_PUMP].cloud_allow:
                            # if we have enough water in the tank
                            if not self.hw[CNFG.R_ID_PUMP].low_level():
                                logger.info(f"Turning on pump.")
                                self.hw[CNFG.R_ID_PUMP].on()
                        else:
                            logger.warn(
                                "Pump not turned on, because cloud does not allow it."
                            )
                elif self.hw[CNFG.R_ID_PUMP].enabled:
                    # turn off when humidity gets above trigger
                    self.hw[CNFG.R_ID_PUMP].off()
                # if the pump is running and level drops too low, turn off
                if (
                    self.hw[CNFG.R_ID_PUMP].low_level()
                    and self.hw[CNFG.R_ID_PUMP].enabled
                ):
                    logger.warn(f"Water level became too low. Shutting pump")
                    self.hw[CNFG.R_ID_PUMP].off()
                # pump was running, but got turned off in the cloud
                if (
                    self.hw[CNFG.R_ID_PUMP].enabled
                    and not self.hw[CNFG.R_ID_PUMP].cloud_allow
                ):
                    logger.info("Cloud turned the pump off")
                    self.hw[CNFG.R_ID_PUMP].off()
                del avg

            # atm humidity check; on/off fan
            if self.data.sht:
                if self.data.sht["hum"] > CNFG.TRG_ATM:
                    if not self.hw[CNFG.R_ID_FAN].enabled:
                        self.hw[CNFG.R_ID_FAN].on()
                elif self.hw[CNFG.R_ID_FAN].enabled:
                    self.hw[CNFG.R_ID_FAN].off()

            # current time check; on/off light
            if time.localtime()[0] != 2000:  # NTP got synced and is not default
                light_on = False
                for interval in CNFG.TRG_LIGHT:
                    current = time.localtime()
                    start = tuple(map(int, interval[0].split(":")))
                    end = tuple(map(int, interval[1].split(":")))

                    if start <= (current[3], current[4]) <= end:
                        light_on = True
                        break
                del start, end
                if light_on:
                    if not self.hw[CNFG.R_ID_LIGHT].enabled:
                        self.hw[CNFG.R_ID_LIGHT].on()
                elif self.hw[CNFG.R_ID_LIGHT].enabled:
                    self.hw[CNFG.R_ID_LIGHT].off()
            else:
                logger.warn("NTP not synced, light setting not changed")

            await uasyncio.sleep(CNFG.T_RELAY)

    async def cr_cloud(self):
        while True:
            mem_cleanup()
            self.cloud.update_streams(self.hw, self.data)

            if self.hw["wifi"].sta_if.isconnected():
                # resync time if network works and it did not work before
                if not self.hw["ntp"].synced:
                    self.hw["ntp"].sync_ntp_time(self.hw["wifi"])
                self.cloud.fetch_pump_setting(self.hw)
            else:
                logger.warn("Pump setting fetch not attempted.")
            mem_cleanup()
            await uasyncio.sleep(CNFG.T_NETWORK_UPDATE)

    def start(self):
        logger.info("Entering asyncio loop")
        loop = uasyncio.get_event_loop(runq_len=40, waitq_len=40)
        loop.create_task(self.cr_measure())
        loop.create_task(self.cr_lcd())
        loop.create_task(self.cr_relays())

        if self.cloud:
            loop.create_task(self.cr_cloud())

        loop.run_forever()


if __name__ == "__main__":
    """def main() not used to expose master obj in global REPL"""

    try:
        master = Orchestrator()
        logger.info("Master created.")
        mem_cleanup()

        autostart = Pin(CNFG.AUTOSTART, Pin.IN, Pin.PULL_UP)
        if autostart.value() == 0:
            logger.warn(f"Autostart pin (G{CNFG.AUTOSTART}) grounded. Start aborted...")
            master.hw["lcd"].longtext(lcd.autostart_aborted(), CNFG.LCD_MAX_CHAR)
        else:
            del autostart  # throw the object away, not needed anymore
            master.start()

    except KeyboardInterrupt:
        logger.info("stopped by user")
