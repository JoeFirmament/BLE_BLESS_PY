CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -g
LDFLAGS = -lsdbus-c++ -pthread

# 定义目标和源文件
TARGETS = ble_basic_api_new ble_convenience_api
BASIC_SRC_NEW = ble_basic_api_new.cpp
CONVENIENCE_SRC = ble_convenience_api.cpp

# 默认目标
all: $(TARGETS)

# 编译新的基本 API 版本
ble_basic_api_new: $(BASIC_SRC_NEW)
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

# 编译便捷 API 版本
ble_convenience_api: $(CONVENIENCE_SRC)
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

# 安装 D-Bus 配置文件（不推荐，可能导致 SSH 连接中断）
install-conf:
	sudo cp org.example.ble_uart.conf /etc/dbus-1/system.d/

# 安装用户级别的 systemd 服务
install-service:
	mkdir -p ~/.config/systemd/user/
	cp ble-uart.service ~/.config/systemd/user/
	systemctl --user daemon-reload
	@echo "服务已安装。使用以下命令启动服务："
	@echo "systemctl --user start ble-uart.service"
	@echo "使用以下命令设置开机自启动："
	@echo "systemctl --user enable ble-uart.service"

# 清理目标
clean:
	rm -f $(TARGETS)

.PHONY: all install-conf clean
