import time
import network

import config as CNFG


def align_to(msg, limit=CNFG.LCD_MAX_CHAR):
    return f"{msg:<{limit}}"


def align_to_center(msg, limit=CNFG.LCD_MAX_CHAR):
    return f"{msg:^{limit}}"


def newline():
    return align_to("")


def parse(msgs: list) -> str:
    return "".join(map(align_to, msgs))


def ds18_and_light(ds18, bh) -> str:
    msgs = []
    for id, value in ds18.items():
        id = hex(id[-1]).replace("0x", "\\")
        msgs.append(f"DS{id}: {value:.4} C")
    msgs.append(newline())
    msgs.append(f"Light: {bh:>.4} lm")
    return parse(msgs)


def sht(data) -> str:
    msgs = ["Atmsphr data"]
    msgs.append(newline())
    msgs.append(newline())
    msgs.append(f"Temp: {data['cels']} C")
    msgs.append(newline())
    msgs.append(f"Humi: {data['hum']} %")
    return parse(msgs)


def network_status(sta_if) -> str:
    # get network and ntp data
    msgs = []
    if not sta_if.isconnected():
        msgs.append("Status: Offline")
        return parse(msgs)
    msgs.append("Status: Connectd")
    msgs.append("IP addr:")
    msgs.append(sta_if.ifconfig()[0])
    msgs.append(newline())
    dt = [f"{dt:02}" for dt in time.localtime()]  # zero padding +str for time and date
    msgs.append("-".join(dt[0:3]))  # date
    msgs.append(":".join(dt[3:6]))  # time
    return parse(msgs)


def network_error(lcd, gfx):
    """clear top half of the display and show the banner there"""
    gfx.fill_rect(0, 0, 128, 32, 0)
    lcd.show()
    lcd.longtext(CNFG.MSG_LCD["offline"], CNFG.LCD_MAX_CHAR, clear=False)


def soil_humidity(data):
    msgs = ["Soil humidity"]
    msgs.append(newline())
    msgs.append(f"0: {data.ads[0]:<3}%   AVRGE:")
    msgs.append(f"1: {data.ads[1]:<3}%   {data.ads_avg:<3} %")
    msgs.append(f"2: {data.ads[2]:<3}%   TRIGG:")
    msgs.append(f"3: {data.ads[3]:<3}%   {CNFG.TRG_SOIL:<3} %")

    # for channel in range(CNFG.ADS_CHANNELS):
    #     val = f"{data.ads[channel]}"
    #     msgs.append(f"{channel}: {val:>8} %")
    # msgs.append(f"AVG: {data.ads_avg}% | TRIG: {CNFG.TRG_SOIL} %")
    return parse(msgs)


def relay_states(relay):
    msgs = ["Relay"]
    msgs.append(newline())
    # find len of max. string
    for name, pin in relay.items():
        state = "OFF" if pin.value() == 1 else "ON"
        name = name if len(name) < 10 else name[:10]
        msgs.append(f"{state:3} - {name}")
    return parse(msgs)


def autostart_aborted():
    msgs = []
    msgs.append(newline())
    msgs.append(align_to_center("AUTOSTART"))
    msgs.append(align_to_center("ABORTED"))
    msgs.append(newline())
    return parse(msgs)
