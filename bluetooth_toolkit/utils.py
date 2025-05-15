"""
工具函数模块 - 提供通用的工具函数
"""

import logging
import re
import subprocess
from typing import List, Dict, Optional, Union, Any

logger = logging.getLogger(__name__)

def is_valid_mac_address(address: str) -> bool:
    """
    检查MAC地址是否有效
    
    参数:
        address: MAC地址
        
    返回:
        bool: MAC地址是否有效
    """
    # 检查MAC地址格式 (XX:XX:XX:XX:XX:XX)
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, address))

def run_command(command: List[str], timeout: int = 10) -> str:
    """
    运行命令并返回输出
    
    参数:
        command: 命令列表
        timeout: 超时时间（秒）
        
    返回:
        str: 命令输出
        
    异常:
        subprocess.TimeoutExpired: 命令执行超时
        subprocess.SubprocessError: 命令执行失败
    """
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        
        # 检查命令是否成功执行
        if result.returncode != 0:
            logger.error(f"命令执行失败: {' '.join(command)}")
            logger.error(f"错误输出: {result.stderr}")
            raise subprocess.SubprocessError(f"命令执行失败: {result.stderr}")
        
        return result.stdout
    except subprocess.TimeoutExpired:
        logger.error(f"命令执行超时: {' '.join(command)}")
        raise
    except Exception as e:
        logger.error(f"执行命令时出错: {e}")
        raise

def bytes_to_hex(data: bytes) -> str:
    """
    将字节数据转换为十六进制字符串
    
    参数:
        data: 字节数据
        
    返回:
        str: 十六进制字符串
    """
    return ' '.join(f'{b:02X}' for b in data)

def hex_to_bytes(hex_str: str) -> bytes:
    """
    将十六进制字符串转换为字节数据
    
    参数:
        hex_str: 十六进制字符串，可以包含空格
        
    返回:
        bytes: 字节数据
    """
    # 移除所有空格
    hex_str = hex_str.replace(' ', '')
    
    # 检查字符串长度是否为偶数
    if len(hex_str) % 2 != 0:
        raise ValueError("十六进制字符串长度必须为偶数")
    
    try:
        return bytes.fromhex(hex_str)
    except ValueError as e:
        logger.error(f"无效的十六进制字符串: {hex_str}")
        raise

def setup_logging(level: int = logging.INFO) -> None:
    """
    设置日志记录
    
    参数:
        level: 日志级别，默认为INFO
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger.info(f"日志记录已设置，级别: {logging.getLevelName(level)}")

def parse_device_info(info_str: str) -> Dict[str, str]:
    """
    解析设备信息字符串
    
    参数:
        info_str: 设备信息字符串
        
    返回:
        Dict[str, str]: 设备信息字典
    """
    info = {}
    for line in info_str.splitlines():
        line = line.strip()
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    return info

def get_bluetooth_status() -> Dict[str, Any]:
    """
    获取蓝牙状态
    
    返回:
        Dict[str, Any]: 蓝牙状态信息
    """
    try:
        result = run_command(["hciconfig", "-a"])
        
        # 解析蓝牙状态
        status = {
            "adapters": []
        }
        
        current_adapter = None
        for line in result.splitlines():
            line = line.strip()
            
            # 新的适配器
            if line and not line.startswith(" "):
                if ":" in line:
                    adapter_name = line.split(":", 1)[0]
                    current_adapter = {
                        "name": adapter_name,
                        "address": "",
                        "status": "",
                        "features": []
                    }
                    status["adapters"].append(current_adapter)
            
            # 适配器信息
            elif current_adapter and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                if key == "BD Address":
                    current_adapter["address"] = value
                elif key == "Status":
                    current_adapter["status"] = value
                elif key == "Features":
                    current_adapter["features"] = [f.strip() for f in value.split(",")]
        
        return status
    except Exception as e:
        logger.error(f"获取蓝牙状态时出错: {e}")
        return {"error": str(e)}

def format_device_list(devices: List[Dict[str, str]]) -> str:
    """
    格式化设备列表
    
    参数:
        devices: 设备列表
        
    返回:
        str: 格式化后的设备列表字符串
    """
    if not devices:
        return "未发现设备"
    
    result = "发现的设备:\n"
    for i, device in enumerate(devices, 1):
        result += f"{i}. {device.get('name', 'Unknown')} ({device.get('address', 'Unknown')})\n"
    
    return result
