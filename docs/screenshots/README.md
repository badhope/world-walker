# 界面截图（docs/screenshots）

本目录是 README 预览用的实况主舞台截图，**非设计稿**——全部由真实面板在浏览器
（Edge / Chromium 内核，Playwright 驱动）中现场渲染后截取，并由
`scripts/audit_ui.py` 逐项断言后入库。

| 文件 | 内容 | 视口 |
|---|---|---|
| `stage-xuanshu.png` | 玄枢界皮肤（墨金）主舞台全页 | 1500×950 |
| `stage-ink.png` | 水墨皮肤（`ui.skin=ink`） | 1500×950 |
| `stage-neon.png` | 霓虹皮肤（`ui.skin=neon`） | 1500×950 |
| `stage-768.png` | 768px 平板视口 | 768×900 |
| `stage-320.png` | 320px 窄屏无横向滚动验证 | 320×800 |
| `drawer-codex.png` | 探索图鉴抽屉（地点/人物/物品/设定词条） | 1500×950 |
| `drawer-market.png` | 市场行情抽屉（高于/低于基准） | 1500×950 |
| `drawer-milestones.png` | 大事记抽屉 | 1500×950 |
| `help.png` | 帮助弹窗（术语表 / 状态文件路径 / 皮肤说明） | 1500×950 |
| `first-visit.png` | 首次访问引导条（localStorage 记忆，只出现一次） | 1500×950 |

截图所用状态：

- 来源为 `scripts/stress_freeplay.py` 跑出的自由玩家存档（玄枢界设定包，主角沈砚，
  回合 500、事件 120 条、大事记 12 条、摘要 20 条、归档 1318 条，侧写曲线为真实走势）。
- 截图前由 `scripts/audit_ui.py` 逐项断言（18 项）：页签标题含品牌、`data-skin`
  与请求皮肤一致、回合号/主角名/气血渲染、图表 canvas 尺寸有效、时间线有事件、
  三个抽屉可展开且滚入视口、帮助弹窗含术语表与状态文件路径、
  1500/768/320 三档无横向溢出、全程零 JS 控制台错误、零失败网络请求。
- 面板本身只读：截图过程不会写回任何对局状态。

重新生成：

```bash
python scripts/stress_freeplay.py 500          # 造一份真实长局存档
python panel.py --state <存档> --port 8803     # 起只读面板
python scripts/audit_ui.py --url http://127.0.0.1:8803   # 断言 + 截图到 scripts/_ui_shots/
```
