import struct
import time
import json 

import espnow
import network
from machine import UART, Pin, Timer

from servo import Servo

led = Pin(8, Pin.OUT, value=1)

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
    """限制输入的值在给定的范围内。"""
    return min(max(value, min_value), max_value)

def time_diff(last_time=[None]):
    """计算两次调用之间的时间差，单位为微秒。"""
    current_time = time.ticks_us()  # 获取当前时间（单位：微秒）

    if last_time[0] is None: # 如果是第一次调用，更新last_time
        last_time[0] = current_time
        return 0.000_001 # 防止除零错误
    
    else: # 计算时间差
        diff = time.ticks_diff(current_time, last_time[0])  # 计算时间差
        last_time[0] = current_time  # 更新上次调用时间
        return diff  # 返回时间差us

def read_uart():
    """读取串口数据并进行解包处理"""
    if uart.any():  # 检查是否有数据可读
        header = uart.read(1)  # 读取数据头部
        print(header)
        if header and header[0] == 0x5A:  # 检查数据头
            data = uart.read(16)  # 读取16字节数据
            # print(data)
            if len(data) == 16:
                packet = struct.unpack("<BfffH", header + data) # 解包数据
                header, yaw, pitch, deep, checksum = packet
                print(f"接收到的数据: yaw={yaw}, pitch={pitch}, deep={deep}, checksum={checksum}")

                led.value(not led.value()) # 闪烁led

                return yaw, pitch, deep
            else:
                print("接收到的数据长度不匹配")

    return 0,0,0

def read_espnow():
    """读取espnow数据并进行解包处理"""
    host, msg = now.recv()
    if msg:
        try:
            data = json.loads(msg)  # 将接收到的消息从 JSON 字符串转换为字典
            # print(data)

            lx = data.get("lx", 0)
            ly = data.get("ly", 0)
            rx = data.get("rx", 0)
            ry = data.get("ry", 0)

            # 检查lx, ly, rx, ry中是否至少有一个绝对值超过40
            stick_work = any(abs(value) > 40 for value in [lx, ly, rx, ry])
            if stick_work:
                led.value(not led.value()) # 闪烁led
                return lx, ly, rx, ry
            else:
                print('No valid data received')
                return 0, 0, 0, 0

        except ValueError as e:
            print(f'解析消息失败: {e}')
            return 0, 0, 0, 0

    else:
        print('No message received')
        return 0, 0, 0, 0

sw = True
def stop_btn_callback(pin):
    global sw
    time.sleep(0.1)
    if pin.value() == 0:
        sw = not sw
        led.value(not led.value())
        print("停止定时器")  # 不然Thonny无法停止程序

stop_btn = Pin(9, Pin.IN, Pin.PULL_UP)
stop_btn.irq(stop_btn_callback, Pin.IRQ_FALLING)


while True:
    if sw:
        time.sleep(0.1)
        yaw, pitch, deep = read_uart()

        if yaw != 0 or pitch != 0 or deep != 0:
            servo_x.set_angle(yaw   * 0.1)  # 灵敏度
            servo_y.set_angle(pitch * 0.1)

        else:
            lx, ly, rx, ry = read_espnow()
            servo_x.set_angle_relative(limit_value(-rx) / 450)  # 灵敏度
            servo_y.set_angle_relative(limit_value(ry)  / 450)

        led.value(1) # 关闭闪烁led

        diff = time_diff()
        print(f"延迟us: {diff}, 频率Hz: {1_000_000 / diff}")


# 数据格式
data_now = {
    "lx": 0, "ly": 0, "ls_sw": True,
    "rx": 0, "ry": 0, "rs_sw": False,
}