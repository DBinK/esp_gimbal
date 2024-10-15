import struct
import zlib

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

# 生成示例消息
header = 0x5A
yaw = -100.2    # 示例航向角
pitch = -200.3  # 示例俯仰角
deep = 3.4   # 示例深度

# 打包数据
packet = struct.pack(
    "<Bfff",  # 数据格式：B表示一个字节，fff表示三个浮点数
    header,
    yaw,
    pitch,
    deep,
)

# 计算校验和
checksum = crc16(packet) & 0xFFFF  # 取低16位作为校验和
packet_with_checksum = packet + struct.pack("<H", checksum)

# 打印打包后的数据
print("打包后的数据:", packet_with_checksum)

# 将打包后的数据转换为十六进制格式
hex_representation = packet_with_checksum.hex() # .upper()

# 打印打包后的数据的十六进制表示
print("打包后的数据（十六进制格式）:", hex_representation)

# 解包数据
unpacked_data = struct.unpack("<BfffH", packet_with_checksum)
print("解包后的数据:", unpacked_data)