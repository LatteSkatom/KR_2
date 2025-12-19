from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QFormLayout, QMessageBox, QDateEdit, QSpinBox, QTextEdit, QComboBox, QFileDialog, QTabWidget, QTimeEdit
from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtCore import QDate
import datetime
import MySQLdb.cursors

from db import register_client, get_clients, create_membership, extend_membership, block_membership
from db import add_complaint, get_complaints, update_complaint_status, add_promotion, get_promotions, set_promotion_active, sales_report_by_month
from db import get_trainers, add_group_class, get_schedule

class AdminWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.admin_id = user['userID']
        self.setWindowTitle(f"Администратор: {user['fio']}")
        self.resize(1000,700)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h2>Панель администратора</h2>"))

        tabs = QTabWidget()

        clients_tab = QWidget()
        clients_layout = QVBoxLayout()
        top = QHBoxLayout()
        self.btn_refresh_clients = QPushButton("Обновить список клиентов")
        self.btn_refresh_clients.clicked.connect(self.load_clients)
        top.addWidget(self.btn_refresh_clients)

        self.btn_register = QPushButton("Зарегистрировать клиента")
        self.btn_register.clicked.connect(self.show_register_dialog)
        top.addWidget(self.btn_register)

        self.btn_membership = QPushButton("Создать / продлить абонемент")
        self.btn_membership.clicked.connect(self.show_membership_dialog)
        top.addWidget(self.btn_membership)

        self.btn_block = QPushButton("Блокировать абонемент")
        self.btn_block.clicked.connect(self.block_selected_membership)
        top.addWidget(self.btn_block)

        self.btn_sales = QPushButton("Отчёт по продажам (год)")
        self.btn_sales.clicked.connect(self.show_sales_report)
        top.addWidget(self.btn_sales)
        clients_layout.addLayout(top)

        self.clients_table = QTableWidget(0,6)
        self.clients_table.setHorizontalHeaderLabels(['ID','ФИО','Телефон','Email','Логин','Тип'])
        clients_layout.addWidget(self.clients_table)

        print_buttons = QHBoxLayout()
        self.btn_print_card = QPushButton("Печать клубной карты для клиента")
        self.btn_print_card.clicked.connect(self.print_card)
        print_buttons.addWidget(self.btn_print_card)
        self.btn_print_receipt = QPushButton("Печать квитанции (чек)")
        self.btn_print_receipt.clicked.connect(self.print_receipt)
        print_buttons.addWidget(self.btn_print_receipt)
        clients_layout.addLayout(print_buttons)
        clients_tab.setLayout(clients_layout)
        tabs.addTab(clients_tab, "Клиенты")

        complaints_tab = QWidget()
        comp_layout = QVBoxLayout()
        comp_layout.addWidget(QLabel("<h3>Жалобы и пожелания</h3>"))
        self.complaints_table = QTableWidget(0,5)
        self.complaints_table.setHorizontalHeaderLabels(['ID','Клиент','Тема','Дата','Статус'])
        comp_layout.addWidget(self.complaints_table)

        comp_buttons = QHBoxLayout()
        self.btn_refresh_complaints = QPushButton("Обновить жалобы")
        self.btn_refresh_complaints.clicked.connect(self.load_complaints)
        comp_buttons.addWidget(self.btn_refresh_complaints)
        self.btn_mark_comp = QPushButton("Пометить как обработано")
        self.btn_mark_comp.clicked.connect(self.mark_complaint_handled)
        comp_buttons.addWidget(self.btn_mark_comp)
        comp_layout.addLayout(comp_buttons)
        complaints_tab.setLayout(comp_layout)
        tabs.addTab(complaints_tab, "Жалобы")

        promos_tab = QWidget()
        promos_layout = QVBoxLayout()
        promos_layout.addWidget(QLabel("<h3>Акции и скидки</h3>"))
        promo_layout = QHBoxLayout()
        self.promo_title = QLineEdit(); self.promo_title.setPlaceholderText("Название акции")
        promo_layout.addWidget(self.promo_title)
        self.promo_disc = QSpinBox(); self.promo_disc.setRange(0,100); self.promo_disc.setSuffix("%")
        promo_layout.addWidget(self.promo_disc)
        self.promo_start = QDateEdit(); self.promo_start.setDate(QDate.currentDate())
        promo_layout.addWidget(self.promo_start)
        self.promo_end = QDateEdit(); self.promo_end.setDate(QDate.currentDate().addDays(30))
        promo_layout.addWidget(self.promo_end)
        self.promo_desc = QLineEdit(); self.promo_desc.setPlaceholderText("Краткое описание")
        promo_layout.addWidget(self.promo_desc)
        self.btn_add_promo = QPushButton("Добавить акцию")
        self.btn_add_promo.clicked.connect(self.add_promo)
        promo_layout.addWidget(self.btn_add_promo)
        promos_layout.addLayout(promo_layout)

        self.promo_table = QTableWidget(0,5)
        self.promo_table.setHorizontalHeaderLabels(['ID','Название','Описание','Скидка','Активна'])
        promos_layout.addWidget(self.promo_table)

        promo_buttons = QHBoxLayout()
        self.btn_refresh_promos = QPushButton("Обновить акции")
        self.btn_refresh_promos.clicked.connect(self.load_promos)
        promo_buttons.addWidget(self.btn_refresh_promos)
        self.btn_toggle_promo = QPushButton("Вкл/Выкл выделенную акцию")
        self.btn_toggle_promo.clicked.connect(self.toggle_promo)
        promo_buttons.addWidget(self.btn_toggle_promo)
        promos_layout.addLayout(promo_buttons)
        promos_tab.setLayout(promos_layout)
        tabs.addTab(promos_tab, "Акции")

        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout()
        schedule_layout.addWidget(QLabel("<h3>Расписание тренировок</h3>"))

        form = QFormLayout()
        self.class_name = QLineEdit(); form.addRow("Название занятия:", self.class_name)

        self.trainer_combo = QComboBox(); form.addRow("Тренер:", self.trainer_combo)

        self.class_date = QDateEdit(); self.class_date.setDate(QDate.currentDate()); form.addRow("Дата:", self.class_date)

        self.start_time = QTimeEdit(); form.addRow("Начало:", self.start_time)
        self.end_time = QTimeEdit(); form.addRow("Конец:", self.end_time)

        self.hall_edit = QLineEdit(); form.addRow("Зал:", self.hall_edit)

        self.max_participants = QSpinBox(); self.max_participants.setRange(1, 200); self.max_participants.setValue(20)
        form.addRow("Макс. участников:", self.max_participants)

        self.btn_add_class = QPushButton("Добавить в расписание")
        self.btn_add_class.clicked.connect(self.add_class_to_schedule)
        form.addRow(self.btn_add_class)

        schedule_layout.addLayout(form)

        self.schedule_table = QTableWidget(0, 7)
        self.schedule_table.setHorizontalHeaderLabels(['ID', 'Название', 'Тренер', 'Дата', 'Начало', 'Конец', 'Зал'])
        schedule_layout.addWidget(self.schedule_table)

        btn_refresh_schedule = QPushButton("Обновить расписание")
        btn_refresh_schedule.clicked.connect(self.load_schedule)
        schedule_layout.addWidget(btn_refresh_schedule)

        schedule_tab.setLayout(schedule_layout)
        tabs.addTab(schedule_tab, "Расписание")

        layout.addWidget(tabs)
        self.setLayout(layout)

        self.load_clients()
        self.load_complaints()
        self.load_promos()
        self.load_trainers()
        self.load_schedule()

    def load_clients(self):
        rows = get_clients(1000)
        self.clients_table.setRowCount(0)
        for r in rows:
            row = self.clients_table.rowCount()
            self.clients_table.insertRow(row)
            self.clients_table.setItem(row,0, QTableWidgetItem(str(r['userID'])))
            self.clients_table.setItem(row,1, QTableWidgetItem(r.get('fio','')))
            self.clients_table.setItem(row,2, QTableWidgetItem(r.get('phone','')))
            self.clients_table.setItem(row,3, QTableWidgetItem(r.get('email','')))
            self.clients_table.setItem(row,4, QTableWidgetItem(r.get('login','')))
            self.clients_table.setItem(row,5, QTableWidgetItem(r.get('userType','')))

    def show_register_dialog(self):
        dlg = QWidget()
        dlg.setWindowTitle("Регистрация клиента")
        form = QFormLayout()
        fio = QLineEdit(); form.addRow("ФИО:", fio)
        phone = QLineEdit(); form.addRow("Телефон:", phone)
        email = QLineEdit(); form.addRow("Email:", email)
        login = QLineEdit(); form.addRow("Логин:", login)
        password = QLineEdit(); form.addRow("Пароль:", password)
        birth = QDateEdit(); birth.setDate(QDate.currentDate().addYears(-25)); form.addRow("Дата рождения:", birth)
        btn = QPushButton("Зарегистрировать")
        def do_reg():
            if not fio.text() or not login.text() or not password.text():
                QMessageBox.warning(dlg, "Ошибка", "Заполните обязательные поля")
                return
            new = register_client(fio.text(), phone.text(), email.text(), login.text(), password.text(), birth.date().toString("yyyy-MM-dd"))
            QMessageBox.information(dlg, "Готово", f"Клиент создан, id={new}")
            dlg.close()
            self.load_clients()
        btn.clicked.connect(do_reg)
        form.addRow(btn)
        dlg.setLayout(form)
        dlg.show()

    def show_membership_dialog(self):
        dlg = QWidget(); dlg.setWindowTitle("Создать/продлить абонемент")
        f = QFormLayout()
        client_combo = QComboBox()
        rows = get_clients(500)
        for r in rows:
            client_combo.addItem(f"{r['fio']} (id:{r['userID']})", r['userID'])
        f.addRow("Клиент:", client_combo)
        typ = QLineEdit(); f.addRow("Тип абонемента:", typ)
        start = QDateEdit(); start.setDate(QDate.currentDate()); f.addRow("Дата начала:", start)
        end = QDateEdit(); end.setDate(QDate.currentDate().addMonths(1)); f.addRow("Дата конца:", end)
        visits = QSpinBox(); visits.setValue(999); f.addRow("Всего посещений:", visits)
        cost = QLineEdit(); f.addRow("Цена:", cost)
        btn = QPushButton("Создать")
        def do_create():
            cid = client_combo.currentData()
            create_membership(cid, typ.text() or 'Месячный', start.date().toString("yyyy-MM-dd"), end.date().toString("yyyy-MM-dd"), visits.value(), 0, 'Все зоны', 'Активен', float(cost.text() or 0), self.admin_id)
            QMessageBox.information(dlg, "Готово", "Абонемент создан")
            dlg.close()
        btn.clicked.connect(do_create)
        f.addRow(btn)
        dlg.setLayout(f)
        dlg.show()

    def block_selected_membership(self):
        sel = self.clients_table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента")
            return
        client_id = int(self.clients_table.item(sel,0).text())
        import MySQLdb.cursors
        conn = None
        try:
            from db import get_connection
            conn = get_connection()
            cur = conn.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT membershipID FROM Memberships WHERE clientID=%s ORDER BY endDate DESC LIMIT 1", (client_id,))
            row = cur.fetchone()
            if not row:
                QMessageBox.warning(self, "Ошибка", "У клиента нет абонемента")
                return
            membership_id = row['membershipID']
            block_membership(membership_id)
            QMessageBox.information(self, "Готово", "Абонемент заблокирован")
        finally:
            if conn:
                conn.close()

    def load_complaints(self):
        rows = get_complaints()
        self.complaints_table.setRowCount(0)
        for r in rows:
            row = self.complaints_table.rowCount()
            self.complaints_table.insertRow(row)
            self.complaints_table.setItem(row,0, QTableWidgetItem(str(r['complaintID'])))
            self.complaints_table.setItem(row,1, QTableWidgetItem(r.get('fio') or ''))
            self.complaints_table.setItem(row,2, QTableWidgetItem(r.get('subject') or ''))
            self.complaints_table.setItem(row,3, QTableWidgetItem(str(r.get('createdAt'))))
            self.complaints_table.setItem(row,4, QTableWidgetItem(r.get('status') or ''))

    def mark_complaint_handled(self):
        sel = self.complaints_table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите жалобу")
            return
        comp_id = int(self.complaints_table.item(sel,0).text())
        update_complaint_status(comp_id, "Обработано")
        QMessageBox.information(self, "Готово", "Жалоба помечена как обработанная")
        self.load_complaints()

    def add_promo(self):
        title = self.promo_title.text().strip()
        desc = self.promo_desc.text().strip()
        disc = self.promo_disc.value()
        start = self.promo_start.date().toString("yyyy-MM-dd")
        end = self.promo_end.date().toString("yyyy-MM-dd")
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите название акции")
            return
        add_promotion(title, desc, disc, start, end, 1)
        QMessageBox.information(self, "Готово", "Акция добавлена")
        self.load_promos()

    def load_promos(self):
        rows = get_promotions(False)
        self.promo_table.setRowCount(0)
        for r in rows:
            row = self.promo_table.rowCount()
            self.promo_table.insertRow(row)
            self.promo_table.setItem(row,0, QTableWidgetItem(str(r['promoID'])))
            self.promo_table.setItem(row,1, QTableWidgetItem(r.get('title') or ''))
            self.promo_table.setItem(row,2, QTableWidgetItem(r.get('description') or ''))
            self.promo_table.setItem(row,3, QTableWidgetItem(str(r.get('discount_percent') or 0)))
            self.promo_table.setItem(row,4, QTableWidgetItem('Да' if r.get('active')==1 else 'Нет'))

    def toggle_promo(self):
        sel = self.promo_table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите акцию")
            return
        pid = int(self.promo_table.item(sel,0).text())
        current = self.promo_table.item(sel,4).text()
        set_promotion_active(pid, 0 if current=='Да' else 1)
        QMessageBox.information(self, "Готово", "Состояние акции изменено")
        self.load_promos()

    def load_trainers(self):
        self.trainer_combo.clear()
        for t in get_trainers():
            self.trainer_combo.addItem(f"{t['fio']} (id:{t['userID']})", t['userID'])

    def load_schedule(self):
        self.schedule_table.setRowCount(0)
        for r in get_schedule():
            row = self.schedule_table.rowCount()
            self.schedule_table.insertRow(row)
            for i, k in enumerate(['classID','className','trainerName','classDate','startTime','endTime','hall']):
                self.schedule_table.setItem(row, i, QTableWidgetItem(str(r.get(k,''))))

    def add_class_to_schedule(self):
        name = self.class_name.text().strip()
        trainer_id = self.trainer_combo.currentData()
        date = self.class_date.date().toString("yyyy-MM-dd")
        start = self.start_time.time().toString("HH:mm:ss")
        end = self.end_time.time().toString("HH:mm:ss")
        hall = self.hall_edit.text().strip()
        maxp = self.max_participants.value()

        if not name or trainer_id is None:
            QMessageBox.warning(self, "Ошибка", "Введите название и выберите тренера")
            return

        add_group_class(name, trainer_id, date, start, end, hall, maxp)
        QMessageBox.information(self, "Готово", "Занятие добавлено в расписание")
        self.load_schedule()

    def print_card(self):
        sel = self.clients_table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента")
            return
        client_id = int(self.clients_table.item(sel,0).text())
        fio = self.clients_table.item(sel,1).text()
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить карту как", f"card_{client_id}.txt", "Text files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Клубная карта\nID: {client_id}\nФИО: {fio}\nДата выдачи: {datetime.date.today()}\n")
            QMessageBox.information(self, "Готово", f"Карта сохранена в {filename}")

    def print_receipt(self):
        sel = self.clients_table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента")
            return
        client_id = int(self.clients_table.item(sel,0).text())
        import MySQLdb.cursors
        from db import get_connection
        conn = get_connection()
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM Memberships WHERE clientID=%s ORDER BY startDate DESC LIMIT 1", (client_id,))
        m = cur.fetchone()
        conn.close()
        if not m:
            QMessageBox.warning(self, "Ошибка", "У клиента нет абонементов")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить чек как", f"receipt_{client_id}.txt", "Text files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("Квитанция\n")
                f.write(f"Клиент: {m.get('clientID')}\nТип: {m.get('membershipType')}\nЦена: {m.get('cost')}\nПериод: {m.get('startDate')} — {m.get('endDate')}\n")
            QMessageBox.information(self, "Готово", f"Чек сохранён: {filename}")

    def show_sales_report(self):
        year, ok = QInputDialog.getInt(self, "Год", "Введите год для отчёта", value=2024, min=2000, max=2100)
        if not ok:
            return
        rows = sales_report_by_month(year)
        txt = f"Отчёт продаж за {year}\n\n"
        for r in rows:
            txt += f"{r['month']}: продано {r['sold_count']}, сумма {r['total_sum']}\n"
        QMessageBox.information(self, "Отчёт", txt)
