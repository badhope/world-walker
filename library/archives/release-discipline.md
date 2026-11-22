# 发布纪律

> 一个版本能不能发，不看提交时间，看门禁、安装包和五个远端是否同时成立。

标签：发布，质量，五平台

## 发布前

- `scripts/ci_core.sh` 与 `scripts/pre_push_gate.sh` 必须全绿；干净副本跑，避免旧 `build/lib` 干扰。
- `docs/metrics.json` 由 `scripts/metrics.py --write` 生成，文档只引用，不手写。
- wheel 必须通过 `scripts/check_wheel.py`；面板、设定包、叙事技能和知识库都要在包里。
- Windows 安装包由 `scripts/build_exe.py` 在 Windows 上构建；Linux 不能交叉编译 PyInstaller 的 exe。

## 发布后

- GitHub 三个账号、Gitee、GitCode 的 `main` 必须指向同一提交。
- 每个平台的 Release 都要有安装包附件，不能只有源码 zip。
- Gitee / GitCode 的附件走各自 Release 附件接口；只创建 Release 不算发完。
