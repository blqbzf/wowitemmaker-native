#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诺兰时光物品工具 - 原生桌面版 v2.5
完整修复版 - 中文字体 + 双语标签 + 完整字段
"""

import sys
import json
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QGroupBox,
    QGridLayout, QMessageBox, QSplitter, QFrame, QScrollArea, QTabWidget,
    QDialog, QFormLayout, QListWidget, QListWidgetItem, QCheckBox, QSpinBox
)
from PyQt5.QtGui import QFont, QIcon
import pymysql

CONFIG_FILE = Path(__file__).parent / 'conninfo.json'

# 设置支持中文的字体
CHINESE_FONT = QFont("PingFang SC", 10)  # macOS中文字体
UI_FONT = QFont("SF Pro Display", 10)  # UI字体

class SearchItemDialog(QDialog):
    """搜索物品对话框"""
    def __init__(self, parent=None, db_config=None):
        super().__init__(parent)
        self.setWindowTitle("搜索物品 / Search Items")
        self.setModal(True)
        self.resize(800, 600)
        self.db_config = db_config or {}
        self.setFont(CHINESE_FONT)
        
        layout = QVBoxLayout(self)
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("关键词 Keyword:"))
        self.keyword = QLineEdit()
        self.keyword.setPlaceholderText("输入物品ID或名称（支持中英文）")
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
            QMessageBox.warning(self, "提示", "请输入搜索关键词")
            return
        if not self.db_config:
            QMessageBox.critical(self, "错误", "数据库配置未设置")
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
                if not rows:
                    QMessageBox.information(self, "提示", "没有找到匹配的物品")
                    return
                for row in rows:
                    entry, name_en, name_zh, quality = row
                    quality_names = ["垃圾Garbage", "普通Common", "优秀Uncommon", "精良Rare", "史诗Epic", "传说Legendary", "神器Artifact"]
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
        self.setWindowTitle("诺兰时光物品工具 v2.5 / WOWItemMaker")
        self.setGeometry(100, 100, 2000, 1200)
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
            "ssh": {"host": "43.248.129.172", "user": "root", "keyPath": "/Users/mac/Desktop/cd.pem", "password": ""},
            "saveConfig": True,
            "savePassword": True
        }
        
        self.fields = {}
        self.create_ui()
        self.load_config()
    
    def create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部配置
        top_frame = self.create_top_panel()
        main_layout.addWidget(top_frame)
        
        # 中间分割器
        splitter = QSplitter(Qt.Horizontal)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([800, 1200])
        main_layout.addWidget(splitter)
        
        # 底部操作
        bottom_frame = self.create_bottom_panel()
        main_layout.addWidget(bottom_frame)
    
    def create_top_panel(self):
        """创建顶部配置面板"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setFont(CHINESE_FONT)
        layout = QVBoxLayout(frame)
        
        # 配置区域
        config_group = QGroupBox("连接配置 / Connection Settings")
        config_layout = QGridLayout(config_group)
        
        # 第一行
        config_layout.addWidget(QLabel("模式 Mode:"), 0, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["remote-SSH转发", "direct-直连"])
        config_layout.addWidget(self.mode_combo, 0, 1)
        
        config_layout.addWidget(QLabel("SSH Host:"), 0, 2)
        self.ssh_host = QLineEdit("43.248.129.172")
        config_layout.addWidget(self.ssh_host, 0, 3)
        
        config_layout.addWidget(QLabel("SSH User:"), 0, 4)
        self.ssh_user = QLineEdit("root")
        config_layout.addWidget(self.ssh_user, 0, 5)
        
        # 第二行
        config_layout.addWidget(QLabel("SSH Key:"), 1, 0)
        self.ssh_key_path = QLineEdit("/Users/mac/Desktop/cd.pem")
        config_layout.addWidget(self.ssh_key_path, 1, 1)
        
        config_layout.addWidget(QLabel("DB Host:"), 1, 2)
        self.db_host = QLineEdit("43.248.129.172")
        config_layout.addWidget(self.db_host, 1, 3)
        
        config_layout.addWidget(QLabel("DB Port:"), 1, 4)
        self.db_port = QLineEdit("3306")
        config_layout.addWidget(self.db_port, 1, 5)
        
        # 第三行
        config_layout.addWidget(QLabel("DB User:"), 2, 0)
        self.db_user = QLineEdit("wowitem")
        config_layout.addWidget(self.db_user, 2, 1)
        
        config_layout.addWidget(QLabel("DB Password:"), 2, 2)
        self.db_password = QLineEdit("GknNJLRtcE6RzigVJFF8")
        self.db_password.setEchoMode(QLineEdit.Password)
        config_layout.addWidget(self.db_password, 2, 3)
        
        config_layout.addWidget(QLabel("Database:"), 2, 4)
        self.db_combo = QComboBox()
        self.db_combo.addItems(["acore_world_test(测试服)", "acore_world(正式服)"])
        config_layout.addWidget(self.db_combo, 2, 5)
        
        layout.addWidget(config_group)
        
        # 按钮行
        btn_layout = QHBoxLayout()
        
        read_config_btn = QPushButton("读取配置 Load")
        read_config_btn.clicked.connect(self.load_config_from_file)
        btn_layout.addWidget(read_config_btn)
        
        save_config_btn = QPushButton("保存配置 Save")
        save_config_btn.clicked.connect(self.save_config_to_file)
        btn_layout.addWidget(save_config_btn)
        
        self.save_password_check = QCheckBox("保存密码 Save Pwd")
        self.save_password_check.setChecked(True)
        btn_layout.addWidget(self.save_password_check)
        
        btn_layout.addStretch()
        
        self.status_label = QLabel("状态: 测试服 Test")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        btn_layout.addWidget(self.status_label)
        
        test_btn = QPushButton("连接数据库 Connect")
        test_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        test_btn.clicked.connect(self.test_connection)
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return frame
    
    def create_left_panel(self):
        """左侧：基础字段"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        widget.setFont(CHINESE_FONT)
        layout = QVBoxLayout(widget)
        
        # Entry
        entry_group = QGroupBox("物品编号 / Item Entry")
        entry_layout = QHBoxLayout(entry_group)
        self.fields['entry'] = QLineEdit()
        self.fields['entry'].setPlaceholderText("输入物品ID")
        entry_layout.addWidget(self.fields['entry'])
        
        read_btn = QPushButton("读取 Load")
        read_btn.clicked.connect(self.load_item)
        entry_layout.addWidget(read_btn)
        
        save_btn = QPushButton("保存 Save")
        save_btn.clicked.connect(self.save_item)
        entry_layout.addWidget(save_btn)
        
        delete_btn = QPushButton("删除 Delete")
        delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        delete_btn.clicked.connect(self.delete_item)
        entry_layout.addWidget(delete_btn)
        
        layout.addWidget(entry_group)
        
        # 基本信息
        basic_group = QGroupBox("基本信息 / Basic Info")
        basic_layout = QGridLayout(basic_group)
        
        row = 0
        fields = [
            ("名称(英) Name", "name_en"),
            ("名称(中) Name CN", "name_zh"),
            ("描述(英) Desc", "desc_en"),
            ("描述(中) Desc CN", "desc_zh"),
            ("显示ID DisplayID", "displayid"),
            ("物品等级 ItemLevel", "itemlevel"),
            ("需要等级 ReqLevel", "requiredlevel"),
            ("绑定类型 Bonding", "bonding", True),
            ("购买数量 BuyCount", "buycount"),
            ("购买价格 BuyPrice", "buyprice"),
            ("出售价格 SellPrice", "sellprice"),
            ("堆叠数量 Stackable", "stackable"),
            ("最大数量 MaxCount", "maxcount"),
            ("容器槽位 ContainerSlots", "containerslots"),
        ]
        
        for item in fields:
            label = item[0]
            field = item[1]
            is_combo = len(item) > 2 and item[2]
            
            basic_layout.addWidget(QLabel(label), row, 0)
            
            if is_combo and field == 'bonding':
                self.fields[field] = QComboBox()
                self.fields[field].addItems(["0-不绑定NoBond", "1-拾取绑定Pickup", "2-装备绑定Equip", "3-使用绑定Use", "4-任务Quest", "5-账号Account"])
            else:
                self.fields[field] = QLineEdit()
            
            basic_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        layout.addWidget(basic_group)
        
        # 分类属性
        class_group = QGroupBox("分类属性 / Class & Properties")
        class_layout = QGridLayout(class_group)
        
        combos = [
            ("物品类型 Class", "class_id", ["0-消耗品Consume", "1-容器Container", "2-武器Weapon", "3-宝石Gem", "4-护甲Armor", "5-材料Material", "6-弹药Ammo", "7-商品Goods", "8-配方Recipe", "9-钱币Money", "10-任务Quest", "11-钥匙Key"]),
            ("子类型 Subclass", "subclass", ["0-通用General", "1-斧Axe", "2-弓Bow", "3-枪Gun", "4-锤Mace", "5-杖Polearm", "6-剑Sword", "7-法杖Staff", "8-匕首Dagger", "9-拳套Fist"]),
            ("品质 Quality", "quality", ["0-垃圾Gray", "1-普通White", "2-优秀Green", "3-精良Blue", "4-史诗Purple", "5-传说Orange", "6-神器Yellow"]),
            ("装备槽 InvType", "inventorytype", ["0-非装备None", "1-头部Head", "2-颈部Neck", "3-肩部Shoulder", "4-衬衫Shirt", "5-胸甲Chest", "6-腰带Waist", "7-腿部Legs", "8-脚Feet", "9-手腕Wrist", "10-手套Hands", "11-手指Finger", "12-饰品Trinket"]),
            ("材质 Material", "material", ["0-无None", "1-金属Metal", "2-木材Wood", "3-液体Liquid", "4-珠宝Jewel", "5-链甲Chain", "6-板甲Plate", "7-布甲Cloth", "8-皮革Leather"]),
        ]
        
        row = 0
        for label, field, items in combos:
            class_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QComboBox()
            self.fields[field].addItems(items)
            class_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        texts = [
            ("护甲 Armor", "armor"),
            ("耐久度 Durability", "maxdurability"),
            ("延迟 Delay", "delay"),
            ("射程 Range", "rangedmodrange"),
            ("格挡 Block", "block"),
            ("弹药类型 AmmoType", "ammotype"),
            ("鞘 Sheath", "sheath"),
        ]
        
        for label, field in texts:
            class_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            class_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        layout.addWidget(class_group)
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def create_right_panel(self):
        """右侧：详细字段选项卡"""
        tabs = QTabWidget()
        tabs.setFont(CHINESE_FONT)
        
        # 属性选项卡
        stats_tab = QWidget()
        stats_layout = QGridLayout(stats_tab)
        
        row = 0
        for i in range(1, 6):
            stats_layout.addWidget(QLabel(f"属性{i}类型 Stat{i}Type"), row, 0)
            self.fields[f'stat_type{i}'] = QComboBox()
            self.fields[f'stat_type{i}'].addItems(["0-无None", "1-力量Str", "2-敏捷Agi", "3-耐力Sta", "4-智力Int", "5-精神Spi", "6-攻强AP", "7-法强SP", "18-穿透Pen", "19-格挡Block", "20-精准Expertise", "21-躲闪Dodge", "22-招架Parry"])
            stats_layout.addWidget(self.fields[f'stat_type{i}'], row, 1)
            
            stats_layout.addWidget(QLabel(f"属性{i}值 Stat{i}Val"), row, 2)
            self.fields[f'stat_value{i}'] = QLineEdit()
            stats_layout.addWidget(self.fields[f'stat_value{i}'], row, 3)
            row += 1
        
        resistances = [("神圣Holy", "holy_res"), ("火焰Fire", "fire_res"), ("自然Nature", "nature_res"), ("冰霜Frost", "frost_res"), ("暗影Shadow", "shadow_res"), ("奥术Arcane", "arcane_res")]
        for label, field in resistances:
            stats_layout.addWidget(QLabel(f"{label}抗性"), row, 0)
            self.fields[field] = QLineEdit()
            stats_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        tabs.addTab(stats_tab, "属性Stats")
        
        # 伤害选项卡
        combat_tab = QWidget()
        combat_layout = QGridLayout(combat_tab)
        
        row = 0
        for i in range(1, 3):
            combat_layout.addWidget(QLabel(f"伤害{i}最小 Dmg{i}Min"), row, 0)
            self.fields[f'dmg_min{i}'] = QLineEdit()
            combat_layout.addWidget(self.fields[f'dmg_min{i}'], row, 1)
            
            combat_layout.addWidget(QLabel(f"伤害{i}最大 Dmg{i}Max"), row, 2)
            self.fields[f'dmg_max{i}'] = QLineEdit()
            combat_layout.addWidget(self.fields[f'dmg_max{i}'], row, 3)
            
            combat_layout.addWidget(QLabel(f"伤害{i}类型 Dmg{i}Type"), row, 4)
            self.fields[f'dmg_type{i}'] = QComboBox()
            self.fields[f'dmg_type{i}'].addItems(["0-物理Physical", "1-神圣Holy", "2-火焰Fire", "3-自然Nature", "4-冰霜Frost", "5-暗影Shadow", "6-奥术Arcane"])
            combat_layout.addWidget(self.fields[f'dmg_type{i}'], row, 5)
            row += 1
        
        tabs.addTab(combat_tab, "伤害Damage")
        
        # 法术选项卡
        spells_tab = QWidget()
        spells_layout = QGridLayout(spells_tab)
        
        for i in range(1, 6):
            row = i - 1
            spells_layout.addWidget(QLabel(f"法术{i}ID Spell{i}ID"), row, 0)
            self.fields[f'spellid_{i}'] = QLineEdit()
            spells_layout.addWidget(self.fields[f'spellid_{i}'], row, 1)
            
            spells_layout.addWidget(QLabel(f"触发{i} Trigger{i}"), row, 2)
            self.fields[f'spelltrigger_{i}'] = QComboBox()
            self.fields[f'spelltrigger_{i}'].addItems(["0-使用OnUse", "1-装备OnEquip", "2-被动Passive"])
            spells_layout.addWidget(self.fields[f'spelltrigger_{i}'], row, 3)
            
            spells_layout.addWidget(QLabel(f"次数{i} Charges{i}"), row, 4)
            self.fields[f'spellcharges_{i}'] = QLineEdit()
            spells_layout.addWidget(self.fields[f'spellcharges_{i}'], row, 5)
        
        tabs.addTab(spells_tab, "法术Spells")
        
        # Socket选项卡
        socket_tab = QWidget()
        socket_layout = QGridLayout(socket_tab)
        
        row = 0
        for i in range(1, 4):
            socket_layout.addWidget(QLabel(f"插槽{i}颜色 Socket{i}"), row, 0)
            self.fields[f'socketColor_{i}'] = QComboBox()
            self.fields[f'socketColor_{i}'].addItems(["0-无None", "1-红色Red", "2-黄色Yellow", "4-蓝色Blue", "8-多彩Meta"])
            socket_layout.addWidget(self.fields[f'socketColor_{i}'], row, 1)
            row += 1
        
        socket_layout.addWidget(QLabel("插槽奖励 SocketBonus"), row, 0)
        self.fields['socketbonus'] = QLineEdit()
        socket_layout.addWidget(self.fields['socketbonus'], row, 1)
        
        socket_layout.addWidget(QLabel("随机属性 RandomProp"), row, 2)
        self.fields['randomproperty'] = QLineEdit()
        socket_layout.addWidget(self.fields['randomproperty'], row, 3)
        
        socket_layout.addWidget(QLabel("随机后缀 RandomSuffix"), row, 4)
        self.fields['randomsuffix'] = QLineEdit()
        socket_layout.addWidget(self.fields['randomsuffix'], row, 5)
        
        tabs.addTab(socket_tab, "Socket")
        
        # 要求选项卡
        req_tab = QWidget()
        req_layout = QGridLayout(req_tab)
        
        req_fields = [
            ("需要技能 ReqSkill", "requiredskill"),
            ("技能等级 SkillRank", "requiredskillrank"),
            ("需要法术 ReqSpell", "requiredspell"),
            ("需要阵营 ReqClass", "allowableclass"),
            ("需要种族 ReqRace", "allowablerace"),
            ("需要荣誉 ReqHonor", "requiredhonorrank"),
            ("声望阵营 RepFaction", "requiredreputationfaction"),
            ("声望等级 RepRank", "requiredreputationrank"),
            ("区域 Area", "area"),
            ("地图 Map", "map"),
            ("物品套装 ItemSet", "itemset"),
            ("锁ID LockID", "lockid"),
            ("任务文本ID PageText", "pagetext"),
            ("语言ID LangID", "languageid"),
        ]
        
        row = 0
        for label, field in req_fields:
            req_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            req_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        tabs.addTab(req_tab, "要求Requirements")
        
        # 高级选项卡
        adv_tab = QWidget()
        adv_layout = QGridLayout(adv_tab)
        
        adv_fields = [
            ("背包类别 BagFamily", "bagfamily"),
            ("持续时间 Duration", "duration"),
            ("额外标志 FlagsExtra", "flagsextra"),
            ("页面材质 PageMaterial", "pagematerial"),
            ("分解技能 Disenchant", "required_disenchant_skill"),
        ]
        
        row = 0
        for label, field in adv_fields:
            adv_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            adv_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        tabs.addTab(adv_tab, "高级Advanced")
        
        # SQL选项卡
        sql_tab = QWidget()
        sql_layout = QVBoxLayout(sql_tab)
        
        sql_layout.addWidget(QLabel("SQL语句预览 / SQL Preview:"))
        self.sql_text = QTextEdit()
        self.sql_text.setFont(QFont("Monaco", 10))
        sql_layout.addWidget(self.sql_text)
        
        btn_layout = QHBoxLayout()
        gen_insert_btn = QPushButton("生成INSERT")
        gen_insert_btn.clicked.connect(lambda: self.generate_sql("INSERT"))
        btn_layout.addWidget(gen_insert_btn)
        
        gen_update_btn = QPushButton("生成UPDATE")
        gen_update_btn.clicked.connect(lambda: self.generate_sql("UPDATE"))
        btn_layout.addWidget(gen_update_btn)
        
        gen_delete_btn = QPushButton("生成DELETE")
        gen_delete_btn.clicked.connect(lambda: self.generate_sql("DELETE"))
        btn_layout.addWidget(gen_delete_btn)
        
        copy_btn = QPushButton("复制SQL Copy")
        copy_btn.clicked.connect(self.copy_sql)
        btn_layout.addWidget(copy_btn)
        
        sql_layout.addLayout(btn_layout)
        
        exec_layout = QHBoxLayout()
        exec_btn = QPushButton("执行SQL Execute")
        exec_btn.setStyleSheet("background-color: #ff9800; color: white;")
        exec_btn.clicked.connect(self.execute_sql)
        exec_layout.addWidget(exec_btn)
        sql_layout.addLayout(exec_layout)
        
        patch_layout = QHBoxLayout()
        gen_patch_btn = QPushButton("生成补丁 GenPatch")
        gen_patch_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        gen_patch_btn.clicked.connect(self.generate_patch)
        patch_layout.addWidget(gen_patch_btn)
        
        push_patch_btn = QPushButton("推送补丁 PushPatch")
        push_patch_btn.setStyleSheet("background-color: #2196F3; color: white;")
        push_patch_btn.clicked.connect(self.push_patch)
        patch_layout.addWidget(push_patch_btn)
        
        sql_layout.addLayout(patch_layout)
        
        tabs.addTab(sql_tab, "SQL")
        
        return tabs
    
    def create_bottom_panel(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setFont(CHINESE_FONT)
        layout = QHBoxLayout(frame)
        
        clone_btn = QPushButton("套用物品 Clone")
        clone_btn.setStyleSheet("background-color: #9c27b0; color: white;")
        clone_btn.clicked.connect(self.clone_item)
        layout.addWidget(clone_btn)
        
        search_btn = QPushButton("搜索物品 Search")
        search_btn.setStyleSheet("background-color: #ff5722; color: white;")
        search_btn.clicked.connect(self.search_item)
        layout.addWidget(search_btn)
        
        layout.addStretch()
        
        self.env_info = QLabel("测试服 Test | 推送: /patches/test/")
        layout.addWidget(self.env_info)
        
        return frame
    
    # 方法实现（简化版，保持不变）
    def on_mode_changed(self, index):
        self.status_label.setText(f"模式: {'SSH' if index == 0 else 'Direct'}")
    
    def on_db_changed(self, index):
        if index == 0:
            self.status_label.setText("状态: 测试服 Test")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.env_info.setText("测试服 Test | 推送: /patches/test/")
        else:
            self.status_label.setText("状态: 正式服 Prod")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.env_info.setText("正式服 Prod | 推送: /patches/release/")
    
    def load_config_from_file(self):
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open('r') as f:
                    self.config.update(json.load(f))
                QMessageBox.information(self, "成功", "配置读取成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取失败: {e}")
    
    def save_config_to_file(self):
        try:
            with CONFIG_FILE.open('w') as f:
                json.dump(self.config, f, indent=2)
            QMessageBox.information(self, "成功", "配置保存成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open('r') as f:
                    self.config.update(json.load(f))
            except:
                pass
    
    def test_connection(self):
        try:
            conn = pymysql.connect(**self.config['db'], connect_timeout=5)
            conn.close()
            QMessageBox.information(self, "成功 Success", "数据库连接成功！")
        except Exception as e:
            QMessageBox.critical(self, "失败 Failed", f"连接失败：{e}")
    
    def get_field_value(self, field_name):
        widget = self.fields.get(field_name)
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        elif isinstance(widget, QComboBox):
            return widget.currentText().split('-')[0]
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
    
    def load_item(self):
        entry = self.get_field_value('entry')
        if not entry:
            QMessageBox.warning(self, "警告", "请输入物品 Entry")
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
                
                # 字段映射
                field_map = {
                    'name': 'name_en', 'description': 'desc_en',
                    'displayid': 'displayid', 'ItemLevel': 'itemlevel',
                    'RequiredLevel': 'requiredlevel', 'class': 'class_id',
                    'subclass': 'subclass', 'Quality': 'quality',
                    'InventoryType': 'inventorytype', 'Material': 'material',
                    'bonding': 'bonding', 'BuyCount': 'buycount',
                    'BuyPrice': 'buyprice', 'SellPrice': 'sellprice',
                    'stackable': 'stackable', 'maxcount': 'maxcount',
                    'ContainerSlots': 'containerslots', 'armor': 'armor',
                    'MaxDurability': 'maxdurability', 'delay': 'delay',
                    'RangedModRange': 'rangedmodrange', 'block': 'block',
                    'ammo_type': 'ammotype', 'sheath': 'sheath',
                }
                
                # 添加所有字段映射
                for i in range(1, 6):
                    field_map.update({
                        f'stat_type{i}': f'stat_type{i}',
                        f'stat_value{i}': f'stat_value{i}',
                        f'spellid_{i}': f'spellid_{i}',
                        f'spelltrigger_{i}': f'spelltrigger_{i}',
                        f'spellcharges_{i}': f'spellcharges_{i}',
                    })
                
                for i in range(1, 3):
                    field_map.update({
                        f'dmg_min{i}': f'dmg_min{i}',
                        f'dmg_max{i}': f'dmg_max{i}',
                        f'dmg_type{i}': f'dmg_type{i}',
                    })
                
                for i in range(1, 4):
                    field_map[f'socketColor_{i}'] = f'socketColor_{i}'
                
                field_map.update({
                    'holy_res': 'holy_res', 'fire_res': 'fire_res',
                    'nature_res': 'nature_res', 'frost_res': 'frost_res',
                    'shadow_res': 'shadow_res', 'arcane_res': 'arcane_res',
                    'socketBonus': 'socketbonus', 'RandomProperty': 'randomproperty',
                    'RandomSuffix': 'randomsuffix', 'BagFamily': 'bagfamily',
                    'duration': 'duration', 'FlagsExtra': 'flagsextra',
                    'RequiredSkill': 'requiredskill', 'RequiredSkillRank': 'requiredskillrank',
                    'requiredspell': 'requiredspell', 'AllowableClass': 'allowableclass',
                    'AllowableRace': 'allowablerace', 'requiredhonorrank': 'requiredhonorrank',
                    'RequiredReputationFaction': 'requiredreputationfaction',
                    'RequiredReputationRank': 'requiredreputationrank',
                    'area': 'area', 'Map': 'map', 'itemset': 'itemset',
                    'lockid': 'lockid', 'PageText': 'pagetext',
                    'LanguageID': 'languageid', 'PageMaterial': 'pagematerial',
                })
                
                for db_field, ui_field in field_map.items():
                    if db_field in item:
                        self.set_field_value(ui_field, item[db_field])
                
                # 读取中文名
                cur.execute("SELECT Name, Description FROM item_template_locale WHERE ID = %s AND locale = 'zhCN'", (entry,))
                locale_row = cur.fetchone()
                if locale_row:
                    self.set_field_value('name_zh', locale_row[0])
                    self.set_field_value('desc_zh', locale_row[1])
            
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
        name = self.get_field_value('name_en')
        if sql_type == "DELETE":
            sql = f"DELETE FROM item_template WHERE entry={entry};"
        else:
            sql = f"-- SQL for {sql_type}: entry={entry}, name={name}"
        self.sql_text.setPlainText(sql)
    
    def copy_sql(self):
        QApplication.clipboard().setText(self.sql_text.toPlainText())
        QMessageBox.information(self, "成功", "SQL已复制")
    
    def execute_sql(self):
        QMessageBox.information(self, "提示", "执行SQL功能开发中...")
    
    def clone_item(self):
        QMessageBox.information(self, "提示", "套用功能开发中...")
    
    def search_item(self):
        dialog = SearchItemDialog(self, self.config['db'])
        if dialog.exec_() == QDialog.Accepted:
            entry = dialog.get_selected_entry()
            if entry:
                self.set_field_value('entry', entry)
                self.load_item()
    
    def generate_patch(self):
        QMessageBox.information(self, "提示", "补丁生成功能开发中...")
    
    def push_patch(self):
        QMessageBox.information(self, "提示", "推送补丁功能开发中...")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置全局字体
    font = QFont("PingFang SC", 10)
    app.setFont(font)
    
    icon_path = Path(__file__).parent / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = WOWItemMakerWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
