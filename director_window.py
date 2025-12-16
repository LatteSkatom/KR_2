from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QTextEdit,
    QInputDialog,
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
)

from db import (
    director_general_stats,
    director_trainer_efficiency,
    director_finance_stats,
    director_staff_list,
    get_membership_prices,
    update_membership_price,
    strategic_report,
    hire_staff,
    fire_staff,
)


class DirectorWindow(QWidget):



    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("Директор клуба")
        self.resize(1100, 720)

        root = QVBoxLayout()
        root.addWidget(QLabel("<h2>Панель директора</h2>"))


        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_general_tab(), "Статистика")
        self.tabs.addTab(self._build_trainers_tab(), "Эффективность тренеров")
        self.tabs.addTab(self._build_finance_tab(), "Финансы")
        self.tabs.addTab(self._build_prices_tab(), "Ценовая политика")
        self.tabs.addTab(self._build_report_tab(), "Стратегические отчёты")
        self.tabs.addTab(self._build_staff_tab(), "Персонал")

        root.addWidget(self.tabs)
        self.setLayout(root)

        self._load_general()
        self._load_trainers()
        self._load_finance()
        self._load_prices()
        self._load_staff()

    # ------------------------------
    # Построение вкладок
    # ------------------------------
    def _build_general_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)


        self.general_table = QTableWidget(0, 2)
        self.general_table.setHorizontalHeaderLabels(["Показатель", "Значение"])
        layout.addWidget(self.general_table)
        return widget

    def _build_trainers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)


        self.trainer_table = QTableWidget(0, 5)
        self.trainer_table.setHorizontalHeaderLabels(
            ["Тренер", "Продажи", "Посещаемость", "KPI", "Клиенты"]
        )
        layout.addWidget(self.trainer_table)
        return widget

    def _build_finance_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)


        self.finance_table = QTableWidget(0, 4)
        self.finance_table.setHorizontalHeaderLabels([
            "Месяц",
            "Выручка",
            "Расходы",
            "Прибыль",
        ])
        layout.addWidget(self.finance_table)
        return widget

    def _build_prices_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)


        self.price_table = QTableWidget(0, 2)
        self.price_table.setHorizontalHeaderLabels(["Тип абонемента", "Цена"])
        layout.addWidget(self.price_table)

        buttons = QHBoxLayout()
        change_btn = QPushButton("Утвердить новую цену")
        change_btn.clicked.connect(self._change_price)
        buttons.addWidget(change_btn)

        discount_btn = QPushButton("Применить скидку")
        discount_btn.clicked.connect(self._discount_price)
        buttons.addWidget(discount_btn)

        layout.addLayout(buttons)
        return widget

    def _build_report_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)


        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(self.report_text)

        btn = QPushButton("Сформировать отчёт")
        btn.clicked.connect(self._make_report)
        layout.addWidget(btn)
        return widget

    def _build_staff_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)


        self.staff_table = QTableWidget(0, 6)
        self.staff_table.setHorizontalHeaderLabels(
            ["ID", "Фамилия", "Имя", "Отчество", "Роль", "Телефон"]
        )
        self.staff_table.setColumnHidden(0, True)
        layout.addWidget(self.staff_table)

        buttons = QHBoxLayout()
        hire_btn = QPushButton("Нанять")
        fire_btn = QPushButton("Уволить")
        hire_btn.clicked.connect(self._hire)
        fire_btn.clicked.connect(self._fire)
        buttons.addWidget(hire_btn)
        buttons.addWidget(fire_btn)
        layout.addLayout(buttons)
        return widget

    # ------------------------------
    # Загрузка данных
    # ------------------------------
    def _load_general(self):
        self.general_table.setRowCount(0)
        try:
            stats = director_general_stats()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить статистику: {exc}")
            return

        for name, value in stats.items():
            row = self.general_table.rowCount()
            self.general_table.insertRow(row)
            self.general_table.setItem(row, 0, QTableWidgetItem(name))
            self.general_table.setItem(row, 1, QTableWidgetItem(str(value)))

    def _load_trainers(self):
        self.trainer_table.setRowCount(0)
        try:
            rows = director_trainer_efficiency()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные по тренерам: {exc}")
            return

        for data in rows:
            row = self.trainer_table.rowCount()
            self.trainer_table.insertRow(row)

            sales = data.get("pt_count", 0) + data.get("group_count", 0)
            attendance = data.get("group_count", 0)
            clients = data.get("clients", 0)
            kpi = self._calc_trainer_kpi(sales, attendance, clients)

            self.trainer_table.setItem(row, 0, QTableWidgetItem(data.get("fio", "")))
            self.trainer_table.setItem(row, 1, QTableWidgetItem(str(sales)))
            self.trainer_table.setItem(row, 2, QTableWidgetItem(str(attendance)))
            self.trainer_table.setItem(row, 3, QTableWidgetItem(kpi))
            self.trainer_table.setItem(row, 4, QTableWidgetItem(str(clients)))

    def _load_finance(self):
        self.finance_table.setRowCount(0)
        try:
            rows = director_finance_stats()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить финансы: {exc}")
            return

        for data in rows:
            row = self.finance_table.rowCount()
            self.finance_table.insertRow(row)

            revenue = data.get("total") or data.get("revenue") or 0
            expenses = data.get("expenses")
            profit = data.get("profit")
            if expenses is None:
                expenses = "—"
            if profit is None:
                if isinstance(revenue, (int, float)) and isinstance(expenses, (int, float)):
                    profit = revenue - expenses
                elif isinstance(revenue, (int, float)):
                    profit = revenue
                else:
                    profit = "—"

            self.finance_table.setItem(row, 0, QTableWidgetItem(str(data.get("month", ""))))
            self.finance_table.setItem(row, 1, QTableWidgetItem(str(revenue)))
            self.finance_table.setItem(row, 2, QTableWidgetItem(str(expenses)))
            self.finance_table.setItem(row, 3, QTableWidgetItem(str(profit)))

    def _load_prices(self):
        self.price_table.setRowCount(0)
        try:
            rows = get_membership_prices()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить цены: {exc}")
            return

        for data in rows:
            row = self.price_table.rowCount()
            self.price_table.insertRow(row)
            membership = data.get("membershipType", "")
            cost = data.get("cost", "")
            self.price_table.setItem(row, 0, QTableWidgetItem(str(membership)))
            self.price_table.setItem(row, 1, QTableWidgetItem(str(cost)))

    def _load_staff(self):
        self.staff_table.setRowCount(0)
        try:
            rows = director_staff_list()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сотрудников: {exc}")
            return

        for data in rows:
            row = self.staff_table.rowCount()
            self.staff_table.insertRow(row)
            self.staff_table.setItem(row, 0, QTableWidgetItem(str(data.get("userID", ""))))
            self.staff_table.setItem(row, 1, QTableWidgetItem(data.get("lastName", "")))
            self.staff_table.setItem(row, 2, QTableWidgetItem(data.get("firstName", "")))
            self.staff_table.setItem(row, 3, QTableWidgetItem(data.get("middleName", "")))
            self.staff_table.setItem(row, 4, QTableWidgetItem(data.get("userType", "")))
            self.staff_table.setItem(row, 5, QTableWidgetItem(data.get("phone", "")))

    # ------------------------------
    # Действия
    # ------------------------------
    def _change_price(self):
        row = self.price_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите тип абонемента")
            return
        membership = self.price_table.item(row, 0).text()
        price, ok = QInputDialog.getDouble(
            self,
            "Новая цена",
            f"Введите новую стоимость для '{membership}':",
            decimals=2,
            min=0,
        )
        if not ok:
            return

        try:
            updated = update_membership_price(membership, float(price))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить цену: {exc}")
            return

        if updated:
            QMessageBox.information(self, "Готово", "Цена утверждена")
            self._load_prices()
        else:
            QMessageBox.warning(self, "Внимание", "Тип абонемента не найден")

    def _discount_price(self):
        row = self.price_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите тип абонемента")
            return
        membership = self.price_table.item(row, 0).text()
        discount, ok = QInputDialog.getDouble(
            self,
            "Скидка",
            "Размер скидки, %:",
            decimals=1,
            min=0,
            max=100,
        )
        if not ok:
            return

        current_price = float(self.price_table.item(row, 1).text())
        new_price = max(0.0, current_price * (1 - discount / 100))
        try:
            updated = update_membership_price(membership, new_price)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось применить скидку: {exc}")
            return

        if updated:
            QMessageBox.information(self, "Готово", "Скидка применена")
            self._load_prices()
        else:
            QMessageBox.warning(self, "Внимание", "Тип абонемента не найден")

    def _make_report(self):
        try:
            data = strategic_report()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сформировать отчёт: {exc}")
            return

        lines = [f"{k}: {v}" for k, v in data.items()]
        self.report_text.setText("\n".join(lines))

    def _hire(self):
        dialog = HireDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()
        fio = " ".join(part for part in [data["last"], data["first"], data["middle"]] if part)
        clean_login = data["login"] or f"{data['last']}_{data['first']}".lower()
        clean_pass = data["password"] or "123"

        try:
            hire_staff(
                fio,
                data["phone"] or None,
                data["email"] or None,
                clean_login,
                clean_pass,
                data["role"],
            )
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить сотрудника: {exc}")
            return

        QMessageBox.information(self, "Готово", "Сотрудник добавлен")
        self._load_staff()

    def _fire(self):
        row = self.staff_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return
        user_id = int(self.staff_table.item(row, 0).text())

        try:
            removed = fire_staff(user_id)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить сотрудника: {exc}")
            return

        if removed:
            QMessageBox.information(self, "Готово", "Сотрудник удалён")
            self._load_staff()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось удалить сотрудника")

    # ------------------------------
    # Вспомогательное
    # ------------------------------
    @staticmethod
    def _calc_trainer_kpi(sales: int, attendance: int, clients: int) -> str:
        if clients <= 0:
            return "—"
        score = (sales * 0.6 + attendance * 0.4) / clients
        return f"{score:.2f}"


class HireDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Найм сотрудника")

        form = QFormLayout()

        self.last_input = QLineEdit()
        self.first_input = QLineEdit()
        self.middle_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_input = QComboBox()
        self.role_input.addItems(["Тренер", "Администратор"])

        form.addRow("Фамилия*", self.last_input)
        form.addRow("Имя*", self.first_input)
        form.addRow("Отчество", self.middle_input)
        form.addRow("Телефон", self.phone_input)
        form.addRow("Email", self.email_input)
        form.addRow("Логин", self.login_input)
        form.addRow("Пароль", self.password_input)
        form.addRow("Роль", self.role_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _on_accept(self):
        if not self.last_input.text().strip() or not self.first_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Фамилия и имя обязательны")
            return
        self.accept()

    def get_data(self):
        return {
            "last": self.last_input.text().strip(),
            "first": self.first_input.text().strip(),
            "middle": self.middle_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "login": self.login_input.text().strip(),
            "password": self.password_input.text(),
            "role": self.role_input.currentText(),
        }
