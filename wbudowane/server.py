import threading
from flask import Flask, render_template, request, redirect, url_for
import time
import sqlite3
from datetime import datetime

# some state for comunicating between threads
mainThreadShouldRun = True

# Login
username = "admin"
password = "123"

# keyboard password
robot_code = "1234"

# dane z bazy
data_from_database = []

# Czy alarm jest wlaczony
alarm_bool = False


class State:
    def __init__(self):
        self.mainThreadShouldRun = True

    def setMainThreadShouldRun(self, value):
        self.mainThreadShouldRun = value

    def getMainThreadShouldRun(self):
        return self.mainThreadShouldRun


# lock when accessing global state
# except for atomic read in loop - like runMainWorker does
globalStateLock = threading.Lock()
globalState = State()


app = Flask(__name__)


# Wpisywanie aktualnej daty i godziny do bazy


def insertDate(action):
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()
    try:
        # Tworzenie tabeli jeśli nie istnieje
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zapisy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                godzina TEXT,
                akcja TEXT
            )
        ''')

        # Uzyskanie aktualnej daty i gozdiny
        teraz = datetime.now()
        data = teraz.strftime('%Y-%m-%d')
        godzina = teraz.strftime('%H:%M:%S')
        if action == 0:
            act = 'Alarm'
        else:
            act = 'Odblokowanie kodem'

        # Wstawianie danych do tabeli
        cursor.execute('''
            INSERT INTO zapisy (data, godzina, akcja)
            VALUES (?, ?, ?)
        ''', (data, godzina, act))

        # Commit
        conn.commit()
        print("Dane zostały zapisane pomyślnie.")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

    finally:
        conn.close()


# Uzyskiwanie danych z bazy


def retrieveDate():
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()

    try:
        # Self explanatory
        cursor.execute('SELECT * FROM zapisy')

        # Wszystko
        rows = cursor.fetchall()

        # Wyswietlanie
        # for row in rows:
        #     print(f"ID: {row[0]}, Data: {row[1]}, Godzina: {row[2]}")

        # zapisanie danych w liscie
        data_from_database.clear()
        data = []
        for row in rows:
            data = [row[0], row[1], row[2], row[3]]
            data_from_database.append(data)

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

    finally:
        conn.close()


# Cos czego nie chcesz zrobic w nowej robocie na stazu


def dropDatabase():
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()

    try:
        # Wykonaj zapytanie SQL do usunięcia wszystkich danych z tabeli
        # cursor.execute('DELETE FROM zapisy')

        # Usuniecie calej tabeli
        cursor.execute('DROP TABLE IF EXISTS zapisy')

        # commit
        conn.commit()

        print("Baza danych została wyczyszczona.")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

    finally:
        conn.close()


def runApp():
    app.run(debug=True, use_reloader=False, port=5000, host='0.0.0.0')


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/process_form', methods=['POST'])
def process_form():
    input_username = request.form['field1']
    input_password = request.form['field2']

    # Sprawdź, czy podane dane są poprawne
    if input_username == username and input_password == password:
        # Przekieruj do /process_form, jeśli dane są poprawne
        return redirect(url_for('info_page'))
    else:
        # Jeśli dane nie są poprawne, wyświetl komunikat na stronie
        error_message = 'Błędny login lub hasło. Spróbuj ponownie.'
        return render_template('index.html', error_message=error_message)


@app.route('/info_page')
def info_page():
    return render_template('info.html', data=data_from_database, alarm_bool=alarm_bool)


@app.route('/change_code', methods=['POST'])
def change_code():
    global robot_code
    robot_code = request.form.get('new_code', '')
    return "OK"


@app.route('/toggle_alarm', methods=['POST'])
def toggle_alarm():
    # Zmiana wartości bool na przeciwną
    global alarm_bool
    alarm_bool = not alarm_bool
    return "OK"


@app.route('/kill')
def func2():
    print("killing thread")
    globalState.setMainThreadShouldRun(False)
    return 'killing thread'


def runMainWorker():
    print('runMainWorker')
    while True:
        print('runMainWorker')
        # insertDate(1)  # Odblokowanie
        # insertDate(0)  # Alarm
        time.sleep(3)
        retrieveDate()
        print(alarm_bool)
        print(robot_code)
        # print(data_from_database)
        if not globalState.getMainThreadShouldRun():
            print('commiting sewside')
            break


if __name__ == '__main__':
    try:
        print(f'start first thread')
        t1 = threading.Thread(target=runApp).start()
        print(f'start second thread')
        t2 = threading.Thread(target=runMainWorker).start()
    except Exception as e:
        print("Unexpected error:" + str(e))
