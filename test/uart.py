from machine import UART
import time
import struct

# 配置串口
uart = UART(1, baudrate=115200, tx=20, rx=21)  # 根据实际引脚配置进行调整
uart.init(bits=8, parity=None, stop=1)

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

def send_data():
    """处理目标信息并通过串口发送"""
    try:
        header = 0x5A
        yaw    = 46.46
        pitch  = 364.5
        deep   = 1046

        #print(f"yaw type: {yaw}, pitch type: {pitch}, deep type: {deep}")

        packet = struct.pack(
            "<Bfff",
            header,
            yaw,
            pitch,
            deep,
        )

        # 计算校验和
        checksum = crc16(packet)  # 使用自定义的CRC16函数
        packet_with_checksum = packet + struct.pack("<H", checksum)

        #print(f"打包后的数据: {packet_with_checksum}")

        uart.write(packet_with_checksum)

    except Exception as e:
        print(f"发送数据时出错: {str(e)}")

def read_data():
    """读取串口数据并进行解包处理"""
    if uart.any():  # 检查是否有数据可读
        # 读取数据头部
        header = uart.read(1)
        print(header)
        if header and header[0] == 0x5A:  # 检查数据头
            data = uart.read(16)  # 读取16字节数据
            print(data)
            if len(data) == 16:
                # 解包数据
                packet = struct.unpack("<BfffH", header + data)
                header, yaw, pitch, deep, checksum = packet
                print(f"接收到的数据: yaw={yaw}, pitch={pitch}, deep={deep}, checksum={checksum}")
            else:
                print("接收到的数据长度不匹配")
        # else:
        #     print("无效数据头，未接收到数据")

while True:
    try:
        print("开始接收数据...")
        send_data()
        read_data()
    except KeyboardInterrupt:
        print("停止接收数据")

    time.sleep(0.1)