import network
import espnow
import time

# A WLAN interface must be active to send()/recv()
sta = network.WLAN(network.STA_IF)  # Or network.AP_IF
sta.active(True)
sta.disconnect()      # For ESP8266

e = espnow.ESPNow()
e.active(True)
peer = b'\xff\xff\xff\xff\xff\xff'  # MAC address of peer's wifi interface
e.add_peer(peer)      # Must add_peer() before send()

e.send(peer, "Starting...")
for i in range(100):
    str1 = str(i)*20
    
    print(str1)
    e.send(peer, str1, True)
    
    time.sleep(1)
    
e.send(peer, b'end')


sta.disconnect()      # For ESP8266