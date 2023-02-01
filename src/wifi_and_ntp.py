# connects to the WiFi network and sync time via NTP
from lib import daylightsaving
import time
import network
import ntptime
import machine
import sys
import gc

import config as CNFG

import log_setup

logger = log_setup.getLogger("wifintp")


class WifiScifi:
    def __init__(self):
        self.conn_attempts = 1

        self.ap = None
        self.deactivate_ap()
        self.sta_if = None

        # create client interface
        if not self.sta_if:
            self.sta_if = network.WLAN(network.STA_IF)

    def deactivate_ap(self):
        """make sure AP mode is off"""
        if not self.ap:
            self.ap_if = network.WLAN(network.AP_IF)
        if self.ap_if.active():
            self.ap_if.active(False)
        del self.ap_if

    def connect(self, ssid, pwd):
        gc.collect()
        try:
            self.sta_if.disconnect()
            time.sleep(2)
        except OSError:
            # OSError: Wifi Not Started
            # already disconnected, no issue here
            pass

        # bounce before connect attempt
        if self.sta_if.active():
            self.sta_if.active(False)
            time.sleep(1)

        self.sta_if.active(True)

        # 1ms before config
        # https://github.com/micropython/micropython/issues/8792#issuecomment-1161447599
        # https://github.com/micropython/micropython/commit/d6bc34a13aa734d8b32e5768c021377ac4815029
        time.sleep_us(100)
        self.sta_if.config(dhcp_hostname=CNFG.DHCP_HOSTNAME)
        time.sleep_us(100)  # extra sleep before connecting

        logger.debug("Connection attempt to WiFi SSID:", ssid)
        self.sta_if.connect(ssid, pwd)

    def check_wifi_connected(self, ssid, lcd=None):
        """print current state and set connection counter"""
        for i in range(0, CNFG.WIFI_CONNECT_TIMEOUT):
            if not (self.sta_if.isconnected()):
                msg = f"SSID: {ssid} {'.' * i}"
                print(msg, end="\r")
                if lcd:
                    msg = CNFG.MSG_LCD["conn"](ssid, CNFG.LCD_MAX_CHAR) + "." * i
                    lcd.longtext(msg, CNFG.LCD_MAX_CHAR)
                time.sleep(1)
            else:
                break
        print()  # newline after the last progress print without it

        logger.info("Wifi connected:", self.sta_if.isconnected())
        logger.info("Wifi config:", self.sta_if.ifconfig())

        if not self.sta_if.isconnected():
            self.conn_attempts += 1
            return False
        else:
            self.conn_attempts = 0
            return True

    def attempt_connection(self, ntw_list=CNFG.NETWORKS, lcd=None, reset=False):
        for ssid, passwd in ntw_list.items():
            self.connect(ssid, passwd)
            self.check_wifi_connected(ssid, lcd)
            if self.sta_if.isconnected():
                break

        if not self.sta_if.isconnected():
            logger.info(
                f"NetworkFail: None of the '{', '.join(ntw_list.keys())}' SSIDs has connected."
            )

        if reset:
            logger.debug(
                f"Reconnection attempts: {self.conn_attempts}. Autoreboot trigger: {CNFG.RECONN_ATTEMPT}"
            )
            if self.conn_attempts >= CNFG.RECONN_ATTEMPT:
                logger.warn(
                    "Autoreboot triggered due to unsuccessful network connection"
                )
                machine.reset()


class NtpSync:
    def __init__(self):
        self.synced = False

    def sync_ntp_time(self, wifi):
        """In case we have active and connected wifi, sync RTC via NTP"""
        if not (wifi.sta_if.active()):
            logger.error("Can't sync NTP. Wifi not active.")
        elif not (wifi.sta_if.isconnected()):
            logger.error("Can't sync NTP. Wifi not connected.")
        else:
            try:

                epoch = ntptime.time()  # get UTC epoch time
                dt = time.gmtime(epoch)  # split do YMDhms
                dt = [str(d) for d in dt]  # int to str for concat
                logger.info(
                    "NTP UTC time loaded:", "-".join(dt[0:3]), ":".join(dt[3:6])
                )
                tzc = self.apply_timezone_dst(epoch)
                machine.RTC().datetime(
                    (tzc[0], tzc[1], tzc[2], tzc[6] + 1, tzc[3], tzc[4], tzc[5], 0)
                )
                del epoch, dt, tzc
                self.synced = True
                # cleanup NTP from imports
                if "ntptime" in sys.modules:
                    del sys.modules["ntptime"]

            except OSError as exc:
                logger.error(f"Failed to load NTP time. {exc}")

    def apply_timezone_dst(self, utc):
        # NTP_DELTA = 3155673600 if time.gmtime(0)[0] == 2000 else 2208988800
        # utc += TIMEZONE_UTC_OFFSET * 3600  # apply timezone offset
        DS = daylightsaving.DaylightSaving(
            daylightsaving.DaylightSavingPolicy(0, 0, 3, 6, 2, 120),
            daylightsaving.StandardTimePolicy(0, 0, 10, 6, 3, 60),
        )
        new_time = DS.localtime(utc)
        del DS  # free the memory
        return time.gmtime(new_time)
