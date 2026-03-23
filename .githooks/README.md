# Git 钩子

启用后，`pre-commit` 会拦截误加入暂存区的机密路径。

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

说明：[`docs/REPOSITORY-PUBLIC-BOUNDARY.md`](../docs/REPOSITORY-PUBLIC-BOUNDARY.md)
