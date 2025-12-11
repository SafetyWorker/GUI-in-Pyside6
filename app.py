from typing import Optional, Tuple, Dict, List
from PySide6.QtCore import Qt, QSize, QPoint, QTimer, Signal
from PySide6.QtGui import QAction, QPainter, QPixmap, QFont
from PySide6.QtGui import QIcon, QPainterPath, QColor, QPen
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QStatusBar, QToolBar, QMessageBox, QLabel, QPushButton,
    QLineEdit, QComboBox, QTabBar, QToolButton, QDialog, QScrollArea,
    QSizePolicy, QFrame, QTextBrowser
)
import sys

APP_NAME = "Application"

QSS_STYLE = """
QWidget { background: #ffffff; color: #000000; }
QLabel { color: #000000; font-size: 13px; }
QLineEdit, QComboBox, QPushButton, QToolButton { color: #000000; background: #ffffff; padding: 4px 10px; font-size: 13px; }
QLineEdit::placeholder { color: #777777; }
QLineEdit::selection { background: #cde6ff; color: #000000; }
QComboBox QAbstractItemView { color: #000000; background: #ffffff; }

/* Tabs & containers */
QTabBar::tab { color: #000000; border: 2px solid #000000; border-top-left-radius: 6px; border-top-right-radius: 6px; padding: 4px 10px; background: #ffffff; margin-right: 4px; }
QTabBar::tab:selected { color: #000000; background: #f2f2f2; }
QScrollArea { border: 2px solid #000000; border-radius: 8px; }
QStatusBar { background: #f0f0f0; }

/* Profiles strip box */
QFrame#ProfilesBox { border: 2px solid #000000; border-radius: 6px; background: #ffffff; padding: 6px; }
QLabel#ProfilesTitle { font-weight: 600; padding: 4px 8px; }

/* Help circle styling */
QToolButton#HelpCircle { border: 2px solid #000000; border-radius: 14px; min-width: 28px; min-height: 28px; padding: 0px; color: #000000; background: #ffffff; }

/* Card outline (outer row) */
#Card { border: 2px solid #000000; border-radius: 8px; }

/* The single joined outline around the four sections */
QFrame#FieldsGroup { border: 2px solid #000000; border-radius: 6px; padding: 8px; background: #ffffff; }

/* Vertical divider between Input type and Calibrate */
QFrame#VDivider { border-left: 2px solid #000000; min-width: 2px; }

/* Power toggle styling: keep white background; icon shows ON/OFF */
QToolButton#PowerToggle {
    border: 2px solid #000000; border-radius: 14px;
    min-width: 28px; min-height: 28px; padding: 0px; background: #ffffff;
}
QToolButton#PowerToggle:checked { background: #ffffff; }

/* Input pill */
QLineEdit#Pill { border: 2px solid #000000; border-radius: 12px; padding: 4px 12px; background: #ffffff; color: #000000; }

/* Buttons */
QPushButton { border: 2px solid #000000; border-radius: 6px; padding: 4px 8px; }
QPushButton#Play { font-weight: bold; min-height: 28px; min-width: 40px; }
QToolButton#Close { border: 2px solid #000000; border-radius: 6px; padding: 2px; min-height: 28px; min-width: 28px; color: #000000; }
QTextBrowser#Manual { border: 2px solid #000000; border-radius: 8px; padding: 10px; }
"""

# --- Helper: power icon ---
def make_power_icon(color: QColor, size: int = 24) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(color, 2))
    rect = pm.rect().adjusted(4, 4, -4, -4)
    path = QPainterPath()
    path.arcMoveTo(rect, 45)
    path.arcTo(rect, 45, 270)
    p.drawPath(path)
    cx = pm.width() // 2
    p.drawLine(cx, 6, cx, pm.height() // 2 - 2)
    p.end()
    return QIcon(pm)

# --- Key capture line edit for human-readable keys ---
class KeyCaptureLineEdit(QLineEdit):
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        parts = []
        if modifiers & Qt.ControlModifier: parts.append('ctrl')
        if modifiers & Qt.ShiftModifier: parts.append('shift')
        if modifiers & Qt.AltModifier: parts.append('alt')
        special = {
            Qt.Key_Space: 'space',
            Qt.Key_Tab: 'tab',
            Qt.Key_Return: 'enter',
            Qt.Key_Enter: 'enter',
            Qt.Key_Backspace: 'backspace',
            Qt.Key_Escape: 'esc',
            Qt.Key_Left: 'left',
            Qt.Key_Right: 'right',
            Qt.Key_Up: 'up',
            Qt.Key_Down: 'down',
        }
        if key in special:
            parts.append(special[key])
            self.setText('+'.join(parts))
            return
        text = event.text().strip()
        if text:
            parts.append(text.lower())
            self.setText('+'.join(parts))
            return
        super().keyPressEvent(event)

# --- EditableTabBar for double-click rename ---
class EditableTabBar(QTabBar):
    renameRequested = Signal(str, str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._editor: Optional[QLineEdit] = None
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._on_close)
    def _on_close(self, idx: int):
        if self.tabText(idx) == 'Default':
            QMessageBox.information(self, 'Info', 'Default profile cannot be closed.')
            return
        self.removeTab(idx)
    def mouseDoubleClickEvent(self, e):
        idx = self.tabAt(e.pos())
        if idx < 0: return super().mouseDoubleClickEvent(e)
        old = self.tabText(idx)
        if old == 'Default':
            QMessageBox.information(self, 'Info', 'Default profile cannot be renamed.')
            return
        r = self.tabRect(idx)
        if self._editor: self._editor.deleteLater()
        self._editor = QLineEdit(self); self._editor.setText(old); self._editor.setGeometry(r); self._editor.setFrame(False)
        self._editor.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._editor.setFocus(); self._editor.selectAll()
        self._editor.returnPressed.connect(lambda: self._finish(idx))
        self._editor.editingFinished.connect(lambda: self._finish(idx))
        self._editor.show()
    def _finish(self, idx: int):
        if not self._editor: return
        old = self.tabText(idx)
        new = (self._editor.text() or '').strip()
        self._editor.deleteLater(); self._editor = None
        if not new or new == old: return
        self.renameRequested.emit(old, new)

class KeyBindingManager:
    def __init__(self):
        self.name_to_key: Dict[str, str] = {}
        self.key_to_name: Dict[str, str] = {}
    def _normalize(self, seq_str: str) -> str:
        if not seq_str: return ''
        return '+'.join([p.strip().lower() for p in seq_str.split('+') if p.strip()])
    def can_assign(self, name: str, new_seq_str: str) -> Tuple[bool, Optional[str]]:
        norm = self._normalize(new_seq_str)
        if not norm: return True, None
        used_by = self.key_to_name.get(norm)
        if used_by is None or used_by == name: return True, None
        return False, used_by
    def assign(self, name: str, new_seq_str: str) -> bool:
        ok, _ = self.can_assign(name, new_seq_str)
        if not ok: return False
        old = self.name_to_key.get(name)
        if old:
            old_norm = self._normalize(old)
            if self.key_to_name.get(old_norm) == name:
                self.key_to_name.pop(old_norm, None)
        self.name_to_key[name] = new_seq_str
        norm = self._normalize(new_seq_str)
        if norm: self.key_to_name[norm] = name
        return True
    def remove_name(self, name: str):
        old = self.name_to_key.pop(name, None)
        if old:
            old_norm = self._normalize(old)
            if self.key_to_name.get(old_norm) == name:
                self.key_to_name.pop(old_norm, None)
    def rename(self, old_name: str, new_name: str):
        if old_name == new_name or not old_name: return
        seq = self.name_to_key.pop(old_name, '')
        if seq:
            norm = self._normalize(seq)
            if self.key_to_name.get(norm) == old_name:
                self.key_to_name[norm] = new_name
            self.name_to_key[new_name] = seq

class CameraWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._recording = False
        self._feed = QLabel(); self._feed.setAlignment(Qt.AlignCenter)
        pm = QPixmap(640, 480); pm.fill(Qt.white)
        painter = QPainter(pm); painter.setPen(Qt.black); painter.drawText(pm.rect(), Qt.AlignCenter, 'Camera Feed'); painter.end()
        self._feed.setPixmap(pm)
        self._dot = QLabel(self); self._dot.setFixedSize(18, 18); self._dot.setVisible(False)
        self._dot.setStyleSheet('background-color: red; border-radius: 14px; border: 2px solid black;')
        layout = QVBoxLayout(self); layout.setContentsMargins(8,8,8,8); layout.addWidget(self._feed)
    def setRecording(self, rec: bool):
        self._recording = rec
        self._dot.setVisible(rec)
        self._position_dot()
    def resizeEvent(self, e):
        super().resizeEvent(e); self._position_dot()
    def _position_dot(self):
        if not self._dot.isVisible(): return
        r = self._feed.geometry()
        self._dot.move(QPoint(r.right()-self._dot.width()-10, r.bottom()-self._dot.height()-10))

class CountdownDialog(QDialog):
    def __init__(self, seconds: int = 3, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Starting')
        self.setModal(True)
        self._remaining = max(1, int(seconds))
        v = QVBoxLayout(self)
        self.lbl = QLabel('', self); self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet('font-size: 22px; font-weight: 600;')
        v.addWidget(self.lbl)
        h = QHBoxLayout(); h.addStretch(1)
        btn_cancel = QToolButton(self); btn_cancel.setText('Cancel'); btn_cancel.clicked.connect(self.reject)
        h.addWidget(btn_cancel); v.addLayout(h)
        self.timer = QTimer(self); self.timer.setInterval(1000); self.timer.timeout.connect(self._tick)
        self._update_label(); self.timer.start()
    def _tick(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self.timer.stop(); self.accept(); return
        self._update_label()
    def _update_label(self):
        self.lbl.setText(f'Starts in {self._remaining}')

class ManualDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Instruction Manual')
        self.resize(700, 520)
        self.setModal(True)
        v = QVBoxLayout(self)
        txt = QTextBrowser(self)
        txt.setObjectName('Manual')
        txt.setOpenExternalLinks(True)
        txt.setReadOnly(True)
        txt.setHtml(self._manual_html())
        v.addWidget(txt)
        btn_row = QHBoxLayout(); btn_row.addStretch(1)
        btn_close = QToolButton(self); btn_close.setText('Close'); btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        v.addLayout(btn_row)
    def _manual_html(self) -> str:
        return (
            "<h2 style='margin-top:0'>Instruction Manual</h2>"
            "<p>This guide explains how to operate the application.</p>"
            "<h3>Profiles</h3>"
            "<ul>"
            "<li>Use the tabs to switch between profiles. The <b>Default</b> profile cannot be closed.</li>"
            "<li>Click the <b>+</b> beside PROFILES to add a new profile.</li>"
            "</ul>"
            "<h3>Add lines</h3>"
            "<ul>"
            "<li>Click the <b>+</b> button (under the tabs) to add a new line.</li>"
            "<li>Each line contains four boxed sections: <b>Name</b>, <b>Key Input</b>, <b>Input type</b>, and <b>Calibrate</b>.</li>"
            "</ul>"
            "<h3>Editing a line</h3>"
            "<ul>"
            "<li><b>Name</b>: type a label for the action.</li>"
            "<li><b>Key Input</b>: enter the key or combination (e.g., <code>w</code>, <code>space</code>, <code>ctrl+shift+a</code>). Duplicate keys across the same profile are not allowed.</li>"
            "<li><b>Input type</b>: choose <b>Click</b> or <b>Hold</b>.</li>"
            "<li><b>Calibrate</b>: press <b>Play</b> to start calibration with a short countdown.</li>"
            "<li><b>Delete</b>: use the <b>x</b> button at the far right of the line to remove it.</li>"
            "</ul>"
            "<h3>Camera & Calibration</h3>"
            "<ul>"
            "<li>Click <b>Camera</b> to open the camera window after a short countdown.</li>"
            "<li>Use the toolbar <b>Recording</b> toggle to start/stop recording in the calibration window.</li>"
            "</ul>"
            "<h3>Tips</h3>"
            "<ul>"
            "<li>All text inputs are single‑line for clean alignment.</li>"
            "<li>Key inputs are normalized (lowercased, trimmed) so <code>A</code> and <code>a</code> are treated the same.</li>"
            "<li>If you see a duplicate key warning, pick a different key to proceed.</li>"
            "</ul>"
        )

class KeyInputCard(QWidget):
    def __init__(self, name_text: str = 'Name', key_text: str = '', input_type: str = 'Click', parent=None):
        super().__init__(parent)
        self.setObjectName('Card')
        self.prev_name = name_text
        self.prev_key = key_text
        outer = QGridLayout(self); outer.setContentsMargins(12, 10, 12, 10); outer.setHorizontalSpacing(12); outer.setVerticalSpacing(8); outer.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.group = QFrame(self); self.group.setObjectName('FieldsGroup')
        g = QGridLayout(self.group); g.setContentsMargins(8, 8, 8, 8); g.setHorizontalSpacing(18); g.setVerticalSpacing(6)
        # Name
        self.edt_name = QLineEdit(); self.edt_name.setText(name_text); self.edt_name.setFixedHeight(28)
        lbl_name = QLabel('Name'); lbl_name.setAlignment(Qt.AlignLeft); g.addWidget(lbl_name, 0, 0, alignment=Qt.AlignLeft); g.addWidget(self.edt_name, 1, 0)
        # Key Input (captures keys as names)
        self.edt_key = KeyCaptureLineEdit(); self.edt_key.setText(key_text); self.edt_key.setObjectName('Pill'); self.edt_key.setFixedHeight(28)
        lbl_key = QLabel('Key Input'); lbl_key.setAlignment(Qt.AlignLeft); g.addWidget(lbl_key, 0, 1, alignment=Qt.AlignLeft); g.addWidget(self.edt_key, 1, 1)
        # Input type
        self.cmb_type = QComboBox(); self.cmb_type.addItems(['Click', 'Hold']); self.cmb_type.setCurrentIndex(0 if input_type == 'Click' else 1); self.cmb_type.setFixedHeight(28)
        lbl_type = QLabel('Input type'); lbl_type.setAlignment(Qt.AlignLeft); g.addWidget(lbl_type, 0, 2, alignment=Qt.AlignLeft); g.addWidget(self.cmb_type, 1, 2)
        # Divider
        vdiv = QFrame(); vdiv.setObjectName('VDivider'); vdiv.setFixedWidth(2); g.addWidget(vdiv, 0, 3, 2, 1)
        # Calibrate
        actions_row = QHBoxLayout(); actions_row.setSpacing(8); actions_row.setAlignment(Qt.AlignLeft)
        self.btn_play = QPushButton('\u25B6'); self.btn_play.setObjectName('Play'); self.btn_play.setFixedSize(48, 28); self.btn_play.setStyleSheet('font-size: 16px;'); self.btn_play.setCursor(Qt.PointingHandCursor); actions_row.addWidget(self.btn_play)
        act_container = QWidget(); act_container.setLayout(actions_row)
        lbl_cal = QLabel('Calibrate'); lbl_cal.setAlignment(Qt.AlignLeft); g.addWidget(lbl_cal, 0, 4, alignment=Qt.AlignLeft); g.addWidget(act_container, 1, 4)
        g.setColumnStretch(0, 1); g.setColumnStretch(1, 1); g.setColumnStretch(2, 1); g.setColumnStretch(4, 1)
        # Close
        self.btn_close = QToolButton(); self.btn_close.setText('x'); self.btn_close.setObjectName('Close'); self.btn_close.setFixedSize(28, 28)
        self.btn_close.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        outer.addWidget(self.group, 0, 0); outer.addWidget(self.btn_close, 0, 1, alignment=Qt.AlignVCenter); outer.setColumnStretch(0, 1)
        self.setMinimumHeight(120); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Signals
        self.edt_name.editingFinished.connect(self._on_name_changed)
        self.edt_key.editingFinished.connect(self._on_key_changed)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)
        self.btn_play.clicked.connect(self._on_calibrate)
        self.btn_close.clicked.connect(self._on_delete)
    def _current_profile(self) -> str:
        win = self.window()
        try:
            idx = win.profiles_bar.tabbar.currentIndex(); return win.profiles_bar.tabbar.tabText(idx)
        except Exception: return 'Default'
    def _normalize_key(self, s: str) -> str:
        return '+'.join([p.strip().lower() for p in s.split('+') if p.strip()])
    def _on_name_changed(self):
        win = self.window(); new_name = self.edt_name.text().strip(); old_name = self.prev_name.strip(); profile = self._current_profile()
        if not new_name: self.edt_name.setText(old_name); return
        if new_name != old_name:
            kbm = win.profile_kbm(profile); kbm.rename(old_name, new_name); win.update_card_model(self, profile, new_name=new_name); self.prev_name = new_name
    def _on_key_changed(self):
        win = self.window(); new_key_raw = self.edt_key.text().strip(); new_key_norm = self._normalize_key(new_key_raw); old_key = self.prev_key; profile = self._current_profile()
        for i in range(win.cards_layout.count()):
            other = win.cards_layout.itemAt(i).widget()
            if isinstance(other, KeyInputCard) and other is not self:
                other_key_norm = self._normalize_key(other.edt_key.text())
                if new_key_norm and other_key_norm and new_key_norm == other_key_norm:
                    QMessageBox.warning(self, 'Duplicate Key', ("The key '{}' is already used by another input in profile '{}'." "No two key inputs can be the same.").format(new_key_raw, profile)); self.edt_key.setText(old_key); return
        nm = self.edt_name.text().strip() or self.prev_name; kbm = win.profile_kbm(profile)
        if kbm.assign(nm, new_key_raw): win.update_card_model(self, profile, new_key=new_key_raw); self.prev_key = new_key_raw
        else:
            conflict_with = kbm.can_assign(nm, new_key_raw)[1]
            QMessageBox.warning(self, 'Duplicate Key', ("The key '{}' is already used by '{}' in profile '{}'." "No two key inputs can be the same.").format(new_key_raw, conflict_with or 'another', profile)); self.edt_key.setText(old_key)
    def _on_type_changed(self, idx: int):
        win = self.window(); profile = self._current_profile(); new_type = self.cmb_type.currentText(); win.update_card_model(self, profile, new_type=new_type)
    def _on_calibrate(self):
        dlg = CountdownDialog(seconds=3, parent=self); result = dlg.exec()
        if result == QDialog.Accepted:
            win = self.window();
            if hasattr(win, 'open_calibration_window'): win.open_calibration_window(start_recording=True)
            try: win.statusBar().showMessage('Calibration started', 1500)
            except Exception: pass
        else:
            try: self.window().statusBar().showMessage('Calibration cancelled', 1500)
            except Exception: pass
    def _on_delete(self):
        win = self.window(); profile = self._current_profile()
        try: win.profile_kbm(profile).remove_name(self.prev_name)
        except Exception: pass
        win.remove_card(self)

class ProfilesBar(QWidget):
    profileRenamed = Signal(str, str)
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self); v.setContentsMargins(8,8,8,8); v.setSpacing(6)
        self.box = QFrame(self); self.box.setObjectName('ProfilesBox')
        strip = QHBoxLayout(self.box); strip.setContentsMargins(8,6,8,6); strip.setSpacing(8)
        self.title = QLabel('PROFILES', self.box); self.title.setObjectName('ProfilesTitle'); strip.addWidget(self.title)
        self.btn_add_profile = QToolButton(self.box); self.btn_add_profile.setText('+'); self.btn_add_profile.setToolTip('Add Profile'); self.btn_add_profile.setFixedSize(28,28); self.btn_add_profile.setObjectName('Close'); strip.addWidget(self.btn_add_profile)
        self.tabbar = EditableTabBar(self.box); strip.addWidget(self.tabbar, 1)
        v.addWidget(self.box)
        actions = QHBoxLayout(); actions.setContentsMargins(0,0,0,0); actions.setSpacing(8)
        self.btn_power = QToolButton(self); self.btn_power.setObjectName('PowerToggle'); self.btn_power.setCheckable(True); self.btn_power.setToolTip('Toggle application on/off'); self.btn_power.setFixedSize(28, 28)
        self.btn_power.setIcon(make_power_icon(QColor(150, 150, 150))); self.btn_power.setIconSize(QSize(20, 20))
        actions.addWidget(self.btn_power, alignment=Qt.AlignVCenter)
        actions.addStretch(1)
        self.btn_add_line = QToolButton(self); self.btn_add_line.setText('+'); self.btn_add_line.setToolTip('Add line'); self.btn_add_line.setFixedSize(28,28); self.btn_add_line.setObjectName('Close')
        actions.addWidget(self.btn_add_line, alignment=Qt.AlignVCenter)
        self.btn_camera = QPushButton('Camera', self); self.btn_camera.setFixedHeight(28); self.btn_camera.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        actions.addWidget(self.btn_camera, alignment=Qt.AlignVCenter)
        self.btn_help = QToolButton(self); self.btn_help.setText('?'); self.btn_help.setObjectName('HelpCircle'); self.btn_help.setFixedSize(28,28)
        actions.addWidget(self.btn_help, alignment=Qt.AlignVCenter)
        v.addLayout(actions)
        # Start the counter based on existing extras so names remain sequential
        self._counter = max(1, self._extra_profile_count() + 1)
        self.btn_add_profile.clicked.connect(self._add_profile)
        self.tabbar.renameRequested.connect(self._on_tab_rename_requested)
        self._ensure_default(); self._add_profile()
    def _find_tab(self, text: str) -> int:
        for i in range(self.tabbar.count()):
            if self.tabbar.tabText(i) == text: return i
        return -1
    def _default_index(self) -> int: return self._find_tab('Default')
    def _ensure_default(self):
        if self._default_index() < 0: self.tabbar.addTab('Default')
    def _add_profile(self):
        self._ensure_default(); text = f'Profile #{self._counter}'; self._counter += 1
        idx_def = self._default_index(); insert_at = idx_def if idx_def >= 0 else self.tabbar.count()
        self.tabbar.insertTab(insert_at, text); self.tabbar.setCurrentIndex(self._find_tab(text))
    def _on_tab_rename_requested(self, old: str, new: str):
        if self._find_tab(new) >= 0:
            QMessageBox.warning(self, 'Duplicate name', f"A profile named '{new}' already exists.")
            return
        idx = self._find_tab(old)
        if idx < 0: return
        self.tabbar.setTabText(idx, new)
        self.profileRenamed.emit(old, new)

class CalibrationWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Calibration Window')
        self.cam = CameraWidget(); self.setCentralWidget(self.cam)
    def start_recording(self): self.cam.setRecording(True)
    def stop_recording(self): self.cam.setRecording(False)

class CameraWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Camera Window')
        self.cam = CameraWidget(); self.setCentralWidget(self.cam); self.cam.setRecording(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(APP_NAME); self.resize(1100, 700)
        QApplication.setFont(QFont('Segoe UI', 10))
        self.profiles_data: Dict[str, List[Dict[str, str]]] = {}
        self.profiles_kbm: Dict[str, KeyBindingManager] = {}
        central = QWidget(); v = QVBoxLayout(central); v.setContentsMargins(8,8,8,8); v.setSpacing(8)
        self.profiles_bar = ProfilesBar(); v.addWidget(self.profiles_bar)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        container = QWidget(); container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cards_layout = QVBoxLayout(container); self.cards_layout.setContentsMargins(8,8,8,8); self.cards_layout.setSpacing(12); self.cards_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.scroll.setWidget(container); v.addWidget(self.scroll, 1)
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar()); self.setStyleSheet(QSS_STYLE)
        self.cal_window = None; self.cam_window = None; self._init_toolbar()
        self.profiles_bar.btn_add_line.clicked.connect(self.add_new_card)
        self.profiles_bar.btn_camera.clicked.connect(self._on_camera_clicked)
        self.profiles_bar.btn_help.clicked.connect(self._on_help_clicked)
        self.profiles_bar.tabbar.currentChanged.connect(self._on_profile_changed)
        self.profiles_bar.profileRenamed.connect(self._on_profile_renamed)
        try: self.profiles_bar.btn_power.toggled.connect(self._on_power_toggled)
        except Exception: pass
        self._ensure_profile('Default'); self._ensure_profile('Profile #1')
        self.profiles_data['Default'] = [
            {'name': 'Name', 'key': 'w', 'type': 'Click'},
            {'name': 'Name', 'key': 'a', 'type': 'Click'},
            {'name': 'Name', 'key': 'space', 'type': 'Hold'},
        ]
        self._rebuild_kbm('Default'); self._load_profile('Default'); self.set_app_enabled(False)
    def _on_help_clicked(self): dlg = ManualDialog(self); dlg.exec()
    def _on_camera_clicked(self):
        dlg = CountdownDialog(seconds=3, parent=self); result = dlg.exec()
        if result == QDialog.Accepted:
            self.open_camera_window(); self.statusBar().showMessage('Camera opened', 1500)
        else: self.statusBar().showMessage('Camera cancelled', 1500)
    def _on_power_toggled(self, checked: bool):
        try:
            self.profiles_bar.btn_power.setIcon(make_power_icon(QColor(46, 204, 113) if checked else QColor(150,150,150)))
        except Exception: pass
        self.set_app_enabled(checked)
    def set_app_enabled(self, enabled: bool):
        self.app_enabled = bool(enabled)
        try: self.rec_act.setEnabled(enabled)
        except Exception: pass
        try: self.profiles_bar.btn_camera.setEnabled(enabled)
        except Exception: pass
        try:
            for i in range(self.cards_layout.count()):
                w = self.cards_layout.itemAt(i).widget()
                if w and hasattr(w, 'btn_play'): w.btn_play.setEnabled(enabled)
        except Exception: pass
        self.statusBar().showMessage('Application ' + ('ON' if enabled else 'OFF'), 1500)
    def _ensure_profile(self, name: str):
        if name not in self.profiles_data: self.profiles_data[name] = []
        if name not in self.profiles_kbm: self.profiles_kbm[name] = KeyBindingManager()
    def profile_kbm(self, name: str) -> KeyBindingManager: self._ensure_profile(name); return self.profiles_kbm[name]
    def _rebuild_kbm(self, name: str):
        kbm = self.profile_kbm(name); kbm.name_to_key.clear(); kbm.key_to_name.clear(); seen = set()
        for item in self.profiles_data.get(name, []):
            nm = item.get('name', ''); key = item.get('key', '')
            norm = kbm._normalize(key)
            if nm and key and norm not in seen: kbm.assign(nm, key); seen.add(norm)
    def _current_profile_name(self) -> str:
        idx = self.profiles_bar.tabbar.currentIndex(); return self.profiles_bar.tabbar.tabText(idx) if idx >= 0 else 'Default'
    def _on_profile_changed(self, idx: int):
        name = self.profiles_bar.tabbar.tabText(idx); self._ensure_profile(name); self._rebuild_kbm(name); self._load_profile(name); self.statusBar().showMessage(f'Switched to {name}', 1500)
    def _on_profile_renamed(self, old: str, new: str):
        self._ensure_profile(old)
        self.profiles_data[new] = self.profiles_data.pop(old, [])
        self.profiles_kbm[new] = self.profiles_kbm.pop(old, KeyBindingManager())
        if self._current_profile_name() == new:
            self._rebuild_kbm(new); self._load_profile(new)
        self.statusBar().showMessage(f"Profile '{old}' renamed to '{new}'", 1500)
    def _clear_cards(self):
        for i in reversed(range(self.cards_layout.count())):
            item = self.cards_layout.itemAt(i); w = item.widget()
            if w is not None: w.setParent(None); w.deleteLater()
            self.cards_layout.takeAt(i)
    def _load_profile(self, name: str):
        self._clear_cards()
        def _populate():
            for item in self.profiles_data.get(name, []):
                card = KeyInputCard(item.get('name', ''), item.get('key', ''), item.get('type', 'Click'))
                self.cards_layout.addWidget(card)
        QTimer.singleShot(0, _populate)
    def add_card(self, name_text: str, key_text: str, input_type: str):
        prof = self._current_profile_name(); self._ensure_profile(prof)
        kbm = self.profile_kbm(prof); ok, _ = kbm.can_assign(name_text or '', key_text)
        if key_text and not ok:
            QMessageBox.warning(self, 'Duplicate Key', ("The key '{}' is already used in profile '{}'." "No two key inputs can be the same.").format(key_text, prof)); key_text = ''
        self.profiles_data[prof].append({'name': name_text, 'key': key_text, 'type': input_type})
        if name_text and key_text: self.profile_kbm(prof).assign(name_text, key_text)
        card = KeyInputCard(name_text, key_text, input_type); self.cards_layout.addWidget(card)
    def add_new_card(self):
        self.add_card('Name', '', 'Click'); self.statusBar().showMessage(f"New line added to {self._current_profile_name()}", 1500)
    def update_card_model(self, card: KeyInputCard, profile: str, new_name: Optional[str] = None, new_key: Optional[str] = None, new_type: Optional[str] = None):
        items = self.profiles_data.get(profile, [])
        for it in items:
            if it.get('name') == card.prev_name and it.get('key') == card.prev_key:
                if new_name is not None: it['name'] = new_name
                if new_key is not None: it['key'] = new_key
                if new_type is not None: it['type'] = new_type
                break
        if new_name is not None: card.prev_name = new_name
        if new_key is not None: card.prev_key = new_key
    def remove_card(self, card: KeyInputCard):
        prof = self._current_profile_name(); items = self.profiles_data.get(prof, [])
        self.profiles_data[prof] = [it for it in items if not (it.get('name') == card.prev_name and it.get('key') == card.prev_key)]
        card.setParent(None); card.deleteLater()
    def open_calibration_window(self, start_recording: bool = False):
        if self.cal_window is None: self.cal_window = CalibrationWindow()
        self.cal_window.show(); self.cal_window.raise_();
        if start_recording: self.cal_window.start_recording()
    def open_camera_window(self):
        if self.cam_window is None: self.cam_window = CameraWindow()
        self.cam_window.show(); self.cam_window.raise_()
    def _init_toolbar(self):
        tb = QToolBar('Main Toolbar'); tb.setIconSize(QSize(16,16)); self.addToolBar(tb)
        self.rec_act = QAction('Recording', self); self.rec_act.setCheckable(True); self.rec_act.toggled.connect(self._toggle_recording)
        tb.addAction(self.rec_act)
    def _toggle_recording(self, checked: bool):
        if checked:
            dlg = CountdownDialog(seconds=3, parent=self); result = dlg.exec()
            if result == QDialog.Accepted:
                self.open_calibration_window(start_recording=True); self.statusBar().showMessage('Recording ON', 1500)
            else:
                self.rec_act.setChecked(False); self.statusBar().showMessage('Recording cancelled', 1500)
        else:
            if self.cal_window: self.cal_window.stop_recording()
            self.statusBar().showMessage('Recording OFF', 1500)

def main():
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
