@app.route('/info_page')
def info_page():
    return render_template('info.html', data=data_from_database, alarm_bool=alarm_bool)


@app.route('/toggle_alarm', methods=['POST'])
def toggle_alarm():
    # Zmiana wartości bool na przeciwną
    global alarm_bool
    alarm_bool = not alarm_bool
    return "OK"