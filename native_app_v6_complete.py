#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诺兰时光物品工具 v3.0 - 完整版
- 配置独立对话框
- 所有138个字段完整支持
- 双语标签
- 中文字体
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
CHINESE_FONT = QFont("PingFang SC", 9)

# 完整字段映射（138个字段）
ALL_FIELDS = [
    # 基础信息
    ("entry", "物品ID Entry", "基础 Basic"),
    ("name", "名称(英) Name", "基础 Basic"),
    ("displayid", "显示ID DisplayID", "基础 Basic"),
    ("Quality", "品质 Quality", "基础 Basic"),
    ("class", "类型 Class", "基础 Basic"),
    ("subclass", "子类型 Subclass", "基础 Basic"),
    ("SoundOverrideSubclass", "声音子类 SoundSub", "基础 Basic"),
    ("Flags", "标志 Flags", "基础 Basic"),
    ("FlagsExtra", "额外标志 FlagsExtra", "基础 Basic"),
    ("BuyCount", "购买数量 BuyCount", "基础 Basic"),
    ("BuyPrice", "购买价格 BuyPrice", "基础 Basic"),
    ("SellPrice", "出售价格 SellPrice", "基础 Basic"),
    ("InventoryType", "装备槽 InvType", "基础 Basic"),
    ("ItemLevel", "物品等级 ItemLevel", "基础 Basic"),
    ("bonding", "绑定类型 Bonding", "基础 Basic"),
    ("description", "描述 Description", "基础 Basic"),
    ("stackable", "堆叠 Stackable", "基础 Basic"),
    ("maxcount", "最大数量 MaxCount", "基础 Basic"),
    ("ContainerSlots", "容器槽 ContainerSlots", "基础 Basic"),
    
    # 需求条件
    ("RequiredLevel", "需要等级 ReqLevel", "需求 Requirements"),
    ("AllowableClass", "允许职业 AllowClass", "需求 Requirements"),
    ("AllowableRace", "允许种族 AllowRace", "需求 Requirements"),
    ("RequiredSkill", "需要技能 ReqSkill", "需求 Requirements"),
    ("RequiredSkillRank", "技能等级 SkillRank", "需求 Requirements"),
    ("requiredspell", "需要法术 ReqSpell", "需求 Requirements"),
    ("requiredhonorrank", "需要荣誉 ReqHonor", "需求 Requirements"),
    ("RequiredCityRank", "城市等级 CityRank", "需求 Requirements"),
    ("RequiredReputationFaction", "声望阵营 RepFaction", "需求 Requirements"),
    ("RequiredReputationRank", "声望等级 RepRank", "需求 Requirements"),
    ("area", "区域 Area", "需求 Requirements"),
    ("Map", "地图 Map", "需求 Requirements"),
    
    # 属性(10组)
    ("stat_type1", "属性1类型 Stat1Type", "属性 Stats"),
    ("stat_value1", "属性1值 Stat1Val", "属性 Stats"),
    ("stat_type2", "属性2类型 Stat2Type", "属性 Stats"),
    ("stat_value2", "属性2值 Stat2Val", "属性 Stats"),
    ("stat_type3", "属性3类型 Stat3Type", "属性 Stats"),
    ("stat_value3", "属性3值 Stat3Val", "属性 Stats"),
    ("stat_type4", "属性4类型 Stat4Type", "属性 Stats"),
    ("stat_value4", "属性4值 Stat4Val", "属性 Stats"),
    ("stat_type5", "属性5类型 Stat5Type", "属性 Stats"),
    ("stat_value5", "属性5值 Stat5Val", "属性 Stats"),
    ("stat_type6", "属性6类型 Stat6Type", "属性 Stats"),
    ("stat_value6", "属性6值 Stat6Val", "属性 Stats"),
    ("stat_type7", "属性7类型 Stat7Type", "属性 Stats"),
    ("stat_value7", "属性7值 Stat7Val", "属性 Stats"),
    ("stat_type8", "属性8类型 Stat8Type", "属性 Stats"),
    ("stat_value8", "属性8值 Stat8Val", "属性 Stats"),
    ("stat_type9", "属性9类型 Stat9Type", "属性 Stats"),
    ("stat_value9", "属性9值 Stat9Val", "属性 Stats"),
    ("stat_type10", "属性10类型 Stat10Type", "属性 Stats"),
    ("stat_value10", "属性10值 Stat10Val", "属性 Stats"),
    ("ScalingStatDistribution", "缩放分布 ScalingDist", "属性 Stats"),
    ("ScalingStatValue", "缩放值 ScalingVal", "属性 Stats"),
    
    # 伤害
    ("dmg_min1", "伤害1最小 Dmg1Min", "伤害 Damage"),
    ("dmg_max1", "伤害1最大 Dmg1Max", "伤害 Damage"),
    ("dmg_type1", "伤害1类型 Dmg1Type", "伤害 Damage"),
    ("dmg_min2", "伤害2最小 Dmg2Min", "伤害 Damage"),
    ("dmg_max2", "伤害2最大 Dmg2Max", "伤害 Damage"),
    ("dmg_type2", "伤害2类型 Dmg2Type", "伤害 Damage"),
    ("armor", "护甲 Armor", "伤害 Damage"),
    ("holy_res", "神圣抗 HolyRes", "伤害 Damage"),
    ("fire_res", "火焰抗 FireRes", "伤害 Damage"),
    ("nature_res", "自然抗 NatureRes", "伤害 Damage"),
    ("frost_res", "冰霜抗 FrostRes", "伤害 Damage"),
    ("shadow_res", "暗影抗 ShadowRes", "伤害 Damage"),
    ("arcane_res", "奥术抗 ArcaneRes", "伤害 Damage"),
    ("delay", "延迟 Delay", "伤害 Damage"),
    ("ammo_type", "弹药类型 AmmoType", "伤害 Damage"),
    ("RangedModRange", "射程 Range", "伤害 Damage"),
    ("block", "格挡 Block", "伤害 Damage"),
    
    # 法术(5组，每组7个字段)
    ("spellid_1", "法术1ID Spell1ID", "法术 Spells"),
    ("spelltrigger_1", "触发1 Trigger1", "法术 Spells"),
    ("spellcharges_1", "次数1 Charges1", "法术 Spells"),
    ("spellppmRate_1", "PPM1 PPMRate1", "法术 Spells"),
    ("spellcooldown_1", "冷却1 Cooldown1", "法术 Spells"),
    ("spellcategory_1", "类别1 Category1", "法术 Spells"),
    ("spellcategorycooldown_1", "类别冷却1 CatCooldown1", "法术 Spells"),
    ("spellid_2", "法术2ID Spell2ID", "法术 Spells"),
    ("spelltrigger_2", "触发2 Trigger2", "法术 Spells"),
    ("spellcharges_2", "次数2 Charges2", "法术 Spells"),
    ("spellppmRate_2", "PPM2 PPMRate2", "法术 Spells"),
    ("spellcooldown_2", "冷却2 Cooldown2", "法术 Spells"),
    ("spellcategory_2", "类别2 Category2", "法术 Spells"),
    ("spellcategorycooldown_2", "类别冷却2 CatCooldown2", "法术 Spells"),
    ("spellid_3", "法术3ID Spell3ID", "法术 Spells"),
    ("spelltrigger_3", "触发3 Trigger3", "法术 Spells"),
    ("spellcharges_3", "次数3 Charges3", "法术 Spells"),
    ("spellppmRate_3", "PPM3 PPMRate3", "法术 Spells"),
    ("spellcooldown_3", "冷却3 Cooldown3", "法术 Spells"),
    ("spellcategory_3", "类别3 Category3", "法术 Spells"),
    ("spellcategorycooldown_3", "类别冷却3 CatCooldown3", "法术 Spells"),
    ("spellid_4", "法术4ID Spell4ID", "法术 Spells"),
    ("spelltrigger_4", "触发4 Trigger4", "法术 Spells"),
    ("spellcharges_4", "次数4 Charges4", "法术 Spells"),
    ("spellppmRate_4", "PPM4 PPMRate4", "法术 Spells"),
    ("spellcooldown_4", "冷却4 Cooldown4", "法术 Spells"),
    ("spellcategory_4", "类别4 Category4", "法术 Spells"),
    ("spellcategorycooldown_4", "类别冷却4 CatCooldown4", "法术 Spells"),
    ("spellid_5", "法术5ID Spell5ID", "法术 Spells"),
    ("spelltrigger_5", "触发5 Trigger5", "法术 Spells"),
    ("spellcharges_5", "次数5 Charges5", "法术 Spells"),
    ("spellppmRate_5", "PPM5 PPMRate5", "法术 Spells"),
    ("spellcooldown_5", "冷却5 Cooldown5", "法术 Spells"),
    ("spellcategory_5", "类别5 Category5", "法术 Spells"),
    ("spellcategorycooldown_5", "类别冷却5 CatCooldown5", "法术 Spells"),
    
    # Socket
    ("socketColor_1", "插槽1颜色 Socket1Color", "Socket"),
    ("socketContent_1", "插槽1内容 Socket1Content", "Socket"),
    ("socketColor_2", "插槽2颜色 Socket2Color", "Socket"),
    ("socketContent_2", "插槽2内容 Socket2Content", "Socket"),
    ("socketColor_3", "插槽3颜色 Socket3Color", "Socket"),
    ("socketContent_3", "插槽3内容 Socket3Content", "Socket"),
    ("socketBonus", "插槽奖励 SocketBonus", "Socket"),
    ("GemProperties", "宝石属性 GemProps", "Socket"),
    
    # 高级
    ("PageText", "页面文本 PageText", "高级 Advanced"),
    ("LanguageID", "语言ID LangID", "高级 Advanced"),
    ("PageMaterial", "页面材质 PageMaterial", "高级 Advanced"),
    ("startquest", "起始任务 StartQuest", "高级 Advanced"),
    ("lockid", "锁ID LockID", "高级 Advanced"),
    ("Material", "材质 Material", "高级 Advanced"),
    ("sheath", "鞘 Sheath", "高级 Advanced"),
    ("RandomProperty", "随机属性 RandomProp", "高级 Advanced"),
    ("RandomSuffix", "随机后缀 RandomSuffix", "高级 Advanced"),
    ("itemset", "物品套装 ItemSet", "高级 Advanced"),
    ("MaxDurability", "耐久度 Durability", "高级 Advanced"),
    ("BagFamily", "背包类别 BagFamily", "高级 Advanced"),
    ("TotemCategory", "图腾类别 TotemCat", "高级 Advanced"),
    ("RequiredDisenchantSkill", "分解技能 Disenchant", "高级 Advanced"),
    ("ArmorDamageModifier", "护甲伤害修正 ArmorDmgMod", "高级 Advanced"),
    ("duration", "持续时间 Duration", "高级 Advanced"),
    ("ItemLimitCategory", "物品限制类别 ItemLimitCat", "高级 Advanced"),
    ("HolidayId", "节日ID HolidayID", "高级 Advanced"),
    ("ScriptName", "脚本名 ScriptName", "高级 Advanced"),
    ("DisenchantID", "分解ID DisenchantID", "高级 Advanced"),
    ("FoodType", "食物类型 FoodType", "高级 Advanced"),
    ("minMoneyLoot", "最小金币 MinMoney", "高级 Advanced"),
    ("maxMoneyLoot", "最大金币 MaxMoney", "高级 Advanced"),
    ("flagsCustom", "自定义标志 CustomFlags", "高级 Advanced"),
    ("VerifiedBuild", "验证版本 VerifiedBuild", "高级 Advanced"),
]


class ConfigDialog(QDialog):
    """配置对话框"""
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("连接配置 / Connection Settings")
        self.setModal(True)
        self.resize(600, 400)
        self.setFont(CHINESE_FONT)
        self.config = config or {}
        
        layout = QVBoxLayout(self)
        
        # 连接模式
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("模式 Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["direct-直连数据库", "remote-SSH转发"])
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)
        
        # SSH配置
        ssh_group = QGroupBox("SSH配置 SSH Settings")
        ssh_layout = QFormLayout(ssh_group)
        self.ssh_host = QLineEdit(self.config.get('ssh', {}).get('host', '43.248.129.172'))
        ssh_layout.addRow("SSH Host:", self.ssh_host)
        self.ssh_user = QLineEdit(self.config.get('ssh', {}).get('user', 'root'))
        ssh_layout.addRow("SSH User:", self.ssh_user)
        self.ssh_key = QLineEdit(self.config.get('ssh', {}).get('keyPath', '/Users/mac/Desktop/cd.pem'))
        ssh_layout.addRow("SSH Key:", self.ssh_key)
        layout.addWidget(ssh_group)
        
        # 数据库配置
        db_group = QGroupBox("数据库配置 Database Settings")
        db_layout = QFormLayout(db_group)
        self.db_host = QLineEdit(self.config.get('db', {}).get('host', '43.248.129.172'))
        db_layout.addRow("DB Host:", self.db_host)
        self.db_port = QLineEdit(str(self.config.get('db', {}).get('port', 3306)))
        db_layout.addRow("DB Port:", self.db_port)
        self.db_user = QLineEdit(self.config.get('db', {}).get('user', 'wowitem'))
        db_layout.addRow("DB User:", self.db_user)
        self.db_password = QLineEdit(self.config.get('db', {}).get('password', 'GknNJLRtcE6RzigVJFF8'))
        self.db_password.setEchoMode(QLineEdit.Password)
        db_layout.addRow("DB Password:", self.db_password)
        self.db_name = QComboBox()
        self.db_name.addItems(["acore_world_test(测试服)", "acore_world(正式服)"])
        db_name = self.config.get('db', {}).get('database', 'acore_world_test')
        self.db_name.setCurrentIndex(0 if 'test' in db_name else 1)
        db_layout.addRow("Database:", self.db_name)
        layout.addWidget(db_group)
        
        # 选项
        options_layout = QHBoxLayout()
        self.save_password = QCheckBox("保存密码 Save Password")
        self.save_password.setChecked(self.config.get('savePassword', True))
        options_layout.addWidget(self.save_password)
        layout.addLayout(options_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        test_btn = QPushButton("测试连接 Test")
        test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(test_btn)
        
        ok_btn = QPushButton("确定 OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消 Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
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
            QMessageBox.information(self, "成功", "连接成功！")
        except Exception as e:
            QMessageBox.critical(self, "失败", f"连接失败：{e}")
    
    def get_config(self):
        return {
            'mode': 'direct' if self.mode_combo.currentIndex() == 0 else 'remote',
            'ssh': {
                'host': self.ssh_host.text(),
                'user': self.ssh_user.text(),
                'keyPath': self.ssh_key.text(),
            },
            'db': {
                'host': self.db_host.text(),
                'port': int(self.db_port.text()),
                'user': self.db_user.text(),
                'password': self.db_password.text(),
                'database': self.db_name.currentText().split('(')[0],
            },
            'savePassword': self.save_password.isChecked(),
        }


class SearchDialog(QDialog):
    """搜索对话框"""
    def __init__(self, parent=None, db_config=None):
        super().__init__(parent)
        self.setWindowTitle("搜索物品 / Search Items")
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
            QMessageBox.critical(self, "错误", f"搜索失败：{e}")
    
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
        self.setWindowTitle("诺兰时光物品工具 v3.0 / WOWItemMaker")
        self.setGeometry(50, 50, 2200, 1300)
        self.setFont(CHINESE_FONT)
        
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self.config = {
            "mode": "direct",
            "db": {
                "host": "43.248.129.172",
                "port": 3306,
                "user": "wowitem",
                "password": "GknNJLRtcE6RzigVJFF8",
                "database": "acore_world_test"
            },
            "ssh": {"host": "43.248.129.172", "user": "root", "keyPath": "/Users/mac/Desktop/cd.pem"},
            "savePassword": True
        }
        
        self.fields = {}
        self.create_ui()
        self.load_config()
    
    def create_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 顶部工具栏（简洁）
        toolbar = QHBoxLayout()
        
        # Entry和基本操作
        toolbar.addWidget(QLabel("物品ID:"))
        self.fields['entry'] = QLineEdit()
        self.fields['entry'].setMaximumWidth(120)
        toolbar.addWidget(self.fields['entry'])
        
        load_btn = QPushButton("读取")
        load_btn.clicked.connect(self.load_item)
        toolbar.addWidget(load_btn)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_item)
        toolbar.addWidget(save_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        delete_btn.clicked.connect(self.delete_item)
        toolbar.addWidget(delete_btn)
        
        toolbar.addSpacing(20)
        
        search_btn = QPushButton("🔍搜索")
        search_btn.clicked.connect(self.search_item)
        toolbar.addWidget(search_btn)
        
        clone_btn = QPushButton("📋套用")
        clone_btn.clicked.connect(self.clone_item)
        toolbar.addWidget(clone_btn)
        
        toolbar.addStretch()
        
        # 环境状态
        self.status_label = QLabel("测试服 Test")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        toolbar.addWidget(self.status_label)
        
        # 配置按钮
        config_btn = QPushButton("⚙️配置")
        config_btn.clicked.connect(self.show_config)
        toolbar.addWidget(config_btn)
        
        layout.addLayout(toolbar)
        
        # 中间：分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：基础信息
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：详细选项卡
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([600, 1600])
        layout.addWidget(splitter)
    
    def create_left_panel(self):
        """左侧：基础信息"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        widget.setFont(CHINESE_FONT)
        layout = QVBoxLayout(widget)
        
        # 基础信息组
        basic_group = QGroupBox("基本信息 / Basic Info")
        basic_layout = QGridLayout(basic_group)
        
        basic_fields = [
            ("name", "名称(英) Name"),
            ("displayid", "显示ID DisplayID"),
            ("Quality", "品质 Quality"),
            ("class", "类型 Class"),
            ("subclass", "子类型 Subclass"),
            ("SoundOverrideSubclass", "声音子类 SoundSub"),
            ("ItemLevel", "物品等级 ItemLevel"),
            ("bonding", "绑定类型 Bonding"),
            ("BuyCount", "购买数量 BuyCount"),
            ("BuyPrice", "购买价格 BuyPrice"),
            ("SellPrice", "出售价格 SellPrice"),
            ("stackable", "堆叠 Stackable"),
            ("maxcount", "最大数量 MaxCount"),
            ("ContainerSlots", "容器槽 ContainerSlots"),
            ("InventoryType", "装备槽 InvType"),
            ("Material", "材质 Material"),
            ("sheath", "鞘 Sheath"),
        ]
        
        row = 0
        for field_id, label in basic_fields:
            basic_layout.addWidget(QLabel(label), row, 0)
            if field_id in ['Quality', 'class', 'subclass', 'bonding', 'InventoryType', 'Material']:
                self.fields[field_id] = QComboBox()
                if field_id == 'Quality':
                    self.fields[field_id].addItems(["0-垃圾", "1-普通", "2-优秀", "3-精良", "4-史诗", "5-传说", "6-神器"])
                elif field_id == 'bonding':
                    self.fields[field_id].addItems(["0-不绑定", "1-拾取绑定", "2-装备绑定", "3-使用绑定", "4-任务"])
            else:
                self.fields[field_id] = QLineEdit()
            basic_layout.addWidget(self.fields[field_id], row, 1)
            row += 1
        
        layout.addWidget(basic_group)
        
        # 描述
        desc_group = QGroupBox("描述 / Description")
        desc_layout = QVBoxLayout(desc_group)
        self.fields['description'] = QTextEdit()
        self.fields['description'].setMaximumHeight(80)
        desc_layout.addWidget(self.fields['description'])
        layout.addWidget(desc_group)
        
        # 标志
        flags_group = QGroupBox("标志 / Flags")
        flags_layout = QGridLayout(flags_group)
        for field_id, label in [("Flags", "标志 Flags"), ("FlagsExtra", "额外标志 FlagsExtra")]:
            row = 0 if field_id == "Flags" else 1
            flags_layout.addWidget(QLabel(label), row, 0)
            self.fields[field_id] = QLineEdit()
            flags_layout.addWidget(self.fields[field_id], row, 1)
        layout.addWidget(flags_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_right_panel(self):
        """右侧：详细选项卡"""
        tabs = QTabWidget()
        tabs.setFont(CHINESE_FONT)
        
        # 需求选项卡
        req_tab = self.create_tab("需求 Requirements", "需求 Requirements")
        tabs.addTab(req_tab, "需求 Req")
        
        # 属性选项卡
        stats_tab = self.create_tab("属性 Stats", "属性 Stats")
        tabs.addTab(stats_tab, "属性 Stats")
        
        # 伤害选项卡
        damage_tab = self.create_tab("伤害 Damage", "伤害 Damage")
        tabs.addTab(damage_tab, "伤害 Damage")
        
        # 法术选项卡
        spells_tab = self.create_tab("法术 Spells", "法术 Spells")
        tabs.addTab(spells_tab, "法术 Spells")
        
        # Socket选项卡
        socket_tab = self.create_tab("Socket", "Socket")
        tabs.addTab(socket_tab, "Socket")
        
        # 高级选项卡
        adv_tab = self.create_tab("高级 Advanced", "高级 Advanced")
        tabs.addTab(adv_tab, "高级 Adv")
        
        # SQL选项卡
        sql_tab = QWidget()
        sql_layout = QVBoxLayout(sql_tab)
        self.sql_text = QTextEdit()
        self.sql_text.setFont(QFont("Monaco", 10))
        sql_layout.addWidget(self.sql_text)
        
        btn_layout = QHBoxLayout()
        for label, action in [("生成INSERT", "INSERT"), ("生成UPDATE", "UPDATE"), ("生成DELETE", "DELETE")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, a=action: self.generate_sql(a))
            btn_layout.addWidget(btn)
        
        copy_btn = QPushButton("复制SQL")
        copy_btn.clicked.connect(self.copy_sql)
        btn_layout.addWidget(copy_btn)
        
        sql_layout.addLayout(btn_layout)
        tabs.addTab(sql_tab, "SQL")
        
        return tabs
    
    def create_tab(self, group_name, category):
        """创建选项卡"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        widget.setFont(CHINESE_FONT)
        layout = QVBoxLayout(widget)
        
        group = QGroupBox(group_name)
        grid = QGridLayout(group)
        
        row = 0
        col = 0
        for field_id, label, cat in ALL_FIELDS:
            if cat != category:
                continue
            
            grid.addWidget(QLabel(label), row, col)
            self.fields[field_id] = QLineEdit()
            grid.addWidget(self.fields[field_id], row, col + 1)
            
            row += 1
            if row > 20:  # 每20个字段换列
                row = 0
                col += 2
        
        layout.addWidget(group)
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def show_config(self):
        """显示配置对话框"""
        dialog = ConfigDialog(self, self.config)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.get_config()
            self.save_config()
            
            # 更新状态
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
                
                # 填充所有字段
                for field_id, label, cat in ALL_FIELDS:
                    if field_id in item:
                        self.set_field_value(field_id, item[field_id])
                
                # 读取中文名
                cur.execute("SELECT Name, Description FROM item_template_locale WHERE ID = %s AND locale = 'zhCN'", (entry,))
                locale_row = cur.fetchone()
                if locale_row:
                    # 如果有中文名，替换英文名显示
                    pass
            
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
    app.setFont(QFont("PingFang SC", 10))
    
    icon_path = Path(__file__).parent / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = WOWItemMakerWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
