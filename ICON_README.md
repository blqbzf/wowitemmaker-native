# 图标文件说明

桌面应用需要图标文件：

## macOS
- 文件名：icon.png
- 尺寸：512x512 或 1024x1024
- 格式：PNG（透明背景）

## Windows
- 文件名：icon.ico
- 尺寸：256x256 或包含多种尺寸
- 格式：ICO

## 当前状态
图标文件未提供，应用将使用默认图标。

## 如何添加图标
1. 准备 512x512 PNG 文件
2. 命名为 icon.png
3. 放在 desktop.spec 同级目录
4. 重新打包：pyinstaller desktop.spec

## Windows ICO 转换
```bash
# 使用 ImageMagick
convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```
