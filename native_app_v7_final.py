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
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QGroupBox,
    QGridLayout, QMessageBox, QSplitter, QFrame, QScrollArea, QTabWidget,
    QDialog, QFormLayout, QListWidget, QListWidgetItem, QCheckBox
)
from PyQt5.QtGui import QFont, QIcon
import pymysql

CONFIG_FILE = Path(__file__).parent / 'conninfo.json'
CHINESE_FONT = QFont("PingFang SC", 12)  # 字体增大到12
UI_FONT = QFont("SF Pro Display", 12)

# 下拉菜单选项定义
COMBO_OPTIONS = {
    'Quality': ["0-垃圾Gray", "1-普通White", "2-优秀Green", "3-精良Blue", "4-史诗Purple", "5-传说Orange", "6-神器Yellow", "7-传家宝Heirloom"],
    'class': ["0-消耗品Consumable", "1-容器Container", "2-武器Weapon", "3-宝石Gem", "4-护甲Armor", "5-材料Reagent", "6-弹药Projectile", "7-商品Tradegoods", "8-配方Recipe", "9-钱币Money", "10-任务Quest", "11-钥匙Key", "12-永久Permanent", "13-垃圾Junk"],
    'subclass': ["0-通用None", "1-斧Axe", "2-弓Bow", "3-枪Gun", "4-锤Mace", "5-杖Polearm", "6-剑Sword", "7-法杖Staff", "8-匕首Dagger", "9-拳套Fist", "10-盾Shield", "11-法杖Wand", "12-弩Crossbow", "13-魔杖Wand", "14-鱼竿Fishing"],
    'bonding': ["0-不绑定None", "1-拾取绑定OnAcquire", "2-装备绑定OnEquip", "3-使用绑定OnUse", "4-任务Quest", "5-账号Account"],
    'InventoryType': ["0-非装备None", "1-头部Head", "2-颈部Neck", "3-肩部Shoulders", "4-衬衫Shirt", "5-胸甲Chest", "6-腰带Waist", "7-腿部Legs", "8-脚Feet", "9-手腕Wrists", "10-手套Hands", "11-手指Finger", "12-饰品Trinket", "13-单手OneHand", "14-盾Shield", "15-弓Ranged", "16-背部Back", "17-双手TwoHand", "18-袋子Bag", "19-徽章Tabard", "20-法袍Robe", "21-主手MainHand", "22-副手OffHand", "23-箭Ammo", "24-子弹Quiver"],
    'Material': ["0-无None", "1-金属Metal", "2-木材Wood", "3-液体Liquid", "4-珠宝Jewelry", "5-链甲Chain", "6-板甲Plate", "7-布甲Cloth", "8-皮革Leather"],
    'sheath': ["0-无None", "1-大型盾牌LargeShield", "2-背包Bags", "3-法杖Staff", "4-盾牌Shield", "5-副手OffHand", "6-大型武器LargeWeapon", "7-中型武器MediumWeapon", "8-小型武器SmallWeapon", "9-弩Crossbow", "10-法杖Wand", "11-弓Bow"],
    'stat_type1': ["0-无None", "1-力量Strength", "2-敏捷Agility", "3-耐力Stamina", "4-智力Intellect", "5-精神Spirit", "6-攻击强度AttackPower", "7-法术强度SpellPower", "18-护甲穿透ArmorPen", "19-格挡BlockRating", "20-精准DodgeRating", "21-躲闪ParryRating", "22-招架DefenseSkill", "23-五秒回蓝ManaRegen", "24-法术穿透SpellPen"],
    'dmg_type1': ["0-物理Physical", "1-神圣Holy", "2-火焰Fire", "3-自然Nature", "4-冰霜Frost", "5-暗影Shadow", "6-奥术Arcane"],
    'spelltrigger_1': ["0-使用OnUse", "1-装备OnEquip", "2-被动Passive", "3-击中OnHit", "4-使用无消耗OnUseNoCharge", "5-使用失败OnFail"],
    'socketColor_1': ["0-无None", "1-红色Red", "2-黄色Yellow", "4-蓝色Blue", "8-多彩Meta", "14-棱镜Prismatic"],
    'BagFamily': ["0-无None", "1-箭袋Quiver", "2-弹药袋AmmoPouch", "3-灵魂碎片袋SoulShard", "4-皮革袋Leatherworking", "5-草药袋Herbalism", "6-附魔袋Enchanting", "7-工程袋Engineering", "8-钥匙袋Keyring", "9-宝石袋Gems", "10-矿石袋Mining", "11-暗月卡片DarkmoonCards", "12-垃圾Junk"],
}

# 完整字段映射
ALL_FIELDS = [
    # 基础信息
    ("entry", "物品ID Entry", "基础 Basic", "text"),
    ("name", "名称 Name", "基础 Basic", "text"),
    ("displayid", "显示ID DisplayID", "基础 Basic", "text"),
    ("Quality", "品质 Quality", "基础 Basic", "combo"),
    ("class", "类型 Class", "基础 Basic", "combo"),
    ("subclass", "子类型 Subclass", "基础 Basic", "combo"),
    ("SoundOverrideSubclass", "声音子类 Sound", "基础 Basic", "text"),
    ("Flags", "标志 Flags", "基础 Basic", "text"),
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
    
    # 需求
    ("RequiredLevel", "需要等级 ReqLvl", "需求 Requirements", "text"),
    ("AllowableClass", "允许职业 AllowClass", "需求 Requirements", "text"),
    ("AllowableRace", "允许种族 AllowRace", "需求 Requirements", "text"),
    ("RequiredSkill", "需要技能 ReqSkill", "需求 Requirements", "text"),
    ("RequiredSkillRank", "技能等级 SkillRank", "需求 Requirements", "text"),
    ("requiredspell", "需要法术 ReqSpell", "需求 Requirements", "text"),
    ("requiredhonorrank", "需要荣誉 ReqHonor", "需求 Requirements", "text"),
    ("RequiredCityRank", "城市等级 CityRank", "需求 Requirements", "text"),
    ("RequiredReputationFaction", "声望阵营 RepFac", "需求 Requirements", "text"),
    ("RequiredReputationRank", "声望等级 RepRank", "需求 Requirements", "text"),
    ("area", "区域 Area", "需求 Requirements", "text"),
    ("Map", "地图 Map", "需求 Requirements", "text"),
    
    # 属性
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
    ("armor", "护甲 Armor", "伤害 Damage", "text"),
    ("holy_res", "神圣抗 HolyRes", "伤害 Damage", "text"),
    ("fire_res", "火焰抗 FireRes", "伤害 Damage", "text"),
    ("nature_res", "自然抗 NatureRes", "伤害 Damage", "text"),
    ("frost_res", "冰霜抗 FrostRes", "伤害 Damage", "text"),
    ("shadow_res", "暗影抗 ShadowRes", "伤害 Damage", "text"),
    ("arcane_res", "奥术抗 ArcaneRes", "伤害 Damage", "text"),
    ("delay", "延迟 Delay", "伤害 Damage", "text"),
    ("ammo_type", "弹药类型 Ammo", "伤害 Damage", "text"),
    ("RangedModRange", "射程 Range", "伤害 Damage", "text"),
    ("block", "格挡 Block", "伤害 Damage", "text"),
    
    # 法术（简化为每个法术单独选项卡）
    ("spellid_1", "法术1ID Spell1", "法术1 Spell1", "text"),
    ("spelltrigger_1", "触发1 Trigger1", "法术1 Spell1", "combo"),
    ("spellcharges_1", "次数1 Charges1", "法术1 Spell1", "text"),
    ("spellppmRate_1", "PPM1 PPM1", "法术1 Spell1", "text"),
    ("spellcooldown_1", "冷却1 CD1", "法术1 Spell1", "text"),
    ("spellcategory_1", "类别1 Cat1", "法术1 Spell1", "text"),
    ("spellcategorycooldown_1", "类别冷却1 CatCD1", "法术1 Spell1", "text"),
    
    ("spellid_2", "法术2ID Spell2", "法术2 Spell2", "text"),
    ("spelltrigger_2", "触发2 Trigger2", "法术2 Spell2", "combo"),
    ("spellcharges_2", "次数2 Charges2", "法术2 Spell2", "text"),
    ("spellppmRate_2", "PPM2 PPM2", "法术2 Spell2", "text"),
    ("spellcooldown_2", "冷却2 CD2", "法术2 Spell2", "text"),
    ("spellcategory_2", "类别2 Cat2", "法术2 Spell2", "text"),
    ("spellcategorycooldown_2", "类别冷却2 CatCD2", "法术2 Spell2", "text"),
    
    ("spellid_3", "法术3ID Spell3", "法术3 Spell3", "text"),
    ("spelltrigger_3", "触发3 Trigger3", "法术3 Spell3", "combo"),
    ("spellcharges_3", "次数3 Charges3", "法术3 Spell3", "text"),
    ("spellppmRate_3", "PPM3 PPM3", "法术3 Spell3", "text"),
    ("spellcooldown_3", "冷却3 CD3", "法术3 Spell3", "text"),
    ("spellcategory_3", "类别3 Cat3", "法术3 Spell3", "text"),
    ("spellcategorycooldown_3", "类别冷却3 CatCD3", "法术3 Spell3", "text"),
    
    ("spellid_4", "法术4ID Spell4", "法术4 Spell4", "text"),
    ("spelltrigger_4", "触发4 Trigger4", "法术4 Spell4", "combo"),
    ("spellcharges_4", "次数4 Charges4", "法术4 Spell4", "text"),
    ("spellppmRate_4", "PPM4 PPM4", "法术4 Spell4", "text"),
    ("spellcooldown_4", "冷却4 CD4", "法术4 Spell4", "text"),
    ("spellcategory_4", "类别4 Cat4", "法术4 Spell4", "text"),
    ("spellcategorycooldown_4", "类别冷却4 CatCD4", "法术4 Spell4", "text"),
    
    ("spellid_5", "法术5ID Spell5", "法术5 Spell5", "text"),
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
    ("socketBonus", "插槽奖励 Bonus", "Socket", "text"),
    ("GemProperties", "宝石属性 GemProps", "Socket", "text"),
    ("RandomProperty", "随机属性 RandomProp", "Socket", "text"),
    ("RandomSuffix", "随机后缀 RandomSuffix", "Socket", "text"),
    
    # 高级
    ("PageText", "页面文本 PageText", "高级 Advanced", "text"),
    ("LanguageID", "语言ID LangID", "高级 Advanced", "text"),
    ("PageMaterial", "页面材质 PageMat", "高级 Advanced", "text"),
    ("startquest", "起始任务 StartQuest", "高级 Advanced", "text"),
    ("lockid", "锁ID LockID", "高级 Advanced", "text"),
    ("itemset", "物品套装 ItemSet", "高级 Advanced", "text"),
    ("MaxDurability", "耐久度 Durability", "高级 Advanced", "text"),
    ("BagFamily", "背包类别 BagFamily", "高级 Advanced", "combo"),
    ("TotemCategory", "图腾类别 TotemCat", "高级 Advanced", "text"),
    ("RequiredDisenchantSkill", "分解技能 Disenchant", "高级 Advanced", "text"),
    ("ArmorDamageModifier", "护甲伤害修正 ArmorDmg", "高级 Advanced", "text"),
    ("duration", "持续时间 Duration", "高级 Advanced", "text"),
    ("ItemLimitCategory", "物品限制类别 ItemLimit", "高级 Advanced", "text"),
    ("HolidayId", "节日ID HolidayID", "高级 Advanced", "text"),
    ("ScriptName", "脚本名 ScriptName", "高级 Advanced", "text"),
    ("DisenchantID", "分解ID DisenchantID", "高级 Advanced", "text"),
    ("FoodType", "食物类型 FoodType", "高级 Advanced", "text"),
    ("minMoneyLoot", "最小金币 MinMoney", "高级 Advanced", "text"),
    ("maxMoneyLoot", "最大金币 MaxMoney", "高级 Advanced", "text"),
    ("flagsCustom", "自定义标志 CustomFlags", "高级 Advanced", "text"),
    ("VerifiedBuild", "验证版本 VerifiedBuild", "高级 Advanced", "text"),
]


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
        
        self.db_name = QComboBox()
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
                sql = """SELECT DISTINCT t.entry, t.name, l.Name as name_zh, t.Quality 
                         FROM item_template t
                         LEFT JOIN item_template_locale l ON t.entry = l.ID AND l.locale = 'zhCN'
                         WHERE t.entry LIKE %s OR t.name LIKE %s OR l.Name LIKE %s
                         LIMIT 100"""
                pattern = f"%{keyword}%"
                cur.execute(sql, (pattern, pattern, pattern))
                rows = cur.fetchall()
                self.results.clear()
                for row in rows:
                    entry, name_en, name_zh, quality = row
                    quality_names = ["垃圾", "普通", "优秀", "精良", "史诗", "传说", "神器"]
                    quality_name = quality_names[quality] if 0 <= quality < len(quality_names) else str(quality)
                    display_name = f"{name_zh or name_en}"
                    if name_zh and name_zh != name_en:
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
                self.fields[field_id] = QComboBox()
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
                    self.fields[field_id] = QComboBox()
                    # 处理 stat_type 和 spelltrigger 的通用选项
                    if 'stat_type' in field_id:
                        options = COMBO_OPTIONS['stat_type1']
                    elif 'spelltrigger' in field_id:
                        options = COMBO_OPTIONS['spelltrigger_1']
                    elif 'dmg_type' in field_id:
                        options = COMBO_OPTIONS['dmg_type1']
                    elif 'socketColor' in field_id:
                        options = COMBO_OPTIONS['socketColor_1']
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
        for label, action in [("生成INSERT", "INSERT"), ("生成UPDATE", "UPDATE"), ("生成DELETE", "DELETE")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, a=action: self.generate_sql(a))
            btn_layout.addWidget(btn)
        
        copy_btn = QPushButton("复制 Copy")
        copy_btn.clicked.connect(self.copy_sql)
        btn_layout.addWidget(copy_btn)
        
        sql_layout.addLayout(btn_layout)
        tabs.addTab(sql_widget, "SQL")
        
        splitter.addWidget(tabs)
        splitter.setSizes([600, 1600])
        layout.addWidget(splitter)
    
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
            for i in range(widget.count()):
                if widget.itemText(i).startswith(str(value)):
                    widget.setCurrentIndex(i)
                    break
        elif isinstance(widget, QTextEdit):
            widget.setPlainText(str(value or ''))
    
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
                
                for field_id, label, category, widget_type in ALL_FIELDS:
                    if field_id in item:
                        self.set_field_value(field_id, item[field_id])
            
            conn.close()
            QMessageBox.information(self, "成功", f"物品 {entry} 读取成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取失败：{e}")
    
    def save_item(self):
        QMessageBox.information(self, "提示", "保存功能开发中...")
    
    def delete_item(self):
        entry = self.get_field_value('entry')
        if not entry:
            return
        if QMessageBox.question(self, "确认", f"删除物品 {entry}?") == QMessageBox.Yes:
            try:
                conn = pymysql.connect(**self.config['db'])
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM item_template WHERE entry = %s", (entry,))
                    conn.commit()
                conn.close()
                QMessageBox.information(self, "成功", "删除成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败：{e}")
    
    def generate_sql(self, sql_type):
        entry = self.get_field_value('entry')
        name = self.get_field_value('name')
        sql = f"-- SQL {sql_type} for entry={entry}, name={name}"
        self.sql_text.setPlainText(sql)
    
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
        QMessageBox.information(self, "提示", "套用功能开发中...")


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
    main()
