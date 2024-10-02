import json  # 导入 ujson 库，用于处理 JSON 格式
import network
import espnow
from machine import Pin, ADC, Timer
import time

# 初始化 wifi
sta = network.WLAN(network.STA_IF)  # 或者使用 network.AP_IF
sta.active(True)
sta.disconnect()      # 对于 ESP8266

# 初始化 espnow
now = espnow.ESPNow()
now.active(True)
peer = b'\xff\xff\xff\xff\xff\xff'  # 使用广播地址
now.add_peer(peer)      

# 初始化 adc 摇杆输入
lx = ADC(Pin(5)) 
lx.atten(ADC.ATTN_11DB)  # 开启衰减器，测量量程增大到 3.3V 
ly = ADC(Pin(7)) 
ly.atten(ADC.ATTN_11DB)  # 开启衰减器，测量量程增大到 3.3V 

rx = ADC(Pin(4))
rx.atten(ADC.ATTN_11DB)
ry = ADC(Pin(6))
ry.atten(ADC.ATTN_11DB)

def debounce(delay_ns):
    """装饰器: 防止函数在指定时间内被重复调用"""
    def decorator(func):
        last_call_time = 0
        result = None

        def wrapper(*args, **kwargs):
            nonlocal last_call_time, result
            current_time = time.time_ns()
            if current_time - last_call_time > delay_ns:
                last_call_time = current_time
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

# 初始化开关
ls_sw = False
@debounce(100_000_000) 
def ls_btn_callback(pin):
    global ls_sw, blink_speed
    if pin.value() == 0:
        ls_sw = not ls_sw
        print(f"开关: {ls_sw}")

        if blink_speed == 5:
            blink_speed = 20
        else:
            blink_speed = 5

ls_btn = Pin(3, Pin.IN, Pin.PULL_UP)
ls_btn.irq(ls_btn_callback, Pin.IRQ_FALLING)

# 初始化开关
rs_sw = False
@debounce(100_000_000) 
def rs_btn_callback(pin):
    global rs_sw
    if pin.value() == 0:
        rs_sw = not rs_sw
        print(f"开关: {rs_sw}")

rs_btn = Pin(2, Pin.IN, Pin.PULL_UP)
rs_btn.irq(rs_btn_callback, Pin.IRQ_FALLING)

led = Pin(15, Pin.OUT, value=1)
cnt = 0
blink_speed = 20
def blink_led():
    global cnt, blink_speed
    cnt += 1
    if cnt % blink_speed == 0:
        led.value(not led.value())
        cnt = 0

def main(tim_callback):
    global ls_sw
    
    if ls_sw:
        lx_raw  = 8191 - lx.read() - 3050
        ly_raw  = 8191 - ly.read() - 3080
        rx_raw  = 8191 - rx.read() - 3160
        ry_raw  = 8191 - ry.read() - 3000

        data = {
            "lx": lx_raw, "ly": ly_raw, "ls": ls_sw,
            "rx": rx_raw, "ry": ry_raw, "rs": rs_sw,
        }
    else:
        data = {
            "lx": 0, "ly": 0, "ls": ls_sw,
            "rx": 0, "ry": 0, "rs": rs_sw,
        }

    data_json = json.dumps(data)  # 将数据转换为 JSON 字符串并发送
    now.send(peer, data_json)  
    print(f"发送数据: {data_json}")

    blink_led()

# 开启定时器
tim = Timer(1)
tim.init(period=20, mode=Timer.PERIODIC, callback=main)