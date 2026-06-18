# Heart Rate Band Logger

跨平台智能手环心率记录器。程序带桌面 GUI，可以搜索附近 BLE 设备，优先显示手环/心率设备，连接标准蓝牙心率服务，并把心率按自定义前缀、后缀输出到文本文件。

最终用户不需要安装 Python；发布时提供 Windows、macOS、Linux 三个平台的打包文件。

## 用户功能

- 双击运行的桌面 GUI
- 扫描附近蓝牙低功耗设备
- 根据名称、Heart Rate Service UUID 和 RSSI 给设备排序
- 连接并订阅标准 Heart Rate Measurement 特征值
- 自定义输出文件、前缀、后缀
- 可选时间戳输出
- 实时心率显示和运行日志

默认使用标准蓝牙心率服务：

- Heart Rate Service: `0000180d-0000-1000-8000-00805f9b34fb`
- Heart Rate Measurement: `00002a37-0000-1000-8000-00805f9b34fb`

## 发布包

推荐通过 GitHub Actions 构建三平台发布包。手动运行 `Build desktop releases` workflow 时会生成构建 artifact；推送 `v*` tag 时会自动创建 GitHub Release，并把三平台 zip 上传为 release assets。

- `HeartRateBandLogger-windows-*.zip`
- `HeartRateBandLogger-darwin-*.zip`
- `HeartRateBandLogger-linux-*.zip`

这些 zip 里包含可执行程序和运行时依赖，用户解压后双击运行。

发布一个正式版本：

```bash
git tag v0.1.0
git push origin v0.1.0
```

## 本地打包

开发者本机需要 Python 仅用于构建，不要求最终用户安装 Python。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build.py
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\build.py
```

构建产物位于 `dist/`。

## 开发运行

开发调试时可以直接运行源码：

```bash
python main.py
```

## 平台注意事项

- macOS: 首次运行时需要允许 App 使用蓝牙。打包配置已加入蓝牙权限说明，但正式分发最好再做 Apple Developer 签名和 notarization。
- Windows: 用户可能需要在系统设置中打开蓝牙；建议用压缩包或后续接入安装器发布。
- Linux: 依赖系统 BlueZ 蓝牙栈，用户账户可能需要蓝牙权限。不同发行版对 BLE 权限策略可能不同。

## 手环设置

很多手环默认不会持续广播标准心率数据。连接前请在官方 App 中开启类似“心率广播”“蓝牙心率广播”“第三方设备连接”的选项，必要时手动开始运动或心率测量。
