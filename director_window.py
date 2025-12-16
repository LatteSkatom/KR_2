from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QMessageBox, QTextEdit, QInputDialog
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
        self.resize(1000, 650)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h2>Панель директора</h2>"))

        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_general_tab(), "Общая статистика")
        self.tabs.addTab(self.build_trainers_tab(), "Тренеры")
        self.tabs.addTab(self.build_finance_tab(), "Финансы")
        self.tabs.addTab(self.build_prices_tab(), "Ценовая политика")
        self.tabs.addTab(self.build_report_tab(), "Стратегический отчёт")
        self.tabs.addTab(self.build_staff_tab(), "Персонал")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.load_general()
        self.load_trainers()
        self.load_finance()
        self.load_prices()
        self.load_staff()


    def build_general_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.general_table = QTableWidget(0, 2)
        self.general_table.setHorizontalHeaderLabels(["Показатель", "Значение"])
        v.addWidget(self.general_table)
        return w

    def build_trainers_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.trainer_table = QTableWidget(0, 4)
        self.trainer_table.setHorizontalHeaderLabels([
            "Тренер", "Групповые", "Персональные", "Клиенты"
        ])
        v.addWidget(self.trainer_table)
        return w

    def build_finance_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.finance_table = QTableWidget(0, 3)
        self.finance_table.setHorizontalHeaderLabels([
            "Месяц", "Продано", "Выручка"
        ])
        v.addWidget(self.finance_table)
        return w

    def build_prices_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.price_table = QTableWidget(0, 2)
        self.price_table.setHorizontalHeaderLabels(["Тип абонемента", "Цена"])
        v.addWidget(self.price_table)

        btn = QPushButton("Изменить цену")
        btn.clicked.connect(self.change_price)
        v.addWidget(btn)
        return w

    def build_report_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        v.addWidget(self.report_text)

        btn = QPushButton("Сформировать отчёт")
        btn.clicked.connect(self.make_report)
        v.addWidget(btn)
        return w

    def build_staff_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.staff_table = QTableWidget(0, 6)
        self.staff_table.setHorizontalHeaderLabels(["ID", "Фамилия", "Имя", "Отчество", "Роль", "Телефон"])
        self.staff_table.setColumnHidden(0, True)
        v.addWidget(self.staff_table)

        btns = QHBoxLayout()
        hire_btn = QPushButton("Нанять")
        fire_btn = QPushButton("Уволить")
        hire_btn.clicked.connect(self.hire)
        fire_btn.clicked.connect(self.fire)
        btns.addWidget(hire_btn)
        btns.addWidget(fire_btn)
        v.addLayout(btns)
        return w


    def load_general(self):
        self.general_table.setRowCount(0)
        try:
            stats = director_general_stats()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить статистику: {exc}")
            return

        for k, v in stats.items():
            r = self.general_table.rowCount()
            self.general_table.insertRow(r)
            self.general_table.setItem(r, 0, QTableWidgetItem(k))
            self.general_table.setItem(r, 1, QTableWidgetItem(str(v)))

    def load_trainers(self):
        self.trainer_table.setRowCount(0)
        try:
            rows = director_trainer_efficiency()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные по тренерам: {exc}")
            return

        for rdata in rows:
            r = self.trainer_table.rowCount()
            self.trainer_table.insertRow(r)
            self.trainer_table.setItem(r, 0, QTableWidgetItem(rdata['fio']))
            self.trainer_table.setItem(r, 1, QTableWidgetItem(str(rdata['group_count'])))
            self.trainer_table.setItem(r, 2, QTableWidgetItem(str(rdata['pt_count'])))
            self.trainer_table.setItem(r, 3, QTableWidgetItem(str(rdata['clients'])))

    def load_finance(self):
        self.finance_table.setRowCount(0)
        try:
            rows = director_finance_stats()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить финансы: {exc}")
            return

        for rdata in rows:
            r = self.finance_table.rowCount()
            self.finance_table.insertRow(r)
            self.finance_table.setItem(r, 0, QTableWidgetItem(rdata['month']))
            self.finance_table.setItem(r, 1, QTableWidgetItem(str(rdata['sold'])))
            self.finance_table.setItem(r, 2, QTableWidgetItem(str(rdata['total'])))

    def load_prices(self):
        self.price_table.setRowCount(0)
        try:
            rows = get_membership_prices()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить цены: {exc}")
            return

        for row in rows:
            r = self.price_table.rowCount()
            self.price_table.insertRow(r)
            membership = row.get('membershipType', '')
            cost = row.get('cost', '')
            self.price_table.setItem(r, 0, QTableWidgetItem(str(membership)))
            self.price_table.setItem(r, 1, QTableWidgetItem(str(cost)))

    def load_staff(self):
        self.staff_table.setRowCount(0)
        try:
            rows = director_staff_list()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сотрудников: {exc}")
            return

        for rdata in rows:
            r = self.staff_table.rowCount()
            self.staff_table.insertRow(r)
            self.staff_table.setItem(r, 0, QTableWidgetItem(str(rdata['userID'])))
            self.staff_table.setItem(r, 1, QTableWidgetItem(rdata.get('lastName', '')))
            self.staff_table.setItem(r, 2, QTableWidgetItem(rdata.get('firstName', '')))
            self.staff_table.setItem(r, 3, QTableWidgetItem(rdata.get('middleName', '')))
            self.staff_table.setItem(r, 4, QTableWidgetItem(rdata['userType']))
            self.staff_table.setItem(r, 5, QTableWidgetItem(rdata.get('phone', '')))


    def change_price(self):
        r = self.price_table.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите тип абонемента")
            return
        t = self.price_table.item(r, 0).text()
        price, ok = QInputDialog.getDouble(self, "Цена", "Новая цена:", decimals=2, min=0)
        if ok:
            try:
                updated = update_membership_price(t, float(price))
            except Exception as exc:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить цену: {exc}")
                return

            if updated:
                QMessageBox.information(self, "Готово", "Цена обновлена")
                self.load_prices()
            else:
                QMessageBox.warning(self, "Внимание", "Тип абонемента не найден")

    def make_report(self):
        try:
            data = strategic_report()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сформировать отчёт: {exc}")
            return

        lines = [f"{k}: {v}" for k, v in data.items()]
        self.report_text.setText("\n".join(lines))

    def hire(self):
        last, ok = QInputDialog.getText(self, "Найм", "Фамилия:")
        if not ok or not last.strip():
            return

        first, ok = QInputDialog.getText(self, "Найм", "Имя:")
        if not ok or not first.strip():
            return

        middle, _ = QInputDialog.getText(self, "Найм", "Отчество (при наличии):")

        phone, _ = QInputDialog.getText(self, "Найм", "Телефон:")
        email, _ = QInputDialog.getText(self, "Найм", "Email:")
        login, _ = QInputDialog.getText(self, "Найм", "Логин:")
        password, _ = QInputDialog.getText(self, "Найм", "Пароль:")

        roles = ["Тренер", "Администратор"]
        role, ok = QInputDialog.getItem(self, "Найм", "Роль:", roles, editable=False)
        if not ok:
            return

        fio = " ".join([part for part in [last.strip(), first.strip(), (middle or "").strip()] if part])
        clean_login = login or "{}_{}".format(last.strip(), first.strip()).lower()
        clean_pass = password or "123"

        try:
            hire_staff(fio, phone or None, email or None, clean_login, clean_pass, role)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить сотрудника: {exc}")
            return

        QMessageBox.information(self, "Готово", "Сотрудник добавлен")
        self.load_staff()

    def fire(self):
        r = self.staff_table.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return
        user_id = int(self.staff_table.item(r, 0).text())
        try:
            removed = fire_staff(user_id)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить сотрудника: {exc}")
            return

        if removed:
            QMessageBox.information(self, "Готово", "Сотрудник удалён")
            self.load_staff()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось удалить сотрудника")
