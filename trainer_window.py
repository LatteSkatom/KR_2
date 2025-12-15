# trainer_window.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QComboBox, QTextEdit, QDateEdit, QTimeEdit, QFormLayout, QLineEdit, QTabWidget
from PyQt6.QtCore import QDate
import MySQLdb.cursors
from db import get_trainer_schedule, get_enrolled_for_class, mark_attendance, add_training_journal, get_training_journal_for_client, add_recommendation, block_trainer_time, get_clients

class TrainerWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.trainer_id = user['userID']
        self.setWindowTitle(f"Тренер: {user['fio']}")
        self.resize(900,600)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"<h2>Панель тренера — {user['fio']}</h2>"))

        tabs = QTabWidget()

        # расписание
        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout()
        schedule_layout.addWidget(QLabel("<b>Моё расписание</b>"))
        self.schedule_table = QTableWidget(0,6)
        self.schedule_table.setHorizontalHeaderLabels(['ID','Занятие','Дата','Начало','Конец','Зал'])
        schedule_layout.addWidget(self.schedule_table)

        btns = QHBoxLayout()
        self.btn_load_schedule = QPushButton("Загрузить расписание")
        self.btn_load_schedule.clicked.connect(self.load_schedule)
        btns.addWidget(self.btn_load_schedule)

        self.btn_view_enrolled = QPushButton("Показать записавшихся")
        self.btn_view_enrolled.clicked.connect(self.show_enrolled_for_selected)
        btns.addWidget(self.btn_view_enrolled)

        schedule_layout.addLayout(btns)

        schedule_layout.addWidget(QLabel("<b>Записавшиеся на выделенное занятие</b>"))
        self.enrolled_table = QTableWidget(0,4)
        self.enrolled_table.setHorizontalHeaderLabels(['ID','Клиент ID','ФИО','Присутствие'])
        schedule_layout.addWidget(self.enrolled_table)

        att_buttons = QHBoxLayout()
        self.btn_mark_present = QPushButton("Отметить присутствие")
        self.btn_mark_present.clicked.connect(self.mark_selected_present)
        att_buttons.addWidget(self.btn_mark_present)
        schedule_layout.addLayout(att_buttons)
        schedule_tab.setLayout(schedule_layout)
        tabs.addTab(schedule_tab, "Расписание")

        # журнал тренера / рекомендации
        journal_tab = QWidget()
        journal_layout = QVBoxLayout()
        journal_layout.addWidget(QLabel("<b>Журнал персональных тренировок / рекомендации</b>"))
        j_layout = QHBoxLayout()
        self.client_combo = QComboBox()
        rows = get_clients(1000)
        for r in rows:
            self.client_combo.addItem(f"{r['fio']} (id:{r['userID']})", r['userID'])
        j_layout.addWidget(self.client_combo)
        self.journal_notes = QTextEdit()
        j_layout.addWidget(self.journal_notes)
        self.journal_metrics = QTextEdit()
        j_layout.addWidget(self.journal_metrics)
        self.btn_add_journal = QPushButton("Добавить в журнал")
        self.btn_add_journal.clicked.connect(self.add_journal_entry)
        j_layout.addWidget(self.btn_add_journal)
        journal_layout.addLayout(j_layout)

        rec_layout = QHBoxLayout()
        self.rec_client_combo = QComboBox()
        for r in rows:
            self.rec_client_combo.addItem(f"{r['fio']} (id:{r['userID']})", r['userID'])
        rec_layout.addWidget(self.rec_client_combo)
        self.rec_text = QTextEdit()
        rec_layout.addWidget(self.rec_text)
        self.btn_add_rec = QPushButton("Добавить рекомендацию")
        self.btn_add_rec.clicked.connect(self.add_rec)
        rec_layout.addWidget(self.btn_add_rec)
        journal_layout.addLayout(rec_layout)
        journal_tab.setLayout(journal_layout)
        tabs.addTab(journal_tab, "Журнал")

        # блокировка времени
        block_tab = QWidget()
        block_layout = QVBoxLayout()
        block_layout.addWidget(QLabel("<b>Блокировка времени</b>"))
        bform = QFormLayout()
        self.block_date = QDateEdit(); self.block_date.setDate(QDate.currentDate())
        self.block_start = QTimeEdit(); self.block_end = QTimeEdit()
        self.block_reason = QLineEdit()
        bform.addRow("Дата:", self.block_date)
        bform.addRow("Начало:", self.block_start)
        bform.addRow("Конец:", self.block_end)
        bform.addRow("Причина:", self.block_reason)
        self.btn_block_time = QPushButton("Заблокировать")
        self.btn_block_time.clicked.connect(self.do_block_time)
        bform.addRow(self.btn_block_time)
        block_layout.addLayout(bform)
        block_tab.setLayout(block_layout)
        tabs.addTab(block_tab, "Блокировки")

        layout.addWidget(tabs)
        self.setLayout(layout)
        self.load_schedule()

    def load_schedule(self):
        rows = get_trainer_schedule(self.trainer_id)
        self.schedule_table.setRowCount(0)
        for r in rows:
            row = self.schedule_table.rowCount()
            self.schedule_table.insertRow(row)
            self.schedule_table.setItem(row,0, QTableWidgetItem(str(r['classID'])))
            self.schedule_table.setItem(row,1, QTableWidgetItem(r.get('className') or ''))
            self.schedule_table.setItem(row,2, QTableWidgetItem(str(r.get('classDate'))))
            self.schedule_table.setItem(row,3, QTableWidgetItem(str(r.get('startTime'))))
            self.schedule_table.setItem(row,4, QTableWidgetItem(str(r.get('endTime'))))
            self.schedule_table.setItem(row,5, QTableWidgetItem(r.get('hall') or ''))

    def show_enrolled_for_selected(self):
        sel = self.schedule_table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите занятие")
            return
        class_id = int(self.schedule_table.item(sel,0).text())
        rows = get_enrolled_for_class(class_id)
        self.enrolled_table.setRowCount(0)
        for r in rows:
            row = self.enrolled_table.rowCount()
            self.enrolled_table.insertRow(row)
            self.enrolled_table.setItem(row,0, QTableWidgetItem(str(r.get('enrollmentID'))))
            self.enrolled_table.setItem(row,1, QTableWidgetItem(str(r.get('clientID'))))
            self.enrolled_table.setItem(row,2, QTableWidgetItem(r.get('fio') or ''))
            # check attendance status
            self.enrolled_table.setItem(row,3, QTableWidgetItem("—"))

    def mark_selected_present(self):
        sel = self.enrolled_table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента в списке")
            return
        class_row_sel = self.schedule_table.currentRow()
        if class_row_sel < 0:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите занятие в расписании")
            return
        class_id = int(self.schedule_table.item(class_row_sel,0).text())
        client_id = int(self.enrolled_table.item(sel,1).text())
        mark_attendance(class_id, client_id, True)
        QMessageBox.information(self, "Готово", "Отмечено как присутствовавший")
        self.show_enrolled_for_selected()

    def add_journal_entry(self):
        client_id = self.client_combo.currentData()
        notes = self.journal_notes.toPlainText()
        metrics = self.journal_metrics.toPlainText()
        add_training_journal(self.trainer_id, client_id, QDate.currentDate().toString("yyyy-MM-dd"), notes, metrics)
        QMessageBox.information(self, "Готово", "Запись в журнал добавлена")

    def add_rec(self):
        client_id = self.rec_client_combo.currentData()
        text = self.rec_text.toPlainText()
        add_recommendation(self.trainer_id, client_id, text)
        QMessageBox.information(self, "Готово", "Рекомендация отправлена")

    def do_block_time(self):
        d = self.block_date.date().toString("yyyy-MM-dd")
        st = self.block_start.time().toString("HH:mm:ss")
        en = self.block_end.time().toString("HH:mm:ss")
        reason = self.block_reason.text()
        block_trainer_time(self.trainer_id, d, st, en, reason)
        QMessageBox.information(self, "Готово", "Время заблокировано")
