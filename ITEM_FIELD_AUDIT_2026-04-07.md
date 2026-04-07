# 物品信息字段审计（基于 item_template 表详解 + 旧 WOWItemMaker 逆向）

日期：2026-04-07

## 目标
用于当前 web 原型继续补齐“物品信息”内容：
1. 哪些字段应该存在
2. 哪些字段适合做下拉
3. 下拉应提供哪些内容
4. 当前已做 / 遗漏项

## 依据
### 1. CHM 资料
- `/Users/mac/Downloads/魔兽DBC和数据库-潇湘雨妃-整合修复版.CHM`
- 解包目录：`/tmp/wow_chm_extract/`
- 重点文件：`/tmp/wow_chm_extract/数据库表中文详解/item_template 表详解.txt`

### 2. 旧 WOWItemMaker 词典资源
- `/Users/mac/Downloads/WOWItemMaker1.73/WOWItemMaker/Data/`

### 3. 已逆向确认的旧 WOWItemMaker 页签/字段
- `memory/wowitemmaker-reverse-engineering-2026-04-06.md`

---

## 一、适合做下拉的字段（应优先补）

### A. 基础页
- `Class` → 下拉
  - 来源：`Data/class.txt`
- `SubClass` → 下拉（随 Class 联动）
  - 来源：`Data/subclass<id>.txt`
- `DisplayID` → 下拉 / 搜索型下拉
  - 来源：`Data/displayid.txt`
- `Quality` → 下拉
  - 来源：`Data/Quality.txt`
- `Bonding` → 下拉
  - 来源：`Data/bonding.txt`

### B. 描述 / 通用属性页
- `Flags` → 下拉（多值组合提示）
  - 来源：`Data/Flags.txt`
- `Ammo_Type` → 下拉
  - 来源：`Data/ammo_type.txt`
- `StatsCount` → 下拉
  - 值：0~10
- `InventoryType` → 下拉
  - 来源：`Data/InventoryType.txt`
- `Sheath` → 下拉
  - 来源：`Data/sheath.txt`
- `Material` → 下拉
  - 来源：`Data/Material.txt`

### C. 限制页
- `AllowableClass` → 下拉/位掩码帮助器
  - CHM：1战士 2圣骑士 4猎人 8盗贼 16牧师 32死骑 64萨满 128法师 256术士 1024德鲁伊
  - 旧工具资源：`Data/AllowableClass.txt`
- `AllowableRace` → 下拉/位掩码帮助器
  - CHM：1人类 2兽人 4矮人 8暗夜精灵 16亡灵 32牛头人 64侏儒 128巨魔 512血精灵 1024德莱尼
  - 旧工具资源：`Data/AllowableRace.txt`
- `Area` → 下拉
  - 来源：`Data/area.txt`
- `Map` → 下拉
  - 来源：`Data/map.txt`
- `RequiredReputationRank` → 下拉
  - CHM：0仇恨 1敌对 2冷漠 3中立 4友善 5尊敬 6崇敬 7崇拜

### D. 属性页
- `Stat_Type1..10` → 下拉
  - 来源：`Data/stat_type.txt`
- `Stat_Value1..10` → 文本框

### E. 战斗页
- `Dmg_Type1..5` → 下拉
  - 来源：`Data/dmg_type.txt`
  - CHM：0普通 1神圣 2火焰 3自然 4冰霜 5阴影 6奥术

### F. 法术页
- `SpellID_1..5` → 下拉（宽下拉）
  - 来源：`Data/spellid.txt`
- `SpellTrigger_1..5` → 下拉
  - 来源：`Data/spelltrigger.txt`
  - CHM：0使用 1装备生效 2击中时可能 4灵魂石 5马上使用 6学习法术

### G. Socket / 高级页
- `SocketColor_1..3` → 下拉
  - 来源：`Data/socketColor.txt`
  - CHM：1多彩 2红 4黄 8蓝 10紫 12绿 14棱彩
- `SocketBonus` → 下拉
  - 来源：`Data/socketBonus.txt`
- `RandomProperty` → 下拉
  - 来源：`Data/RandomProperty.txt`
- `RandomSuffix` → 下拉
  - 来源：`Data/RandomSuffix.txt`

### H. 后续应补充词典型下拉/辅助选择器
这些不一定要纯下拉，但应该有选择器：
- `RequiredSkill`
- `RequiredSpell`
- `RequiredReputationFaction`
- `LockID`
- `PageText`
- `ItemSet`
- `GemProperties`
- `TotemCategory`
- `ItemLimitCategory`
- `HolidayId`
- `DisenchantID`
- `RequiredDisenchantSkill`

---

## 二、当前原型已覆盖但还不完整的部分

### 已有但需要改成真实词典/联动
- `Class`
- `SubClass`
- `Quality`
- `DisplayID`
- `Bonding`
- `Flags`
- `Ammo_Type`
- `InventoryType`
- `Sheath`
- `Material`
- `Area`
- `Map`
- `SpellID_1..5`
- `SpellTrigger_1..5`
- `SocketColor_1..3`
- `SocketBonus`
- `RandomProperty`
- `RandomSuffix`

### 当前明显缺失的“应该做下拉/选择器”的项
- `AllowableClass`
- `AllowableRace`
- `RequiredReputationRank`
- `Stat_Type1..10`
- `Dmg_Type1..5`
- `RequiredSkill`
- `RequiredSpell`
- `RequiredReputationFaction`
- `LockID`
- `PageText`
- `ItemSet`
- `GemProperties`
- `TotemCategory`
- `ItemLimitCategory`
- `HolidayId`
- `DisenchantID`

---

## 三、物品信息当前仍遗漏/需要确认补入的项

### 旧工具已确认、但当前 web 原型未完整覆盖或未做好联动
- `SoundOverrideSubclass`
- `RequiredHonnorRank`
- `RequiredCityRank`
- `Dmg_Min3..5 / Dmg_Max3..5 / Dmg_Type3..5`（UI是否条件展示）
- `Block`
- `RangedModRange`
- `SocketContent_1..3`
- `HolidayId`
- `ScriptName`
- `Duration`
- `ArmorDamageModifier`
- `MinMoneyLoot`
- `MaxMoneyLoot`
- `FoodType`
- `DisenchantID`
- `ScalingStatDistribution`
- `ScalingStatValue`
- `RequiredDisenchantSkill`
- `GemProperties`
- `TotemCategory`
- `ItemLimitCategory`

### CHM 里还有但旧工具/UI里未必全部暴露，需要后续比对决定
- `flagsCustom`
- `VerifiedBuild`
- 某些更尾部 / 内部维护字段

原则：
- 先以旧 WOWItemMaker 已暴露内容为主
- 再决定是否把 CHM 里额外字段加入“高级字段”页

---

## 四、建议直接执行顺序
1. 用旧工具 `Data/*.txt` 替换当前手写假词典
2. 先补“应该下拉但目前还是文本框”的字段：
   - `AllowableClass`
   - `AllowableRace`
   - `Stat_Type1..10`
   - `Dmg_Type1..5`
   - `RequiredReputationRank`
3. 再补“应有选择器”的外键/引用字段：
   - `RequiredSkill`
   - `RequiredSpell`
   - `RequiredReputationFaction`
   - `LockID`
   - `PageText`
   - `ItemSet`
   - `GemProperties`
   - `TotemCategory`
   - `ItemLimitCategory`
   - `HolidayId`
   - `DisenchantID`
4. 最后审一遍当前页面是否仍漏旧工具字段

---

## 五、结论
可以明确：
- 当前“物品信息”还没补齐
- 还有一批字段适合下拉/选择器但未实现
- CHM + 旧 WOWItemMaker Data 目录已经足够作为这轮补齐依据
