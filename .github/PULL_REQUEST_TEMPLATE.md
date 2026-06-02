<!-- markdownlint-disable MD041 MD024 -->
# Pull Request 模板 / Pull Request Template

感谢你为本项目贡献代码！在提交 PR 之前，请确认完成以下检查项。

Thank you for contributing! Please confirm the following before submitting.

---

## 变更说明 / Description

<!-- 请清晰描述本次 PR 的目的和实现思路 -->
<!-- Please describe the purpose and implementation of this PR -->

### 解决的问题 / Issue

<!-- 使用 Fixes #123 / Closes #456 关联 Issue -->
<!-- Use Fixes #123 / Closes #456 to link issues -->

- Fixes #
- Related: #

### 变更类型 / Type of Change

- [ ] 🐛 Bug 修复 (Bug fix)
- [ ] ✨ 新功能 (New feature)
- [ ] 💥 破坏性变更 (Breaking change)
- [ ] 📝 文档更新 (Documentation)
- [ ] 🎨 代码风格 (Style/Formatting)
- [ ] ♻️ 重构 (Refactoring)
- [ ] ⚡ 性能优化 (Performance)
- [ ] ✅ 测试 (Tests)

---

## 改动文件 / Files Changed

<!-- 列出主要改动文件 -->
<!-- List main changed files -->

- `path/to/file1.py`
- `path/to/file2.html`

---

## 测试 / Testing

### 自动化测试 / Automated Tests

- [ ] 已添加单元测试
- [ ] 已添加集成测试
- [ ] 全部测试通过 (`make test`)
- [ ] 测试覆盖率 ≥ 80%

### 手动测试 / Manual Testing

<!-- 描述你如何手动验证了这些变更 -->
<!-- Describe how you manually verified -->

1. 步骤 1
2. 步骤 2
3. 结果：✅ / ❌

### 浏览器测试 (如涉及前端)

- [ ] Chrome 桌面端
- [ ] Firefox 桌面端
- [ ] Safari 桌面端
- [ ] 移动端响应式

### 截图 / Screenshots (如适用)

<!-- 拖拽图片到此处 -->

---

## 检查清单 / Checklist

### 代码质量 / Code Quality

- [ ] 遵循 [CONTRIBUTING.md](./CONTRIBUTING.md) 中的代码规范
- [ ] 已运行 `make lint` 无错误
- [ ] 已运行 `make format` 格式化
- [ ] 已运行 `make typecheck` 类型检查通过
- [ ] 没有引入新的 lint 警告
- [ ] 没有遗留的 `print()` / `console.log()` / 调试代码
- [ ] 没有遗留的 TODO/FIXME (或已在 PR 描述中说明)

### 文档 / Documentation

- [ ] 更新了相关文档
- [ ] 更新了 API 文档 (如修改了 API)
- [ ] 更新了 CHANGELOG.md
- [ ] 添加/更新了 docstring
- [ ] 复杂逻辑添加了注释说明

### 兼容性 / Compatibility

- [ ] 向后兼容 (不破坏现有功能)
- [ ] 已更新依赖 (`requirements.txt`)
- [ ] 已更新环境变量 (`.env.example`)
- [ ] 数据库迁移脚本 (如需)
- [ ] 没有引入新的安全漏洞

### 部署 / Deployment

- [ ] 本地构建成功 (`docker-compose build`)
- [ ] 本地运行正常 (`docker-compose up`)
- [ ] 健康检查通过 (`/health` 返回 200)
- [ ] 没有破坏现有 API 契约

---

## 风险评估 / Risk Assessment

<!-- 评估本次变更的潜在风险及回滚方案 -->
<!-- Assess potential risks and rollback plan -->

**风险等级 / Risk Level**: 🟢 Low / 🟡 Medium / 🔴 High

**影响范围 / Impact**:

**回滚方案 / Rollback Plan**:

---

## 关联信息 / Related Information

### 依赖的 PR / Dependent PRs

- #

### 阻塞的 PR / Blocking PRs

- #

### 文档链接 / Documentation Links

-

---

## 审查者建议 / Reviewer Suggestions

<!-- @ 提及你希望审查此 PR 的人 -->
<!-- @ mention reviewers -->

@

---

## 附加信息 / Additional Notes

<!-- 任何其他审查者需要知道的信息 -->
<!-- Any other information reviewers should know -->

