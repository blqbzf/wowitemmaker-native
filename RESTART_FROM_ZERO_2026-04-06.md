# 从零重开（基于逆向成果与规格文档）

## 保留
- ITEMINFO_MAPPING_2026-04-06.md
- iteminfo-layout-plan.json
- 逆向得到的 ItemInfo -> UI 映射
- 旧 WOWItemMaker 的 tab / group / 页面结构理解

## 废弃
- 当前半成品 V2 迁移状态
- 当前坏掉的默认入口切换思路
- 当前未跑通的混合接线状态

## 新开发原则
1. 新页面 / 新闭环 / 新入口，不污染旧页
2. 先做最小可用链：
   - 连接配置
   - 测试连接
   - 读取 item
   - 回填主字段
   - 保存 item
   - 保存 locale
3. 每步都先本地跑通再继续
4. 跑通后再加：
   - 删除
   - normalize
   - 字典
   - 联动
   - SQL
   - app / exe 壳
