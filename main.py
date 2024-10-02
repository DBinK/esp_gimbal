import time
import json 

import espnow
import network
from machine import UART

from servo import Servo

# 创建串口对象
uart = UART(1, 115200, rx=21, tx=20)  # 设置串口号1和波特率
uart.write("Hello Gimbal!")  # 发送一条数据

# 创建舵机对象
servo_x = Servo(5)
servo_x.set_limit(30,150)

servo_y = Servo(6)
servo_y.set_limit(60,120)

# 初始化 WiFi 和 espnow
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()  # 因为 ESP8266 会自动连接到最后一个接入点

now = espnow.ESPNow()
now.active(True)    # 连接广播地址
now.add_peer(b'\xff\xff\xff\xff\xff\xff')  

while True:
    time.sleep(0.02)
    host, msg = now.recv()
    if msg:  # msg == None 如果在 recv() 中超时
        print(msg)

        # 解析 JSON 消息
        try:
            data = json.loads(msg)  # 将接收到的消息从 JSON 字符串转换为字典

            lx = data.get("lx", 0)  
            ly = data.get("ly", 0)  

            rx = data.get("rx", 0)
            ry = data.get("ry", 0)
        
        except ValueError as e:
            print(f'解析消息失败: {e}') 
            continue
        
        if abs(lx) > 50 or abs(ly) > 50:
            print('lx:', lx, 'ly:', ly)
            servo_x.set_angle_relative(-rx/1000)
            servo_y.set_angle_relative( ly/1000)

    else:
        print('No message received')

data = {
    "lx": 0, "ly": 0, "ls_sw": True,
    "rx": 0, "ry": 0, "rs_sw": False,
}