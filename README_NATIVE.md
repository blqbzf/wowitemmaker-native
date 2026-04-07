# 诺兰时光物品工具 v2.0 - 原生桌面版

## ✅ 这是真正的原生桌面应用！

- ❌ 不使用浏览器
- ❌ 不使用WebEngine
- ✅ 纯PyQt5原生控件
- ✅ 独立窗口应用
- ✅ 跨平台支持

---

## 功能特性

### 原生UI控件
- QLineEdit - 文本输入框
- QComboBox - 下拉选择框
- QPushButton - 按钮
- QTabWidget - 选项卡
- QGroupBox - 分组框
- QScrollArea - 滚动区域

### 完整功能
✅ 读取/编辑/删除物品
✅ 自动填充字段
✅ 中文/英文名称支持
✅ SQL语句生成
✅ SQL复制到剪贴板
✅ 数据库连接测试
✅ 测试服/正式服切换
✅ 环境状态显示

---

## macOS 使用方法

### 方式1：双击运行（推荐）
```bash
cd dist/
./WOWItemMaker
```

### 方式2：使用启动脚本
```bash
双击 "启动原生版.command"
```

---

## Windows 版本

### 自动构建（推荐）
1. 推送代码到GitHub
2. GitHub Actions自动构建
3. 下载Windows版本

### 手动构建
```bash
pip install PyQt5 pymysql pyinstaller
pyinstaller native.spec
```

---

## 界面布局

### 顶部
- 数据库选择（测试服/正式服）
- 连接状态显示
- 测试连接按钮

### 左侧：基本字段
- 物品Entry输入
- 基本信息组（名称、描述、显示ID等）
- 分类和属性组（类型、品质、装备槽等）

### 右侧：详细字段（选项卡）
- **属性选项卡**：力量、敏捷、耐力、抗性等
- **法术选项卡**：法术ID、触发类型等
- **要求选项卡**：技能、阵营、声望等
- **SQL和补丁选项卡**：SQL预览、生成、复制、补丁操作

### 底部
- 套用物品
- 搜索物品
- 环境信息提示

---

## 数据库配置

### 测试服
- 数据库：`acore_world_test`
- 推送目标：`/patches/test/`
- 登录器：`combined-test-manifest.json`

### 正式服
- 数据库：`acore_world`
- 推送目标：`/patches/release/`
- 登录器：`combined-release-manifest.json`

---

## 技术栈

### 核心
- Python 3.10+
- PyQt5（桌面框架）
- PyMySQL（数据库）

### 打包
- PyInstaller
- macOS: Mach-O arm64
- Windows: PE x64

---

## 开发者说明

### 本地开发
```bash
# 安装依赖
pip install PyQt5 pymysql

# 运行原生应用
python native_app.py

# 打包macOS
pyinstaller native.spec
```

### 项目结构
```
wowitemmaker-macos-prototype/
├── native_app.py          # 原生桌面应用主文件
├── native.spec            # PyInstaller配置
├── server.py              # 后端服务器
├── minimal-app.html       # 网页版界面（备用）
├── wowitemmaker-data-dicts.json  # 数据字典
└── dist/
    └── WOWItemMaker       # 打包后的可执行文件
```

---

## 对比

| 特性 | 网页版 | 原生版 |
|------|--------|--------|
| 界面 | 浏览器 | 原生窗口 |
| 控件 | HTML | PyQt5 |
| 性能 | 一般 | 快 |
| 体积 | 大（含WebEngine） | 小（26MB） |
| 风格 | Web | 桌面应用 |

---

## 许可证

© 2026 诺兰时光魔兽

---

## 常见问题

### Q: 为什么选择PyQt5而不是C#？
A: PyQt5跨平台，代码复用度高，开发速度快。

### Q: 原生版和网页版有什么区别？
A: 原生版使用纯桌面控件，不依赖浏览器，更像旧WOWItemMaker。

### Q: Windows版本什么时候有？
A: 推送到GitHub后，Actions会自动构建，约10分钟。
