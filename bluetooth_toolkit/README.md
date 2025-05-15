# 蓝牙协议工具包

这个工具包提供了用于蓝牙设备通信和协议传递的Python库。

## 功能特性

- 蓝牙设备发现和连接
- 低功耗蓝牙(BLE)支持
- 自定义协议传输
- 简单易用的API接口

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用示例

```python
from bluetooth_toolkit import BluetoothManager

# 初始化蓝牙管理器
bt_manager = BluetoothManager()

# 扫描设备
devices = bt_manager.scan_devices(timeout=5)
for device in devices:
    print(f"发现设备: {device.name} ({device.address})")

# 连接到设备
device = bt_manager.connect_device("XX:XX:XX:XX:XX:XX")

# 发送数据
device.send_data(b"Hello World")

# 接收数据
data = device.receive_data(timeout=5)
print(f"接收到数据: {data}")

# 断开连接
device.disconnect()
```

## 项目结构

- `bluetooth_toolkit/` - 主要代码库
  - `__init__.py` - 包初始化文件
  - `manager.py` - 蓝牙管理器类
  - `device.py` - 蓝牙设备类
  - `protocol.py` - 协议处理类
  - `utils.py` - 工具函数
- `examples/` - 使用示例
- `tests/` - 测试代码

## 许可证

MIT
