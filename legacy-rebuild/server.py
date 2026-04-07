#!/usr/bin/env python3
import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = {
  "class": ["0 消耗品", "1 容器", "2 武器", "4 护甲", "15 杂项"],
  "subclass0": ["0 消耗品"],
  "quality": ["0 普通", "1 优秀", "2 精良", "3 稀有", "4 史诗", "5 传说", "6 神器", "7 传家宝"],
  "displayid": ["0", "1143", "21600", "33681"],
  "bonding": ["0 不绑定", "1 拾取绑定", "2 装备绑定", "3 使用绑定", "4 任务绑定"],
  "flags": ["0", "1 灵魂绑定", "64 可触发使用", "32768 独特"],
  "ammo_type": ["0 无", "2 箭", "3 子弹"],
  "stats_count": [str(i) for i in range(0,11)],
  "inventory_type": ["0 非装备", "1 头部", "2 颈部", "3 肩部", "4 衬衣", "5 胸部", "13 单手", "14 盾牌", "15 远程", "16 背部", "17 双手", "21 主手", "22 副手", "23 持有", "24 弹药", "25 投掷", "26 远程右", "28 圣物"],
  "sheath": ["0 无", "1 单手", "2 双手", "3 腰间"],
  "material": ["-1 消耗品", "0 未知", "1 金属", "2 木材", "3 液体", "4 珠宝", "5 链甲", "6 板甲", "7 布甲", "8 皮甲"],
  "spellid": ["0", "470", "483", "8690", "25990"],
  "spelltrigger": ["0 使用", "1 装备", "2 命中", "4 灵魂石", "5 学习法术"],
  "socketColor": ["0 无", "1 多彩", "2 红", "4 黄", "8 蓝"],
  "socketBonus": ["0", "3312", "3753", "2872"],
  "randomProperty": ["0", "1 随机属性1", "2 随机属性2"],
  "randomSuffix": ["0", "1 猫头鹰", "2 雄鹰"],
  "area": ["0 无", "1519 暴风城", "1637 奥格瑞玛"],
  "map": ["0 无", "0 Eastern Kingdoms", "1 Kalimdor", "530 Outland", "571 Northrend"]
}

class H(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/dicts':
            body = json.dumps({"ok": True, "dicts": DATA}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8010), H).serve_forever()
