import faulthandler
faulthandler.enable()

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox,
    QFormLayout, QTextEdit, QComboBox, QDateEdit, QTimeEdit
)
from PyQt6.QtCore import QDate
import datetime

from db import (
    get_schedule,
    enroll_client_in_class,
    get_enrollments_for_client,
    cancel_enrollment,
    cancel_personal_training,
    get_membership_for_client,
    book_personal_training,
    get_training_history,
    get_anthropometrics,
    get_notifications,
    mark_notification_read,
    get_connection,
    get_training_journal_for_client,
    get_recommendations_for_client,
)


class ClientWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.client_id = user.get('userID')
        self.current_membership = None

        self.setWindowTitle(f"Клиент: {user.get('fio', '')}")
        self.resize(900, 600)

        layout = QVBoxLayout()


        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_schedule_tab(), "Расписание")
        self.tabs.addTab(self.build_my_classes_tab(), "Мои записи")
        self.tabs.addTab(self.build_personal_training_tab(), "Персональные тренировки")
        self.tabs.addTab(self.build_visits_tab(), "Абонемент")
        self.tabs.addTab(self.build_history_tab(), "История тренировок")
        self.tabs.addTab(self.build_trainer_journal_tab(), "Записи тренера")
        self.tabs.addTab(self.build_profile_tab(), "Антропометрия")
        self.tabs.addTab(self.build_notifications_tab(), "Уведомления")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.refresh_all()


    def refresh_all(self):
        for fn in (
            self.refresh_schedule,
            self.refresh_my_enrollments,
            self.refresh_membership,
            self.refresh_history,
            self.refresh_trainer_journal,
            self.refresh_anthro,
            self.refresh_notifications,
        ):
            try:
                fn()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def text(self, table, row, col):
        item = table.item(row, col)
        return item.text() if item else None

    def membership_allows_date(self, date_str):
        m = getattr(self, 'current_membership', None) or get_membership_for_client(self.client_id)
        if not m:
            QMessageBox.warning(self, "Абонемент", "У вас нет активного абонемента")
            return False

        status = m.get('membershipStatus')
        if status != 'Активен':
            QMessageBox.warning(self, "Абонемент", "Абонемент заблокирован или неактивен")
            return False

        def parse_date(val):
            if isinstance(val, datetime.date):
                return val
            try:
                return datetime.date.fromisoformat(str(val))
            except Exception:
                return None

        target = parse_date(date_str)
        start = parse_date(m.get('startDate'))
        end = parse_date(m.get('endDate'))

        if not (target and start and end and start <= target <= end):
            QMessageBox.warning(self, "Абонемент", "Дата вне периода действия абонемента")
            return False

        visits_total = m.get('visitsTotal')
        visits_used = m.get('visitsUsed') or 0
        if visits_total not in (None, 0) and visits_used >= visits_total:
            QMessageBox.warning(self, "Абонемент", "Посещения по абонементу исчерпаны")
            return False

        return True


    def build_schedule_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)

        self.schedule_table = QTableWidget(0, 7)
        self.schedule_table.setHorizontalHeaderLabels(
            ['ID', 'Занятие', 'Тренер', 'Дата', 'Начало', 'Конец', 'Зал']
        )
        self.schedule_table.setColumnHidden(0, True)
        v.addWidget(self.schedule_table)

        b = QPushButton("Записаться")
        b.clicked.connect(self.enroll_selected)
        v.addWidget(b)
        return w

    def build_my_classes_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)

        self.my_classes_table = QTableWidget(0, 6)
        self.my_classes_table.setHorizontalHeaderLabels(
            ['ID', 'Занятие', 'Дата', 'Время', 'Статус', 'Тип']
        )
        self.my_classes_table.setColumnHidden(0, True)
        self.my_classes_table.setColumnHidden(5, True)
        v.addWidget(self.my_classes_table)

        b = QPushButton("Отменить запись")
        b.clicked.connect(self.cancel_selected)
        v.addWidget(b)
        return w

    def build_personal_training_tab(self):
        w = QWidget()
        f = QFormLayout(w)

        self.trainer_combo = QComboBox()
        f.addRow("Тренер:", self.trainer_combo)

        self.pt_date = QDateEdit(QDate.currentDate())
        f.addRow("Дата:", self.pt_date)

        self.pt_start = QTimeEdit()
        f.addRow("Начало:", self.pt_start)

        self.pt_notes = QTextEdit()
        f.addRow("Примечание:", self.pt_notes)

        b = QPushButton("Забронировать")
        b.clicked.connect(self.book_pt)
        f.addRow(b)

        self.refresh_trainers()
        return w

    def build_visits_tab(self):
        w = QWidget()
        self.membership_table = QTableWidget(0, 2)
        self.membership_table.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self.membership_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        QVBoxLayout(w).addWidget(self.membership_table)
        return w

    def build_history_tab(self):
        w = QWidget()
        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels(['Тип', 'Дата', 'Описание'])
        QVBoxLayout(w).addWidget(self.history_table)
        return w

    def build_trainer_journal_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)

        self.journal_table = QTableWidget(0, 4)
        self.journal_table.setHorizontalHeaderLabels(['Дата', 'Тренер', 'Заметки', 'Показатели'])
        v.addWidget(self.journal_table)

        self.rec_table = QTableWidget(0, 3)
        self.rec_table.setHorizontalHeaderLabels(['Дата', 'Тренер', 'Рекомендация'])
        v.addWidget(self.rec_table)

        return w

    def build_profile_tab(self):
        w = QWidget()
        self.anthro_table = QTableWidget(0, 5)
        self.anthro_table.setHorizontalHeaderLabels([
            'Дата', 'Вес', 'Рост', '% жира', 'Примечание'
        ])
        QVBoxLayout(w).addWidget(self.anthro_table)
        return w

    def build_notifications_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)

        self.notif_table = QTableWidget(0, 3)
        self.notif_table.setHorizontalHeaderLabels(['ID', 'Сообщение', 'Дата'])
        self.notif_table.setColumnHidden(0, True)
        v.addWidget(self.notif_table)

        b = QPushButton("Отметить прочитанным")
        b.clicked.connect(self.mark_notif_read)
        v.addWidget(b)
        return w


    def refresh_schedule(self):
        self.schedule_table.setRowCount(0)
        for r in get_schedule():
            row = self.schedule_table.rowCount()
            self.schedule_table.insertRow(row)
            for i, k in enumerate(
                ['classID', 'className', 'trainerName', 'classDate', 'startTime', 'endTime', 'hall']
            ):
                self.schedule_table.setItem(row, i, QTableWidgetItem(str(r.get(k, ''))))

    def enroll_selected(self):
        row = self.schedule_table.currentRow()
        if row < 0:
            return
        cid = self.text(self.schedule_table, row, 0)
        class_date = self.text(self.schedule_table, row, 3)
        if class_date and not self.membership_allows_date(class_date):
            return
        if enroll_client_in_class(self.client_id, int(cid)):
            QMessageBox.information(self, "OK", "Вы записаны")
            self.refresh_my_enrollments()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось записаться")

    def refresh_my_enrollments(self):
        self.my_classes_table.setRowCount(0)
        for r in get_enrollments_for_client(self.client_id):
            row = self.my_classes_table.rowCount()
            self.my_classes_table.insertRow(row)
            for i, k in enumerate(['classID', 'className', 'classDate', 'startTime', 'status', 'type']):
                self.my_classes_table.setItem(row, i, QTableWidgetItem(str(r.get(k, ''))))

    def cancel_selected(self):
        row = self.my_classes_table.currentRow()
        if row < 0:
            return

        cid = self.text(self.my_classes_table, row, 0)
        rtype = self.text(self.my_classes_table, row, 5)

        if rtype == 'group':
            ok = cancel_enrollment(self.client_id, int(cid))
        elif rtype == 'pt':
            ok = cancel_personal_training(int(cid))
        else:
            ok = False

        if ok:
            QMessageBox.information(self, "OK", "Отменено")
            self.refresh_my_enrollments()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось отменить")

    def refresh_trainers(self):
        import MySQLdb.cursors
        conn = get_connection()
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT userID, CONCAT_WS(' ', lastName, firstName, middleName) AS fio
            FROM Users
            WHERE userType='Тренер'
            ORDER BY lastName, firstName
        """)
        self.trainer_combo.clear()
        for r in cur.fetchall():
            self.trainer_combo.addItem(r['fio'], r['userID'])
        conn.close()

    def book_pt(self):
        trainer_id = self.trainer_combo.currentData()
        start = self.pt_start.time()
        end = start.addSecs(3600)

        date_str = self.pt_date.date().toString("yyyy-MM-dd")
        if not self.membership_allows_date(date_str):
            return

        ok = book_personal_training(
            self.client_id,
            trainer_id,
            date_str,
            start.toString("HH:mm:ss"),
            end.toString("HH:mm:ss"),
            self.pt_notes.toPlainText()
        )

        if ok:
            QMessageBox.information(self, "OK", "Тренировка забронирована")
            self.refresh_my_enrollments()
        else:
            QMessageBox.warning(self, "Ошибка", "В это время тренировка невозможна")

    def refresh_membership(self):
        m = get_membership_for_client(self.client_id)
        self.current_membership = m
        self.membership_table.setRowCount(0)
        if not m:
            self.membership_table.setRowCount(1)
            self.membership_table.setItem(0, 0, QTableWidgetItem("Абонемент"))
            self.membership_table.setItem(0, 1, QTableWidgetItem("Отсутствует"))
            return

        rows = [
            ("Тип", m['membershipType']),
            ("Начало", m['startDate']),
            ("Окончание", m['endDate']),
            ("Всего", m['visitsTotal']),
            ("Использовано", m['visitsUsed']),
            ("Статус", m['membershipStatus']),
        ]

        self.membership_table.setRowCount(len(rows))
        for i, (k, v) in enumerate(rows):
            self.membership_table.setItem(i, 0, QTableWidgetItem(k))
            self.membership_table.setItem(i, 1, QTableWidgetItem(str(v)))

    def refresh_history(self):
        self.history_table.setRowCount(0)
        for r in get_training_history(self.client_id):
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            for i, k in enumerate(['trainingType', 'date', 'description']):
                self.history_table.setItem(row, i, QTableWidgetItem(str(r.get(k, ''))))

    def refresh_trainer_journal(self):
        self.journal_table.setRowCount(0)
        for r in get_training_journal_for_client(self.client_id):
            row = self.journal_table.rowCount()
            self.journal_table.insertRow(row)
            for i, k in enumerate(['journalDate', 'trainerName', 'notes', 'metrics']):
                self.journal_table.setItem(row, i, QTableWidgetItem(str(r.get(k, ''))))

        self.rec_table.setRowCount(0)
        for r in get_recommendations_for_client(self.client_id):
            row = self.rec_table.rowCount()
            self.rec_table.insertRow(row)
            for i, k in enumerate(['createdAt', 'trainerName', 'text']):
                self.rec_table.setItem(row, i, QTableWidgetItem(str(r.get(k, ''))))

    def refresh_anthro(self):
        self.anthro_table.setRowCount(0)
        for r in get_anthropometrics(self.client_id):
            row = self.anthro_table.rowCount()
            self.anthro_table.insertRow(row)
            for i, k in enumerate(['recordDate', 'weight', 'height', 'bodyFat', 'notes']):
                self.anthro_table.setItem(row, i, QTableWidgetItem(str(r.get(k, ''))))

    def refresh_notifications(self):
        self.notif_table.setRowCount(0)
        for r in get_notifications(self.client_id):
            row = self.notif_table.rowCount()
            self.notif_table.insertRow(row)
            self.notif_table.setItem(row, 0, QTableWidgetItem(str(r['notifID'])))
            self.notif_table.setItem(row, 1, QTableWidgetItem(r['message']))
            self.notif_table.setItem(row, 2, QTableWidgetItem(str(r['createdAt'])))

    def mark_notif_read(self):
        row = self.notif_table.currentRow()
        nid = self.text(self.notif_table, row, 0)
        if nid:
            mark_notification_read(int(nid))
            self.refresh_notifications()
