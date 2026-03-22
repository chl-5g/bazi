# Cursor 里 `git commit` 报错 `unknown option trailer`

Cursor 默认会给 Agent 触发的 `git commit` 加上 `--trailer "Made-with: Cursor"`。  
**Apple 自带的 Git（如 2.24）没有 `git commit --trailer`**（该选项约在 **Git 2.32+** 才有），所以会报错。

## 做法一：关掉提交署名（推荐）

- **Cursor 里（IDE Agent）**  
  **Settings → Agents → Attribution**  
  关闭 **Commit attribution**（「将 Agent 提交标记为 Made with Cursor」一类选项）。  
  官方说明见论坛：[Bug: unsupported `--trailer`](https://forum.cursor.com/t/bug-report-git-commit-commands-automatically-add-unsupported-trailer-option/153427)。

- **Cursor CLI（`~/.cursor/cli-config.json`）**  
  将 `attribution.attributeCommitsToAgent` 设为 **`false`**（与 IDE 设置独立）。

## 做法二：升级 Git

安装 **2.32+** 并保证终端优先用它，例如：

```bash
brew install git
# 把 Homebrew 的 bin 放在 PATH 前面（二选一或都写上，不存在的路径会被忽略）
echo 'export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
git --version   # 应显示 2.32+，且路径多为 /opt/homebrew 或 /usr/local
```

若 `brew install git` 报错 **Command Line Tools are too outdated**，请先在 **系统设置 → 软件更新** 更新「命令行开发者工具」，或执行：

```bash
sudo rm -rf /Library/Developer/CommandLineTools
sudo xcode-select --install
```

也可从 [Apple Developer 下载](https://developer.apple.com/download/all/) 安装对应 macOS 版本的 **Command Line Tools for Xcode**，再重试 `brew install git`。

## 仍失败时的临时做法

在终端里不用 Agent 包装、直接 `git commit`，或使用 `git commit-tree` 等方式创建提交（不经过带 `--trailer` 的包装）。
