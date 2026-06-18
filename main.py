import asyncio
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QAbstractItemView,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
APP_NAME = "Heart Rate Band Logger"
AUTO_SCAN_INTERVAL_MS = 5000
AUTO_SCAN_TIMEOUT_SECONDS = 1.2

BAND_KEYWORDS = (
    "band",
    "xiaomi",
    "mi smart",
    "mi band",
    "redmi",
    "huawei",
    "honor",
    "amazfit",
    "zepp",
    "fitbit",
    "garmin",
    "polar",
    "coros",
    "whoop",
    "watch",
    "bracelet",
    "手环",
    "小米",
    "华为",
    "荣耀",
)


@dataclass
class ScanResult:
    name: str
    address: str
    rssi: int
    score: int
    services: str
    device: BLEDevice


def normalize_uuid(uuid: str) -> str:
    return uuid.lower()


def score_device(name: str, rssi: Optional[int], service_uuids: list[str]) -> int:
    text = (name or "").lower()
    score = 0
    if any(keyword in text for keyword in BAND_KEYWORDS):
        score += 70
    if normalize_uuid(HR_SERVICE_UUID) in [normalize_uuid(uuid) for uuid in service_uuids]:
        score += 100
    if rssi is not None:
        if rssi >= -55:
            score += 20
        elif rssi >= -70:
            score += 10
        elif rssi < -90:
            score -= 10
    return score


def parse_heart_rate(data: bytearray) -> int:
    if not data or len(data) < 2:
        raise ValueError("心率数据包为空或格式不完整")
    flags = data[0]
    if flags & 0x01:
        if len(data) < 3:
            raise ValueError("16 位心率数据包长度不足")
        return int.from_bytes(data[1:3], byteorder="little")
    return int(data[1])


def safe_write_text(path: str, text: str) -> None:
    folder = os.path.dirname(os.path.abspath(path))
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
        file.flush()


def default_output_file() -> str:
    documents = Path.home() / "Documents"
    if documents.exists():
        return str(documents / "heart_rate_log.txt")
    return str(Path.home() / "heart_rate_log.txt")


class ScanWorker(QObject):
    found = Signal(object)
    results_ready = Signal(object)
    status = Signal(str)
    finished = Signal()
    failed = Signal(str)

    def __init__(self, timeout: float):
        super().__init__()
        self.timeout = timeout

    def run(self) -> None:
        try:
            asyncio.run(self._scan())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()

    async def _scan(self) -> None:
        self.status.emit("正在扫描附近蓝牙设备...")
        discovered = await BleakScanner.discover(
            timeout=float(self.timeout),
            return_adv=True,
        )
        results: list[ScanResult] = []
        for item in discovered.values():
            if isinstance(item, tuple):
                device, adv_data = item
            else:
                device, adv_data = item, None
            adv_name = getattr(adv_data, "local_name", None)
            name = device.name or adv_name or "未命名设备"
            if adv_data is not None and adv_data.local_name:
                name = device.name or adv_data.local_name
            service_uuids = list(getattr(adv_data, "service_uuids", None) or [])
            rssi = getattr(adv_data, "rssi", None)
            if rssi is None:
                rssi = getattr(device, "rssi", None)
            if rssi is None:
                rssi = -100
            score = score_device(name, rssi, service_uuids)
            services = ", ".join(service_uuids)
            results.append(
                ScanResult(
                    name=name,
                    address=device.address,
                    rssi=int(rssi),
                    score=score,
                    services=services,
                    device=device,
                )
            )

        results.sort(key=lambda item: (item.score, item.rssi), reverse=True)
        self.results_ready.emit(results)
        self.status.emit(f"扫描完成，找到 {len(results)} 个设备。")


class HeartRateWorker(QObject):
    status = Signal(str)
    heart_rate = Signal(int, str)
    failed = Signal(str)
    disconnected = Signal()

    def __init__(
        self,
        device: BLEDevice,
        output_file: str,
        prefix: str,
        suffix: str,
    ):
        super().__init__()
        self.device = device
        self.output_file = output_file
        self.prefix = prefix
        self.suffix = suffix
        self._stop_requested = False
        self._client: Optional[BleakClient] = None

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        try:
            asyncio.run(self._connect_and_listen())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.disconnected.emit()

    async def _connect_and_listen(self) -> None:
        self.status.emit(f"正在连接 {self.device.name or self.device.address}...")
        async with BleakClient(self.device) as client:
            self._client = client
            if not client.is_connected:
                raise RuntimeError("连接失败")

            self.status.emit("连接成功，正在订阅心率数据...")
            await client.start_notify(HR_MEASUREMENT_UUID, self._handle_notify)
            self.status.emit("开始记录心率。")

            while not self._stop_requested and client.is_connected:
                await asyncio.sleep(0.2)

            try:
                await client.stop_notify(HR_MEASUREMENT_UUID)
            except Exception:
                pass
            self.status.emit("已停止记录。")

    def _handle_notify(self, _sender, data: bytearray) -> None:
        try:
            hr = parse_heart_rate(data)
            body = f"{hr}"
            line = f"{self.prefix}{body}{self.suffix}\n"
            safe_write_text(self.output_file, line)
            self.heart_rate.emit(hr, line.rstrip("\n"))
        except Exception as exc:
            self.failed.emit(f"心率数据解析失败: {exc}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Heart Rate Band Logger")
        self.resize(1080, 720)
        self.scan_thread: Optional[QThread] = None
        self.scan_worker: Optional[ScanWorker] = None
        self.hr_thread: Optional[QThread] = None
        self.hr_worker: Optional[HeartRateWorker] = None
        self.results: list[ScanResult] = []
        self.last_hr: Optional[int] = None
        self.auto_scan_paused = False
        self._build_ui()
        self._apply_style()

        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._update_connection_badge)
        self.pulse_timer.start(1000)

        self.auto_scan_timer = QTimer(self)
        self.auto_scan_timer.timeout.connect(self.start_scan)
        self.auto_scan_timer.start(AUTO_SCAN_INTERVAL_MS)
        QTimer.singleShot(100, self.start_scan)

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(14)

        title_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("智能手环心率记录器")
        title.setObjectName("Title")
        subtitle = QLabel("搜索 BLE 设备，连接标准心率服务，并将数据写入文本文件")
        subtitle.setObjectName("Subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.badge = QLabel("未连接")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setObjectName("Badge")
        title_row.addLayout(title_box)
        title_row.addStretch(1)
        title_row.addWidget(self.badge)
        layout.addLayout(title_row)

        top = QHBoxLayout()
        top.setSpacing(14)
        top.addWidget(self._create_scan_panel(), 2)
        top.addWidget(self._create_output_panel(), 1)
        layout.addLayout(top, 2)

        bottom = QHBoxLayout()
        bottom.setSpacing(14)
        bottom.addWidget(self._create_live_panel(), 1)
        bottom.addWidget(self._create_log_panel(), 2)
        layout.addLayout(bottom, 1)

    def _create_scan_panel(self) -> QWidget:
        group = QGroupBox("附近设备")
        layout = QVBoxLayout(group)
        control = QHBoxLayout()

        self.scan_btn = QPushButton("立即扫描")
        self.scan_btn.clicked.connect(self.start_scan)
        self.auto_scan_btn = QPushButton("暂停自动刷新")
        self.auto_scan_btn.clicked.connect(self.toggle_auto_scan)
        self.connect_btn = QPushButton("连接并记录")
        self.connect_btn.setEnabled(False)
        self.connect_btn.clicked.connect(self.start_recording)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_recording)

        control.addWidget(QLabel("自动刷新：每 5 秒"))
        control.addStretch(1)
        control.addWidget(self.scan_btn)
        control.addWidget(self.auto_scan_btn)
        control.addWidget(self.connect_btn)
        control.addWidget(self.stop_btn)
        layout.addLayout(control)

        notice = QLabel("请先在手环或手表中打开心率广播功能，再选择设备连接。")
        notice.setObjectName("Notice")
        layout.addWidget(notice)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["推荐", "名称", "地址"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        return group

    def _create_output_panel(self) -> QWidget:
        group = QGroupBox("输出设置")
        layout = QGridLayout(group)
        layout.setColumnStretch(1, 1)

        self.file_edit = QLineEdit(default_output_file())
        browse_btn = QPushButton("选择")
        browse_btn.clicked.connect(self.choose_output_file)
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_edit)
        file_row.addWidget(browse_btn)

        self.prefix_edit = QLineEdit("")
        self.prefix_edit.setPlaceholderText("例如 HR=")
        self.suffix_edit = QLineEdit("")
        self.suffix_edit.setPlaceholderText("例如 ;")

        layout.addWidget(QLabel("文本文件"), 0, 0)
        layout.addLayout(file_row, 0, 1)
        layout.addWidget(QLabel("前缀"), 1, 0)
        layout.addWidget(self.prefix_edit, 1, 1)
        layout.addWidget(QLabel("后缀"), 2, 0)
        layout.addWidget(self.suffix_edit, 2, 1)

        self.preview_label = QLabel()
        self.preview_label.setObjectName("Preview")
        layout.addWidget(QLabel("预览"), 3, 0)
        layout.addWidget(self.preview_label, 3, 1)

        self.prefix_edit.textChanged.connect(self.update_preview)
        self.suffix_edit.textChanged.connect(self.update_preview)
        self.update_preview()
        return group

    def _create_live_panel(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("LivePanel")
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel("实时心率")
        label.setObjectName("LiveLabel")
        self.hr_value = QLabel("--")
        self.hr_value.setObjectName("HeartRate")
        unit = QLabel("bpm")
        unit.setObjectName("Unit")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hr_value, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(unit, alignment=Qt.AlignmentFlag.AlignCenter)
        return frame

    def _create_log_panel(self) -> QWidget:
        group = QGroupBox("运行日志")
        layout = QVBoxLayout(group)
        self.status_label = QLabel("准备就绪。")
        self.status_label.setObjectName("Status")
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log)
        return group

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f5f7fb;
                color: #172033;
                font-size: 14px;
            }
            #Title {
                font-size: 28px;
                font-weight: 750;
            }
            #Subtitle, #Notice {
                color: #657085;
            }
            #Notice {
                background: #fff7ed;
                border: 1px solid #fed7aa;
                border-radius: 6px;
                color: #9a3412;
                padding: 8px 10px;
            }
            QGroupBox, #LivePanel {
                background: #ffffff;
                border: 1px solid #dce2ee;
                border-radius: 8px;
                margin-top: 12px;
                padding: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #3c465a;
                font-weight: 650;
            }
            QPushButton {
                background: #1463ff;
                color: white;
                border: 0;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 650;
            }
            QPushButton:hover {
                background: #0f55de;
            }
            QPushButton:disabled {
                background: #c6cedc;
            }
            QLineEdit, QTextEdit, QTableWidget {
                background: #ffffff;
                border: 1px solid #cfd7e6;
                border-radius: 6px;
                padding: 7px;
                selection-background-color: #1f6fff;
                selection-color: #ffffff;
            }
            QTableWidget {
                gridline-color: #edf1f7;
                alternate-background-color: #f8fafd;
                outline: 0;
            }
            QTableWidget::item {
                padding: 5px;
                border: 0;
            }
            QTableWidget::item:selected {
                background: #1f6fff;
                color: #ffffff;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #f3f6fb;
                border: 0;
                margin: 0;
                width: 10px;
                height: 10px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #b8c3d6;
                border-radius: 5px;
                min-height: 28px;
                min-width: 28px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #8fa0b8;
            }
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::add-page, QScrollBar::sub-page {
                border: 0;
                background: transparent;
                width: 0;
                height: 0;
            }
            QHeaderView::section {
                background: #eef3fb;
                border: 0;
                border-bottom: 1px solid #dce2ee;
                padding: 8px;
                font-weight: 650;
            }
            #Badge {
                min-width: 92px;
                border-radius: 14px;
                padding: 6px 12px;
                background: #e9edf5;
                color: #4d596d;
                font-weight: 700;
            }
            #LivePanel {
                background: #ffffff;
                border-left: 5px solid #22c55e;
            }
            #LiveLabel {
                color: #657085;
                font-size: 16px;
            }
            #HeartRate {
                color: #16a34a;
                font-size: 76px;
                font-weight: 800;
            }
            #Unit {
                color: #657085;
                font-size: 22px;
                font-weight: 650;
            }
            #Preview {
                background: #f0f4fb;
                border: 1px solid #dce2ee;
                border-radius: 6px;
                padding: 10px;
                color: #273244;
                font-family: Menlo, Consolas, monospace;
            }
            #Status {
                color: #3c465a;
                font-weight: 650;
            }
            """
        )

    def update_preview(self) -> None:
        self.preview_label.setText(f"{self.prefix_edit.text()}72{self.suffix_edit.text()}")

    def choose_output_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "选择输出文本文件",
            self.file_edit.text(),
            "Text Files (*.txt);;All Files (*)",
        )
        if path:
            self.file_edit.setText(path)

    def start_scan(self) -> None:
        if self._is_recording():
            return
        if self._thread_is_running(self.scan_thread):
            return
        self.scan_btn.setEnabled(False)
        self.connect_btn.setEnabled(False)
        self._set_status("准备扫描...")

        self.scan_thread = QThread(self)
        self.scan_worker = ScanWorker(AUTO_SCAN_TIMEOUT_SECONDS)
        self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.results_ready.connect(self._replace_scan_results)
        self.scan_worker.status.connect(self._set_status)
        self.scan_worker.failed.connect(self._show_error)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.finished.connect(self.scan_worker.deleteLater)
        self.scan_thread.finished.connect(self.scan_thread.deleteLater)
        self.scan_thread.finished.connect(self._on_scan_finished)
        self.scan_thread.start()

    def toggle_auto_scan(self) -> None:
        if self._is_recording():
            return
        self.auto_scan_paused = not self.auto_scan_paused
        if self.auto_scan_paused:
            self.auto_scan_timer.stop()
            self.auto_scan_btn.setText("恢复自动刷新")
            self._set_status("已暂停自动刷新。")
        else:
            self.auto_scan_timer.start(AUTO_SCAN_INTERVAL_MS)
            self.auto_scan_btn.setText("暂停自动刷新")
            self._set_status("已恢复自动刷新。")
            self.start_scan()

    def _on_scan_finished(self) -> None:
        self.scan_btn.setEnabled(not self._is_recording())
        self.scan_thread = None
        self.scan_worker = None
        self._selection_changed()

    def _replace_scan_results(self, results: list[ScanResult]) -> None:
        previous = self.selected_result()
        previous_address = previous.address if previous else ""
        self.results.clear()
        self.table.setRowCount(0)
        for result in results:
            self._add_scan_result(result)
        if previous_address:
            self._select_address(previous_address)
        elif self.table.rowCount():
            self.table.selectRow(0)

    def _add_scan_result(self, result: ScanResult) -> None:
        self.results.append(result)
        row = self.table.rowCount()
        self.table.insertRow(row)
        recommendation = "高" if result.score >= 100 else "中" if result.score >= 70 else "低"
        values = [
            f"{recommendation} ({result.score})",
            result.name,
            result.address,
        ]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            if column == 0:
                if result.score >= 100:
                    item.setBackground(QColor("#dcfce7"))
                elif result.score >= 70:
                    item.setBackground(QColor("#fef9c3"))
            self.table.setItem(row, column, item)

    def _select_address(self, address: str) -> None:
        for row, result in enumerate(self.results):
            if result.address == address:
                self.table.selectRow(row)
                return
        if self.table.rowCount():
            self.table.selectRow(0)

    def _selection_changed(self) -> None:
        self.connect_btn.setEnabled(bool(self.table.selectionModel().selectedRows()) and not self._is_recording())

    def selected_result(self) -> Optional[ScanResult]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        if 0 <= row < len(self.results):
            return self.results[row]
        return None

    def start_recording(self) -> None:
        result = self.selected_result()
        if not result:
            QMessageBox.information(self, "请选择设备", "请先扫描并选择一个蓝牙设备。")
            return
        output_file = self.file_edit.text().strip()
        if not output_file:
            QMessageBox.warning(self, "输出文件为空", "请选择或填写一个文本输出文件。")
            return

        self.auto_scan_timer.stop()
        self.last_hr = None
        self.hr_thread = QThread(self)
        self.hr_worker = HeartRateWorker(
            result.device,
            output_file,
            self.prefix_edit.text(),
            self.suffix_edit.text(),
        )
        self.hr_worker.moveToThread(self.hr_thread)
        self.hr_thread.started.connect(self.hr_worker.run)
        self.hr_worker.status.connect(self._set_status)
        self.hr_worker.heart_rate.connect(self._on_heart_rate)
        self.hr_worker.failed.connect(self._show_error)
        self.hr_worker.disconnected.connect(self._on_disconnected)
        self.hr_worker.disconnected.connect(self.hr_thread.quit)
        self.hr_worker.disconnected.connect(self.hr_worker.deleteLater)
        self.hr_thread.finished.connect(self.hr_thread.deleteLater)

        self.connect_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.auto_scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.badge.setText("连接中")
        self.badge.setStyleSheet("background:#fff7cc;color:#775f00;")
        self.hr_thread.start()

    def stop_recording(self) -> None:
        if self.hr_worker:
            self.hr_worker.stop()
            self._set_status("正在停止记录...")
        self.stop_btn.setEnabled(False)

    def _on_heart_rate(self, value: int, line: str) -> None:
        self.last_hr = value
        self.hr_value.setText(str(value))
        self._append_log(line)
        self.badge.setText("记录中")
        self.badge.setStyleSheet("background:#dcfce7;color:#166534;")

    def _on_disconnected(self) -> None:
        self.stop_btn.setEnabled(False)
        self.scan_btn.setEnabled(True)
        self.auto_scan_btn.setEnabled(True)
        self.connect_btn.setEnabled(bool(self.table.selectionModel().selectedRows()))
        self.badge.setText("未连接")
        self.badge.setStyleSheet("")
        self.hr_worker = None
        self.hr_thread = None
        if not self.auto_scan_paused and not self.auto_scan_timer.isActive():
            self.auto_scan_timer.start(AUTO_SCAN_INTERVAL_MS)

    def _update_connection_badge(self) -> None:
        if self._is_recording() and self.last_hr is None:
            self.badge.setText("等待数据")

    def _is_recording(self) -> bool:
        return self._thread_is_running(self.hr_thread)

    def _thread_is_running(self, thread: Optional[QThread]) -> bool:
        if not thread:
            return False
        try:
            return thread.isRunning()
        except RuntimeError:
            return False

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)
        self._append_log(text)

    def _append_log(self, text: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        self.log.append(f"[{stamp}] {text}")

    def _show_error(self, text: str) -> None:
        self._append_log(f"错误: {text}")
        if "not found" in text.lower() or "uuid" in text.lower():
            self._append_log("提示: 请确认手环已开启心率广播/第三方设备连接。")

    def closeEvent(self, event) -> None:
        self.auto_scan_timer.stop()
        self.stop_recording()
        if self._thread_is_running(self.hr_thread):
            self.hr_thread.quit()
            self.hr_thread.wait(2000)
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    font = QFont()
    font.setFamilies(["Inter", "Segoe UI", "PingFang SC", "Microsoft YaHei", "Arial"])
    app.setFont(font)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
