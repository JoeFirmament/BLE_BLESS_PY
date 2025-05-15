#!/usr/bin/env python3
"""
基于 bless 的 BLE UART 服务器示例
实现 Nordic UART Service (NUS)
"""

import asyncio
import logging
import signal
import sys
import time
import traceback
from typing import Dict, Any
from bless import BlessServer, BlessGATTCharacteristic, BlessGATTService, GATTCharacteristicProperties, GATTAttributePermissions
from bless.exceptions import BlessError

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,  # 生产环境使用 INFO，调试时改为 DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ble_uart.log')  # 添加文件日志
    ]
)
logger = logging.getLogger(__name__)

# 定义 Nordic UART Service (NUS) UUIDs
NUS_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
NUS_RX_CHARACTERISTIC_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # 用于客户端写入 (手机发送数据到板端)
NUS_TX_CHARACTERISTIC_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # 用于服务器通知 (板端发送数据到手机)

# 全局变量
server = None
running = True
connection_manager = None # Make connection_manager global or pass it
server_status = None # Make server_status global or pass it

class ConnectionManager:
    """连接管理器"""
    def __init__(self):
        self.connected_clients = set()
        self._lock = asyncio.Lock()

    async def add_client(self, client_address):
        async with self._lock:
            self.connected_clients.add(client_address)
            logger.info(f"客户端已连接: {client_address}, 当前连接数: {len(self.connected_clients)}")

    async def remove_client(self, client_address):
        async with self._lock:
            self.connected_clients.discard(client_address)
            logger.info(f"客户端已断开: {client_address}, 当前连接数: {len(self.connected_clients)}")

    def is_connected(self, client_address):
        return client_address in self.connected_clients

class ServerStatus:
    """服务器状态监控"""
    def __init__(self):
        self.start_time = None
        self.total_messages = 0
        self.error_count = 0
        self._lock = asyncio.Lock()

    async def start(self):
        self.start_time = time.time()

    async def record_message(self):
        async with self._lock:
            self.total_messages += 1

    async def record_error(self):
        async with self._lock:
            self.error_count += 1

    def get_uptime(self):
        if self.start_time:
            return time.time() - self.start_time
        return 0

    def get_stats(self):
        return {
            "uptime": self.get_uptime(),
            "total_messages": self.total_messages,
            "error_rate": self.error_count / self.total_messages if self.total_messages > 0 else 0
        }

async def check_prerequisites():
    """检查运行前提条件"""
    try:
        # 检查蓝牙控制器状态
        logger.debug("检查蓝牙控制器状态...")
        result = await asyncio.create_subprocess_shell(
            "hciconfig",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()

        if result.returncode != 0:
            logger.error(f"hciconfig 命令失败，返回码: {result.returncode}, 错误: {stderr.decode()}")
            return False

        if b"UP RUNNING" not in stdout:
            logger.error("蓝牙控制器未启动或未运行。请使用 'sudo hciconfig hci0 up' 启动。")
            return False

        logger.debug("蓝牙控制器检查通过。")
        return True
    except Exception as e:
        logger.error(f"前提条件检查失败: {e}")
        traceback.print_exc()
        return False

def signal_handler(sig, frame):
    """处理信号"""
    global running, server
    logger.info("正在关闭服务器...")
    running = False

# Define the write request handler function, now accepting characteristic as argument
async def handle_write_request(characteristic: BlessGATTCharacteristic, value: bytearray, **kwargs):
    """处理从客户端接收到的数据"""
    global server_status # Access global server_status

    logger.debug(f"收到写入请求到特征 {characteristic.uuid}: {value}")

    # Check if the write is for the RX characteristic
    if characteristic.uuid == NUS_RX_CHARACTERISTIC_UUID:
        try:
            # 数据验证
            if not value:
                logger.warning("收到空数据")
                await server_status.record_error()
                return False

            # 假设最大数据长度为 512 字节
            if len(value) > 512:
                logger.warning(f"数据过长: {len(value)} bytes")
                await server_status.record_error()
                return False

            # 记录消息
            await server_status.record_message()

            message = value.decode('utf-8', errors='ignore')
            logger.info(f"收到消息: {message}")

            if not message.strip():
                logger.warning("收到空消息")
                await server_status.record_error()
                return False

            # --- 您可以在这里处理收到的自定义信息 ---
            # 例如，根据收到的信息执行某些操作
            # 如果需要发送回复，可以使用 server.update_value 或 server.send_notification

            # 示例：收到数据后，发送一个简单的回复 (通过 TX 特征发送通知)
            # 获取 TX 特征对象
            tx_characteristic = server.get_characteristic(NUS_TX_CHARACTERISTIC_UUID)
            if tx_characteristic:
                response = f"Echo: {message}".encode('utf-8') # 将回复编码回字节
                # update_value 会更新特征的本地值，send_notification 会发送通知给已订阅的客户端
                # 对于通知，通常只需要 update_value，订阅的客户端会自动收到新的值
                try:
                     # Use asyncio.timeout for sending notification as well
                    async with asyncio.timeout(5.0):
                        await server.update_value(NUS_TX_CHARACTERISTIC_UUID, response)
                        logger.info(f"已发送回复: {response.decode('utf-8', errors='ignore')}")
                except asyncio.TimeoutError:
                    logger.error("发送响应超时")
                    await server_status.record_error()
                    return False # Indicate failure to the client if response sending fails
            else:
                 logger.warning("TX 特征不可用，无法发送回复")
                 await server_status.record_error()
                 return False # Indicate failure to the client if TX characteristic is missing


            return True # 返回 True 表示写入成功
        except Exception as e:
            logger.error(f"处理写入数据时出错: {e}")
            traceback.print_exc()
            await server_status.record_error()
            return False # 返回 False 表示处理失败
    else:
        logger.warning(f"收到写入请求到未知特征: {characteristic.uuid}")
        await server_status.record_error()
        return False # Indicate failure for writes to other characteristics


async def main():
    """主函数，设置并运行 BLE 服务器"""
    global running, server, connection_manager, server_status # Declare global variables

    # 创建状态管理器
    connection_manager = ConnectionManager()
    server_status = ServerStatus()

    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 检查前提条件
    if not await check_prerequisites():
        logger.error("前提条件检查失败，程序退出")
        return

    logger.info("正在创建 BLE 服务器...")

    try:
        # 获取当前运行的事件循环
        loop = asyncio.get_running_loop()

        # 创建 BLE 服务器实例
        # Pass connection and disconnection handlers to the constructor
        server = BlessServer(
            name="Rock5C_BLE_UART",
            loop=loop,
            handle_connection=connection_manager.add_client, # Pass the coroutine directly
            handle_disconnection=connection_manager.remove_client # Pass the coroutine directly
        )
        logger.debug("BlessServer 实例创建成功")

        # Remove the incorrect set_connection_handler and set_disconnection_handler calls
        # server.set_connection_handler(lambda client_address: asyncio.create_task(connection_manager.add_client(client_address)))
        # server.set_disconnection_handler(lambda client_address: asyncio.create_task(connection_manager.remove_client(client_address)))
        # logger.debug("连接和断开连接处理器设置成功") # Removed this log as handlers are set in constructor


        # 启动状态监控
        await server_status.start()

        try:
            # 添加 Nordic UART Service (NUS)
            logger.debug(f"尝试添加服务: {NUS_SERVICE_UUID}")
            await server.add_new_service(NUS_SERVICE_UUID)
            logger.info(f"已添加服务: {NUS_SERVICE_UUID}")

            # 添加 RX 特征 (客户端写入)
            rx_properties = GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response
            rx_permissions = GATTAttributePermissions.writeable # Corrected permission name
            logger.debug(f"尝试添加 RX 特征: {NUS_RX_CHARACTERISTIC_UUID} with properties {rx_properties} and permissions {rx_permissions}")
            try:
                await server.add_new_characteristic(
                    NUS_SERVICE_UUID,
                    NUS_RX_CHARACTERISTIC_UUID,
                    rx_properties,
                    bytearray(), # 初始值
                    rx_permissions
                )
                logger.info(f"已添加 RX 特征: {NUS_RX_CHARACTERISTIC_UUID}")
            except Exception as e:
                logger.error(f"添加 RX 特征时出错: {e}")
                traceback.print_exc()
                running = False
                return

            # 添加 TX 特征 (服务器通知和读取)
            if running:
                tx_properties = GATTCharacteristicProperties.notify | GATTCharacteristicProperties.read
                tx_permissions = GATTAttributePermissions.readable # Corrected permission name
                logger.debug(f"尝试添加 TX 特特征: {NUS_TX_CHARACTERISTIC_UUID} with properties {tx_properties} and permissions {tx_permissions}")
                try:
                    await server.add_new_characteristic(
                        NUS_SERVICE_UUID,
                        NUS_TX_CHARACTERISTIC_UUID,
                        tx_properties,
                        bytearray(), # 初始值
                        tx_permissions
                    )
                    logger.info(f"已添加 TX 特征: {NUS_TX_CHARACTERISTIC_UUID}")
                except Exception as e:
                    logger.error(f"添加 TX 特征时出错: {e}")
                    traceback.print_exc()
                    running = False
                    return

            # 设置服务器级别的写入请求处理器
            # This handler will be called for all write requests
            server.write_request_func = handle_write_request
            logger.info("已设置服务器写入请求处理器")


        except BlessError as e:
             logger.error(f"Bless Error during service/characteristic setup: {e}")
             traceback.print_exc()
             running = False
             return
        except Exception as e:
             logger.error(f"Unexpected error during service/characteristic setup: {e}")
             traceback.print_exc()
             running = False
             return


        # Start the BLE server and begin advertising
        if running:
            logger.debug("尝试启动服务器...")
            await server.start()
            logger.info(f"BLE UART 服务器已启动，设备名称: {server.name}")
            logger.info(f"服务 UUID: {NUS_SERVICE_UUID}")
            logger.info(f"RX 特征 UUID (写入): {NUS_RX_CHARACTERISTIC_UUID}")
            logger.info(f"TX 特征 UUID (通知/读取): {NUS_TX_CHARACTERISTIC_UUID}")
            logger.info("等待客户端连接...")

            # Keep the server running until the running flag is set to False by signal handler or setup error
            while running:
                await asyncio.sleep(1)

            # Stop the server when the loop exits
            if server:
                try:
                    logger.debug("尝试停止服务器...")
                    await server.stop()
                    logger.info("BLE UART 服务器已停止")
                except Exception as e:
                    logger.error(f"停止服务器时出错: {e}")
                    traceback.print_exc()


    except Exception as e:
        logger.error(f"顶级运行时出错: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序通过 Ctrl+C 退出")
        pass

