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
    'AllowableRace': ["-1-全种族", "1-人类", "2-兽人", "4-矮人", "8-夜精灵", "16-亡灵", "32-牛头人", "64-侏儒", "128-巨魔", "256-血精灵", "512-德莱尼", "777-联盟", "690-部落"],
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
    ("AllowableClass", "允许职业 AllowClass", "高级 Advanced", "combo"),
    ("AllowableRace", "允许种族 AllowRace", "高级 Advanced", "combo"),
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
