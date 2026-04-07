#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诺兰时光物品工具 - 原生桌面版 v2.3
使用 PyQt5 原生控件，完整功能
"""

import sys
import json
import subprocess
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QGroupBox,
    QGridLayout, QMessageBox, QSplitter, QFrame, QScrollArea, QTabWidget,
    QFileDialog, QDialog, QFormLayout, QListWidget, QListWidgetItem, QProgressDialog,
    QCheckBox
)
from PyQt5.QtGui import QFont, QIcon

import pymysql
import csv
import struct


# 配置文件路径
CONFIG_FILE = Path(__file__).parent / 'conninfo.json'


class CloneItemDialog(QDialog):
    """套用物品对话框"""
    def __init__(self, parent=None, current_entry=''):
        super().__init__(parent)
        self.setWindowTitle("套用物品")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QFormLayout(self)
        
        self.src_entry = QLineEdit(current_entry)
        layout.addRow("源物品 Entry:", self.src_entry)
        
        self.new_entry = QLineEdit()
        layout.addRow("新物品 Entry:", self.new_entry)
        
        self.new_name_en = QLineEdit()
        layout.addRow("新名称(英文):", self.new_name_en)
        
        self.new_name_zh = QLineEdit()
        layout.addRow("新名称(中文):", self.new_name_zh)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)
    
    def get_data(self):
        return {
            'src_entry': self.src_entry.text().strip(),
            'new_entry': self.new_entry.text().strip(),
            'new_name_en': self.new_name_en.text().strip(),
            'new_name_zh': self.new_name_zh.text().strip()
        }


class SearchItemDialog(QDialog):
    """搜索物品对话框"""
    def __init__(self, parent=None, db_config=None):
        super().__init__(parent)
        self.setWindowTitle("搜索物品")
        self.setModal(True)
        self.resize(800, 600)
        self.db_config = db_config or {}
        
        layout = QVBoxLayout(self)
        
        # 搜索输入
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("关键词:"))
        self.keyword = QLineEdit()
        self.keyword.setPlaceholderText("输入物品ID或名称")
        self.keyword.returnPressed.connect(self.search)
        search_layout.addWidget(self.keyword)
        
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.search)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        # 结果列表
        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self.select_item)
        layout.addWidget(self.results)
        
        # 按钮
        buttons = QHBoxLayout()
        select_btn = QPushButton("选择")
        select_btn.clicked.connect(self.select_item)
        close_btn = QPushButton("关闭")
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
                sql = """SELECT entry, name, Quality 
                         FROM item_template 
                         WHERE entry LIKE %s OR name LIKE %s 
                         LIMIT 100"""
                pattern = f"%{keyword}%"
                cur.execute(sql, (pattern, pattern))
                rows = cur.fetchall()
                
                self.results.clear()
                if not rows:
                    QMessageBox.information(self, "提示", "没有找到匹配的物品")
                    return
                
                for row in rows:
                    entry, name, quality = row
                    quality_names = ["垃圾", "普通", "优秀", "精良", "史诗", "传说", "神器"]
                    quality_name = quality_names[quality] if 0 <= quality < len(quality_names) else str(quality)
                    item = QListWidgetItem(f"[{entry}] {name} ({quality_name})")
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
        self.setWindowTitle("诺兰时光物品工具 v2.3 - 原生版")
        self.setGeometry(100, 100, 1600, 1000)
        
        # 设置图标
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 配置
        self.config = {
            "mode": "direct",
            "db": {
                "host": "43.248.129.172",
                "port": 3306,
                "user": "wowitem",
                "password": "GknNJLRtcE6RzigVJFF8",
                "database": "acore_world_test"
            },
            "ssh": {
                "host": "43.248.129.172",
                "user": "root",
                "keyPath": "/Users/mac/Desktop/cd.pem"
            }
        }
        
        # 字段映射
        self.fields = {}
        
        # 创建界面
        self.create_ui()
        
        # 加载配置
        self.load_config()
    
    def create_ui(self):
        """创建界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部：配置和连接
        top_frame = self.create_top_panel()
        main_layout.addWidget(top_frame)
        
        # 中间:分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧:物品基本字段
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧:物品详细字段(选项卡)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([700, 900])
        main_layout.addWidget(splitter)
        
        # 底部:操作按钮
        bottom_frame = self.create_bottom_panel()
        main_layout.addWidget(bottom_frame)
    
    def create_top_panel(self):
        """创建顶部面板：配置和连接"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        
        # 第一行：模式选择和数据库
        row1 = QHBoxLayout()
        
        # 连接模式
        row1.addWidget(QLabel("连接模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["direct-直连数据库", "ssh-SSH隧道"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        row1.addWidget(self.mode_combo)
        
        # 数据库选择
        row1.addWidget(QLabel("数据库:"))
        self.db_combo = QComboBox()
        self.db_combo.addItems(["acore_world_test（测试服）", "acore_world（正式服）"])
        self.db_combo.currentIndexChanged.connect(self.on_db_changed)
        row1.addWidget(self.db_combo)
        
        # 环境状态
        self.status_label = QLabel("状态: 测试服")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        row1.addWidget(self.status_label)
        
        row1.addStretch()
        layout.addLayout(row1)
        
        # 第二行：配置按钮
        row2 = QHBoxLayout()
        
        read_config_btn = QPushButton("读取配置")
        read_config_btn.clicked.connect(self.load_config_from_file)
        row2.addWidget(read_config_btn)
        
        save_config_btn = QPushButton("保存配置")
        save_config_btn.clicked.connect(self.save_config_to_file)
        row2.addWidget(save_config_btn)
        
        self.save_password_check = QCheckBox("保存密码")
        row2.addWidget(self.save_password_check)
        
        row2.addStretch()
        
        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self.test_connection)
        row2.addWidget(test_btn)
        
        layout.addLayout(row2)
        
        return frame
    
    def create_left_panel(self):
        """创建左侧面板：基本字段（双列布局）"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 物品 Entry
        entry_group = QGroupBox("物品 Entry")
        entry_layout = QHBoxLayout(entry_group)
        self.fields['entry'] = QLineEdit()
        self.fields['entry'].setPlaceholderText("输入物品ID")
        entry_layout.addWidget(self.fields['entry'])
        
        read_btn = QPushButton("读取")
        read_btn.clicked.connect(self.load_item)
        entry_layout.addWidget(read_btn)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_item)
        entry_layout.addWidget(save_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        delete_btn.clicked.connect(self.delete_item)
        entry_layout.addWidget(delete_btn)
        
        layout.addWidget(entry_group)
        
        # 基本信息（双列）
        basic_group = QGroupBox("基本信息")
        basic_layout = QGridLayout(basic_group)
        basic_layout.setColumnStretch(1, 1)
        basic_layout.setColumnStretch(3, 1)
        
        # 第一列
        row = 0
        col = 0
        for label, field, width in [
            ("名称(英)", "name_en", 200),
            ("名称(中)", "name_zh", 200),
            ("描述(英)", "desc_en", 200),
            ("描述(中)", "desc_zh", 200),
        ]:
            basic_layout.addWidget(QLabel(label), row, col)
            self.fields[field] = QLineEdit()
            if width:
                self.fields[field].setMaximumWidth(width)
            basic_layout.addWidget(self.fields[field], row, col + 1)
            row += 1
        
        # 第二列
        row = 0
        col = 2
        for label, field, width in [
            ("显示ID", "displayid", 80),
            ("物品等级", "itemlevel", 80),
            ("需要等级", "requiredlevel", 80),
            ("容器槽", "containerslots", 80),
        ]:
            basic_layout.addWidget(QLabel(label), row, col)
            self.fields[field] = QLineEdit()
            if width:
                self.fields[field].setMaximumWidth(width)
            basic_layout.addWidget(self.fields[field], row, col + 1)
            row += 1
        
        layout.addWidget(basic_group)
        
        # 分类和属性（双列）
        class_group = QGroupBox("分类和属性")
        class_layout = QGridLayout(class_group)
        class_layout.setColumnStretch(1, 1)
        class_layout.setColumnStretch(3, 1)
        
        # 下拉框字段（第一列）
        row = 0
        for label, field, items in [
            ("物品类型", "class_id", ["0-消耗品", "1-容器", "2-武器", "3-宝石", "4-护甲", "5-材料", "6-弹药", "7-商品", "8-配方", "9-钱币", "10-任务", "11-钥匙", "12-永久", "13-垃圾"]),
            ("品质", "quality", ["0-垃圾(灰)", "1-普通(白)", "2-优秀(绿)", "3-精良(蓝)", "4-史诗(紫)", "5-传说(橙)", "6-神器(黄)"]),
            ("装备槽", "inventorytype", ["0-非装备", "1-头部", "2-颈部", "3-肩部", "4-衬衫", "5-胸甲", "6-腰带", "7-腿部", "8-脚", "9-手腕", "10-手套", "11-手指", "12-饰品"]),
        ]:
            class_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QComboBox()
            self.fields[field].addItems(items)
            self.fields[field].setMaximumWidth(150)
            class_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        # 下拉框字段（第二列）
        row = 0
        for label, field, items in [
            ("子类型", "subclass", ["0-通用", "1-斧", "2-弓", "3-枪", "4-锤", "5-长柄", "6-剑", "7-法杖", "8-匕首", "9-拳套", "10-盾牌"]),
            ("材质", "material", ["0-无", "1-金属", "2-木材", "3-液体", "4-珠宝", "5-链甲", "6-板甲", "7-布甲", "8-皮革"]),
            ("绑定类型", "bonding", ["0-不绑定", "1-拾取绑定", "2-装备绑定", "3-使用绑定", "4-任务物品"]),
        ]:
            class_layout.addWidget(QLabel(label), row, 2)
            self.fields[field] = QComboBox()
            self.fields[field].addItems(items)
            self.fields[field].setMaximumWidth(150)
            class_layout.addWidget(self.fields[field], row, 3)
            row += 1
        
        # 数值字段（第一列）
        row = 3
        for label, field in [
            ("购买价格", "buyprice"),
            ("出售价格", "sellprice"),
            ("堆叠数量", "stackable"),
        ]:
            class_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(100)
            class_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        # 数值字段（第二列）
        row = 3
        for label, field in [
            ("最大数量", "maxcount"),
            ("护甲", "armor"),
            ("耐久度", "maxdurability"),
        ]:
            class_layout.addWidget(QLabel(label), row, 2)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(100)
            class_layout.addWidget(self.fields[field], row, 3)
            row += 1
        
        layout.addWidget(class_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_right_panel(self):
        """创建右侧面板：详细字段（选项卡）"""
        tabs = QTabWidget()
        
        # 选项卡1：属性（双列）
        stats_tab = QWidget()
        stats_layout = QGridLayout(stats_tab)
        stats_layout.setColumnStretch(1, 1)
        stats_layout.setColumnStretch(3, 1)
        
        # 第一列：基础属性
        row = 0
        for label, field in [
            ("力量", "stat_value1"), ("敏捷", "stat_value2"),
            ("耐力", "stat_value3"), ("智力", "stat_value4"),
            ("精神", "stat_value5"),
        ]:
            stats_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(80)
            stats_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        # 第二列：抗性
        row = 0
        for label, field in [
            ("神圣抗性", "holy_res"), ("火焰抗性", "fire_res"),
            ("自然抗性", "nature_res"), ("冰霜抗性", "frost_res"),
            ("暗影抗性", "shadow_res"), ("奥术抗性", "arcane_res"),
        ]:
            stats_layout.addWidget(QLabel(label), row, 2)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(80)
            stats_layout.addWidget(self.fields[field], row, 3)
            row += 1
        
        tabs.addTab(stats_tab, "属性")
        
        # 选项卡2：伤害和防御
        damage_tab = QWidget()
        damage_layout = QGridLayout(damage_tab)
        damage_layout.setColumnStretch(1, 1)
        damage_layout.setColumnStretch(3, 1)
        
        # 第一列
        row = 0
        for label, field in [
            ("最小伤害", "dmg_min1"), ("最大伤害", "dmg_max1"),
            ("伤害类型", "dmg_type1"), ("攻击速度", "delay"),
            ("每秒伤害", "dps"),
        ]:
            damage_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(80)
            damage_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        # 第二列
        row = 0
        for label, field in [
            ("最小伤害2", "dmg_min2"), ("最大伤害2", "dmg_max2"),
            ("伤害类型2", "dmg_type2"), ("格挡", "block"),
            ("射程", "rangedmodrange"),
        ]:
            damage_layout.addWidget(QLabel(label), row, 2)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(80)
            damage_layout.addWidget(self.fields[field], row, 3)
            row += 1
        
        tabs.addTab(damage_tab, "伤害")
        
        # 选项卡3：法术效果（5个法术）
        spells_tab = QWidget()
        spells_layout = QGridLayout(spells_tab)
        
        for i in range(1, 6):
            row = i - 1
            # 法术ID
            spells_layout.addWidget(QLabel(f"法术{i} ID"), row, 0)
            self.fields[f'spellid_{i}'] = QLineEdit()
            self.fields[f'spellid_{i}'].setMaximumWidth(100)
            spells_layout.addWidget(self.fields[f'spellid_{i}'], row, 1)
            
            # 触发类型
            spells_layout.addWidget(QLabel(f"触发{i}"), row, 2)
            self.fields[f'spelltrigger_{i}'] = QComboBox()
            self.fields[f'spelltrigger_{i}'].addItems(["0-使用", "1-装备", "2-被动"])
            spells_layout.addWidget(self.fields[f'spelltrigger_{i}'], row, 3)
            
            # 冷却
            spells_layout.addWidget(QLabel(f"冷却{i}"), row, 4)
            self.fields[f'spellcooldown_{i}'] = QLineEdit()
            self.fields[f'spellcooldown_{i}'].setMaximumWidth(80)
            spells_layout.addWidget(self.fields[f'spellcooldown_{i}'], row, 5)
        
        tabs.addTab(spells_tab, "法术")
        
        # 选项卡4：要求（双列）
        req_tab = QWidget()
        req_layout = QGridLayout(req_tab)
        req_layout.setColumnStretch(1, 1)
        req_layout.setColumnStretch(3, 1)
        
        # 第一列
        row = 0
        for label, field in [
            ("需要技能", "requiredskill"),
            ("技能等级", "requiredskillrank"),
            ("需要法术", "requiredspell"),
            ("需要阵营", "allowableclass"),
            ("需要种族", "allowablerace"),
            ("需要荣誉", "requiredhonorrank"),
        ]:
            req_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(100)
            req_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        # 第二列
        row = 0
        for label, field in [
            ("声望阵营", "requiredreputationfaction"),
            ("声望等级", "requiredreputationrank"),
            ("区域", "area"),
            ("地图", "map"),
            ("物品套装", "itemset"),
            ("任务物品", "page_text"),
        ]:
            req_layout.addWidget(QLabel(label), row, 2)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(100)
            req_layout.addWidget(self.fields[field], row, 3)
            row += 1
        
        tabs.addTab(req_tab, "要求")
        
        # 选项卡5：SQL和补丁
        sql_tab = QWidget()
        sql_layout = QVBoxLayout(sql_tab)
        
        # SQL预览
        sql_layout.addWidget(QLabel("SQL语句预览:"))
        self.sql_text = QTextEdit()
        self.sql_text.setFont(QFont("Monaco", 10))
        self.sql_text.setMaximumHeight(300)
        sql_layout.addWidget(self.sql_text)
        
        # SQL操作按钮
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
        
        copy_btn = QPushButton("复制SQL")
        copy_btn.clicked.connect(self.copy_sql)
        btn_layout.addWidget(copy_btn)
        
        sql_layout.addLayout(btn_layout)
        
        # 执行SQL
        exec_layout = QHBoxLayout()
        exec_btn = QPushButton("执行当前SQL")
        exec_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold;")
        exec_btn.clicked.connect(self.execute_sql)
        exec_layout.addWidget(exec_btn)
        sql_layout.addLayout(exec_layout)
        
        # 补丁操作
        patch_layout = QHBoxLayout()
        
        gen_patch_btn = QPushButton("生成问号补丁")
        gen_patch_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        gen_patch_btn.clicked.connect(self.generate_patch)
        patch_layout.addWidget(gen_patch_btn)
        
        push_patch_btn = QPushButton("推送补丁到服务器")
        push_patch_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        push_patch_btn.clicked.connect(self.push_patch)
        patch_layout.addWidget(push_patch_btn)
        
        sql_layout.addLayout(patch_layout)
        
        tabs.addTab(sql_tab, "SQL和补丁")
        
        return tabs
    
    def create_bottom_panel(self):
        """创建底部面板"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        
        # 套用物品
        clone_btn = QPushButton("套用物品")
        clone_btn.setStyleSheet("background-color: #9c27b0; color: white;")
        clone_btn.clicked.connect(self.clone_item)
        layout.addWidget(clone_btn)
        
        # 搜索物品
        search_btn = QPushButton("搜索物品")
        search_btn.setStyleSheet("background-color: #ff5722; color: white;")
        search_btn.clicked.connect(self.search_item)
        layout.addWidget(search_btn)
        
        layout.addStretch()
        
        # 环境提示
        self.env_info = QLabel()
        self.update_env_info()
        layout.addWidget(self.env_info)
        
        return frame
    
    def on_mode_changed(self, index):
        """连接模式切换"""
        mode = "direct" if index == 0 else "ssh"
        self.config['mode'] = mode
        self.update_env_info()
    
    def on_db_changed(self, index):
        """数据库切换"""
        if index == 0:
            self.config['db']['database'] = 'acore_world_test'
            self.status_label.setText("状态: 测试服")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.config['db']['database'] = 'acore_world'
            self.status_label.setText("状态: 正式服")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.update_env_info()
    
    def update_env_info(self):
        """更新环境信息"""
        db = self.config['db']['database']
        mode = self.config.get('mode', 'direct')
        mode_text = "直连" if mode == "direct" else "SSH"
        
        if 'test' in db:
            self.env_info.setText(f"{mode_text} | 测试服 | 推送: /patches/test/")
        else:
            self.env_info.setText(f"{mode_text} | 正式服 | 推送: /patches/release/")
    
    def load_config_from_file(self):
        """从文件读取配置"""
        try:
            if CONFIG_FILE.exists():
                with CONFIG_FILE.open('r', encoding='utf-8') as f:
                    saved = json.load(f)
                    
                    # 应用配置
                    if 'mode' in saved:
                        mode = saved['mode']
                        self.mode_combo.setCurrentIndex(0 if mode == 'direct' else 1)
                    
                    if 'db' in saved:
                        self.config['db'].update(saved['db'])
                        
                        # 更新数据库选择
                        db_name = self.config['db'].get('database', '')
                        if 'test' in db_name:
                            self.db_combo.setCurrentIndex(0)
                        else:
                            self.db_combo.setCurrentIndex(1)
                    
                    if 'ssh' in saved:
                        self.config['ssh'].update(saved['ssh'])
                    
                    if 'savePassword' in saved:
                        self.save_password_check.setChecked(saved['savePassword'])
                    
                    self.config.update(saved)
                    
                    QMessageBox.information(self, "成功", "配置读取成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取配置失败：{e}")
    
    def save_config_to_file(self):
        """保存配置到文件"""
        try:
            # 收集配置
            self.config['savePassword'] = self.save_password_check.isChecked()
            
            # 如果不保存密码，清除密码字段
            if not self.save_password_check.isChecked():
                self.config['db']['password'] = ''
            
            # 写入文件
            with CONFIG_FILE.open('w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "成功", "配置保存成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败：{e}")
    
    def load_config(self):
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open('r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.config.update(saved)
                    
                    # 应用到界面
                    mode = saved.get('mode', 'direct')
                    self.mode_combo.setCurrentIndex(0 if mode == 'direct' else 1)
                    
                    db_name = self.config.get('db', {}).get('database', 'acore_world_test')
                    if 'test' in db_name:
                        self.db_combo.setCurrentIndex(0)
                    else:
                        self.db_combo.setCurrentIndex(1)
                    
                    if 'savePassword' in saved:
                        self.save_password_check.setChecked(saved['savePassword'])
                    
                    self.update_env_info()
            except:
                pass
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            db_config = self.config['db'].copy()
            conn = pymysql.connect(**db_config, connect_timeout=5)
            conn.close()
            QMessageBox.information(self, "成功", "数据库连接成功！")
        except Exception as e:
            QMessageBox.critical(self, "失败", f"连接失败：{e}")
    
    def get_field_value(self, field_name):
        """获取字段值"""
        widget = self.fields.get(field_name)
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        elif isinstance(widget, QComboBox):
            return widget.currentText().split('-')[0]
        return ''
    
    def set_field_value(self, field_name, value):
        """设置字段值"""
        widget = self.fields.get(field_name)
        if isinstance(widget, QLineEdit):
            widget.setText(str(value or ''))
        elif isinstance(widget, QComboBox):
            # 查找匹配项
            for i in range(widget.count()):
                if widget.itemText(i).startswith(str(value)):
                    widget.setCurrentIndex(i)
                    break
    
    def load_item(self):
        """读取物品"""
        entry = self.get_field_value('entry')
        if not entry:
            QMessageBox.warning(self, "警告", "请输入物品 Entry")
            return
        
        try:
            db_config = self.config['db'].copy()
            conn = pymysql.connect(**db_config)
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM item_template WHERE entry = %s", (entry,))
                row = cur.fetchone()
                
                if not row:
                    QMessageBox.warning(self, "警告", f"未找到物品 {entry}")
                    return
                
                # 获取字段名
                columns = [desc[0] for desc in cur.description]
                item = dict(zip(columns, row))
                
                # 填充字段（完整映射）
                field_map = {
                    # 基本信息
                    'name': 'name_en', 'description': 'desc_en',
                    'displayid': 'displayid', 'ItemLevel': 'itemlevel',
                    'RequiredLevel': 'requiredlevel', 'ContainerSlots': 'containerslots',
                    
                    # 分类和属性
                    'class': 'class_id', 'subclass': 'subclass',
                    'Quality': 'quality', 'InventoryType': 'inventorytype',
                    'Material': 'material', 'bonding': 'bonding',
                    'BuyPrice': 'buyprice', 'SellPrice': 'sellprice',
                    'stackable': 'stackable', 'maxcount': 'maxcount',
                    'armor': 'armor', 'MaxDurability': 'maxdurability',
                    
                    # 属性
                    'stat_value1': 'stat_value1', 'stat_value2': 'stat_value2',
                    'stat_value3': 'stat_value3', 'stat_value4': 'stat_value4',
                    'stat_value5': 'stat_value5',
                    'holy_res': 'holy_res', 'fire_res': 'fire_res',
                    'nature_res': 'nature_res', 'frost_res': 'frost_res',
                    'shadow_res': 'shadow_res', 'arcane_res': 'arcane_res',
                    
                    # 伤害
                    'dmg_min1': 'dmg_min1', 'dmg_max1': 'dmg_max1',
                    'dmg_type1': 'dmg_type1', 'delay': 'delay',
                    'dmg_min2': 'dmg_min2', 'dmg_max2': 'dmg_max2',
                    'dmg_type2': 'dmg_type2', 'block': 'block',
                    'RangedModRange': 'rangedmodrange',
                    
                    # 法术
                    'spellid_1': 'spellid_1', 'spelltrigger_1': 'spelltrigger_1',
                    'spellcooldown_1': 'spellcooldown_1',
                    'spellid_2': 'spellid_2', 'spelltrigger_2': 'spelltrigger_2',
                    'spellcooldown_2': 'spellcooldown_2',
                    'spellid_3': 'spellid_3', 'spelltrigger_3': 'spelltrigger_3',
                    'spellcooldown_3': 'spellcooldown_3',
                    'spellid_4': 'spellid_4', 'spelltrigger_4': 'spelltrigger_4',
                    'spellcooldown_4': 'spellcooldown_4',
                    'spellid_5': 'spellid_5', 'spelltrigger_5': 'spelltrigger_5',
                    'spellcooldown_5': 'spellcooldown_5',
                    
                    # 要求
                    'RequiredSkill': 'requiredskill', 'RequiredSkillRank': 'requiredskillrank',
                    'requiredspell': 'requiredspell', 'AllowableClass': 'allowableclass',
                    'AllowableRace': 'allowablerace', 'RequiredHonorRank': 'requiredhonorrank',
                    'RequiredReputationFaction': 'requiredreputationfaction',
                    'RequiredReputationRank': 'requiredreputationrank',
                    'area': 'area', 'Map': 'map',
                    'itemset': 'itemset', 'PageText': 'page_text',
                }
                
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
        """保存物品"""
        entry = self.get_field_value('entry')
        if not entry:
            QMessageBox.warning(self, "警告", "请输入物品 Entry")
            return
        
        # TODO: 实现保存逻辑（类似读取，但是反向）
        QMessageBox.information(self, "提示", "保存功能开发中...")
    
    def delete_item(self):
        """删除物品"""
        entry = self.get_field_value('entry')
        if not entry:
            QMessageBox.warning(self, "警告", "请输入物品 Entry")
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除物品 {entry} 吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            db_config = self.config['db'].copy()
            conn = pymysql.connect(**db_config)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM item_template WHERE entry = %s", (entry,))
                cur.execute("DELETE FROM item_template_locale WHERE ID = %s AND locale = 'zhCN'", (entry,))
                conn.commit()
            
            conn.close()
            QMessageBox.information(self, "成功", f"物品 {entry} 已删除")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败：{e}")
    
    def generate_sql(self, sql_type):
        """生成SQL"""
        entry = self.get_field_value('entry')
        name = self.get_field_value('name_en')
        
        if sql_type == "INSERT":
            sql = f"""INSERT INTO item_template (entry, name, displayid, Quality, class, subclass, InventoryType, Material)
VALUES ({entry}, '{name}', {self.get_field_value('displayid') or 0}, {self.get_field_value('quality') or 0}, 
{self.get_field_value('class_id') or 0}, {self.get_field_value('subclass') or 0}, 
{self.get_field_value('inventorytype') or 0}, {self.get_field_value('material') or 0});"""
        elif sql_type == "UPDATE":
            sql = f"""UPDATE item_template SET 
name='{name}', displayid={self.get_field_value('displayid') or 0}, Quality={self.get_field_value('quality') or 0},
class={self.get_field_value('class_id') or 0}, subclass={self.get_field_value('subclass') or 0},
InventoryType={self.get_field_value('inventorytype') or 0}, Material={self.get_field_value('material') or 0}
WHERE entry={entry};"""
        else:  # DELETE
            sql = f"DELETE FROM item_template WHERE entry={entry};"
        
        self.sql_text.setPlainText(sql)
    
    def copy_sql(self):
        """复制SQL"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.sql_text.toPlainText())
        QMessageBox.information(self, "成功", "SQL已复制到剪贴板")
    
    def execute_sql(self):
        """执行SQL"""
        sql = self.sql_text.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "警告", "SQL语句为空")
            return
        
        reply = QMessageBox.question(
            self, "确认执行",
            f"确定要执行以下SQL吗？\n\n{sql[:200]}...",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            db_config = self.config['db'].copy()
            conn = pymysql.connect(**db_config)
            with conn.cursor() as cur:
                cur.execute(sql)
                conn.commit()
                affected = cur.rowcount
            
            conn.close()
            QMessageBox.information(self, "成功", f"SQL执行成功\n影响行数：{affected}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行失败：{e}")
    
    def clone_item(self):
        """套用物品"""
        dialog = CloneItemDialog(self, self.get_field_value('entry'))
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            
            if not all([data['src_entry'], data['new_entry'], data['new_name_en']]):
                QMessageBox.warning(self, "警告", "请填写所有必填字段")
                return
            
            try:
                db_config = self.config['db'].copy()
                conn = pymysql.connect(**db_config)
                with conn.cursor() as cur:
                    # 读取源物品
                    cur.execute("SELECT * FROM item_template WHERE entry = %s", (data['src_entry'],))
                    src_row = cur.fetchone()
                    
                    if not src_row:
                        QMessageBox.warning(self, "警告", f"源物品 {data['src_entry']} 不存在")
                        return
                    
                    columns = [desc[0] for desc in cur.description]
                    src_item = dict(zip(columns, src_row))
                    
                    # 修改字段
                    src_item['entry'] = data['new_entry']
                    src_item['name'] = data['new_name_en']
                    
                    # 插入新物品
                    placeholders = ', '.join(['%s'] * len(src_item))
                    columns_str = ', '.join(src_item.keys())
                    sql = f"INSERT INTO item_template ({columns_str}) VALUES ({placeholders})"
                    cur.execute(sql, list(src_item.values()))
                    
                    # 插入中文名
                    if data['new_name_zh']:
                        cur.execute("""REPLACE INTO item_template_locale (ID, locale, Name, Description)
                            VALUES (%s, 'zhCN', %s, %s)""", 
                            (data['new_entry'], data['new_name_zh'], ''))
                    
                    conn.commit()
                
                conn.close()
                QMessageBox.information(self, "成功", f"物品已复制到 {data['new_entry']}")
                
                # 自动加载新物品
                self.set_field_value('entry', data['new_entry'])
                self.load_item()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"复制失败：{e}")
    
    def search_item(self):
        """搜索物品"""
        db_config = self.config['db'].copy()
        dialog = SearchItemDialog(self, db_config)
        
        if dialog.exec_() == QDialog.Accepted:
            entry = dialog.get_selected_entry()
            if entry:
                self.set_field_value('entry', entry)
                self.load_item()
    
    def generate_patch(self):
        """生成问号补丁"""
        QMessageBox.information(self, "提示", "补丁生成功能开发中...")
    
    def push_patch(self):
        """推送补丁"""
        db = self.config['db']['database']
        env = 'test' if 'test' in db else 'release'
        env_name = '测试服' if env == 'test' else '正式服'
        
        reply = QMessageBox.question(
            self, "确认推送",
            f"确定要推送到 {env_name} 吗？\n\n"
            f"数据库：{db}\n"
            f"目标目录：/patches/{env}/",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        QMessageBox.information(self, "提示", "补丁推送功能开发中...")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 跨平台统一风格
    
    # 设置应用图标
    icon_path = Path(__file__).parent / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = WOWItemMakerWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
