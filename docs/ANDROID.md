# World Walker for Android

**v1.20.0 · `com.worldwalker.app` · minSdk 24 · targetSdk 35**

下载页：[GitHub Releases · v1.20.0](https://github.com/Morningstar202604/world-walker/releases/tag/v1.20.0)。

安卓版不是另一套规则，也不是把网页丢进浏览器。APK 里带的是同一个 Python 引擎：Chaquopy 在 App 进程里启动本地 HTTP 面板，WebView 只访问 `127.0.0.1`。模型 Key、存档、世界包、角色卡都留在 App 私有目录，不经过中转服务器。

## 下载哪一个

| 文件 | 给谁 | 体积 |
| --- | --- | --- |
| `world-walker-1.20.0-arm64-v8a.apk` | 绝大多数现役安卓手机 | 约 25 MB |
| `world-walker-1.20.0-x86_64.apk` | x86 平板、模拟器 | 约 25 MB |
| `world-walker-1.20.0-universal.apk` | 不确定机型，或两个都要 | 约 38 MB |

Release 签名证书 SHA-256：

```text
45:F9:F8:E9:31:31:12:77:F0:C3:A6:E6:B4:F8:81:25:E7:36:0A:1E:BA:7E:50:5A:DE:35:0F:17:7A:ED:7D:D1
```

升级时请覆盖安装同一包名；签名不一致会要求先卸载，存档会被清掉。

## 安装

1. 把 APK 传到手机，点开。
2. 系统会提示“未知来源”；允许当前文件管理器/浏览器安装。
3. 首次启动会看到“正在把世界放到你的口袋里…”。首次解压运行包约 2–5 秒。
4. 进入大厅后，点“模型未连接 · 去设置”，填一个 OpenAI-compatible 端点：

```text
Base URL: https://你的网关/v1
Model:    你的模型名
API Key:  你的 Key
```

端点必须能从**手机**访问；电脑上的 `localhost` 在手机上指向手机自己。局域网模型请填电脑的局域网 IP，并确保同一 Wi-Fi、防火墙放行。

## 手机壳做了什么

- 大厅、旗舰开局、知识库、战报回放、导出/分享都沿用桌面同一套页面。
- `<=760px` 时右栏不再硬塞在输入框下面，改成“面板”按钮打开的底部抽屉；返回键先收抽屉，再收弹层，最后回大厅。
- 输入框、按钮和抽屉都按 44dp 触控下限与安全区处理；键盘弹出时输入框留在可视区上方。
- 下载走 MediaStore，落在 `Downloads/World Walker`；JSON 世界包/角色卡导入走系统文件选择器。
- 首次启动铺一份折剑行演示档；之后按 `saves/` 里最近修改的存档续上。

## 架构

```text
MainActivity (Java)
  ├─ 解压 assets/runtime.zip 到 filesDir/runtime/v20/
  ├─ Python.start(AndroidPlatform)
  ├─ world_walker_android.start_server(...)
  │    ├─ 设置 HOME / TMPDIR / WW_MODEL_CONFIG / WW_HARNESS_CONFIG
  │    ├─ 解压出 game_engine 包 + settings + library + narrative_skills
  │    ├─ certifi 写入 SSL_CERT_FILE
  │    └─ panel.start(state, port=0, host=127.0.0.1)
  └─ WebView.loadUrl(http://127.0.0.1:<随机端口>/)
```

`runtime.zip` 是构建产物，不入库；`python3 scripts/build_android.py --no-build` 可单独生成并检查。APK 的 Python 源码不复制到 `android/`，始终从仓库根打包，避免两套代码漂移。

## 本地构建

需要：

- JDK 17
- Android SDK Platform 35、Build Tools 35.0.0
- Python 3.12（Chaquopy 构建机版本必须与 App 内 Python 一致）
- 网络（首次拉 Gradle/Chaquopy/PyPI 依赖）

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export ANDROID_HOME=$HOME/android-sdk

python3 scripts/build_android.py            # 签名 Release，三个 ABI
python3 scripts/build_android.py --debug    # 调试包，不签 Release
python3 scripts/verify_android.py           # 36 项静态 + 启动校验
```

产物在 `dist/android/`，含 `SHA256SUMS` 和 `build-manifest.json`。

本地 Release 密钥默认生成在 `.android-signing/`（已 gitignore）。**不要提交、不要丢**：丢了就无法给同一包名做覆盖升级。生产签名也可以改用环境变量：

```bash
WW_ANDROID_KEYSTORE=/path/to/release.jks \
WW_ANDROID_KEY_ALIAS=worldwalker \
WW_ANDROID_KEYSTORE_PASS=... \
python3 scripts/build_android.py
```

## 边界

- 安卓版只带玩家面板，不带 MCP server。MCP 仍属于桌面/服务端集成，不塞进手机后台。
- 没有常驻后台服务；App 退到后台后 WebView 暂停，回到前台会重新拉当前局面。
- 没有账号、云同步、多人桌、内购。存档只在本机，卸载即删。
- 模型调用由 Python 发出；手机系统代理、VPN 和证书策略会影响连通性。
- `certifi` 只解决 Python 侧的 HTTPS CA 路径，不绕过用户自己安装的抓包证书或企业代理。

## 排障

**卡在“世界没有醒过来”**
点“重试”。如果仍失败，把屏幕上的错误信息发我；常见原因是 APK 安装不完整、存储空间不足，或系统杀掉了进程。

**页面空白但状态栏正常**
下拉刷新不一定有用，先返回大厅再进对局；仍空白时杀掉 App 重开。`runtime.zip` 解压失败会在加载层显示错误，不会静默白屏。

**模型 401 / 404 / timeout**
先在电脑上用同一 Base URL 和 Key 测通，再检查手机是否能访问该地址。`/v1` 是否重复、网关是否只绑定了 `127.0.0.1`，是最常见的两个原因。

**下载找不到**
看 `Downloads/World Walker/`。Android 10 以下交给系统 DownloadManager，通知栏会有一条完成通知。

## 验证记录

- `scripts/verify_android.py`：37/37，通过 runtime 内容、APK 包名/版本/ABI/签名、以及“解压后真的能起面板”的启动检查。
- 已在 Android 11（API 30）x86_64 模拟器安装并启动实际 APK：健康检查返回 `version: 1.20.0`，初始档正确读到 `折剑行` 第 180 回合。期间抓到一个只在 Android 出现的路径问题：App 的 `/data/user/0/...` 在进程内是指向 `/data/data/...` 的软链，`input_policy` 的软链防护把合法存档判成不安全；改为把 Java 传入的私有目录先 `getCanonicalPath()` 后解决，`verify_android.py` 已加回归断言。
- 手机布局截图：`docs/assets/android-lobby.png`、`android-play.png`、`android-rail.png`、`android-featured.png`（390×844 视口，2× 像素密度）。
- 桌面布局在 1920×993 复查，未被手机断点改坏。
