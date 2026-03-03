# claude-profile

用于保存和同步我在 Claude Code 中的个人协作配置，包括用户画像、协作规则、想法记录等。

任意设备 clone 后执行一条命令即可恢复完整的 Claude 协作机制。

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `CLAUDE.md` | 用户画像与协作指令，Claude Code 自动读取 |
| `ideas-todo.md` | 对话中捕捉的想法与待办事项 |
| `sync.py` | 同步脚本，负责合并仓库与本地的 CLAUDE.md |

---

## 首次使用（新设备）

**1. 克隆仓库**
```bash
git clone https://github.com/kkrimen/claude-profile.git
cd claude-profile
```

**2. 执行同步脚本**
```bash
python sync.py
```

脚本会自动将 `CLAUDE.md` 同步到 `~/.claude/CLAUDE.md`，对所有 Claude Code 会话全局生效。

**3. 启动 Claude Code**

在任意目录启动，画像和协作规则自动加载：
```bash
claude
```

---

## 日常使用

每次开始工作前，进入仓库目录执行同步，确保配置是最新的：
```bash
cd claude-profile
python sync.py
```

---

## 同步逻辑说明

`sync.py` 会对比仓库中的 `CLAUDE.md` 与本地 `~/.claude/CLAUDE.md`，按以下规则处理：

| 情况 | 处理方式 |
|------|---------|
| 仓库有新内容，本地没有 | 自动更新本地文件 |
| 本地有新内容，仓库没有 | 自动合并进仓库并 push |
| 双向都有新增 | 合并后两端同步并 push |
| 完全一致 | 提示无需同步 |

---

## 注意事项

- 首次使用的设备需确保已配置 git 用户信息：
  ```bash
  git config --global user.email "kkrimen@gmail.com"
  git config --global user.name "kkrimen"
  ```
- 需要 Python 3.6+，无额外依赖
