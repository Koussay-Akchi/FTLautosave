import json
import sys
import os
import shutil
import subprocess
import time
import threading
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtGui import QIcon, QPainterPath, QRegion, QPixmap, QPainter
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QSpinBox, QLabel
import sys
		
def resource_path(relative_path):
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class FTLAutosave(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setWindowIcon(QIcon(resource_path('bg.ico')))
        self.resize(600, 400)
        self.setWindowTitle('FTL Autosave Manager')

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(button_layout)
        button_widget.setFixedWidth(300)

        spacer = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)
        layout.addWidget(button_widget)

        self.label = QtWidgets.QLabel('Autosave Interval :')
        self.label.setFixedHeight(10)
        button_layout.addWidget(self.label)

        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 999)
        self.interval_spinbox.setValue(1)
        self.update_spinbox_suffix()
        self.interval_spinbox.valueChanged.connect(self.update_spinbox_suffix)
        button_layout.addWidget(self.interval_spinbox)

        self.play_button = QtWidgets.QPushButton('Play')
        self.play_button.clicked.connect(self.play)
        button_layout.addWidget(self.play_button)

        self.restart_button = QtWidgets.QPushButton('Restart')
        self.restart_button.clicked.connect(self.restart)
        button_layout.addWidget(self.restart_button)

        self.restore_button = QtWidgets.QPushButton('Restore Backup')
        self.restore_button.clicked.connect(self.restore_backup)
        button_layout.addWidget(self.restore_button)

        self.exit_button = QtWidgets.QPushButton('Exit')
        self.exit_button.setStyleSheet("QPushButton { margin-top: 20px; }")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)

        self.setLayout(layout)
        self.setMask(self.create_rounded_mask(self.size()))

        self.ensure_folders_exist()
        self.update_button_states()

    def update_spinbox_suffix(self):
        value = self.interval_spinbox.value()
        if value == 1:
            self.interval_spinbox.setSuffix(' minute')
        else:
            self.interval_spinbox.setSuffix(' minutes')

    def ensure_folders_exist(self):
        os.makedirs(autosave_folder, exist_ok=True)
        os.makedirs(backup_folder, exist_ok=True)

    def create_rounded_mask(self, size):
        path = QPainterPath()
        path.addRoundedRect(QtCore.QRectF(0, 0, size.width(), size.height()), 30, 30)
        mask = QRegion(path.toFillPolygon().toPolygon())
        return mask

    def get_shortcut_path(self):
        autosave_file = os.path.join(os.getenv('APPDATA'), 'FTLautosave.json')
        if os.path.exists(autosave_file):
            with open(autosave_file, 'r') as f:
                data = json.load(f)
                if os.path.exists(data.get('shortcut_path', '')):
                    return data['shortcut_path']

        shortcut_path, _ = QFileDialog.getOpenFileName(self, "Select FTL Shortcut", "", "Shortcut Files (*.lnk)")
        if shortcut_path:
            with open(autosave_file, 'w') as f:
                json.dump({'shortcut_path': shortcut_path}, f)
            return shortcut_path

        return None

    def check_continue_sav(self, folder_path):
        return os.path.isfile(os.path.join(folder_path, 'continue.sav'))

    def update_button_states(self):
        self.restart_button.setEnabled(self.check_continue_sav(autosave_folder))
        self.restore_button.setEnabled(self.check_continue_sav(backup_folder))

    def play(self):
        shortcut_path = self.get_shortcut_path()
        if not shortcut_path:
            QMessageBox.critical(self, "Error", "FTL shortcut not found or not selected.")
            return

        def clean_and_copy(source_folder, target_folder):
            for filename in os.listdir(target_folder):
                file_path = os.path.join(target_folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")

            try:
                shutil.copytree(source_folder, target_folder, dirs_exist_ok=True)
            except Exception as e:
                print(f"Failed to copy {source_folder} to {target_folder}. Reason: {e}")

        if not self.check_continue_sav(autosave_folder):
            clean_and_copy(ftl_folder, autosave_folder)

        if not self.check_continue_sav(backup_folder):
            clean_and_copy(ftl_folder, backup_folder)

        interval_minutes = self.interval_spinbox.value()

        def run_backup_cycle():
            while True:
                try:
                    shutil.copytree(autosave_folder, backup_folder, dirs_exist_ok=True)
                    shutil.copytree(ftl_folder, autosave_folder, dirs_exist_ok=True)
                    print("Backup and copy operation completed.")
                except Exception as e:
                    print(f'Failed during backup cycle. Reason: {e}')
                time.sleep(interval_minutes * 60)  

        try:
            subprocess.run(shortcut_path, shell=True)
            print("FTL has been launched successfully.")
        except Exception as e:
            print(f'Failed to run FTL. Reason: {e}')

        threading.Thread(target=run_backup_cycle, daemon=True).start()

    def restart(self):
        for filename in os.listdir(ftl_folder):
            file_path = os.path.join(ftl_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete {file_path}. Reason: {e}")
                return

        try:
            shutil.copytree(autosave_folder, ftl_folder, dirs_exist_ok=True)
            print("Restart operation completed successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy {autosave_folder} to {ftl_folder}. Reason: {e}")

    def restore_backup(self):
        for filename in os.listdir(autosave_folder):
            file_path = os.path.join(autosave_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete {file_path}. Reason: {e}")
                return

        try:
            shutil.copytree(backup_folder, autosave_folder, dirs_exist_ok=True)
            print("Restore backup operation completed successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy {backup_folder} to {autosave_folder}. Reason: {e}")

    def paintEvent(self, event):
        painter = QPainter(self)
        pixmap = QPixmap(resource_path('bg.ico'))
        painter.drawPixmap(self.rect(), pixmap)
        super().paintEvent(event)

if __name__ == '__main__':
    user_home = os.path.expanduser("~")
    ftl_folder = os.path.join(user_home, "Documents", "My Games", "FasterThanLight")
    autosave_folder = os.path.join(user_home, "Documents", "My Games", "autosave")
    backup_folder = os.path.join(user_home, "Documents", "My Games", "backup")
    app = QtWidgets.QApplication(sys.argv)
    window = FTLAutosave()
    window.show()
    sys.exit(app.exec())
