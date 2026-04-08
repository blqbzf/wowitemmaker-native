#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诺兰时光物品工具 v3.1 - 完整修复版
- 字体增大到12
- 所有下拉菜单完整
- 无乱码
"""

import sys
import json
from pathlib import Path
import subprocess
import hashlib
import time
import urllib.request
import urllib.parse
import re
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QGroupBox,
    QGridLayout, QMessageBox, QSplitter, QFrame, QScrollArea, QTabWidget,
    QDialog, QFormLayout, QListWidget, QListWidgetItem, QCheckBox, QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QFileDialog, QMenu, QDialogButtonBox
)
from PyQt5.QtGui import QFont, QIcon
import pymysql

CONFIG_FILE = Path(__file__).parent / 'conninfo.json'
CHINESE_FONT = QFont("PingFang SC", 12)  # 字体增大到12
UI_FONT = QFont("SF Pro Display", 12)

# 获取数据目录的绝对路径
def get_data_dir():
    """获取数据目录的绝对路径"""
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的路径
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境
        base_path = Path(__file__).parent
    return base_path / 'data'

DATA_DIR = get_data_dir()

# 下拉菜单选项定义（根据旧WOWItemMaker真实数据完整版）
COMBO_OPTIONS = {
    'Quality': ["0-灰色", "1-白色", "2-绿色", "3-蓝色", "4-紫色", "5-橙色", "6-红色"],
    'class': ["0-消耗品", "1-容器", "2-武器", "3-宝石", "4-护甲", "5-材料", "6-弹药", "7-商品", "8-配方", "9-钱币", "10-任务物品", "11-钥匙", "12-永久", "13-垃圾"],
    'subclass': ["0-无", "1-斧", "2-弓", "3-枪", "4-锤", "5-长柄", "6-剑", "7-法杖", "8-匕首", "9-拳套", "10-盾牌", "11-魔杖", "12-弩", "13-投掷", "14-鱼竿"],
    'bonding': ["0-不绑定", "1-拾取绑定", "2-装备绑定", "3-使用绑定", "4-任务物品", "5-账号绑定"],
    'InventoryType': ["0-无", "1-头", "2-脖子", "3-肩膀", "4-衬衣", "5-胸", "6-腰带", "7-腿", "8-脚", "9-手腕", "10-手套", "11-手指", "12-饰品", "13-单手", "14-盾牌", "15-弓", "16-披风", "17-双手", "18-包", "19-战袍", "20-法衣", "21-主手", "22-副手", "23-箭", "24-子弹"],
    'Material': ["-1-消费品", "1-金属", "2-木制品", "3-液体", "4-珠宝", "5-锁甲", "6-板甲", "7-布甲", "8-皮革"],
    'sheath': ["0-无", "1-大型盾牌", "2-背包", "3-法杖", "4-盾牌", "5-副手", "6-大型武器", "7-中型武器", "8-小型武器", "9-弩", "10-魔杖", "11-弓"],
    'stat_type': ["0-无", "1-力量", "2-敏捷", "3-耐力", "4-智力", "5-精神", "6-攻击强度", "7-法术强度", "18-护甲穿透", "19-格挡等级", "20-精准等级", "21-躲闪等级", "22-招架等级", "23-五秒回蓝", "24-法术穿透"],
    'dmg_type': ["0-物理", "1-神圣", "2-火焰", "3-自然", "4-冰霜", "5-暗影", "6-奥术"],
    'spelltrigger': ["0-使用", "1-装备", "2-被动", "3-击中", "4-使用无消耗", "5-使用失败"],
    'socketColor': ["0-无", "1-红", "2-黄", "4-蓝", "8-多彩", "14-棱彩"],
    'BagFamily': ["0-无", "1-箭袋", "2-弹药袋", "3-灵魂碎片袋", "4-皮革包", "5-草药包", "6-附魔包", "7-工程包", "8-钥匙包", "9-宝石包", "10-矿石包", "11-暗月卡片", "12-垃圾包"],
    'ammo_type': ["0-无", "2-弓箭", "3-子弹"],
    'RandomSuffix': ["0-无", "5-灵猴之", "6-雄鹰之", "7-野熊之", "8-巨鲸之", "9-夜枭之", "10-巨猿之", "11-猎鹰之", "12-野猪之", "13-孤狼之", "14-猛虎之", "15-精神之", "16-耐力之", "17-力量之", "18-敏捷之", "19-智力之", "20-能量之", "21-法术能量之", "22-火焰法术之", "23-冰霜法术之", "24-自然法术之", "25-暗影法术之", "26-神圣法术之", "27-防御之", "28-再生之", "29-闪避之", "30-专注之", "31-秘法防护之", "32-火焰防护之", "33-冰霜防护之", "34-自然防护之", "35-暗影防护之", "36-术士之", "37-医师之", "38-预言者之", "39-塑能师之", "40-强盗之", "41-野兽之", "42-祭司之", "43-士兵之", "44-长者之", "45-勇士之", "93-恢复之"],
    'AllowableClass': ["-1-全职业", "1-战士", "2-圣骑士", "4-猎人", "8-盗贼", "16-牧师", "32-死亡骑士", "64-萨满", "128-法师", "256-术士", "512-德鲁伊", "1489-全职业"],
}

# 动态加载的下拉菜单数据
def load_json_data(filename):
    """安全加载JSON数据文件"""
    filepath = DATA_DIR / filename
    try:
        if not filepath.exists():
            print(f"警告: 数据文件不存在: {filepath}")
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: JSON格式错误 {filename}: {e}")
        return None
    except Exception as e:
        print(f"错误: 加载 {filename} 失败: {e}")
        return None



def load_txt_options(filename):
    """从旧WOWItemMaker Data/*.txt加载下拉选项，只增加真实词典，不删除现有默认项。"""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return []
    for enc in ('utf-8-sig', 'gbk', 'utf-8'):
        try:
            lines = filepath.read_text(encoding=enc).splitlines()
            break
        except Exception:
            lines = []
    options = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ',' in line:
            k, v = line.split(',', 1)
            options.append(f"{k.strip()}-{v.strip()}")
        elif ';' in line:
            k, v = line.split(';', 1)
            options.append(f"{k.strip()}-{v.strip()}")
        else:
            options.append(line)
    return options

def add_txt_combo(key, filename):
    opts = load_txt_options(filename)
    if opts:
        COMBO_OPTIONS[key] = opts


def format_bilingual(zh_value, en_value=''):
    zh_value = (str(zh_value or '')).strip()
    en_value = (str(en_value or '')).strip()
    if zh_value and en_value and zh_value != en_value:
        return f"{zh_value} ({en_value})"
    return zh_value or en_value


def normalize_option_label(option_text):
    text = str(option_text or '').strip()
    if not text:
        return text
    if '-' not in text:
        return text
    key, value = text.split('-', 1)
    value = value.strip()
    return f"{key}-{value}"


def refresh_combo_options(widget, options):
    if not isinstance(widget, QComboBox):
        return
    current = widget.currentText()
    current_id = current.split('-', 1)[0] if current else ''
    widget.blockSignals(True)
    widget.clear()
    widget.addItems(options)
    if current_id:
        for idx in range(widget.count()):
            if widget.itemText(idx).startswith(current_id + '-') or widget.itemText(idx) == current_id:
                widget.setCurrentIndex(idx)
                break
    widget.blockSignals(False)

# 旧WOWItemMaker 1.73真实Data词典：只增加/覆盖为更完整数据，不删除字段
for _key, _file in {
    'Quality': 'Quality.txt',
    'class': 'class.txt',
    'bonding': 'bonding.txt',
    'InventoryType': 'InventoryType.txt',
    'Material': 'Material.txt',
    'sheath': 'sheath.txt',
    'dmg_type': 'dmg_type.txt',
    'spelltrigger': 'spelltrigger.txt',
    'socketColor': 'socketColor.txt',
    'socketBonus': 'socketBonus.txt',
    'AllowableClass': 'AllowableClass.txt',
    'AllowableRace': 'AllowableRace.txt',
    'ammo_type': 'ammo_type.txt',
    'Flags': 'Flags.txt',
    'area': 'area.txt',
    'Map': 'map.txt',
    'displayid': 'displayid.txt',
    'RandomProperty': 'RandomProperty.txt',
    'RandomSuffix': 'RandomSuffix.txt',
    'spellid': 'spellid.txt',
}.items():
    add_txt_combo(_key, _file)

for i in range(0, 17):
    add_txt_combo(f'subclass{i}', f'subclass{i}.txt')
for i in range(1, 11):
    COMBO_OPTIONS[f'stat_type{i}'] = load_txt_options('stat_type.txt') or COMBO_OPTIONS.get(f'stat_type{i}', COMBO_OPTIONS.get('stat_type', []))
for i in range(1, 6):
    COMBO_OPTIONS[f'dmg_type{i}'] = COMBO_OPTIONS.get('dmg_type', [])
    COMBO_OPTIONS[f'spellid_{i}'] = COMBO_OPTIONS.get('spellid', COMBO_OPTIONS.get(f'spellid_{i}', []))
    COMBO_OPTIONS[f'spelltrigger_{i}'] = COMBO_OPTIONS.get('spelltrigger', COMBO_OPTIONS.get(f'spelltrigger_{i}', []))
for i in range(1, 4):
    COMBO_OPTIONS[f'socketColor_{i}'] = COMBO_OPTIONS.get('socketColor', [])
COMBO_OPTIONS['RequiredReputationRank'] = ['0-仇恨', '1-敌对', '2-冷漠', '3-中立', '4-友善', '5-尊敬', '6-崇敬', '7-崇拜']
COMBO_OPTIONS['SpellsCount'] = [str(i) for i in range(0, 6)]
COMBO_OPTIONS['DbStruct'] = ['3.0.X', '3.1.X', '3.2.X', '3.3.X', '3.3.5', '3.3.5(TC2)']
COMBO_OPTIONS['StatsCount'] = [str(i) for i in range(0, 11)]
COMBO_OPTIONS['RequiredSkill'] = ['0-无', '762-骑术', '171-炼金', '164-锻造', '333-附魔', '202-工程', '182-草药', '773-铭文', '755-珠宝加工', '165-制皮', '186-采矿', '393-剥皮', '197-裁缝', '129-急救', '185-烹饪', '356-钓鱼']
COMBO_OPTIONS['FoodType'] = ['0-无', '1-肉', '2-鱼', '3-奶酪', '4-面包', '5-真菌', '6-水果', '7-生肉', '8-生鱼']
COMBO_OPTIONS['TotemCategory'] = ['0-无']
COMBO_OPTIONS['ItemLimitCategory'] = ['0-无']
COMBO_OPTIONS['GemProperties'] = ['0-无']
COMBO_OPTIONS['DisenchantID'] = ['0-无']
COMBO_OPTIONS['RequiredDisenchantSkill'] = ['0-无']
COMBO_OPTIONS['RequiredSpell'] = ['0-无']
COMBO_OPTIONS['RequiredReputationFaction'] = ['0-无']

# 加载stat_type数据
stat_data = load_json_data('stat_types.json')
if stat_data:
    stat_options = [f"{item['id']}-{item['name']}" for item in stat_data] if isinstance(stat_data, list) else [f"{k}-{v.get('name', '未知')}" for k, v in stat_data.items()]
    for i in range(1, 11):
        COMBO_OPTIONS[f'stat_type{i}'] = stat_options
else:
    # 使用默认的stat_type选项
    for i in range(1, 11):
        COMBO_OPTIONS[f'stat_type{i}'] = COMBO_OPTIONS['stat_type']

# 加载displayid数据
display_data = load_json_data('display_ids.json')
if display_data:
    display_options = [f"{item['id']}-{item['name']}" for item in display_data] if isinstance(display_data, list) else [f"{k}-{v.get('name', '未知')}" for k, v in display_data.items()]
    COMBO_OPTIONS['displayid'] = display_options

# 加载RandomSuffix数据
suffix_data = load_json_data('random_suffixes.json')
if suffix_data:
    suffix_options = [f"{item['id']}-{item['name']}" for item in suffix_data] if isinstance(suffix_data, list) else [f"{k}-{v.get('name', '未知')}" for k, v in suffix_data.items()]
    COMBO_OPTIONS['RandomSuffix'] = suffix_options

# 加载RandomProperty数据
prop_data = load_json_data('random_properties.json')
if prop_data:
    if isinstance(prop_data, list):
        prop_options = [f"{item.get('id', '')}-{item.get('name', '未知')}" for item in prop_data]
    else:
        prop_options = [f"{k}-{v.get('name', '未知')}" for k, v in list(prop_data.items())]
    COMBO_OPTIONS['RandomProperty'] = prop_options

# 加载spellid数据
spell_data = load_json_data('spell_effects.json')
if spell_data:
    if isinstance(spell_data, list):
        spell_options = [f"{item.get('id', '')}-{item.get('name', item.get('desc', '未知'))}" for item in spell_data]
    else:
        spell_options = [f"{k}-{v.get('name', '未知')}" for k, v in list(spell_data.items())]
    for i in range(1, 6):
        COMBO_OPTIONS[f'spellid_{i}'] = spell_options

# 为spelltrigger字段补齐分组字段选项
for i in range(1, 6):
    COMBO_OPTIONS[f'spelltrigger_{i}'] = COMBO_OPTIONS['spelltrigger']


FLAG_OPTIONS = [
    (0, '无'),
    (2, '魔法制造'),
    (4, '字箱'),
    (32, '徽章/图腾'),
    (64, '设计图/马等'),
    (256, '魔杖'),
    (512, '包装盒'),
    (8192, '公会登记表'),
    (134217728, '账号绑定'),
]
FLAG_EXTRA_OPTIONS = [
    (0, '无'),
    (1, '部落'),
    (2, '联盟'),
    (4, '扩展预留'),
]


# 完整字段映射
ALL_FIELDS = [
    # 基础信息
    ("entry", "物品ID Entry", "基础 Basic", "text"),
    ("DbStruct", "结构版本 DbStruct", "基础 Basic", "combo"),
    ("name", "名称 Name", "基础 Basic", "text"),
    ("Name_zhCN", "中文名称 Name zhCN", "基础 Basic", "text"),
    ("displayid", "显示ID DisplayID", "基础 Basic", "text"),
    ("Quality", "品质 Quality", "基础 Basic", "combo"),
    ("class", "类型 Class", "基础 Basic", "combo"),
    ("subclass", "子类型 Subclass", "基础 Basic", "combo"),
    ("SoundOverrideSubclass", "声音子类 Sound", "基础 Basic", "text"),
    ("Flags", "标志 Flags", "基础 Basic", "combo"),
    ("FlagsExtra", "额外标志 Extra", "基础 Basic", "text"),
    ("BuyCount", "购买数量 BuyCnt", "基础 Basic", "text"),
    ("BuyPrice", "购买价格 BuyPrice", "基础 Basic", "text"),
    ("SellPrice", "出售价格 SellPrice", "基础 Basic", "text"),
    ("InventoryType", "装备槽 InvType", "基础 Basic", "combo"),
    ("ItemLevel", "物品等级 ItemLvl", "基础 Basic", "text"),
    ("bonding", "绑定类型 Bonding", "基础 Basic", "combo"),
    ("stackable", "堆叠 Stack", "基础 Basic", "text"),
    ("maxcount", "最大数量 MaxCnt", "基础 Basic", "text"),
    ("ContainerSlots", "容器槽 Container", "基础 Basic", "text"),
    ("Material", "材质 Material", "基础 Basic", "combo"),
    ("sheath", "鞘 Sheath", "基础 Basic", "combo"),
    ("description", "描述 Desc", "基础 Basic", "textarea"),
    ("Description_zhCN", "中文描述 Desc zhCN", "基础 Basic", "textarea"),
    
    # 需求
    ("RequiredLevel", "需要等级 ReqLvl", "需求 Requirements", "text"),
    ("AllowableClass", "允许职业 AllowClass", "需求 Requirements", "combo"),
    ("AllowableRace", "允许种族 AllowRace", "需求 Requirements", "combo"),
    ("RequiredSkill", "需要技能 ReqSkill", "需求 Requirements", "combo"),
    ("RequiredSkillRank", "技能等级 SkillRank", "需求 Requirements", "text"),
    ("requiredspell", "需要法术 ReqSpell", "需求 Requirements", "text"),
    ("requiredhonorrank", "需要荣誉 ReqHonor", "需求 Requirements", "text"),
    ("RequiredCityRank", "城市等级 CityRank", "需求 Requirements", "text"),
    ("RequiredReputationFaction", "声望阵营 RepFac", "需求 Requirements", "combo"),
    ("RequiredReputationRank", "声望等级 RepRank", "需求 Requirements", "combo"),
    ("area", "区域 Area", "需求 Requirements", "combo"),
    ("Map", "地图 Map", "需求 Requirements", "combo"),
    
    # 属性
    ("StatsCount", "绿字数量 StatsCount", "属性 Stats", "combo"),
    ("stat_type1", "属性1类型 Stat1Type", "属性 Stats", "combo"),
    ("stat_value1", "属性1值 Stat1Val", "属性 Stats", "text"),
    ("stat_type2", "属性2类型 Stat2Type", "属性 Stats", "combo"),
    ("stat_value2", "属性2值 Stat2Val", "属性 Stats", "text"),
    ("stat_type3", "属性3类型 Stat3Type", "属性 Stats", "combo"),
    ("stat_value3", "属性3值 Stat3Val", "属性 Stats", "text"),
    ("stat_type4", "属性4类型 Stat4Type", "属性 Stats", "combo"),
    ("stat_value4", "属性4值 Stat4Val", "属性 Stats", "text"),
    ("stat_type5", "属性5类型 Stat5Type", "属性 Stats", "combo"),
    ("stat_value5", "属性5值 Stat5Val", "属性 Stats", "text"),
    ("stat_type6", "属性6类型 Stat6Type", "属性 Stats", "combo"),
    ("stat_value6", "属性6值 Stat6Val", "属性 Stats", "text"),
    ("stat_type7", "属性7类型 Stat7Type", "属性 Stats", "combo"),
    ("stat_value7", "属性7值 Stat7Val", "属性 Stats", "text"),
    ("stat_type8", "属性8类型 Stat8Type", "属性 Stats", "combo"),
    ("stat_value8", "属性8值 Stat8Val", "属性 Stats", "text"),
    ("stat_type9", "属性9类型 Stat9Type", "属性 Stats", "combo"),
    ("stat_value9", "属性9值 Stat9Val", "属性 Stats", "text"),
    ("stat_type10", "属性10类型 Stat10Type", "属性 Stats", "combo"),
    ("stat_value10", "属性10值 Stat10Val", "属性 Stats", "text"),
    ("ScalingStatDistribution", "缩放分布 Scaling", "属性 Stats", "text"),
    ("ScalingStatValue", "缩放值 ScaleVal", "属性 Stats", "text"),
    
    # 伤害
    ("dmg_min1", "伤害1最小 Dmg1Min", "伤害 Damage", "text"),
    ("dmg_max1", "伤害1最大 Dmg1Max", "伤害 Damage", "text"),
    ("dmg_type1", "伤害1类型 Dmg1Type", "伤害 Damage", "combo"),
    ("dmg_min2", "伤害2最小 Dmg2Min", "伤害 Damage", "text"),
    ("dmg_max2", "伤害2最大 Dmg2Max", "伤害 Damage", "text"),
    ("dmg_type2", "伤害2类型 Dmg2Type", "伤害 Damage", "combo"),
    ("dmg_min3", "伤害3最小 Dmg3Min", "伤害 Damage", "text"),
    ("dmg_max3", "伤害3最大 Dmg3Max", "伤害 Damage", "text"),
    ("dmg_type3", "伤害3类型 Dmg3Type", "伤害 Damage", "combo"),
    ("dmg_min4", "伤害4最小 Dmg4Min", "伤害 Damage", "text"),
    ("dmg_max4", "伤害4最大 Dmg4Max", "伤害 Damage", "text"),
    ("dmg_type4", "伤害4类型 Dmg4Type", "伤害 Damage", "combo"),
    ("dmg_min5", "伤害5最小 Dmg5Min", "伤害 Damage", "text"),
    ("dmg_max5", "伤害5最大 Dmg5Max", "伤害 Damage", "text"),
    ("dmg_type5", "伤害5类型 Dmg5Type", "伤害 Damage", "combo"),
    ("armor", "护甲 Armor", "伤害 Damage", "text"),
    ("holy_res", "神圣抗 HolyRes", "伤害 Damage", "text"),
    ("fire_res", "火焰抗 FireRes", "伤害 Damage", "text"),
    ("nature_res", "自然抗 NatureRes", "伤害 Damage", "text"),
    ("frost_res", "冰霜抗 FrostRes", "伤害 Damage", "text"),
    ("shadow_res", "暗影抗 ShadowRes", "伤害 Damage", "text"),
    ("arcane_res", "奥术抗 ArcaneRes", "伤害 Damage", "text"),
    ("delay", "延迟 Delay", "伤害 Damage", "text"),
    ("ammo_type", "弹药类型 Ammo", "伤害 Damage", "combo"),
    ("RangedModRange", "射程 Range", "伤害 Damage", "text"),
    ("block", "格挡 Block", "伤害 Damage", "text"),
    
    # 法术（简化为每个法术单独选项卡）
    ("SpellsCount", "法术数量 SpellsCount", "法术1 Spell1", "combo"),
    ("spellid_1", "法术1ID Spell1", "法术1 Spell1", "combo"),
    ("spelltrigger_1", "触发1 Trigger1", "法术1 Spell1", "combo"),
    ("spellcharges_1", "次数1 Charges1", "法术1 Spell1", "text"),
    ("spellppmRate_1", "PPM1 PPM1", "法术1 Spell1", "text"),
    ("spellcooldown_1", "冷却1 CD1", "法术1 Spell1", "text"),
    ("spellcategory_1", "类别1 Cat1", "法术1 Spell1", "text"),
    ("spellcategorycooldown_1", "类别冷却1 CatCD1", "法术1 Spell1", "text"),
    
    ("spellid_2", "法术2ID Spell2", "法术2 Spell2", "combo"),
    ("spelltrigger_2", "触发2 Trigger2", "法术2 Spell2", "combo"),
    ("spellcharges_2", "次数2 Charges2", "法术2 Spell2", "text"),
    ("spellppmRate_2", "PPM2 PPM2", "法术2 Spell2", "text"),
    ("spellcooldown_2", "冷却2 CD2", "法术2 Spell2", "text"),
    ("spellcategory_2", "类别2 Cat2", "法术2 Spell2", "text"),
    ("spellcategorycooldown_2", "类别冷却2 CatCD2", "法术2 Spell2", "text"),
    
    ("spellid_3", "法术3ID Spell3", "法术3 Spell3", "combo"),
    ("spelltrigger_3", "触发3 Trigger3", "法术3 Spell3", "combo"),
    ("spellcharges_3", "次数3 Charges3", "法术3 Spell3", "text"),
    ("spellppmRate_3", "PPM3 PPM3", "法术3 Spell3", "text"),
    ("spellcooldown_3", "冷却3 CD3", "法术3 Spell3", "text"),
    ("spellcategory_3", "类别3 Cat3", "法术3 Spell3", "text"),
    ("spellcategorycooldown_3", "类别冷却3 CatCD3", "法术3 Spell3", "text"),
    
    ("spellid_4", "法术4ID Spell4", "法术4 Spell4", "combo"),
    ("spelltrigger_4", "触发4 Trigger4", "法术4 Spell4", "combo"),
    ("spellcharges_4", "次数4 Charges4", "法术4 Spell4", "text"),
    ("spellppmRate_4", "PPM4 PPM4", "法术4 Spell4", "text"),
    ("spellcooldown_4", "冷却4 CD4", "法术4 Spell4", "text"),
    ("spellcategory_4", "类别4 Cat4", "法术4 Spell4", "text"),
    ("spellcategorycooldown_4", "类别冷却4 CatCD4", "法术4 Spell4", "text"),
    
    ("spellid_5", "法术5ID Spell5", "法术5 Spell5", "combo"),
    ("spelltrigger_5", "触发5 Trigger5", "法术5 Spell5", "combo"),
    ("spellcharges_5", "次数5 Charges5", "法术5 Spell5", "text"),
    ("spellppmRate_5", "PPM5 PPM5", "法术5 Spell5", "text"),
    ("spellcooldown_5", "冷却5 CD5", "法术5 Spell5", "text"),
    ("spellcategory_5", "类别5 Cat5", "法术5 Spell5", "text"),
    ("spellcategorycooldown_5", "类别冷却5 CatCD5", "法术5 Spell5", "text"),
    
    # Socket
    ("socketColor_1", "插槽1颜色 Socket1", "Socket", "combo"),
    ("socketContent_1", "插槽1内容 Content1", "Socket", "text"),
    ("socketColor_2", "插槽2颜色 Socket2", "Socket", "combo"),
    ("socketContent_2", "插槽2内容 Content2", "Socket", "text"),
    ("socketColor_3", "插槽3颜色 Socket3", "Socket", "combo"),
    ("socketContent_3", "插槽3内容 Content3", "Socket", "text"),
    ("socketBonus", "插槽奖励 Bonus", "Socket", "combo"),
    ("GemProperties", "宝石属性 GemProps", "Socket", "combo"),
    ("RandomProperty", "随机属性 RandomProp", "Socket", "combo"),
    ("RandomSuffix", "随机后缀 RandomSuffix", "Socket", "combo"),
    
    # 高级
    ("PageText", "页面文本 PageText", "高级 Advanced", "text"),
    ("LanguageID", "语言ID LangID", "高级 Advanced", "text"),
    ("PageMaterial", "页面材质 PageMat", "高级 Advanced", "text"),
    ("startquest", "起始任务 StartQuest", "高级 Advanced", "text"),
    ("lockid", "锁ID LockID", "高级 Advanced", "text"),
    ("itemset", "物品套装 ItemSet", "高级 Advanced", "text"),
    ("MaxDurability", "耐久度 Durability", "高级 Advanced", "text"),
    ("BagFamily", "背包类别 BagFamily", "高级 Advanced", "combo"),
    ("TotemCategory", "图腾类别 TotemCat", "高级 Advanced", "combo"),
    ("RequiredDisenchantSkill", "分解技能 Disenchant", "高级 Advanced", "combo"),
    ("ArmorDamageModifier", "护甲伤害修正 ArmorDmg", "高级 Advanced", "text"),
    ("duration", "持续时间 Duration", "高级 Advanced", "text"),
    ("ItemLimitCategory", "物品限制类别 ItemLimit", "高级 Advanced", "combo"),
    ("HolidayId", "节日ID HolidayID", "高级 Advanced", "text"),
    ("ScriptName", "脚本名 ScriptName", "高级 Advanced", "text"),
    ("DisenchantID", "分解ID DisenchantID", "高级 Advanced", "combo"),
    ("FoodType", "食物类型 FoodType", "高级 Advanced", "combo"),
    ("minMoneyLoot", "最小金币 MinMoney", "高级 Advanced", "text"),
    ("maxMoneyLoot", "最大金币 MaxMoney", "高级 Advanced", "text"),
    ("flagsCustom", "自定义标志 CustomFlags", "高级 Advanced", "text"),
    ("VerifiedBuild", "验证版本 VerifiedBuild", "高级 Advanced", "text"),
    ("AllowableClass", "允许职业 AllowClass", "高级 Advanced", "combo"),
    ("AllowableRace", "允许种族 AllowRace", "高级 Advanced", "combo"),
]


class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class FlagEditorDialog(QDialog):
    def __init__(self, title, options, current_value='0', parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(420, 520)
        self.setFont(CHINESE_FONT)
        self.options = options
        layout = QVBoxLayout(self)
        self.checks = []
        current_int = 0
        try:
            current_int = int(str(current_value or '0'))
        except Exception:
            current_int = 0
        for value, label in self.options:
            cb = QCheckBox(f'{value} - {label}')
            if value == 0:
                cb.setChecked(current_int == 0)
            elif current_int & value:
                cb.setChecked(True)
            layout.addWidget(cb)
            self.checks.append((value, cb))
        self.value_edit = QLineEdit(str(current_int))
        layout.addWidget(QLabel('结果数值:'))
        layout.addWidget(self.value_edit)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        for value, cb in self.checks:
            cb.stateChanged.connect(self.recompute)

    def recompute(self):
        total = 0
        for value, cb in self.checks:
            if value == 0:
                continue
            if cb.isChecked():
                total |= value
        if total == 0:
            for value, cb in self.checks:
                if value == 0:
                    cb.blockSignals(True)
                    cb.setChecked(True)
                    cb.blockSignals(False)
        else:
            for value, cb in self.checks:
                if value == 0:
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
        self.value_edit.setText(str(total))

    def get_value(self):
        return self.value_edit.text().strip()


class ConfigDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("连接配置 Connection Settings")
        self.setModal(True)
        self.resize(500, 350)
        self.setFont(CHINESE_FONT)
        self.config = config or {}
        
        layout = QVBoxLayout(self)
        
        # 数据库配置
        db_group = QGroupBox("数据库配置 Database")
        db_layout = QFormLayout(db_group)
        
        self.db_host = QLineEdit(self.config.get('db', {}).get('host', '43.248.129.172'))
        db_layout.addRow("主机 Host:", self.db_host)
        
        self.db_port = QLineEdit(str(self.config.get('db', {}).get('port', 3306)))
        db_layout.addRow("端口 Port:", self.db_port)
        
        self.db_user = QLineEdit(self.config.get('db', {}).get('user', 'wowitem'))
        db_layout.addRow("用户 User:", self.db_user)
        
        self.db_password = QLineEdit(self.config.get('db', {}).get('password', 'GknNJLRtcE6RzigVJFF8'))
        self.db_password.setEchoMode(QLineEdit.Password)
        db_layout.addRow("密码 Password:", self.db_password)
        
        self.db_name = NoWheelComboBox()
        self.db_name.addItems(["acore_world_test(测试服)", "acore_world(正式服)"])
        db_name = self.config.get('db', {}).get('database', 'acore_world_test')
        self.db_name.setCurrentIndex(0 if 'test' in db_name else 1)
        db_layout.addRow("数据库 Database:", self.db_name)
        
        layout.addWidget(db_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        test_btn = QPushButton("测试连接 Test")
        test_btn.clicked.connect(self.test_connection)
        btn_layout.addWidget(test_btn)
        
        ok_btn = QPushButton("确定 OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消 Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def test_connection(self):
        try:
            conn = pymysql.connect(
                host=self.db_host.text(),
                port=int(self.db_port.text()),
                user=self.db_user.text(),
                password=self.db_password.text(),
                database=self.db_name.currentText().split('(')[0],
                connect_timeout=5
            )
            conn.close()
            QMessageBox.information(self, "成功", "连接成功！Connection successful!")
        except Exception as e:
            QMessageBox.critical(self, "失败", f"连接失败：{e}")
    
    def get_config(self):
        return {
            'db': {
                'host': self.db_host.text(),
                'port': int(self.db_port.text()),
                'user': self.db_user.text(),
                'password': self.db_password.text(),
                'database': self.db_name.currentText().split('(')[0],
            },
            'savePassword': True,
        }


def sql_quote(value):
    if value is None:
        return 'NULL'
    s = str(value)
    if s == '':
        return "''"
    s = s.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{s}'"


SPELL_EXTRA_CACHE = Path(__file__).parent / 'data' / 'spellid_extra.json'


def load_spell_extra_cache():
    try:
        if SPELL_EXTRA_CACHE.exists():
            return json.load(open(SPELL_EXTRA_CACHE, 'r', encoding='utf-8'))
    except Exception:
        pass
    return {}


def save_spell_extra_cache(data):
    try:
        SPELL_EXTRA_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(SPELL_EXTRA_CACHE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_faction_options_from_db(db_config):
    try:
        conn = pymysql.connect(**db_config, connect_timeout=10)
        with conn.cursor() as cur:
            cur.execute("SELECT ID, COALESCE(Name_Lang_zhCN,''), COALESCE(Name_Lang_enUS,'') FROM faction_dbc ORDER BY ID ASC")
            rows = cur.fetchall()
        conn.close()
        return [f"{rid}-{format_bilingual(zh, en) or '未命名阵营'}" for rid, zh, en in rows]
    except Exception:
        return []


def load_required_spell_options_from_db(db_config):
    return load_spell_options_from_db(db_config)


def load_disenchant_options_from_db(db_config):
    return load_spell_options_from_db(db_config)


def fetch_spell_label_from_nfuwow(spell_id):
    try:
        url = f'https://db.nfuwow.com/80/?spell={urllib.parse.quote(str(spell_id))}&locale=4'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8', errors='ignore')
        # 优先抓标题
        m = re.search(r'<title>\s*(.*?)\s*-\s*(?:法术|Spell)\s*-', html, re.I | re.S)
        if m:
            title = re.sub(r'<.*?>', '', m.group(1)).strip()
            if title:
                return f'{spell_id}-{title}'
        # 兜底抓 h1
        m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.I | re.S)
        if m:
            title = re.sub(r'<.*?>', '', m.group(1)).strip()
            if title:
                return f'{spell_id}-{title}'
    except Exception:
        return None
    return None


def load_spell_options_from_db(db_config):
    try:
        conn = pymysql.connect(**db_config, connect_timeout=10)
        with conn.cursor() as cur:
            cur.execute("SELECT ID, COALESCE(Name_Lang_zhCN,''), COALESCE(Name_Lang_enUS,'') FROM spell_dbc ORDER BY ID ASC")
            rows = cur.fetchall()
        conn.close()
        options = []
        extra_cache = load_spell_extra_cache()
        cache_changed = False
        for spell_id, zh_name, en_name in rows:
            spell_id = str(spell_id)
            zh_name = (zh_name or '').strip()
            en_name = (en_name or '').strip()
            cached = (extra_cache.get(spell_id, '') or '').strip()
            if not zh_name and not cached and en_name and spell_id in extra_cache:
                cached = extra_cache.get(spell_id, '').strip()
            if cached:
                if en_name and cached != en_name:
                    label = f"{cached} ({en_name})"
                else:
                    label = cached
            elif zh_name and en_name and zh_name != en_name:
                label = f"{zh_name} ({en_name})"
            else:
                label = zh_name or en_name or '未命名法术'
            options.append(f"{spell_id}-{label}")
        if cache_changed:
            save_spell_extra_cache(extra_cache)
        return options
    except Exception:
        return []


def lookup_spell_label(db_config, spell_id):
    extra_cache = load_spell_extra_cache()
    cached = extra_cache.get(str(spell_id), '').strip()
    try:
        conn = pymysql.connect(**db_config, connect_timeout=10)
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(Name_Lang_zhCN,''), COALESCE(Name_Lang_enUS,'') FROM spell_dbc WHERE ID=%s", (spell_id,))
            row = cur.fetchone()
        conn.close()
        if row:
            zh_name, en_name = row
            zh_name = (zh_name or '').strip()
            en_name = (en_name or '').strip()
            if cached:
                if en_name and cached != en_name:
                    return f"{spell_id}-{cached} ({en_name})"
                return f"{spell_id}-{cached}"
            if zh_name and en_name and zh_name != en_name:
                return f"{spell_id}-{zh_name} ({en_name})"
            if zh_name or en_name:
                # 数据库只有英文时，尝试网页补中文
                if not zh_name:
                    fetched = fetch_spell_label_from_nfuwow(spell_id)
                    if fetched:
                        fetched_name = fetched.split('-',1)[1]
                        extra_cache[str(spell_id)] = fetched_name
                        save_spell_extra_cache(extra_cache)
                        if en_name and fetched_name != en_name:
                            return f"{spell_id}-{fetched_name} ({en_name})"
                        return f"{spell_id}-{fetched_name}"
                return f"{spell_id}-{zh_name or en_name}"
    except Exception:
        pass
    fetched = fetch_spell_label_from_nfuwow(spell_id)
    if fetched:
        extra_cache[str(spell_id)] = fetched.split('-',1)[1]
        save_spell_extra_cache(extra_cache)
        return fetched
    return None


class PlaceholderDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(680, 420)
        self.setFont(CHINESE_FONT)
        layout = QVBoxLayout(self)
        info = QTextEdit()
        info.setReadOnly(True)
        info.setPlainText(message)
        layout.addWidget(info)
        close_btn = QPushButton("关闭 Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class SendMailDialog(QDialog):
    def __init__(self, parent=None, db_config=None):
        super().__init__(parent)
        self.setWindowTitle("邮件发送 Server_SendMail")
        self.resize(1200, 820)
        self.setFont(CHINESE_FONT)
        self.db_config = db_config or {}
        self.receivers = []
        self.items = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.receiver_keyword = QLineEdit()
        self.receiver_keyword.setPlaceholderText('收件人关键词：角色名 / 账号')
        top.addWidget(QLabel('收件人:'))
        top.addWidget(self.receiver_keyword)
        btn = QPushButton('搜索收件人 SearchReceiver')
        btn.clicked.connect(self.search_receivers)
        top.addWidget(btn)
        layout.addLayout(top)

        self.receiver_results = QTableWidget(0, 3)
        self.receiver_results.setHorizontalHeaderLabels(['选择', 'GUID/账号', '角色名'])
        self.receiver_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.receiver_results)

        receiver_btns = QHBoxLayout()
        b1 = QPushButton('加入收件人 AddReceiver')
        b1.clicked.connect(self.add_selected_receivers)
        receiver_btns.addWidget(b1)
        b2 = QPushButton('清空收件人 ClearReceiver')
        b2.clicked.connect(self.clear_receivers)
        receiver_btns.addWidget(b2)
        layout.addLayout(receiver_btns)

        self.receiver_list = QListWidget()
        layout.addWidget(self.receiver_list)

        item_top = QHBoxLayout()
        self.item_keyword = QLineEdit()
        self.item_keyword.setPlaceholderText('物品关键词：ID / 中英文名称')
        item_top.addWidget(QLabel('附件物品:'))
        item_top.addWidget(self.item_keyword)
        ibtn = QPushButton('搜索物品 SearchItems')
        ibtn.clicked.connect(self.search_items)
        item_top.addWidget(ibtn)
        layout.addLayout(item_top)

        self.item_results = QTableWidget(0, 4)
        self.item_results.setHorizontalHeaderLabels(['选择', 'Entry', '名称', '品质'])
        self.item_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.item_results)

        item_btns = QHBoxLayout()
        a1 = QPushButton('加入附件 AddItem')
        a1.clicked.connect(self.add_selected_items)
        item_btns.addWidget(a1)
        a2 = QPushButton('清空附件 ClearItems')
        a2.clicked.connect(self.clear_items)
        item_btns.addWidget(a2)
        layout.addLayout(item_btns)

        self.item_list = QTableWidget(0, 3)
        self.item_list.setHorizontalHeaderLabels(['Entry', '名称', '数量'])
        self.item_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.item_list)

        form = QFormLayout()
        self.title_edit = QLineEdit()
        self.content_edit = QTextEdit()
        self.content_edit.setMaximumHeight(140)
        self.money_spin = QSpinBox()
        self.money_spin.setRange(0, 100000000)
        form.addRow('标题 Title:', self.title_edit)
        form.addRow('正文 Content:', self.content_edit)
        form.addRow('金币 Money(copper):', self.money_spin)
        layout.addLayout(form)

        self.sql_preview = QTextEdit()
        self.sql_preview.setFont(QFont('Monaco', 11))
        layout.addWidget(self.sql_preview)

        bottom = QHBoxLayout()
        gen_btn = QPushButton('生成邮件SQL Generate')
        gen_btn.clicked.connect(self.generate_mail_sql)
        bottom.addWidget(gen_btn)
        copy_btn = QPushButton('复制SQL Copy')
        copy_btn.clicked.connect(self.copy_sql)
        bottom.addWidget(copy_btn)
        close_btn = QPushButton('关闭 Close')
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    def _connect(self):
        return pymysql.connect(**self.db_config, connect_timeout=10)

    def search_receivers(self):
        keyword = self.receiver_keyword.text().strip()
        if not keyword:
            return
        rows = []
        try:
            conn = self._connect()
            with conn.cursor() as cur:
                try:
                    cur.execute("SELECT guid, name, account FROM characters WHERE name LIKE %s LIMIT 100", (f'%{keyword}%',))
                    rows = cur.fetchall()
                except Exception:
                    cur.execute("SELECT guid, name FROM characters WHERE name LIKE %s LIMIT 100", (f'%{keyword}%',))
                    tmp = cur.fetchall()
                    rows = [(r[0], r[1], '') for r in tmp]
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'搜索收件人失败：{e}')
            return
        self.receiver_results.setRowCount(0)
        for guid, name, account in rows:
            row = self.receiver_results.rowCount()
            self.receiver_results.insertRow(row)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            self.receiver_results.setItem(row, 0, chk)
            self.receiver_results.setItem(row, 1, QTableWidgetItem(str(account or guid)))
            self.receiver_results.setItem(row, 2, QTableWidgetItem(str(name)))
            self.receiver_results.item(row, 0).setData(Qt.UserRole, {'guid': guid, 'name': name, 'account': account})

    def add_selected_receivers(self):
        for row in range(self.receiver_results.rowCount()):
            item = self.receiver_results.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                data = item.data(Qt.UserRole)
                key = f"{data['guid']}:{data['name']}"
                if key not in [f"{x['guid']}:{x['name']}" for x in self.receivers]:
                    self.receivers.append(data)
                    self.receiver_list.addItem(f"[{data['guid']}] {data['name']}")

    def clear_receivers(self):
        self.receivers = []
        self.receiver_list.clear()

    def search_items(self):
        keyword = self.item_keyword.text().strip()
        if not keyword:
            return
        try:
            conn = self._connect()
            with conn.cursor() as cur:
                sql = "SELECT DISTINCT t.entry, t.name, COALESCE(l.Name, t.name) AS disp_name, t.Quality FROM item_template t LEFT JOIN item_template_locale l ON t.entry = l.ID AND l.locale = 'zhCN' WHERE t.entry LIKE %s OR t.name LIKE %s OR l.Name LIKE %s LIMIT 100"
                pattern = f'%{keyword}%'
                cur.execute(sql, (pattern, pattern, pattern))
                rows = cur.fetchall()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'搜索物品失败：{e}')
            return
        self.item_results.setRowCount(0)
        for entry, name_en, disp_name, quality in rows:
            row = self.item_results.rowCount()
            self.item_results.insertRow(row)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            self.item_results.setItem(row, 0, chk)
            self.item_results.setItem(row, 1, QTableWidgetItem(str(entry)))
            self.item_results.setItem(row, 2, QTableWidgetItem(str(disp_name or name_en)))
            self.item_results.setItem(row, 3, QTableWidgetItem(str(quality)))
            self.item_results.item(row, 0).setData(Qt.UserRole, {'entry': entry, 'name': disp_name or name_en, 'quality': quality})

    def add_selected_items(self):
        for row in range(self.item_results.rowCount()):
            item = self.item_results.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                data = item.data(Qt.UserRole)
                if str(data['entry']) not in [str(x['entry']) for x in self.items]:
                    data = dict(data)
                    data['count'] = 1
                    self.items.append(data)
        self.refresh_item_list()

    def refresh_item_list(self):
        self.item_list.setRowCount(0)
        for data in self.items:
            row = self.item_list.rowCount()
            self.item_list.insertRow(row)
            self.item_list.setItem(row, 0, QTableWidgetItem(str(data['entry'])))
            self.item_list.setItem(row, 1, QTableWidgetItem(str(data['name'])))
            spin = QSpinBox()
            spin.setRange(1, 999999)
            spin.setValue(int(data.get('count', 1)))
            def _upd(val, ref=data):
                ref['count'] = val
            spin.valueChanged.connect(_upd)
            self.item_list.setCellWidget(row, 2, spin)

    def clear_items(self):
        self.items = []
        self.item_list.setRowCount(0)

    def generate_mail_sql(self):
        if not self.receivers:
            QMessageBox.warning(self, '警告', '请先加入至少一个收件人')
            return
        title = self.title_edit.text().strip()
        content = self.content_edit.toPlainText().strip()
        money = int(self.money_spin.value())
        sql_parts = ['-- 邮件发送 SQL 预览（仅生成，不直接执行）']
        for idx, r in enumerate(self.receivers, start=1):
            sql_parts.append(f"-- Receiver {idx}: [{r['guid']}] {r['name']}")
            sql_parts.append("INSERT INTO `mail_draft` (`receiver_guid`, `subject`, `body`, `money`) VALUES " + f"({sql_quote(r['guid'])}, {sql_quote(title)}, {sql_quote(content)}, {money});")
            for item in self.items:
                sql_parts.append("INSERT INTO `mail_draft_items` (`receiver_guid`, `item_entry`, `item_count`) VALUES " + f"({sql_quote(r['guid'])}, {sql_quote(item['entry'])}, {int(item.get('count',1))});")
        self.sql_preview.setPlainText('\n'.join(sql_parts))


class SqlResultDialog(QDialog):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(860, 620)
        self.setFont(CHINESE_FONT)
        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont('Monaco', 11))
        text_edit.setPlainText(content)
        layout.addWidget(text_edit)
        close_btn = QPushButton('关闭 Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class CloneDialog(QDialog):
    def __init__(self, parent=None, defaults=None):
        super().__init__(parent)
        self.setWindowTitle('套用 Clone')
        self.resize(760, 360)
        self.setFont(CHINESE_FONT)
        defaults = defaults or {}
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.entry_edit = QLineEdit(defaults.get('entry', ''))
        self.name_edit = QLineEdit(defaults.get('name', ''))
        self.zh_name_edit = QLineEdit(defaults.get('Name_zhCN', ''))
        self.displayid_edit = QLineEdit(defaults.get('displayid', ''))
        self.zh_desc_edit = QTextEdit(defaults.get('Description_zhCN', ''))
        self.zh_desc_edit.setMaximumHeight(100)
        form.addRow('新物品ID Entry:', self.entry_edit)
        form.addRow('英文名称 Name:', self.name_edit)
        form.addRow('中文名称 Name zhCN:', self.zh_name_edit)
        form.addRow('显示ID DisplayID:', self.displayid_edit)
        form.addRow('中文描述 Description zhCN:', self.zh_desc_edit)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_values(self):
        return {
            'entry': self.entry_edit.text().strip(),
            'name': self.name_edit.text().strip(),
            'Name_zhCN': self.zh_name_edit.text().strip(),
            'displayid': self.displayid_edit.text().strip(),
            'Description_zhCN': self.zh_desc_edit.toPlainText().strip(),
        }


class LookupDialog(QDialog):
    def __init__(self, parent=None, db_config=None, field_name='itemset'):
        super().__init__(parent)
        self.setWindowTitle(f'查询选择器 {field_name}')
        self.resize(900, 620)
        self.setFont(CHINESE_FONT)
        self.db_config = db_config or {}
        self.field_name = field_name
        self.selected_value = None
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.keyword = QLineEdit()
        self.keyword.setPlaceholderText('输入关键词/ID后搜索')
        top.addWidget(self.keyword)
        btn = QPushButton('搜索 Search')
        btn.clicked.connect(self.search)
        top.addWidget(btn)
        layout.addLayout(top)
        self.results = QTableWidget(0, 3)
        self.results.setHorizontalHeaderLabels(['ID', '名称/内容', '备注'])
        self.results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.results)
        bottom = QHBoxLayout()
        ok_btn = QPushButton('选择 Select')
        ok_btn.clicked.connect(self.accept_selection)
        bottom.addWidget(ok_btn)
        close_btn = QPushButton('关闭 Close')
        close_btn.clicked.connect(self.reject)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    def _connect(self):
        return pymysql.connect(**self.db_config, connect_timeout=10)

    def search(self):
        kw = self.keyword.text().strip()
        if not kw:
            kw = '%'
        pattern = f'%{kw}%'
        rows = []
        try:
            conn = self._connect()
            with conn.cursor() as cur:
                if self.field_name == 'itemset':
                    try:
                        cur.execute("SELECT id, name, '' FROM item_set_names WHERE CAST(id AS CHAR) LIKE %s OR name LIKE %s LIMIT 100", (pattern, pattern))
                        rows = cur.fetchall()
                    except Exception:
                        cur.execute("SELECT itemset, COALESCE(name,''), COUNT(*) FROM item_template WHERE CAST(itemset AS CHAR) LIKE %s AND itemset <> 0 GROUP BY itemset, name LIMIT 100", (pattern,))
                        rows = [(sid, name, f'引用物品数={cnt}') for sid, name, cnt in cur.fetchall()]
                elif self.field_name == 'lockid':
                    try:
                        cur.execute("SELECT id, CONCAT('type=', type1, ', index=', index1), '' FROM lock WHERE CAST(id AS CHAR) LIKE %s LIMIT 100", (pattern,))
                        rows = cur.fetchall()
                    except Exception:
                        rows = []
                elif self.field_name == 'PageText':
                    try:
                        cur.execute("SELECT id, LEFT(text, 120), CASE WHEN next_page <> 0 THEN CONCAT('next=', next_page) ELSE '' END FROM page_text WHERE CAST(id AS CHAR) LIKE %s OR text LIKE %s LIMIT 100", (pattern, pattern))
                        rows = cur.fetchall()
                    except Exception:
                        rows = []
                elif self.field_name == 'RequiredReputationFaction':
                    try:
                        cur.execute("SELECT ID, COALESCE(Name_Lang_zhCN,''), COALESCE(Name_Lang_enUS,'') FROM faction_dbc WHERE CAST(ID AS CHAR) LIKE %s OR Name_Lang_enUS LIKE %s OR Name_Lang_zhCN LIKE %s LIMIT 100", (pattern, pattern, pattern))
                        rows = [(rid, format_bilingual(zh, en), en) for rid, zh, en in cur.fetchall()]
                    except Exception:
                        rows = []
                elif self.field_name == 'requiredspell':
                    try:
                        cur.execute("SELECT ID, COALESCE(Name_Lang_zhCN,''), COALESCE(Name_Lang_enUS,'') FROM spell_dbc WHERE CAST(ID AS CHAR) LIKE %s OR Name_Lang_enUS LIKE %s OR Name_Lang_zhCN LIKE %s LIMIT 100", (pattern, pattern, pattern))
                        rows = [(sid, format_bilingual(zh, en), en) for sid, zh, en in cur.fetchall()]
                    except Exception:
                        rows = []
                elif self.field_name == 'DisenchantID':
                    try:
                        cur.execute("SELECT ID, COALESCE(Name_Lang_zhCN,''), COALESCE(Name_Lang_enUS,'') FROM spell_dbc WHERE CAST(ID AS CHAR) LIKE %s OR Name_Lang_enUS LIKE %s OR Name_Lang_zhCN LIKE %s LIMIT 100", (pattern, pattern, pattern))
                        rows = [(sid, format_bilingual(zh, en), en) for sid, zh, en in cur.fetchall()]
                    except Exception:
                        rows = []
                elif self.field_name == 'GemProperties':
                    try:
                        cur.execute("SELECT ID, Enchant_Id, Maxcount_inv FROM gemproperties_dbc WHERE CAST(ID AS CHAR) LIKE %s LIMIT 100", (pattern,))
                        rows = [(gid, f'附魔ID={enchant_id}', f'MaxCount={maxc}') for gid, enchant_id, maxc in cur.fetchall()]
                    except Exception:
                        rows = []
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'查询失败：{e}')
            return
        self.results.setRowCount(0)
        for a, b, c in rows:
            row = self.results.rowCount()
            self.results.insertRow(row)
            self.results.setItem(row, 0, QTableWidgetItem(str(a)))
            self.results.setItem(row, 1, QTableWidgetItem(str(b)))
            self.results.setItem(row, 2, QTableWidgetItem(str(c)))

    def accept_selection(self):
        row = self.results.currentRow()
        if row < 0:
            return
        self.selected_value = self.results.item(row, 0).text()
        self.accept()

    def get_selected_value(self):
        return self.selected_value


class MPQMakerDialog(QDialog):
    def __init__(self, parent=None, db_config=None):
        super().__init__(parent)
        self.setWindowTitle('MPQ工具 FrmMPQMaker')
        self.resize(980, 760)
        self.setFont(CHINESE_FONT)
        self.db_config = db_config or {}
        self.project_dir = Path(__file__).parent
        self.default_base_dbc = self.project_dir / 'data' / 'Item.dbc'
        self.default_out_dir = self.project_dir / 'build_patch'
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.base_dbc_edit = QLineEdit(str(self.default_base_dbc))
        base_btn = QPushButton('选择 Select')
        base_btn.clicked.connect(self.choose_base_dbc)
        base_row = QHBoxLayout()
        base_row.addWidget(self.base_dbc_edit)
        base_row.addWidget(base_btn)
        form.addRow('基础 Item.dbc:', base_row)

        self.output_dir_edit = QLineEdit(str(self.default_out_dir))
        out_btn = QPushButton('选择 Select')
        out_btn.clicked.connect(self.choose_output_dir)
        out_row = QHBoxLayout()
        out_row.addWidget(self.output_dir_edit)
        out_row.addWidget(out_btn)
        form.addRow('输出目录 Output:', out_row)

        self.csv_name_edit = QLineEdit('item_template_export.csv')
        self.out_dbc_name_edit = QLineEdit('Item.dbc')
        form.addRow('导出CSV文件名:', self.csv_name_edit)
        form.addRow('输出DBC文件名:', self.out_dbc_name_edit)
        layout.addLayout(form)

        tip = QTextEdit()
        tip.setReadOnly(True)
        tip.setMaximumHeight(90)
        tip.setPlainText("这版 MPQ 工具先补 GUI 入口和 Item.dbc 构建链路。\n\n已接入：\n- itemdbc_mpq_builder.py\n- build_patch 输出目录\n\n当前先做：导出 CSV、重建 Item.dbc、打开输出目录、复制命令日志。")
        layout.addWidget(tip)

        btns = QHBoxLayout()
        b1 = QPushButton('导出CSV Export CSV')
        b1.clicked.connect(self.export_csv)
        btns.addWidget(b1)
        b2 = QPushButton('重建DBC Build Item.dbc')
        b2.clicked.connect(self.build_dbc)
        btns.addWidget(b2)
        b3 = QPushButton('生成MPQ Build MPQ')
        b3.clicked.connect(self.build_mpq)
        btns.addWidget(b3)
        b4 = QPushButton('生成清单 Manifest/Version')
        b4.clicked.connect(self.generate_patch_metadata)
        btns.addWidget(b4)
        b5 = QPushButton('打开输出目录 Open Output')
        b5.clicked.connect(self.open_output_dir)
        btns.addWidget(b5)
        b6 = QPushButton('复制日志 Copy Log')
        b6.clicked.connect(self.copy_log)
        btns.addWidget(b6)
        layout.addLayout(btns)

        self.log_text = QTextEdit()
        self.log_text.setFont(QFont('Monaco', 11))
        layout.addWidget(self.log_text)

        close_btn = QPushButton('关闭 Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def append_log(self, text):
        old = self.log_text.toPlainText()
        self.log_text.setPlainText((old + "\n" + text).strip())

    def choose_base_dbc(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择基础 Item.dbc', str(self.default_base_dbc.parent), 'DBC Files (*.dbc);;All Files (*)')
        if path:
            self.base_dbc_edit.setText(path)

    def choose_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, '选择输出目录', self.output_dir_edit.text())
        if path:
            self.output_dir_edit.setText(path)

    def _builder_cmd(self, export_csv=True):
        out_dir = Path(self.output_dir_edit.text().strip())
        out_dir.mkdir(parents=True, exist_ok=True)
        base_dbc = Path(self.base_dbc_edit.text().strip())
        export_csv_path = out_dir / self.csv_name_edit.text().strip()
        out_dbc_path = out_dir / self.out_dbc_name_edit.text().strip()
        cmd = [
            sys.executable,
            str(self.project_dir / 'itemdbc_mpq_builder.py'),
            '--base-item-dbc', str(base_dbc),
            '--out-item-dbc', str(out_dbc_path),
        ]
        if export_csv:
            cmd += [
                '--export-csv', str(export_csv_path),
                '--db-host', str(self.db_config.get('host', '127.0.0.1')),
                '--db-port', str(self.db_config.get('port', 3306)),
                '--db-name', str(self.db_config.get('database', 'acore_world_test')),
                '--db-user', str(self.db_config.get('user', 'root')),
                '--db-password', str(self.db_config.get('password', '')),
            ]
        return cmd, export_csv_path, out_dbc_path

    def export_csv(self):
        cmd, export_csv_path, out_dbc_path = self._builder_cmd(export_csv=True)
        preview_cmd = ' '.join(cmd)
        self.append_log('[Export CSV] ' + preview_cmd)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_dir))
            self.append_log(result.stdout.strip())
            if result.stderr.strip():
                self.append_log('[stderr]\n' + result.stderr.strip())
            if result.returncode == 0:
                QMessageBox.information(self, '成功', f'CSV已导出：{export_csv_path}')
            else:
                QMessageBox.critical(self, '失败', f'导出CSV失败，退出码 {result.returncode}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导出CSV失败：{e}')

    def build_dbc(self):
        cmd, export_csv_path, out_dbc_path = self._builder_cmd(export_csv=True)
        preview_cmd = ' '.join(cmd)
        self.append_log('[Build Item.dbc] ' + preview_cmd)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_dir))
            self.append_log(result.stdout.strip())
            if result.stderr.strip():
                self.append_log('[stderr]\n' + result.stderr.strip())
            if result.returncode == 0:
                QMessageBox.information(self, '成功', f'Item.dbc已生成：{out_dbc_path}')
            else:
                QMessageBox.critical(self, '失败', f'重建DBC失败，退出码 {result.returncode}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'重建DBC失败：{e}')

    def find_mpqcli(self):
        candidates = [
            Path('/Users/mac/Desktop/诺兰补丁/tools/mpqcli/build/bin/mpqcli'),
            self.project_dir / 'tools' / 'mpqcli' / 'build' / 'bin' / 'mpqcli',
        ]
        for c in candidates:
            if c.exists():
                return c
        return None

    def sha256_of(self, path):
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()

    def build_mpq(self):
        cmd, export_csv_path, out_dbc_path = self._builder_cmd(export_csv=True)
        self.append_log('[Build MPQ] 先重建 Item.dbc')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_dir))
            self.append_log(result.stdout.strip())
            if result.stderr.strip():
                self.append_log('[stderr]\n' + result.stderr.strip())
            if result.returncode != 0:
                QMessageBox.critical(self, '失败', f'重建DBC失败，退出码 {result.returncode}')
                return
        except Exception as e:
            QMessageBox.critical(self, '错误', f'重建DBC失败：{e}')
            return

        mpqcli = self.find_mpqcli()
        if not mpqcli:
            QMessageBox.warning(self, '提示', '未找到 mpqcli，已完成 DBC 阶段，但还不能生成 MPQ')
            return

        out_dir = Path(self.output_dir_edit.text().strip())
        mpq_root = out_dir / 'mpq_root'
        dbfiles = mpq_root / 'DBFilesClient'
        zhcn = mpq_root / 'zhCN' / 'DBFilesClient'
        dbfiles.mkdir(parents=True, exist_ok=True)
        zhcn.mkdir(parents=True, exist_ok=True)

        root_item = dbfiles / 'Item.dbc'
        zh_item = zhcn / 'Item.dbc'
        root_item.write_bytes(Path(out_dbc_path).read_bytes())
        zh_item.write_bytes(Path(out_dbc_path).read_bytes())

        targets = [out_dir / 'patch-Z.mpq', out_dir / 'patch-zhCN-Z.mpq']
        for target in targets:
            if target.exists():
                target.unlink()
            run = subprocess.run([str(mpqcli), 'create', str(mpq_root), '-o', str(target), '-g', 'wow-wotlk'], capture_output=True, text=True)
            self.append_log(f'## {target.name}')
            if run.stdout.strip():
                self.append_log(run.stdout.strip())
            if run.stderr.strip():
                self.append_log('[stderr]\n' + run.stderr.strip())

        ok = all(t.exists() for t in targets)
        if not ok:
            QMessageBox.critical(self, '失败', 'MPQ 生成失败，请看日志')
            return

        summary = []
        for t in targets:
            summary.append(f"{t.name} | size={t.stat().st_size} | sha256={self.sha256_of(t)}")
        self.append_log('\n'.join(summary))
        QMessageBox.information(self, '成功', '已生成 patch-Z.mpq 和 patch-zhCN-Z.mpq')


    def patch_env_name(self):
        db_name = str(self.db_config.get('database', 'acore_world_test'))
        return 'test' if 'test' in db_name else 'release'

    def patch_base_url(self):
        return 'http://43.248.129.172:88'

    def write_json(self, path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def generate_patch_metadata(self):
        out_dir = Path(self.output_dir_edit.text().strip())
        env = self.patch_env_name()
        patch_root = out_dir / 'patch-Z.mpq'
        patch_zh = out_dir / 'patch-zhCN-Z.mpq'
        if not patch_root.exists() or not patch_zh.exists():
            QMessageBox.warning(self, '警告', '请先生成 MPQ，再生成 manifest/version')
            return

        version = time.strftime('%Y.%m.%d.%H%M%S', time.localtime())
        version_token = str(int(time.time()))
        base_url = self.patch_base_url()

        sha_root = self.sha256_of(patch_root)
        sha_zh = self.sha256_of(patch_zh)
        size_root = patch_root.stat().st_size
        size_zh = patch_zh.stat().st_size

        manifest = {
            'version': version,
            'files': [
                {
                    'name': 'patch-Z.mpq',
                    'url': f"{base_url}/patches/{env}/patch-Z.mpq?v={version_token}",
                    'sha256': sha_root,
                    'size': size_root,
                },
                {
                    'name': 'patch-zhCN-Z.mpq',
                    'url': f"{base_url}/patches/{env}/patch-zhCN-Z.mpq?v={version_token}",
                    'sha256': sha_zh,
                    'size': size_zh,
                }
            ]
        }
        version_json = {'version': version}

        patch_entry_root = {
            'Name': 'patch-Z',
            'Version': version,
            'Hash': sha_root,
            'HashType': 'sha256',
            'DownloadUrl': f"{base_url}/patches/{env}/patch-Z.mpq?v={version_token}",
            'LocalRelativePath': 'Data/patch-Z.mpq',
            'Size': size_root,
        }
        patch_entry_zh = {
            'Name': 'patch-zhCN-Z',
            'Version': version,
            'Hash': sha_zh,
            'HashType': 'sha256',
            'DownloadUrl': f"{base_url}/patches/{env}/patch-zhCN-Z.mpq?v={version_token}",
            'LocalRelativePath': 'Data/zhCN/patch-zhCN-Z.mpq',
            'Size': size_zh,
        }
        channel_manifest = [patch_entry_root, patch_entry_zh]
        channel_version = {
            'Version': version,
            'PatchCount': len(channel_manifest),
            'GeneratedAt': version,
        }
        combined_manifest = channel_manifest
        combined_version = channel_version

        outputs = {
            out_dir / f'manifest_{env}.json': manifest,
            out_dir / f'version_{env}.json': version_json,
            out_dir / f'root_manifest_{env}.json': manifest,
            out_dir / f'root_version_{env}.json': version_json,
            out_dir / f'channel_manifest_{env}.json': channel_manifest,
            out_dir / f'channel_version_{env}.json': channel_version,
            out_dir / f'combined_manifest_{env}.json': combined_manifest,
            out_dir / f'combined_version_{env}.json': combined_version,
        }
        for path, data in outputs.items():
            self.write_json(path, data)
            self.append_log(f'[write] {path}')

        self.append_log(f'[manifest] env={env} version={version}')
        self.append_log(f'patch-Z.mpq sha256={sha_root} size={size_root}')
        self.append_log(f'patch-zhCN-Z.mpq sha256={sha_zh} size={size_zh}')
        QMessageBox.information(self, '成功', f'已生成 {env} 环境的 manifest/version JSON')

    def open_output_dir(self):
        out_dir = self.output_dir_edit.text().strip()
        subprocess.run(['open', out_dir])

    def copy_log(self):
        QApplication.clipboard().setText(self.log_text.toPlainText())
        QMessageBox.information(self, '成功', '日志已复制')


class SearchDialog(QDialog):
    def __init__(self, parent=None, db_config=None):
        super().__init__(parent)
        self.setWindowTitle("搜索物品 Search Items")
        self.setModal(True)
        self.resize(800, 600)
        self.setFont(CHINESE_FONT)
        self.db_config = db_config or {}
        
        layout = QVBoxLayout(self)
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索类型 Type:"))
        self.search_type = NoWheelComboBox()
        self.search_type.addItems(['综合 Mixed', '按ID Entry', '按中文 Chinese', '按英文 English'])
        search_layout.addWidget(self.search_type)
        search_layout.addWidget(QLabel("关键词 Keyword:"))
        self.keyword = QLineEdit()
        self.keyword.returnPressed.connect(self.search)
        search_layout.addWidget(self.keyword)
        search_btn = QPushButton("搜索 Search")
        search_btn.clicked.connect(self.search)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self.select_item)
        layout.addWidget(self.results)
        
        buttons = QHBoxLayout()
        select_btn = QPushButton("选择 Select")
        select_btn.clicked.connect(self.select_item)
        close_btn = QPushButton("关闭 Close")
        close_btn.clicked.connect(self.reject)
        buttons.addWidget(select_btn)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)
    
    def search(self):
        keyword = self.keyword.text().strip()
        if not keyword:
            return
        try:
            conn = pymysql.connect(**self.db_config, connect_timeout=10)
            with conn.cursor() as cur:
                stype = self.search_type.currentText()
                pattern = f"%{keyword}%"
                if stype.startswith('按ID'):
                    sql = """SELECT DISTINCT t.entry, t.name, l.Name as name_zh, t.Quality 
                             FROM item_template t
                             LEFT JOIN item_template_locale l ON t.entry = l.ID AND l.locale = 'zhCN'
                             WHERE CAST(t.entry AS CHAR) LIKE %s
                             LIMIT 100"""
                    args = (pattern,)
                elif stype.startswith('按中文'):
                    sql = """SELECT DISTINCT t.entry, t.name, l.Name as name_zh, t.Quality 
                             FROM item_template t
                             LEFT JOIN item_template_locale l ON t.entry = l.ID AND l.locale = 'zhCN'
                             WHERE l.Name LIKE %s
                             LIMIT 100"""
                    args = (pattern,)
                elif stype.startswith('按英文'):
                    sql = """SELECT DISTINCT t.entry, t.name, l.Name as name_zh, t.Quality 
                             FROM item_template t
                             LEFT JOIN item_template_locale l ON t.entry = l.ID AND l.locale = 'zhCN'
                             WHERE t.name LIKE %s
                             LIMIT 100"""
                    args = (pattern,)
                else:
                    sql = """SELECT DISTINCT t.entry, t.name, l.Name as name_zh, t.Quality 
                             FROM item_template t
                             LEFT JOIN item_template_locale l ON t.entry = l.ID AND l.locale = 'zhCN'
                             WHERE CAST(t.entry AS CHAR) LIKE %s OR t.name LIKE %s OR l.Name LIKE %s
                             LIMIT 100"""
                    args = (pattern, pattern, pattern)
                cur.execute(sql, args)
                rows = cur.fetchall()
                self.results.clear()
                for row in rows:
                    entry, name_en, name_zh, quality = row
                    quality_names = ["垃圾", "普通", "优秀", "精良", "史诗", "传说", "神器"]
                    quality_name = quality_names[quality] if 0 <= quality < len(quality_names) else str(quality)
                    display_name = f"{name_zh or name_en}"
                    if name_zh and name_en and name_zh != name_en:
                        display_name += f" ({name_en})"
                    item = QListWidgetItem(f"[{entry}] {display_name} - {quality_name}")
                    item.setData(Qt.UserRole, entry)
                    self.results.addItem(item)
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "错误 Error", f"搜索失败：{e}")
    
    def select_item(self):
        current = self.results.currentItem()
        if current:
            self.selected_entry = current.data(Qt.UserRole)
            self.accept()
    
    def get_selected_entry(self):
        return getattr(self, 'selected_entry', None)


class WOWItemMakerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("诺兰时光物品工具 v3.1 / WOWItemMaker")
        self.setGeometry(50, 50, 2200, 1300)
        self.setFont(CHINESE_FONT)
        
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self.config = {
            "db": {
                "host": "43.248.129.172",
                "port": 3306,
                "user": "wowitem",
                "password": "GknNJLRtcE6RzigVJFF8",
                "database": "acore_world_test"
            },
            "savePassword": True
        }
        
        self.fields = {}
        self.create_ui()
        self.load_config()
        self.refresh_dynamic_spell_options(force=True)
        self.refresh_dynamic_bilingual_options()
        self.refresh_local_dictionary_options()
    
    def normalize_spell_combo_labels(self):
        extra_cache = load_spell_extra_cache()
        if not extra_cache:
            return
        for i in range(1, 6):
            widget = self.fields.get(f'spellid_{i}')
            if isinstance(widget, QComboBox):
                for idx in range(widget.count()):
                    txt = widget.itemText(idx)
                    if '-' not in txt:
                        continue
                    spell_id, rest = txt.split('-', 1)
                    cached = (extra_cache.get(str(spell_id), '') or '').strip()
                    if cached and cached not in rest:
                        en = rest.strip()
                        new_label = f"{spell_id}-{cached} ({en})" if en and cached != en else f"{spell_id}-{cached}"
                        widget.setItemText(idx, new_label)

    def refresh_dynamic_spell_options(self, force=False):
        spell_options = load_spell_options_from_db(self.config.get('db', {}))
        if not spell_options:
            spell_options = COMBO_OPTIONS.get('spellid', [])
        # 去重，防止缓存回填和已有选项重复
        dedup = []
        seen = set()
        for opt in spell_options:
            if '-' in opt:
                sid = opt.split('-', 1)[0]
            else:
                sid = opt
            if sid in seen:
                continue
            seen.add(sid)
            dedup.append(opt)
        spell_options = dedup
        COMBO_OPTIONS['spellid'] = spell_options
        for i in range(1, 6):
            COMBO_OPTIONS[f'spellid_{i}'] = spell_options
            widget = self.fields.get(f'spellid_{i}')
            current = widget.currentText() if isinstance(widget, QComboBox) else ''
            current_id = current.split('-', 1)[0] if current else ''
            if isinstance(widget, QComboBox):
                widget.blockSignals(True)
                widget.clear()
                widget.addItems(spell_options)
                if current_id:
                    found = False
                    for idx in range(widget.count()):
                        if widget.itemText(idx).startswith(current_id + '-') or widget.itemText(idx) == current_id:
                            widget.setCurrentIndex(idx)
                            found = True
                            break
                    if not found:
                        self.ensure_spell_option(f'spellid_{i}', current_id)
                widget.blockSignals(False)
        self.normalize_spell_combo_labels()

    def hydrate_spell_option_from_web(self, spell_id):
        spell_str = str(spell_id or '').strip()
        if not spell_str or spell_str == '0':
            return None
        label = lookup_spell_label(self.config.get('db', {}), spell_str)
        if not label:
            return None
        # update all spell combo rows with the hydrated bilingual label
        for i in range(1, 6):
            widget = self.fields.get(f'spellid_{i}')
            if isinstance(widget, QComboBox):
                for idx in range(widget.count()):
                    if widget.itemText(idx).startswith(spell_str + '-'):
                        widget.setItemText(idx, label)
                        break
        return label

    def refresh_dynamic_bilingual_options(self):
        faction_options = load_faction_options_from_db(self.config.get('db', {}))
        if faction_options:
            COMBO_OPTIONS['RequiredReputationFaction'] = faction_options
            widget = self.fields.get('RequiredReputationFaction')
            current = widget.currentText() if isinstance(widget, QComboBox) else ''
            current_id = current.split('-', 1)[0] if current else ''
            if isinstance(widget, QComboBox):
                widget.blockSignals(True)
                widget.clear()
                widget.addItems(faction_options)
                if current_id:
                    for idx in range(widget.count()):
                        if widget.itemText(idx).startswith(current_id + '-'):
                            widget.setCurrentIndex(idx)
                            break
                widget.blockSignals(False)

        spell_options = load_required_spell_options_from_db(self.config.get('db', {}))
        for key in ['requiredspell', 'DisenchantID']:
            widget = self.fields.get(key)
            current = widget.currentText() if isinstance(widget, QComboBox) else ''
            current_id = current.split('-', 1)[0] if current else ''
            if isinstance(widget, QComboBox) and spell_options:
                widget.blockSignals(True)
                widget.clear()
                widget.addItems(spell_options)
                if current_id:
                    for idx in range(widget.count()):
                        if widget.itemText(idx).startswith(current_id + '-'):
                            widget.setCurrentIndex(idx)
                            break
                widget.blockSignals(False)

    def refresh_local_dictionary_options(self):
        mappings = {
            'RandomProperty': COMBO_OPTIONS.get('RandomProperty', []),
            'RandomSuffix': COMBO_OPTIONS.get('RandomSuffix', []),
            'displayid': COMBO_OPTIONS.get('displayid', []),
        }
        for key, options in mappings.items():
            normalized = [normalize_option_label(opt) for opt in options if opt]
            dedup = []
            seen = set()
            for opt in normalized:
                oid = opt.split('-', 1)[0] if '-' in opt else opt
                if oid in seen:
                    continue
                seen.add(oid)
                dedup.append(opt)
            COMBO_OPTIONS[key] = dedup
            widget = self.fields.get(key)
            if isinstance(widget, QComboBox):
                refresh_combo_options(widget, dedup)

    def tracked_fields(self):
        fields = ['Quality', 'class', 'subclass', 'bonding', 'InventoryType', 'Flags', 'FlagsExtra', 'StatsCount', 'SpellsCount']
        fields += [f'spelltrigger_{i}' for i in range(1, 6)]
        fields += [f'spellid_{i}' for i in range(1, 6)]
        return fields

    def highlight_changed_field(self, field_name):
        widget = self.fields.get(field_name)
        if not widget:
            return
        widget.setStyleSheet('background-color: #fff3cd; border: 1px solid #f0ad4e;')

    def clear_field_highlight(self, field_name):
        widget = self.fields.get(field_name)
        if not widget:
            return
        widget.setStyleSheet('')

    def connect_change_highlights(self):
        for field_name in self.tracked_fields():
            widget = self.fields.get(field_name)
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(lambda _=None, f=field_name: self.highlight_changed_field(f))
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda _=None, f=field_name: self.highlight_changed_field(f))
            elif isinstance(widget, QTextEdit):
                widget.textChanged.connect(lambda f=field_name: self.highlight_changed_field(f))

    def build_change_summary(self):
        rows = []
        mapping = {
            'entry': '物品ID',
            'name': '名称',
            'Quality': '品质',
            'class': '类型',
            'subclass': '子类型',
            'bonding': '绑定',
            'InventoryType': '装备槽',
            'StatsCount': '绿字数量',
            'SpellsCount': '法术数量',
            'Flags': 'Flags',
            'FlagsExtra': 'FlagsExtra',
        }
        for k, label in mapping.items():
            v = self.fields.get(k)
            if v is not None:
                rows.append(f'{label}: {self.get_field_value(k)}')
        for i in range(1, 6):
            sid = self.get_field_value(f'spellid_{i}')
            trg = self.get_field_value(f'spelltrigger_{i}')
            if sid not in ('', '0'):
                rows.append(f'法术{i}: {sid} | 触发={trg}')
        return '\n'.join(rows)

    def confirm_action_with_summary(self, title, lead_text):
        summary = self.build_change_summary()
        msg = lead_text + '\n\n' + summary
        return QMessageBox.question(self, title, msg) == QMessageBox.Yes

    def create_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("物品ID:"))
        self.fields['entry'] = QLineEdit()
        self.fields['entry'].setMaximumWidth(150)
        toolbar.addWidget(self.fields['entry'])
        
        load_btn = QPushButton("读取 Load")
        load_btn.clicked.connect(self.load_item)
        toolbar.addWidget(load_btn)
        
        save_btn = QPushButton("保存 Save")
        save_btn.clicked.connect(self.save_item)
        toolbar.addWidget(save_btn)
        
        delete_btn = QPushButton("删除 Delete")
        delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        delete_btn.clicked.connect(self.delete_item)
        toolbar.addWidget(delete_btn)
        
        toolbar.addSpacing(20)
        
        search_btn = QPushButton("搜索 Search")
        search_btn.clicked.connect(self.search_item)
        toolbar.addWidget(search_btn)
        
        clone_btn = QPushButton("套用 Clone")
        clone_btn.clicked.connect(self.clone_item)
        toolbar.addWidget(clone_btn)

        tools_btn = QPushButton("辅助 Tools")
        tools_btn.clicked.connect(self.show_tools_menu)
        toolbar.addWidget(tools_btn)

        copy_btn = QPushButton("复制 Copy")
        copy_btn.clicked.connect(self.copy_item)
        toolbar.addWidget(copy_btn)

        sql_btn = QPushButton("SQL工具 SQL")
        sql_btn.clicked.connect(self.show_sql_tools)
        toolbar.addWidget(sql_btn)

        mpq_btn = QPushButton("MPQ工具 MPQ")
        mpq_btn.clicked.connect(self.show_mpq_maker)
        toolbar.addWidget(mpq_btn)

        patch_btn = QPushButton("问号补丁 Patch")
        patch_btn.clicked.connect(self.make_question_patch)
        toolbar.addWidget(patch_btn)

        push_patch_btn = QPushButton("推送补丁 Push")
        push_patch_btn.clicked.connect(self.push_patch_to_server)
        toolbar.addWidget(push_patch_btn)

        check_patch_btn = QPushButton("校验补丁 Check")
        check_patch_btn.clicked.connect(self.check_patch_preflight)
        toolbar.addWidget(check_patch_btn)

        mail_btn = QPushButton("邮件 SendMail")
        mail_btn.clicked.connect(self.show_send_mail)
        toolbar.addWidget(mail_btn)

        server_btn = QPushButton("服务器 Server")
        server_btn.clicked.connect(self.show_server_manager)
        toolbar.addWidget(server_btn)
        
        toolbar.addStretch()
        
        self.status_label = QLabel("测试服 Test")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        toolbar.addWidget(self.status_label)
        
        config_btn = QPushButton("配置 Config")
        config_btn.clicked.connect(self.show_config)
        toolbar.addWidget(config_btn)
        
        layout.addLayout(toolbar)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：基础信息
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_widget = QWidget()
        left_widget.setFont(CHINESE_FONT)
        left_layout = QVBoxLayout(left_widget)
        
        # 基础信息组
        basic_group = QGroupBox("基本信息 Basic Info")
        basic_layout = QGridLayout(basic_group)
        
        row = 0
        for field_id, label, category, widget_type in ALL_FIELDS:
            if category != "基础 Basic":
                continue
            
            basic_layout.addWidget(QLabel(label), row, 0)
            
            if widget_type == "combo":
                self.fields[field_id] = NoWheelComboBox()
                options = COMBO_OPTIONS.get(field_id, [])
                if options:
                    self.fields[field_id].addItems(options)
            elif widget_type == "textarea":
                self.fields[field_id] = QTextEdit()
                self.fields[field_id].setMaximumHeight(80)
            else:
                self.fields[field_id] = QLineEdit()
            
            basic_layout.addWidget(self.fields[field_id], row, 1)
            row += 1
        
        left_layout.addWidget(basic_group)
        left_layout.addStretch()
        
        left_scroll.setWidget(left_widget)
        splitter.addWidget(left_scroll)
        
        # 右侧：详细选项卡
        tabs = QTabWidget()
        tabs.setFont(CHINESE_FONT)
        
        # 各选项卡
        for tab_category, tab_name in [
            ("需求 Requirements", "需求 Req"),
            ("属性 Stats", "属性 Stats"),
            ("伤害 Damage", "伤害 Damage"),
            ("法术1 Spell1", "法术1 Spell1"),
            ("法术2 Spell2", "法术2 Spell2"),
            ("法术3 Spell3", "法术3 Spell3"),
            ("法术4 Spell4", "法术4 Spell4"),
            ("法术5 Spell5", "法术5 Spell5"),
            ("Socket", "Socket"),
            ("高级 Advanced", "高级 Adv"),
        ]:
            tab_scroll = QScrollArea()
            tab_scroll.setWidgetResizable(True)
            tab_widget = QWidget()
            tab_widget.setFont(CHINESE_FONT)
            tab_layout = QVBoxLayout(tab_widget)
            
            tab_group = QGroupBox(tab_category)
            tab_grid = QGridLayout(tab_group)
            
            row = 0
            for field_id, label, category, widget_type in ALL_FIELDS:
                if category != tab_category:
                    continue
                
                tab_grid.addWidget(QLabel(label), row, 0)
                
                if widget_type == "combo":
                    self.fields[field_id] = NoWheelComboBox()
                    # 处理 stat_type 和 spelltrigger 的通用选项
                    if 'stat_type' in field_id:
                        options = COMBO_OPTIONS['stat_type1']
                    elif 'spelltrigger' in field_id:
                        options = COMBO_OPTIONS['spelltrigger_1']
                    elif 'dmg_type' in field_id:
                        options = COMBO_OPTIONS.get('dmg_type', [])
                    elif 'socketColor' in field_id:
                        options = COMBO_OPTIONS.get('socketColor', [])
                    elif field_id == 'subclass':
                        current_class = self.get_field_value('class') or '0'
                        options = COMBO_OPTIONS.get(f'subclass{current_class}', COMBO_OPTIONS.get('subclass0', COMBO_OPTIONS.get(field_id, [])))
                    else:
                        options = COMBO_OPTIONS.get(field_id, [])
                    
                    if options:
                        self.fields[field_id].addItems(options)
                else:
                    self.fields[field_id] = QLineEdit()
                
                tab_grid.addWidget(self.fields[field_id], row, 1)
                row += 1
            
            tab_layout.addWidget(tab_group)
            tab_layout.addStretch()
            
            tab_scroll.setWidget(tab_widget)
            tabs.addTab(tab_scroll, tab_name)
        
        # SQL选项卡
        sql_widget = QWidget()
        sql_layout = QVBoxLayout(sql_widget)
        
        self.sql_text = QTextEdit()
        self.sql_text.setFont(QFont("Monaco", 12))
        sql_layout.addWidget(self.sql_text)
        
        btn_layout = QHBoxLayout()
        for label, action in [("生成INSERT", "INSERT"), ("生成REPLACE", "REPLACE"), ("生成UPDATE", "UPDATE"), ("生成DELETE", "DELETE")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, a=action: self.generate_sql(a))
            btn_layout.addWidget(btn)
        
        exec_btn = QPushButton("执行SQL Execute")
        exec_btn.clicked.connect(self.execute_current_sql)
        btn_layout.addWidget(exec_btn)

        preview_btn = QPushButton("结果窗口 Result")
        preview_btn.clicked.connect(self.show_sql_result_window)
        btn_layout.addWidget(preview_btn)

        copy_btn = QPushButton("复制 Copy")
        copy_btn.clicked.connect(self.copy_sql)
        btn_layout.addWidget(copy_btn)
        
        sql_layout.addLayout(btn_layout)
        tabs.addTab(sql_widget, "SQL")
        
        splitter.addWidget(tabs)
        splitter.setSizes([600, 1600])
        layout.addWidget(splitter)

        if 'class' in self.fields and isinstance(self.fields['class'], QComboBox):
            self.fields['class'].currentIndexChanged.connect(self.update_subclass_options)
        if 'StatsCount' in self.fields and isinstance(self.fields['StatsCount'], QComboBox):
            self.fields['StatsCount'].currentIndexChanged.connect(self.update_stats_visibility)
        if 'SpellsCount' in self.fields and isinstance(self.fields['SpellsCount'], QComboBox):
            self.fields['SpellsCount'].currentIndexChanged.connect(self.update_spell_visibility)
        if 'DbStruct' in self.fields and isinstance(self.fields['DbStruct'], QComboBox):
            self.fields['DbStruct'].currentIndexChanged.connect(self.apply_schema_hints)
        if 'RequiredSkill' in self.fields and isinstance(self.fields['RequiredSkill'], QComboBox):
            self.fields['RequiredSkill'].currentIndexChanged.connect(self.sync_riding_requirement)
        if 'RequiredSkillRank' in self.fields and isinstance(self.fields['RequiredSkillRank'], QLineEdit):
            self.fields['RequiredSkillRank'].textChanged.connect(lambda _=None: self.sync_riding_requirement())
        if 'DbStruct' in self.fields:
            self.set_field_value('DbStruct', '3.3.5(TC2)')
        self.connect_change_highlights()
        self.update_subclass_options()
        self.update_stats_visibility()
        self.update_spell_visibility()
        self.apply_schema_hints()
    
    def update_subclass_options(self):
        subclass_widget = self.fields.get('subclass')
        class_value = self.get_field_value('class') or '0'
        if not isinstance(subclass_widget, QComboBox):
            return
        current = subclass_widget.currentText()
        options = COMBO_OPTIONS.get(f'subclass{class_value}', COMBO_OPTIONS.get('subclass0', []))
        subclass_widget.blockSignals(True)
        subclass_widget.clear()
        subclass_widget.addItems(options)
        if current:
            for i in range(subclass_widget.count()):
                if subclass_widget.itemText(i) == current or subclass_widget.itemText(i).startswith(current.split('-')[0]):
                    subclass_widget.setCurrentIndex(i)
                    break
        subclass_widget.blockSignals(False)

    def ensure_stat_fields(self):
        for i in range(1, 11):
            type_key = f'stat_type{i}'
            value_key = f'stat_value{i}'
            if type_key not in self.fields:
                combo = NoWheelComboBox()
                combo.addItems(COMBO_OPTIONS.get(type_key, COMBO_OPTIONS.get('stat_type1', [])))
                self.fields[type_key] = combo
            if value_key not in self.fields:
                self.fields[value_key] = QLineEdit()

    def update_stats_visibility(self):
        self.ensure_stat_fields()
        count_text = self.get_field_value('StatsCount') or '10'
        try:
            count = int(count_text)
        except Exception:
            count = 10
        for i in range(1, 11):
            type_widget = self.fields.get(f'stat_type{i}')
            value_widget = self.fields.get(f'stat_value{i}')
            visible = i <= count if count >= 0 else True
            if type_widget:
                type_widget.setVisible(visible)
            if value_widget:
                value_widget.setVisible(visible)

    def update_spell_visibility(self):
        count_text = self.get_field_value('SpellsCount') or '5'
        try:
            count = int(count_text)
        except Exception:
            count = 5
        spell_fields = ['spellid', 'spelltrigger', 'spellcharges', 'spellppmRate', 'spellcooldown', 'spellcategory', 'spellcategorycooldown']
        for i in range(1, 6):
            visible = i <= count if count >= 0 else True
            for prefix in spell_fields:
                widget = self.fields.get(f'{prefix}_{i}')
                if widget:
                    widget.setVisible(visible)

    def apply_schema_hints(self):
        dbstruct = self.get_field_value('DbStruct') or '3.3.5(TC2)'
        holiday_widget = self.fields.get('HolidayId')
        flags_extra_widget = self.fields.get('FlagsExtra')
        rep_faction_widget = self.fields.get('RequiredReputationFaction')
        dmg3_fields = [self.fields.get(f'{k}{i}') for i in (3,4,5) for k in ('dmg_min','dmg_max','dmg_type')]

        show_dmg35 = dbstruct.startswith('3.0.')
        show_faction = dbstruct in ('3.2.X', '3.3.X', '3.3.5', '3.3.5(TC2)')
        show_holiday = dbstruct in ('3.3.X', '3.3.5(TC2)')
        show_flags_extra = dbstruct == '3.3.5(TC2)'

        for w in dmg3_fields:
            if w:
                w.setVisible(show_dmg35)
        if holiday_widget:
            holiday_widget.setVisible(show_holiday)
            if isinstance(holiday_widget, QLineEdit):
                holiday_widget.setPlaceholderText(f'{dbstruct} 常见字段')
        if flags_extra_widget:
            flags_extra_widget.setVisible(show_flags_extra)
            if isinstance(flags_extra_widget, QLineEdit):
                flags_extra_widget.setPlaceholderText(f'{dbstruct} 常见 FlagsExtra')
        if rep_faction_widget:
            rep_faction_widget.setVisible(show_faction)
            if isinstance(rep_faction_widget, QComboBox) and rep_faction_widget.count() == 1:
                rep_faction_widget.setEditable(True)
        for key in ['GemProperties', 'DisenchantID', 'RequiredDisenchantSkill', 'TotemCategory', 'ItemLimitCategory']:
            w = self.fields.get(key)
            if isinstance(w, QComboBox):
                w.setEditable(True)

    def show_tools_menu(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('辅助 Tools')
        dlg.resize(360, 260)
        layout = QVBoxLayout(dlg)
        for label, handler in [
            ('Flags辅助', self.show_flags_helper),
            ('FlagsExtra辅助', self.show_flags_extra_helper),
            ('Socket辅助', self.show_socket_helper),
            ('外键查询', self.show_lookup_tools),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked=False, h=handler, d=dlg: (d.accept(), h()))
            layout.addWidget(btn)
        close_btn = QPushButton('关闭 Close')
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec_()

    def show_flags_helper(self):
        current = self.get_field_value('Flags')
        dlg = FlagEditorDialog('Flags 组合器', FLAG_OPTIONS, current, self)
        if dlg.exec_() == QDialog.Accepted:
            self.set_field_value('Flags', dlg.get_value())

    def show_flags_extra_helper(self):
        current = self.get_field_value('FlagsExtra')
        dlg = FlagEditorDialog('FlagsExtra 组合器', FLAG_EXTRA_OPTIONS, current, self)
        if dlg.exec_() == QDialog.Accepted:
            self.set_field_value('FlagsExtra', dlg.get_value())

    def show_socket_helper(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('Socket 辅助')
        dlg.resize(620, 460)
        layout = QVBoxLayout(dlg)
        info = QTextEdit()
        info.setReadOnly(True)
        info.setPlainText("Socket 区说明\n\n- socketColor_1..3: 插槽颜色\n- socketContent_1..3: 插槽内容/占位\n- socketBonus: 插槽奖励\n- GemProperties: 宝石属性\n\n旧工具里这些是成组使用的。当前版本先补结构辅助，保留你现有字段，不做删减。")
        layout.addWidget(info)
        fill_btn = QPushButton('按插槽颜色数量推断补全')
        def _fill():
            count = 0
            for i in range(1,4):
                v = self.get_field_value(f'socketColor_{i}')
                if v not in ('', '0', 'None'):
                    count += 1
                    if self.get_field_value(f'socketContent_{i}') == '':
                        self.set_field_value(f'socketContent_{i}', 0)
            QMessageBox.information(dlg, '完成', f'已检查 {count} 个插槽，并为空内容位补了 0')
        fill_btn.clicked.connect(_fill)
        layout.addWidget(fill_btn)
        close_btn = QPushButton('关闭 Close')
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec_()

    def sync_riding_requirement(self):
        skill = self.get_field_value('RequiredSkill')
        rank = self.get_field_value('RequiredSkillRank')
        if str(skill).split('-',1)[0] == '762':
            self.set_field_value('RequiredRidingRank', rank)
        else:
            self.set_field_value('RequiredRidingRank', '')

    def show_config(self):
        dialog = ConfigDialog(self, self.config)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.get_config()
            self.save_config()
            
            if 'test' in self.config['db']['database']:
                self.status_label.setText("测试服 Test")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_label.setText("正式服 Prod")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.refresh_dynamic_spell_options()
            self.refresh_dynamic_bilingual_options()
    
    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open('r') as f:
                    self.config.update(json.load(f))
            except:
                pass
    
    def save_config(self):
        try:
            with CONFIG_FILE.open('w') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def get_field_value(self, field_name):
        widget = self.fields.get(field_name)
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        elif isinstance(widget, QComboBox):
            return widget.currentText().split('-')[0]
        elif isinstance(widget, QTextEdit):
            return widget.toPlainText().strip()
        return ''
    
    def set_field_value(self, field_name, value):
        widget = self.fields.get(field_name)
        if isinstance(widget, QLineEdit):
            widget.setText(str(value or ''))
        elif isinstance(widget, QComboBox):
            value_str = str(value or '')
            found = False
            for i in range(widget.count()):
                item_text = widget.itemText(i)
                if item_text == value_str or item_text.startswith(value_str + '-'):
                    widget.setCurrentIndex(i)
                    found = True
                    break
            if not found and value_str != '':
                widget.insertItem(0, f"{value_str}-当前值(词典缺失)")
                widget.setCurrentIndex(0)
        elif isinstance(widget, QTextEdit):
            widget.setPlainText(str(value or ''))
    
    def ensure_spell_option(self, field_name, spell_id):
        widget = self.fields.get(field_name)
        if not isinstance(widget, QComboBox):
            return
        spell_str = str(spell_id or '').strip()
        if not spell_str or spell_str == '0':
            return
        for i in range(widget.count()):
            txt = widget.itemText(i)
            if txt == spell_str or txt.startswith(spell_str + '-'):
                label = lookup_spell_label(self.config.get('db', {}), spell_str)
                if label and label != txt:
                    widget.setItemText(i, label)
                return
        label = lookup_spell_label(self.config.get('db', {}), spell_str)
        widget.insertItem(0, label or f"{spell_str}-当前物品法术(词典缺失)")

    def load_item(self):
        entry = self.get_field_value('entry')
        if not entry:
            QMessageBox.warning(self, "警告", "请输入物品ID")
            return
        
        try:
            conn = pymysql.connect(**self.config['db'])
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM item_template WHERE entry = %s", (entry,))
                row = cur.fetchone()
                if not row:
                    QMessageBox.warning(self, "警告", f"未找到物品 {entry}")
                    return
                
                columns = [desc[0] for desc in cur.description]
                item = dict(zip(columns, row))
                try:
                    with conn.cursor() as cur2:
                        cur2.execute("SELECT COALESCE(Name,''), COALESCE(Description,'') FROM item_template_locale WHERE ID=%s AND locale='zhCN'", (entry,))
                        loc = cur2.fetchone()
                        if loc:
                            item['Name_zhCN'] = loc[0]
                            item['Description_zhCN'] = loc[1]
                except Exception:
                    pass

                for i in range(1, 6):
                    self.ensure_spell_option(f'spellid_{i}', item.get(f'spellid_{i}'))
                    self.hydrate_spell_option_from_web(item.get(f'spellid_{i}'))
                
                for field_id, label, category, widget_type in ALL_FIELDS:
                    if field_id in item:
                        self.set_field_value(field_id, item[field_id])

                stat_count = 0
                for i in range(1, 11):
                    if str(item.get(f'stat_type{i}', '0')) not in ('', '0', 'None') or str(item.get(f'stat_value{i}', '0')) not in ('', '0', 'None'):
                        stat_count = i
                if 'StatsCount' in self.fields:
                    self.set_field_value('StatsCount', stat_count)

                spell_count = 0
                for i in range(1, 6):
                    if str(item.get(f'spellid_{i}', '0')) not in ('', '0', 'None'):
                        spell_count = i
                if 'SpellsCount' in self.fields:
                    self.set_field_value('SpellsCount', spell_count)
                self.update_subclass_options()
                self.update_stats_visibility()
                self.update_spell_visibility()
                self.normalize_spell_combo_labels()
                self.refresh_dynamic_bilingual_options()
                self.refresh_local_dictionary_options()
                self.sync_riding_requirement()
                self.apply_schema_hints()
                for f in self.tracked_fields():
                    self.clear_field_highlight(f)
            
            conn.close()
            QMessageBox.information(self, "成功", f"物品 {entry} 读取成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取失败：{e}")
    
    def collect_item_data(self):
        data = {}
        for field_id, label, category, widget_type in ALL_FIELDS:
            data[field_id] = self.get_field_value(field_id)
        return data

    def get_nonempty_item_data(self, include_entry=True):
        data = self.collect_item_data()
        result = {}
        for k, v in data.items():
            if v == '':
                continue
            if k in ('StatsCount', 'SpellsCount', 'DbStruct', 'Name_zhCN', 'Description_zhCN', 'RequiredRidingRank'):
                continue
            if not include_entry and k == 'entry':
                continue
            result[k] = v
        return result

    def show_lookup_tools(self):
        menu = QMenu(self)
        actions = [
            ('ItemSet', 'itemset'),
            ('LockID', 'lockid'),
            ('PageText', 'PageText'),
            ('RequiredReputationFaction', 'RequiredReputationFaction'),
            ('RequiredSpell', 'requiredspell'),
            ('DisenchantID', 'DisenchantID'),
            ('GemProperties', 'GemProperties'),
        ]
        buttons = []
        dlg = QDialog(self)
        dlg.setWindowTitle('外键查询 Lookup')
        dlg.resize(360, 220)
        layout = QVBoxLayout(dlg)
        info = QLabel('选择要查询并回填的字段：')
        layout.addWidget(info)
        for label, field in actions:
            btn = QPushButton(label)
            def _mk(f=field):
                return lambda: self.open_lookup_dialog(f, dlg)
            btn.clicked.connect(_mk(field))
            layout.addWidget(btn)
        close_btn = QPushButton('关闭 Close')
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec_()

    def open_lookup_dialog(self, field_name, parent_dialog=None):
        dlg = LookupDialog(self, self.config['db'], field_name)
        if dlg.exec_() == QDialog.Accepted:
            value = dlg.get_selected_value()
            if value is not None:
                self.set_field_value(field_name, value)
        if parent_dialog is not None:
            parent_dialog.accept()

    def sql_field_order_template(self):
        base_order = [
            'entry','class','subclass','SoundOverrideSubclass','name','displayid','Quality','Flags','FlagsExtra',
            'BuyCount','BuyPrice','SellPrice','InventoryType','AllowableClass','AllowableRace','ItemLevel','RequiredLevel',
            'RequiredSkill','RequiredSkillRank','requiredspell','requiredhonorrank','RequiredCityRank',
            'RequiredReputationFaction','RequiredReputationRank','maxcount','stackable','ContainerSlots',
            'stat_type1','stat_value1','stat_type2','stat_value2','stat_type3','stat_value3','stat_type4','stat_value4','stat_type5','stat_value5',
            'stat_type6','stat_value6','stat_type7','stat_value7','stat_type8','stat_value8','stat_type9','stat_value9','stat_type10','stat_value10',
            'ScalingStatDistribution','ScalingStatValue',
            'dmg_min1','dmg_max1','dmg_type1','dmg_min2','dmg_max2','dmg_type2','dmg_min3','dmg_max3','dmg_type3','dmg_min4','dmg_max4','dmg_type4','dmg_min5','dmg_max5','dmg_type5',
            'armor','holy_res','fire_res','nature_res','frost_res','shadow_res','arcane_res','delay','ammo_type','RangedModRange','block',
            'spellid_1','spelltrigger_1','spellcharges_1','spellppmRate_1','spellcooldown_1','spellcategory_1','spellcategorycooldown_1',
            'spellid_2','spelltrigger_2','spellcharges_2','spellppmRate_2','spellcooldown_2','spellcategory_2','spellcategorycooldown_2',
            'spellid_3','spelltrigger_3','spellcharges_3','spellppmRate_3','spellcooldown_3','spellcategory_3','spellcategorycooldown_3',
            'spellid_4','spelltrigger_4','spellcharges_4','spellppmRate_4','spellcooldown_4','spellcategory_4','spellcategorycooldown_4',
            'spellid_5','spelltrigger_5','spellcharges_5','spellppmRate_5','spellcooldown_5','spellcategory_5','spellcategorycooldown_5',
            'bonding','description','PageText','LanguageID','PageMaterial','startquest','lockid','Material','sheath','RandomProperty','RandomSuffix',
            'block','itemset','MaxDurability','area','Map','BagFamily','TotemCategory','socketColor_1','socketContent_1','socketColor_2','socketContent_2','socketColor_3','socketContent_3','socketBonus','GemProperties',
            'RequiredDisenchantSkill','ArmorDamageModifier','duration','ItemLimitCategory','HolidayId','ScriptName','DisenchantID','FoodType','minMoneyLoot','maxMoneyLoot','VerifiedBuild'
        ]
        return base_order

    def order_sql_data(self, data):
        ordered = {}
        template = self.sql_field_order_template()
        for key in template:
            if key in data:
                ordered[key] = data[key]
        for key, value in data.items():
            if key not in ordered:
                ordered[key] = value
        return ordered

    def schema_allowed_fields(self):
        dbstruct = self.get_field_value('DbStruct') or '3.3.5(TC2)'
        fields = {field_id for field_id, _, _, _ in ALL_FIELDS}
        fields.discard('DbStruct')
        fields.discard('StatsCount')
        fields.discard('SpellsCount')

        if dbstruct != '3.0.X':
            for i in (3, 4, 5):
                fields.discard(f'dmg_min{i}')
                fields.discard(f'dmg_max{i}')
                fields.discard(f'dmg_type{i}')
        if dbstruct not in ('3.2.X', '3.3.X', '3.3.5', '3.3.5(TC2)'):
            fields.discard('RequiredReputationFaction')
        if dbstruct not in ('3.3.X', '3.3.5(TC2)'):
            fields.discard('HolidayId')
        if dbstruct != '3.3.5(TC2)':
            fields.discard('FlagsExtra')
        if dbstruct in ('3.0.X', '3.1.X'):
            fields.discard('RequiredReputationFaction')
            fields.discard('HolidayId')
        if dbstruct == '3.3.5':
            fields.discard('HolidayId')
        return fields

    def schema_filtered_item_data(self, include_entry=True):
        allowed = self.schema_allowed_fields()
        raw = self.get_nonempty_item_data(include_entry=include_entry)
        return {k: v for k, v in raw.items() if k in allowed or (include_entry and k == 'entry')}

    def normalize_sql_value(self, field, value):
        if value is None:
            return ''
        s = str(value).strip()
        return s

    def build_oldtool_header(self, mode):
        entry = self.get_field_value('entry')
        name = self.get_field_value('name')
        dbstruct = self.get_field_value('DbStruct') or '3.3.5(TC2)'
        return f"-- WOWItemMaker {mode}\n-- entry={entry}\n-- name={name}\n-- dbstruct={dbstruct}\n"

    def GetAddSql(self):
        return self.build_insert_sql(replace=False)

    def GetEditSql(self):
        return self.build_update_sql()

    def GetDelSql(self, entry=None):
        entry = entry or self.get_field_value('entry')
        return self.build_oldtool_header('DELETE') + f"DELETE FROM `item_template` WHERE `entry` = {sql_quote(entry)};"

    def GetReplaceSql(self):
        return self.build_insert_sql(replace=True)

    def build_insert_sql(self, replace=False):
        data = self.order_sql_data(self.schema_filtered_item_data(include_entry=True))
        cols = ', '.join(f'`{k}`' for k in data.keys())
        vals = ', '.join(sql_quote(v) for v in data.values())
        verb = 'REPLACE' if replace else 'INSERT'
        return self.build_oldtool_header(verb) + f"{verb} INTO `item_template` (\n  {cols}\n) VALUES (\n  {vals}\n);"

    def build_update_sql(self):
        entry = self.get_field_value('entry')
        if not entry:
            return '-- 缺少 entry，无法生成 UPDATE'
        data = self.order_sql_data(self.schema_filtered_item_data(include_entry=False))
        sets = ',\n  '.join(f"`{k}` = {sql_quote(v)}" for k, v in data.items())
        return self.build_oldtool_header('UPDATE') + f"UPDATE `item_template` SET\n  {sets}\nWHERE `entry` = {sql_quote(entry)};"

    def save_item(self):
        entry = self.get_field_value('entry')
        if not entry:
            QMessageBox.warning(self, "警告", "请输入物品ID")
            return
        if not self.confirm_action_with_summary('保存确认', '将生成保存/替换 SQL，请确认以下关键信息：'):
            return
        sql = self.GetReplaceSql()
        self.sql_text.setPlainText(sql)
        QMessageBox.information(self, "提示", "已按旧工具风格生成保存SQL到SQL页。当前仍不直接写库。")
    
    def delete_item(self):
        entry = self.get_field_value('entry')
        if not entry:
            return
        if QMessageBox.question(self, "确认", f"删除物品 {entry}? 同时会生成DELETE SQL。") == QMessageBox.Yes:
            sql = self.GetDelSql(entry)
            self.sql_text.setPlainText(sql)
            QMessageBox.information(self, "成功", "已按旧工具风格生成 DELETE SQL 到 SQL 页")
    
    def generate_sql(self, sql_type):
        if sql_type == 'INSERT':
            sql = self.GetAddSql()
        elif sql_type == 'UPDATE':
            sql = self.GetEditSql()
        elif sql_type == 'DELETE':
            sql = self.GetDelSql()
        elif sql_type == 'REPLACE':
            sql = self.GetReplaceSql()
        else:
            sql = f"-- Unknown SQL type: {sql_type}"
        self.sql_text.setPlainText(sql)
    
    def show_sql_result_window(self):
        content = self.sql_text.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, '提示', 'SQL页当前为空')
            return
        dlg = SqlResultDialog('SQL结果窗口 FrmGetSql', content, self)
        dlg.exec_()

    def execute_current_sql(self):
        sql = self.sql_text.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, '提示', '请先生成或粘贴 SQL')
            return
        confirm = QMessageBox.question(
            self,
            '确认执行',
            '将对当前数据库执行 SQL。\n\n这会改变数据库状态。是否继续？'
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            conn = pymysql.connect(**self.config['db'])
            with conn.cursor() as cur:
                statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
                logs = []
                total_affected = 0
                for stmt in statements:
                    cur.execute(stmt)
                    affected = getattr(cur, 'rowcount', -1)
                    total_affected += max(affected, 0)
                    logs.append(f'OK | affected={affected} | {stmt[:180]}')
                conn.commit()
            conn.close()
            result = '\n'.join(logs) + f"\n\n总影响行数: {total_affected}"
            SqlResultDialog('执行结果 StateForm', result, self).exec_()
        except Exception as e:
            SqlResultDialog('执行失败 StateForm', f'执行SQL失败：{e}\n\n原SQL:\n{sql}', self).exec_()

    def copy_sql(self):
        QApplication.clipboard().setText(self.sql_text.toPlainText())
        QMessageBox.information(self, "成功", "SQL已复制")
    
    def search_item(self):
        dialog = SearchDialog(self, self.config['db'])
        if dialog.exec_() == QDialog.Accepted:
            entry = dialog.get_selected_entry()
            if entry:
                self.set_field_value('entry', entry)
                self.load_item()

    def clone_item(self):
        source_entry = self.get_field_value('entry')
        if not source_entry:
            QMessageBox.warning(self, "警告", "请先读取一个物品，再套用")
            return
        defaults = {
            'entry': '',
            'name': self.get_field_value('name'),
            'Name_zhCN': self.get_field_value('Name_zhCN'),
            'displayid': self.get_field_value('displayid'),
            'Description_zhCN': self.get_field_value('Description_zhCN'),
        }
        dlg = CloneDialog(self, defaults)
        if dlg.exec_() != QDialog.Accepted:
            return
        values = dlg.get_values()
        if not values.get('entry'):
            QMessageBox.warning(self, "警告", "新物品ID不能为空")
            return
        for k, v in values.items():
            if v != '':
                self.set_field_value(k, v)
        self.sql_text.setPlainText(self.GetAddSql())
        QMessageBox.information(self, "成功", f"已按物品 {source_entry} 套用为新物品 {values.get('entry')}，并生成 INSERT SQL")

    def copy_item(self):
        lines = []
        for field_id, label, category, widget_type in ALL_FIELDS:
            value = self.get_field_value(field_id)
            if value != '':
                lines.append(f"{field_id} = {value}")
        QApplication.clipboard().setText('\n'.join(lines))
        QMessageBox.information(self, "成功", "当前物品信息已复制到剪贴板")

    def show_sql_tools(self):
        self.sql_text.setFocus()
        QMessageBox.information(self, "SQL工具", "SQL页已就绪：GetAddSql / GetEditSql / GetDelSql / GetReplaceSql 均已接入。")

    def build_patch_preflight_report(self):
        out_dir = Path(__file__).parent / 'build_patch'
        db_name = str(self.config.get('db', {}).get('database', 'acore_world_test'))
        env = 'test' if 'test' in db_name else 'release'
        required = [
            out_dir / 'patch-Z.mpq',
            out_dir / 'patch-zhCN-Z.mpq',
            out_dir / f'manifest_{env}.json',
            out_dir / f'version_{env}.json',
            out_dir / f'channel_manifest_{env}.json',
            out_dir / f'channel_version_{env}.json',
            out_dir / f'combined_manifest_{env}.json',
            out_dir / f'combined_version_{env}.json',
        ]
        missing = [p.name for p in required if not p.exists()]
        lines = [f'环境: {env}', f'输出目录: {out_dir}']
        for p in required:
            if p.exists():
                lines.append(f'OK  {p.name}  size={p.stat().st_size}')
            else:
                lines.append(f'MISS {p.name}')
        ok = len(missing) == 0
        if ok:
            lines.append('\n预检结果：通过')
        else:
            lines.append('\n预检结果：失败')
            lines.append('缺失文件：' + ', '.join(missing))
        return ok, '\n'.join(lines)

    def check_patch_preflight(self):
        ok, report = self.build_patch_preflight_report()
        title = '补丁预检通过' if ok else '补丁预检失败'
        SqlResultDialog(title, report, self).exec_()

    def push_patch_to_server(self):
        ok, report = self.build_patch_preflight_report()
        if not ok:
            SqlResultDialog('推送前检查', report, self).exec_()
            return
        out_dir = Path(__file__).parent / 'build_patch'
        patch_root = out_dir / 'patch-Z.mpq'
        patch_zh = out_dir / 'patch-zhCN-Z.mpq'
        db_name = str(self.config.get('db', {}).get('database', 'acore_world_test'))
        env = 'test' if 'test' in db_name else 'release'
        candidates = [
            out_dir / f'manifest_{env}.json',
            out_dir / f'version_{env}.json',
            out_dir / f'root_manifest_{env}.json',
            out_dir / f'root_version_{env}.json',
            out_dir / f'channel_manifest_{env}.json',
            out_dir / f'channel_version_{env}.json',
            out_dir / f'combined_manifest_{env}.json',
            out_dir / f'combined_version_{env}.json',
        ]
        missing = [str(p.name) for p in [patch_root, patch_zh] + candidates if not p.exists()]
        if missing:
            SqlResultDialog('推送前检查', '缺少以下文件，无法推送：\n\n' + '\n'.join(missing), self).exec_()
            return
        reply = QMessageBox.question(
            self,
            '推送补丁',
            f'将把 {env} 环境补丁推送到服务器。\n\n文件包括 MPQ 与 manifest/version。\n\n是否继续？'
        )
        if reply != QMessageBox.Yes:
            return
        try:
            ssh_host = '43.248.129.172'
            ssh_user = 'root'
            ssh_key = '/Users/mac/Desktop/服务器开发素材/cd.pem'
            base_remote_dir = f'/www/wwwroot/wow/patches/{env}'
            root_patch_dir = '/www/wwwroot/wow/patches'
            shared_patch_dir = '/www/wwwroot/wow/patches/shared'
            api_dir = '/www/wwwroot/wow/api/patches'
            api_env_dir = f'/www/wwwroot/wow/api/patches/{env}'
            channel_dir = '/www/wwwroot/wow/patches-channels'
            channel_env_dir = f'/www/wwwroot/wow/patches-channels/{env}'
            channel_shared_dir = '/www/wwwroot/wow/patches-channels/shared'
            uploads = [
                (str(patch_root), f'{base_remote_dir}/patch-Z.mpq'),
                (str(patch_zh), f'{base_remote_dir}/patch-zhCN-Z.mpq'),
                (str(patch_root), f'{root_patch_dir}/patch-Z.mpq'),
                (str(patch_zh), f'{root_patch_dir}/patch-zhCN-Z.mpq'),
                (str(patch_root), f'{shared_patch_dir}/patch-Z.mpq'),
                (str(patch_zh), f'{shared_patch_dir}/patch-zhCN-Z.mpq'),
                (str(out_dir / f'manifest_{env}.json'), f'{api_dir}/manifest.json'),
                (str(out_dir / f'version_{env}.json'), f'{api_dir}/version.json'),
                (str(out_dir / f'manifest_{env}.json'), f'{api_env_dir}/manifest.json'),
                (str(out_dir / f'version_{env}.json'), f'{api_env_dir}/version.json'),
                (str(out_dir / f'channel_manifest_{env}.json'), f'{channel_env_dir}/manifest.json'),
                (str(out_dir / f'channel_version_{env}.json'), f'{channel_env_dir}/version.json'),
                (str(out_dir / f'combined_manifest_{env}.json'), f'{channel_dir}/combined-{env}-manifest.json'),
                (str(out_dir / f'combined_version_{env}.json'), f'{channel_dir}/combined-{env}-version.json'),
                (str(out_dir / f'channel_manifest_{env}.json'), f'{channel_shared_dir}/manifest.json'),
                (str(out_dir / f'channel_version_{env}.json'), f'{channel_shared_dir}/version.json'),
                (str(patch_root), f'{channel_shared_dir}/patch-Z.mpq'),
                (str(patch_zh), f'{channel_shared_dir}/patch-zhCN-Z.mpq'),
            ]
            logs = []
            mkdir_cmd = [
                'ssh', '-i', ssh_key, '-o', 'StrictHostKeyChecking=no',
                f'{ssh_user}@{ssh_host}',
                f'mkdir -p {base_remote_dir} {root_patch_dir} {shared_patch_dir} {api_dir} {api_env_dir} {channel_dir} {channel_env_dir} {channel_shared_dir}'
            ]
            r = subprocess.run(mkdir_cmd, capture_output=True, text=True)
            logs.append('MKDIR rc=' + str(r.returncode))
            if r.stdout.strip(): logs.append(r.stdout.strip())
            if r.stderr.strip(): logs.append(r.stderr.strip())
            for local_path, remote_path in uploads:
                cmd = ['scp', '-i', ssh_key, '-o', 'StrictHostKeyChecking=no', local_path, f'{ssh_user}@{ssh_host}:{remote_path}']
                rr = subprocess.run(cmd, capture_output=True, text=True)
                logs.append(f'SCP rc={rr.returncode} | {Path(local_path).name} -> {remote_path}')
                if rr.stdout.strip(): logs.append(rr.stdout.strip())
                if rr.stderr.strip(): logs.append(rr.stderr.strip())
            SqlResultDialog('推送结果 StateForm', '\n'.join(logs), self).exec_()
        except Exception as e:
            SqlResultDialog('推送失败 StateForm', f'推送补丁失败：{e}', self).exec_()

    def make_question_patch(self):
        reply = QMessageBox.question(
            self,
            '问号补丁',
            '将打开 MPQ 工具并沿用现有补丁链路生成问号补丁。\n\n是否继续？'
        )
        if reply != QMessageBox.Yes:
            return
        self.show_mpq_maker()

    def show_mpq_maker(self):
        dlg = MPQMakerDialog(self, self.config['db'])
        dlg.exec_()

    def show_send_mail(self):
        dlg = SendMailDialog(self, self.config['db'])
        dlg.exec_()

    def show_server_manager(self):
        dlg = PlaceholderDialog("服务器管理 ServerManager", "旧工具存在服务器管理模块。\n\n这一批先补入口。\n下一批可继续补：\n- 测试服 / 正式服切换\n- 连接状态\n- 常用操作入口\n- 状态查看", self)
        dlg.exec_()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("PingFang SC", 12))
    
    icon_path = Path(__file__).parent / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = WOWItemMakerWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open('/tmp/wowitemmaker_crash.log', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())
        raise
