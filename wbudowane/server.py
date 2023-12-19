import threading
from flask import Flask, render_template, request, redirect, session, url_for
import time
import sqlite3
from datetime import datetime
import random

from State import *

# some state for comunicating between threads
mainThreadShouldRun = True


# dane z bazy
data_from_database = []


# zgaduje ze to globalState.isAlarmArmed
# Czy alarm jest wlaczony
alarm_bool = False


app = Flask(__name__)
app.secret_key = 'l124iAE1j412EAdajFA132fBM'


# Wpisywanie aktualnej daty i godziny do bazy


def insertDate(action, id=0):
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()
    try:
        # Tworzenie tabeli jeśli nie istnieje
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zapisy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                godzina TEXT,
                akcja TEXT,
                pracownik INTEGER       
            )
        ''')

        # Uzyskanie aktualnej daty i gozdiny
        teraz = datetime.now()
        data = teraz.strftime('%Y-%m-%d')
        godzina = teraz.strftime('%H:%M:%S')
        if action == 0:
            act = 'Alarm'
        elif action == 1:
            act = 'Odblokowanie kodem'
        elif action == 2:
            act = 'Alarm: Podano błędny numer pracownika'
        elif action == 3:
            act = 'Wyłączono alarm zdalnie'

        # Wstawianie danych do tabeli
        if action == 1 or action == 3:
            cursor.execute('''
                INSERT INTO zapisy (data, godzina, akcja, pracownik)
                VALUES (?, ?, ?, ?)
            ''', (data, godzina, act, id))
        else:
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


def retrieveDate(admin, id):
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()

    try:
        # pobranie danych
        if admin == "nie":
            cursor.execute('SELECT * FROM zapisy WHERE pracownik = ? ORDER BY ID DESC', (id,))
        else:
            cursor.execute('SELECT * FROM zapisy ORDER BY ID DESC')

        # Wszystko
        rows = cursor.fetchall()

        # Wyswietlanie
        # for row in rows:
        #     print(f"ID: {row[0]}, Data: {row[1]}, Godzina: {row[2]}")

        # zapisanie danych w liscie
        data_from_database.clear()
        data = []
        for row in rows:
            data = [row[0], row[1], row[2], row[3], row[4]]
            data_from_database.append(data)

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

    finally:
        conn.close()


def insertPeople(name, surname, is_admin, password: str):
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
                password TEXT
            )
        ''')

        random_password = password

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


def init_db():
    insertPeople("janek", "konieczko", "nie", "1337")
    insertPeople("Krzysztof", "Matyla", "tak", "6969")


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


# retrievePeople()


def get_password_by_id(employee_id):
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()

    # Pobieranie hasła dla określonego id
    cursor.execute(
        'SELECT password FROM pracownicy WHERE id = ?', (employee_id,))
    result = cursor.fetchone()

    password = ""
    # Sprawdzanie, czy znaleziono hasło
    if result:
        password = result[0]
        print(f"Hasło dla pracownika o ID {employee_id}: {password}")
    else:
        print(f"Brak pracownika o ID {employee_id}")

    # Zamykanie połączenia
    conn.close()

    return password


# Info do stronki
def get_info_by_id(employee_id):
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()

    # Pobieranie hasła dla określonego id
    cursor.execute(
        'SELECT * FROM pracownicy WHERE id = ?', (employee_id,))
    result = cursor.fetchone()

    # Zwracanie info
    if result:
        return result
    else:
        print(f"Brak pracownika o ID {employee_id}")

    # Zamykanie połączenia
    conn.close()

    return ""


# Cos czego nie chcesz zrobic w nowej robocie na stazu


def dropDatabase():
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()

    try:
        # Wykonaj zapytanie SQL do usunięcia wszystkich danych z tabeli
        cursor.execute('DELETE FROM zapisy')

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

    # Pobierz hasło dla podanego użytkownika
    stored_password = str(get_password_by_id(input_username))

    # Sprawdź, czy hasła są identyczne
    if stored_password == input_password:
        # ustaw id pracownika w danej sesji
        session['logged_ID'] = int(input_username)
        # Przekieruj do /process_form, jeśli dane są poprawne
        return redirect(url_for('info_page'))
    else:
        # Jeśli dane nie są poprawne, wyświetl komunikat na stronie
        error_message = 'Błędny login lub hasło. Spróbuj ponownie.'
        return render_template('index.html', error_message=error_message)


@app.route('/info_page')
def info_page():
    logged_ID = session["logged_ID"]
    info = get_info_by_id(logged_ID)
    name = info[1]
    surname = info[2]
    admin = info[3]
    retrieveDate(admin, logged_ID)
    return render_template('info.html', data=data_from_database, alarm_bool=globalState.isAlarmArmed, logged_ID=logged_ID, name=name, surname=surname, admin=admin)


@app.route('/change_code', methods=['POST'])
def change_code():
    new_pass = request.form.get('new_code', '')
    logged_ID = session["logged_ID"]
    # save to database
    conn = sqlite3.connect('based_baza_danych.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE pracownicy SET password = ? WHERE id = ?', (new_pass, logged_ID))
        conn.commit()
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
    finally:
        conn.close()
    return "OK"


@app.route('/toggle_alarm', methods=['POST'])
def toggle_alarm():
    # Od teraz to tylko wylaczanie alarmu
    # w sensie ze przesrtaje grac
    if globalState.isAlarmSounding:
        insertDate(3, session["logged_ID"])
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

        # Pobierz oryginalną nazwę pliku
        original_filename = music_file.filename

        # Pobierz rozszerzenie pliku
        file_extension = original_filename.split('.')[-1].lower()

        # Utwórz nazwę pliku z nowym rozszerzeniem
        music = f"alarm_music{upload_music.musicCounter}.{file_extension}"

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
        retrievePeople()
        # insertDate(1)  # Odblokowanie
        # insertDate(0)  # Alarm
        # insertDate(2)  # Podano bledny numer pracownika
        # insertDate(3)  # Wylaczenie alarmu zdalnie
        time.sleep(3)

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
