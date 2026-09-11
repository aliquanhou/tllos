# TLL OS Canonical Validator

Canonical Layer JSON 结构验证器。

## 功能

验证以下 Canonical JSON 文件的结构完整性：

| 文件 | 验证内容 |
|------|----------|
| `tllos/identity/genesis.json` | Genesis 身份字段完整 |
| `tllos/identity/canonical_manifest.json` | Manifest 字段完整 |
| `tllos/agents/agent_capability.json` | Agent 能力描述字段完整 |
| `tllos/truth/evidence_index.json` | Evidence 索引字段完整 |

## 用法

```bash
# 从项目根目录运行
python tools/canonical_validator/validate_json.py
```

## 退出码

- `0`: 全部验证通过
- `1`: 存在验证失败

## 验证等级

当前：**Basic Structural Validation**

- ✅ JSON 文件可以正常 parse
- ✅ 必需字段存在
- ✅ 字段类型正确

未来升级：
- 完整 JSON Schema Validation（使用 jsonschema 库）
- Hash 一致性验证（对比 manifest 中记录的 SHA256）

## CI 集成

本验证器已接入 GitHub Actions CI gate。
任何 push 到主分支的修改，如果破坏了 Canonical Layer 结构，CI 会自动 FAIL。
