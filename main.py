import time
import json 

import espnow
import network
from machine import UART, Pin

from servo import Servo

led = Pin(8, Pin.OUT)

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

def limit_value(value, min_value=-3000 , max_value=3000):
    return min(max(value, min_value), max_value)

while True:
    time.sleep(0.01)
    
    led.value(1)
    
    host, msg = now.recv()
    if msg:  # msg == None 如果在 recv() 中超时
        # print(msg)

        # 解析 JSON 消息
        try:
            data = json.loads(msg)  # 将接收到的消息从 JSON 字符串转换为字典

            print(data)
 
            lx = data.get("lx", 0)
            ly = data.get("ly", 0)
            rx = data.get("rx", 0)
            ry = data.get("ry", 0)
        
        except ValueError as e:
            print(f'解析消息失败: {e}') 
            continue
        
        # 检查lx, ly, rx, ry中是否至少有一个绝对值超过40
        stick_work = any(abs(value) > 40 for value in [lx, ly, rx, ry])

        if stick_work:
            servo_x.set_angle_relative(limit_value(-rx) / 450)  # 灵敏度
            servo_y.set_angle_relative(limit_value(ry)  / 450)
            
            # 切换LED的状态
            led.value(not led.value())

    else:
        print('No message received')

# 数据格式
data = {
    "lx": 0, "ly": 0, "ls_sw": True,
    "rx": 0, "ry": 0, "rs_sw": False,
}