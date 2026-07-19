# 📅 Days-Matter - 桌面倒数日工具

一个跨平台的桌面倒数日应用，支持 Windows 和麒麟系统（Kylin OS），提供高度客制化的桌面悬浮组件。

## 特性

- 🖥️ **桌面悬浮组件** - 透明、无边框、可拖动、可缩放的倒计时窗口
- 🎨 **高度客制化** - 字体、字号、颜色、背景、阴影等所有视觉元素可自定义
- 📋 **多事件管理** - 支持添加多个倒数日（或正计时）事件
- 🔄 **双模式** - 支持倒计时和目标日期后的正计时
- 🚀 **开机自启** - 通过系统 autostart 机制实现（Linux）
- 📌 **系统托盘** - 系统托盘常驻，不占用任务栏空间
- 🖱️ **便捷交互** - 拖动调整位置、滚轮调整大小、右键菜单快速操作
- 🪟 **Windows 支持** - 兼容 Windows 10/11 桌面环境
- 🐲 **麒麟系统优化** - 适配 UKUI 桌面环境，兼容飞腾/鲲鹏/龙芯

## 系统要求

- **Windows**: Windows 10/11，Python 3.6+，PyQt5
- **麒麟系统**: Kylin OS 或任何基于 Linux 的系统，Python 3.6+，PyQt5
- **通用**: 支持 Python 3.6+ 和 PyQt5 的操作系统

## 快速安装

### Windows 安装

```bash
# 1. 进入项目目录
cd Days-Matter

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

### 麒麟系统安装

```bash
# 1. 解压或进入项目目录
cd Days-Matter

# 2. 运行安装脚本
bash install_kylin.sh

# 3. 从开始菜单启动「倒数日」
```

### 手动安装（Linux）

```bash
# 1. 安装依赖
sudo apt install python3-pyqt5
pip3 install -r requirements.txt --user

# 2. 运行
python3 main.py
```

## 使用说明

### 添加事件
1. 右键系统托盘图标 → 「打开管理界面」
2. 点击右上角「+ 添加倒数日」按钮
3. 填写标题、目标日期、选择模式
4. 自定义显示样式：字体、颜色、背景、阴影等
5. 点击「保存」

### 桌面悬浮窗操作
- **拖动**：左键按住拖动组件到任意位置
- **缩放**：鼠标悬停右下角拖动，或使用鼠标滚轮
- **右键菜单**：编辑事件、锁定位置、切换置顶、删除

### 样式自定义
每个倒数日组件支持独立配置：
- 字体族和字号（标题/天数/时间分别设置）
- 各元素颜色（标题/天数/时间/背景）
- 背景透明度和圆角半径
- 阴影效果（开关/颜色/偏移）
- 窗口置顶和位置锁定

## 项目结构

```
Days-Matter/
├── main.py              # 应用主入口
├── requirements.txt     # Python 依赖
├── install_kylin.sh     # 麒麟系统安装脚本
├── uninstall_kylin.sh   # 麒麟系统卸载脚本
├── README.md
├── core/                # 核心引擎
│   ├── countdown_engine.py  # 倒计时计算
│   └── storage.py           # 数据持久化
├── ui/                  # 用户界面
│   ├── desktop_widget.py    # 桌面悬浮组件
│   ├── event_dialog.py      # 事件编辑对话框
│   ├── main_window.py       # 主管理窗口
│   └── system_tray.py       # 系统托盘
├── integration/         # 系统集成
│   └── desktop_entry.py     # .desktop 文件管理
└── resources/           # 资源文件
```

## 卸载

### 麒麟系统
```bash
bash /opt/days-matter/uninstall_kylin.sh
```

### Windows
直接删除项目目录即可。用户数据存储在 `~/.days_matter/`，如需完全清除请手动删除。

## 技术细节

- **开发语言**：Python 3
- **GUI 框架**：PyQt5（跨平台，兼容 Windows 和 UKUI 桌面环境）
- **数据存储**：JSON 文件（`~/.days_matter/config.json`）
- **系统集成**：Linux Freedesktop 标准（.desktop 文件）

## License

MIT License