#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import shlex
import struct
import subprocess
from pathlib import Path

HEADER_STRUCT = struct.Struct('<4s4I')


def _read_c_string(blob: bytes, offset: int) -> str:
    if offset <= 0 or offset >= len(blob):
        return ''
    end = blob.find(b'\\x00'.decode('unicode_escape').encode('latin1'), offset)
    if end < 0:
        end = len(blob)
    return blob[offset:end].decode('utf-8', errors='ignore')


def read_dbc_table(path: Path):
    data = path.read_bytes()
    magic, record_count, field_count, record_size, string_size = HEADER_STRUCT.unpack_from(data, 0)
    if magic != b'WDBC':
        raise ValueError(f'{path} 不是 WDBC 文件')
    start = HEADER_STRUCT.size
    records_end = start + record_count * record_size
    string_block = data[records_end:records_end + string_size]
    rows = []
    for i in range(record_count):
        off = start + i * record_size
        row = list(struct.unpack_from(f'<{field_count}I', data, off))
        rows.append(row)
    return field_count, record_size, rows, string_block


def detect_text_columns(rows: list[list[int]], string_block: bytes) -> list[bool]:
    if not rows:
        return []
    field_count = len(rows[0])
    flags = [False] * field_count
    for c in range(field_count):
        for row in rows:
            v = int(row[c])
            if v == 0:
                continue
            if 0 < v < len(string_block):
                s = _read_c_string(string_block, v)
                if s:
                    flags[c] = True
                    break
    return flags


def materialize_rows(rows: list[list[int]], text_cols: list[bool], string_block: bytes):
    out = []
    for row in rows:
        vals = []
        for i, v in enumerate(row):
            if i < len(text_cols) and text_cols[i]:
                vals.append(_read_c_string(string_block, int(v)))
            else:
                vals.append(str(int(v)))
        out.append(vals)
    return out


def save_dbc_table(path: Path, rows: list[list[str]], field_count: int, text_cols: list[bool]):
    zero_byte = b'\\x00'.decode('unicode_escape').encode('latin1')
    string_bytes = bytearray(zero_byte)
    prepared: list[list[int]] = []
    for row in rows:
        out = []
        for i, cell in enumerate(row):
            if i < len(text_cols) and text_cols[i]:
                text = '' if cell is None else str(cell)
                if text == '':
                    out.append(0)
                else:
                    off = len(string_bytes)
                    string_bytes.extend(text.encode('utf-8'))
                    string_bytes.extend(zero_byte)
                    out.append(off)
            else:
                s = '0' if cell is None or str(cell).strip() == '' else str(cell).strip()
                out.append(int(s))
        prepared.append(out)
    with path.open('wb') as f:
        f.write(HEADER_STRUCT.pack(b'WDBC', len(prepared), field_count, field_count * 4, len(string_bytes)))
        for row in prepared:
            f.write(struct.pack(f'<{field_count}I', *[(x + (1<<32)) & 0xffffffff if int(x) < 0 else int(x) for x in row]))
        f.write(string_bytes)


def read_db_rows(csv_path: Path):
    with csv_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        return header, [row for row in reader if row]


def merge_rows(base_rows: list[list[str]], db_rows: list[list[str]]) -> list[list[str]]:
    db_map = {int(r[0]): r for r in db_rows}
    merged = [r for r in base_rows if int(r[0]) not in db_map]
    merged.extend(db_rows)
    merged.sort(key=lambda r: int(r[0]))
    return merged


def export_db_csv(out_csv: Path, *, db_host: str, db_port: int, db_name: str, db_user: str, db_password: str, tc2: bool):
    col4 = 'SoundOverrideSubclass'
    sql = f"SELECT entry,class,subclass,{col4},material,displayid,InventoryType,sheath FROM item_template ORDER BY entry ASC"
    mysql_cmd = f"mysql --batch --raw --skip-column-names --protocol=tcp -h{shlex.quote(db_host)} -P{int(db_port)} -u{shlex.quote(db_user)} -p{shlex.quote(db_password)} {shlex.quote(db_name)} -e {shlex.quote(sql)}"
    result = subprocess.run(mysql_cmd, check=True, shell=True, capture_output=True, text=True)
    rows = [line.split('	')[:8] for line in result.stdout.splitlines() if line.strip()]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['entry','class','subclass',col4,'material','displayid','InventoryType','sheath'])
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description='按旧 WOWItemMaker 逻辑重建 Item.dbc 并打包 MPQ')
    ap.add_argument('--base-item-dbc', required=True, type=Path)
    ap.add_argument('--db-csv', type=Path)
    ap.add_argument('--export-csv', type=Path)
    ap.add_argument('--db-host', default='127.0.0.1')
    ap.add_argument('--db-port', default=3306, type=int)
    ap.add_argument('--db-name')
    ap.add_argument('--db-user')
    ap.add_argument('--db-password')
    ap.add_argument('--tc2', action='store_true')
    ap.add_argument('--out-item-dbc', required=True, type=Path)
    args = ap.parse_args()
    csv_path = args.db_csv
    if args.export_csv:
        export_db_csv(args.export_csv, db_host=args.db_host, db_port=args.db_port, db_name=args.db_name, db_user=args.db_user, db_password=args.db_password, tc2=args.tc2)
        csv_path = args.export_csv
    if not csv_path:
        raise SystemExit('必须提供 --db-csv 或 --export-csv')
    field_count, record_size, base_rows_raw, string_block = read_dbc_table(args.base_item_dbc)
    text_cols = detect_text_columns(base_rows_raw, string_block)
    base_rows = materialize_rows(base_rows_raw, text_cols, string_block)
    header, db_rows = read_db_rows(csv_path)
    merged_rows = merge_rows(base_rows, db_rows)
    args.out_item_dbc.parent.mkdir(parents=True, exist_ok=True)
    save_dbc_table(args.out_item_dbc, merged_rows, field_count, text_cols)
    print(f'base_rows={len(base_rows)} db_rows={len(db_rows)} merged_rows={len(merged_rows)} field_count={field_count} record_size={record_size}')
    print(f'written_item_dbc={args.out_item_dbc}')

if __name__ == '__main__':
    main()
