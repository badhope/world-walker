# 安全策略

## 支持的版本

下表说明本项目哪些版本正在接收安全更新：

| 版本 | 支持状态 |
|------|---------|
| 4.x（最新） | ✅ 积极维护 |
| 3.x | ⚠️ 仅关键修复 |
| < 3.0 | ❌ 不再维护 |

## 报告漏洞

我们非常重视安全问题。如果您发现了本项目的安全漏洞，
**请勿** 在公开 Issue 中披露，请通过以下方式私下联系：

📧 **security@regional-economic-analysis.org** （替换为实际邮箱）

请在邮件中包含：

1. 漏洞的简要描述
2. 复现步骤 / PoC（最小可复现代码或 curl）
3. 影响范围（哪些组件、哪些数据）
4. 您的姓名/昵称（可选，希望致谢时使用）
5. 您是否已公开披露过

我们承诺：

- **48 小时内** 确认收到您的报告
- **7 个工作日内** 给出初步评估和修复计划
- 修复发布后公开致谢（除非您要求匿名）

## 安全最佳实践（部署侧）

部署本项目时，请务必：

1. **修改默认密钥** — `cp .env.example .env` 后，**必须** 修改：
   - `SECRET_KEY`（JWT 签名）
   - `ADMIN_PASSWORD`
   - `MODEL_SIGNING_KEY`
2. **限制 CORS 来源** — 生产环境 `CORS_ORIGINS` 不要使用 `*`
3. **启用 HTTPS** — 通过 Nginx / Caddy / Cloudflare 终止 TLS
4. **不要提交 `.env`** — 已在 `.gitignore` 中，但仍请检查
5. **定期更新依赖** — Dependabot 已配置每周自动 PR
6. **关闭调试模式** — `DEBUG=False`
7. **限制管理端口暴露** — 8000 端口只对内网开放或通过反向代理
8. **审计第三方模型** — 如加载用户上传的模型文件，启用 HMAC 签名校验

## 已知安全问题

无。

## 致谢

感谢以下安全研究者的贡献（按时间排序）：

- _暂无公开致谢_

---

> 本文件遵循 [GitHub 默认社区健康文件](https://docs.github.com/zh/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)。
