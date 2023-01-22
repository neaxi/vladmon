# connects to the WiFi network and sync time via NTP
from lib import daylightsaving
import time
import network
import ntptime
import machine
import sys

TIMEZONE_UTC_OFFSET = 1  #  1 = Central Europe / Prague
WAIT_FOR_CONNECT = 10

# create networking interface
sta_if = network.WLAN(network.STA_IF)


def progress_bar(ssid):
    for i in range(0, WAIT_FOR_CONNECT):
        if not (sta_if.isconnected()):
            print(f"{i:02} - " + "." * i + f" -> SSID: {ssid}", end="\r")
            time.sleep(1)
        else:
            break
    print()  # newline after the last progress print without it


def wifi_connect(ssid, pwd):
    """connect to wifi with provided password and print the result
    20 sec delay loop the check if we're connected
    """
    # activate the interface
    sta_if.active(True)

    # connect it to the network
    try:
        sta_if.connect(ssid, pwd)
    except OSError:
        # OSError: Wifi Internal Error
        # wifi connection failed
        # ignore the error and try another ID
        pass

    # check result
    print("Connection attempt to WiFi SSID:", ssid)
    progress_bar(ssid)
    print("Wifi connected:", sta_if.isconnected())
    print("Wifi config:", sta_if.ifconfig())


def sync_ntp_time():
    """In case we have active and connected wifi, sync RTC via NTP"""
    if not (sta_if.active()):
        print("Can't sync NTP. Wifi not active.")
    elif not (sta_if.isconnected()):
        print("Can't sync NTP. Wifi not connected.")
    else:
        try:

            epoch = ntptime.time()  # get UTC epoch time
            dt = time.gmtime(epoch)  # split do YMDhms
            dt = [str(d) for d in dt]  # int to str for concat
            print("NTP UTC time loaded:", "-".join(dt[0:3]), ":".join(dt[3:6]))
            tzc = apply_timezone_dst(epoch)
            machine.RTC().datetime(
                (tzc[0], tzc[1], tzc[2], tzc[6] + 1, tzc[3], tzc[4], tzc[5], 0)
            )
            del epoch, dt, tzc

        except OSError as exc:
            print(f"Failed to load NTP time. {exc}")


def apply_timezone_dst(utc):
    # NTP_DELTA = 3155673600 if time.gmtime(0)[0] == 2000 else 2208988800
    # utc += TIMEZONE_UTC_OFFSET * 3600  # apply timezone offset
    DS = daylightsaving.DaylightSaving(
        daylightsaving.DaylightSavingPolicy(0, 0, 3, 6, 2, 120),
        daylightsaving.StandardTimePolicy(0, 0, 10, 6, 3, 60),
    )
    new_time = DS.localtime(utc)
    del DS  # free the memory
    return time.gmtime(new_time)


def startup(ntw_list={}):
    """try all provided networks
    if connected sync NTP"""
    if ntw_list:
        for ssid, passwd in ntw_list.items():
            wifi_connect(ssid, passwd)
            if sta_if.isconnected():
                break
        if sta_if.isconnected():
            sync_ntp_time()
        else:
            print(
                f"NetworkFail: None of the '{','.join(ntw_list.keys())}' SSIDs has connected."
            )
    # cleanup NTP from imports
    if "ntptime" in sys.modules:
        del sys.modules["ntptime"]
