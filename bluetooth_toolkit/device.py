"""
蓝牙设备模块 - 提供蓝牙设备的基本操作
"""

import logging
import time
import subprocess
from typing import Optional, List, Dict, Any, Union

from .utils import run_command, is_valid_mac_address

logger = logging.getLogger(__name__)

class BluetoothDevice:
    """蓝牙设备基类，提供基本的蓝牙设备操作"""
    
    def __init__(self, address: str, name: str = "Unknown"):
        """
        初始化蓝牙设备
        
        参数:
            address: 设备MAC地址
            name: 设备名称，默认为"Unknown"
        """
        if not is_valid_mac_address(address):
            raise ValueError(f"无效的MAC地址: {address}")
        
        self.address = address
        self.name = name
        self.connected = False
        self.services = {}
        self.characteristics = {}
    
    def connect(self) -> bool:
        """
        连接到设备
        
        返回:
            bool: 是否成功连接
        """
        try:
            # 使用bluetoothctl连接设备
            result = run_command(["bluetoothctl", "connect", self.address])
            
            if "Connection successful" in result:
                self.connected = True
                logger.info(f"已连接到设备: {self.name} ({self.address})")
                return True
            else:
                logger.error(f"连接设备失败: {self.name} ({self.address})")
                return False
        except Exception as e:
            logger.error(f"连接设备时出错: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        断开与设备的连接
        
        返回:
            bool: 是否成功断开连接
        """
        if not self.connected:
            logger.warning(f"设备未连接: {self.name} ({self.address})")
            return True
        
        try:
            # 使用bluetoothctl断开设备
            result = run_command(["bluetoothctl", "disconnect", self.address])
            
            if "Successful disconnected" in result or "Device has been disconnected" in result:
                self.connected = False
                logger.info(f"已断开与设备的连接: {self.name} ({self.address})")
                return True
            else:
                logger.error(f"断开设备连接失败: {self.name} ({self.address})")
                return False
        except Exception as e:
            logger.error(f"断开设备连接时出错: {e}")
            return False
    
    def is_connected(self) -> bool:
        """
        检查设备是否已连接
        
        返回:
            bool: 设备是否已连接
        """
        try:
            # 使用bluetoothctl检查设备连接状态
            result = run_command(["bluetoothctl", "info", self.address])
            
            if "Connected: yes" in result:
                self.connected = True
                return True
            else:
                self.connected = False
                return False
        except Exception as e:
            logger.error(f"检查设备连接状态时出错: {e}")
            return False
    
    def send_data(self, data: bytes) -> bool:
        """
        向设备发送数据
        
        参数:
            data: 要发送的数据
            
        返回:
            bool: 是否成功发送数据
        """
        if not self.connected:
            logger.error(f"设备未连接: {self.name} ({self.address})")
            return False
        
        # 这里需要根据具体的蓝牙协议实现数据发送
        # 由于标准蓝牙发送数据需要使用RFCOMM或其他协议，这里只是一个示例
        logger.warning("标准蓝牙设备的send_data方法需要在子类中实现")
        return False
    
    def receive_data(self, timeout: int = 5) -> Optional[bytes]:
        """
        从设备接收数据
        
        参数:
            timeout: 接收超时时间（秒）
            
        返回:
            Optional[bytes]: 接收到的数据，超时或失败则返回None
        """
        if not self.connected:
            logger.error(f"设备未连接: {self.name} ({self.address})")
            return None
        
        # 这里需要根据具体的蓝牙协议实现数据接收
        # 由于标准蓝牙接收数据需要使用RFCOMM或其他协议，这里只是一个示例
        logger.warning("标准蓝牙设备的receive_data方法需要在子类中实现")
        return None
    
    def __str__(self) -> str:
        """返回设备的字符串表示"""
        return f"{self.name} ({self.address})"


class BLEDevice(BluetoothDevice):
    """低功耗蓝牙设备类，提供BLE特有的操作"""
    
    def __init__(self, address: str, name: str = "Unknown"):
        """
        初始化BLE设备
        
        参数:
            address: 设备MAC地址
            name: 设备名称，默认为"Unknown"
        """
        super().__init__(address, name)
        self.services = {}
        self.characteristics = {}
    
    def discover_services(self) -> List[str]:
        """
        发现设备提供的服务
        
        返回:
            List[str]: 服务UUID列表
        """
        if not self.connected:
            logger.error(f"设备未连接: {self.name} ({self.address})")
            return []
        
        try:
            # 使用bluetoothctl获取设备服务
            result = run_command(["bluetoothctl", "info", self.address])
            
            # 解析服务UUID
            services = []
            for line in result.splitlines():
                line = line.strip()
                if "UUID:" in line:
                    uuid = line.split("UUID:", 1)[1].strip().split(" ", 1)[0]
                    services.append(uuid)
                    self.services[uuid] = {}
            
            logger.info(f"发现设备服务: {len(services)} 个")
            return services
        except Exception as e:
            logger.error(f"发现设备服务时出错: {e}")
            return []
    
    def read_characteristic(self, characteristic_uuid: str) -> Optional[bytes]:
        """
        读取特征值
        
        参数:
            characteristic_uuid: 特征UUID
            
        返回:
            Optional[bytes]: 特征值，失败则返回None
        """
        if not self.connected:
            logger.error(f"设备未连接: {self.name} ({self.address})")
            return None
        
        try:
            # 这里需要使用gatttool或其他工具读取特征值
            # 由于命令行操作较为复杂，这里只是一个示例
            cmd = [
                "gatttool",
                "-b", self.address,
                "--char-read",
                "--uuid", characteristic_uuid
            ]
            
            result = run_command(cmd)
            
            # 解析特征值
            if "Characteristic value/descriptor:" in result:
                value_hex = result.split("Characteristic value/descriptor:", 1)[1].strip()
                value_bytes = bytes.fromhex(value_hex.replace(" ", ""))
                return value_bytes
            else:
                logger.error(f"读取特征值失败: {characteristic_uuid}")
                return None
        except Exception as e:
            logger.error(f"读取特征值时出错: {e}")
            return None
    
    def write_characteristic(self, characteristic_uuid: str, data: bytes, response: bool = True) -> bool:
        """
        写入特征值
        
        参数:
            characteristic_uuid: 特征UUID
            data: 要写入的数据
            response: 是否需要响应
            
        返回:
            bool: 是否成功写入
        """
        if not self.connected:
            logger.error(f"设备未连接: {self.name} ({self.address})")
            return False
        
        try:
            # 将数据转换为十六进制字符串
            data_hex = data.hex()
            data_str = " ".join(data_hex[i:i+2] for i in range(0, len(data_hex), 2))
            
            # 这里需要使用gatttool或其他工具写入特征值
            # 由于命令行操作较为复杂，这里只是一个示例
            cmd = [
                "gatttool",
                "-b", self.address,
                "--char-write" + ("-req" if response else ""),
                "--uuid", characteristic_uuid,
                "--value", data_str
            ]
            
            result = run_command(cmd)
            
            if "Characteristic value was written successfully" in result:
                logger.info(f"特征值写入成功: {characteristic_uuid}")
                return True
            else:
                logger.error(f"特征值写入失败: {characteristic_uuid}")
                return False
        except Exception as e:
            logger.error(f"写入特征值时出错: {e}")
            return False
    
    def send_data(self, data: bytes, characteristic_uuid: Optional[str] = None) -> bool:
        """
        向设备发送数据
        
        参数:
            data: 要发送的数据
            characteristic_uuid: 特征UUID，如果为None则使用默认特征
            
        返回:
            bool: 是否成功发送数据
        """
        if not self.connected:
            logger.error(f"设备未连接: {self.name} ({self.address})")
            return False
        
        # 如果未指定特征UUID，则尝试使用已知的可写特征
        if characteristic_uuid is None:
            # 这里需要实现查找可写特征的逻辑
            # 由于命令行操作较为复杂，这里只是一个示例
            logger.error("未指定特征UUID")
            return False
        
        return self.write_characteristic(characteristic_uuid, data)
    
    def receive_data(self, timeout: int = 5, characteristic_uuid: Optional[str] = None) -> Optional[bytes]:
        """
        从设备接收数据
        
        参数:
            timeout: 接收超时时间（秒）
            characteristic_uuid: 特征UUID，如果为None则使用默认特征
            
        返回:
            Optional[bytes]: 接收到的数据，超时或失败则返回None
        """
        if not self.connected:
            logger.error(f"设备未连接: {self.name} ({self.address})")
            return None
        
        # 如果未指定特征UUID，则尝试使用已知的可读特征
        if characteristic_uuid is None:
            # 这里需要实现查找可读特征的逻辑
            # 由于命令行操作较为复杂，这里只是一个示例
            logger.error("未指定特征UUID")
            return None
        
        return self.read_characteristic(characteristic_uuid)
