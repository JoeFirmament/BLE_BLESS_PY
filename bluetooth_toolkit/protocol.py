"""
协议处理模块 - 提供蓝牙协议的封装和处理
"""

import logging
import struct
import time
from typing import Dict, List, Optional, Union, Callable, Any, Tuple

logger = logging.getLogger(__name__)

class Protocol:
    """协议基类，定义协议的基本结构和操作"""
    
    def __init__(self, name: str, version: str = "1.0"):
        """
        初始化协议
        
        参数:
            name: 协议名称
            version: 协议版本，默认为"1.0"
        """
        self.name = name
        self.version = version
        self.commands = {}  # 命令字典
        self.handlers = {}  # 处理函数字典
    
    def register_command(self, command_id: int, name: str, handler: Optional[Callable] = None) -> None:
        """
        注册命令
        
        参数:
            command_id: 命令ID
            name: 命令名称
            handler: 命令处理函数，可选
        """
        self.commands[command_id] = name
        if handler:
            self.handlers[command_id] = handler
            logger.debug(f"已注册命令处理函数: {name} (ID: {command_id})")
    
    def encode_packet(self, command_id: int, data: bytes = b"") -> bytes:
        """
        编码数据包
        
        参数:
            command_id: 命令ID
            data: 数据负载
            
        返回:
            bytes: 编码后的数据包
        """
        # 基本协议格式: [包头(1字节)] [命令ID(1字节)] [数据长度(2字节)] [数据] [校验和(1字节)]
        packet_header = 0xAA  # 包头
        data_length = len(data)
        
        # 构建数据包
        packet = struct.pack("!BH", command_id, data_length) + data
        
        # 计算校验和
        checksum = sum(packet) & 0xFF
        
        # 添加包头和校验和
        packet = bytes([packet_header]) + packet + bytes([checksum])
        
        return packet
    
    def decode_packet(self, packet: bytes) -> Tuple[Optional[int], Optional[bytes]]:
        """
        解码数据包
        
        参数:
            packet: 接收到的数据包
            
        返回:
            Tuple[Optional[int], Optional[bytes]]: (命令ID, 数据负载)，解析失败则返回(None, None)
        """
        # 检查数据包长度
        if len(packet) < 5:  # 包头(1) + 命令ID(1) + 数据长度(2) + 校验和(1)
            logger.error(f"数据包长度不足: {len(packet)}")
            return None, None
        
        # 检查包头
        if packet[0] != 0xAA:
            logger.error(f"无效的包头: {packet[0]}")
            return None, None
        
        # 解析命令ID和数据长度
        command_id, data_length = struct.unpack("!BH", packet[1:4])
        
        # 检查数据包长度是否匹配
        expected_length = 5 + data_length  # 包头(1) + 命令ID(1) + 数据长度(2) + 数据(data_length) + 校验和(1)
        if len(packet) != expected_length:
            logger.error(f"数据包长度不匹配: 预期 {expected_length}，实际 {len(packet)}")
            return None, None
        
        # 提取数据负载
        data = packet[4:-1]
        
        # 检查校验和
        expected_checksum = sum(packet[1:-1]) & 0xFF
        actual_checksum = packet[-1]
        if expected_checksum != actual_checksum:
            logger.error(f"校验和不匹配: 预期 {expected_checksum}，实际 {actual_checksum}")
            return None, None
        
        return command_id, data
    
    def handle_packet(self, packet: bytes) -> Optional[bytes]:
        """
        处理接收到的数据包
        
        参数:
            packet: 接收到的数据包
            
        返回:
            Optional[bytes]: 响应数据包，如果不需要响应则返回None
        """
        # 解码数据包
        command_id, data = self.decode_packet(packet)
        if command_id is None:
            return None
        
        # 查找命令处理函数
        handler = self.handlers.get(command_id)
        if handler:
            try:
                # 调用处理函数
                response_data = handler(data)
                if response_data is not None:
                    # 编码响应数据包
                    return self.encode_packet(command_id, response_data)
            except Exception as e:
                logger.error(f"处理命令时出错: {e}")
        else:
            logger.warning(f"未找到命令处理函数: {command_id}")
        
        return None


class ProtocolHandler:
    """协议处理器，用于管理多个协议"""
    
    def __init__(self):
        """初始化协议处理器"""
        self.protocols = {}  # 协议字典
        self.default_protocol = None  # 默认协议
    
    def register_protocol(self, protocol_id: int, protocol: Protocol, default: bool = False) -> None:
        """
        注册协议
        
        参数:
            protocol_id: 协议ID
            protocol: 协议对象
            default: 是否设为默认协议
        """
        self.protocols[protocol_id] = protocol
        logger.info(f"已注册协议: {protocol.name} (ID: {protocol_id})")
        
        if default or self.default_protocol is None:
            self.default_protocol = protocol_id
            logger.info(f"已设置默认协议: {protocol.name} (ID: {protocol_id})")
    
    def get_protocol(self, protocol_id: Optional[int] = None) -> Optional[Protocol]:
        """
        获取协议对象
        
        参数:
            protocol_id: 协议ID，如果为None则返回默认协议
            
        返回:
            Optional[Protocol]: 协议对象，如果未找到则返回None
        """
        if protocol_id is None:
            if self.default_protocol is None:
                logger.error("未设置默认协议")
                return None
            protocol_id = self.default_protocol
        
        protocol = self.protocols.get(protocol_id)
        if protocol is None:
            logger.error(f"未找到协议: {protocol_id}")
        
        return protocol
    
    def encode_packet(self, command_id: int, data: bytes = b"", protocol_id: Optional[int] = None) -> Optional[bytes]:
        """
        编码数据包
        
        参数:
            command_id: 命令ID
            data: 数据负载
            protocol_id: 协议ID，如果为None则使用默认协议
            
        返回:
            Optional[bytes]: 编码后的数据包，如果协议未找到则返回None
        """
        protocol = self.get_protocol(protocol_id)
        if protocol:
            return protocol.encode_packet(command_id, data)
        return None
    
    def decode_packet(self, packet: bytes, protocol_id: Optional[int] = None) -> Tuple[Optional[int], Optional[bytes]]:
        """
        解码数据包
        
        参数:
            packet: 接收到的数据包
            protocol_id: 协议ID，如果为None则使用默认协议
            
        返回:
            Tuple[Optional[int], Optional[bytes]]: (命令ID, 数据负载)，解析失败则返回(None, None)
        """
        protocol = self.get_protocol(protocol_id)
        if protocol:
            return protocol.decode_packet(packet)
        return None, None
    
    def handle_packet(self, packet: bytes, protocol_id: Optional[int] = None) -> Optional[bytes]:
        """
        处理接收到的数据包
        
        参数:
            packet: 接收到的数据包
            protocol_id: 协议ID，如果为None则使用默认协议
            
        返回:
            Optional[bytes]: 响应数据包，如果不需要响应则返回None
        """
        protocol = self.get_protocol(protocol_id)
        if protocol:
            return protocol.handle_packet(packet)
        return None
