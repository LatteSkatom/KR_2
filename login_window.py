from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
from db import check_user

class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.setWindowTitle("Авторизация — Фитнес-клуб")
        self.resize(350,200)
        layout = QVBoxLayout()
        self.lbl = QLabel("<h2>Вход</h2>")
        layout.addWidget(self.lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Логин")
        layout.addWidget(self.login_edit)
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Пароль")
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pass_edit)
        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.try_login)
        layout.addWidget(self.btn_login)
        self.setLayout(layout)

    def try_login(self):
        login = self.login_edit.text().strip()
        password = self.pass_edit.text().strip()
        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
        user = check_user(login, password)
        if not user:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
            return
        self.on_login_success(user)
        self.close()
