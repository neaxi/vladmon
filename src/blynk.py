import gc
import lib.urequests as urequests
import config as CNFG
import log_setup
import wifi_and_ntp


logger = log_setup.getLogger("api")


class BlApi:
    def __init__(self):
        pass

    def create_payload(self, hw, data):

        values = []

        # DS18
        if len(hw["ds18"].scan()) > 0:
            for pin, id in CNFG.DS_IDS.items():
                try:
                    if data.ds18[id]:
                        values.append((pin, data.ds18[id]))
                except KeyError:
                    logger.warn(f"DS18 {id} not in data dict")
        # BH1750
        # 0 lx is a common value, we want to send those too
        if data.bh1750 or data.bh1750 == 0:
            values.append((CNFG.BL_VPIN["BH1750"], data.bh1750))

        # ADS
        if data.ads:
            for i, pin in enumerate(CNFG.BL_VPIN["ADS"]):
                values.append((pin, data.ads[i]))

        # SHT3X
        if data.sht:
            if data.sht["cels"]:
                values.append((CNFG.BL_VPIN["SHT"][0], data.sht["cels"]))
            if data.sht["hum"]:
                values.append((CNFG.BL_VPIN["SHT"][1], data.sht["hum"]))

        # relays
        if CNFG.R_ID_LIGHT in hw.keys():
            if hw[CNFG.R_ID_LIGHT].enabled:
                values.append((CNFG.BL_VPIN["R_LGHT"], 1))
            else:
                values.append((CNFG.BL_VPIN["R_LGHT"], 0))

        if CNFG.R_ID_FAN in hw.keys():
            if hw[CNFG.R_ID_FAN].enabled:
                values.append((CNFG.BL_VPIN["R_FAN"], 1))
            else:
                values.append((CNFG.BL_VPIN["R_FAN"], 0))

        if CNFG.R_ID_PUMP in hw.keys():
            if hw[CNFG.R_ID_PUMP].low_level():
                values.append((CNFG.BL_VPIN["WTR_LVL"], 1))
            else:
                values.append((CNFG.BL_VPIN["WTR_LVL"], 0))

            if hw[CNFG.R_ID_PUMP].enabled:
                values.append((CNFG.BL_VPIN["R_PUMP"], 1))
            else:
                values.append((CNFG.BL_VPIN["R_PUMP"], 0))

        return values

    def cloud_comm(self, payload, push_data=False, reattempt=False, **kw):
        if push_data:
            url = CNFG.BLYNK_BULK_URL
        else:
            url = CNFG.BLYNK_SINGLE_URL.format(func=kw["api_func"])
        url = url + payload
        logger.debug(url)
        resp = urequests.Response("")

        try:
            if push_data:
                resp = urequests.get(url, timeout=5)
            else:
                resp = urequests.get(url, json=True, timeout=5)

            if push_data and resp.status_code == 200:
                logger.info("API updated")
            elif not push_data and resp.status_code == 200:
                logger.debug("Data fetched")
                return resp.text
            else:
                # API works, server refused payload
                logger.error("Failed to comm with cloud")
                logger.debug(resp.__dict__)

        except OSError as exc:
            # ignore known error and try to reconnect
            if not "EHOSTUNREACH" in str(exc):
                logger.critical(exc)
            elif reattempt:
                logger.error("Reattempted cloud comm failed too..")
            # try again - once!
            if not reattempt:
                logger.warn("Reattempting Wi-Fi connection and to cloud comm")
                wifi_and_ntp.startup(CNFG.NETWORKS)
                self.cloud_comm(payload, reattempt=True, push_data=push_data, **kw)

        except MemoryError as exc:
            if "memory allocation failed" in str(exc):
                logger.warn("Connection attempt failed to allocate memory")
                prior_cleanup = gc.mem_free()
                gc.collect()
                logger.debug(
                    f"Free RAM before: {prior_cleanup}. Current: {gc.mem_free()}"
                )
                del prior_cleanup
                if not reattempt:
                    self.cloud_comm(payload, reattempt=True, push_data=push_data, **kw)
                else:
                    logger.critical("Cloud comm reattempt failed")

        finally:
            resp.close()
            del resp

    def fetch_pump_setting(self, hw):
        logger.info("Fetching cloud pump switch state")
        old_state = hw[CNFG.R_ID_PUMP].cloud_allow
        # JSON has to be set to True, otherwise socket read failes to detect 0
        # "0"/"1" is a JSON payload also per wireshark
        state = self.cloud_comm(f"V{CNFG.BL_VPIN['EN_PUMP']}", api_func="get")
        try:
            state = int(state)
            if state == 1:
                hw[CNFG.R_ID_PUMP].cloud_allow = True
            else:
                hw[CNFG.R_ID_PUMP].cloud_allow = False

            if old_state != hw[CNFG.R_ID_PUMP].cloud_allow:
                logger.debug(
                    f"Pump cloud_allow switch changed from {old_state} to {hw[CNFG.R_ID_PUMP].cloud_allow}"
                )

        except (ValueError, TypeError):
            logger.warn("Failed to read pump switch state from cloud")
            logger.debug(f"'state' value returned by server: {state}")
        finally:
            del state, old_state

    def update_streams(self, hw, data):
        logger.info("Preparing API payload")
        payload = self.create_payload(hw, data)
        logger.debug(payload)
        # make it a single string joined by &
        payload = "&".join([f"V{meas[0]}={meas[1]}" for meas in payload])

        logger.info("Sending data to cloud")
        self.cloud_comm(payload, push_data=True)
        del payload
