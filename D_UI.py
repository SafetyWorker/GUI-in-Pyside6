from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import QSize
from PySide6.QtWidgets import ( 
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QStatusBar, QMessageBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTabBar, QToolButton, QDialog, QScrollArea, 
    QSizePolicy, QFrame, QTextBrowser, QGraphicsDropShadowEffect, QTabWidget
) 

# tabs = window.findChild(QTabWidget, "tabWidget")
# btn = QPushButton("+")
# btn.setFixedSize(50,50)
# tabs.setCornerWidget(btn, Qt.TopRightCorner)
    
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        file = QFile("testv2.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.window = loader.load(file, self)
        file.close()

        # --- THIS IS WHERE WE FIND YOUR ORIGINAL WIDGETS ---
        # We find them ONCE here, instead of finding them repeatedly in resizeEvent
        self.tabs = self.window.findChild(QTabWidget, "tabWidget")
        self.power_btn = self.window.findChild(QWidget, "pushButton") # Your 'power' button

        # --- FINDING THE NEW BUTTONS ---
        self.btnRecord = self.window.findChild(QPushButton, "btnRecord")
        self.btnAddLie = self.window.findChild(QPushButton, "btnAddLie")
        self.btnCamera = self.window.findChild(QPushButton, "btnCamera")
        self.btnSettings = self.window.findChild(QPushButton, "btnSettings")

        # Setup custom new tab button
        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setFixedSize(50,50)
        self.new_tab_btn.setCursor(Qt.PointingHandCursor)
        
    def resizeEvent(self, event):
        self.window.setGeometry(self.rect())
        geom = self.geometry()
        
        # --- HANDLING YOUR ORIGINAL TABS ---
        if self.tabs:
            # logic: fill width, but leave 80px at bottom for the new buttons
            self.tabs.setGeometry(0, 14, geom.width(), geom.height() - 80)

        # --- HANDLING YOUR ORIGINAL POWER BUTTON ---
        if self.power_btn:
            self.power_btn.move(geom.width() - self.power_btn.width(), 0)

        # --- HANDLING THE NEW 4 BUTTONS (Keep them at bottom) ---
        buttons = [self.btnRecord, self.btnAddLie, self.btnCamera, self.btnSettings]
        valid_buttons = [b for b in buttons if b is not None]

        if valid_buttons:
            margin_bottom = 20
            spacing = 10
            total_width = sum(b.width() for b in valid_buttons) + (spacing * (len(valid_buttons) - 1))
            current_x = (geom.width() - total_width) // 2 
            
            for btn in valid_buttons:
                pos_y = geom.height() - btn.height() - margin_bottom
                btn.move(current_x, pos_y)
                current_x += btn.width() + spacing

        super().resizeEvent(event)
app = QApplication([])
window = MainWindow()
window.show()
app.exec()