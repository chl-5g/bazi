# 仓库公开边界（机密不入库）

本仓库会同步到 **GitHub 等公开远程**。以下内容属于**产品核心机密或课程衍生资产**，**必须只留在本机**，已通过根目录 `.gitignore` 排除。

## 永不提交的路径（摘要）

| 路径 | 原因 |
|------|------|
| `docs/blind-fate-*` | 规则清单、口播归纳、引擎对齐等 |
| `docs/disk-space-asr.md` | 与私有转写流程强相关 |
| `blind_fate*.txt` | 笔记/抽取稿 |
| `local/blind-fate-private/` | 建议将上述材料副本统一放此目录（自建） |
| `local/course-transcripts/` | ASR 全文 |
| `tools/course-transcribe/` | 转写脚本、纠错表、桌面输出路径与课名引用 |

## 协作者与本机习惯

1. **不要**使用 `git add -f` 强行加入上述文件。
2. 启用钩子（一次性）：

   ```bash
   cd /path/to/bazi
   git config core.hooksPath .githooks
   chmod +x .githooks/pre-commit
   ```

   提交前若暂存区含被禁路径，提交会被拒绝。

3. 若历史里**曾经误提交**过机密文件：仅靠 `.gitignore` 不够，需从历史中清除（如 `git filter-repo`）并轮换可能泄露的密钥。

## 公开仓库里允许的内容

- 通用排盘 Web / MCP 代码、`ai-fortune` **占位 UI**（不含盲派规则 JSON/清单）。
- 本文件与 `docs/cursor-git-commit.md` 等**不含**课程推理链的说明。
