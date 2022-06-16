import csv
import os
import sys

from src import db, DATA_PATH
from src.models import Recipe, Ingridient, RecipeIngridients
from sqlalchemy.exc import IntegrityError, DatabaseError


def initialize_db():
    files = os.listdir(DATA_PATH)
    if not 'cook.db' in files:
        print("Database not found. Creating Database File...")
        db.create_all()
        print("Database Created...")
        populate_db()
    else:
        print("Database found. Starting app..")


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


def populate_db():
    DATA_FOR_DB = read_csv(os.path.join(DATA_PATH, 'cookbook.csv'))
    print('Populating Database...')
    try:
        for entry in DATA_FOR_DB:
            recipe_text = load_recipe_from_file(entry['name'])
            recipe = Recipe(name=entry['name'], recipe=recipe_text)
            db.session.add(recipe)
            db.session.commit()
            recipe_id = recipe.id
            ingridients = [ingridient.strip() for ingridient in entry['ingridients'].split(',')]
            ingridients_list = []
            for ingridient in ingridients:
                test_ingridient = db.session.query(Ingridient).filter_by(name=ingridient).first()
                if not test_ingridient:
                    _ingridient = Ingridient(name=ingridient)
                    db.session.add(_ingridient)
                    db.session.commit()
                    ingridients_list.append(_ingridient)
                    ingridient_id = _ingridient.id
                else:
                    ingridients_list.append(test_ingridient)
                    ingridient_id = test_ingridient.id
                recipe_ingridient = RecipeIngridients(recipe_id=recipe_id, ingridient_id=ingridient_id)
                db.session.add(recipe_ingridient)
            db.session.commit()
            recipe.ingridients = ingridients_list.copy()
    except(KeyError, TypeError, ValueError, IndexError, AttributeError, IntegrityError, DatabaseError):
        print('Fatal database error, cleaning up remaining files...')
        print(sys.exc_info())
        db.session.rollback()
        db.session.close()
        os.remove(os.path.join(DATA_PATH, 'cook.db'))
        print('Closing app...')
        exit()
    else:
        print('Database Populated!')
