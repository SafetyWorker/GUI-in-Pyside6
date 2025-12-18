 
from typing import Optional, Tuple, Dict, List 
from PySide6.QtCore import Qt, QSize, QPoint, QTimer, Signal 
from PySide6.QtGui import QPainter, QPixmap, QFont, QIcon, QPainterPath, QColor, QPen 
from PySide6.QtWidgets import ( 
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QStatusBar, QMessageBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTabBar, QToolButton, QDialog, QScrollArea, 
    QSizePolicy, QFrame, QTextBrowser, QGraphicsDropShadowEffect 
) 
import re 
import sys 

APP_NAME = "Application" 

# ---------------- Appearance (QSS) ----------------
QSS_STYLE = """
/* Global */
QWidget { background: #2B2834; color: #ECECF2; }
/* Labels transparent to avoid any highlight */
QLabel { color: #E2E1ED; font-size: 13px; background: transparent; padding: 0px; }
QStatusBar { background: #2B2834; color: #CFCFE0; }

/* Top Profiles strip */
QFrame#ProfilesBox { border: none; background: #1F1C27; border-radius: 10px; }
QToolButton#HelpCircle, QToolButton#Close { border: 1px solid #6F6A7F; color: #ECECF2; background: #2B2834; border-radius: 8px; padding: 2px; }
QToolButton#HelpCircle:hover, QToolButton#Close:hover { background: #363246; }

/* Tabs as rounded pills */
QTabBar::tab { color: #ECECF2; padding: 6px 14px; background: #3B3746; border: 1px solid #5A5568; border-radius: 10px; margin-right: 6px; }
QTabBar::tab:selected { background: #4A4656; }
QTabBar::tab:hover { background: #454154; }
QTabBar { background: transparent; }
QScrollArea { border: none; }

/* Card group */
#Card { border: none; }
QFrame#FieldsGroup { border: none; padding: 12px; background: #3B3746; border-radius: 14px; }

/* Power toggle (top-right) */
QToolButton#PowerToggle {
  background: transparent;
  border: 2px solid #ECECF2;            /* light outline ring */
  color: #ECECF2;
  border-radius: 14px;                   /* circular */
  min-width: 28px; min-height: 28px;    /* compact */
  padding: 0px;
}
QToolButton#PowerToggle:hover { background: #332F3F; }
QToolButton#PowerToggle:checked { border-color: #2ECC71; color: #2ECC71; }

/* Inputs */
/* Input Type: plain black down arrow caret and clean drop-down area */
QComboBox { padding-right: 24px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: right; width: 18px; border: none; background: transparent; }
QComboBox::down-arrow { image: url(arrow_down_black.png); width: 10px; height: 6px; }
QComboBox::down-arrow:on { top: 1px; }

QLineEdit, QComboBox, QPushButton, QToolButton { color: #2B2834; background: #D9D6E3; padding: 4px 12px; font-size: 13px; border: 1px solid #B7B0C9; border-radius: 12px; }
QLineEdit#Pill { border: 1px solid #B7B0C9; border-radius: 12px; padding: 6px 12px; background: #D9D6E3; color: #2B2834; }
QLineEdit::placeholder { color: #7E7A8E; }
QLineEdit::selection { background: #CDE6FF; color: #2B2834; }
QComboBox QAbstractItemView { color: #2B2834; background: #D9D6E3; }

/* Buttons */
QPushButton { border: 1px solid #B7B0C9; border-radius: 12px; padding: 6px 12px; }
QToolButton#Close { min-height: 28px; min-width: 28px; }

/* Icon-only triangle recalibrate button */
QToolButton#CamButton {
  background: transparent;
  border: 2px solid #D39AA0; /* muted pink outline */
  color: #D39AA0;
  border-radius: 10px;
  padding: 2px;           /* small inset so icon doesn't clip */
}
QToolButton#CamButton:hover { background: #332F3F; }
QToolButton#CamButton:disabled { border-color: #8A8597; color: #8A8597; }

/* Manual */
QTextBrowser#Manual { border: 1px solid #6F6A7F; border-radius: 10px; padding: 10px; background: #2B2834; }

/* Tab bar close 'x' (plain glyph, no bubble) */
QTabBar QToolButton { background: transparent; border: none; padding: 0; color: #000; }
QTabBar QToolButton:hover { background: transparent; }
"""

# --- Helper: power icon (full ring + vertical stem) ---
def make_power_icon(color: QColor, size: int = 24) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    ring_rect = pm.rect().adjusted(4, 4, -4, -4)
    p.drawEllipse(ring_rect)
    cx = pm.width() // 2
    top_y = ring_rect.top() + 1
    stem_end_y = int(ring_rect.top() + ring_rect.height() * 0.42)
    p.drawLine(cx, top_y, cx, stem_end_y)
    p.end()
    return QIcon(pm)

# --- Helper: triangle play icon ---
def make_play_icon(color: QColor, size: int = 20) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(color, 2))
    p.setBrush(QColor(color))
    w, h = pm.width(), pm.height()
    path = QPainterPath()
    path.moveTo(int(w*0.30), int(h*0.20))
    path.lineTo(int(w*0.30), int(h*0.80))
    path.lineTo(int(w*0.80), int(h*0.50))
    path.closeSubpath()
    p.drawPath(path)
    p.end()
    return QIcon(pm)

# --- Key capture line edit ---
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

# --- EditableTabBar ---
class EditableTabBar(QTabBar):
    renameRequested = Signal(str, str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._editor: Optional[QLineEdit] = None
        self.setMouseTracking(True)
        self._hover_idx = -1
        self._close_on_hover_enabled = True
        self.setTabsClosable(False)
        self.setExpanding(False)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
    def setCloseOnHoverEnabled(self, enabled: bool):
        self._close_on_hover_enabled = bool(enabled)
        if not enabled:
            for i in range(self.count()):
                btn = self.tabButton(i, QTabBar.RightSide)
                if isinstance(btn, QToolButton):
                    btn.setVisible(False)
        self.update()
    def tabInserted(self, index: int):
        self._install_close_button(index)
    def _install_close_button(self, idx: int):
        btn = QToolButton(self)
        btn.setText('x')
        btn.setAutoRaise(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setVisible(False)
        btn.setToolTip('Close')
        btn.clicked.connect(self._on_close_button_clicked)
        self.setTabButton(idx, QTabBar.RightSide, btn)
    def _index_for_button(self, btn: QToolButton) -> int:
        for i in range(self.count()):
            if self.tabButton(i, QTabBar.RightSide) is btn:
                return i
        return -1
    def _on_close_button_clicked(self):
        btn = self.sender()
        if not isinstance(btn, QToolButton):
            return
        idx = self._index_for_button(btn)
        if idx < 0:
            return
        text = self.tabText(idx)
        if text == 'Default':
            QMessageBox.information(self, 'Info', 'Default profile cannot be closed.')
            return
        try:
            self.tabCloseRequested.emit(idx)
        except Exception:
            pass
        self.removeTab(idx)
        btn.deleteLater()
        self._update_close_visibility()
    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        idx = self.tabAt(e.pos())
        if idx != self._hover_idx:
            self._hover_idx = idx
            self._update_close_visibility()
    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._hover_idx = -1
        self._update_close_visibility()
    def _update_close_visibility(self):
        for i in range(self.count()):
            btn = self.tabButton(i, QTabBar.RightSide)
            if not isinstance(btn, QToolButton):
                continue
        
            show = (self._close_on_hover_enabled and i == self._hover_idx and self.tabText(i) != 'Default')
            btn.setVisible(show)
    def mouseDoubleClickEvent(self, e):
        idx = self.tabAt(e.pos())
        if idx < 0:
            return super().mouseDoubleClickEvent(e)
        old = self.tabText(idx)
        if old == 'Default':
            QMessageBox.information(self, 'Info', 'Default profile cannot be renamed.')
            return
        try:
            win = self.window()
            if hasattr(win, 'app_enabled') and not win.app_enabled:
                return
        except Exception:
            pass
        r = self.tabRect(idx)
        if self._editor: self._editor.deleteLater()
        self._editor = QLineEdit(self)
        self._editor.setText(old)
        self._editor.setGeometry(r)
        self._editor.setFrame(False)
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

# --- Key binding manager ---
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

# --- Camera widget & dialogs ---
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
        self.lbl.setStyleSheet('font-size: 22px; font-weight: 600; background: transparent;')
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
            "<li>The <b>Default</b> profile is fixed at the left and cannot be closed.</li>"
            "<li>Click the <b>+</b> next to the tabs to add a new profile on the right.</li>"
            "</ul>"
            "<h3>Add lines</h3>"
            "<ul>"
            "<li>Click the <b>+</b> button (under the tabs) to add a new line.</li>"
            "<li>Each line contains four sections: <b>Name</b>, <b>Key Input</b>, <b>Input type</b>, and <b>Calibrate</b>.</li>"
            "</ul>"
            "<h3>Editing a line</h3>"
            "<ul>"
            "<li><b>Name</b>: type a label for the action.</li>"
            "<li><b>Key Input</b>: enter the key or combination (e.g., <code>w</code>, <code>space</code>, <code>ctrl+shift+a</code>). Duplicate keys across the same profile are not allowed.</li>"
            "<li><b>Input type</b>: choose <b>Click</b> or <b>Hold</b>.</li>"
            "<li><b>Calibrate</b>: press the triangle button to start calibration with a short countdown.</li>"
            "<li><b>Delete</b>: use the <b>x</b> button at the far right of the line to remove it.</li>"
            "</ul>"
            "<h3>Camera & Calibration</h3>"
            "<ul>"
            "<li>Click <b>Camera</b> to open the camera window after a short countdown.</li>"
            "</ul>"
            "<h3>Tips</h3>"
            "<ul>"
            "<li>All text inputs are single-line for clean alignment.</li>"
            "<li>Key inputs are normalized (lowercased, trimmed).</li>"
            "<li>If you see a duplicate key warning, pick a different key.</li>"
            "</ul>"
        )

# --- KeyInputCard ---
class KeyInputCard(QWidget):
    def __init__(self, name_text: str = 'Name', key_text: str = '', input_type: str = 'Click', parent=None, modifiable: bool = True):
        super().__init__(parent)
        self.setObjectName('Card')
        self.prev_name = name_text
        self.prev_key = key_text
        self.modifiable = bool(modifiable)
        outer = QGridLayout(self); outer.setContentsMargins(12, 10, 12, 10)
        outer.setHorizontalSpacing(12); outer.setVerticalSpacing(8)
        outer.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.group = QFrame(self); self.group.setObjectName('FieldsGroup')
        g = QGridLayout(self.group); g.setContentsMargins(12, 12, 12, 12)
        g.setHorizontalSpacing(24); g.setVerticalSpacing(8)
        shadow = QGraphicsDropShadowEffect(self.group)
        shadow.setBlurRadius(18); shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.group.setGraphicsEffect(shadow)

        # Column 0: Name
        col0 = QVBoxLayout(); col0.setContentsMargins(0,0,0,0); col0.setSpacing(6); col0.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        lbl_name = QLabel('Name'); lbl_name.setAlignment(Qt.AlignHCenter); lbl_name.setStyleSheet('background: transparent;')
        self.edt_name = QLineEdit(); self.edt_name.setText(name_text); self.edt_name.setFixedHeight(32); self.edt_name.setFixedWidth(180); self.edt_name.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        col0.addWidget(lbl_name); col0.addWidget(self.edt_name, alignment=Qt.AlignHCenter)

        # Column 1: Key Input
        col1 = QVBoxLayout(); col1.setContentsMargins(0,0,0,0); col1.setSpacing(6); col1.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        lbl_key_title = QLabel('KEY INPUT'); lbl_key_title.setAlignment(Qt.AlignHCenter); lbl_key_title.setStyleSheet('background: transparent;')
        self.edt_key = KeyCaptureLineEdit(); self.edt_key.setText(key_text); self.edt_key.setObjectName('Pill'); self.edt_key.setFixedHeight(32); self.edt_key.setFixedWidth(140); self.edt_key.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        col1.addWidget(lbl_key_title); col1.addWidget(self.edt_key, alignment=Qt.AlignHCenter)

        # Column 2: Input Type
        col2 = QVBoxLayout(); col2.setContentsMargins(0,0,0,0); col2.setSpacing(6); col2.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        lbl_type_title = QLabel('INPUT TYPE'); lbl_type_title.setAlignment(Qt.AlignHCenter); lbl_type_title.setStyleSheet('background: transparent;')
        self.cmb_type = QComboBox(); self.cmb_type.addItems(['Click', 'Hold']); self.cmb_type.setCurrentIndex(0 if (input_type or 'Click').lower() == 'click' else 1); self.cmb_type.setFixedHeight(32); self.cmb_type.setFixedWidth(120); self.cmb_type.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        col2.addWidget(lbl_type_title); col2.addWidget(self.cmb_type, alignment=Qt.AlignHCenter)

        # Column 3: Recalibrate
        col3 = QVBoxLayout(); col3.setContentsMargins(0,0,0,0); col3.setSpacing(6); col3.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        lbl_cal_title = QLabel('RECALIBRATE'); lbl_cal_title.setAlignment(Qt.AlignHCenter); lbl_cal_title.setStyleSheet('background: transparent;')
        self.btn_cam = QToolButton(); self.btn_cam.setObjectName('CamButton'); self.btn_cam.setToolTip('Recalibrate'); self.btn_cam.setCursor(Qt.PointingHandCursor)
        self.btn_cam.setIcon(make_play_icon(QColor(211, 154, 160))); self.btn_cam.setIconSize(QSize(20, 20)); self.btn_cam.setFixedSize(44, 28)
        col3.addWidget(lbl_cal_title); col3.addWidget(self.btn_cam, alignment=Qt.AlignHCenter)

        # Place four equal-width columns (layouts)
        g.addLayout(col0, 0, 0, 2, 1)
        g.addLayout(col1, 0, 1, 2, 1)
        g.addLayout(col2, 0, 2, 2, 1)
        g.addLayout(col3, 0, 3, 2, 1)
        g.setColumnStretch(0, 1); g.setColumnStretch(1, 1); g.setColumnStretch(2, 1); g.setColumnStretch(3, 1)

        # Close button at far right of the card
        self.btn_close = QToolButton(); self.btn_close.setText('x'); self.btn_close.setObjectName('Close'); self.btn_close.setFixedSize(28, 28)
        self.btn_close.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        outer.addWidget(self.group, 0, 0)
        outer.addWidget(self.btn_close, 0, 1, alignment=Qt.AlignVCenter)
        outer.setColumnStretch(0, 1)

        self.setMinimumHeight(120); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Signals
        self.edt_name.editingFinished.connect(self._on_name_changed)
        self.edt_key.editingFinished.connect(self._on_key_changed)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)
        self.btn_cam.clicked.connect(self._on_calibrate)
        self.btn_close.clicked.connect(self._on_delete)

        self.set_modifiable(self.modifiable)

    def set_modifiable(self, can_edit: bool):
        self.modifiable = bool(can_edit)
        for w in (self.edt_name, self.edt_key, self.cmb_type, self.btn_close):
            w.setEnabled(can_edit)
    def _current_profile(self) -> str:
        win = self.window()
        try:
            idx = win.profiles_bar.tabbar.currentIndex(); return win.profiles_bar.tabbar.tabText(idx)
        except Exception: return 'Default'
    def _normalize_key(self, s: str) -> str:
        return '+'.join([p.strip().lower() for p in s.split('+') if p.strip()])
    def _on_name_changed(self):
        if not self.modifiable: return
        win = self.window(); new_name = self.edt_name.text().strip(); old_name = self.prev_name.strip(); profile = self._current_profile()
        if not new_name:
            self.edt_name.setText(old_name); return
        if new_name != old_name:
            kbm = win.profile_kbm(profile); kbm.rename(old_name, new_name)
            win.update_card_model(self, profile, new_name=new_name); self.prev_name = new_name
    def _on_key_changed(self):
        if not self.modifiable: return
        win = self.window(); new_key_raw = self.edt_key.text().strip(); new_key_norm = self._normalize_key(new_key_raw); old_key = self.prev_key; profile = self._current_profile()
        for i in range(win.cards_layout.count()):
            other = win.cards_layout.itemAt(i).widget()
            if isinstance(other, KeyInputCard) and other is not self:
                other_key_norm = self._normalize_key(other.edt_key.text())
                if new_key_norm and other_key_norm and new_key_norm == other_key_norm:
                    QMessageBox.warning(self, 'Duplicate Key', ("The key '{}' is already used by another input in profile '{}'." "No two key inputs can be the same.").format(new_key_raw, profile))
                    self.edt_key.setText(old_key); return
        nm = self.edt_name.text().strip() or self.prev_name; kbm = win.profile_kbm(profile)
        if kbm.assign(nm, new_key_raw):
            win.update_card_model(self, profile, new_key=new_key_raw); self.prev_key = new_key_raw
        else:
            conflict_with = kbm.can_assign(nm, new_key_raw)[1]
            QMessageBox.warning(self, 'Duplicate Key', ("The key '{}' is already used by '{}' in profile '{}'." "No two key inputs can be the same.").format(new_key_raw, conflict_with or 'another', profile))
            self.edt_key.setText(old_key)
    def _on_type_changed(self, idx: int):
        if not self.modifiable: return
        win = self.window(); profile = self._current_profile(); new_type = self.cmb_type.currentText()
        win.update_card_model(self, profile, new_type=new_type)
    def _on_calibrate(self):
        dlg = CountdownDialog(seconds=3, parent=self); result = dlg.exec()
        if result == QDialog.Accepted:
            win = self.window()
            if hasattr(win, 'open_calibration_window'): win.open_calibration_window(start_recording=True)
            try: win.statusBar().showMessage('Calibration started', 1500)
            except Exception: pass
        else:
            try: self.window().statusBar().showMessage('Calibration cancelled', 1500)
            except Exception: pass
    def _on_delete(self):
        if not self.modifiable: return
        win = self.window(); profile = self._current_profile()
        try: win.profile_kbm(profile).remove_name(self.prev_name)
        except Exception: pass
        win.remove_card(self)

# --- Profiles bar ---
class ProfilesBar(QWidget):
    profileRenamed = Signal(str, str)
    profileAdded = Signal(str)  # NEW: emitted when a new profile is created
    MAX_EXTRA_PROFILES = 4
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self); v.setContentsMargins(8,8,8,8); v.setSpacing(6)
        self.box = QFrame(self); self.box.setObjectName('ProfilesBox')
        strip = QHBoxLayout(self.box); strip.setContentsMargins(8,6,8,6); strip.setSpacing(8)
        self.tabbar = EditableTabBar(self.box)
        strip.addWidget(self.tabbar)
        self.btn_add_profile = QToolButton(self.box); self.btn_add_profile.setText('+'); self.btn_add_profile.setToolTip('Add Profile'); self.btn_add_profile.setFixedSize(28,28); self.btn_add_profile.setObjectName('Close')
        strip.addWidget(self.btn_add_profile)
        strip.addStretch(1)
        self.btn_power = QToolButton(self.box); self.btn_power.setObjectName('PowerToggle'); self.btn_power.setCheckable(True); self.btn_power.setToolTip('Toggle application on/off'); self.btn_power.setFixedSize(28, 28)
        self.btn_power.setIcon(make_power_icon(QColor(236, 236, 242)))
        self.btn_power.setIconSize(QSize(20, 20))
        strip.addWidget(self.btn_power, alignment=Qt.AlignRight | Qt.AlignVCenter)
        v.addWidget(self.box)

        actions = QHBoxLayout(); actions.setContentsMargins(0,0,0,0); actions.setSpacing(8)
        actions.addStretch(1)
        self.btn_add_line = QToolButton(self); self.btn_add_line.setText('+'); self.btn_add_line.setToolTip('Add line'); self.btn_add_line.setFixedSize(28,28); self.btn_add_line.setObjectName('Close')
        actions.addWidget(self.btn_add_line, alignment=Qt.AlignVCenter)
        self.btn_camera = QPushButton('Camera', self); self.btn_camera.setFixedHeight(28); self.btn_camera.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        actions.addWidget(self.btn_camera, alignment=Qt.AlignVCenter)
        self.btn_help = QToolButton(self); self.btn_help.setText('?'); self.btn_help.setObjectName('HelpCircle'); self.btn_help.setFixedSize(28,28)
        actions.addWidget(self.btn_help, alignment=Qt.AlignVCenter)
        v.addLayout(actions)

        # Signals
        self.btn_add_profile.clicked.connect(self._add_profile)
        self.tabbar.renameRequested.connect(self._on_tab_rename_requested)
        self.tabbar.tabCloseRequested.connect(self._on_tab_closed)

        self._ensure_default(); self._update_add_profile_enabled()

    def _find_tab(self, text: str) -> int:
        for i in range(self.tabbar.count()):
            if self.tabbar.tabText(i) == text: return i
        return -1
    def _default_index(self) -> int: return self._find_tab('Default')
    def _ensure_default(self):
        idx = self._default_index()
        if idx < 0:
            self.tabbar.insertTab(0, 'Default')
        else:
            if idx != 0:
                self.tabbar.removeTab(idx)
                self.tabbar.insertTab(0, 'Default')
        self.tabbar.setCurrentIndex(0)
    def _extra_profile_numbers(self) -> List[int]:
        nums: List[int] = []
        for i in range(self.tabbar.count()):
            text = self.tabbar.tabText(i)
            m = re.match(r"^Profile\s?#(\d+)$", text)
            if m:
                nums.append(int(m.group(1)))
        return nums
    def _next_available_number(self) -> Optional[int]:
        used = set(self._extra_profile_numbers())
        for n in range(1, self.MAX_EXTRA_PROFILES + 1):
            if n not in used:
                return n
        return None
    def _extra_profile_count(self) -> int:
        return len(self._extra_profile_numbers())
    def _update_add_profile_enabled(self):
        self.btn_add_profile.setEnabled(self._extra_profile_count() < self.MAX_EXTRA_PROFILES)
    def _add_profile(self):
        n = self._next_available_number()
        if n is None:
            self._update_add_profile_enabled()
            QMessageBox.information(self, 'Limit reached', f"Only up to {self.MAX_EXTRA_PROFILES} new profiles are allowed (excluding 'Default').")
            return
        text = f'Profile #{n}'
        self.tabbar.addTab(text)
        self.tabbar.setCurrentIndex(self.tabbar.count() - 1)
        self.profileAdded.emit(text)  # notify MainWindow
        self._update_add_profile_enabled()
    def _on_tab_closed(self, idx: int):
        self._update_add_profile_enabled()
        QTimer.singleShot(0, self._update_add_profile_enabled)
    def _on_tab_rename_requested(self, old: str, new: str):
        if self._find_tab(new) >= 0:
            QMessageBox.warning(self, 'Duplicate name', f"A profile named '{new}' already exists.")
            return
        idx = self._find_tab(old)
        if idx < 0: return
        self.tabbar.setTabText(idx, new)
        self.profileRenamed.emit(old, new)

# --- Windows ---
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



# --- asset helper: create a tiny black down caret PNG for QComboBox arrow ---
def ensure_down_arrow_asset():
    from PySide6.QtGui import QPainter, QPixmap, QColor, QPainterPath
    from PySide6.QtCore import Qt
    pm = QPixmap(12, 8)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    path = QPainterPath()
    path.moveTo(1, 1)
    path.lineTo(pm.width()-1, 1)
    path.lineTo(pm.width()//2, pm.height()-1)
    path.closeSubpath()
    p.fillPath(path, QColor(0, 0, 0))
    p.end()
    pm.save('arrow_down_black.png', 'PNG')
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
        self.cal_window = None; self.cam_window = None

        # Connect actions
        self.profiles_bar.btn_add_line.clicked.connect(self.add_new_card)
        self.profiles_bar.btn_camera.clicked.connect(self._on_camera_clicked)
        self.profiles_bar.btn_help.clicked.connect(self._on_help_clicked)
        self.profiles_bar.tabbar.currentChanged.connect(self._on_profile_changed)
        self.profiles_bar.profileRenamed.connect(self._on_profile_renamed)
        self.profiles_bar.profileAdded.connect(self._on_profile_added)  # NEW
        try: self.profiles_bar.btn_power.toggled.connect(self._on_power_toggled)
        except Exception: pass

        # Seed Default with sample inputs
        self._ensure_profile('Default')
        self.profiles_data['Default'] = [
            {'name': 'Forward',  'key': 'w', 'type': 'Click'},
            {'name': 'Backwards','key': 's', 'type': 'Click'},
            {'name': 'Left',     'key': 'a', 'type': 'Click'},
            {'name': 'Right',    'key': 'd', 'type': 'Click'},
        ]
        self._rebuild_kbm('Default')
        self._load_profile('Default')
        self.set_app_enabled(False)

    # --- Help & Camera ---
    def _on_help_clicked(self): dlg = ManualDialog(self); dlg.exec()
    def _on_camera_clicked(self):
        dlg = CountdownDialog(seconds=3, parent=self); result = dlg.exec()
        if result == QDialog.Accepted:
            self.open_camera_window(); self.statusBar().showMessage('Camera opened', 1500)
        else: self.statusBar().showMessage('Camera cancelled', 1500)

    # --- Power ---
    def _on_power_toggled(self, checked: bool):
        try:
            self.profiles_bar.btn_power.setIcon(make_power_icon(QColor(46, 204, 113) if checked else QColor(236, 236, 242)))
        except Exception: pass
        self.set_app_enabled(checked)

    def set_app_enabled(self, enabled: bool):
        self.app_enabled = bool(enabled)
        try: self.profiles_bar.btn_camera.setEnabled(enabled)
        except Exception: pass
        try:
            self.profiles_bar.btn_add_line.setEnabled(enabled and self._current_profile_name() != 'Default')
            self.profiles_bar.btn_add_profile.setEnabled(enabled and self.profiles_bar._extra_profile_count() < self.profiles_bar.MAX_EXTRA_PROFILES)
            self.profiles_bar.tabbar.setCloseOnHoverEnabled(enabled)
        except Exception: pass
        try:
            for i in range(self.cards_layout.count()):
                w = self.cards_layout.itemAt(i).widget()
                if isinstance(w, KeyInputCard):
                    is_default = (self._current_profile_name() == 'Default')
                    w.set_modifiable(enabled and not is_default)
                    w.btn_cam.setEnabled(enabled)
        except Exception: pass
        self.statusBar().showMessage('Application ' + ('ON' if enabled else 'OFF'), 1500)

    # --- Profiles & data ---
    def _ensure_profile(self, name: str):
        if name not in self.profiles_data: self.profiles_data[name] = []
        if name not in self.profiles_kbm: self.profiles_kbm[name] = KeyBindingManager()

    def _on_profile_added(self, name: str):
        # Initialize empty model immediately and show it
        self._ensure_profile(name)
        self._rebuild_kbm(name)
        self._load_profile(name)
        self.statusBar().showMessage(f"Profile '{name}' created (empty)", 1500)

    def profile_kbm(self, name: str) -> KeyBindingManager:
        self._ensure_profile(name); return self.profiles_kbm[name]

    def _rebuild_kbm(self, name: str):
        kbm = self.profile_kbm(name); kbm.name_to_key.clear(); kbm.key_to_name.clear(); seen = set()
        for item in self.profiles_data.get(name, []):
            nm = item.get('name', ''); key = item.get('key', '')
            norm = kbm._normalize(key)
            if nm and key and norm not in seen:
                kbm.assign(nm, key); seen.add(norm)

    def _current_profile_name(self) -> str:
        idx = self.profiles_bar.tabbar.currentIndex(); return self.profiles_bar.tabbar.tabText(idx) if idx >= 0 else 'Default'

    def _on_profile_changed(self, idx: int):
        name = self.profiles_bar.tabbar.tabText(idx) if idx >= 0 else 'Default'
        self._ensure_profile(name)
        self._rebuild_kbm(name)
        self._load_profile(name)
        try:
            self.profiles_bar.btn_add_line.setEnabled(self.app_enabled and name != 'Default')
        except Exception: pass
        self.statusBar().showMessage(f'Switched to {name}', 1500)

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
            if w is not None:
                w.setParent(None); w.deleteLater()
            self.cards_layout.takeAt(i)

    def _load_profile(self, name: str):
        # Synchronous populate—avoids leftovers and race conditions
        self._clear_cards()
        for item in self.profiles_data.get(name, []):
            modifiable = (name != 'Default') and self.app_enabled
            card = KeyInputCard(item.get('name', ''), item.get('key', ''), item.get('type', 'Click'), modifiable=modifiable)
            self.cards_layout.addWidget(card)

    def add_card(self, name_text: str, key_text: str, input_type: str):
        prof = self._current_profile_name(); self._ensure_profile(prof)
        if prof == 'Default':
            QMessageBox.information(self, 'Info', 'Default profile cannot be modified.')
            return
        if not self.app_enabled:
            QMessageBox.information(self, 'Info', 'Turn ON the power to modify profiles.')
            return
        kbm = self.profile_kbm(prof); ok, _ = kbm.can_assign(name_text or '', key_text)
        if key_text and not ok:
            QMessageBox.warning(self, 'Duplicate Key', ("The key '{}' is already used in profile '{}'." "No two key inputs can be the same.").format(key_text, prof)); key_text = ''
        self.profiles_data[prof].append({'name': name_text, 'key': key_text, 'type': input_type})
        if name_text and key_text:
            self.profile_kbm(prof).assign(name_text, key_text)
        card = KeyInputCard(name_text, key_text, input_type, modifiable=True)
        self.cards_layout.addWidget(card)

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
        prof = self._current_profile_name()
        if prof == 'Default' or not self.app_enabled:
            QMessageBox.information(self, 'Info', 'Cannot delete in Default profile or when power is OFF.')
            return
        items = self.profiles_data.get(prof, [])
        self.profiles_data[prof] = [it for it in items if not (it.get('name') == card.prev_name and it.get('key') == card.prev_key)]
        card.setParent(None); card.deleteLater()

    def open_calibration_window(self, start_recording: bool = False):
        if self.cal_window is None: self.cal_window = CalibrationWindow()
        self.cal_window.show(); self.cal_window.raise_()
        if start_recording: self.cal_window.start_recording()

    def open_camera_window(self):
        if self.cam_window is None: self.cam_window = CameraWindow()
        self.cam_window.show(); self.cam_window.raise_()

# --- main ---
def main():
    app = QApplication(sys.argv)
    ensure_down_arrow_asset()
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
