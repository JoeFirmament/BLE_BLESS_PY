# 开发日志

## 开发平台信息

### 硬件信息

- **开发板**：RK3588 (Rock 5C)
- **CPU 架构**：ARM64 (Cortex-A76 + Cortex-A55)
- **内存**：4GB LPDDR4
- **蓝牙芯片**：内置蓝牙 5.0

### 软件信息

- **操作系统**：Linux (Debian 11)
- **内核版本**：5.10.160
- **编译器**：g++ (GCC) 10.2.1
- **蓝牙协议栈**：BlueZ 5.55
- **D-Bus 库**：sdbus-cpp 0.8.3

### 开发环境

- **IDE**：Visual Studio Code
- **构建系统**：Make
- **版本控制**：Git
- **调试工具**：
  - D-Bus 监视器 (`dbus-monitor`)
  - BlueZ 工具 (`bluetoothctl`, `hciconfig`)
  - 系统日志 (`journalctl`)

### 测试设备

- **移动设备**：iPhone 13 Pro
- **应用程序**：LightBlue Explorer
- **协议**：Bluetooth Low Energy (BLE) 5.0

## sdbus-cpp 三层 API 详解

sdbus-cpp 提供了三种不同层次的 API 来实现 D-Bus 通信：

### 1. 基本 API 层 (Basic API Layer)

这是最底层的 API，直接在 sd-bus 之上提供 C++ 封装：

- **特点**：需要手动创建和处理 D-Bus 消息
- **优势**：提供最大的灵活性和控制
- **劣势**：代码冗长，需要处理更多底层细节
- **适用场景**：需要精细控制 D-Bus 消息的场景，或需要使用 sdbus-cpp 未直接支持的 D-Bus 功能

基本 API 层的典型用法：
```cpp
// 创建方法调用
auto methodCall = proxy->createMethodCall("org.example.Interface", "Method");
// 添加参数
methodCall << arg1 << arg2;
// 发送调用并获取回复
auto reply = proxy->callMethod(methodCall);
// 从回复中提取结果
Type result;
reply >> result;
```

### 2. 便捷 API 层 (Convenience API Layer)

这一层抽象了底层的 D-Bus 消息概念：

- **特点**：提供更简洁、更易用的接口
- **优势**：代码简洁，易于理解，利用 C++ 类型系统在编译时推导
- **劣势**：灵活性略低于基本 API 层
- **适用场景**：大多数标准 D-Bus 通信场景

便捷 API 层的典型用法：
```cpp
// 一行代码完成方法调用并获取结果
Type result;
proxy->callMethod("Method")
    .onInterface("org.example.Interface")
    .withArguments(arg1, arg2)
    .storeResultsTo(result);
```

### 3. C++ 绑定层 (C++ Bindings Layer)

这是最高级别的 API，使用代码生成工具：

- **特点**：使用 `sdbus-c++-xml2cpp` 工具从 D-Bus XML IDL 描述生成 C++ 绑定代码
- **优势**：D-Bus RPC 调用看起来完全像本地 C++ 对象的调用，最简洁
- **劣势**：需要额外的代码生成步骤，灵活性最低
- **适用场景**：有明确定义的 D-Bus 接口，需要最高级别抽象的场景

C++ 绑定层的典型用法：
```cpp
// 假设已生成绑定代码
auto proxy = createProxy<org::example::Interface>();
// 直接调用方法，就像调用本地对象一样
Type result = proxy->Method(arg1, arg2);
```

## BlueZ D-Bus API 详解

BlueZ 是 Linux 的官方蓝牙协议栈，它通过 D-Bus 提供了其 API。以下是我们在项目中使用的主要 BlueZ D-Bus 接口：

### 1. GattManager1

用于注册和管理 GATT 应用程序：

- **主要方法**：
  - `RegisterApplication(object application, dict options)` - 注册 GATT 应用程序
  - `UnregisterApplication(object application)` - 注销 GATT 应用程序

### 2. LEAdvertisingManager1

用于注册和管理 BLE 广告：

- **主要方法**：
  - `RegisterAdvertisement(object advertisement, dict options)` - 注册广告
  - `UnregisterAdvertisement(object advertisement)` - 注销广告

### 3. GattService1

表示 GATT 服务：

- **主要属性**：
  - `UUID` - 服务的 UUID
  - `Primary` - 是否是主服务
  - `Characteristics` - 服务包含的特性列表

### 4. GattCharacteristic1

表示 GATT 特性：

- **主要方法**：
  - `ReadValue(dict options)` - 读取特性值
  - `WriteValue(array{byte} value, dict options)` - 写入特性值
  - `StartNotify()` - 开始通知
  - `StopNotify()` - 停止通知

- **主要属性**：
  - `UUID` - 特性的 UUID
  - `Service` - 特性所属的服务
  - `Value` - 特性的当前值
  - `Flags` - 特性的标志（如 "read", "write", "notify" 等）

### 5. LEAdvertisement1

表示 BLE 广告：

- **主要方法**：
  - `Release()` - 释放广告资源

- **主要属性**：
  - `Type` - 广告类型（如 "peripheral"）
  - `ServiceUUIDs` - 广告中包含的服务 UUID 列表
  - `LocalName` - 设备的本地名称
  - `Discoverable` - 是否可被发现

## 开发记录

### 2023-07-10

- 初始化项目
- 创建了两个实现版本：
  - 使用 sdbus-cpp 基本 API 层的实现 (`ble_basic_api_new.cpp`)
  - 使用 sdbus-cpp 便捷 API 层的实现 (`ble_convenience_api.cpp`)
- 实现了 Nordic UART Service (NUS)，包含 RX 和 TX 特性
- 添加了 D-Bus 配置文件 `org.example.ble_uart.conf`
- 创建了 Makefile 和 README 文件
- 详细研究了 sdbus-cpp 的三层 API 和 BlueZ D-Bus API

### 2023-07-11

- 添加了 systemd 用户服务支持，避免使用 `make install-conf` 导致 SSH 连接中断
- 修改了 Makefile，添加了 `install-service` 目标
- 更新了 README 文件，添加了关于使用 systemd 服务的说明

### 2023-07-12

- 调试便捷 API 层的实现
- 发现在用户级别的 systemd 服务中运行时，程序无法访问 BlueZ 的 D-Bus 接口，出现 "No object received" 错误
- 添加了更多的调试信息，以便更好地了解问题所在
- 使用 D-Bus 内省功能检查了 BlueZ 适配器上可用的接口
- 发现以 root 权限直接运行时，程序可以找到 BlueZ 适配器，但在注册 GATT 应用时卡住了

### 2023-07-13

- 尝试调试基本 API 层的实现
- 发现与便捷 API 层的实现类似的问题
- 分析了可能的原因：
  - BlueZ 的 D-Bus 接口可能需要特殊的权限或配置
  - GATT 应用实现可能有问题，导致 BlueZ 无法正确处理它
  - 可能存在超时或死锁问题
- 记录了建议的解决方案：
  - 检查 BlueZ 的日志
  - 使用 D-Bus 监视器工具
  - 尝试使用更简单的 BLE 示例程序
  - 考虑使用 BlueZ 的 Python API

### 2024-05-16

- 使用 bluez-dbus-cpp 库实现 Nordic UART Service
- 从 bluez-dbus-cpp 仓库中的示例程序修改创建了 `nus_simple.cpp` 文件
- 修改了 Makefile.nus_simple，添加了正确的包含路径和库路径
- 安装了 D-Bus 配置文件，解决了权限问题
- 简化了广告参数，解决了广告注册失败的问题
- 成功实现了 BLE UART 服务，可以在 LightBlue 应用中发现并连接
- 测试了数据收发功能，验证了通信正常
- 放弃了之前基于 sdbus-cpp 直接实现的方案，转而使用更高级的 bluez-dbus-cpp 库

## Nordic UART Service (NUS) 详解

Nordic UART Service (NUS) 是一个由 Nordic Semiconductor 定义的 BLE 服务，用于在 BLE 设备和中央设备（如手机）之间提供类似 UART 的通信。

### 服务 UUID

- **服务 UUID**: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`

### 特性

1. **RX 特性 (UUID: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`)**
   - **功能**: 用于从中央设备（如手机）向外设（如 RK3588）发送数据
   - **属性**: Write, Write Without Response
   - **数据流向**: 中央设备 → 外设

2. **TX 特性 (UUID: `6E400003-B5A3-F393-E0A9-E50E24DCCA9E`)**
   - **功能**: 用于从外设（如 RK3588）向中央设备（如手机）发送数据
   - **属性**: Read, Notify
   - **数据流向**: 外设 → 中央设备

### 通信流程

1. **连接建立**:
   - 外设广播其服务 UUID
   - 中央设备扫描并连接到外设

2. **数据发送 (外设 → 中央设备)**:
   - 中央设备订阅 TX 特性的通知
   - 外设通过 TX 特性发送通知
   - 中央设备接收通知数据

3. **数据接收 (中央设备 → 外设)**:
   - 中央设备向 RX 特性写入数据
   - 外设接收并处理数据

### 在我们的实现中

我们的实现完全符合 Nordic UART Service 规范，可以与支持 NUS 的应用程序（如 LightBlue）进行通信。我们的服务器每 5 秒发送一条 "Hello X" 消息，其中 X 是一个递增的字符，以演示通知功能。当服务器接收到来自客户端的数据时，会在控制台打印出来。

## 功能实现

- [x] 创建 BLE GATT 服务器
- [x] 实现 Nordic UART Service
- [x] 实现 BLE 广告
- [x] 实现数据发送（通知）
- [x] 实现数据接收（写入）
- [x] 优雅地处理信号（如 Ctrl+C）

## 调试问题与解决方案

在开发过程中，我们遇到了一些问题，并尝试了一些解决方案：

### 1. SSH 连接中断问题

**问题**：使用 `make install-conf` 安装 D-Bus 配置文件后，SSH 连接会中断。

**原因**：修改系统级别的 D-Bus 配置文件并重启 D-Bus 服务可能会影响依赖于 D-Bus 的系统服务，包括网络管理和 SSH 服务。

**解决方案**：
- 创建用户级别的 systemd 服务，避免修改系统配置
- 添加了 `install-service` 目标到 Makefile
- 更新了 README 文件，添加了关于使用 systemd 服务的说明

### 2. D-Bus 权限问题

**问题**：在用户级别的 systemd 服务中运行时，程序无法访问 BlueZ 的 D-Bus 接口，出现 "No object received" 错误。

**原因**：BlueZ 的 D-Bus 接口需要特殊的权限，只有 root 用户和 bluetooth 组的用户才能完全访问。

**解决方案**：
- 确保用户属于 bluetooth 组
- 以 root 权限运行程序
- 考虑修改 BlueZ 的 D-Bus 配置文件，允许更多的访问权限

### 3. GATT 应用注册问题

**问题**：以 root 权限直接运行时，程序可以找到 BlueZ 适配器，但在注册 GATT 应用时卡住了。

**原因**：可能是以下几种情况之一：
- GATT 应用实现可能有问题，导致 BlueZ 无法正确处理它
- 可能存在超时或死锁问题
- BlueZ 可能需要特定的 D-Bus 对象路径或接口
- ObjectManager 接口实现不完整

**调试步骤**：
- 添加了更多的调试信息
- 使用 D-Bus 内省功能检查了 BlueZ 适配器上可用的接口
- 尝试使用不同的方法来注册 GATT 应用
- 添加了超时机制，避免程序无限期卡住
- 添加了 ObjectManager 接口，并手动注册了服务和特性
- 检查了 BlueZ 的日志和 D-Bus 监视器的输出

**发现**：
- BlueZ 守护进程 (bluetoothd) 版本是 5.66，正在正常运行
- 没有在 BlueZ 日志中看到与我们的应用程序相关的错误
- 程序在调用 RegisterApplication 方法时超时，没有收到 BlueZ 的响应
- 基本 API 层和便捷 API 层的实现都遇到了相同的问题

**进一步分析**：
- ObjectManager 接口实现可能不完整：BlueZ 期望 GATT 应用程序实现 ObjectManager 接口，并通过该接口提供服务和特性的信息
- D-Bus 权限问题：虽然以 root 权限运行程序，但可能仍有一些 D-Bus 权限问题
- BlueZ 版本兼容性：BlueZ 5.66 可能与我们的代码有一些兼容性问题
- 缺少必要的 D-Bus 接口或方法：我们可能缺少 BlueZ 期望的一些必要的 D-Bus 接口或方法

**下一步计划**：
- 深入研究 BlueZ 的 D-Bus API 文档，了解 GATT 应用程序注册的详细要求
- 查看 BlueZ 的示例代码，特别是 GATT 服务器的示例代码
- 继续使用 D-Bus 调试工具监控 D-Bus 消息和 BlueZ 日志
- 尝试创建一个最小的 GATT 服务器实现，只包含必要的功能

## 待办事项

### 高优先级
- [ ] 解决 GATT 应用注册问题：
  - [ ] 正确实现 GetManagedObjects 方法
  - [ ] 确保 D-Bus 对象路径符合 BlueZ 的要求
  - [ ] 提供 BlueZ 期望的所有属性和方法
  - [ ] 测试注册流程
- [ ] 添加更多错误处理：
  - [ ] 处理 BlueZ 服务不可用的情况
  - [ ] 处理注册失败的情况
  - [ ] 处理连接断开的情况

### 中优先级
- [ ] 实现重连机制：
  - [ ] 检测连接断开
  - [ ] 自动重新注册 GATT 应用和广告
- [ ] 添加单元测试：
  - [ ] 测试 GATT 服务和特性的实现
  - [ ] 测试 D-Bus 接口的实现
  - [ ] 测试错误处理

### 低优先级
- [ ] 优化性能：
  - [ ] 减少不必要的 D-Bus 调用
  - [ ] 优化数据传输
- [ ] 添加更多配置选项：
  - [ ] 配置 GATT 服务和特性的 UUID
  - [ ] 配置广告参数
  - [ ] 配置安全级别
- [ ] 考虑使用 BlueZ 的 C API 作为替代方案

## 已知问题

- 需要 root 权限运行（可以通过修改 D-Bus 配置解决）
- 在某些系统上可能需要手动启用蓝牙适配器（`sudo hciconfig hci0 up`）
- GATT 应用注册时可能会卡住
- 在用户级别的 systemd 服务中运行时，可能无法访问 BlueZ 的 D-Bus 接口

## BlueZ D-Bus API 研究

### GATT 应用程序注册流程

根据 BlueZ 的文档和源代码，GATT 应用程序注册的流程如下：

1. **创建 GATT 应用程序对象**：
   - 应用程序对象需要实现 `org.freedesktop.DBus.ObjectManager` 接口
   - 应用程序对象需要提供 `GetManagedObjects` 方法，返回所有服务和特性的信息

2. **创建 GATT 服务对象**：
   - 服务对象需要实现 `org.bluez.GattService1` 接口
   - 服务对象需要提供以下属性：
     - `UUID`：服务的 UUID
     - `Primary`：是否是主服务
     - `Characteristics`：服务包含的特性列表

3. **创建 GATT 特性对象**：
   - 特性对象需要实现 `org.bluez.GattCharacteristic1` 接口
   - 特性对象需要提供以下属性：
     - `UUID`：特性的 UUID
     - `Service`：特性所属的服务
     - `Value`：特性的当前值
     - `Flags`：特性的标志（如 "read", "write", "notify" 等）
   - 特性对象需要提供以下方法：
     - `ReadValue`：读取特性值
     - `WriteValue`：写入特性值
     - `StartNotify`：开始通知
     - `StopNotify`：停止通知

4. **注册 GATT 应用程序**：
   - 调用 `org.bluez.GattManager1.RegisterApplication` 方法
   - 提供应用程序对象的路径和选项

### BlueZ 源代码分析

为了更深入地理解 BlueZ 的 GATT 应用程序注册流程，我们查看了 BlueZ 源代码中的关键部分：

1. **RegisterApplication 方法**：
   ```c
   static DBusMessage *manager_register_app(DBusConnection *conn,
                       DBusMessage *msg, void *user_data)
   {
       struct btd_gatt_database *database = user_data;
       const char *sender = dbus_message_get_sender(msg);
       DBusMessageIter args;
       const char *path;
       struct gatt_app *app;
       struct svc_match_data match_data;

       // ... 参数检查 ...

       app = create_app(conn, msg, path);
       if (!app)
           return btd_error_failed(msg, "Failed to register application");

       DBG("Registering application: %s:%s", sender, path);

       app->database = database;
       queue_push_tail(database->apps, app);

       return NULL;
   }
   ```

2. **create_app 函数**：
   ```c
   static struct gatt_app *create_app(DBusConnection *conn, DBusMessage *msg,
                           const char *path)
   {
       struct gatt_app *app;
       const char *sender = dbus_message_get_sender(msg);

       if (!path || !g_str_has_prefix(path, "/"))
           return NULL;

       app = new0(struct gatt_app, 1);

       app->client = g_dbus_client_new_full(conn, sender, path, path);
       if (!app->client)
           goto fail;

       // ... 初始化 app 结构 ...

       g_dbus_client_set_disconnect_watch(app->client, client_disconnect_cb, app);
       g_dbus_client_set_proxy_handlers(app->client, proxy_added_cb,
                       proxy_removed_cb, NULL, app);
       g_dbus_client_set_ready_watch(app->client, client_ready_cb, app);

       return app;

   fail:
       app_free(app);
       return NULL;
   }
   ```

3. **client_ready_cb 函数**：
   ```c
   static void client_ready_cb(GDBusClient *client, void *user_data)
   {
       struct gatt_app *app = user_data;
       DBusMessage *reply;
       bool fail = false;

       /*
        * Process received objects
        */
       if (queue_isempty(app->proxies)) {
           error("No object received");
           fail = true;
           reply = btd_error_failed(app->reg,
                       "No object received");
           goto reply;
       }

       queue_foreach(app->proxies, register_profile, app);
       queue_foreach(app->proxies, register_service, app);
       queue_foreach(app->proxies, register_characteristic, app);
       queue_foreach(app->proxies, register_descriptor, app);

       // ... 检查注册结果 ...

       DBG("GATT application registered: %s:%s", app->owner, app->path);

       reply = dbus_message_new_method_return(app->reg);

   reply:
       g_dbus_send_message(btd_get_dbus_connection(), reply);
       dbus_message_unref(app->reg);
       app->reg = NULL;

       if (fail)
           remove_app(app);
   }
   ```

4. **register_service 函数**：
   ```c
   static void register_service(void *data, void *user_data)
   {
       struct gatt_app *app = user_data;
       GDBusProxy *proxy = data;
       const char *iface = g_dbus_proxy_get_interface(proxy);
       const char *path = g_dbus_proxy_get_path(proxy);

       if (app->failed)
           return;

       if (g_strcmp0(iface, GATT_SERVICE_INTERFACE) == 0) {
           struct external_service *service;

           service = create_service(app, proxy, path);
           if (!service) {
               app->failed = true;
               return;
           }
       }
   }
   ```

### 关键发现

通过分析 BlueZ 源代码，我们发现了以下关键信息：

1. **注册流程**：
   - BlueZ 创建一个 GDBusClient 来监视应用程序的 D-Bus 对象
   - 当客户端准备就绪时，BlueZ 调用 client_ready_cb 函数
   - client_ready_cb 函数检查应用程序提供的对象，并注册服务、特性和描述符

2. **关键问题**：
   - 在 client_ready_cb 函数中，如果 queue_isempty(app->proxies) 为真，即应用程序没有提供任何对象，BlueZ 会返回错误 "No object received"
   - 这与我们在调试中看到的错误一致
   - 这表明我们的应用程序没有正确地向 BlueZ 提供 GATT 服务、特性和描述符的 D-Bus 对象

3. **ObjectManager 接口的重要性**：
   - BlueZ 使用 ObjectManager 接口来发现应用程序提供的服务和特性
   - 应用程序必须正确实现 GetManagedObjects 方法，返回所有服务和特性的信息
   - 如果 GetManagedObjects 方法没有返回任何对象，BlueZ 会认为应用程序没有提供任何服务或特性

4. **D-Bus 对象路径的层次结构**：
   - BlueZ 期望应用程序、服务和特性的对象路径有一定的层次结构
   - 例如：
     - 应用程序：`/org/example/nus_application`
     - 服务：`/org/example/nus_application/nus_service0`
     - 特性：`/org/example/nus_application/nus_service0/nus_rx_char`

### 问题原因分析

根据我们的研究，我们的 BLE UART 服务在注册 GATT 应用程序时遇到的问题可能是由以下原因导致的：

1. **GetManagedObjects 方法实现不正确**：
   - 我们添加了 ObjectManager 接口，但可能没有正确实现 GetManagedObjects 方法
   - 我们手动注册了服务和特性，但可能没有按照 BlueZ 期望的格式返回信息
   - 当 BlueZ 调用 GetManagedObjects 方法时，可能没有收到任何对象，导致 "No object received" 错误

2. **D-Bus 对象路径不符合要求**：
   - 我们使用的对象路径可能不符合 BlueZ 的要求
   - 例如，我们的服务和特性的对象路径可能没有正确的层次结构
   - BlueZ 可能无法正确识别我们的服务和特性

3. **服务和特性的属性不完整**：
   - 我们可能没有提供 BlueZ 期望的所有属性
   - 例如，我们可能缺少了一些必要的属性，如 `Value` 属性
   - BlueZ 可能无法正确识别我们的服务和特性的功能

4. **D-Bus 接口实现不完整**：
   - 我们可能没有正确实现 BlueZ 期望的所有 D-Bus 接口
   - 例如，我们可能缺少了一些必要的方法，如 `GetAll` 方法
   - BlueZ 可能无法正确与我们的服务和特性交互

### 解决方案

根据我们的研究，我们可以采取以下措施来解决问题：

1. **正确实现 GetManagedObjects 方法**：
   - 确保 GetManagedObjects 方法返回所有服务、特性和描述符的信息
   - 返回的信息应该包括每个对象的路径、接口和属性
   - 确保返回的信息符合 BlueZ 的期望格式

2. **使用正确的对象路径层次结构**：
   - 确保服务、特性和描述符的对象路径符合 BlueZ 的期望
   - 例如，服务的对象路径应该是应用程序对象路径的子路径
   - 特性的对象路径应该是服务对象路径的子路径

3. **提供所有必要的属性**：
   - 确保服务、特性和描述符提供 BlueZ 期望的所有属性
   - 例如，服务应该提供 UUID 和 Primary 属性
   - 特性应该提供 UUID、Service、Flags 和 Value 属性

4. **正确实现所有必要的 D-Bus 接口**：
   - 确保服务、特性和描述符实现 BlueZ 期望的所有 D-Bus 接口
   - 例如，特性应该实现 ReadValue、WriteValue、StartNotify 和 StopNotify 方法
   - 确保这些方法的签名符合 BlueZ 的期望

## 参考资料

- [BlueZ D-Bus API 文档](https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc)
- [BlueZ GATT API 文档](https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/gatt-api.txt)
- [BlueZ 源代码](https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/)
- [D-Bus 规范](https://dbus.freedesktop.org/doc/dbus-specification.html)
- [sdbus-cpp 文档](https://github.com/Kistler-Group/sdbus-cpp)
- [Nordic UART Service 规范](https://infocenter.nordicsemi.com/index.jsp?topic=%2Fcom.nordic.infocenter.sdk5.v14.0.0%2Fble_sdk_app_nus_eval.html)
- [LightBlue App](https://punchthrough.com/lightblue/)