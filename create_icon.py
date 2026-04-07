#!/usr/bin/env python3
"""
创建应用图标
"""
from PIL import Image, ImageDraw, ImageFont
import sys

def create_icon(size=512):
    """创建图标"""
    # 创建图像
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 背景渐变效果（简化版）
    for i in range(size):
        alpha = int(255 * (1 - i / size * 0.3))
        draw.rectangle([0, i, size, i+1], fill=(70, 130, 180, alpha))  # 钢蓝色
    
    # 中心圆圈
    margin = size // 6
    draw.ellipse([margin, margin, size-margin, size-margin], 
                 fill=(255, 215, 0, 255),  # 金色
                 outline=(139, 69, 19, 255),  # 深棕色边框
                 width=size//30)
    
    # W字母（WoW的W）
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size//2)
    except:
        font = ImageFont.load_default()
    
    text = "W"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - size//20
    
    draw.text((x, y), text, fill=(0, 0, 0, 255), font=font)
    
    return img

def main():
    # 创建不同尺寸的图标
    sizes = [512, 256, 128, 64, 32, 16]
    
    # 创建主图标
    icon_512 = create_icon(512)
    icon_512.save('icon.png', 'PNG')
    print("✅ 已创建 icon.png (512x512)")
    
    # 创建 ICO 文件（Windows）
    try:
        icons = []
        for size in sizes:
            icons.append(create_icon(size))
        
        # 保存为 ICO
        icon_512.save('icon.ico', format='ICO', sizes=[(s, s) for s in sizes])
        print("✅ 已创建 icon.ico (多尺寸)")
    except Exception as e:
        print(f"⚠️  创建 ICO 失败: {e}")
        print("   Windows 用户可以从 PNG 转换")

if __name__ == "__main__":
    main()
