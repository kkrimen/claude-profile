#!/usr/bin/env python3
"""
sync.py - 同步 claude-profile 仓库与本地 ~/.claude/ 配置

同步范围：
- CLAUDE.md（主配置文件）
- rules/*.md（模块化规则文件）
- ideas-todo.md（想法捕捉列表）

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
LOCAL_CLAUDE_DIR = Path.home() / ".claude"

# 需要同步的文件对：(仓库路径, 本地路径)
SYNC_FILES = [
    (REPO_DIR / "CLAUDE.md",          LOCAL_CLAUDE_DIR / "CLAUDE.md"),
    (REPO_DIR / "ideas-todo.md",       LOCAL_CLAUDE_DIR / "ideas-todo.md"),
]

# 需要同步的目录：(仓库子目录, 本地子目录)
SYNC_DIRS = [
    (REPO_DIR / "rules", LOCAL_CLAUDE_DIR / "rules"),
]


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


def sync_file_pair(repo_file, local_file, has_changes):
    """同步单个文件对，返回是否产生了需要 git commit 的变更"""
    print(f"\n  文件: {repo_file.name}")

    repo_lines = read_lines(repo_file)
    local_lines = read_lines(local_file)

    if not repo_lines and not local_file.exists():
        print("    两端均不存在，跳过。")
        return False

    if not repo_lines:
        # 仓库无此文件，本地有 → 复制到仓库
        print(f"    本地有，仓库无 → 复制到仓库")
        repo_file.parent.mkdir(parents=True, exist_ok=True)
        repo_file.write_text("".join(local_lines), encoding="utf-8")
        return True

    if not local_lines:
        # 本地无此文件 → 复制到本地
        print(f"    仓库有，本地无 → 复制到本地")
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_text("".join(repo_lines), encoding="utf-8")
        return False

    diff = show_diff(f"git:{repo_file.name}", repo_lines, f"local:{local_file.name}", local_lines)
    if not diff:
        print("    一致，无需同步。")
        return False

    only_in_repo  = extract_only_in(repo_lines, local_lines)
    only_in_local = extract_only_in(local_lines, repo_lines)

    print(f"    仓库新增 {len(only_in_repo)} 行，本地新增 {len(only_in_local)} 行")

    if only_in_repo and not only_in_local:
        local_file.write_text("".join(repo_lines), encoding="utf-8")
        print("    本地已更新为仓库最新版本。")
        return False

    elif only_in_local and not only_in_repo:
        merged = repo_lines + ["\n"] + only_in_local
        merged_text = "".join(merged)
        repo_file.write_text(merged_text, encoding="utf-8")
        local_file.write_text(merged_text, encoding="utf-8")
        print("    本地新增已合并入仓库，两端同步。")
        return True

    else:
        merged = repo_lines + ["\n"] + only_in_local
        merged_text = "".join(merged)
        repo_file.write_text(merged_text, encoding="utf-8")
        local_file.write_text(merged_text, encoding="utf-8")
        print("    双向合并完成，两端已同步。")
        return True


def sync_directory(repo_dir, local_dir):
    """同步目录下所有 .md 文件，返回是否有变更需要 commit"""
    repo_dir.mkdir(parents=True, exist_ok=True)
    local_dir.mkdir(parents=True, exist_ok=True)

    # 收集两端所有 .md 文件名
    repo_files  = {f.name for f in repo_dir.glob("*.md")}
    local_files = {f.name for f in local_dir.glob("*.md")}
    all_files   = repo_files | local_files

    has_changes = False
    for fname in sorted(all_files):
        changed = sync_file_pair(repo_dir / fname, local_dir / fname, has_changes)
        if changed:
            has_changes = True
    return has_changes


def main():
    print("=" * 50)
    print("Claude Profile 同步工具")
    print("=" * 50)

    # Step 1: git pull
    print("\n[1/3] 正在执行 git pull ...")
    out, err, code = run("git pull", cwd=REPO_DIR)
    if code != 0:
        print(f"git pull 失败：{err}")
        sys.exit(1)
    print(f"  {out or '已是最新'}")

    # Step 2: 同步文件
    print("\n[2/3] 同步文件 ...")
    needs_commit = False

    print("\n--- 单文件同步 ---")
    for repo_file, local_file in SYNC_FILES:
        if sync_file_pair(repo_file, local_file, needs_commit):
            needs_commit = True

    print("\n--- 目录同步 ---")
    for repo_subdir, local_subdir in SYNC_DIRS:
        print(f"\n  目录: {repo_subdir.name}/")
        if sync_directory(repo_subdir, local_subdir):
            needs_commit = True

    # Step 3: 提交推送
    print("\n[3/3] 提交推送 ...")
    if not needs_commit:
        print("  无需提交。")
    else:
        _git_commit_and_push()

    print("\n同步完成。")


def _git_commit_and_push():
    print("  提交并推送仓库变更 ...")
    run("git add CLAUDE.md ideas-todo.md rules/", cwd=REPO_DIR)
    out, err, code = run('git commit -m "sync: 合并本地新增内容"', cwd=REPO_DIR)
    if code != 0:
        print(f"  commit 失败（可能无变更）：{err}")
        return
    out, err, code = run("git push", cwd=REPO_DIR)
    if code != 0:
        print(f"  push 失败：{err}")
    else:
        print("  推送成功。")


if __name__ == "__main__":
    main()
