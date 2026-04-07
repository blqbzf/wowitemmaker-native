#!/usr/bin/env python3
"""
测试数据库连接
"""
import pymysql

# 测试连接
configs = [
    {
        "name": "测试1: 43.248.129.172:3306 wowitem",
        "config": {
            "host": "43.248.129.172",
            "port": 3306,
            "user": "wowitem",
            "password": "GknNJLRtcE6RzigVJFF8",
            "database": "acore_world_test",
            "connect_timeout": 10
        }
    },
    {
        "name": "测试2: 43.248.129.172:3306 wowitem (密码2)",
        "config": {
            "host": "43.248.129.172",
            "port": 3306,
            "user": "wowitem",
            "password": "GknNJLRtcE6RzigVJFF8",
            "database": "acore_world_test",
            "connect_timeout": 10
        }
    },
    {
        "name": "测试3: 43.248.129.172:3306 root",
        "config": {
            "host": "43.248.129.172",
            "port": 3306,
            "user": "root",
            "password": "4b2d30200120feb3",
            "database": "acore_world_test",
            "connect_timeout": 10
        }
    }
]

for test in configs:
    print(f"\n{'='*60}")
    print(f"测试: {test['name']}")
    print(f"{'='*60}")
    
    try:
        conn = pymysql.connect(**test['config'])
        print("✅ 连接成功!")
        
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM item_template")
            count = cur.fetchone()[0]
            print(f"   物品数量: {count}")
        
        conn.close()
        print("✅ 测试通过，使用此配置")
        break
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print(f"   配置: {test['config']}")
