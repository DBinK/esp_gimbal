import time
import network
import espnow
import json 

from machine import Pin, PWM  # type: ignore

# 初始化 PWM 引脚
in1 = PWM(Pin(5, Pin.OUT), freq=100000, duty=0)
in2 = Pin(6, Pin.OUT, value=0)

in3 = PWM(Pin(9, Pin.OUT), freq=100000, duty=0)
in4 = Pin(10, Pin.OUT, value=0) 

# A WLAN interface must be active to send()/recv()
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()  # 因为 ESP8266 会自动连接到最后一个接入点

e = espnow.ESPNow()
e.active(True)

peer = b'\xff\xff\xff\xff\xff\xff'  # 同伴的 WiFi 接口的 MAC 地址
e.add_peer(peer)  

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