import struct
import time
import json
import asyncio
import espnow
import network
from machine import UART, Pin

from servo import Servo

# 定义数据包结构
HEADER_FORMAT = "<Bfff"  # 数据格式：B表示一个字节，fff表示三个浮点数
CHECKSUM_FORMAT = "<H"    # 校验和格式：H表示一个无符号短整数

led = Pin(8, Pin.OUT, value=1)

# 创建串口对象
uart = UART(1, 115200, rx=21, tx=20)  # 设置串口号1和波特率
uart.init(bits=8, parity=None, stop=1)
uart.write("Hello Gimbal!")  # 发送一条数据

# 创建舵机对象
servo_x = Servo(5)
servo_x.set_limit(30, 150)

servo_y = Servo(6)
servo_y.set_limit(60, 120)

# 初始化 WiFi 和 espnow
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()  # 因为 ESP8266 会自动连接到最后一个接入点

now = espnow.ESPNow()
now.active(True)    # 连接广播地址
now.add_peer(b'\xff\xff\xff\xff\xff\xff')

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

def limit_value(value, min_value=-3000, max_value=3000):
    """限制输入的值在给定的范围内。"""
    return min(max(value, min_value), max_value)

def time_diff(last_time=[None]):
    """计算两次调用之间的时间差，单位为微秒。"""
    current_time = time.ticks_us()  # 获取当前时间（单位：微秒）

    if last_time[0] is None:  # 如果是第一次调用，更新last_time
        last_time[0] = current_time
        return 0.000_001  # 防止除零错误
    
    else:  # 计算时间差
        diff = time.ticks_diff(current_time, last_time[0])  # 计算时间差
        last_time[0] = current_time  # 更新上次调用时间
        return diff  # 返回时间差us

# 计算CRC16校验和
def crc16(data: bytes) -> int:
    """计算CRC16校验和"""
    crc = 0xFFFF  # 初始化CRC值
    for byte in data:
        crc ^= byte  # 异或操作
        for _ in range(8):  # 对每个字节进行8次处理
            if crc & 0x0001:  # 检查最低位
                crc >>= 1  # 右移
                crc ^= 0xA001  # 进行多项式异或
            else:
                crc >>= 1  # 右移
    return crc

async def read_espnow():
    """读取espnow数据并进行解包处理"""
    while True:
        host, msg = now.recv()  # 读取所有可用的数据
        process_espnow_data(msg)  # 处理接收到的数据
        await asyncio.sleep(0.001)  # 等待一段时间再检查

def process_espnow_data(msg):
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
                led.value(not led.value())  # 闪烁led
                if lx != 0 or ly != 0 or rx != 0 or ry != 0:
                    print(f"接收到espnow数据: lx={lx}, ly={ly}, rx={rx}, ry={ry}")
                    servo_x.set_angle_relative(limit_value(-rx) / 450)  # 灵敏度
                    servo_y.set_angle_relative(limit_value(ry) / 450)

        except ValueError as e:
            print(f'解析消息失败: {e}')
    else:
        print('No message received')

async def read_uart():
    while True:
        if uart.any():  # 检查是否有可读数据
            data = uart.read(uart.any())  # 读取所有可用的数据
            process_uart_data(data)  # 处理接收到的数据
        await asyncio.sleep(0.001)  # 等待一段时间再检查

def process_uart_data(data):
    # 检查数据长度
    if len(data) < 13:  # 1字节头 + 3x4字节浮点数 + 2字节校验和 = 13字节
        print(f"数据长度不足，丢弃数据: {data.hex()}")
        return

    # 解包数据
    header, yaw, pitch, deep = struct.unpack(HEADER_FORMAT, data[:13])
    received_checksum = struct.unpack(CHECKSUM_FORMAT, data[13:])[0]

    # 计算校验和
    packet = data[:13]  # 包含头部和浮点数部分
    checksum = crc16(packet) & 0xFFFF  # 取低16位作为校验和

    # 校验和验证
    if received_checksum == checksum:
        print(f"\n头部: {hex(header)}, 航向角: {yaw}, 俯仰角: {pitch}, 深度: {deep}")
    else:
        print(f"校验和错误，丢弃数据: {data.hex()}")

    if yaw != 0 or pitch != 0 or deep != 0:
        print(f"接收到串口数据: yaw={yaw}, pitch={pitch}, deep={deep}")
        servo_x.set_angle_relative(yaw * 0.1)  # 灵敏度
        servo_y.set_angle_relative(-pitch * 0.1)

async def main():
    await asyncio.gather(
        read_uart(),   # 启动读取 UART 的任务
        read_espnow(), # 启动读取 espnow 的任务
    )

# 运行主协程
asyncio.run(main())

# 数据格式
data_now = {
    "lx": 0, "ly": 0, "ls_sw": True,
    "rx": 0, "ry": 0, "rs_sw": False,
}