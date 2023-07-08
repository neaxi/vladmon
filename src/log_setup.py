import ulogger
import time
import config as CNFG


def term_handler(level=CNFG.LOG_LEVEL):
    """logging message parameters"""
    hdl_terminal = ulogger.Handler(
        level=CNFG.LOG_LEVEL,
        colorful=True,
        fmt="&(time)% - &(level)% - &(name)% - &(fnname)% - &(msg)%",
        clock=None,
        direction=ulogger.TO_TERM,
    )
    return hdl_terminal


def getLogger(name=None, level=None):
    logger = ulogger.Logger(name=name, handlers=(term_handler(level),))
    return logger


# def test():
#     log = getLogger()
#     log.debug("DEBUG")
#     log.info("INFO")
#     log.warn("warning")
#     log.error("error")
#     log.critical("exception")
