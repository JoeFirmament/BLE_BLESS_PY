#!/usr/bin/env python3
"""
BLE客户端示例
"""

import sys
import os
import logging
import time
import argparse

# 添加父目录到模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bluetooth_toolkit import BluetoothManager
from bluetooth_toolkit.utils import setup_logging, bytes_to_hex, hex_to_bytes

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='BLE客户端示例')
    parser.add_argument('--scan', action='store_true', help='扫描设备')
    parser.add_argument('--connect', type=str, help='连接到指定MAC地址的设备')
    parser.add_argument('--read', type=str, help='读取特征值 (需要指定UUID)')
    parser.add_argument('--write', type=str, nargs=2, help='写入特征值 (需要指定UUID和十六进制数据)')
    parser.add_argument('--timeout', type=int, default=10, help='操作超时时间（秒）')
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(logging.INFO)
    
    # 创建蓝牙管理器
    manager = BluetoothManager()
    
    # 扫描设备
    if args.scan:
        print("开始扫描BLE设备...")
        devices = manager.scan_devices(timeout=args.timeout, ble=True)
        
        if not devices:
            print("未发现BLE设备")
            return
        
        print(f"发现 {len(devices)} 个BLE设备:")
        for i, device in enumerate(devices, 1):
            print(f"{i}. {device.name} ({device.address})")
        return
    
    # 连接设备
    if args.connect:
        device_addr = args.connect
        print(f"正在连接到设备: {device_addr}...")
        
        device = manager.connect_device(device_addr, ble=True)
        if not device:
            print("连接失败")
            return
        
        print(f"已连接到设备: {device.name} ({device.address})")
        
        # 发现服务
        print("正在发现服务...")
        services = device.discover_services()
        
        if not services:
            print("未发现服务")
        else:
            print(f"发现 {len(services)} 个服务:")
            for i, service_uuid in enumerate(services, 1):
                print(f"{i}. {service_uuid}")
        
        # 读取特征值
        if args.read:
            char_uuid = args.read
            print(f"正在读取特征值: {char_uuid}...")
            
            value = device.read_characteristic(char_uuid)
            if value:
                print(f"特征值: {bytes_to_hex(value)}")
                try:
                    # 尝试将字节解析为ASCII字符串
                    text = value.decode('ascii')
                    print(f"ASCII文本: {text}")
                except UnicodeDecodeError:
                    pass
            else:
                print("读取特征值失败")
        
        # 写入特征值
        if args.write:
            char_uuid, hex_data = args.write
            try:
                data = hex_to_bytes(hex_data)
                print(f"正在写入特征值: {char_uuid}...")
                print(f"数据: {bytes_to_hex(data)}")
                
                success = device.write_characteristic(char_uuid, data)
                if success:
                    print("写入特征值成功")
                else:
                    print("写入特征值失败")
            except ValueError as e:
                print(f"错误: {e}")
        
        # 断开连接
        print("正在断开连接...")
        device.disconnect()
        print("已断开连接")
        return
    
    # 如果没有指定操作，显示帮助信息
    parser.print_help()

if __name__ == "__main__":
    main()
