# 모든 종속성을 포함하고 / 콘솔창 없이 실행
# pyinstaller --onefile --noconsole commadqt_g.py
# --icon=icon.ico 로 아이콘 적용

import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QTextEdit, QLineEdit,
    QLabel, QFileDialog, QMessageBox, QInputDialog
)
from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtGui import QColor

CONFIG_PATH = os.path.expanduser("~/.config/test/commands.json")

os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as f:
        json.dump([], f)


def load_commands(): # json 파일 불러오기
    try:
        with open(CONFIG_PATH, "r") as f:
            data = f.read().strip()
            return json.loads(data) if data else []
    except json.JSONDecodeError:
        QMessageBox.warning(None, "Error", "Failed to load JSON file. JSON file might be corrupted.")
        return []
    except FileNotFoundError:
        return [] # File might be deleted after initial check but before loading

def save_commands(commands): # json 파일을 저장
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(commands, f, indent=4)
    except IOError as e:
        QMessageBox.warning(None, "Error", f"Failed to save commands: {e}")



class CommandManager(QWidget): 
    def __init__(self):
        super().__init__() # 다른 클래스의 메소드를 자동으로 불러와서 사용
        #QWidget도 클래스이다
        self.commands = load_commands()
        self.init_ui()
        self.process = None
        self.sudo_password = None # Initialize sudo_password

    def init_ui(self):
        self.setWindowTitle("Ubuntu Package installer")
        self.resize(700, 800)

        main_layout = QVBoxLayout()

        # Input Area
        self.name_entry = QLineEdit() #텍스트를 입력 및 수정을 위한 GUI, 복붙넣자르기 가능
        self.name_entry.setPlaceholderText("Enter command name (e.g., 'Update System')")
        self.command_entry = QTextEdit() #LineEdit과 비슷하지만 여러 줄을 입력받는다.
        self.command_entry.setPlaceholderText("Enter the command (e.g., 'sudo apt update && sudo apt upgrade -y') \n Better to add -y option on your command")

        form_layout = QVBoxLayout() # 위젯을 세로 방향으로 배치
        form_layout.addWidget(QLabel("명령어 제목:"))
        form_layout.addWidget(self.name_entry)
        form_layout.addWidget(QLabel("명령어:"))
        form_layout.addWidget(self.command_entry)
        main_layout.addLayout(form_layout)

        # Buttons Area
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("추가")
        self.delete_btn = QPushButton("삭제")
        self.update_btn = QPushButton("수정")
        self.run_btn = QPushButton("실행")
        self.run_btn.setStyleSheet("background-color: #ff0000; color: white; font-weight: bold;") # Use hex color
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.update_btn)
        button_layout.addWidget(self.run_btn)
        main_layout.addLayout(button_layout)

        # List Area
        self.command_list = QListWidget()
        self.command_list.addItems([cmd['name'] for cmd in self.commands])
        main_layout.addWidget(self.command_list)

        # Output Area
        self.output = QTextEdit()
        self.output.setStyleSheet("background-color: black; color: white; font-family: monospace;")
        self.output.setReadOnly(True)
        main_layout.addWidget(QLabel("출력 결과:"))
        main_layout.addWidget(self.output)

        # JSON import/export
        json_btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("JSON 내보내기")
        self.import_btn = QPushButton("JSON 가져오기")
        json_btn_layout.addWidget(self.export_btn)
        json_btn_layout.addWidget(self.import_btn)
        main_layout.addLayout(json_btn_layout)

        self.setLayout(main_layout)

        # Signal Connections
        self.add_btn.clicked.connect(self.add_command)
        self.update_btn.clicked.connect(self.update_command)
        self.run_btn.clicked.connect(self.run_command)
        self.delete_btn.clicked.connect(self.delete_command)
        self.command_list.currentRowChanged.connect(self.select_command)
        self.export_btn.clicked.connect(self.export_json)
        self.import_btn.clicked.connect(self.import_json)



    def add_command(self):
        name = self.name_entry.text().strip()
        cmd_content = self.command_entry.toPlainText().strip()

        if not cmd_content:
            QMessageBox.warning(self, "Input Error", "Command content cannot be empty.")
            return
        if not name:
            name = cmd_content.split("\n")[0] # Auto-fill name if not provided

        self.commands.append({"name": name, "command": cmd_content})
        save_commands(self.commands)
        self.refresh_list()
        self.name_entry.clear()
        self.command_entry.clear()
        QMessageBox.information(self, "Success", "Command added successfully.")


    def update_command(self):
        index = self.command_list.currentRow()
        if index < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a command to update.")
            return

        name = self.name_entry.text().strip()
        cmd_content = self.command_entry.toPlainText().strip()

        if not cmd_content:
            QMessageBox.warning(self, "Input Error", "Command content cannot be empty.")
            return
        if not name:
            name = cmd_content.split("\n")[0] # Auto-fill name if not provided

        self.commands[index]["name"] = name
        self.commands[index]["command"] = cmd_content
        save_commands(self.commands)
        self.refresh_list()
        QMessageBox.information(self, "Success", "Command updated successfully.")


    def delete_command(self):
        index = self.command_list.currentRow()
        if index < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a command to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to delete '{self.commands[index]['name']}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            del self.commands[index]
            save_commands(self.commands)
            self.refresh_list()
            self.name_entry.clear()
            self.command_entry.clear()
            QMessageBox.information(self, "Success", "Command deleted successfully.")


    def select_command(self, index):
        if index >= 0 and index < len(self.commands):
            self.name_entry.setText(self.commands[index]['name'])
            self.command_entry.setPlainText(self.commands[index]['command'])
        else: # Handle case where selection is cleared
            self.name_entry.clear()
            self.command_entry.clear()


    def refresh_list(self):
        self.command_list.clear()
        self.command_list.addItems([cmd['name'] for cmd in self.commands])

    def run_command(self):
        index = self.command_list.currentRow() # select current row in command list
        if index < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a command to run.")
            return

        cmd = self.commands[index]['command'] # load command from

        # QProcess 클래스는  외부 프로그램을 실행 후 결과를 얻어온다
        if self.process and self.process.state() == QProcess.Running:
            QMessageBox.information(self, "Command Running", "A command is already running. Please wait for it to finish.")
            return

        # Sudo handling
        if "sudo" in cmd:
            if not self.sudo_password: # Only prompt if password isn't stored
                password, ok = QInputDialog.getText(self, "sudo 비밀번호 입력", "비밀번호:", QLineEdit.Password)
                if not ok:
                    QMessageBox.information(self, "Cancelled", "Sudo password entry cancelled.")
                    return
                self.sudo_password = password
            
            # Prepend echo password to sudo command using -S
            # This requires careful handling if the command itself has pipes or complex structures
            # A more robust solution might involve writing the password to stdin,
            # but for simple sudo, this pattern is common.
            cmd_to_execute = f"echo {self.sudo_password} | sudo -S bash -c '{cmd}'"
        else:
            cmd_to_execute = cmd

        self.output.append(f"\n$ {cmd}\n")
        self.run_btn.setEnabled(False) # Disable run button while command is executing
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels) # Merge stdout and stderr
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.command_finished)
        
        # Start the command using bash -c to ensure complex commands are parsed correctly
        self.process.start("bash", ["-c", cmd_to_execute])

    def read_output(self):
        if self.process:
            text = self.process.readAllStandardOutput().data().decode(errors='ignore') # Ignore decoding errors
            self.output.insertPlainText(text) # Use insertPlainText to avoid adding newlines
            self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum()) # Scroll to bottom

    def command_finished(self):
        self.output.append("\n[Command Finished]")
        self.run_btn.setEnabled(True) # Re-enable run button
        # Optionally clear sudo_password if you want to prompt every time
        # self.sudo_password = None


    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "JSON 내보내기", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "w") as f:
                    json.dump(self.commands, f, indent=4)
                QMessageBox.information(self, "Success", f"Commands exported to {path}")
            except IOError as e:
                QMessageBox.critical(self, "Error", f"Failed to export JSON: {e}")


    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "JSON 가져오기", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r") as f:
                    new_commands = json.load(f)
                self.commands = new_commands
                save_commands(self.commands)
                self.refresh_list()
                QMessageBox.information(self, "Success", f"Commands imported from {path}")
            except (IOError, json.JSONDecodeError) as e:
                QMessageBox.critical(self, "Error", f"Failed to import JSON: {e}")

# 파이썬 파일이 실해오디면 __name__에 현재 파일 이름을 할당함
# 스크립트를 직접 실행하면 name에 main을 할당
# 모듈로 불러오면 name에 import된 이름으로 저장
# 즉, 파일이 직접 실행될 때만 아래의 코드를 실행한다
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CommandManager()
    win.show()
    sys.exit(app.exec_())
