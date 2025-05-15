#!/usr/bin/env python3
"""
扫描附近的蓝牙设备示例
"""

import sys
import os
import logging
import time

# 添加父目录到模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bluetooth_toolkit import BluetoothManager
from bluetooth_toolkit.utils import setup_logging

def main():
    # 设置日志
    setup_logging(logging.INFO)
    
    # 创建蓝牙管理器
    manager = BluetoothManager()
    
    print("开始扫描蓝牙设备...")
    
    # 扫描设备
    devices = manager.scan_devices(timeout=10)
    
    if not devices:
        print("未发现蓝牙设备")
        return
    
    print(f"发现 {len(devices)} 个蓝牙设备:")
    
    # 显示设备列表
    for i, device in enumerate(devices, 1):
        print(f"{i}. {device.name} ({device.address})")
    
    # 选择设备
    while True:
        try:
            choice = input("\n请选择要连接的设备编号 (输入q退出): ")
            if choice.lower() == 'q':
                break
            
            index = int(choice) - 1
            if 0 <= index < len(devices):
                selected_device = devices[index]
                print(f"选择了设备: {selected_device.name} ({selected_device.address})")
                
                # 获取设备详细信息
                info = manager.get_device_info(selected_device.address)
                print("\n设备信息:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
                
                # 询问是否连接
                connect = input("\n是否连接到该设备? (y/n): ")
                if connect.lower() == 'y':
                    print(f"正在连接到设备: {selected_device.name}...")
                    device = manager.connect_device(selected_device.address)
                    
                    if device:
                        print(f"已连接到设备: {device.name}")
                        
                        # 等待几秒钟
                        time.sleep(3)
                        
                        # 断开连接
                        print("正在断开连接...")
                        device.disconnect()
                        print("已断开连接")
                    else:
                        print("连接失败")
            else:
                print("无效的选择，请重试")
        except ValueError:
            print("请输入有效的数字")
        except KeyboardInterrupt:
            break
    
    print("程序结束")

if __name__ == "__main__":
    main()
