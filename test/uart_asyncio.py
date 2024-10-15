import uasyncio as asyncio
from machine import UART, Pin
import struct

# 配置串口
uart = UART(1, baudrate=115200, tx=20, rx=21)  # 根据实际引脚配置进行调整
uart.init(bits=8, parity=None, stop=1)

# 定义数据包结构
HEADER_FORMAT = "<Bfff"  # 数据格式：B表示一个字节，fff表示三个浮点数
CHECKSUM_FORMAT = "<H"    # 校验和格式：H表示一个无符号短整数

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

async def read_uart():
    while True:
        if uart.any():  # 检查是否有可读数据
            data = uart.read(uart.any())  # 读取所有可用的数据
            process_data(data)  # 处理接收到的数据
        await asyncio.sleep(0.1)  # 等待一段时间再检查

def process_data(data):
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
    # if received_checksum == checksum:
    if True:
        print("\n头部:", header.hex())
        print("航向角:", yaw)
        print("俯仰角:", pitch)
        print("深度:", deep)
        print("收到的校验和:", received_checksum)
        print("计算的校验和:", checksum)
    else:
        print("校验和错误，丢弃数据")

async def main():
    await asyncio.gather(
        read_uart(),  # 启动读取 UART 的任务
    )

# 运行主协程
asyncio.run(main())