from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QMessageBox, QFormLayout, QLineEdit, QComboBox, QTextEdit
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
    fire_staff
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

    # -------- tabs --------

    def build_general_tab(self):
        w = QWidget(); v = QVBoxLayout(w)
        self.general_table = QTableWidget(0, 2)
        self.general_table.setHorizontalHeaderLabels(["Показатель", "Значение"])
        v.addWidget(self.general_table)
        return w

    def build_trainers_tab(self):
        w = QWidget(); v = QVBoxLayout(w)
        self.trainer_table = QTableWidget(0, 4)
        self.trainer_table.setHorizontalHeaderLabels([
            "Тренер", "Групповые", "Персональные", "Клиенты"
        ])
        v.addWidget(self.trainer_table)
        return w

    def build_finance_tab(self):
        w = QWidget(); v = QVBoxLayout(w)
        self.finance_table = QTableWidget(0, 3)
        self.finance_table.setHorizontalHeaderLabels([
            "Месяц", "Продано", "Выручка"
        ])
        v.addWidget(self.finance_table)
        return w

    # -------- NEW --------

    def build_prices_tab(self):
        w = QWidget(); v = QVBoxLayout(w)
        self.price_table = QTableWidget(0, 2)
        self.price_table.setHorizontalHeaderLabels(["Тип абонемента", "Цена"])
        v.addWidget(self.price_table)

        btn = QPushButton("Изменить цену")
        btn.clicked.connect(self.change_price)
        v.addWidget(btn)
        return w

    def build_report_tab(self):
        w = QWidget(); v = QVBoxLayout(w)
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        v.addWidget(self.report_text)

        btn = QPushButton("Сформировать отчёт")
        btn.clicked.connect(self.make_report)
        v.addWidget(btn)
        return w

    def build_staff_tab(self):
        w = QWidget(); v = QVBoxLayout(w)
        self.staff_table = QTableWidget(0, 3)
        self.staff_table.setHorizontalHeaderLabels(["ФИО", "Роль", "Телефон"])
        v.addWidget(self.staff_table)

        btns = QHBoxLayout()
        hire = QPushButton("Нанять")
        fire = QPushButton("Уволить")
        hire.clicked.connect(self.hire)
        fire.clicked.connect(self.fire)
        btns.addWidget(hire); btns.addWidget(fire)
        v.addLayout(btns)
        return w

    # -------- load --------

    def load_general(self):
        self.general_table.setRowCount(0)
        for k, v in director_general_stats().items():
            r = self.general_table.rowCount()
            self.general_table.insertRow(r)
            self.general_table.setItem(r, 0, QTableWidgetItem(k))
            self.general_table.setItem(r, 1, QTableWidgetItem(str(v)))

    def load_trainers(self):
        self.trainer_table.setRowCount(0)
        for rdata in director_trainer_efficiency():
            r = self.trainer_table.rowCount()
            self.trainer_table.insertRow(r)
            self.trainer_table.setItem(r, 0, QTableWidgetItem(rdata['fio']))
            self.trainer_table.setItem(r, 1, QTableWidgetItem(str(rdata['group_count'])))
            self.trainer_table.setItem(r, 2, QTableWidgetItem(str(rdata['pt_count'])))
            self.trainer_table.setItem(r, 3, QTableWidgetItem(str(rdata['clients'])))

    def load_finance(self):
        self.finance_table.setRowCount(0)
        for rdata in director_finance_stats():
            r = self.finance_table.rowCount()
            self.finance_table.insertRow(r)
            self.finance_table.setItem(r, 0, QTableWidgetItem(rdata['month']))
            self.finance_table.setItem(r, 1, QTableWidgetItem(str(rdata['sold'])))
            self.finance_table.setItem(r, 2, QTableWidgetItem(str(rdata['total'])))

    def load_prices(self):
        self.price_table.setRowCount(0)
        for t, p in get_membership_prices():
            r = self.price_table.rowCount()
            self.price_table.insertRow(r)
            self.price_table.setItem(r, 0, QTableWidgetItem(t))
            self.price_table.setItem(r, 1, QTableWidgetItem(str(p)))

    def load_staff(self):
        self.staff_table.setRowCount(0)
        for rdata in director_staff_list():
            r = self.staff_table.rowCount()
            self.staff_table.insertRow(r)
            self.staff_table.setItem(r, 0, QTableWidgetItem(rdata['fio']))
            self.staff_table.setItem(r, 1, QTableWidgetItem(rdata['userType']))
            self.staff_table.setItem(r, 2, QTableWidgetItem(rdata.get('phone', '')))

    # -------- actions --------

    def change_price(self):
        r = self.price_table.currentRow()
        if r < 0: return
        t = self.price_table.item(r, 0).text()
        price, ok = QLineEdit.getText(self, "Цена", "Новая цена:")
        if ok:
            update_membership_price(t, float(price))
            self.load_prices()

    def make_report(self):
        self.report_text.setText(strategic_report())

    def hire(self):
        fio, ok = QLineEdit.getText(self, "Найм", "ФИО:")
        if ok:
            hire_staff(fio)
            self.load_staff()

    def fire(self):
        r = self.staff_table.currentRow()
        if r < 0: return
        fio = self.staff_table.item(r, 0).text()
        fire_staff(fio)
        self.load_staff()