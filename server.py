#!/usr/bin/env python3
import json
import shlex
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pymysql

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "conninfo.json"
DICT_PATH = ROOT / "wowitemmaker-data-dicts.json"
DEFAULT_CONFIG = {
    "mode": "remote",
    "ssh": {
        "host": "43.248.129.172",
        "user": "root",
        "keyPath": "/Users/mac/Desktop/cd.pem",
        "password": ""
    },
    "db": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "wowitem",
        "password": "GknNJLRtcE6RzigVJFF8",
        "database": "acore_world_test",
        "dbstruct": "3.3.5(TC2)"
    },
    "saveConfig": True,
    "savePassword": True
}

FIELDS = [
    "entry","name","displayid","Quality","class","subclass","InventoryType","Material",
    "bonding","AllowableClass","AllowableRace","Flags","RequiredLevel","stackable",
    "spellid_1","spelltrigger_1","spellcharges_1","spellid_2","spelltrigger_2","spellcharges_2","spellid_3","spelltrigger_3","spellcharges_3","spellid_4","spelltrigger_4","spellcharges_4",
    "stat_type1","stat_value1","stat_type2","stat_value2","stat_type3","stat_value3","stat_type4","stat_value4","stat_type5","stat_value5","socketColor_1","socketColor_2","socketColor_3","socketBonus",
    "RandomProperty","RandomSuffix","sheath","ammo_type","dmg_type1","area","Map",
    "RequiredSkill","RequiredSkillRank","requiredspell","requiredhonorrank","RequiredCityRank","RequiredReputationFaction","RequiredReputationRank",
    "PageText","LanguageID","PageMaterial","lockid","itemset","MaxDurability","BagFamily","armor",
    "duration","FlagsExtra","BuyCount","BuyPrice","SellPrice","maxcount","ContainerSlots",
    "delay","RangedModRange","block","holy_res","fire_res","nature_res","frost_res","shadow_res","arcane_res","description",
    "locale_name","locale_description"
]

FLAT_MAP = {
    "mode": (None, "mode"),
    "saveConfig": (None, "saveConfig"),
    "savePassword": (None, "savePassword"),
    "ssh_host": ("ssh", "host"),
    "ssh_user": ("ssh", "user"),
    "ssh_key_path": ("ssh", "keyPath"),
    "ssh_password": ("ssh", "password"),
    "db_host": ("db", "host"),
    "db_port": ("db", "port"),
    "db_user": ("db", "user"),
    "db_password": ("db", "password"),
    "db_name": ("db", "database"),
    "dbstruct": ("db", "dbstruct"),
}


def load_dicts() -> dict:
    if DICT_PATH.exists():
        return json.loads(DICT_PATH.read_text(encoding="utf-8"))
    return {}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg = json.loads(json.dumps(DEFAULT_CONFIG))
            for key in ("mode", "saveConfig", "savePassword"):
                if key in saved:
                    cfg[key] = saved[key]
            for sec in ("ssh", "db"):
                if sec in saved and isinstance(saved[sec], dict):
                    cfg[sec].update(saved[sec])
            return cfg
        except Exception:
            return json.loads(json.dumps(DEFAULT_CONFIG))
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_posted_config(cfg: dict, posted: dict) -> dict:
    for key, value in posted.items():
        if key in FLAT_MAP:
            sec, sub = FLAT_MAP[key]
            if sec is None:
                cfg[sub] = value
            else:
                cfg.setdefault(sec, {})[sub] = value
    for sec in ("ssh", "db"):
        if sec in posted and isinstance(posted[sec], dict):
            cfg[sec].update(posted[sec])
    return cfg


def run_direct_query(sql: str, cfg: dict):
    db = cfg["db"]
    conn = pymysql.connect(
        host=str(db["host"]),
        port=int(db["port"]),
        user=str(db["user"]),
        password=str(db["password"]),
        database=str(db["database"]),
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.Cursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description:
                return cur.fetchall()
            return []
    finally:
        conn.close()


def build_mysql_cmd(sql: str, cfg: dict) -> str:
    db = cfg["db"]
    return (
        "mysql --batch --raw --skip-column-names --protocol=tcp "
        f"-h{shlex.quote(str(db['host']))} -P{int(db['port'])} -u{shlex.quote(str(db['user']))} -p{shlex.quote(str(db['password']))} "
        f"-D{shlex.quote(str(db['database']))} -e {shlex.quote(sql)}"
    )


def run_remote_query(sql: str, cfg: dict) -> str:
    mysql_cmd = build_mysql_cmd(sql, cfg)
    ssh = cfg["ssh"]
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no"]
    if ssh.get("keyPath"):
        ssh_cmd += ["-i", str(ssh["keyPath"])]
    ssh_cmd += [f"{ssh['user']}@{ssh['host']}", mysql_cmd]
    return subprocess.check_output(ssh_cmd, text=True, stderr=subprocess.DEVNULL).strip()


def run_query(sql: str, cfg: dict):
    if cfg.get("mode") == "direct":
        return run_direct_query(sql, cfg)
    return run_remote_query(sql, cfg)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/config":
            self._json({"ok": True, "config": load_config()})
            return
        if parsed.path == "/api/dicts":
            self._json({"ok": True, "dicts": load_dicts()})
            return
        if parsed.path == "/api/lookup":
            qs = parse_qs(parsed.query)
            kind = (qs.get("kind") or [""])[0].strip()
            q = (qs.get("q") or [""])[0].strip()
            limit = int((qs.get("limit") or ["50"])[0])
            cfg = load_config()
            try:
                if kind == "itemset":
                    sql = f"SELECT id, name_zhCN FROM itemset_dbc WHERE id LIKE '%{q}%' OR name_zhCN LIKE '%{q}%' ORDER BY id LIMIT {limit}"
                elif kind == "lock":
                    sql = f"SELECT ID, Type FROM lock_dbc WHERE ID LIKE '%{q}%' ORDER BY ID LIMIT {limit}"
                elif kind == "pagetext":
                    sql = f"SELECT entry, LEFT(text,80) FROM page_text WHERE entry LIKE '%{q}%' OR text LIKE '%{q}%' ORDER BY entry LIMIT {limit}"
                elif kind == "faction":
                    sql = f"SELECT ID, Name_Lang_zhCN FROM faction_dbc WHERE ID LIKE '%{q}%' OR Name_Lang_zhCN LIKE '%{q}%' ORDER BY ID LIMIT {limit}"
                elif kind == "gemproperties":
                    sql = f"SELECT ID, Enchant_ID FROM gemproperties_dbc WHERE ID LIKE '%{q}%' ORDER BY ID LIMIT {limit}"
                elif kind == "totemcategory":
                    sql = f"SELECT ID, Name_Lang_zhCN FROM totemcategory_dbc WHERE ID LIKE '%{q}%' OR Name_Lang_zhCN LIKE '%{q}%' ORDER BY ID LIMIT {limit}"
                elif kind == "itemlimitcategory":
                    sql = f"SELECT ID, Name_Lang_zhCN FROM itemlimitcategory_dbc WHERE ID LIKE '%{q}%' OR Name_Lang_zhCN LIKE '%{q}%' ORDER BY ID LIMIT {limit}"
                elif kind == "disenchant":
                    sql = f"SELECT entry, item, chanceOrQuestChance FROM disenchant_loot_template WHERE entry LIKE '%{q}%' ORDER BY entry LIMIT {limit}"
                else:
                    self._json({"ok": False, "error": "invalid lookup kind"}, 400)
                    return
                result = run_query(sql, cfg)
                if cfg.get("mode") == "direct":
                    rows = [["" if v is None else str(v) for v in row] for row in result]
                else:
                    rows = [line.split("	") for line in result.splitlines() if line.strip()]
                self._json({"ok": True, "rows": rows})
            except Exception as e:
                self._json({"ok": False, "error": f"lookup failed: {e}"}, 500)
            return
        if parsed.path == "/api/search-item":
            qs = parse_qs(parsed.query)
            q = ((qs.get("q") or [""])[0]).strip().replace("'", "''")
            limit = int((qs.get("limit") or ["50"])[0])
            if not q:
                self._json({"ok": True, "rows": []})
                return
            cfg = load_config()
            try:
                sql = (
                    "SELECT it.entry, it.name, COALESCE(loc.Name,''), it.class, it.subclass "
                    "FROM item_template it LEFT JOIN item_template_locale loc ON loc.ID=it.entry AND loc.locale='zhCN' "
                    f"WHERE CAST(it.entry AS CHAR) = '{q}' OR it.name LIKE '%{q}%' OR COALESCE(loc.Name,'') LIKE '%{q}%' ORDER BY it.entry LIMIT {limit}"
                )
                result = run_query(sql, cfg)
                rows = [["" if v is None else str(v) for v in row] for row in result] if cfg.get("mode") == "direct" else [line.split("	") for line in result.splitlines() if line.strip()]
                self._json({"ok": True, "rows": rows})
            except Exception as e:
                self._json({"ok": False, "error": f"search failed: {e}"}, 500)
            return
        if parsed.path == "/api/item":
            qs = parse_qs(parsed.query)
            entry = (qs.get("entry") or [""])[0].strip()
            if not entry.isdigit():
                self._json({"ok": False, "error": "invalid entry"}, 400)
                return
            try:
                cfg = load_config()
                sql = (
                    "SELECT it.entry,it.name,it.displayid,it.Quality,it.class,it.subclass,it.InventoryType,it.Material,"
                    "it.bonding,it.AllowableClass,it.AllowableRace,it.Flags,it.RequiredLevel,it.stackable,"
                    "it.spellid_1,it.spelltrigger_1,it.spellcharges_1,it.spellid_2,it.spelltrigger_2,it.spellcharges_2,it.spellid_3,it.spelltrigger_3,it.spellcharges_3,it.spellid_4,it.spelltrigger_4,it.spellcharges_4,"
                    "it.stat_type1,it.stat_value1,it.stat_type2,it.stat_value2,it.stat_type3,it.stat_value3,it.stat_type4,it.stat_value4,it.stat_type5,it.stat_value5,it.socketColor_1,it.socketColor_2,it.socketColor_3,it.socketBonus,"
                    "it.RandomProperty,it.RandomSuffix,it.sheath,it.ammo_type,it.dmg_type1,it.area,it.Map,"
                    "it.RequiredSkill,it.RequiredSkillRank,it.requiredspell,it.requiredhonorrank,it.RequiredCityRank,it.RequiredReputationFaction,it.RequiredReputationRank,"
                    "it.PageText,it.LanguageID,it.PageMaterial,it.lockid,it.itemset,it.MaxDurability,it.BagFamily,it.armor,"
                    "it.duration,it.FlagsExtra,it.BuyCount,it.BuyPrice,it.SellPrice,it.maxcount,it.ContainerSlots,it.delay,it.RangedModRange,it.block,it.holy_res,it.fire_res,it.nature_res,it.frost_res,it.shadow_res,it.arcane_res,it.description,"
                    "COALESCE(loc.Name,''),COALESCE(loc.Description,'') "
                    "FROM item_template it "
                    "LEFT JOIN item_template_locale loc ON loc.ID = it.entry AND loc.locale='zhCN' "
                    f"WHERE it.entry={entry}"
                )
                result = run_query(sql, cfg)
                if cfg.get("mode") == "direct":
                    if not result:
                        self._json({"ok": False, "error": "not found"}, 404)
                        return
                    row = dict(zip(FIELDS, ["" if v is None else str(v) for v in result[0]]))
                    self._json({"ok": True, "item": row})
                    return
                out = result
                if not out:
                    self._json({"ok": False, "error": "not found"}, 404)
                    return
                parts = out.split("\t")
                while len(parts) < len(FIELDS):
                    parts.append("")
                row = dict(zip(FIELDS, parts))
                self._json({"ok": True, "item": row})
            except Exception as e:
                self._json({"ok": False, "error": f"query failed: {e}"}, 500)
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/api/config", "/api/test-conn", "/api/save-item", "/api/save-locale", "/api/delete-item", "/api/execute-sql", "/api/make-item-patch", "/api/push-patch", "/api/clone-item"):
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body or "{}")

            if parsed.path == "/api/config":
                cfg = apply_posted_config(load_config(), data if isinstance(data, dict) else {})
                if cfg.get("saveConfig", True):
                    save_config(cfg)
                self._json({"ok": True, "config": cfg})
                return

            if parsed.path == "/api/test-conn":
                cfg = apply_posted_config(load_config(), data if isinstance(data, dict) else {})
                try:
                    if cfg.get("mode") == "direct":
                        rows = run_direct_query("SELECT 1", cfg)
                        self._json({"ok": True, "result": rows[0][0] if rows else 1})
                    else:
                        out = run_remote_query("SELECT 1", cfg)
                        self._json({"ok": True, "result": out or "1"})
                except Exception as e:
                    self._json({"ok": False, "error": f"test conn failed: {e}"}, 500)
                return

            cfg = load_config()
            if parsed.path == "/api/push-patch":
                try:
                    env = str(data.get('env','')).strip()
                    if env not in ('test','prod','release'):
                        self._json({'ok': False, 'error': 'env must be test or prod'}, 400)
                        return
                    mpq_path = ROOT / 'build_patch' / 'patch-zhCN-Z.mpq'
                    mpq_path_root = ROOT / 'build_patch' / 'patch-Z.mpq'
                    if not mpq_path.exists() or not mpq_path_root.exists():
                        self._json({'ok': False, 'error': 'patch mpq not found, please run make-item-patch first'}, 400)
                        return
                    import hashlib, json as _json, time
                    env = 'release' if env == 'prod' else env
                    remote_dir = '/www/wwwroot/wow/patches/test' if env == 'test' else '/www/wwwroot/wow/patches/release'
                    remote_api_dir = '/www/wwwroot/wow/api/patches/test' if env == 'test' else '/www/wwwroot/wow/api/patches/release'
                    remote_root_file = '/www/wwwroot/wow/patches/patch-zhCN-Z.mpq'
                    remote_root_file2 = '/www/wwwroot/wow/patches/patch-Z.mpq'
                    base_url = 'http://43.248.129.172:88'
                    version = time.strftime('%Y.%m.%d.%H%M%S', time.localtime())
                    version_token = str(int(time.time()))
                    remote_file_root = f"{remote_dir}/patch-Z.mpq"
                    remote_file = f"{remote_dir}/patch-zhCN-Z.mpq"
                    data = mpq_path.read_bytes()
                    sha256 = hashlib.sha256(data).hexdigest()
                    size = len(data)
                    data_root = mpq_path_root.read_bytes()
                    sha256_root = hashlib.sha256(data_root).hexdigest()
                    size_root = len(data_root)
                    manifest = {
                        'version': version,
                        'files': [
                            {
                                'name': 'patch-Z.mpq',
                                'url': f"{base_url}/patches/{'test' if env=='test' else 'release'}/patch-Z.mpq?v={version_token}",
                                'sha256': sha256_root,
                                'size': size_root
                            },
                            {
                                'name': 'patch-zhCN-Z.mpq',
                                'url': f"{base_url}/patches/{'test' if env=='test' else 'release'}/patch-zhCN-Z.mpq?v={version_token}",
                                'sha256': sha256,
                                'size': size
                            }
                        ]
                    }
                    version_json = {'version': version}
                    tmp_manifest = ROOT / 'build_patch' / f'manifest_{env}.json'
                    tmp_version = ROOT / 'build_patch' / f'version_{env}.json'
                    tmp_manifest.write_text(_json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
                    tmp_version.write_text(_json.dumps(version_json, ensure_ascii=False, indent=2), encoding='utf-8')
                    uploads = [
                        (str(mpq_path_root), remote_file_root),
                        (str(mpq_path_root), remote_root_file2),
                        (str(mpq_path), remote_file),
                        (str(mpq_path), remote_root_file),
                        (str(tmp_manifest), f"{remote_api_dir}/manifest.json"),
                        (str(tmp_version), f"{remote_api_dir}/version.json"),
                    ]
                    if env == 'release':
                        pass
                    upload_logs = []
                    ok = True
                    for local_path, remote_path in uploads:
                        ssh_cmd = ['scp', '-i', '/Users/mac/Desktop/cd.pem', '-o', 'StrictHostKeyChecking=no', local_path, f"root@43.248.129.172:{remote_path}"]
                        result = subprocess.run(ssh_cmd, capture_output=True, text=True)
                        upload_logs.append({'local': local_path, 'remote': remote_path, 'code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
                        if result.returncode != 0:
                            ok = False
                    root_manifest = ROOT / 'build_patch' / f'root_manifest_{env}.json'
                    root_version = ROOT / 'build_patch' / f'root_version_{env}.json'
                    root_manifest.write_text(_json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
                    root_version.write_text(_json.dumps(version_json, ensure_ascii=False, indent=2), encoding='utf-8')
                    for local_path, remote_path in [(str(root_manifest), '/www/wwwroot/wow/api/patches/manifest.json'), (str(root_version), '/www/wwwroot/wow/api/patches/version.json')]:
                        result = subprocess.run(['scp','-i','/Users/mac/Desktop/cd.pem','-o','StrictHostKeyChecking=no',local_path,f"root@43.248.129.172:{remote_path}"], capture_output=True, text=True)
                        upload_logs.append({'local': local_path, 'remote': remote_path, 'code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
                        if result.returncode != 0:
                            ok = False

                    # channel manifests/version for launcher actual chain
                    patch_entry_root = {
                        'Name': 'patch-Z',
                        'Version': version,
                        'Size': size_root,
                        'Sha256': sha256_root,
                        'DownloadUrl': f"{base_url}/patches/{'test' if env=='test' else 'release'}/patch-Z.mpq?v={version_token}",
                        'LocalRelativePath': 'Data/patch-Z.mpq',
                        'Required': True,
                    }
                    patch_entry = {
                        'Name': 'patch-zhCN-Z',
                        'Version': version,
                        'Size': size,
                        'Sha256': sha256,
                        'DownloadUrl': f"{base_url}/patches/{'test' if env=='test' else 'release'}/patch-zhCN-Z.mpq?v={version_token}",
                        'LocalRelativePath': 'Data/zhCN/patch-zhCN-Z.mpq',
                        'Required': True,
                    }
                    channel_manifest = [patch_entry_root, patch_entry]
                    channel_version = {
                        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                        'patchCount': 1,
                        'channel': env,
                    }
                    shared_manifest_path = '/www/wwwroot/wow/patches-channels/shared/manifest.json'
                    shared_version_path = '/www/wwwroot/wow/patches-channels/shared/version.json'
                    ssh_cat = ['ssh','-i','/Users/mac/Desktop/cd.pem','-o','StrictHostKeyChecking=no','root@43.248.129.172']
                    shared_manifest_raw = subprocess.run(ssh_cat + [f"cat {shared_manifest_path}"], capture_output=True, text=True)
                    shared_version_raw = subprocess.run(ssh_cat + [f"cat {shared_version_path}"], capture_output=True, text=True)
                    shared_manifest = []
                    shared_version = {}
                    try:
                        if shared_manifest_raw.returncode == 0 and shared_manifest_raw.stdout.strip():
                            shared_manifest = _json.loads(shared_manifest_raw.stdout)
                    except Exception:
                        shared_manifest = []
                    try:
                        if shared_version_raw.returncode == 0 and shared_version_raw.stdout.strip():
                            shared_version = _json.loads(shared_version_raw.stdout)
                    except Exception:
                        shared_version = {}
                    merged = {}
                    for item in list(shared_manifest) + channel_manifest:
                        name = str(item.get('Name', '')).strip()
                        if not name:
                            continue
                        merged[name] = item
                    combined_manifest = list(merged.values())
                    combined_version = {
                        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                        'patchCount': len(combined_manifest),
                        'channel': env,
                        'layers': ['shared', env],
                    }
                    cm = ROOT / 'build_patch' / f'channel_manifest_{env}.json'
                    cv = ROOT / 'build_patch' / f'channel_version_{env}.json'
                    cmm = ROOT / 'build_patch' / f'combined_manifest_{env}.json'
                    cmv = ROOT / 'build_patch' / f'combined_version_{env}.json'
                    cm.write_text(_json.dumps(channel_manifest, ensure_ascii=False, indent=2), encoding='utf-8')
                    cv.write_text(_json.dumps(channel_version, ensure_ascii=False, indent=2), encoding='utf-8')
                    cmm.write_text(_json.dumps(combined_manifest, ensure_ascii=False, indent=2), encoding='utf-8')
                    cmv.write_text(_json.dumps(combined_version, ensure_ascii=False, indent=2), encoding='utf-8')
                    extra_uploads = [
                        (str(cm), f"/www/wwwroot/wow/patches-channels/{env}/manifest.json"),
                        (str(cv), f"/www/wwwroot/wow/patches-channels/{env}/version.json"),
                        (str(cmm), f"/www/wwwroot/wow/patches-channels/combined-{env}-manifest.json"),
                        (str(cmv), f"/www/wwwroot/wow/patches-channels/combined-{env}-version.json"),
                    ]
                    for local_path, remote_path in extra_uploads:
                        result = subprocess.run(['scp','-i','/Users/mac/Desktop/cd.pem','-o','StrictHostKeyChecking=no',local_path,f"root@43.248.129.172:{remote_path}"], capture_output=True, text=True)
                        upload_logs.append({'local': local_path, 'remote': remote_path, 'code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
                        if result.returncode != 0:
                            ok = False
                    self._json({'ok': ok, 'env': env, 'remoteFile': remote_file, 'version': version, 'sha256': sha256, 'size': size, 'manifestUrl': f"{base_url}/api/patches/{'test' if env=='test' else 'release'}/manifest.json", 'versionUrl': f"{base_url}/api/patches/{'test' if env=='test' else 'release'}/version.json", 'combinedManifestUrl': f"{base_url}/patches-channels/combined-{env}-manifest.json", 'combinedVersionUrl': f"{base_url}/patches-channels/combined-{env}-version.json", 'uploads': upload_logs}, 200 if ok else 500)
                except Exception as e:
                    self._json({'ok': False, 'error': f'push patch failed: {e}'}, 500)
                return
            if parsed.path == "/api/clone-item":
                try:
                    src_entry = str(data.get('srcEntry','')).strip()
                    dst_entry = str(data.get('dstEntry','')).strip()
                    new_name_en = str(data.get('newNameEn','')).strip()
                    new_name_zh = str(data.get('newNameZh','')).strip()
                    if not src_entry.isdigit() or not dst_entry.isdigit():
                        self._json({'ok': False, 'error': 'srcEntry/dstEntry invalid'}, 400)
                        return
                    cfg = load_config()
                    if cfg.get('mode') != 'direct':
                        self._json({'ok': False, 'error': 'clone-item 暂仅支持 direct 模式'}, 400)
                        return
                    conn = pymysql.connect(host=cfg['db']['host'], port=int(cfg['db']['port']), user=cfg['db']['user'], password=cfg['db']['password'], database=cfg['db']['database'], charset='utf8mb4', autocommit=True)
                    zh_name = ''
                    zh_desc = ''
                    try:
                        with conn.cursor() as cur:
                            cur.execute(f"SHOW COLUMNS FROM item_template")
                            cols = [r[0] for r in cur.fetchall()]
                            cur.execute(f"SELECT * FROM item_template WHERE entry={int(src_entry)}")
                            row = cur.fetchone()
                            if not row:
                                raise Exception('source item not found')
                            data_map = dict(zip(cols, row))
                            data_map['entry'] = int(dst_entry)
                            if new_name_en:
                                data_map['name'] = new_name_en
                            col_names = ','.join(f'`{c}`' for c in cols)
                            placeholders = ','.join(['%s']*len(cols))
                            values = [data_map[c] for c in cols]
                            cur.execute(f"REPLACE INTO item_template ({col_names}) VALUES ({placeholders})", values)
                            cur.execute(f"SELECT Name, Description FROM item_template_locale WHERE ID={int(src_entry)} AND locale='zhCN'")
                            loc = cur.fetchone()
                            if loc:
                                zh_name = loc[0] or ''
                                zh_desc = loc[1] or ''
                            if new_name_zh:
                                zh_name = new_name_zh
                            if zh_name or zh_desc:
                                cur.execute("REPLACE INTO item_template_locale (ID, locale, Name, Description) VALUES (%s,'zhCN',%s,%s)", (int(dst_entry), zh_name, zh_desc))
                    finally:
                        conn.close()
                    self._json({'ok': True, 'srcEntry': src_entry, 'dstEntry': dst_entry, 'newNameEn': new_name_en, 'newNameZh': new_name_zh, 'localeName': zh_name, 'localeDescription': zh_desc})
                except Exception as e:
                    self._json({'ok': False, 'error': f'clone item failed: {e}'}, 500)
                return
            if parsed.path == "/api/make-item-patch":
                try:
                    cfg = load_config()
                    tc2 = str(cfg.get('db',{}).get('dbstruct','')).strip() == '3.3.5(TC2)'
                    base_item = Path('/Users/mac/wow-server/pb-core/env/dist/bin/dbc/Item.dbc')
                    out_dir = ROOT / 'build_patch'
                    out_dir.mkdir(parents=True, exist_ok=True)
                    csv_path = out_dir / 'item_template_export.csv'
                    out_item = out_dir / 'Item.dbc'
                    script = ROOT / 'itemdbc_mpq_builder.py'
                    cmd = [
                        'python3', str(script),
                        '--base-item-dbc', str(base_item),
                        '--export-csv', str(csv_path),
                        '--db-host', str(cfg['db']['host']),
                        '--db-port', str(cfg['db']['port']),
                        '--db-name', str(cfg['db']['database']),
                        '--db-user', str(cfg['db']['user']),
                        '--db-password', str(cfg['db']['password']),
                        '--out-item-dbc', str(out_item),
                    ]
                    if tc2:
                        cmd.append('--tc2')
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
                    mpqcli = Path('/Users/mac/Desktop/诺兰补丁/tools/mpqcli/build/bin/mpqcli')
                    mpq_ready = False
                    mpq_reason = ''
                    mpq_path = out_dir / 'patch-zhCN-Z.mpq'
                    mpq_path_root = out_dir / 'patch-Z.mpq'
                    mpq_stdout = ''
                    mpq_stderr = ''
                    if result.returncode == 0:
                        if mpqcli.exists():
                            mpq_dir = out_dir / 'mpq_root'
                            target_dir = mpq_dir / 'DBFilesClient'
                            target_dir.mkdir(parents=True, exist_ok=True)
                            (target_dir / 'Item.dbc').write_bytes(out_item.read_bytes())
                            for target_mpq in (mpq_path, mpq_path_root):
                                if target_mpq.exists():
                                    target_mpq.unlink()
                                mpq_run = subprocess.run([
                                    str(mpqcli), 'create', str(mpq_dir), '-o', str(target_mpq), '-g', 'wow-wotlk'
                                ], capture_output=True, text=True, cwd=str(ROOT))
                                mpq_stdout += f"\n## {target_mpq.name}\n" + (mpq_run.stdout or '')
                                mpq_stderr += f"\n## {target_mpq.name}\n" + (mpq_run.stderr or '')
                            mpq_ready = mpq_path.exists() and mpq_path_root.exists()
                            mpq_reason = '' if mpq_ready else 'mpqcli 执行失败'
                        else:
                            mpq_reason = '本机未找到 mpqcli，已先完成旧逻辑前半段：导库 -> 重建 Item.dbc'
                    self._json({
                        'ok': result.returncode == 0,
                        'returncode': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'itemDbc': str(out_item),
                        'csv': str(csv_path),
                        'mpqReady': mpq_ready,
                        'mpqReason': mpq_reason,
                        'mpqPath': str(mpq_path),
                        'mpqPathRoot': str(mpq_path_root),
                        'mpqStdout': mpq_stdout,
                        'mpqStderr': mpq_stderr
                    }, 200 if result.returncode == 0 else 500)
                except Exception as e:
                    self._json({'ok': False, 'error': f'make item patch failed: {e}'}, 500)
                return
            if parsed.path == "/api/execute-sql":
                sql_text = str(data.get("sql", "")).strip()
                parts = [x.strip() for x in sql_text.split(";") if x.strip()]
                try:
                    out_rows = []
                    for sql in parts:
                        result = run_query(sql, cfg)
                        if cfg.get("mode") == "direct":
                            out_rows.append([["" if v is None else str(v) for v in row] for row in result])
                        else:
                            out_rows.append([line.split("	") for line in result.splitlines() if line.strip()])
                    self._json({"ok": True, "results": out_rows})
                except Exception as e:
                    self._json({"ok": False, "error": f"execute sql failed: {e}"}, 500)
                return
            entry = str(data.get("entry", "")).strip()
            if not entry.isdigit():
                self._json({"ok": False, "error": "invalid entry"}, 400)
                return
            if parsed.path == "/api/delete-item":
                try:
                    sql = f"DELETE FROM item_template WHERE entry = {int(entry)}"
                    if cfg.get("mode") != "direct":
                        raise Exception("delete-item 暂仅支持 direct 模式")
                    run_direct_query(sql, cfg)
                    self._json({"ok": True})
                except Exception as e:
                    self._json({"ok": False, "error": f"delete item failed: {e}"}, 500)
                return
            name_en = str(data.get("name_en", ""))
            desc_en = str(data.get("desc_en", ""))
            name_zh = str(data.get("name_zh", ""))
            desc_zh = str(data.get("desc_zh", ""))

            if parsed.path == "/api/save-item":
                sql = (
                    "REPLACE INTO item_template (entry, name, displayid, Quality, class, subclass, InventoryType, Material, bonding, AllowableClass, AllowableRace, Flags, RequiredLevel, stackable, spellid_1, spelltrigger_1, spellcharges_1, spellid_2, spelltrigger_2, spellcharges_2, spellid_3, spelltrigger_3, spellcharges_3, spellid_4, spelltrigger_4, spellcharges_4, stat_type1, stat_value1, stat_type2, stat_value2, stat_type3, stat_value3, stat_type4, stat_value4, stat_type5, stat_value5, socketColor_1, socketColor_2, socketColor_3, socketBonus, RandomProperty, RandomSuffix, RequiredSkill, RequiredSkillRank, requiredspell, requiredhonorrank, RequiredCityRank, RequiredReputationFaction, RequiredReputationRank, PageText, LanguageID, PageMaterial, lockid, itemset, MaxDurability, BagFamily, armor, duration, FlagsExtra, BuyCount, BuyPrice, SellPrice, maxcount, ContainerSlots, delay, RangedModRange, block, holy_res, fire_res, nature_res, frost_res, shadow_res, arcane_res, description) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                )
                vals = (
                    int(entry), name_en, int(data.get("displayid") or 0), int(data.get("quality") or 0), int(data.get("class_id") or 0), int(data.get("subclass") or 0),
                    int(data.get("inventorytype") or 0), int(data.get("material") or 0), int(data.get("bonding") or 0), int(data.get("allowableclass") or -1), int(data.get("allowablerace") or -1),
                    int(data.get("flags") or 0), int(data.get("requiredlevel") or 0), int(data.get("stackable") or 1),
                    int(data.get("spellid_1") or 0), int(data.get("spelltrigger_1") or 0), int(data.get("spellcharges_1") or 0),
                    int(data.get("spellid_2") or 0), int(data.get("spelltrigger_2") or 0), int(data.get("spellcharges_2") or 0),
                    int(data.get("spellid_3") or 0), int(data.get("spelltrigger_3") or 0), int(data.get("spellcharges_3") or 0),
                    int(data.get("spellid_4") or 0), int(data.get("spelltrigger_4") or 0), int(data.get("spellcharges_4") or 0),
                    int(data.get("stat_type_1") or 0), int(data.get("stat_value_1") or 0), int(data.get("stat_type_2") or 0), int(data.get("stat_value_2") or 0),
                    int(data.get("stat_type_3") or 0), int(data.get("stat_value_3") or 0), int(data.get("stat_type_4") or 0), int(data.get("stat_value_4") or 0),
                    int(data.get("stat_type_5") or 0), int(data.get("stat_value_5") or 0),
                    int(data.get("socket_color_1") or 0), int(data.get("socket_color_2") or 0), int(data.get("socket_color_3") or 0), int(data.get("socket_bonus") or 0),
                    int(data.get("random_property") or 0), int(data.get("random_suffix") or 0),
                    int(data.get("required_skill") or 0), int(data.get("required_skill_rank") or 0), int(data.get("requiredspell") or 0), int(data.get("requiredhonorrank") or 0),
                    int(data.get("required_city_rank") or 0), int(data.get("required_reputation_faction") or 0), int(data.get("required_reputation_rank") or 0),
                    int(data.get("page_text") or 0), int(data.get("language_id") or 0), int(data.get("page_material") or 0), int(data.get("lock_id") or 0), int(data.get("itemset") or 0),
                    int(data.get("maxdurability") or 0), int(data.get("bag_family") or 0), int(data.get("armor") or 0), int(data.get("duration") or 0), int(data.get("flags_extra") or 0),
                    int(data.get("buycount") or 1), int(data.get("buyprice") or 0), int(data.get("sellprice") or 0), int(data.get("maxcount") or 0), int(data.get("container_slots") or 0),
                    int(data.get("delay") or 0), float(data.get("ranged_mod_range") or 0), int(data.get("block") or 0), int(data.get("holy_res") or 0), int(data.get("fire_res") or 0), int(data.get("nature_res") or 0), int(data.get("frost_res") or 0), int(data.get("shadow_res") or 0), int(data.get("arcane_res") or 0), desc_en,
                )
                try:
                    if cfg.get("mode") != "direct":
                        raise Exception("save-item 暂仅支持 direct 模式")
                    conn = pymysql.connect(host=cfg['db']['host'], port=int(cfg['db']['port']), user=cfg['db']['user'], password=cfg['db']['password'], database=cfg['db']['database'], charset='utf8mb4', autocommit=True)
                    try:
                        with conn.cursor() as cur:
                            cur.execute(sql, vals)
                    finally:
                        conn.close()
                    self._json({"ok": True})
                except Exception as e:
                    self._json({"ok": False, "error": f"save item failed: {e}"}, 500)
                return

            if parsed.path == "/api/save-locale":
                sql = "REPLACE INTO item_template_locale (ID, locale, Name, Description) VALUES (%s,'zhCN',%s,%s)"
                try:
                    if cfg.get("mode") != "direct":
                        raise Exception("save-locale 暂仅支持 direct 模式")
                    conn = pymysql.connect(host=cfg['db']['host'], port=int(cfg['db']['port']), user=cfg['db']['user'], password=cfg['db']['password'], database=cfg['db']['database'], charset='utf8mb4', autocommit=True)
                    try:
                        with conn.cursor() as cur:
                            cur.execute(sql, (int(entry), name_zh, desc_zh))
                    finally:
                        conn.close()
                    self._json({"ok": True})
                except Exception as e:
                    self._json({"ok": False, "error": f"save locale failed: {e}"}, 500)
                return
        self.send_error(404)

    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_server():
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()

if __name__ == "__main__":
    run_server()
