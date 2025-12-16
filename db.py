import MySQLdb as mdb


def _fio_alias(column_prefix: str = "u"):
    return f"CONCAT_WS(' ', {column_prefix}.lastName, {column_prefix}.firstName, {column_prefix}.middleName)"


def split_fio(fio: str):
    parts = (fio or "").strip().split()
    last = parts[0] if len(parts) > 0 else ""
    first = parts[1] if len(parts) > 1 else ""
    middle = " ".join(parts[2:]) if len(parts) > 2 else ""
    return last, first, middle

def get_connection():
    return mdb.connect(
        host='localhost',
        user='root',
        passwd='',
        db='fitness'
    )

def check_user(login: str, password: str):
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute(
        f"""
        SELECT u.*, {_fio_alias()} AS fio
        FROM Users u
        WHERE login=%s AND password=%s
        """,
        (login, password)
    )
    row = cur.fetchone()
    conn.close()
    return row

def get_schedule():
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute(f"""
        SELECT g.*, {_fio_alias('u')} AS trainerName
        FROM GroupClasses g
        LEFT JOIN Users u ON g.trainerID = u.userID
        ORDER BY g.classDate, g.startTime
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_enrollments_for_client(client_id):
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)

    cur.execute("""
        (
            SELECT 
                g.classID AS classID,
                g.className AS className,
                g.classDate AS classDate,
                g.startTime AS startTime,
                'Записан' AS status,
                'group' AS type
            FROM Enrollments e
            JOIN GroupClasses g ON e.classID = g.classID
            WHERE e.clientID=%s
        )
        UNION ALL
        (
            SELECT
                pt.trainingID AS classID,
                CONCAT('Персональная тренировка с ', {_fio_alias('u')}) AS className,
                pt.trainingDate AS classDate,
                pt.startTime AS startTime,
                'Записан' AS status,
                'pt' AS type
            FROM PersonalTraining pt
            JOIN Users u ON u.userID = pt.trainerID
            WHERE pt.clientID=%s
        )
        ORDER BY classDate, startTime
    """, (client_id, client_id))

    rows = cur.fetchall()
    conn.close()
    return rows



def _membership_is_active_for_date(client_id, target_date):
    """Check that the client has an active membership covering the target date."""
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute(
        """
        SELECT *
        FROM Memberships
        WHERE clientID=%s
        ORDER BY endDate DESC
        LIMIT 1
        """,
        (client_id,),
    )
    membership = cur.fetchone()
    conn.close()

    if not membership:
        return False

    if membership.get("membershipStatus") != "Активен":
        return False

    start_date = membership.get("startDate")
    end_date = membership.get("endDate")

    if not (start_date and end_date):
        return False

    if not (start_date <= target_date <= end_date):
        return False

    visits_total = membership.get("visitsTotal")
    visits_used = membership.get("visitsUsed") or 0
    if visits_total is not None and visits_total > 0 and visits_used >= visits_total:
        return False

    return True


def enroll_client_in_class(client_id, class_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT classDate FROM GroupClasses WHERE classID=%s", (class_id,))
    date_row = cur.fetchone()
    if not date_row:
        conn.close()
        return False
    class_date = date_row[0]

    if not _membership_is_active_for_date(client_id, class_date):
        conn.close()
        return False

    cur.execute("SELECT maxParticipants FROM GroupClasses WHERE classID=%s", (class_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    maxp = row[0]

    cur.execute("SELECT COUNT(*) FROM Enrollments WHERE classID=%s", (class_id,))
    cnt = cur.fetchone()[0]
    if cnt >= maxp:
        conn.close()
        return False

    cur.execute("SELECT * FROM Enrollments WHERE classID=%s AND clientID=%s", (class_id, client_id))
    if cur.fetchone():
        conn.close()
        return False

    cur.execute("INSERT INTO Enrollments (classID, clientID) VALUES (%s,%s)", (class_id, client_id))
    conn.commit()
    conn.close()
    return True

def cancel_enrollment(client_id, class_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Enrollments WHERE classID=%s AND clientID=%s", (class_id, client_id))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_membership_for_client(client_id):
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute("""
        SELECT *
        FROM Memberships
        WHERE clientID=%s
        ORDER BY endDate DESC
        LIMIT 1
    """, (client_id,))
    row = cur.fetchone()
    conn.close()
    return row

def _trainer_is_blocked(trainer_id, date, start_time, end_time):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 1
        FROM TrainerBlockedTime
        WHERE trainerID=%s
          AND blockDate=%s
          AND NOT (%s >= endTime OR %s <= startTime)
        LIMIT 1
        """,
        (trainer_id, date, start_time, end_time),
    )
    blocked = cur.fetchone() is not None
    conn.close()
    return blocked


def book_personal_training(client_id, trainer_id, date, start_time, end_time, notes):
    conn = get_connection()
    cur = conn.cursor()

    if not _membership_is_active_for_date(client_id, date):
        conn.close()
        return False

    cur.execute("""
        SELECT 1 FROM PersonalTraining
        WHERE clientID=%s
          AND trainingDate=%s
          AND NOT (%s >= endTime OR %s <= startTime)
    """, (client_id, date, start_time, end_time))

    if cur.fetchone():
        conn.close()
        return False

    cur.execute("""
        SELECT 1 FROM PersonalTraining
        WHERE trainerID=%s
          AND trainingDate=%s
          AND NOT (%s >= endTime OR %s <= startTime)
    """, (trainer_id, date, start_time, end_time))

    if cur.fetchone():
        conn.close()
        return False

    if _trainer_is_blocked(trainer_id, date, start_time, end_time):
        conn.close()
        return False

    cur.execute("""
        INSERT INTO PersonalTraining
        (clientID, trainerID, trainingDate, startTime, endTime, notes)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (client_id, trainer_id, date, start_time, end_time, notes))

    conn.commit()
    conn.close()
    return True



def cancel_personal_training(training_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM PersonalTraining
        WHERE trainingID=%s
    """, (training_id,))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0



def get_training_history(client_id):
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute("SELECT * FROM TrainingHistory WHERE clientID=%s ORDER BY date DESC", (client_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_anthropometrics(client_id):
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute("""
        SELECT *
        FROM Anthropometrics
        WHERE clientID=%s
        ORDER BY recordDate DESC
    """, (client_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_notifications(client_id):
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute("SELECT * FROM Notifications WHERE clientID=%s ORDER BY createdAt DESC", (client_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_notification_read(notif_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Notifications SET isRead=1 WHERE notifID=%s", (notif_id,))
    conn.commit()
    conn.close()
    return True



import MySQLdb.cursors
from typing import List, Dict

def register_client(fio, phone, email, login, password, birthDate=None):
    conn = get_connection()
    cur = conn.cursor()
    last, first, middle = split_fio(fio)
    cur.execute("""
        INSERT INTO Users (lastName, firstName, middleName, phone, email, login, password, userType, birthDate)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'Клиент',%s)
    """, (last, first, middle, phone, email, login, password, birthDate))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

def create_membership(client_id, membershipType, startDate, endDate, visitsTotal, visitsUsed, zones, status, cost, admin_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Memberships (clientID, membershipType, startDate, endDate, visitsTotal, visitsUsed, zones, membershipStatus, cost, adminID)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (client_id, membershipType, startDate, endDate, visitsTotal, visitsUsed, zones, status, cost, admin_id))
    conn.commit()
    inserted = cur.lastrowid
    conn.close()
    return inserted

def extend_membership(membership_id, new_end_date, add_visits=0):
    conn = get_connection()
    cur = conn.cursor()
    if add_visits:
        cur.execute("UPDATE Memberships SET endDate=%s, visitsTotal=visitsTotal+%s WHERE membershipID=%s", (new_end_date, add_visits, membership_id))
    else:
        cur.execute("UPDATE Memberships SET endDate=%s WHERE membershipID=%s", (new_end_date, membership_id))
    conn.commit()
    conn.close()
    return True

def block_membership(membership_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Memberships SET membershipStatus='Заблокирован' WHERE membershipID=%s", (membership_id,))
    conn.commit()
    conn.close()
    return True

def get_clients(limit=200):
    conn = get_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        f"""
        SELECT userID, lastName, firstName, middleName, phone, email, login, userType, birthDate,
               {_fio_alias()} AS fio
        FROM Users u
        ORDER BY lastName, firstName
        LIMIT %s
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def add_complaint(client_id, subject, message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Complaints (clientID, subject, message) VALUES (%s,%s,%s)", (client_id, subject, message))
    conn.commit()
    conn.close()
    return True

def get_complaints(status=None):
    conn = get_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    if status:
        cur.execute(
            f"""
            SELECT c.*, {_fio_alias('u')} AS fio
            FROM Complaints c
            LEFT JOIN Users u ON c.clientID=u.userID
            WHERE c.status=%s
            ORDER BY c.createdAt DESC
            """,
            (status,),
        )
    else:
        cur.execute(
            f"""
            SELECT c.*, {_fio_alias('u')} AS fio
            FROM Complaints c
            LEFT JOIN Users u ON c.clientID=u.userID
            ORDER BY c.createdAt DESC
            """
        )
    rows = cur.fetchall()
    conn.close()
    return rows

def update_complaint_status(complaint_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Complaints SET status=%s WHERE complaintID=%s", (status, complaint_id))
    conn.commit()
    conn.close()
    return True

def add_promotion(title, description, discount_percent, startDate, endDate, active=1):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Promotions (title, description, discount_percent, startDate, endDate, active) VALUES (%s,%s,%s,%s,%s,%s)",
                (title, description, discount_percent, startDate, endDate, active))
    conn.commit()
    conn.close()
    return True

def get_promotions(active_only=True):
    conn = get_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    if active_only:
        cur.execute("SELECT * FROM Promotions WHERE active=1 ORDER BY startDate DESC")
    else:
        cur.execute("SELECT * FROM Promotions ORDER BY startDate DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def set_promotion_active(promo_id, active):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Promotions SET active=%s WHERE promoID=%s", (1 if active else 0, promo_id))
    conn.commit()
    conn.close()
    return True

def sales_report_by_month(year):
    conn = get_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT DATE_FORMAT(startDate, '%%Y-%%m') AS month, COUNT(*) AS sold_count, SUM(cost) AS total_sum
        FROM Memberships
        WHERE YEAR(startDate)=%s
        GROUP BY DATE_FORMAT(startDate, '%%Y-%%m')
        ORDER BY month
    """, (year,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_enrolled_for_class(class_id):
    conn = get_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        f"""
        SELECT e.enrollmentID, e.clientID, {_fio_alias('u')} AS fio
        FROM Enrollments e
        JOIN Users u ON e.clientID=u.userID
        WHERE e.classID=%s
        """,
        (class_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_attendance(class_id, client_id, present):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT attendID FROM Attendance WHERE classID=%s AND clientID=%s", (class_id, client_id))
    existing = cur.fetchone()
    if existing:
        cur.execute("UPDATE Attendance SET present=%s, markedAt=NOW() WHERE classID=%s AND clientID=%s", (1 if present else 0, class_id, client_id))
    else:
        cur.execute("INSERT INTO Attendance (classID, clientID, present) VALUES (%s,%s,%s)", (class_id, client_id, 1 if present else 0))
    conn.commit()
    conn.close()
    return True

def get_trainer_schedule(trainer_id):
    conn = get_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM GroupClasses WHERE trainerID=%s ORDER BY classDate, startTime", (trainer_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_training_journal(trainer_id, client_id, journalDate, notes, metrics):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO TrainingJournal (trainerID, clientID, journalDate, notes, metrics) VALUES (%s,%s,%s,%s,%s)",
                (trainer_id, client_id, journalDate, notes, metrics))
    conn.commit()
    conn.close()
    return True

def get_training_journal_for_client(client_id):
    conn = get_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        f"""
        SELECT tj.*, {_fio_alias('u')} as trainerName
        FROM TrainingJournal tj
        LEFT JOIN Users u ON tj.trainerID=u.userID
        WHERE tj.clientID=%s
        ORDER BY tj.journalDate DESC
        """,
        (client_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def add_recommendation(trainer_id, client_id, text):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Recommendations (trainerID, clientID, text) VALUES (%s,%s,%s)", (trainer_id, client_id, text))
    conn.commit()
    conn.close()
    return True

def get_recommendations_for_client(client_id):
    conn = get_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        f"""
        SELECT r.*, {_fio_alias('u')} as trainerName
        FROM Recommendations r
        LEFT JOIN Users u ON r.trainerID=u.userID
        WHERE r.clientID=%s
        ORDER BY r.createdAt DESC
        """,
        (client_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def block_trainer_time(trainer_id, blockDate, startTime, endTime, reason):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO TrainerBlockedTime (trainerID, blockDate, startTime, endTime, reason) VALUES (%s,%s,%s,%s,%s)",
                (trainer_id, blockDate, startTime, endTime, reason))
    conn.commit()
    conn.close()
    return True



def director_general_stats():
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)

    cur.execute("SELECT COUNT(*) c FROM Users WHERE userType='Клиент'")
    clients = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) c FROM Memberships WHERE membershipStatus='Активен'")
    active = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) c FROM GroupClasses")
    classes = cur.fetchone()['c']

    conn.close()
    return {
        "Клиенты": clients,
        "Активные абонементы": active,
        "Групповые занятия": classes
    }


def director_trainer_efficiency():
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute(f"""
        SELECT {_fio_alias('u')} AS fio,
        COUNT(DISTINCT g.classID) AS group_count,
        COUNT(DISTINCT pt.trainingID) AS pt_count,
        COUNT(DISTINCT pt.clientID) AS clients
        FROM Users u
        LEFT JOIN GroupClasses g ON g.trainerID=u.userID
        LEFT JOIN PersonalTraining pt ON pt.trainerID=u.userID
        WHERE u.userType='Тренер'
        GROUP BY u.userID
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def director_finance_stats():
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute("""
        SELECT DATE_FORMAT(startDate,'%Y-%m') AS month,
        COUNT(*) AS sold,
        SUM(cost) AS total
        FROM Memberships
        GROUP BY month
        ORDER BY month
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def director_staff_list():
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute(
        f"""
        SELECT userID, {_fio_alias()} AS fio, userType, phone
        FROM Users
        WHERE userType IN ('Тренер','Администратор')
        ORDER BY lastName, firstName
    """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_membership_prices():
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)
    cur.execute("""
        SELECT membershipType, ROUND(AVG(cost), 2) AS cost
        FROM Memberships
        GROUP BY membershipType
        ORDER BY membershipType
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def update_membership_price(membership_type, new_cost):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE Memberships
        SET cost=%s
        WHERE membershipType=%s
    """, (new_cost, membership_type))
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected > 0

def strategic_report():
    conn = get_connection()
    cur = conn.cursor(mdb.cursors.DictCursor)

    cur.execute("SELECT COUNT(*) c FROM Users WHERE userType='Клиент'")
    clients = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) c FROM Memberships WHERE membershipStatus='Активен'")
    active_memberships = cur.fetchone()['c']

    cur.execute("SELECT SUM(cost) s FROM Memberships")
    revenue = cur.fetchone()['s'] or 0

    cur.execute(f"""
        SELECT {_fio_alias('u')} AS fio, COUNT(pt.trainingID) c
        FROM Users u
        LEFT JOIN PersonalTraining pt ON pt.trainerID=u.userID
        WHERE u.userType='Тренер'
        GROUP BY u.userID
        ORDER BY c DESC
        LIMIT 1
    """)
    best_trainer = cur.fetchone()

    conn.close()

    return {
        "Всего клиентов": clients,
        "Активные абонементы": active_memberships,
        "Общая выручка": revenue,
        "Лучший тренер": best_trainer['fio'] if best_trainer else "—"
    }

def hire_staff(fio, phone, email, login, password, userType, birthDate=None):
    conn = get_connection()
    cur = conn.cursor()
    last, first, middle = split_fio(fio)
    cur.execute("""
        INSERT INTO Users (lastName, firstName, middleName, phone, email, login, password, userType, birthDate)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (last, first, middle, phone, email, login, password, userType, birthDate))
    conn.commit()
    staff_id = cur.lastrowid
    conn.close()
    return staff_id

def fire_staff(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM Users
        WHERE userID=%s
          AND userType IN ('Тренер','Администратор')
    """, (user_id,))
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected > 0


