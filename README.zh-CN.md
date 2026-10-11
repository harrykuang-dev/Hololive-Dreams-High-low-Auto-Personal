# Hololive Dreams — 自动猜高低

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Windows 自动猜高低程序，提供 1.0.1 原版与三阶段策略。界面支持英文、繁体中文、日文、韩文、印尼语与简体中文。

## 下载与运行

从[最新版本](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal/releases/latest)下载 **HololiveDreamsHighLowAuto.exe** 后运行。模板、OCR 模型及必要资源包含在单一可执行文件中，启动时临时解压。

1. 打开游戏的猜高低画面。
2. 选择策略；默认为原版策略。
3. 按 **F8** 开始、**INSERT** 停止，或使用界面按钮。

点击快捷键栏位，按下按键或 Ctrl / Alt / Shift 组合即可修改。**Esc** 取消录制。开始与停止快捷键不能相同；Num Lock 不会加入 Alt 修饰键。

## 记录与净利

今日代币显示已确认的入账总额。净利为 **确认入账 − 50 ×（胜局 + 败局）**。每个成功结算的胜局也须扣除 50 代币投入；此扣除只修正净利显示，入账金额与策略决策维持原有规则。

`daily_coins.json` 保存当日入账、局数及三阶段进度；`settings.json` 保存语言、策略及快捷键。升级前停止程序，保留这两个文件并放在新 EXE 同级目录。

旧版当日记录若缺少胜局次数，保留已有入账并将净利显示为无法确认，不估算过去投入；下一日期恢复完整统计。不保存日志或截图。

## 从源码运行与打包

```powershell
python -m pip install -r requirements.txt pyinstaller
python main_ui.py
python -m PyInstaller --noconfirm "Hololive Dreams-Auto.spec"
```

输出：`dist/HololiveDreamsHighLowAuto.exe`。

## 文档与授权

[三阶段策略](THREE_STAGE.md#zh-cn) · [游戏用词](docs/GAME_TERMS.md) · [奖金 OCR](docs/OCR.md) · [v1.1.0 更新说明](docs/RELEASE-1.1.0.md) · [版本历史](HISTORY.md)

识牌与留牌策略来自 [hololive-dreams-helper](https://github.com/Oreki0504/hololive-dreams-helper)。其 [MIT 声明](licenses/poker-core-MIT.txt)和其他必要授权声明保留于 [licenses](licenses/)。
