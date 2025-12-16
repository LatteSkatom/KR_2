import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from login_window import LoginWindow
from client_window import ClientWindow
from trainer_window import TrainerWindow
from admin_window import AdminWindow
from director_window import DirectorWindow

def on_login(user):
    role = user.get('userType')

    if role == 'Клиент':
        w = ClientWindow(user)
    elif role == 'Тренер':
        w = TrainerWindow(user)
    elif role == 'Администратор':
        w = AdminWindow(user)
    elif role == 'Директор':
        w = DirectorWindow(user)
    else:
        QMessageBox.critical(None, "Ошибка", "Неизвестная роль")
        return

    w.show()
    windows.append(w)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    windows = []

    def start_login():
        lw = LoginWindow(on_login)
        lw.show()
        windows.append(lw)

    try:
        start_login()
        sys.exit(app.exec())
    except Exception as e:
        print("Ошибка:", e)
        raise

