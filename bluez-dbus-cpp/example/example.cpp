//
// Copyright Audiofile LLC 2019 - 2020.
// Distributed under the Boost Software License, Version 1.0.
// (See accompanying file LICENSE_1_0.txt or copy at https://www.boost.org/LICENSE_1_0.txt)
//

#include <bluez-dbus-cpp/bluez.h>
#include <bluez-dbus-cpp/GenericCharacteristic.h>
#include <bluez-dbus-cpp/ReadOnlyCharacteristic.h>
#include "SerialCharacteristic.h"

#include <iostream>
#include <signal.h>

using namespace org::bluez;

constexpr const char* BLUEZ_SERVICE = "org.bluez";
constexpr const char* DEVICE0 = "/org/bluez/hci0";

static int sig = 0;
static void sig_callback(int signum)
{
    exit(signum);
}

int main(int argc, char *argv[])
{
    std::cout << "=== BLE 示例程序启动 ===" << std::endl;

    if( signal(SIGINT, sig_callback) == SIG_ERR )
        std::cerr << std::endl << "错误：注册信号处理程序失败" << std::endl;

    constexpr const char* APP_PATH = "/org/bluez/example";
    constexpr const char* ADV_PATH = "/org/bluez/example/advertisement1";

    constexpr const char* NAME = "RK3588_BLE";

    std::cout << "应用路径: " << APP_PATH << std::endl;
    std::cout << "广告路径: " << ADV_PATH << std::endl;
    std::cout << "设备名称: " << NAME << std::endl;

    std::cout << "创建系统 D-Bus 连接..." << std::endl;
    std::shared_ptr<IConnection> connection{ std::move( sdbus::createSystemBusConnection() ) };
    std::cout << "系统 D-Bus 连接已创建" << std::endl;

    // ---- Adapter Info -----------------------------------------------------------------------------------------------

    {
        Adapter1 adapter1{ *connection, BLUEZ_SERVICE, DEVICE0 };

        adapter1.Powered( true );
        adapter1.Discoverable( true );
        adapter1.Pairable( true );
        adapter1.Alias( NAME );

        std::cout << "Found adapter '" << DEVICE0 << "'" << std::endl;
        std::cout << "  Name: " << adapter1.Name() << std::endl;
        std::cout << "  Address: " << adapter1.Address() << " type: " << adapter1.AddressType() << std::endl;
        std::cout << "  Powered: " << adapter1.Powered() << std::endl;
        std::cout << "  Discoverable: " << adapter1.Discoverable() << std::endl;
        std::cout << "  Pairable: " << adapter1.Pairable() << std::endl;
    }

    std::cout << std::endl;

    // ---- Services ---------------------------------------------------------------------------------------------------
    GattManager1 gattMgr{ connection, BLUEZ_SERVICE, DEVICE0 };
    auto app =  std::make_shared<GattApplication1>( connection, APP_PATH );
    auto srv1 = std::make_shared<GattService1>( app, "deviceinfo", "180A" );
    ReadOnlyCharacteristic::createFinal( srv1, "2A24", NAME ); // model name
    ReadOnlyCharacteristic::createFinal( srv1, "2A25", "333-12345678-888" ); // serial number
    ReadOnlyCharacteristic::createFinal( srv1, "2A26", "1.0.1" ); // fw rev
    ReadOnlyCharacteristic::createFinal( srv1, "2A27", "rev A" ); // hw rev
    ReadOnlyCharacteristic::createFinal( srv1, "2A28", "5.0" ); // sw rev
    ReadOnlyCharacteristic::createFinal( srv1, "2A29", "ACME Inc." ); // manufacturer

    // 使用 Nordic UART Service UUID (NUS)，这是一个更常见的 UUID
    std::cout << "创建 Nordic UART Service (NUS)..." << std::endl;
    auto srv2 = std::make_shared<GattService1>( app, "serial", "6E400001-B5A3-F393-E0A9-E50E24DCCA9E" );
    std::cout << "NUS 服务已创建，UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E" << std::endl;

    // 使用 NUS RX 特性 UUID
    std::cout << "创建 NUS RX 特性..." << std::endl;
    SerialCharacteristic::create( srv2, connection, "6E400002-B5A3-F393-E0A9-E50E24DCCA9E" )
        .finalize();
    std::cout << "NUS RX 特性已创建，UUID: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E" << std::endl;

    std::cout << "准备注册 GATT 应用程序..." << std::endl;

    auto register_app_callback = [](const sdbus::Error* error)
    {
        if( error == nullptr )
        {
            std::cout << "GATT 应用程序注册成功！" << std::endl;
            std::cout << "现在您应该能够在 LightBlue 应用中看到设备 'RK3588_BLE'" << std::endl;
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

    // ---- Advertising ------------------------------------------------------------------------------------------------

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
            std::cout << "Advertisement registered." << std::endl;
        }
        else
        {
            std::cerr << "Error registering advertisment " << error->getName() << " with message " << error->getMessage() << std::endl;
        }
    };

    std::cout << "创建广告..." << std::endl;

    // 使用 NUS UUID 进行广告
    std::cout << "广告 UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E" << std::endl;

    // 创建广告选项
    std::map<std::string, sdbus::Variant> advOptions;

    // 设置广告间隔（单位：毫秒）
    // 较小的值会增加发现的可能性，但会消耗更多电量
    // 默认值通常是 1000-1500 毫秒
    advOptions["MinInterval"] = sdbus::Variant(uint16_t(100)); // 100 毫秒
    advOptions["MaxInterval"] = sdbus::Variant(uint16_t(200)); // 200 毫秒

    std::cout << "广告间隔: 100-200 毫秒" << std::endl;

    // 设置广告类型为 "peripheral"
    advOptions["Type"] = sdbus::Variant(std::string("peripheral"));

    std::cout << "广告类型: peripheral" << std::endl;

    auto ad = LEAdvertisement1::create( *connection, ADV_PATH )
        .withLocalName( NAME )
        .withServiceUUIDs( std::vector{ std::string{"6E400001-B5A3-F393-E0A9-E50E24DCCA9E"} } )
        .withIncludes( std::vector{ std::string{ "tx-power" }, std::string{ "appearance" } } )
        .onReleaseCall( [](){ std::cout << "广告已释放" << std::endl; } )
        .registerWith( mgr, register_adv_callback, advOptions );

    std::cout << "广告已注册" << std::endl;

    std::cout << "Loading complete." << std::endl;

    connection->enterProcessingLoopAsync();

    bool run = true;
    while( run) {
        char cmd;
        std::cout << "commands:" << std::endl;
        std::cout << "  q      quit" << std::endl;
        std::cout << "$> ";
        std::cin >> cmd;

        switch(cmd)
        {
            case 'q':
                run = false;
        }
    }
}
