# 开发日志

## 2024-03-21

### 问题1：LightBlue 持续请求配对
**问题描述**：
- 在使用 LightBlue 连接设备时，应用持续请求配对
- 这不是我们期望的行为，因为这是一个简单的 UART 服务，不需要配对

**解决方案**：
- 在代码中设置 `adapter1.Pairable(false)` 禁用配对功能
- 修改位置：`nus_simple.cpp` 中的蓝牙适配器配置部分
- 这样设置后，LightBlue 可以直接连接设备，无需配对

### 问题2：运行时找不到动态库
**问题描述**：
- 运行 `./nus_simple` 时报错：找不到 `libbluez-dbus-cpp.so.0`
- 库文件实际位置在 `/home/radxa/bluetooth_toolkit/bluez-dbus-cpp/build/` 目录下

**解决方案**：
- 使用 `LD_LIBRARY_PATH` 环境变量指定库文件路径
- 运行命令：
```bash
LD_LIBRARY_PATH=./bluez-dbus-cpp/build:$LD_LIBRARY_PATH ./nus_simple
```
- 这样程序可以正确找到并加载动态库

### 开发进度
- [x] 解决 LightBlue 配对问题
- [x] 解决动态库加载问题
- [ ] 考虑将解决方案添加到自动化构建流程中 