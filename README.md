# BLE UART 服务器 (基于 BLESS)

这是一个基于 Python BLESS 库实现的 BLE UART 服务器，用于在 Rock 5C 开发板上实现 Nordic UART Service (NUS)。

## 功能特点

- 实现标准的 Nordic UART Service (NUS)
- 支持 BLE GATT 服务器功能
- 提供双向通信能力（读写和通知）
- 完整的错误处理和日志记录
- 连接管理和状态监控
- 支持与 iPhone LightBlue 等 BLE 客户端应用通信

## 硬件要求

- Rock 5C 开发板
- AICSemi AIC 8800D80 WiFi+蓝牙芯片
- 支持 BLE 的客户端设备（如智能手机）

## 软件要求

- Python 3.7+
- Linux 操作系统（已在 Rock 5C 上测试）
- bless 库
- 其他 Python 依赖包

## 安装

1. 克隆仓库：
```bash
git clone git@github.com:JoeFirmament/BLE_BLESS_PY.git
cd BLE_BLESS_PY
```

2. 创建并激活虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 确保蓝牙控制器已启动：
```bash
sudo hciconfig hci0 up
```

2. 运行服务器：
```bash
python3 bless_uart_server.py
```

3. 使用 BLE 客户端（如 iPhone 的 LightBlue 应用）连接到设备：
   - 设备名称：Rock5C_BLE_UART
   - 服务 UUID：6E400001-B5A3-F393-E0A9-E50E24DCCA9E
   - RX 特征 UUID：6E400002-B5A3-F393-E0A9-E50E24DCCA9E（写入）
   - TX 特征 UUID：6E400003-B5A3-F393-E0A9-E50E24DCCA9E（通知/读取）

## 特性说明

- **连接管理**：支持多客户端连接管理
- **状态监控**：实时监控服务器状态、消息统计和错误率
- **自动回显**：收到消息后自动发送回显响应
- **错误处理**：完整的错误处理和日志记录机制
- **资源管理**：自动管理连接和资源释放

## 日志

日志文件保存在 `ble_uart.log`，包含详细的运行时信息和错误记录。

## 开发

### 代码结构

- `bless_uart_server.py`：主服务器实现
- `ConnectionManager`：连接管理类
- `ServerStatus`：服务器状态监控类
- `handle_write_request`：数据处理函数

### 调试模式

修改日志级别为 DEBUG 可以获取更详细的调试信息：

```python
logging.basicConfig(level=logging.DEBUG)
```

## 故障排除

1. 确保蓝牙控制器正常工作：
```bash
hciconfig
```

2. 检查服务器日志：
```bash
tail -f ble_uart.log
```

3. 常见问题：
   - 蓝牙控制器未启动
   - 权限问题
   - 客户端连接超时
   - 数据格式错误

4. TODO  发送信息只是做了触发，没有显示。此程序用来验证流程性。
