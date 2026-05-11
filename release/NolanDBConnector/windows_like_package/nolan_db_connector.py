#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox, QLabel, QHBoxLayout
from PyQt5.QtGui import QFont
import pymysql

BASE = Path(__file__).resolve().parent
CONFIG_JSON = BASE / 'conninfo.json'
CONNINFO_CFG = BASE / 'ConnInfo.cfg'
FONT = QFont("Microsoft YaHei", 11)

DEFAULT = {
    'db': {'host':'43.248.129.172','port':3306,'user':'root','password':'','database':'acore_world'},
    'savePassword': True
}

def load_cfg():
    if CONFIG_JSON.exists():
        try:
            return json.loads(CONFIG_JSON.read_text(encoding='utf-8'))
        except Exception:
            pass
    return DEFAULT.copy()

def save_cfg(cfg):
    CONFIG_JSON.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
    xml = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<WOWItemMaker>
  <HostName>{cfg['db']['host']}</HostName>
  <UserName>{cfg['db']['user']}</UserName>
  <PassWord>{cfg['db']['password'] if cfg.get('savePassword') else ''}</PassWord>
  <DataBase>{cfg['db']['database']}</DataBase>
  <Dbstruct>TrinityCore</Dbstruct>
</WOWItemMaker>
"""
    CONNINFO_CFG.write_text(xml, encoding='utf-8')

class W(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('诺兰时光数据库连接器')
        self.resize(520, 260)
        self.setFont(FONT)
        self.cfg = load_cfg()
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel('用途：测试数据库连接，并生成 WOWItemMaker 可用的 ConnInfo.cfg'))
        form = QFormLayout()
        self.host = QLineEdit(str(self.cfg['db'].get('host','')))
        self.port = QLineEdit(str(self.cfg['db'].get('port',3306)))
        self.user = QLineEdit(str(self.cfg['db'].get('user','')))
        self.password = QLineEdit(str(self.cfg['db'].get('password','')))
        self.password.setEchoMode(QLineEdit.Password)
        self.db = QLineEdit(str(self.cfg['db'].get('database','acore_world')))
        for n,w in [('Host',self.host),('Port',self.port),('User',self.user),('Password',self.password),('Database',self.db)]:
            form.addRow(n, w)
        lay.addLayout(form)
        row = QHBoxLayout()
        self.btn_test = QPushButton('测试连接')
        self.btn_save = QPushButton('保存配置并生成 ConnInfo.cfg')
        self.btn_test.clicked.connect(self.test_conn)
        self.btn_save.clicked.connect(self.save_only)
        row.addWidget(self.btn_test)
        row.addWidget(self.btn_save)
        lay.addLayout(row)
    def current(self):
        return {'db': {'host': self.host.text().strip(), 'port': int(self.port.text().strip() or '3306'), 'user': self.user.text().strip(), 'password': self.password.text(), 'database': self.db.text().strip()}, 'savePassword': True}
    def test_conn(self):
        cfg = self.current()
        try:
            conn = pymysql.connect(**cfg['db'], connect_timeout=8)
            with conn.cursor() as cur:
                cur.execute('SELECT DATABASE(), VERSION()')
                row = cur.fetchone()
            conn.close()
            save_cfg(cfg)
            QMessageBox.information(self, '成功', f'连接成功\nDB: {row[0]}\nVersion: {row[1]}\n\n已保存 conninfo.json 和 ConnInfo.cfg')
        except Exception as e:
            QMessageBox.critical(self, '连接失败', str(e))
    def save_only(self):
        cfg = self.current()
        save_cfg(cfg)
        QMessageBox.information(self, '已保存', '已生成 conninfo.json 和 ConnInfo.cfg')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = W()
    w.show()
    sys.exit(app.exec_())
