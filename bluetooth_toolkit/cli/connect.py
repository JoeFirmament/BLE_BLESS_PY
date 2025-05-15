#!/usr/bin/env python3
"""
蓝牙设备连接命令行工具
"""

import argparse
import logging
import sys
import time

from bluetooth_toolkit import BluetoothManager
from bluetooth_toolkit.utils import setup_logging, bytes_to_hex, hex_to_bytes

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='蓝牙设备连接工具')
    parser.add_argument('address', help='设备MAC地址')
    parser.add_argument('--ble', action='store_true', help='连接BLE设备')
    parser.add_argument('--info', action='store_true', help='显示设备信息')
    parser.add_argument('--services', action='store_true', help='显示设备服务')
    parser.add_argument('--read', type=str, help='读取特征值 (需要指定UUID)')
    parser.add_argument('--write', type=str, nargs=2, help='写入特征值 (需要指定UUID和十六进制数据)')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    args = parser.parse_args()
    
    # 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # 创建蓝牙管理器
    manager = BluetoothManager()
    
    # 连接设备
    print(f"正在连接到设备: {args.address}...")
    device = manager.connect_device(args.address, ble=args.ble)
    
    if not device:
        print("连接失败")
        return 1
    
    print(f"已连接到设备: {device.name} ({device.address})")
    
    try:
        # 显示设备信息
        if args.info:
            info = manager.get_device_info(args.address)
            print("\n设备信息:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        
        # 显示设备服务
        if args.services and args.ble:
            print("\n正在发现服务...")
            services = device.discover_services()
            
            if not services:
                print("未发现服务")
            else:
                print(f"发现 {len(services)} 个服务:")
                for i, service_uuid in enumerate(services, 1):
                    print(f"{i}. {service_uuid}")
        
        # 读取特征值
        if args.read and args.ble:
            char_uuid = args.read
            print(f"\n正在读取特征值: {char_uuid}...")
            
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
        if args.write and args.ble:
            char_uuid, hex_data = args.write
            try:
                data = hex_to_bytes(hex_data)
                print(f"\n正在写入特征值: {char_uuid}...")
                print(f"数据: {bytes_to_hex(data)}")
                
                success = device.write_characteristic(char_uuid, data)
                if success:
                    print("写入特征值成功")
                else:
                    print("写入特征值失败")
            except ValueError as e:
                print(f"错误: {e}")
        
        # 如果没有指定操作，等待一段时间
        if not (args.info or args.services or args.read or args.write):
            print("\n设备已连接，按Ctrl+C断开连接...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n用户中断")
    
    finally:
        # 断开连接
        print("\n正在断开连接...")
        device.disconnect()
        print("已断开连接")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
