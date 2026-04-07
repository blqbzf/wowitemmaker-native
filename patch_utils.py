#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补丁生成和推送功能
集成到原生应用
"""

import sys
import json
import csv
import struct
import subprocess
import tempfile
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtGui import QIcon

import pymysql


def build_item_patch(db_config, custom_items, output_path):
    """
    生成Item.dbc补丁
    
    Args:
        db_config: 数据库配置
        custom_items: 自定义物品entry列表，如 [910000, 910001, 910002]
        output_path: 输出文件路径
    
    Returns:
        生成的Item.dbc路径
    """
    # 1. 从数据库导出自定义物品
    csv_data = []
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cur:
            placeholders = ','.join(['%s'] * len(custom_items))
            sql = f"""SELECT entry,class,subclass,SoundOverrideSubclass,material,displayid,InventoryType,sheath 
                FROM item_template 
                WHERE entry IN ({placeholders})"""
            cur.execute(sql, custom_items)
            rows = cur.fetchall()
            
            # 转换为CSV格式
            for row in rows:
                csv_data.append([str(x) for x in row])
        
        conn.close()
    except Exception as e:
        raise Exception(f"读取数据库失败: {e}")
    
    if not csv_data:
        raise Exception("没有找到自定义物品")
    
    # 2. 读取基础Item.dbc
    base_dbc = Path(__file__).parent / 'data' / 'Item.dbc'
    if not base_dbc.exists():
        # 尝试其他路径
        base_dbc = Path(__file__).parent.parent / 'data' / 'Item.dbc'
    
    if not base_dbc.exists():
        raise Exception(f"找不到基础Item.dbc文件")
    
    # 3. 合并数据并生成新的Item.dbc
    try:
        field_count, record_size, base_rows, string_block = read_dbc_table(base_dbc)
        
        # 合并数据
        merged_rows = merge_rows(base_rows, csv_data)
        
        # 生成新的Item.dbc
        save_dbc_table(output_path, merged_rows, field_count, string_block)
        
        return output_path
        
    except Exception as e:
        raise Exception(f"生成Item.dbc失败: {e}")


def read_dbc_table(path):
    """读取DBC文件"""
    data = path.read_bytes()
    magic, record_count, field_count, record_size, string_size = struct.unpack('<4s4I', data[:20])
    
    if magic != b'WDBC':
        raise ValueError(f'{path} 不是有效的DBC文件')
    
    start = 20
    records_end = start + record_count * record_size
    string_block = data[records_end:records_end + string_size]
    
    rows = []
    for i in range(record_count):
        off = start + i * record_size
        row = list(struct.unpack_from(f'<{field_count}I', data, off))
        rows.append([str(x) for x in row])
    
    return field_count, record_size, rows, string_block


def merge_rows(base_rows, csv_data):
    """合并CSV数据到基础数据"""
    csv_map = {int(row[0]): row for row in csv_data}
    
    merged = []
    for row in base_rows:
        entry = int(row[0])
        if entry in csv_map:
            merged.append(csv_map[entry])
        else:
            merged.append(row)
    
    return merged


def save_dbc_table(path, rows, field_count, string_block):
    """保存DBC文件"""
    # 重新构建字符串块
    string_bytes = bytearray(b'\\x00'.decode('unicode_escape').encode('latin1'))
    prepared = []
    
    for row in rows:
        out = []
        for i in range(field_count):
            if i < len(row):
                # 假设第一列是entry（数值），其他列需要从字符串块读取
                if i == 0:
                    out.append(int(row[i]))
                else:
                    text = str(row[i]) if row[i] else ''
                    if text:
                        off = len(string_bytes)
                        string_bytes.extend(text.encode('utf-8'))
                        string_bytes.extend(b'\\x00'.decode('unicode_escape').encode('latin1'))
                        out.append(off)
                    else:
                        out.append(0)
            else:
                out.append(0)
        prepared.append(out)
    
    # 写入文件
    with path.open('wb') as f:
        f.write(struct.pack('<4s4I', b'WDBC', len(prepared), field_count, field_count * 4, len(string_bytes)))
        for row in prepared:
            f.write(struct.pack(f'<{field_count}I', *row))
        f.write(string_bytes)


def push_patch_to_server(local_path, remote_path, ssh_config):
    """
    推送补丁到服务器
    
    Args:
        local_path: 本地补丁路径
        remote_path: 服务器远程路径
        ssh_config: SSH配置
            - host: 服务器地址
            - user: 用户名
            - key_path: SSH密钥路径
    
    Returns:
        bool: 是否成功
    """
    try:
        # 构建SCP命令
        cmd = [
            'scp',
            '-i', ssh_config['key_path'],
            '-o', 'StrictHostKeyChecking=no',
            str(local_path),
            f"{ssh_config['user']}@{ssh_config['host']}:{remote_path}"
        ]
        
        # 执行上传
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"SCP上传失败: {result.stderr.decode('utf-8', errors='ignore')}")
        
        return True
        
    except Exception as e:
        raise Exception(f"推送补丁失败: {e}")


def update_server_manifest(ssh_config, patch_filename, env='test'):
    """
    更新服务器上的manifest.json
    
    Args:
        ssh_config: SSH配置
        patch_filename: 补丁文件名
        env: 环境（test/release）
    """
    try:
        # 读取现有manifest
        manifest_path = f'/www/wwwroot/wow/patches/{env}/combined-{env}-manifest.json'
        
        cmd_read = [
            'ssh',
            '-i', ssh_config['key_path'],
            '-o', 'StrictHostKeyChecking=no',
            f"{ssh_config['user']}@{ssh_config['host']}",
            f'cat {manifest_path}'
        ]
        
        result = subprocess.run(cmd_read, capture_output=True, text=True)
        
        if result.returncode == 0:
            manifest = json.loads(result.stdout)
        else:
            manifest = {"patches": []}
        
        # 更新补丁列表
        patch_entry = {
            "filename": patch_filename,
            "version": "1.0.0",
            "sha256": ""  # 可以计算SHA256，这里简化
        }
        
        # 移除旧的同一补丁
        manifest['patches'] = [p for p in manifest['patches'] if p['filename'] != patch_filename]
        manifest['patches'].append(patch_entry)
        
        # 写回manifest
        manifest_json = json.dumps(manifest, indent=2)
        
        cmd_write = [
            'ssh',
            '-i', ssh_config['key_path'],
            '-o', 'StrictHostKeyChecking=no',
            f"{ssh_config['user']}@{ssh_config['host']}",
            f"echo '{manifest_json}' > {manifest_path}"
        ]
        
        result = subprocess.run(cmd_write, capture_output=True, text=True, shell=True)
        
        return result.returncode == 0
        
    except Exception as e:
        raise Exception(f"更新manifest失败: {e}")
