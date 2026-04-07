#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诺兰时光物品工具 - 原生桌面版
使用 PyQt5 原生控件，不依赖浏览器
"""

import sys
import json
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QGroupBox,
    QGridLayout, QMessageBox, QSplitter, QFrame, QScrollArea, QTabWidget
)
from PyQt5.QtGui import QFont

import pymysql


class WOWItemMakerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("诺兰时光物品工具 v2.0 - 原生版")
        self.setGeometry(100, 100, 1400, 900)
        
        # 数据库配置
        self.config = {
            "host": "43.248.129.172",
            "port": 3306,
            "user": "wowitem",
            "password": "GknNJLRtcE6RzigVJFF8",
            "database": "acore_world_test"
        }
        
        # 字段映射
        self.fields = {}
        
        # 创建界面
        self.create_ui()
        
        # 加载数据字典
        self.load_dicts()
    
    def create_ui(self):
        """创建界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部：数据库选择和连接
        top_frame = self.create_top_panel()
        main_layout.addWidget(top_frame)
        
        # 中间：分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：物品基本字段
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：物品详细字段（选项卡）
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([600, 800])
        main_layout.addWidget(splitter)
        
        # 底部：操作按钮
        bottom_frame = self.create_bottom_panel()
        main_layout.addWidget(bottom_frame)
    
    def create_top_panel(self):
        """创建顶部面板"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        
        # 数据库选择
        layout.addWidget(QLabel("数据库："))
        self.db_combo = QComboBox()
        self.db_combo.addItems(["acore_world_test（测试服）", "acore_world（正式服）"])
        self.db_combo.currentIndexChanged.connect(self.on_db_changed)
        layout.addWidget(self.db_combo)
        
        # 环境状态
        self.status_label = QLabel("状态：测试服")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 连接测试
        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self.test_connection)
        layout.addWidget(test_btn)
        
        return frame
    
    def create_left_panel(self):
        """创建左侧面板：基本字段"""
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
        delete_btn.setStyleSheet("background-color: #ff6b6b;")
        delete_btn.clicked.connect(self.delete_item)
        entry_layout.addWidget(delete_btn)
        
        layout.addWidget(entry_group)
        
        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QGridLayout(basic_group)
        
        row = 0
        for label, field, width in [
            ("名称（英文）", "name_en", 300),
            ("名称（中文）", "name_zh", 300),
            ("描述（英文）", "desc_en", 300),
            ("描述（中文）", "desc_zh", 300),
            ("显示ID", "displayid", 100),
            ("物品等级", "itemlevel", 80),
            ("RequiredLevel", "requiredlevel", 80),
        ]:
            basic_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            if width:
                self.fields[field].setMaximumWidth(width)
            basic_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        layout.addWidget(basic_group)
        
        # 分类和属性
        class_group = QGroupBox("分类和属性")
        class_layout = QGridLayout(class_group)
        
        # 下拉框字段
        row = 0
        for label, field, items in [
            ("物品类型", "class_id", ["0-消耗品", "1-容器", "2-武器", "3-宝石", "4-护甲", "5-材料", "6-弹药", "7-商品", "8-配方", "9-钱币", "10-任务物品", "11-钥匙", "12-永久物品", "13-垃圾"]),
            ("子类型", "subclass", ["0-通用", "1-斧", "2-弓", "3-枪", "4-单手锤", "5-长柄", "6-单手剑", "7-法杖", "8-匕首", "9-拳套", "10-盾牌", "11-法杖", "12-弩", "13-魔杖", "14-鱼竿"]),
            ("品质", "quality", ["0-垃圾(灰)", "1-普通(白)", "2-优秀(绿)", "3-精良(蓝)", "4-史诗(紫)", "5-传说(橙)", "6-神器(黄)"]),
            ("装备槽", "inventorytype", ["0-非装备", "1-头部", "2-颈部", "3-肩部", "4-衬衫", "5-胸甲", "6-腰带", "7-腿部", "8-脚", "9-手腕", "10-手套", "11-手指", "12-饰品", "13-单手", "14-盾牌", "15-弓", "16-背部", "17-双手", "18-袋子", "19-徽章", "20-法袍", "21-主手", "22-副手", "23-箭", "24-子弹"]),
            ("材质", "material", ["0-无", "1-金属", "2-木材", "3-液体", "4-珠宝", "5-链甲", "6-板甲", "7-布甲", "8-皮革"]),
        ]:
            class_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QComboBox()
            self.fields[field].addItems(items)
            self.fields[field].setMaximumWidth(200)
            class_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        # 数值字段
        for label, field in [
            ("购买价格", "buyprice"),
            ("出售价格", "sellprice"),
            ("堆叠数量", "stackable"),
            ("最大数量", "maxcount"),
            ("护甲", "armor"),
            ("耐久度", "maxdurability"),
            ("延迟", "delay"),
        ]:
            class_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(100)
            class_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        layout.addWidget(class_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_right_panel(self):
        """创建右侧面板：详细字段（选项卡）"""
        tabs = QTabWidget()
        
        # 选项卡1：属性
        stats_tab = QWidget()
        stats_layout = QGridLayout(stats_tab)
        
        row = 0
        for label, field in [
            ("力量", "stat_value1"), ("敏捷", "stat_value2"),
            ("耐力", "stat_value3"), ("智力", "stat_value4"),
            ("精神", "stat_value5"),
            ("神圣抗性", "holy_res"), ("火焰抗性", "fire_res"),
            ("自然抗性", "nature_res"), ("冰霜抗性", "frost_res"),
            ("暗影抗性", "shadow_res"), ("奥术抗性", "arcane_res"),
        ]:
            stats_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(80)
            stats_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        tabs.addTab(stats_tab, "属性")
        
        # 选项卡2：法术效果
        spells_tab = QWidget()
        spells_layout = QGridLayout(spells_tab)
        
        for i in range(1, 6):
            row = i - 1
            spells_layout.addWidget(QLabel(f"法术{i} ID"), row, 0)
            self.fields[f'spellid_{i}'] = QLineEdit()
            self.fields[f'spellid_{i}'].setMaximumWidth(100)
            spells_layout.addWidget(self.fields[f'spellid_{i}'], row, 1)
            
            spells_layout.addWidget(QLabel(f"触发{i}"), row, 2)
            self.fields[f'spelltrigger_{i}'] = QComboBox()
            self.fields[f'spelltrigger_{i}'].addItems(["0-使用", "1-装备", "2-被动"])
            spells_layout.addWidget(self.fields[f'spelltrigger_{i}'], row, 3)
        
        tabs.addTab(spells_tab, "法术")
        
        # 选项卡3：要求
        req_tab = QWidget()
        req_layout = QGridLayout(req_tab)
        
        row = 0
        for label, field in [
            ("需要技能", "required_skill"),
            ("技能等级", "required_skill_rank"),
            ("需要法术", "requiredspell"),
            ("需要阵营", "allowableclass"),
            ("需要种族", "allowablerace"),
            ("需要声望阵营", "required_reputation_faction"),
            ("需要声望等级", "required_reputation_rank"),
            ("需要荣誉等级", "requiredhonorrank"),
            ("区域", "area"),
            ("地图", "map"),
        ]:
            req_layout.addWidget(QLabel(label), row, 0)
            self.fields[field] = QLineEdit()
            self.fields[field].setMaximumWidth(100)
            req_layout.addWidget(self.fields[field], row, 1)
            row += 1
        
        tabs.addTab(req_tab, "要求")
        
        # 选项卡4：SQL和补丁
        sql_tab = QWidget()
        sql_layout = QVBoxLayout(sql_tab)
        
        # SQL预览
        sql_layout.addWidget(QLabel("SQL语句预览："))
        self.sql_text = QTextEdit()
        self.sql_text.setFont(QFont("Monaco", 10))
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
        clone_btn.clicked.connect(self.clone_item)
        layout.addWidget(clone_btn)
        
        # 搜索物品
        search_btn = QPushButton("搜索物品")
        search_btn.clicked.connect(self.search_item)
        layout.addWidget(search_btn)
        
        layout.addStretch()
        
        # 环境提示
        self.env_info = QLabel()
        self.update_env_info()
        layout.addWidget(self.env_info)
        
        return frame
    
    def load_dicts(self):
        """加载数据字典"""
        dict_path = Path(__file__).parent / "wowitemmaker-data-dicts.json"
        if dict_path.exists():
            with open(dict_path, 'r', encoding='utf-8') as f:
                self.dicts = json.load(f)
    
    def on_db_changed(self, index):
        """数据库切换"""
        if index == 0:
            self.config['database'] = 'acore_world_test'
            self.status_label.setText("状态：测试服")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.config['database'] = 'acore_world'
            self.status_label.setText("状态：正式服")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.update_env_info()
    
    def update_env_info(self):
        """更新环境信息"""
        db = self.config['database']
        if 'test' in db:
            self.env_info.setText("测试服 | 推送目标: /patches/test/ | 登录器: combined-test-manifest.json")
        else:
            self.env_info.setText("正式服 | 推送目标: /patches/release/ | 登录器: combined-release-manifest.json")
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            conn = pymysql.connect(**self.config, connect_timeout=5)
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
            conn = pymysql.connect(**self.config)
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM item_template WHERE entry = %s", (entry,))
                row = cur.fetchone()
                
                if not row:
                    QMessageBox.warning(self, "警告", f"未找到物品 {entry}")
                    return
                
                # 获取字段名
                columns = [desc[0] for desc in cur.description]
                item = dict(zip(columns, row))
                
                # 填充字段
                field_map = {
                    'name': 'name_en', 'description': 'desc_en',
                    'displayid': 'displayid', 'ItemLevel': 'itemlevel',
                    'RequiredLevel': 'requiredlevel', 'class': 'class_id',
                    'subclass': 'subclass', 'Quality': 'quality',
                    'InventoryType': 'inventorytype', 'Material': 'material',
                    'BuyPrice': 'buyprice', 'SellPrice': 'sellprice',
                    'stackable': 'stackable', 'maxcount': 'maxcount',
                    'armor': 'armor', 'MaxDurability': 'maxdurability',
                    'delay': 'delay', 'stat_value1': 'stat_value1',
                    'stat_value2': 'stat_value2', 'stat_value3': 'stat_value3',
                    'stat_value4': 'stat_value4', 'stat_value5': 'stat_value5',
                    'holy_res': 'holy_res', 'fire_res': 'fire_res',
                    'nature_res': 'nature_res', 'frost_res': 'frost_res',
                    'shadow_res': 'shadow_res', 'arcane_res': 'arcane_res',
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
        
        # 收集字段值
        item_data = {
            'entry': entry,
            'name': self.get_field_value('name_en'),
            'displayid': self.get_field_value('displayid') or 0,
            'ItemLevel': self.get_field_value('itemlevel') or 0,
            'RequiredLevel': self.get_field_value('requiredlevel') or 0,
            'class': self.get_field_value('class_id') or 0,
            'subclass': self.get_field_value('subclass') or 0,
            'Quality': self.get_field_value('quality') or 0,
            'InventoryType': self.get_field_value('inventorytype') or 0,
            'Material': self.get_field_value('material') or 0,
            'BuyPrice': self.get_field_value('buyprice') or 0,
            'SellPrice': self.get_field_value('sellprice') or 0,
            'stackable': self.get_field_value('stackable') or 1,
            'maxcount': self.get_field_value('maxcount') or 0,
            'armor': self.get_field_value('armor') or 0,
            'MaxDurability': self.get_field_value('maxdurability') or 0,
            'delay': self.get_field_value('delay') or 0,
        }
        
        try:
            conn = pymysql.connect(**self.config)
            with conn.cursor() as cur:
                # 检查是否存在
                cur.execute("SELECT entry FROM item_template WHERE entry = %s", (entry,))
                exists = cur.fetchone()
                
                if exists:
                    # 更新
                    sql = """UPDATE item_template SET 
                        name=%(name)s, displayid=%(displayid)s, ItemLevel=%(ItemLevel)s,
                        RequiredLevel=%(RequiredLevel)s, class=%(class)s, subclass=%(subclass)s,
                        Quality=%(Quality)s, InventoryType=%(InventoryType)s, Material=%(Material)s,
                        BuyPrice=%(BuyPrice)s, SellPrice=%(SellPrice)s, stackable=%(stackable)s,
                        maxcount=%(maxcount)s, armor=%(armor)s, MaxDurability=%(MaxDurability)s,
                        delay=%(delay)s
                        WHERE entry=%(entry)s"""
                else:
                    # 插入
                    sql = """INSERT INTO item_template (entry, name, displayid, ItemLevel, RequiredLevel,
                        class, subclass, Quality, InventoryType, Material, BuyPrice, SellPrice,
                        stackable, maxcount, armor, MaxDurability, delay)
                        VALUES (%(entry)s, %(name)s, %(displayid)s, %(ItemLevel)s, %(RequiredLevel)s,
                        %(class)s, %(subclass)s, %(Quality)s, %(InventoryType)s, %(Material)s,
                        %(BuyPrice)s, %(SellPrice)s, %(stackable)s, %(maxcount)s, %(armor)s,
                        %(MaxDurability)s, %(delay)s)"""
                
                cur.execute(sql, item_data)
                
                # 保存中文名
                name_zh = self.get_field_value('name_zh')
                desc_zh = self.get_field_value('desc_zh')
                if name_zh:
                    cur.execute("""REPLACE INTO item_template_locale (ID, locale, Name, Description)
                        VALUES (%s, 'zhCN', %s, %s)""", (entry, name_zh, desc_zh))
                
                conn.commit()
            
            conn.close()
            QMessageBox.information(self, "成功", f"物品 {entry} 保存成功")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：{e}")
    
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
            conn = pymysql.connect(**self.config)
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
    
    def clone_item(self):
        """套用物品"""
        QMessageBox.information(self, "提示", "套用物品功能开发中...")
    
    def search_item(self):
        """搜索物品"""
        QMessageBox.information(self, "提示", "搜索物品功能开发中...")
    
    def generate_patch(self):
        """生成补丁"""
        QMessageBox.information(self, "提示", "生成补丁功能开发中...")
    
    def push_patch(self):
        """推送补丁"""
        QMessageBox.information(self, "提示", "推送补丁功能开发中...")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 跨平台统一风格
    
    window = WOWItemMakerWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
