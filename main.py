import time
from machine import UART

from servo import Servo

# 创建串口对象
uart = UART(1, 115200, rx=21, tx=20)  # 设置串口号1和波特率
uart.write("Hello 01Studio!")  # 发送一条数据

# 创建舵机对象
servo_x = Servo(5)
servo_x.set_limit(30,150)

servo_y = Servo(6)
servo_y.set_limit(60,120)

while True:
    