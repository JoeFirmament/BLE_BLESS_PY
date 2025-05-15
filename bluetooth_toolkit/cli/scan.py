#!/usr/bin/env python3
"""
蓝牙设备扫描命令行工具
"""

import argparse
import logging
import sys
import time

from bluetooth_toolkit import BluetoothManager
from bluetooth_toolkit.utils import setup_logging

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='蓝牙设备扫描工具')
    parser.add_argument('--timeout', type=int, default=10, help='扫描超时时间（秒）')
    parser.add_argument('--ble', action='store_true', help='扫描BLE设备')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    args = parser.parse_args()
    
    # 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # 创建蓝牙管理器
    manager = BluetoothManager()
    
    print(f"开始扫描{'BLE' if args.ble else '蓝牙'}设备...")
    print(f"扫描时间: {args.timeout}秒")
    
    # 扫描设备
    devices = manager.scan_devices(timeout=args.timeout, ble=args.ble)
    
    if not devices:
        print("未发现设备")
        return 1
    
    print(f"发现 {len(devices)} 个设备:")
    
    # 显示设备列表
    for i, device in enumerate(devices, 1):
        print(f"{i}. {device.name} ({device.address})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
