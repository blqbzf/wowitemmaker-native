#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import threading
import webbrowser
from pathlib import Path

from PyQt5.QtCore import QUrl, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenuBar, QAction, QMessageBox, QLabel, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtGui import QIcon, QDesktopServices

# 导入服务器
import server as backend_server

class WOWItemMakerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("诺兰时光物品工具 v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置窗口图标（如果有）
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建 WebEngine 视图
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)
        
        # 状态栏
        self.statusBar().showMessage("正在连接数据库...")
        
        # 创建菜单
        self.create_menu()
        
        # 启动服务器线程
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        
        # 延迟加载网页
        QTimer.singleShot(1000, self.load_page)
    
    def start_server(self):
        """在后台启动服务器"""
        try:
            backend_server.run_server()
        except Exception as e:
            print(f"服务器启动失败: {e}")
    
    def load_page(self):
        """加载网页"""
        html_path = Path(__file__).parent / "minimal-app.html"
        if html_path.exists():
            self.browser.setUrl(QUrl.fromLocalFile(str(html_path)))
            self.statusBar().showMessage("就绪")
        else:
            self.statusBar().showMessage("错误: 找不到界面文件")
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 打开浏览器
        open_browser_action = QAction("在浏览器中打开(&B)", self)
        open_browser_action.setShortcut("Ctrl+B")
        open_browser_action.triggered.connect(self.open_in_browser)
        file_menu.addAction(open_browser_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def open_in_browser(self):
        """在默认浏览器中打开"""
        webbrowser.open("http://127.0.0.1:8000/minimal-app.html")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于诺兰时光物品工具",
            """<h2>诺兰时光物品工具 v1.0</h2>
            <p>一个强大的魔兽世界物品编辑工具</p>
            <p>支持：</p>
            <ul>
                <li>物品读取/编辑/删除</li>
                <li>物品模板复制</li>
                <li>Item.dbc 补丁生成</li>
                <li>MPQ 补丁打包</li>
                <li>服务器补丁推送</li>
            </ul>
            <p>© 2026 诺兰时光魔兽</p>"""
        )
    
    def closeEvent(self, event):
        """关闭窗口时的事件"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    # 启用高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("诺兰时光物品工具")
    app.setOrganizationName("诺兰时光魔兽")
    
    window = WOWItemMakerWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
