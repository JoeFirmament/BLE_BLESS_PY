//
// 基于 bluez-dbus-cpp 示例程序的 Nordic UART Service 实现
//

#include <bluez-dbus-cpp/bluez.h>
#include <bluez-dbus-cpp/GenericCharacteristic.h>
#include <bluez-dbus-cpp/ReadOnlyCharacteristic.h>
#include "bluez-dbus-cpp/example/SerialCharacteristic.h"

#include <iostream>
#include <signal.h>

using namespace org::bluez;

constexpr const char* BLUEZ_SERVICE = "org.bluez";
constexpr const char* DEVICE0 = "/org/bluez/hci0";

// 自定义 BLE 服务 UUIDs
constexpr const char* NUS_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb";
constexpr const char* NUS_RX_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"; // 接收特征值（写入）
constexpr const char* NUS_TX_CHAR_UUID = "0000ffe2-0000-1000-8000-00805f9b34fb"; // 发送特征值（通知）

static int sig = 0;
static void sig_callback(int signum)
{
    exit(signum);
}

int main(int, char**)
{
    std::cout << "=== Nordic UART Service (NUS) 示例程序 ===" << std::endl;

    if( signal(SIGINT, sig_callback) == SIG_ERR )
        std::cerr << std::endl << "错误：注册信号处理程序失败" << std::endl;

    constexpr const char* APP_PATH = "/org/bluez/example";
    constexpr const char* ADV_PATH = "/org/bluez/example/advertisement1";

    constexpr const char* NAME = "RK3588_BLE_DEVICE";

    std::cout << "应用路径: " << APP_PATH << std::endl;
    std::cout << "广告路径: " << ADV_PATH << std::endl;
    std::cout << "设备名称: " << NAME << std::endl;

    std::cout << "创建系统 D-Bus 连接..." << std::endl;
    std::shared_ptr<IConnection> connection{ std::move( sdbus::createSystemBusConnection() ) };
    std::cout << "系统 D-Bus 连接已创建" << std::endl;

    // ---- 适配器信息 -----------------------------------------------------------------------------------------------

    {
        Adapter1 adapter1{ *connection, BLUEZ_SERVICE, DEVICE0 };

        adapter1.Powered( true );
        adapter1.Discoverable( true );
        //无需验证和加密
        adapter1.Pairable( false ); 
        adapter1.Alias( NAME );

        std::cout << "找到适配器 '" << DEVICE0 << "'" << std::endl;
        std::cout << "  名称: " << adapter1.Name() << std::endl;
        std::cout << "  地址: " << adapter1.Address() << " 类型: " << adapter1.AddressType() << std::endl;
        std::cout << "  已启用: " << adapter1.Powered() << std::endl;
        std::cout << "  可发现: " << adapter1.Discoverable() << std::endl;
        std::cout << "  可配对: " << adapter1.Pairable() << std::endl;
    }

    std::cout << std::endl;

    // ---- 服务 ---------------------------------------------------------------------------------------------------
    GattManager1 gattMgr{ connection, BLUEZ_SERVICE, DEVICE0 };
    auto app = std::make_shared<GattApplication1>( connection, APP_PATH );

    // 创建设备信息服务
    auto srv1 = std::make_shared<GattService1>( app, "deviceinfo", "180A" );
    ReadOnlyCharacteristic::createFinal( srv1, "2A24", NAME ); // 型号名称
    ReadOnlyCharacteristic::createFinal( srv1, "2A25", "RK3588-12345678" ); // 序列号
    ReadOnlyCharacteristic::createFinal( srv1, "2A26", "1.0.0" ); // 固件版本
    ReadOnlyCharacteristic::createFinal( srv1, "2A27", "A" ); // 硬件版本
    ReadOnlyCharacteristic::createFinal( srv1, "2A28", "1.0" ); // 软件版本
    ReadOnlyCharacteristic::createFinal( srv1, "2A29", "Radxa" ); // 制造商

    // 创建 Nordic UART Service
    std::cout << "创建 Nordic UART Service (NUS)..." << std::endl;
    auto srv2 = std::make_shared<GattService1>( app, "nus", NUS_SERVICE_UUID );
    std::cout << "NUS 服务已创建，UUID: " << NUS_SERVICE_UUID << std::endl;

    // 创建 NUS RX 特性（用于接收数据）
    std::cout << "创建 NUS RX 特性..." << std::endl;
    SerialCharacteristic::create( srv2, connection, NUS_RX_CHAR_UUID )
        .finalize();
    std::cout << "NUS RX 特性已创建，UUID: " << NUS_RX_CHAR_UUID << std::endl;

    std::cout << "准备注册 GATT 应用程序..." << std::endl;

    auto register_app_callback = [](const sdbus::Error* error)
    {
        if( error == nullptr )
        {
            std::cout << "GATT 应用程序注册成功！" << std::endl;
            std::cout << "现在您应该能够在 LightBlue 应用中看到设备 'RK3588_BLE_UART'" << std::endl;
            std::cout << "如果看不到，请尝试以下操作：" << std::endl;
            std::cout << "1. 确保 iPhone 的蓝牙已启用" << std::endl;
            std::cout << "2. 刷新 LightBlue 应用中的设备列表" << std::endl;
            std::cout << "3. 确保 iPhone 与 RK3588 板之间的距离不太远" << std::endl;
        }
        else
        {
            std::cerr << "错误：注册 GATT 应用程序失败" << std::endl;
            std::cerr << "错误名称: " << error->getName() << std::endl;
            std::cerr << "错误消息: " << error->getMessage() << std::endl;
        }
    };

    gattMgr.RegisterApplicationAsync( app->getPath(), {} )
        .uponReplyInvoke(register_app_callback);

    // ---- 广告 ------------------------------------------------------------------------------------------------

    auto mgr = std::make_shared<LEAdvertisingManager1>( connection, BLUEZ_SERVICE, DEVICE0 );
    std::cout << "LEAdvertisingManager1" << std::endl;
    std::cout << "  ActiveInstances: " << mgr->ActiveInstances() << std::endl;
    std::cout << "  SupportedInstances: " << mgr->SupportedInstances() << std::endl;
    {
        std::cout << "  SupportedIncludes: ";
        auto includes = mgr->SupportedIncludes();
        for( auto include : includes )
        {
            std::cout << "\"" << include <<"\",";
        }
        std::cout << std::endl;
    }

    auto register_adv_callback = [](const sdbus::Error* error) -> void
    {
        if( error == nullptr )
        {
            std::cout << "广告注册成功。" << std::endl;
        }
        else
        {
            std::cerr << "错误：注册广告失败 " << error->getName() << " 错误消息: " << error->getMessage() << std::endl;
        }
    };

    std::cout << "创建广告..." << std::endl;

    // 使用 NUS UUID 进行广告
    std::cout << "广告 UUID: " << NUS_SERVICE_UUID << std::endl;

    // 创建广告对象并注册
    // 简化广告参数，只使用必要的选项
    auto ad = LEAdvertisement1::create( *connection, ADV_PATH )
        .withLocalName( NAME )
        .withServiceUUIDs( std::vector{ std::string{NUS_SERVICE_UUID} } )
        // 只包含 tx-power，不包含 appearance
        .withIncludes( std::vector{ std::string{ "tx-power" } } )
        .onReleaseCall( [](){ std::cout << "广告已释放" << std::endl; } )
        .registerWith( mgr, register_adv_callback );

    std::cout << "广告已注册" << std::endl;

    std::cout << "加载完成。" << std::endl;

    // 使用 enterEventLoopAsync 替代已弃用的 enterProcessingLoopAsync
    connection->enterEventLoopAsync();

    bool run = true;
    while( run) {
        char cmd;
        std::cout << "命令:" << std::endl;
        std::cout << "  q      退出" << std::endl;
        std::cout << "$> ";
        std::cin >> cmd;

        switch(cmd)
        {
            case 'q':
                run = false;
        }
    }
}
