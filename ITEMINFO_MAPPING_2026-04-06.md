# WOWItemMaker 物品信息页精确布局与完整字段映射（2026-04-06）

## 一、真实读取链

旧 WOWItemMaker 的读取流程已确认：

1. `MainForm::GetItemInfo(string Entry)`
2. `StateForm::DBAdapter("select * from item_template where entry='...'" )`
3. `StateForm` 查询成功后 `Invoke(GetItemInfo(DataSet))`
4. `GetItemInfo(DataSet)` 将 `DataSet.Tables[0].Rows[0]` 写入 `ItemInfo`
5. `ShowDialog()` 返回后，若 `ItemInfo.Stat == true`
6. 主窗体把 `ItemInfo` 全量回填到 UI 控件

---

## 二、ItemInfo -> UI 控件完整主映射（已实锤）

### 1. 基础页（身份 / 商业 / 名称）
| ItemInfo 字段 | UI 控件 |
|---|---|
| Entry | `EntryTextBox` |
| Class | `ItemClassList` |
| SubClass | `ItemSubClassList` |
| DisplayID | `DisplayIDList` |
| Quality | `QualityList` |
| BuyCount | `BuyCountTextBox` |
| BuyPrice | `BuyPriceTextBox` |
| SellPrice | `SellPriceTextBox` |
| ItemLevel | `ItemLevelTextBox` |
| MaxCount | `maxcountTextBox` |
| StackAble | `StackAbleTextBox` |
| Bonding | `BondingList` |
| MaxDurability | `MaxDurabilityTextBox` |
| Name | `RTB_ItemName.ColorText` |

### 2. 描述 / 扩展属性页
| ItemInfo 字段 | UI 控件 |
|---|---|
| Description | `RTB_Description.ColorText` |
| Flags | `FlagsList` |
| Ammo_Type | `Ammo_TypeList` |
| StatsCount | `StatsCountList` |
| ContainerSlots | `ContainerSlotsTextBox` |
| InventoryType | `InventoryTypeList` |
| ItemSet | `ItemSetTextBox` |
| Sheath | `SheathList` |
| Material | `MaterialList` |
| LockID | `LockIdTextBox` |
| StartQuest | `StartQuestTextBox` |
| PageMeterial | `PageMeterialTextBox` |
| LanguageID | `LanguageIDTextBox` |
| PageText | `PageTextTextBox` |

### 3. 限制页
| ItemInfo 字段 | UI 控件 |
|---|---|
| AllowableClass | `AllowableClassList` |
| AllowableRace | `AllowableRaceList` |
| RequiredLevel | `RequiredLevelTextBox` |
| RequiredSkill | `RequiredSkillTextBox` |
| RequiredSkillRank | `RequiredSkillRankTextBox` |
| RequiredSpell | `RequiredSpellTextBox` |
| RequiredHonnorRank | `RequiredHonnorRankTextBox` |
| RequiredCityRank | `RequiredCityRankTextBox` |
| RequiredReputationFaction | `RequiredReputationFactionTextBox` |
| RequiredReputationRank | `RequiredReputationRankTextBox` |
| Area | `AreaList` |
| Map | `MapList` |

### 4. 属性页（10 槽）
| ItemInfo 字段 | UI 控件 |
|---|---|
| Stat_Type1..10 | `Stat_Type1List .. Stat_Type10List` |
| Stat_Value1..10 | `Stat_Value1TextBox .. Stat_Value10TextBox` |
| StatsCount | `StatsCountList` |

### 5. 战斗页（伤害 / 抗性 / 基础战斗）
| ItemInfo 字段 | UI 控件 |
|---|---|
| Armor | `armorTextBox` |
| Delay | `delayTextBox` |
| Block | `blockTextBox` |
| Holy_Res | `holy_resTextBox` |
| Fire_Res | `fire_resTextBox` |
| Nature_Res | `nature_resTextBox` |
| Frost_Res | `frost_resTextBox` |
| Shadow_Res | `shadow_resTextBox` |
| Arcane_Res | `arcane_resTextBox` |
| Dmg_Min1 | `dmg_min1TextBox` |
| Dmg_Max1 | `dmg_max1TextBox` |
| Dmg_Type1 | `dmg_type1List` |
| Dmg_Min2 | `dmg_min2TextBox` |
| Dmg_Max2 | `dmg_max2TextBox` |
| Dmg_Type2 | `dmg_type2List` |

#### 老版本额外伤害槽（3.0.0-3.0.9）
| ItemInfo 字段 | UI 控件 |
|---|---|
| Dmg_Min3 | `dmg_min3TextBox` |
| Dmg_Max3 | `dmg_max3TextBox` |
| Dmg_Type3 | `dmg_type3List` |
| Dmg_Min4 | `dmg_min4TextBox` |
| Dmg_Max4 | `dmg_max4TextBox` |
| Dmg_Type4 | `dmg_type4List` |
| Dmg_Min5 | `dmg_min5TextBox` |
| Dmg_Max5 | `dmg_max5TextBox` |
| Dmg_Type5 | `dmg_type5List` |

### 6. 法术页（5 槽基础）
| ItemInfo 字段 | UI 控件 |
|---|---|
| SpellID_1..5 | `spellid_1List .. spellid_5List` |
| SpellTrigger_1..5 | `spelltrigger_1List .. spelltrigger_5List` |
| SpellCooldown_1..5 | `spellcooldown_1TextBox .. spellcooldown_5TextBox` |

### 7. 高级法术参数页（5 槽高级）
| ItemInfo 字段 | UI 控件 |
|---|---|
| SpellCategory_1..5 | `SpellCategory_1TextBox .. SpellCategory_5TextBox` |
| SpellCategoryCooldown_1..5 | `SpellCategoryCooldown_1TextBox .. SpellCategoryCooldown_5TextBox` |
| SpellCharges_1..5 | `SpellCharges_1TextBox .. SpellCharges_5TextBox` |
| SpellppmRate_1..5 | `SpellppmRate_1TextBox .. SpellppmRate_5TextBox` |

### 8. Socket 页 / 高级 socket 字段
| ItemInfo 字段 | UI 控件 |
|---|---|
| SocketColor_1 | `SocketColor_1List` |
| SocketColor_2 | `SocketColor_2List` |
| SocketColor_3 | `SocketColor_3List` |
| SocketBonus | `SocketBonusList` |
| SocketContent_1 | `SocketContent_1TextBox` |
| SocketContent_2 | `SocketContent_2TextBox` |
| SocketContent_3 | `SocketContent_3TextBox` |

### 9. 高级机制 / 杂项页
| ItemInfo 字段 | UI 控件 |
|---|---|
| GemProperties | `GemPropertiesTextBox` |
| BagFamily | `BagFamilyTextBox` |
| RandomProperty | `RandomPropertyList` |
| RandomSuffix | `RandomSuffixList` |
| RangedModRange | `RangedModRangeTextBox` |
| RequiredDisenchantSkill | `RequiredDisenchantSkillTextBox` |
| ScalingStatDistribution | `ScalingStatDistributionTextBox` |
| ScalingStatValue | `ScalingStatValueTextBox` |
| TotemCategory | `TotemCategoryTextBox` |
| Unk0 | `unk0TextBox` |
| FoodType | `FoodTypeTextBox` |
| DisenchantID | `DisenchantIDTextBox` |
| ScriptName | `ScriptNameTextBox` |
| ItemLimitCategory | `ItemLimitCategoryTextBox` |
| Duration | `DurationTextBox` |
| ArmorDamageModifier | `ArmorDamageModifierTextBox` |
| MinMoneyLoot | `MinMoneyLootTextBox` |
| MaxMoneyLoot | `MaxMoneyLootTextBox` |

### 10. 版本切换字段
| Dbstruct | 额外行为 |
|---|---|
| `3.3.X` | `HolidayId -> HolidayIDTextBox`，`label1 = Faction(...)` |
| `3.3.5(TC2)` | `HolidayId -> HolidayIDTextBox`，但 `label1 = FlagsExtra:` |

---

## 三、物品信息页精确布局结构（可直接复刻）

### A. 基础页
- 左上：身份区
  - Entry / Class / SubClass / DisplayID / Quality
- 中段：商业与堆叠区
  - BuyCount / BuyPrice / SellPrice / ItemLevel / MaxCount / StackAble / Bonding / MaxDurability
- 下段：名称富文本区
  - `RTB_ItemName`
  - `Btn_NameColor`

### B. 描述 / 扩展属性页
- 上段：描述富文本区
  - `RTB_Description`
  - `Btn_DcpColor`
- 中段：Flags / Ammo / StatsCount / Container / Inventory
- 下段：Set / Sheath / Material / Lock / Page / Language

### C. 限制页
- 第一段：资格限制
  - AllowableClass / AllowableRace / RequiredLevel / RequiredSkill / RequiredSkillRank / RequiredSpell / RequiredHonnorRank / RequiredCityRank / RequiredReputationFaction / RequiredReputationRank
- 第二段：空间限制
  - Area / Map

### D. 属性页
- 固定 10 行双列矩阵
  - 左列：`Stat_TypeN`
  - 右列：`Stat_ValueN`
- 独立放 `StatsCount`

### E. 战斗页
- `groupBox3`：五段伤害矩阵
  - 每段：Min / Max / Type
- `groupBox4`：六抗矩阵
  - Holy / Fire / Nature / Frost / Shadow / Arcane
- `groupBox5`：基础战斗三件套
  - Armor / Delay / Block

### F. 法术页
- 5 槽基础矩阵
  - SpellID / Trigger / Cooldown

### G. 高级法术参数页
- 5 槽高级矩阵
  - Category / CategoryCooldown / PPM / Charges

### H. Socket 页
- 三个颜色 + 一个 bonus

### I. 高级机制页
- 随机属性 / BagFamily / Range / Scaling / Disenchant / Gem / Totem
- 再接 unk0 / money loot / food / script / duration / item limit / armor damage modifier

---

## 四、直接落地建议（双语版）
- 旧工具结构保留
- 窗口整体放大一档
- 标签统一 `FieldName（中文说明）`
- 属性/法术/高级法术参数统一做成矩阵表格
- 限制页和高级机制页加更宽标签列

---

## 五、当前结论
这份映射已足够支撑“物品信息页第一版正式复刻”，不需要再等待更多逆向才能开工。
