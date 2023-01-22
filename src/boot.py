# boot.py -- run on boot-up
try:
    from config import NETWORKS
except ImportError:
    # not an exemption, as we might want just to import functions and pass these args manually
    print("Failed to load wifi SSID and/or password from config")
    print("Trying it manually with wifi_and_ntp.startup(ssid, passwd)")
    raise OSError("Network not configured")

import wifi_and_ntp

wifi_and_ntp.startup(NETWORKS)

print("-" * 40, "boot complete", "-" * 40)
