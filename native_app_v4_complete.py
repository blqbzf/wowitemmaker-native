#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诺兰时光物品工具 - 原生桌面版 v2.4
完整版 - 补充所有缺失字段
"""

import sys
import json
import subprocess
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
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("关键词:"))
        self.keyword = QLineEdit()
        self.keyword.setPlaceholderText("输入物品ID或名称（支持中英文）")
        self.keyword.returnPressed.connect(self.search)
        search_layout.addWidget(self.keyword)
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.search)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self.select_item)
        layout.addWidget(self.results)
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
                sql = """SELECT DISTINCT t.entry, t.name, l.Name as name_zh, t.Quality 
                         FROM item_template t
                         LEFT JOIN item_template_locale l ON t.entry = l.ID AND l.locale = 'zhCN'
                         WHERE t.entry LIKE %s 
                            OR t.name LIKE %s 
                            OR l.Name LIKE %s
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
                    quality_names = ["垃圾", "普通", "优秀", "精良", "史诗", "传说", "神器"]
                    quality_name = quality_names[quality] if 0 <= quality < len(quality_names) else str(quality)
                    display_name = f"{name_zh or name_en}{' (' + name_en + ')' if name_zh and name_zh != name_en else ''}"
                    item = QListWidgetItem(f"[{entry}] {display_name} ({quality_name})")
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
        self.setWindowTitle("诺兰时光物品工具 v2.4 - 完整版")
        self.setGeometry(100, 100, 1800, 1100)
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
            "ssh": {
                "host": "43.248.129.172",
                "user": "root",
                "keyPath": "/Users/mac/Desktop/cd.pem",
                "password": ""
            },
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
        
        # 顶部：配置
        top_frame = self.create_top_panel()
        main_layout.addWidget(top_frame)
        
        # 中间：分割器
        splitter = QSplitter(Qt.Horizontal)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 1100])
        main_layout.addWidget(splitter)
        
        # 底部：操作按钮
        bottom_frame = self.create_bottom_panel()
        main_layout.addWidget(bottom_frame)
    
    def create_top_panel(self):
        """创建顶部面板"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        
        # 配置区域
        config_group = QGroupBox("连接信息 / 数据库配置")
        config_layout = QGridLayout(config_group)
        config_layout.setColumnStretch(1, 1)
        config_layout.setColumnStretch(3, 1)
        config_layout.setColumnStretch(5, 1)
        
        row = 0
        config_layout.addWidget(QLabel("Mode(连接模式):"), row, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["remote-SSH转发", "direct-数据库直连"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        config_layout.addWidget(self.mode_combo, row, 1)
        
        config_layout.addWidget(QLabel("SSH Host:"), row, 2)
        self.ssh_host = QLineEdit("43.248.129.172")
        config_layout.addWidget(self.ssh_host, row, 3)
        
        config_layout.addWidget(QLabel("SSH User:"), row, 4)
        self.ssh_user = QLineEdit("root")
        config_layout.addWidget(self.ssh_user, row, 5)
        
        row += 1
        config_layout.addWidget(QLabel("SSH Key Path:"), row, 0)
        self.ssh_key_path = QLineEdit("/Users/mac/Desktop/cd.pem")
        config_layout.addWidget(self.ssh_key_path, row, 1)
        
        config_layout.addWidget(QLabel("DB Host:"), row, 2)
        self.db_host = QLineEdit("43.248.129.172")
        config_layout.addWidget(self.db_host, row, 3)
        
        config_layout.addWidget(QLabel("DB Port:"), row, 4)
        self.db_port = QLineEdit("3306")
        config_layout.addWidget(self.db_port, row, 5)
        
        row += 1
        config_layout.addWidget(QLabel("DB User:"), row, 0)
        self.db_user = QLineEdit("wowitem")
        config_layout.addWidget(self.db_user, row, 1)
        
        config_layout.addWidget(QLabel("DB Password:"), row, 2)
        self.db_password = QLineEdit("GknNJLRtcE6RzigVJFF8")
        self.db_password.setEchoMode(QLineEdit.Password)
        config_layout.addWidget(self.db_password, row, 3)
        
        config_layout.addWidget(QLabel("Database:"), row, 4)
        self.db_combo = QComboBox()
        self.db_combo.addItems(["acore_world_test（测试服）", "acore_world（正式服）"])
        self.db_combo.currentIndexChanged.connect(self.on_db_changed)
        config_layout.addWidget(self.db_combo, row, 5)
        
        layout.addWidget(config_group)
        
        # 按钮行
        btn_layout = QHBoxLayout()
        
        read_config_btn = QPushButton("读取配置")
        read_config_btn.clicked.connect(self.load_config_from_file)
        btn_layout.addWidget(read_config_btn)
        
        save_config_btn = QPushButton("保存配置")
        save_config_btn.clicked.connect(self.save_config_to_file)
        btn_layout.addWidget(save_config_btn)
        
        self.save_config_check = QCheckBox("SaveAccount(保存账号)")
        self.save_config_check.setChecked(True)
        btn_layout.addWidget(self.save_config_check)
        
        self.save_password_check = QCheckBox("SavePassword(保存密码)")
        self.save_password_check.setChecked(True)
        btn_layout.addWidget(self.save_password_check)
        
        btn_layout.addStretch()
        
        self.status_label = QLabel("状态: 测试服")
        self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
        btn_layout.addWidget(self.status_label)
        
        test_btn = QPushButton("连接数据库")
        test_btn.clicked.connect(self.test_connection)
        test_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_layout.addWidget(test_btn)
        
        layout.addLayout(btn_layout)
        return frame
    
    def create_left_panel(self):
        """左侧：基本字段"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Entry
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
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QGridLayout(basic_group)
        row = 0
        for label, field, width in [
            ("名称(英文)", "name_en", 300),
            ("名称(中文)", "name_zh", 300),
            ("描述(英文)", "desc_en", 300),
            ("描述(中文)", "desc_zh", 300),
            ("显示ID", "displayid", 100),
            ("物品等级", "itemlevel", 80),
            ("需要等级", "requiredlevel", 80),
            ("绑定类型", "bonding", 150),
            ("购买数量", "buycount", 80),
            ("购买价格", "buyprice", 100),
            ("出售价格", "sellprice", 100),
            ("堆叠数量", "stackable", 80),
            ("最大数量", "maxcount", 80),
            ("容器槽位", "containerslots", 80),
        ]:
            basic_layout.addWidget(QLabel(label), row, 0)
            if field == 'bonding':
                self.fields[field] = QComboBox()
                self.fields[field].addItems(["0-不绑定", "1-拾取绑定", "2-装备绑定", "3-使用绑定", "4-任务物品", "5-账号绑定"])
                self.fields[field].setMaximumWidth(width)
            else:
                self.fields[field] = QLineEdit()
                if width:
                    self.fields[field].setMaximumWidth(width)
            basic_layout.addWidget(self.fields[field], row, 1)
            row += 1
        layout.addWidget(basic_group)
        
        # 分类和属性
        class_group = QGroupBox("分类和属性")
        class_layout = QGridLayout(class_group)
        row = 0
        for label, field, items in [
            ("物品类型", "class_id", ["0-消耗品", "1-容器", "2-武器", "3-宝石", "4-护甲", "5-材料", "6-弹药", "7-商品", "8-配方", "9-钱币", "10-任务物品", "11-钥匙", "12-永久物品", "13-垃圾"]),
            ("子类型", "subclass", ["0-通用", "1-斧", "2-弓", "3-枪", "4-单手锤", "5-长柄", "6-单手剑", "7-法杖", "8-匕首", "9-拳套", "10-盾牌", "11-法杖", "12-弩", "13-魔杖", "14-鱼竿"]),
            ("品质", "quality", ["0-垃圾(灰)", "1-普通(白)", "2-优秀(绿)", "3-精良(蓝)", "4-史诗(紫)", "5-传说(橙)", "6-神器(黄)"]),
            ("装备槽", "inventorytype", ["0-非装备", "1-头部", "2-颈部", "3-肩部", "4-衬衫", "5-胸甲", "6-腰带", "7-腿部", "8-脚", "9-手腕", "10-手套", "11-手指", "12-饰品", "13-单手", "14-盾牌", "15-弓", "16-背部", "17-双手", "18-袋子", "19-徽章", "20-法袍", "21-主手", "22-副手", "23-箭", "24-子弹"]),
            ("材质", "material", ["0-无", "1-金属", "2-木材", "3-液体", "4-珠宝", "5-链甲", "6-板甲", "7-布甲", "8-皮革"]),
            ("护甲", "armor", None),
            ("耐久度", "maxdurability", None),
            ("延迟", "delay", None),
        ]:
            class_layout.addWidget(QLabel(label), row, 0)
            if items:
                self.fields[field] = QComboBox()
                self.fields[field].addItems(items)
                self.fields[field].setMaximumWidth(200)
            else:
                self.fields[field] = QLineEdit()
                self.fields[field].setMaximumWidth(100)
            class_layout.addWidget(self.fields[field], row, 1)
            row += 1
        layout.addWidget(class_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_right_panel(self):
        """右侧：详细字段（选项卡）"""
        tabs = QTabWidget()
        
        # 选项卡1：属性（带类型）
        stats_tab = QWidget()
        stats_layout = QGridLayout(stats_tab)
        row = 0
        for i in range(1, 6):
            stats_layout.addWidget(QLabel(f"属性{i}类型"), row, 0)
            self.fields[f'stat_type{i}'] = QComboBox()
            self.fields[f'stat_type{i}'].addItems(["0-无", "1-力量", "2-敏捷", "3-耐力", "4-智力", "5-精神", "6-攻击强度", "7-法术强度", "18-护甲穿透", "19-格挡", "20-精准", "21-躲闪", "22-招架", "23-五秒回蓝", "24-法术穿透"])
            stats_layout.addWidget(self.fields[f'stat_type{i}'], row, 1)
            
            stats_layout.addWidget(QLabel(f"属性{i}值"), row, 2)
            self.fields[f'stat_value{i}'] = QLineEdit()
            self.fields[f'stat_value{i}'].setMaximumWidth(80)
            stats_layout.addWidget(self.fields[f'stat_value{i}'], row, 3)
            row += 1
        
        # 抗性
        for label, field in [("神圣抗性", "holy_res"), ("火焰抗性", "fire_res"), ("自然抗性", "nature_res"), ("冰霜抗性", "frost_res"), ("暗影抗性", "shadow_res"), ("奥术抗性", "arcane_res")]:
            stats_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(80)
            stats_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        tabs.addTab(stats_tab, "属性")
        
        # 选项卡2：伤害
        combat_tab = QWidget()
        combat_layout = QGridLayout(combat_tab)
        row = 0
        for i in range(1, 3):
            combat_layout.addWidget(QLabel(f"伤害{i}最小"), row, 0)
            self.fields[f'dmg_min{i}'] = QLineEdit()
            self.fields[f'dmg_min{i}'].setMaximumWidth(80)
            combat_layout.addWidget(self.fields[f'dmg_min{i}'], row, 1)
            
            combat_layout.addWidget(QLabel(f"伤害{i}最大"), row, 2)
            self.fields[f'dmg_max{i}'] = QLineEdit()
            self.fields[f'dmg_max{i}'].setMaximumWidth(80)
            combat_layout.addWidget(self.fields[f'dmg_max{i}'], row, 3)
            
            combat_layout.addWidget(QLabel(f"伤害{i}类型"), row, 4)
            self.fields[f'dmg_type{i}'] = QComboBox()
            self.fields[f'dmg_type{i}'].addItems(["0-物理", "1-神圣", "2-火焰", "3-自然", "4-冰霜", "5-暗影", "6-奥术"])
            combat_layout.addWidget(self.fields[f'dmg_type{i}'], row, 5)
            row += 1
        
        for label, field in [("攻击速度", "delay"), ("射程", "rangedmodrange"), ("格挡", "block")]:
            combat_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(100)
            combat_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        tabs.addTab(combat_tab, "伤害")
        
        # 选项卡3：法术（完整版）
        spells_tab = QWidget()
        spells_layout = QGridLayout(spells_tab)
        for i in range(1, 6):
            row = i - 1
            spells_layout.addWidget(QLabel(f"法术{i}ID"), row, 0)
            self.fields[f'spellid_{i}'] = QLineEdit()
            self.fields[f'spellid_{i}'].setMaximumWidth(100)
            spells_layout.addWidget(self.fields[f'spellid_{i}'], row, 1)
            
            spells_layout.addWidget(QLabel(f"触发{i}"), row, 2)
            self.fields[f'spelltrigger_{i}'] = QComboBox()
            self.fields[f'spelltrigger_{i}'].addItems(["0-使用", "1-装备", "2-被动"])
            spells_layout.addWidget(self.fields[f'spelltrigger_{i}'], row, 3)
            
            spells_layout.addWidget(QLabel(f"次数{i}"), row, 4)
            self.fields[f'spellcharges_{i}'] = QLineEdit()
            self.fields[f'spellcharges_{i}'].setMaximumWidth(80)
            spells_layout.addWidget(self.fields[f'spellcharges_{i}'], row, 5)
        
        tabs.addTab(spells_tab, "法术")
        
        # 选项卡4：Socket
        socket_tab = QWidget()
        socket_layout = QGridLayout(socket_tab)
        row = 0
        for i in range(1, 4):
            socket_layout.addWidget(QLabel(f"插槽{i}颜色"), row, 0)
            self.fields[f'socketColor_{i}'] = QComboBox()
            self.fields[f'socketColor_{i}'].addItems(["0-无", "1-红色", "2-黄色", "4-蓝色", "8-多彩"])
            socket_layout.addWidget(self.fields[f'socketColor_{i}'], row, 1)
            row += 1
        
        socket_layout.addWidget(QLabel("插槽奖励"), row, 0)
        self.fields['socketbonus'] = QLineEdit()
        self.fields['socketbonus'].setMaximumWidth(200)
        socket_layout.addWidget(self.fields['socketbonus'], row, 1)
        
        tabs.addTab(socket_tab, "Socket")
        
        # 选项卡5：要求
        req_tab = QWidget()
        req_layout = QGridLayout(req_tab)
        row = 0
        for label, field in [
            ("需要技能", "requiredskill"), ("技能等级", "requiredskillrank"),
            ("需要法术", "requiredspell"), ("需要阵营", "allowableclass"),
            ("需要种族", "allowablerace"), ("需要荣誉等级", "requiredhonorrank"),
            ("需要声望阵营", "requiredreputationfaction"), ("需要声望等级", "requiredreputationrank"),
            ("区域", "area"), ("地图", "map"),
            ("物品套装", "itemset"), ("锁ID", "lockid"),
        ]:
            req_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(100)
            req_layout.addWidget(self.fields[field], row, 1)
            row += 1
        tabs.addTab(req_tab, "要求")
        
        # 选项卡6：高级
        adv_tab = QWidget()
        adv_layout = QGridLayout(adv_tab)
        row = 0
        for label, field in [
            ("背包类别", "bagfamily"), ("持续时间", "duration"),
            ("随机属性", "randomproperty"), ("随机后缀", "randomsuffix"),
            ("弹药类型", "ammotype"), ("鞘", "sheath"),
            ("额外标志", "flagsextra"), ("任务文本ID", "pagetext"),
            ("语言ID", "languageid"), ("页面材质", "pagematerial"),
            ("需要分解技能", "required_disenchant_skill"), ("宝石属性", "gemproperties"),
        ]:
            adv_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(100)
            adv_layout.addWidget(self.fields[field], row, 1)
            row += 1
        tabs.addTab(adv_tab, "高级")
        
        # 选项卡7：SQL和补丁
        sql_tab = QWidget()
        sql_layout = QVBoxLayout(sql_tab)
        sql_layout.addWidget(QLabel("SQL语句预览:"))
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
        copy_btn = QPushButton("复制SQL")
        copy_btn.clicked.connect(self.copy_sql)
        btn_layout.addWidget(copy_btn)
        sql_layout.addLayout(btn_layout)
        
        exec_layout = QHBoxLayout()
        exec_btn = QPushButton("执行当前SQL")
        exec_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold;")
        exec_btn.clicked.connect(self.execute_sql)
        exec_layout.addWidget(exec_btn)
        sql_layout.addLayout(exec_layout)
        
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
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        
        clone_btn = QPushButton("套用物品")
        clone_btn.setStyleSheet("background-color: #9c27b0; color: white;")
        clone_btn.clicked.connect(self.clone_item)
        layout.addWidget(clone_btn)
        
        search_btn = QPushButton("搜索物品")
        search_btn.setStyleSheet("background-color: #ff5722; color: white;")
        search_btn.clicked.connect(self.search_item)
        layout.addWidget(search_btn)
        
        layout.addStretch()
        
        self.env_info = QLabel()
        self.update_env_info()
        layout.addWidget(self.env_info)
        
        return frame
    
    # 以下是所有方法（保持不变）
    def on_mode_changed(self, index):
        mode = "remote" if index == 0 else "direct"
        self.config['mode'] = mode
        self.status_label.setText(f"状态: 模式={mode}")
    
    def on_db_changed(self, index):
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
        db = self.config['db']['database']
        env = 'test' if 'test' in db else 'release'
        self.env_info.setText(f"{'测试服' if env == 'test' else '正式服'} | 推送: /patches/{env}/")
    
    def load_config_from_file(self):
        try:
            if CONFIG_FILE.exists():
                with CONFIG_FILE.open('r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.config.update(saved)
                    QMessageBox.information(self, "成功", "配置读取成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取配置失败：{e}")
    
    def save_config_to_file(self):
        try:
            with CONFIG_FILE.open('w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "成功", "配置保存成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败：{e}")
    
    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open('r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.config.update(saved)
                    self.update_env_info()
            except:
                pass
    
    def test_connection(self):
        try:
            conn = pymysql.connect(**self.config['db'], connect_timeout=5)
            conn.close()
            QMessageBox.information(self, "成功", "数据库连接成功！")
        except Exception as e:
            QMessageBox.critical(self, "失败", f"连接失败：{e}")
    
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
                }
                for i in range(1, 6):
                    field_map[f'stat_type{i}'] = f'stat_type{i}'
                    field_map[f'stat_value{i}'] = f'stat_value{i}'
                for i in range(1, 6):
                    field_map[f'spellid_{i}'] = f'spellid_{i}'
                    field_map[f'spelltrigger_{i}'] = f'spelltrigger_{i}'
                    field_map[f'spellcharges_{i}'] = f'spellcharges_{i}'
                for i in range(1, 3):
                    field_map[f'dmg_min{i}'] = f'dmg_min{i}'
                    field_map[f'dmg_max{i}'] = f'dmg_max{i}'
                    field_map[f'dmg_type{i}'] = f'dmg_type{i}'
                for i in range(1, 4):
                    field_map[f'socketColor_{i}'] = f'socketColor_{i}'
                field_map.update({
                    'holy_res': 'holy_res', 'fire_res': 'fire_res',
                    'nature_res': 'nature_res', 'frost_res': 'frost_res',
                    'shadow_res': 'shadow_res', 'arcane_res': 'arcane_res',
                    'socketBonus': 'socketbonus', 'RandomProperty': 'randomproperty',
                    'RandomSuffix': 'randomsuffix', 'BagFamily': 'bagfamily',
                    'duration': 'duration', 'FlagsExtra': 'flagsextra',
                    'ammo_type': 'ammotype', 'sheath': 'sheath',
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
        entry = self.get_field_value('entry')
        if not entry:
            QMessageBox.warning(self, "警告", "请输入物品 Entry")
            return
        QMessageBox.information(self, "提示", "保存功能开发中...")
    
    def delete_item(self):
        entry = self.get_field_value('entry')
        if not entry:
            QMessageBox.warning(self, "警告", "请输入物品 Entry")
            return
        reply = QMessageBox.question(self, "确认删除", f"确定要删除物品 {entry} 吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            conn = pymysql.connect(**self.config['db'])
            with conn.cursor() as cur:
                cur.execute("DELETE FROM item_template WHERE entry = %s", (entry,))
                cur.execute("DELETE FROM item_template_locale WHERE ID = %s AND locale = 'zhCN'", (entry,))
                conn.commit()
            conn.close()
            QMessageBox.information(self, "成功", f"物品 {entry} 已删除")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败：{e}")
    
    def generate_sql(self, sql_type):
        entry = self.get_field_value('entry')
        name = self.get_field_value('name_en')
        if sql_type == "INSERT":
            sql = f"INSERT INTO item_template (entry, name, displayid, Quality, class, subclass, InventoryType, Material) VALUES ({entry}, '{name}', {self.get_field_value('displayid') or 0}, {self.get_field_value('quality') or 0}, {self.get_field_value('class_id') or 0}, {self.get_field_value('subclass') or 0}, {self.get_field_value('inventorytype') or 0}, {self.get_field_value('material') or 0});"
        elif sql_type == "UPDATE":
            sql = f"UPDATE item_template SET name='{name}', displayid={self.get_field_value('displayid') or 0}, Quality={self.get_field_value('quality') or 0}, class={self.get_field_value('class_id') or 0}, subclass={self.get_field_value('subclass') or 0}, InventoryType={self.get_field_value('inventorytype') or 0}, Material={self.get_field_value('material') or 0} WHERE entry={entry};"
        else:
            sql = f"DELETE FROM item_template WHERE entry={entry};"
        self.sql_text.setPlainText(sql)
    
    def copy_sql(self):
        QApplication.clipboard().setText(self.sql_text.toPlainText())
        QMessageBox.information(self, "成功", "SQL已复制到剪贴板")
    
    def execute_sql(self):
        sql = self.sql_text.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "警告", "SQL语句为空")
            return
        reply = QMessageBox.question(self, "确认执行", f"确定要执行吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            conn = pymysql.connect(**self.config['db'])
            with conn.cursor() as cur:
                cur.execute(sql)
                conn.commit()
                affected = cur.rowcount
            conn.close()
            QMessageBox.information(self, "成功", f"SQL执行成功\n影响行数：{affected}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行失败：{e}")
    
    def clone_item(self):
        dialog = CloneItemDialog(self, self.get_field_value('entry'))
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "提示", "套用功能开发中...")
    
    def search_item(self):
        dialog = SearchItemDialog(self, self.config['db'])
        if dialog.exec_() == QDialog.Accepted:
            entry = dialog.get_selected_entry()
            if entry:
                self.set_field_value('entry', entry)
                self.load_item()
    
    def generate_patch(self):
        QMessageBox.information(self, "提示", "问号补丁生成功能开发中...")
    
    def push_patch(self):
        QMessageBox.information(self, "提示", "推送补丁功能开发中...")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    icon_path = Path(__file__).parent / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = WOWItemMakerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
