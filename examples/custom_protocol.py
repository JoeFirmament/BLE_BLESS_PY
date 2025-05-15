#!/usr/bin/env python3
"""
自定义协议示例
"""

import sys
import os
import logging
import time
import struct

# 添加父目录到模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bluetooth_toolkit import BluetoothManager, Protocol, ProtocolHandler
from bluetooth_toolkit.utils import setup_logging, bytes_to_hex

# 定义命令ID
CMD_PING = 0x01
CMD_GET_STATUS = 0x02
CMD_SET_CONFIG = 0x03
CMD_GET_DATA = 0x04

def handle_ping(data):
    """处理Ping命令"""
    print(f"收到Ping命令，数据: {bytes_to_hex(data)}")
    # 返回相同的数据作为响应
    return data

def handle_get_status(data):
    """处理获取状态命令"""
    print(f"收到获取状态命令，数据: {bytes_to_hex(data)}")
    # 返回模拟的状态数据
    return struct.pack("!BBHH", 0x01, 0x02, 1000, 2000)

def handle_set_config(data):
    """处理设置配置命令"""
    print(f"收到设置配置命令，数据: {bytes_to_hex(data)}")
    # 解析配置数据
    if len(data) >= 4:
        config_id, config_value = struct.unpack("!HH", data[:4])
        print(f"配置ID: {config_id}, 值: {config_value}")
        # 返回成功响应
        return struct.pack("!B", 0x00)
    else:
        # 返回错误响应
        return struct.pack("!B", 0xFF)

def handle_get_data(data):
    """处理获取数据命令"""
    print(f"收到获取数据命令，数据: {bytes_to_hex(data)}")
    # 解析数据请求
    if len(data) >= 2:
        data_id = struct.unpack("!H", data[:2])[0]
        print(f"数据ID: {data_id}")
        # 返回模拟的数据
        return struct.pack("!HI", data_id, 12345678)
    else:
        # 返回错误响应
        return struct.pack("!B", 0xFF)

def main():
    # 设置日志
    setup_logging(logging.INFO)
    
    # 创建自定义协议
    protocol = Protocol("MyCustomProtocol", "1.0")
    
    # 注册命令
    protocol.register_command(CMD_PING, "Ping", handle_ping)
    protocol.register_command(CMD_GET_STATUS, "GetStatus", handle_get_status)
    protocol.register_command(CMD_SET_CONFIG, "SetConfig", handle_set_config)
    protocol.register_command(CMD_GET_DATA, "GetData", handle_get_data)
    
    # 创建协议处理器
    handler = ProtocolHandler()
    handler.register_protocol(0x01, protocol, default=True)
    
    # 测试协议
    print("测试协议编码和解码:")
    
    # 测试Ping命令
    ping_data = b"Hello, World!"
    ping_packet = protocol.encode_packet(CMD_PING, ping_data)
    print(f"Ping命令数据包: {bytes_to_hex(ping_packet)}")
    
    cmd_id, data = protocol.decode_packet(ping_packet)
    print(f"解码结果: 命令ID={cmd_id}, 数据={bytes_to_hex(data)}")
    
    # 测试处理数据包
    response = protocol.handle_packet(ping_packet)
    if response:
        print(f"响应数据包: {bytes_to_hex(response)}")
        cmd_id, data = protocol.decode_packet(response)
        print(f"响应解码结果: 命令ID={cmd_id}, 数据={bytes_to_hex(data)}")
    
    # 测试获取状态命令
    status_packet = protocol.encode_packet(CMD_GET_STATUS)
    print(f"\nGetStatus命令数据包: {bytes_to_hex(status_packet)}")
    
    response = protocol.handle_packet(status_packet)
    if response:
        print(f"响应数据包: {bytes_to_hex(response)}")
        cmd_id, data = protocol.decode_packet(response)
        print(f"响应解码结果: 命令ID={cmd_id}, 数据={bytes_to_hex(data)}")
        
        # 解析状态数据
        if len(data) >= 6:
            status1, status2, value1, value2 = struct.unpack("!BBHH", data[:6])
            print(f"状态1: {status1}, 状态2: {status2}, 值1: {value1}, 值2: {value2}")
    
    # 测试设置配置命令
    config_data = struct.pack("!HH", 0x0001, 0x1234)  # 配置ID=1, 值=0x1234
    config_packet = protocol.encode_packet(CMD_SET_CONFIG, config_data)
    print(f"\nSetConfig命令数据包: {bytes_to_hex(config_packet)}")
    
    response = protocol.handle_packet(config_packet)
    if response:
        print(f"响应数据包: {bytes_to_hex(response)}")
        cmd_id, data = protocol.decode_packet(response)
        print(f"响应解码结果: 命令ID={cmd_id}, 数据={bytes_to_hex(data)}")
        
        # 解析响应
        if len(data) >= 1:
            result = struct.unpack("!B", data[:1])[0]
            print(f"结果: {result} ({'成功' if result == 0 else '失败'})")
    
    # 测试获取数据命令
    data_req = struct.pack("!H", 0x0002)  # 数据ID=2
    data_packet = protocol.encode_packet(CMD_GET_DATA, data_req)
    print(f"\nGetData命令数据包: {bytes_to_hex(data_packet)}")
    
    response = protocol.handle_packet(data_packet)
    if response:
        print(f"响应数据包: {bytes_to_hex(response)}")
        cmd_id, data = protocol.decode_packet(response)
        print(f"响应解码结果: 命令ID={cmd_id}, 数据={bytes_to_hex(data)}")
        
        # 解析数据
        if len(data) >= 6:
            data_id, value = struct.unpack("!HI", data[:6])
            print(f"数据ID: {data_id}, 值: {value}")

if __name__ == "__main__":
    main()
