"""
蓝牙协议工具包 - 用于蓝牙设备通信和协议传递的Python库
"""

__version__ = '0.1.0'

from .manager import BluetoothManager
from .device import BluetoothDevice, BLEDevice
from .protocol import Protocol, ProtocolHandler

__all__ = [
    'BluetoothManager',
    'BluetoothDevice',
    'BLEDevice',
    'Protocol',
    'ProtocolHandler',
]
