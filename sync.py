#!/usr/bin/env python3
"""
sync.py - 同步 claude-profile 仓库中的 CLAUDE.md 与本地 ~/.claude/CLAUDE.md

逻辑：
- git 仓库新增的内容 → 自动合并到本地
- 本地新增的内容（不在 git 仓库中）→ 自动合并到 git 仓库，并提示
- 两者完全一致 → 提示无需同步
"""

import subprocess
import sys
import os
from pathlib import Path
from difflib import unified_diff

# Windows 终端中文输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


REPO_DIR = Path(__file__).parent.resolve()
REPO_FILE = REPO_DIR / "CLAUDE.md"
LOCAL_FILE = Path.home() / ".claude" / "CLAUDE.md"


def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def read_lines(path):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def show_diff(label_a, lines_a, label_b, lines_b):
    diff = list(unified_diff(lines_a, lines_b, fromfile=label_a, tofile=label_b))
    if diff:
        print("".join(diff))
    return diff


def extract_only_in(lines_a, lines_b):
    """返回只在 lines_a 中出现、不在 lines_b 中出现的行（去重）"""
    set_b = set(lines_b)
    return [l for l in lines_a if l not in set_b]


def main():
    print("=" * 50)
    print("Claude Profile 同步工具")
    print("=" * 50)

    # Step 1: git pull
    print("\n[1/4] 正在执行 git pull ...")
    out, err, code = run("git pull", cwd=REPO_DIR)
    if code != 0:
        print(f"git pull 失败：{err}")
        sys.exit(1)
    print(f"  {out or '已是最新'}")

    # Step 2: 读取两个文件
    repo_lines = read_lines(REPO_FILE)
    local_lines = read_lines(LOCAL_FILE)

    if not repo_lines:
        print("\n仓库中 CLAUDE.md 为空，退出。")
        sys.exit(0)

    if not local_lines:
        print(f"\n本地 {LOCAL_FILE} 不存在，直接复制仓库版本。")
        LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_FILE.write_text("".join(repo_lines), encoding="utf-8")
        print("  已复制到本地。")
        sys.exit(0)

    # Step 3: 对比差异
    print("\n[2/4] 对比差异 ...")
    diff = show_diff(f"git:{REPO_FILE.name}", repo_lines, f"local:{LOCAL_FILE}", local_lines)

    if not diff:
        print("  两个文件完全一致，无需同步。")
        sys.exit(0)

    # Step 4: 分析差异方向
    only_in_repo  = extract_only_in(repo_lines, local_lines)   # git 有、本地没有
    only_in_local = extract_only_in(local_lines, repo_lines)   # 本地有、git 没有

    print(f"\n[3/4] 差异分析：")
    print(f"  仓库新增（将自动同步到本地）: {len(only_in_repo)} 行")
    print(f"  本地新增（将自动合并到仓库）: {len(only_in_local)} 行")

    # Step 5: 合并
    print("\n[4/4] 执行合并 ...")

    if only_in_repo and not only_in_local:
        # 仓库更新了，直接用仓库版本覆盖本地
        LOCAL_FILE.write_text("".join(repo_lines), encoding="utf-8")
        print("  本地文件已更新为仓库最新版本。")

    elif only_in_local and not only_in_repo:
        # 本地有新增，合并进仓库版本
        merged = repo_lines + ["\n"] + only_in_local
        merged_text = "".join(merged)
        REPO_FILE.write_text(merged_text, encoding="utf-8")
        LOCAL_FILE.write_text(merged_text, encoding="utf-8")
        print("  本地新增内容已合并进仓库版本，两端同步。")
        print("\n  本地新增内容如下：")
        for line in only_in_local:
            print(f"    + {line}", end="")
        _git_commit_and_push()

    else:
        # 双向都有新增，各自追加到对方
        merged = repo_lines + ["\n"] + only_in_local
        merged_text = "".join(merged)
        REPO_FILE.write_text(merged_text, encoding="utf-8")
        LOCAL_FILE.write_text(merged_text, encoding="utf-8")
        print("  双向合并完成，两端已同步。")
        print("\n  本地新增内容（已合并进仓库）：")
        for line in only_in_local:
            print(f"    + {line}", end="")
        _git_commit_and_push()

    print("\n同步完成。")


def _git_commit_and_push():
    print("\n  提交并推送仓库变更 ...")
    run("git add CLAUDE.md", cwd=REPO_DIR)
    out, err, code = run('git commit -m "sync: 合并本地新增内容"', cwd=REPO_DIR)
    if code != 0:
        print(f"  commit 失败：{err}")
        return
    out, err, code = run("git push", cwd=REPO_DIR)
    if code != 0:
        print(f"  push 失败：{err}")
    else:
        print("  推送成功。")


if __name__ == "__main__":
    main()
