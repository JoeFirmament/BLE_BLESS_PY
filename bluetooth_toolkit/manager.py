"""
蓝牙管理器模块 - 提供蓝牙设备发现和连接功能
"""

import logging
import subprocess
import re
import time
from typing import List, Dict, Optional, Union, Tuple

from .device import BluetoothDevice, BLEDevice
from .utils import is_valid_mac_address, run_command

logger = logging.getLogger(__name__)

class BluetoothManager:
    """蓝牙管理器类，用于管理蓝牙设备的发现和连接"""
    
    def __init__(self, adapter: str = "hci0"):
        """
        初始化蓝牙管理器
        
        参数:
            adapter: 蓝牙适配器名称，默认为"hci0"
        """
        self.adapter = adapter
        self.devices = {}  # 存储发现的设备
        self._check_adapter()
    
    def _check_adapter(self) -> bool:
        """
        检查蓝牙适配器是否可用
        
        返回:
            bool: 适配器是否可用
        """
        try:
            result = run_command(["hciconfig", self.adapter])
            if "UP RUNNING" in result:
                logger.info(f"蓝牙适配器 {self.adapter} 已就绪")
                return True
            else:
                # 尝试启用适配器
                run_command(["hciconfig", self.adapter, "up"])
                result = run_command(["hciconfig", self.adapter])
                if "UP RUNNING" in result:
                    logger.info(f"蓝牙适配器 {self.adapter} 已启用")
                    return True
                else:
                    logger.error(f"无法启用蓝牙适配器 {self.adapter}")
                    return False
        except Exception as e:
            logger.error(f"检查蓝牙适配器时出错: {e}")
            return False
    
    def scan_devices(self, timeout: int = 10, ble: bool = True) -> List[Union[BluetoothDevice, BLEDevice]]:
        """
        扫描附近的蓝牙设备
        
        参数:
            timeout: 扫描超时时间（秒）
            ble: 是否扫描BLE设备
            
        返回:
            List[Union[BluetoothDevice, BLEDevice]]: 发现的设备列表
        """
        self.devices = {}
        
        # 使用bluetoothctl扫描设备
        try:
            # 启动扫描
            process = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 发送扫描命令
            commands = [
                "scan on\n"
            ]
            
            for cmd in commands:
                process.stdin.write(cmd)
                process.stdin.flush()
            
            # 等待扫描完成
            start_time = time.time()
            device_pattern = re.compile(r"\[NEW\] Device ([0-9A-F:]+) (.+)")
            
            while time.time() - start_time < timeout:
                output = process.stdout.readline()
                if not output:
                    continue
                
                # 解析设备信息
                match = device_pattern.search(output)
                if match:
                    addr = match.group(1)
                    name = match.group(2).strip()
                    
                    # 创建设备对象
                    if ble:
                        device = BLEDevice(addr, name)
                    else:
                        device = BluetoothDevice(addr, name)
                    
                    self.devices[addr] = device
                    logger.info(f"发现设备: {name} ({addr})")
            
            # 停止扫描
            process.stdin.write("scan off\n")
            process.stdin.write("quit\n")
            process.stdin.flush()
            process.terminate()
            
            return list(self.devices.values())
            
        except Exception as e:
            logger.error(f"扫描设备时出错: {e}")
            return []
    
    def get_device_info(self, address: str) -> Dict:
        """
        获取设备详细信息
        
        参数:
            address: 设备MAC地址
            
        返回:
            Dict: 设备信息字典
        """
        if not is_valid_mac_address(address):
            raise ValueError(f"无效的MAC地址: {address}")
        
        try:
            # 使用bluetoothctl获取设备信息
            result = run_command(["bluetoothctl", "info", address])
            
            # 解析设备信息
            info = {}
            for line in result.splitlines():
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[key.strip()] = value.strip()
            
            return info
        except Exception as e:
            logger.error(f"获取设备信息时出错: {e}")
            return {}
    
    def connect_device(self, address: str, ble: bool = True) -> Optional[Union[BluetoothDevice, BLEDevice]]:
        """
        连接到指定的蓝牙设备
        
        参数:
            address: 设备MAC地址
            ble: 是否为BLE设备
            
        返回:
            Optional[Union[BluetoothDevice, BLEDevice]]: 连接的设备对象，连接失败则返回None
        """
        if not is_valid_mac_address(address):
            raise ValueError(f"无效的MAC地址: {address}")
        
        # 如果设备已经在列表中，直接使用
        if address in self.devices:
            device = self.devices[address]
        else:
            # 获取设备信息
            info = self.get_device_info(address)
            name = info.get("Name", "Unknown")
            
            # 创建设备对象
            if ble:
                device = BLEDevice(address, name)
            else:
                device = BluetoothDevice(address, name)
            
            self.devices[address] = device
        
        # 连接设备
        if device.connect():
            logger.info(f"已连接到设备: {device.name} ({device.address})")
            return device
        else:
            logger.error(f"连接设备失败: {device.name} ({device.address})")
            return None
    
    def disconnect_device(self, address: str) -> bool:
        """
        断开与指定设备的连接
        
        参数:
            address: 设备MAC地址
            
        返回:
            bool: 是否成功断开连接
        """
        if not is_valid_mac_address(address):
            raise ValueError(f"无效的MAC地址: {address}")
        
        if address in self.devices:
            device = self.devices[address]
            if device.disconnect():
                logger.info(f"已断开与设备的连接: {device.name} ({device.address})")
                return True
            else:
                logger.error(f"断开设备连接失败: {device.name} ({device.address})")
                return False
        else:
            logger.warning(f"设备不在已知列表中: {address}")
            return False
