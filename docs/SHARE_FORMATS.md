# 分享格式与接口

World Walker 不维护第二套存档。战报、世界包和角色卡都是对同一份状态文件的只读投影；导入世界包会生成新档，不会覆盖原局。

## 战报回放 `world-walker.replay.v1`

`GET /api/v1/replay` 返回：

```json
{
  "format": "world-walker.replay.v1",
  "world": {"name": "灰雾荒原", "era": "第 1 天", "tick": 3, "mode": "爽文"},
  "timeline": [
    {"kind": "narrator", "tick": 0, "text": "……", "delta": null},
    {"kind": "player", "tick": 1, "text": "擦一根火柴"},
    {"kind": "narrator", "tick": 1, "text": "……", "delta": {"changes": []}}
  ],
  "counts": {"player": 1, "narrator": 2, "total": 3}
}
```

`timeline` 按 tick 排序：旧档只有 `prose` 时合成叙述行；`world_info.prologue` 作为开场段纳入，若旧 `prose` 已含同一序章则去重。每条 assistant 行可以带本回合 `delta`（有界，最多 12 项）。

`GET /api/v1/export?kind=story` 输出 Markdown：序章、`> **你**` 的玩家行动、叙述正文，以及 `结算：气血 -15；体温 1/6→3/6` 这样的差异行。它适合直接贴到论坛或存档备份，不包含模型配置。

## 世界包 `world-walker.worldpack.v1`

```json
{
  "format": "world-walker.worldpack.v1",
  "name": "灰雾荒原",
  "world": {"name": "灰雾荒原", "tick": 3, "protagonist": "陈砚"},
  "source": {"file": "灰雾荒原.save.json"},
  "contains_spoilers": true,
  "snapshot": {"world_info": {}, "entities": {}, "scene": {}}
}
```

- `snapshot` 是当前状态的完整深拷贝；导入时仍走同一套状态校验。
- `contains_spoilers: true` 是明确警告：包里带着已发现的线索、已填的压力钟和 NPC 关系，不是无剧透设定集。
- 导入 `POST /api/v1/import/world`，请求体为 `{"pack": {...}}` 或世界包本体；上限 4 MB。导入会写一份新存档并切换当前局，不信任包里的外部路径，只在 `imported_from` 记格式、名称和导出时间。

## 角色卡 `chara_card_v2`

`GET /api/v1/export?kind=character` 把当前主角投影成 SillyTavern V2 卡。引擎自己的活动字段（`activity/intent/mood/routine/status/agenda/aliases/location/last_seen_tick`）放进 `data.extensions.world_walker`，不会被别的工具误当提示词。

`POST /api/v1/import/character` 接受 `{"card": {...}, "entity_id": "可选", "hp": 100, "location": "可选"}`，上限 1 MB。JSON 卡会在当前局里落成一个 NPC；PNG 卡仍走 MCP 的 `character_card_read` + `add_character`，因为面板不解析图片里的元数据。

## 接口一览

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/v1/replay` | 回放时间线 |
| GET | `/api/v1/export?kind=save` | 原样下载当前存档 |
| GET | `/api/v1/export?kind=story` | Markdown 战报 |
| GET | `/api/v1/export?kind=world` | 世界包 JSON |
| GET | `/api/v1/export?kind=character` | V2 角色卡 JSON |
| POST | `/api/v1/import/world` | 导入世界包，生成新档 |
| POST | `/api/v1/import/character` | 导入 JSON 角色卡为 NPC |

面板只监听 `127.0.0.1`；这些接口默认没有公网鉴权，不要把端口直接暴露到公网。

## 边界

- 世界包可以给朋友，但会剧透。只想分享世界观，导出设定包或写一份不带 `snapshot` 的说明。
- 战报是 Markdown，不是可执行页面；不要把它当 HTML 渲染。
- 角色卡导入只做结构化投影，不会执行卡里的提示词，也不会绕过 `canon` 与知识边界。
