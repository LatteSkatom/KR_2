from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QFormLayout
from PyQt6.QtCore import Qt
from db import check_user

class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.setWindowTitle("Авторизация — Фитнес-клуб")
        self.resize(360, 220)
        layout = QVBoxLayout()
        layout.setSpacing(12)
        self.lbl = QLabel("Вход в систему")
        layout.addWidget(self.lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Введите логин")
        form.addRow("Логин:", self.login_edit)
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Введите пароль")
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Пароль:", self.pass_edit)
        layout.addLayout(form)
        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.try_login)
        layout.addWidget(self.btn_login)
        layout.addStretch()
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
