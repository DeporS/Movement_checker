import threading
from flask import Flask, render_template, request, redirect, url_for
import time
import sqlite3
from datetime import datetime

from State import * 

# some state for comunicating between threads
mainThreadShouldRun = True

# Login
username = "admin"
password = "123"


# dane z bazy
data_from_database = []


# zgaduje ze to globalState.isAlarmArmed
# Czy alarm jest wlaczony
alarm_bool = False 


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


def insertPeople(name, surname, is_admin):
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()
    try:
        # Tworzenie tabeli jeśli nie istnieje
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pracownicy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                surname TEXT,
                admin TEXT CHECK (admin IN ('tak', 'nie')),
                password INTEGER
            )
        ''')

        random_password = random.randint(1000, 9999)

        # Wstawianie danych do tabeli
        cursor.execute('''
            INSERT INTO pracownicy (name, surname, admin, password)
            VALUES (?, ?, ?, ?)
        ''', (name, surname, is_admin, random_password))

        # Commit
        conn.commit()
        print("Dane zostały zapisane pomyślnie.")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

    finally:
        conn.close()


def clearPeople():
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS pracownicy')
    conn.commit()

# clearPeople()
insertPeople("janek", "konieczko", "nie")
insertPeople("Krzysztof", "Matyla", "tak")


people_from_database = []


def retrievePeople():
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()

    try:
        # Self explanatory
        cursor.execute('SELECT * FROM pracownicy')

        # Wszystko
        rows = cursor.fetchall()

        # Wyswietlanie
        for row in rows:
            print(
                f"ID: {row[0]}, Imie: {row[1]}, Nazwisko: {row[2]}, Admin: {row[3]}, Hasło: {row[4]}")

        # zapisanie danych w liscie
        people_from_database.clear()
        data = []
        for row in rows:
            data = [row[0], row[1], row[2], row[3], row[4]]
            people_from_database.append(data)

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

    finally:
        conn.close()


retrievePeople()


def get_password_by_id(employee_id):
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()

    # Pobieranie hasła dla określonego id
    cursor.execute(
        'SELECT password FROM pracownicy WHERE id = ?', (employee_id,))
    result = cursor.fetchone()

    # Sprawdzanie, czy znaleziono hasło
    if result:
        password = result[0]
        print(f"Hasło dla pracownika o ID {employee_id}: {password}")
    else:
        print(f"Brak pracownika o ID {employee_id}")

    # Zamykanie połączenia
    conn.close()

    return password

# Cos czego nie chcesz zrobic w nowej robocie na stazu


def dropDatabase():
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()

    try:
        # Wykonaj zapytanie SQL do usunięcia wszystkich danych z tabeli
        cursor.execute('DELETE FROM zapisy')

        # Usuniecie calej tabeli
        # cursor.execute('DROP TABLE IF EXISTS zapisy')

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

    # Pobierz hasło dla podanego użytkownika
    stored_password = str(get_password_by_id(input_username))

    # Sprawdź, czy hasła są identyczne
    if stored_password == input_password:
        # Przekieruj do /process_form, jeśli dane są poprawne
        return redirect(url_for('info_page'))
    else:
        # Jeśli dane nie są poprawne, wyświetl komunikat na stronie
        error_message = 'Błędny login lub hasło. Spróbuj ponownie.'
        return render_template('index.html', error_message=error_message)


@app.route('/info_page')
def info_page():
    retrieveDate()
    return render_template('info.html', data=data_from_database, alarm_bool=globalState.isAlarmArmed)


@app.route('/change_code', methods=['POST'])
def change_code():
    globalState.password = request.form.get('new_code', '')
    return "OK"


@app.route('/toggle_alarm', methods=['POST'])
def toggle_alarm():
    # Od teraz to tylko wylaczanie alarmu
    # w sensie ze przesrtaje grac
    if globalState.isAlarmSounding:
        globalState.isAlarmSounding = False
    return "OK"


@app.route('/kill')
def func2():
    print("killing thread")
    globalState.setMainThreadShouldRun(False)
    return 'killing thread'



@app.route('/upload_music', methods=['POST'])
def upload_music():
    upload_music.musicCounter += 1

    try:
        # Pobierz przesłany plik muzyki
        music_file = request.files['music_file']

        music = f"alarm_music{upload_music.musicCounter}.mp3"

        # Zapisz plik w odpowiednim miejscu na serwerze
        music_file.save('music/' + music)

        # Zatrzymaj odtwarzacz
        musicPlayerLock.acquire()
        globalState.player = vlc.MediaPlayer("music/" + music)
        musicPlayerLock.release()

        return "OK"
    except Exception as e:
        # Obsługa błędu
        print(f"Błąd podczas przesyłania muzyki: {e}")
        return "Błąd"
upload_music.musicCounter = 0

#  --- running serer only stuff ---
def runMainWorker():
    print('runMainWorker')
    while True:
        print('runMainWorker')
        # insertDate(1)  # Odblokowanie
        # insertDate(0)  # Alarm
        time.sleep(3)
        retrieveDate()
        print(globalState.isAlarmArmed)
        print(globalState.password)
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
