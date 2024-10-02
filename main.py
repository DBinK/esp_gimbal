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

e = espnow.ESPNow()
e.active(True)    # 连接广播地址
e.add_peer(b'\xff\xff\xff\xff\xff\xff')  

while True:
    host, msg = e.recv()
    if msg:  # msg == None 如果在 recv() 中超时
        print(host, msg)

        # 解析 JSON 消息
        try:
            data = json.loads(msg)  # 将接收到的消息从 JSON 字符串转换为字典
            v_pwm_l = data.get("l_motor", 0)  # 获取左电机的 PWM 值，默认为0
            v_pwm_r = data.get("r_motor", 0)  # 获取右电机的 PWM 值，默认为0
            
            # 设置 PWM 值
            in1.duty(v_pwm_l)  # 设置左电机 PWM
            in3.duty(v_pwm_r)  # 设置右电机 PWM
            
            print(f'左电机 PWM 值: {v_pwm_l}, 右电机 PWM 值: {v_pwm_r}')
        
        except ValueError as e:
            print(f'解析消息失败: {e}')  # 处理解析错误
            continue 

        if msg == b'end':
            break
    else:
        # 设置 PWM 值
        in1.duty(0)  # 设置左电机 PWM
        in3.duty(0)  # 设置右电机 PWM
        print('No message received')