# 维护指南

这是 [bggRGjQaUbCoE/PiliPlus](https://github.com/bggRGjQaUbCoE/PiliPlus) 的个人长期维护版，主要加入了 iPhone Duo（折叠屏 iPhone）适配。下面的规则适用于所有改动，人和 AI 都一样。

本文件的维护规则在作者本机的 Claude 记忆里也有一份。修改其中任何一处时，两边要一起更新，保持一致。

## 分支

| 分支 | 用途 |
|---|---|
| `release` | 默认分支，长期主线。所有新改动都合并到这里 |
| `main` | 只同步上游，不放自己的改动 |

最初的 Duo 适配已冻结为标签 [`iphone-duo-v1`](https://github.com/ShionjiART/PiliPlus/releases/tag/iphone-duo-v1)，原来的 `feat/iphone-duo` 分支已删除。

## 标签

标签用来标记版本，不用来标记单个改动：

- 打出来给人用的安装包，打一个标签并发布 Release，标签名为 `duo-<上游版本号>-<序号>`，例如 `duo-2.2.0-1`。同一个上游版本每发一次序号加一，上游升级版本后从 1 重新开始。之前发布的 `iphone-duo-v1`、`iphone-duo-v2` 保持原名。
- 安装包文件名为 `PiliPlus_ios_<标签>_<日期>_<9 位提交号>_unsigned.ipa`，例如 `PiliPlus_ios_duo-2.2.0-2_20261115_835223c8e_unsigned.ipa`；同时附上同名的 `.sha256` 校验文件。文件名里的 `ios` 和提交号不能省：App 的「检查更新」靠 `ios` 找到 iOS 安装包，靠提交号判断已经装的是不是这一版。
- 发布、编辑或删除 Release 后，`AltStore Source` 工作流（`.github/workflows/altstore.yml`）会重新生成 AltStore / SideStore 源，部署到 `https://shionjiart.github.io/PiliPlus/altstore.json`。版本号、构建号和权限都从各个 Release 的安装包里读，不用手改；预发布（pre-release）不会进源。替换 Release 里的安装包不会触发 Release 事件，由每小时一次的检查发现后自动更新，最多晚一小时；急着用可以手动运行 `gh workflow run altstore.yml --repo ShionjiArt/PiliPlus`。`release` 分支上改了源的脚本、工作流或图标后，也会自动重新部署。
- 没有合并就放弃、但想留着的分支，删除前先打标签 `archive/分支名`，否则它的提交会丢失。
- fork 时从上游复制来了约 150 个标签。自己的标签统一用 `iphone-duo-`、`duo-`、`archive/` 开头，以便区分。

## 每个改动的流程

1. 从 `release` 开一个短分支，按用途加前缀：`feat/`（功能）、`fix/`（修复）、`sync/`（同步上游）、`docs/`（文档）。
2. 多个改动同时进行时，每个都在自己的 git worktree 里做，不要在同一个文件夹里切换分支。worktree 一律放在项目里的 `.claude/worktrees/<名字>`，编译和测试日志一律写到项目里的 `logs/`。这两个位置都已被 git 忽略。不要放到项目文件夹外面（例如 `../PiliPlus-Duo-xxx` 或 `../xxx.log`），以免堆在上一级目录里。
3. 改完后跑 `flutter analyze` 和相关测试。涉及界面的改动，在 iPhone Duo 模拟器上检查合上、展开和旋转；并行时每个任务新建自己的模拟器，不要共用。
4. 在本仓库开 PR 合并到 `release`，说明改了什么、为什么改、怎么测的。用户能感受到的功能和修复，在同一个 PR 里更新 [`FEATURES.md`](FEATURES.md)：新增一条或把对应的条目打勾，并附上 PR 链接。
5. 用 merge commit 合并，不用 squash。合并后删除分支（本地和 GitHub 上都删）；改动记录保留在 PR 页面，需要时可以从 PR 页面恢复分支。还要用的分支先保留，例如准备提给上游的分支。
6. 合并后不用自己打包：`release` 上的 Check 通过后，`iOS Release` 工作流会和最新的 Release 比较，改到了 App 本身（`lib/`、`ios/`、`assets/`、`pubspec.*`，同步上游也算）就自动编译、打标签、发布新的 Release，并通知 AltStore 源更新；只改文档、CI 的不发。这样 AltStore 源和 App 的「检查更新」都能收到新版本。合并后到 Actions 页面看一下它有没有成功（大约 10 分钟）；失败时修好后重跑，或按下面「发布安装包」手动补发。自动生成的说明只列出合并的 PR，需要时可以改写 Release 说明，AltStore 源会跟着更新。

## 提交

- 作者统一为 `sssakuya <moe@sssakuya.moe>`。
- 备注用中文，第一行带前缀：`功能:`、`修复:`、`同步:`、`文档:`。正文简短说明为什么改。
- 提交、PR 和评论里都不加 AI 署名（例如 `Co-Authored-By: Claude` 或 “Generated with Claude Code”）。

示例：

```text
修复: 折叠后页面状态丢失

旋转或折叠时安全区在 0 和非 0 之间变化，页面会被重建。
现在始终使用同一套结构。
```

## 同步上游

在 `sync/` 分支上把上游 `main` 合并进来，再按上面的流程合并到 `release`。只用 merge，不用 rebase，这样不需要强制推送。

和 Duo 无关的修复，可以从上游 `main` 开分支，方便以后提给上游；同时也合并到 `release`。给上游提 PR 前要先经过作者同意。

## 构建

- 本项目只能用打过补丁的 Flutter SDK 编译，补丁见 `lib/scripts/patch.ps1`。`pubspec.yaml` 锁定了具体的 Flutter 版本。
- 打过补丁的 SDK 和 pub 缓存要和其他项目分开放，不要改动其他项目共用的 SDK。
- 上游升级 Flutter 版本后，把单独的 SDK 切到新版本，再重新应用补丁。
- 在干净的构建目录里编译模拟器时，`flutter build ios --config-only` 可能要跑两次：第一次可能会在 `ios/Flutter/Generated.xcconfig` 里写入 `EXCLUDED_ARCHS[sdk=iphonesimulator*]=i386 arm64`，导致 arm64 模拟器编译失败。
- `macos/Flutter/` 下的 `.xcconfig` 会在编译时被自动修改，不要提交。

## 发布安装包

平时由 `iOS Release` 工作流（`.github/workflows/ios_release.yml`）在合并后自动发布，见「每个改动的流程」第 6 步。它和下面的手动步骤做的事一样，判断和说明由 `.github/ios-release/release.py` 生成。

- 手动运行 `gh workflow run ios_release.yml --repo ShionjiArt/PiliPlus` 默认是试运行：即使 App 没有改动也编译，安装包和说明留在运行页面（保留 7 天），不打标签、不发布。加 `-f dry_run=false` 才会在 App 有改动时真的发布。
- 工作流用 GitHub 的 `xcode-27` 镜像，选和作者本机相同的 Xcode 27.2。这个镜像目前是公开预览，转为正式版或升级 Xcode 时要跟着改。

自动发布失败或需要手动发布时，按下面的步骤做：

1. 定标签和标题：用 `gh release list --repo ShionjiArt/PiliPlus` 和 `git ls-remote --tags fork 'duo-*'` 查已有的版本，序号接着最大的加一（规则见「标签」）；标题为「iPhone Duo 适配 v<N>」，N 接着上一个 Release 加一。别的会话可能刚发过，以 GitHub 上的为准。
2. 从最新的 `fork/release` 新建一个 detached worktree `.claude/worktrees/ipa-<标签>`，在里面打包，日志写到 `logs/`：
   - 加载打过补丁的 SDK 和 pub 缓存（作者本机：`source ~/development/piliplus-env.sh`，见「构建」）。
   - 和 CI 一样给项目打 iOS 补丁：`git apply lib/scripts/bottom_sheet_ios_piliplus.patch lib/scripts/geetest_ios.patch`。
   - 照 `lib/scripts/build.ps1` 定版本：把 `pubspec.yaml` 的 `version` 改成 `<版本号>+<git rev-list --count HEAD 的结果>`，并写出 `pili_release.json`（`pili.name`、`pili.code`、`pili.hash`、`pili.time`）。
   - `flutter build ios --release --no-codesign --dart-define-from-file=pili_release.json`
   - 照 `.github/workflows/ios.yml` 里的命令，给 `Runner.app/Frameworks` 下的每个 `.framework` 做 ad-hoc 签名，再把 `Payload/Runner.app` 打成 zip。按「标签」里的规则命名，并生成同名的 `.sha256`。
3. 打带注释的标签（作者 sssakuya）推到本仓库，用 `gh release create` 发布，附上 `.ipa` 和 `.sha256`，标为最新。说明用中文，写清基于哪个提交、包含哪些 PR、用户能感受到的变化和已知问题，格式参考上一个 Release。
4. 发布后 AltStore 源会自动更新。确认线上 `altstore.json` 里出现了新版本，版本号和构建号与安装包一致，然后删除打包用的 worktree。

合并前给作者在真机上试的测试包不发 Release：文件名用 `PiliPlus_ios_test-<名字>_<日期>_<9 位提交号>_unsigned.ipa`，放在 `~/Downloads`。

## 进度

- 相对原版新增的功能和修复，见 [`FEATURES.md`](FEATURES.md)。
- 正在移植的功能和完成情况，见 [Issue #2](https://github.com/ShionjiART/PiliPlus/issues/2)。每完成一项，在 Issue 里勾选并附上 PR 链接。
- 每个分支的用途记录在作者本机的 Claude 记忆里（分支记录），新建、合并或删除分支时更新。
