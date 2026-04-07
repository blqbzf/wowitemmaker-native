# 诺兰时光物品工具（桌面版）

真正的跨平台桌面应用，不是命令行+浏览器。

## 功能特性

✅ **真正的桌面应用**
- 内嵌浏览器引擎
- 原生窗口和菜单
- 不需要命令行
- 不需要手动打开浏览器

✅ **完整功能**
- 读取/编辑/删除物品
- 复制/套用物品模板
- 生成 Item.dbc 补丁
- 打包 MPQ 补丁
- 推送补丁到服务器
- 自动识别测试服/正式服环境

✅ **跨平台**
- macOS（ARM64）
- Windows（x64）

## macOS 使用方法

### 方式1：直接运行
双击 `WOWItemMaker` 可执行文件

### 方式2：DMG 安装（推荐）
1. 双击 `WOWItemMaker-macos.dmg`
2. 拖动应用到 Applications 文件夹
3. 双击运行

## Windows 使用方法

1. 解压 `WOWItemMaker-windows.zip`
2. 双击 `WOWItemMaker.exe`

## 功能说明

### 数据库选择
- **acore_world_test（测试服）**
  - 推送目标：/patches/test/
  - 登录器拉取：combined-test-manifest.json

- **acore_world（正式服）**
  - 推送目标：/patches/release/
  - 登录器拉取：combined-release-manifest.json

### 主要功能

#### 1. 物品管理
- 读取物品：输入 entry 点击"读取物品"
- 编辑物品：修改字段后点击"保存 item"
- 删除物品：点击"删除物品"

#### 2. 物品复制
- 点击"套用物品"
- 输入源 entry 和新物品名
- 点击"复制"

#### 3. 补丁生成
- 点击"问号补丁"生成 Item.dbc
- 自动打包成 MPQ

#### 4. 补丁推送
- 选择数据库后点击"推送补丁"
- 自动推送到对应环境

## 菜单功能

### 文件
- **在浏览器中打开**（Ctrl+B）：在默认浏览器中打开界面
- **退出**（Ctrl+Q）：退出程序

### 帮助
- **关于**：显示程序信息

## 系统要求

### macOS
- macOS 10.14 或更高版本
- ARM64（M1/M2）或 x64

### Windows
- Windows 10 或更高版本
- x64

## 技术栈

- Python 3.10
- PyQt5（桌面框架）
- QtWebEngine（内嵌浏览器）
- PyInstaller（打包）

## 开发者说明

### 本地开发
```bash
# 安装依赖
pip install PyQt5 PyQtWebEngine pymysql

# 运行桌面应用
python desktop_app.py

# 打包 macOS
pyinstaller desktop.spec

# 打包 Windows
pyinstaller desktop.spec
```

### GitHub 自动构建
- Push 到 main/master 分支
- GitHub Actions 自动构建
- 自动发布到 Releases

## 许可证

© 2026 诺兰时光魔兽
