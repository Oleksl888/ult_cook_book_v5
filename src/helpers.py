import csv
import os
import datetime
import sqlite3
import smtplib
import sys

from flask import request, flash, session, jsonify
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash

from src import mail, DATA_PATH, STATIC_PATH


def load_recepies_from_db(query=None):
    if query is None:
        db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
        cur = db.cursor()
        recepies = cur.execute('''SELECT recepies.name, ingridients.name FROM recepies 
        JOIN recipe_ingridients ON recepies.id=recipe_ingridients.recipe_id 
        JOIN ingridients ON recipe_ingridients.ingridient_id=ingridients.id;''').fetchall()
        cookdb = {}
        for entry in recepies:
            cookdb[entry[0]] = cookdb.get(entry[0], [])
            cookdb[entry[0]].append(entry[1])
        for val in cookdb.values():
            val.sort()
        return cookdb
    else:
        db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
        cur = db.cursor()
        try:
            recepies = cur.execute('SELECT recipe FROM recepies WHERE name=?', (query.lower(),)).fetchone()[0]
        except (TypeError, ValueError, IndexError, sqlite3.DatabaseError):
            recepies = "Could not retrieve info from DB"
        return recepies


def load_recepies_from_db_api(query=None):
    if query is None:
        db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
        cur = db.cursor()
        recepies_list = cur.execute('''SELECT name, recipe FROM recepies''').fetchall()
        cookdb = {}
        for entry in recepies_list:
            cookdb[entry[0]] = entry[1]
        return cookdb
    else:
        db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
        cur = db.cursor()
        try:
            recepies = cur.execute('SELECT name, recipe FROM recepies WHERE id=?', (query,)).fetchone()
            recepy = {recepies[0]: recepies[1]}
        except (TypeError, ValueError, IndexError, sqlite3.DatabaseError):
            recepies = jsonify("Could not retrieve info from DB")
            return recepies
        return recepy


def read_csv(filename):
    """This function opens csv file, reads it into a dictionary and converts in json format"""
    try:
        with open(filename, encoding='utf8') as file:
            cook_book_list = []
            reader = csv.DictReader(file)
            for row in reader:
                cook_book_list.append(row)
    except FileNotFoundError:
        return {}
    else:
        return cook_book_list


def extract_recepies(cookdb):
    """This function takes a list of recepies and creates a dictionary to display on website"""
    recepies = {}
    for recipe in cookdb:
        recepies[recipe['name'].capitalize()] = recipe['ingridients']
    return recepies


def load_recipe_from_file(name):
    read_recipe = ''
    with open(os.path.join(DATA_PATH, 'recepies.txt'), encoding='utf-8-sig') as file:
        for line in file:
            if line.strip().lower() == name.lower():
                while len(line) > 1:
                    line = file.readline()
                    read_recipe += line
                return read_recipe
    return 'The recipe is unavailable'


def make_search(keyword):
    """Looks for a value provided in database, returns a dictionary with results"""
    recepies = {}
    if '+' in keyword:
        keyword = keyword.replace('+', ' ')
    elif '_' in keyword:
        keyword = keyword.replace('_', ' ')
    cookdb = load_recepies_from_db()
    for key, value in cookdb.items():
        if keyword.lower() in key.lower() or keyword.lower() in value:
            recepies[key] = value
    return recepies


def return_ingridients():
    """Function takes a dictionary as input and returns html-formatted table with ingridients to display on web page"""
    try:
        db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
        ingridients = db.execute('SELECT DISTINCT name FROM ingridients').fetchall()
        print(ingridients)
    except (FileNotFoundError, sqlite3.DatabaseError):
        return 'Could not open Database'
    else:
        db.close()
        return sorted(ingridients)


def gallery_loader():
    """Prepares file saved locally to be send to gallery"""
    file_list = os.listdir(os.path.join(STATIC_PATH, 'img')) # Getting list of files saved locally in /img folder
    # Going through the loop to cycle through all the files and create a table where cells are images
    file_path = ['img/' + file for file in file_list if file != 'nothing_to_display.jpg']
    file_pretty_names = [file.replace('_', ' ').upper()[:-4] for file in file_list if file != 'nothing_to_display.jpg']
    return zip(file_path, file_pretty_names)


def feedback_loader(recipe=None):
    if recipe is None:
        try:
            db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
            data = db.execute('SELECT * FROM feedback').fetchall()
        except (FileNotFoundError, sqlite3.DatabaseError):
            return 'Could not open Database'
        else:
            db.close()
    else:
        try:
            db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
            data = db.execute(
                '''SELECT users.name, recipe_feedback.message, recipe_feedback.date_time FROM recipe_feedback JOIN users 
                ON recipe_feedback.user_id=users.id JOIN recepies ON recipe_feedback.recipe_id=recepies.id 
                WHERE recepies.name=?''', (recipe,)
            ).fetchall()
            print(data)
        except (FileNotFoundError, sqlite3.DatabaseError):
            return 'Could not retrieve recipe comments'
        else:
            db.close()
    return data


def feedback_saver(message, recipe=None):
    name = message.get('fname', 'FNU')
    msg = message.get('messg', 'No message passed')
    now = datetime.datetime.now()
    date = now.strftime('%d-%b-%Y, %H:%M:%S')
    ip_address = '1.1.1.1' #change it later
    if recipe is None:
        try:
            db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
            db.execute("INSERT INTO feedback (name, message, date_time) VALUES (?, ?, ?)",
                           (name, msg, date))
        except (FileNotFoundError, sqlite3.DatabaseError):
            print(sys.exc_info())
            return 'Database Error. Could not add data.'
        else:
            db.commit()
            db.close()
            return 'success'
    else:
        name = session.get('username', '')
        try:
            db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
            cur = db.cursor()
        except (FileNotFoundError, sqlite3.DatabaseError):
            return 'Entry has not been added'
        try:
            recipe_id = cur.execute('SELECT id FROM recepies WHERE name = ?', (recipe,)).fetchone()[0]
            user_id = cur.execute('SELECT id FROM users WHERE name = ?', (name,)).fetchone()[0]
        except (TypeError, sqlite3.DatabaseError):
            return 'Could not process your request'
        try:
            cur.execute(
                'INSERT INTO recipe_feedback (recipe_id, message, date_time, ip, user_id) VALUES (?, ?, ?, ?, ?)',
                (recipe_id, msg, date, ip_address, user_id))
            db.commit()
        except sqlite3.DatabaseError:
            db.rollback()
            db.close()
            return 'Database Error. Could not add data.'
        else:
            db.close()
            return 'success'


def register_user():
    data = request.form
    try:
        name = data.get('name', '').lower()
        email = data.get('email', '').lower()
        password = generate_password_hash(data.get('pass', ''))
        now = datetime.datetime.now()
        date = now.strftime('%d-%b-%Y, %H:%M:%S')
    except KeyError:
        flash("Could not retrive user data")
        return False
    try:
        db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
    except (FileNotFoundError, sqlite3.DatabaseError):
        return False
    else:
        try:
            db.execute("INSERT INTO users (name, email, password, registered_date) VALUES (?, ?, ?, ?)",
                       (name, email, password, date))
        except sqlite3.IntegrityError:
            flash("User already exists. Use different username or email, or login")
            return False
        except sqlite3.DatabaseError:
            flash("Database error. Could not register user")
            return False
        else:
            db.commit()
            db.close()
            if send_mail(name, email):
                flash(f'User {name} has been registered. Keep an eye for updates')
            else:
                flash(f'User {name} has been registered. But there was an error sending email upon registration')
            return True


def login_user():
    data = request.form
    name = data.get('name', '').lower()
    now = datetime.datetime.now()
    date = now.strftime('%d-%b-%Y, %H:%M:%S')
    password = data.get('pass', '')
    try:
        db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
    except (FileNotFoundError, sqlite3.DatabaseError):
        return False
    else:
        pw = db.execute('SELECT password FROM users WHERE name = ?', (name, )).fetchone()
        if not pw:
            flash('Username not found')
            return False
        if check_password_hash(pw[0], password):
            session['username'] = name
            session['usr_login_datetime'] = date
            try:
                session['last_login'] = db.execute('SELECT last_login FROM users WHERE name=?', (name,)).fetchone()
                db.execute('UPDATE users SET last_login=? WHERE name=?', (date, name))
            except sqlite3.DatabaseError:
                flash('Could not update login timestamp information in DB')
            else:
                db.commit()
                db.close()
                return True
        else:
            flash('Password does not match')
            return False


def logout_user():
    now = datetime.datetime.now()
    date = now.strftime('%d-%b-%Y, %H:%M:%S')
    name = session.pop('username', None)
    try:
        db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
    except (FileNotFoundError, sqlite3.DatabaseError):
        return False
    try:
        db.execute('UPDATE users SET last_login=? WHERE name=?', (date, name))
    except sqlite3.DatabaseError:
        flash('Could not update logout information in DB')
    else:
        db.commit()
        db.close()
        return True


def calculate_timedelta():
    last_login = session.get('last_login', '')
    if len(last_login) == 0 or last_login[0] is None:
        return 'never'
    now = datetime.datetime.strptime(session['usr_login_datetime'], '%d-%b-%Y, %H:%M:%S')
    date = datetime.datetime.strptime(last_login[0], '%d-%b-%Y, %H:%M:%S')
    return str(now - date)[:-10].replace(':', ' hours ') + ' minutes'


def load_userpic():
    name = session.get('username', '')
    try:
        db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
    except (FileNotFoundError, sqlite3.DatabaseError):
        return False
    else:
        try:
            userpic = db.execute('SELECT userpic FROM users WHERE name = ?', (name, )).fetchone()[0]
        except sqlite3.DatabaseError:
            flash('Could not get userpic')
            return False
        else:
            db.close()
            return userpic


def send_mail(name, email):
    print('Sending mail...')
    message = Message(
        subject='You have been registered',
        recipients=[email],
        sender='olesliusarenko@gmail.com',
        body=f'Hello, {name}! This is a test.'
    )
    mail.send(message)
    print('Email sent successfully...')
    return 'success'
