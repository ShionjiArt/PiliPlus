#!/usr/bin/env python3
"""自动发布 iOS 安装包时用到的两步，由 .github/workflows/ios_release.yml 调用。

plan <提交>    判断要不要发布：和最新的 Release 相比，改到了 App 本身才发。
               算出新的标签、标题和上一版，写进 GITHUB_OUTPUT（本机运行时打印出来）。
notes <提交>   生成中文的 Release 说明，打印到标准输出。

也可以在本机运行检查（需要 gh 和完整的 git 历史与标签）：

    python3 .github/ios-release/release.py plan $(git rev-parse fork/release)
    python3 .github/ios-release/release.py notes <提交> --prev duo-2.2.1-2 --tag duo-2.2.1-3 --title "iPhone Duo 适配 v6"
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

# 这些路径有改动才算改到了 App 本身；只改文档、CI、AltStore 源的不发布。
APP_PATHS = ["lib", "ios", "assets", "pubspec.yaml", "pubspec.lock"]


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def succeeds(*args: str) -> bool:
    return subprocess.run(args, capture_output=True).returncode == 0


def repo() -> str:
    return os.environ.get("GITHUB_REPOSITORY", "ShionjiArt/PiliPlus")


def latest_release_tag() -> str:
    return run("gh", "api", f"repos/{repo()}/releases/latest", "--jq", ".tag_name")


def pubspec_version(sha: str) -> str:
    match = re.search(r"^version:\s*([\d.]+)", run("git", "show", f"{sha}:pubspec.yaml"), re.M)
    if not match:
        raise SystemExit("pubspec.yaml 里找不到 version")
    return match.group(1)


def next_tag(version: str) -> str:
    """duo-<上游版本号>-<序号>：同一个上游版本序号加一，新版本从 1 开始。"""
    numbers = [
        int(m.group(1))
        for t in run("git", "tag", "-l", f"duo-{version}-*").split()
        if (m := re.fullmatch(rf"duo-{re.escape(version)}-(\d+)", t))
    ]
    return f"duo-{version}-{max(numbers, default=0) + 1}"


def next_title() -> str:
    """「iPhone Duo 适配 v<N>」，N 接着已有 Release 里最大的加一。"""
    names = run("gh", "release", "list", "--repo", repo(), "--limit", "200", "--json", "name", "--jq", ".[].name")
    numbers = [int(m.group(1)) for n in names.splitlines() if (m := re.search(r"适配 v(\d+)", n))]
    return f"iPhone Duo 适配 v{max(numbers, default=0) + 1}"


def merged_prs(prev: str, sha: str) -> list[tuple[str, str]]:
    """上一版之后合并进 release 的 PR：(编号, 标题)，按合并顺序。"""
    log = run("git", "log", "--merges", "--first-parent", "--reverse", "--format=%s%x1f%b%x1e", f"{prev}..{sha}")
    prs = []
    for record in filter(None, (r.strip() for r in log.split("\x1e"))):
        subject, _, body = record.partition("\x1f")
        match = re.match(r"Merge pull request #(\d+) ", subject)
        if match:
            title = next((line.strip() for line in body.splitlines() if line.strip()), subject)
            prs.append((match.group(1), title))
    return prs


def write_outputs(values: dict[str, str]) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    lines = "".join(f"{k}={v}\n" for k, v in values.items())
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(lines)
    print(lines, end="")


def plan(sha: str, prev: str | None) -> None:
    prev = prev or latest_release_tag()
    version = pubspec_version(sha)
    values = {
        "sha": sha,
        "prev_tag": prev,
        "version": version,
        "tag": next_tag(version),
        "title": next_title(),
    }
    already = [t for t in run("git", "tag", "--points-at", sha).split() if t.startswith("duo-")]
    if already:
        values |= {"release": "false", "reason": f"这个提交已经发布过（{already[0]}）"}
    elif not succeeds("git", "merge-base", "--is-ancestor", prev, sha):
        values |= {"release": "false", "reason": f"{sha[:9]} 不在 {prev} 之后"}
    else:
        changed = run("git", "diff", "--name-only", prev, sha, "--", *APP_PATHS).splitlines()
        if changed:
            values |= {"release": "true", "reason": f"和 {prev} 相比改了 {len(changed)} 个 App 文件"}
        else:
            values |= {"release": "false", "reason": f"和 {prev} 相比没有改到 App（只改了文档、CI 等）"}
    write_outputs(values)


def notes(sha: str, prev: str, tag: str, title: str, build: str | None, min_os: str | None, ipa: str | None,
          sha256: str | None) -> None:
    version = pubspec_version(sha)
    owner, name = repo().split("/")
    base = f"https://github.com/{repo()}"
    prs = merged_prs(prev, sha)
    lines = [
        f"PiliPlus {version} 的 iPhone Duo（可折叠 iPhone）适配 {title.rsplit(' ', 1)[-1]}，"
        f"基于 `release` 分支的提交 {sha[:9]}，包含 [{prev}]({base}/releases/tag/{prev}) 之后合并的改动。"
        f"完整清单见 [FEATURES.md]({base}/blob/release/FEATURES.md)。",
        "",
        "## 合并的改动",
        "",
        *([f"- {t}（#{n}）" for n, t in prs] or ["- （没有找到合并的 PR）"]),
        "",
        "## 安装",
        "",
        f"- 可以在 AltStore 或 SideStore 里添加源 https://{owner.lower()}.github.io/{name}/ ，之后会自动收到更新。",
    ]
    detail = "，".join(filter(None, [f"版本 {version}+{build}" if build else None, f"最低 iOS {min_os}" if min_os else None]))
    lines.append(f"- 附件是**未签名**的 IPA{f'（{detail}）' if detail else ''}，也可以自己签名后安装。")
    if ipa and sha256:
        lines.append(f"- IPA 的 SHA-256：`{sha256}`，同一个值也放在附件 `{ipa}.sha256` 里，"
                     f"可以用 `shasum -a 256 -c {ipa}.sha256` 校验。")
    lines += ["", "> 这份说明由 GitHub Actions 在合并后自动生成，之后可能会补充更详细的说明。"]
    print("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan")
    p.add_argument("sha")
    p.add_argument("--prev", help="和哪个标签比较，默认是最新的 Release")
    n = sub.add_parser("notes")
    n.add_argument("sha")
    n.add_argument("--prev", required=True)
    n.add_argument("--tag", required=True)
    n.add_argument("--title", required=True)
    n.add_argument("--build")
    n.add_argument("--min-os")
    n.add_argument("--ipa", help="安装包文件名")
    n.add_argument("--sha256")
    args = parser.parse_args()
    sha = run("git", "rev-parse", f"{args.sha}^{{commit}}")
    if args.command == "plan":
        plan(sha, args.prev)
    else:
        notes(sha, args.prev, args.tag, args.title, args.build, args.min_os, args.ipa, args.sha256)


if __name__ == "__main__":
    sys.exit(main())
