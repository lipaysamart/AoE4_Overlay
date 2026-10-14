# Windows 打包说明

本说明用于在 Windows x64 上构建 AoE4 Overlay，生成包含运行库、图片和网页
资源的 ZIP 包。流程使用 Python 3.11、MSVC 和 Nuitka，沿用项目锁定的运行依赖。

命令请按顺序在**同一个 PowerShell 窗口**中执行。示例项目目录为
`C:\Build\AoE4_Overlay`；使用其他目录时修改第 2 步的路径。
任一步失败时停止执行，先处理错误，再继续。

> 验证状态：命令已按当前源码和官方参数核对，但尚未在 Windows 上实际执行。
> 桌面中文支持已实现；五项优先缺陷仍是已知问题，见
> [优先问题修复方案](priority-fixes.md)。

## 使用 GitHub Actions 自动打包

工作流文件为 [Windows build](../.github/workflows/windows-build.yml)。它使用
Windows 2022 runner、Python 3.11 x64 和 MSVC，先运行桌面测试，再构建并打包。
运行依赖来自 `requirements.txt`，构建工具版本固定在 `requirements-build.txt`。

提交并推送项目改动后，可在 GitHub 仓库的 **Actions → Windows build →
Run workflow** 中选择分支并启动。手动入口需要该工作流已存在于默认分支。
它也会在 `main` 或 `dev` 上的源码、测试、依赖、许可证或工作流变更时自动运行，
并验证面向这两个分支的相关 PR；仅修改说明文档不会触发自动构建。

推送形如 `v1.2.3` 的标签会构建正式版本并在构建成功后创建 GitHub Release，
并附上 `AoE4_Overlay.zip` 与 `SHA256SUMS.txt`。标签推送不经过路径过滤，
且只接受 `v` 加三段数字的格式；构建前会校验标签与应用内 `VERSION` 一致，
不一致时在构建阶段直接失败，不会产出程序包或 Release。

构建成功后，在运行页面的 **Artifacts** 下载 `AoE4_Overlay-windows-x64`。
下载的 artifact 包含 `AoE4_Overlay.zip` 和 `SHA256SUMS.txt`；解压前者后即可
运行程序。构建日志、依赖记录及编译报告保存在 `windows-build-diagnostics`，
失败时也会尝试上传。程序包保留 30 天，诊断文件保留 14 天。

此工作流在分支运行时把构建产物上传为 Actions artifact（保留 30 天），
在版本标签运行时额外创建 GitHub Release；不需要配置额外 Secrets。
产物结构检查不能替代真实 Windows 上的 GUI、全局快捷键与 OBS 人工验收。
同一分支或 PR 的新运行会取消尚未完成的旧运行。

以下步骤用于在自己的 Windows 机器上手动构建。

## 1. 安装构建工具

### Python

从 [Python 3.11.9 官方页面](https://www.python.org/downloads/release/python-3119/)
下载 **Windows installer (64-bit)**。安装时勾选 Python Launcher，保留 pip 和
venv 组件。这里选择 3.11 系列以配合项目现有的旧依赖，不代表本项目已经验证
其他 Python 版本。

### C++ 编译器

安装 Visual Studio C++ Build Tools，在安装器中选择**使用 C++ 的桌面开发**，
包含 MSVC x64/x86 构建工具及 Windows SDK；保留英文语言包。

参考：[Microsoft C++ 安装说明](https://learn.microsoft.com/en-us/cpp/build/vscpp-step-0-installation?view=msvc-170)、
[Nuitka 编译器要求](https://nuitka.net/user-documentation/user-manual.html)。

安装后打开 **Developer PowerShell for VS 2022**。如果安装的是更新版本，
打开对应版本的 Developer PowerShell。本说明不需要激活虚拟环境，也无需
修改 PowerShell 执行策略。

## 2. 复制项目并检查 Python

把 Mac 上**包含当前改动的项目**复制到：

```text
C:\Build\AoE4_Overlay
```

项目应包含 `requirements.txt`、`requirements-build.txt`、`LICENSE`、完整的
`src` 目录和 `tests` 目录。
特别检查新文件：

```text
src\overlay\i18n.py
tests\test_localization.py
```

仅从 GitHub 克隆尚未更新的远端代码，不会包含本次中文支持。无需复制 Mac
的虚拟环境、构建产物和 `__pycache__` 缓存。

```powershell
Set-Location C:\Build\AoE4_Overlay

py -3.11 --version
py -3.11 -c "import struct; print('Python bits:', struct.calcsize('P') * 8)"
```

第二条应输出 `Python bits: 64`。如果找不到 `py`，重新打开 Developer
PowerShell，并检查 Python Launcher 是否安装；也可以使用 Python 3.11
解释器的完整路径替代 `py -3.11`。

## 3. 创建虚拟环境并安装依赖

直接使用虚拟环境中的解释器，确保安装与构建使用同一个 Python：

```powershell
py -3.11 -m venv .venv-win
if ($LASTEXITCODE -ne 0) { throw "创建虚拟环境失败" }

$Python = Join-Path (Get-Location) ".venv-win\Scripts\python.exe"

& $Python -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { throw "安装基础构建工具失败" }

& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "安装项目依赖失败" }

& $Python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "安装 Nuitka 失败" }

& $Python -m pip check
if ($LASTEXITCODE -ne 0) { throw "依赖检查失败" }

& $Python -m nuitka --version
& $Python -m nuitka --help
```

项目运行依赖沿用 `requirements.txt`，不升级其中的版本。构建依赖使用
`requirements-build.txt`，与 CI 保持一致。
后续会记录本次实际使用的完整依赖版本，方便复现。

## 4. 验证源码

先运行自动化测试，再启动源码程序：

```powershell
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "测试失败，请先处理错误" }

& $Python src\AoE4_Overlay.py
```

测试应全部通过，Qt 集成检查不应因缺少依赖而跳过。启动程序后检查：

- Settings、Games、Build orders、Randomize、Override 五个页面可以打开。
- 在 **Settings → Language / 语言** 中选择**简体中文**。
- 关闭程序并重新运行，确认中文界面生效；切换回英文同样需要重启。
- 文明、地图名称保持原样，随机选择页面的图片正常显示。
- 已保存的建造顺序内容保持原文。

检查完成后关闭程序，再进行构建。中文支持不会改动悬浮窗与 OBS 输出。

## 5. 执行 Nuitka 构建

每次使用新的构建目录，避免混入旧产物。这里直接运行 Nuitka，暂不使用
仓库现有的 `compile.py`；以下命令使用现行参数，并在构建失败时停止打包。

```powershell
$BuildStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BuildDir = "build-win-$BuildStamp"

New-Item -ItemType Directory -Path $BuildDir | Out-Null

& $Python -m pip freeze |
    Set-Content "$BuildDir\build-environment.txt" -Encoding UTF8

$BuildArgs = @(
    "-m"
    "nuitka"
    "--standalone"
    "--enable-plugin=pyqt5"
    "--include-qt-plugins=sensible,imageformats"
    "--msvc=latest"
    "--windows-console-mode=disable"
    "--windows-icon-from-ico=src/img/aoe4_sword_shield.ico"
    "--include-data-dir=src/img=img"
    "--include-data-dir=src/html=html"
    "--noinclude-data-files=html/custom.css"
    "--noinclude-data-files=html/custom.js"
    "--output-filename=AoE4_Overlay.exe"
    "--output-dir=$BuildDir"
    "--report=$BuildDir/compilation-report.xml"
    "src/AoE4_Overlay.py"
)

& $Python @BuildArgs
if ($LASTEXITCODE -ne 0) { throw "Nuitka 构建失败，不执行 ZIP 打包" }
```

`--standalone` 生成包含依赖的目录；`--windows-console-mode=disable` 隐藏
控制台窗口；资源参数递归包含图片和网页文件。Qt 插件包含平台插件和图片
格式插件，以支持 Windows 界面及 WebP 图片。用户自定义的 `custom.css` 和
`custom.js` 不随包分发，由程序在运行时创建缺失的文件。

参考：[Nuitka 参数说明](https://nuitka.net/user-documentation/user-manual.html)。

预期输出：

```text
build-win-时间戳\
├── AoE4_Overlay.dist\
│   ├── AoE4_Overlay.exe
│   ├── img\
│   ├── html\
│   └── ……运行库与插件
├── build-environment.txt
└── compilation-report.xml
```

## 6. 检查产物并试运行

```powershell
$DistDir = Join-Path $BuildDir "AoE4_Overlay.dist"
$ExePath = Join-Path $DistDir "AoE4_Overlay.exe"

if (-not (Test-Path $ExePath)) { throw "未找到可执行文件" }
if (-not (Test-Path "$DistDir\img\build_order")) { throw "缺少建造顺序图片" }
if (-not (Test-Path "$DistDir\html\overlay.html")) { throw "缺少网页资源" }

$PlatformPlugin = Get-ChildItem $DistDir -Recurse -Filter qwindows.dll
$WebpPlugin = Get-ChildItem $DistDir -Recurse -Filter qwebp.dll

if (-not $PlatformPlugin) { throw "缺少 Qt Windows 平台插件" }
if (-not $WebpPlugin) { throw "缺少 Qt WebP 图片插件" }

$PlatformPlugin
$WebpPlugin

Start-Process -FilePath $ExePath
```

重复第 4 步的界面检查。程序会沿用当前用户已有配置；如果之前已选过中文，
构建后的程序也会显示中文。未配置语言的新用户默认使用英文。

若程序立即退出，可检查日志：

```powershell
Get-Content "$env:LOCALAPPDATA\AoE4_Overlay\overlay.log" -Tail 80
```

配置与日志位于用户数据目录，不在构建产物内，不需要随 ZIP 分发。

## 7. 制作 ZIP

关闭构建出的程序后执行：

```powershell
$ReleaseDir = Join-Path "release" $BuildStamp
$PackageDir = Join-Path $ReleaseDir "AoE4_Overlay"

New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null

Copy-Item -Path "$DistDir\*" -Destination $PackageDir -Recurse -ErrorAction Stop
Copy-Item -Path LICENSE -Destination "$PackageDir\LICENSE.txt" -ErrorAction Stop

$ZipPath = Join-Path $ReleaseDir "AoE4_Overlay.zip"

Compress-Archive -Path $PackageDir -DestinationPath $ZipPath -ErrorAction Stop

Get-Item $ZipPath
Get-FileHash $ZipPath -Algorithm SHA256
```

最终交付文件：

```text
C:\Build\AoE4_Overlay\release\时间戳\AoE4_Overlay.zip
```

解压后保留整个 `AoE4_Overlay` 文件夹，再运行其中的 EXE；不能只分发单独
的 EXE。最好在另一台未安装 Python 的 Windows 上再次验证解压后的程序。
保留本次构建目录中的依赖记录和编译报告。

## 出错时收集的信息

如果遇到错误，保留以下内容用于定位：

- 失败的步骤和完整终端报错。
- `py -3.11 --version`、`& $Python -m nuitka --version` 的输出。
- 本次构建目录中的 `build-environment.txt` 和 `compilation-report.xml`
  （若失败发生在报告生成前，报告可能不存在）。
- 程序启动异常时的 `overlay.log` 最后 80 行。

找不到 MSVC 时，检查 C++ 工作负载是否安装，并重新打开 Developer
PowerShell。图片缺失时，核对第 5 步资源参数及第 6 步的 Qt 插件检查。
