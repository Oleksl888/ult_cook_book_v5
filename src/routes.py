import os
import sqlite3

import requests
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from marshmallow.exceptions import ValidationError
from werkzeug.utils import secure_filename

from src.flickr_api_helper import check_for_image
from src.helpers import load_recepies_from_db, feedback_loader, feedback_saver, make_search, return_ingridients, \
    gallery_loader, login_user, logout_user, calculate_timedelta, load_userpic, load_recepies_from_db_api, send_mail, \
    register_user
from src.models import User, Recipe, Ingridient, Feedback, RecipeFeedback
from src.schemas import UserSchema, RecipeSchema, IngridientSchema, FeedbackSchema, RecipeFeedbackSchema
from src import app, db, STATIC_PATH, DATA_PATH
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from datetime import datetime, timedelta, date
from src.geo_api import geo_request, make_response_geo_data, return_unique_visitors
from flask import render_template, request, redirect, flash, url_for, abort, jsonify, session


@app.route('/api/recipe')
@app.route('/api/recipe/<int:id>', strict_slashes=False)
def api_recipe(id=None):
    make_response_geo_data(geo_request(), '/index')
    recipe_schema = RecipeSchema()
    if id is None:
        recipes = db.session.query(Recipe).all()
        recipes_data = recipe_schema.dump(recipes, many=True)
    else:
        recipe = db.session.query(Recipe).filter_by(id=id).first()
        if not recipe:
            return jsonify(message='Recipe not found'), 404
        recipes_data = recipe_schema.dump(recipe)
        print(recipe.ingridients)
    return jsonify(recipes_data), 200


@app.route('/api/ingridients', strict_slashes=False)
@app.route('/api/ingridients/<int:id>', strict_slashes=False)
def api_ingridients(id=None):
    make_response_geo_data(geo_request(), '/ingridients')
    ingridient_schema = IngridientSchema()
    if id is None:
        ingridients = db.session.query(Ingridient).all()
        ingridients_data = ingridient_schema.dump(ingridients, many=True)
    else:
        ingridients = db.session.query(Ingridient).filter_by(id=id).first()
        if not ingridients:
            return jsonify(message='Ingridient not found'), 404
        ingridients_data = ingridient_schema.dump(ingridients)
    return jsonify(ingridients_data), 200


@app.route('/api/register', methods=['POST'], strict_slashes=False)
def api_register_user():
    make_response_geo_data(geo_request(), '/register')
    """add requirements to user/email/password"""
    userschema = UserSchema()
    if request.is_json:
        username = request.json.get('username', '')
        email = request.json.get('email', '')
        password = request.json.get('password', '')
        print('Json', username, email, password)
    else:
        username = request.form.get('username', None)
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        print('Form-Data', username, email, password)

    error = userschema.validate(data={'name': username, 'email': email, 'password': password})
    if error:
        return jsonify(error)
    if len(password) < 8:
        return jsonify(message='Password too short. Must be at least 8 characters')
    if not username.isalpha():
        return jsonify(message="Username must consist of only alphabetic characters")

    test_user_name = db.session.query(User).filter_by(name=username.lower()).first()
    test_user_email = db.session.query(User).filter_by(email=email.lower()).first()
    if test_user_name or test_user_email:
        return jsonify(message='User already exists'), 401

    user = User(name=username.lower(), email=email.lower(), password=password)
    db.session.add(user)
    db.session.commit()
    send_mail(username, email)
    return jsonify(message='User created')


@app.route('/api/login', methods=['POST'], strict_slashes=False)
def api_login():
    make_response_geo_data(geo_request(), '/login')
    if request.is_json:
        email = request.json.get('email', '')
        password = request.json.get('password', '')
    else:
        email = request.form.get('email', None)
        password = request.form.get('password', None)
    user = db.session.query(User).filter_by(email=email).first()
    if not user:
        return jsonify(message='User not found'), 409
    if check_password_hash(user.password, password):
        timestamp = datetime.now()
        user.last_login = user.current_login
        user.current_login = timestamp
        db.session.commit()
        access_token = create_access_token(
            identity=user.uuid,
            expires_delta=timedelta(hours=2),
            additional_claims={'is_admin': user.is_admin, 'name': user.name, 'id': user.id}
        )
        return jsonify(message=f'User {user.name} logged in successfully!', access_token=access_token), 200
    else:
        return jsonify(message='Wrong password'), 409


@app.route('/api/users', methods=['GET', 'POST'], strict_slashes=False)
@app.route('/api/users/<int:id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'], strict_slashes=False)
@jwt_required()
def api_manage_users(id=None):
    is_admin = get_jwt().get('is_admin', 0)
    if is_admin:
        userschema = UserSchema()
        """add admin priveleges here"""
        make_response_geo_data(geo_request(), '/users')
        if request.method == 'GET':
            if not id:
                users = db.session.query(User).all()
                users_data = userschema.dump(users, many=True)
                return jsonify(users_data), 200
            else:
                user = db.session.query(User).filter_by(id=id).first()
                if not user:
                    return jsonify(message='User not found'), 409
                user_data = userschema.dump(user)
                return jsonify(user_data), 200

        if request.method == 'POST':
            if request.is_json:
                username = request.json.get('username', '')
                email = request.json.get('email', '')
                password = request.json.get('password', '')
                print('Json', username, email, password)
            else:
                username = request.form.get('username', None)
                email = request.form.get('email', None)
                password = request.form.get('password', None)
                print('Form-Data', username, email, password)

            error = userschema.validate(data={'name': username, 'email': email, 'password': password})
            if error:
                return jsonify(error)
            if len(password) < 8:
                return jsonify(message='Password too short. Must be at least 8 characters')
            if not username.isalpha():
                return jsonify(message="Username must consist of only alphabetic characters")

            test_user_name = db.session.query(User).filter_by(name=username.lower()).first()
            test_user_email = db.session.query(User).filter_by(email=email.lower()).first()
            if test_user_name or test_user_email:
                return jsonify(message='User already exists')

            user = User(name=username.lower(), email=email.lower(), password=password)
            db.session.add(user)
            db.session.commit()
            return jsonify(message='User created')

        if request.method == 'PUT':
            if not id:
                return jsonify(message='Must specify user id that needs to be updated')
            else:
                if request.is_json:
                    username = request.json.get('username', '')
                    email = request.json.get('email', '')
                    password = request.json.get('password', '')
                    set_admin = bool(request.json.get('set_admin', 0))
                    print('Json', username, email, password)
                else:
                    username = request.form.get('username', None)
                    email = request.form.get('email', None)
                    password = request.form.get('password', None)
                    set_admin = bool(request.form.get('set_admin', 0))
                    print('Form-Data', username, email, password)

                test_user = db.session.query(User).filter_by(id=id).first()
                if not test_user:
                    return jsonify(message='User Does not exist')

                error = userschema.validate(data={'name': username, 'email': email, 'password': password})
                if error:
                    return jsonify(error)
                if len(password) < 8:
                    return jsonify(message='Password too short. Must be at least 8 characters')
                if not username.isalpha():
                    return jsonify(message="Username must consist of only alphabetic characters")

                try:
                    test_user.name = username.lower()
                    test_user.email = email.lower()
                    test_user.password = generate_password_hash(password)
                    test_user.is_admin = set_admin
                    db.session.commit()
                except IntegrityError:
                    return jsonify(message="This name/email is already taken")
                else:
                    return jsonify(message='All user info Updated')

        if request.method == 'PATCH':
            if not id:
                return jsonify(message='Must specify user id that needs to be updated')
            else:
                if request.is_json:
                    username = request.json.get('username', '')
                    email = request.json.get('email', '')
                    password = request.json.get('password', '')
                    set_admin = bool(request.json.get('set_admin', 0))
                    print('Json', username, email, password)
                else:
                    username = request.form.get('username', '')
                    email = request.form.get('email', '')
                    password = request.form.get('password', '')
                    set_admin = bool(request.form.get('set_admin', 0))
                    print('Form-Data', username, email, password)

                test_user = db.session.query(User).filter_by(id=id).first()
                if not test_user:
                    return jsonify(message='User Does not exist')

                try:
                    if username:
                        if username.isalpha():
                            test_user.name = username.lower()
                        else:
                            return jsonify(message="This name is invalid")
                    if email:
                        userschema.validate(data={'email': email})
                        test_user.email = email.lower()
                    if password:
                        if len(password) > 7:
                            test_user.password = generate_password_hash(password)
                        else:
                            return jsonify(message="Password must be at least 8 characters")
                    if set_admin:
                        test_user.is_admin = set_admin
                    db.session.commit()
                except IntegrityError:
                    return jsonify(message="This name/email is already taken")
                except ValidationError:
                    return jsonify(message="Email field is incorrect")
                else:
                    return jsonify(message='Partial User info Updated')

        if request.method == 'DELETE':
            if not id:
                return jsonify(message='Must specify user id that needs to be deleted')
            user = db.session.query(User).filter_by(id=id).first()
            if not user:
                return jsonify(message='User Does not exist')
            db.session.delete(user)
            db.session.commit()
            return jsonify(message='User info deleted')
    else:
        return jsonify(message='Only Users with admin rights can access this'), 403


@app.route('/api/feedback', methods=['GET'], strict_slashes=False)
def api_retrieve_feedback():
    make_response_geo_data(geo_request(), '/feedback-Read')
    feedbackschema = FeedbackSchema()
    feedback = db.session.query(Feedback).all()
    feedback_data = feedbackschema.dump(feedback, many=True)
    return jsonify(feedback_data), 200


@app.route('/api/feedback', methods=['POST'], strict_slashes=False)
@jwt_required()
def api_add_feedback():
    username = get_jwt().get('name', None)
    make_response_geo_data(geo_request(), '/feedback')
    feedbackschema = FeedbackSchema()
    if request.is_json:
        message = request.json.get('message', '')
    else:
        message = request.form.get('message', '')

    error = feedbackschema.validate(data={'name': username, 'message': message})
    if error:
        return jsonify(error)
    if not username:
        return jsonify(message='User name is invalid')
    if not message:
        return jsonify(message="Message cannot be empty")

    test_feedback = db.session.query(func.count(Feedback.id)).filter(
        Feedback.date_time==date.today(),
        Feedback.name==username
    ).scalar()
    print(test_feedback)
    if test_feedback > 10:
        return jsonify(message="User's message cap has been reached")
    feedback = Feedback(name=username, message=message)
    db.session.add(feedback)
    db.session.commit()
    return jsonify(message='Feedback has been added')


@app.route('/api/recipe/feedback', strict_slashes=False)
@app.route('/api/recipe/<int:id>/feedback', strict_slashes=False, methods=['POST', 'GET'])
@jwt_required()
def api_recipe_feedback(id=None):
    recipe_feedback_schema = RecipeFeedbackSchema()
    make_response_geo_data(geo_request(), '/recipe-feedback')
    if id is None:
        return jsonify(message='You must speicfy recipe to reach out to feedback'), 404
    if request.method == 'GET':
        recipe_feedback = db.session.query(RecipeFeedback).filter_by(recipe_id=id).all()
        print(recipe_feedback)
        if not recipe_feedback:
            return jsonify(message='THere is no feedback for this'), 404
        recipes_data = recipe_feedback_schema.dump(recipe_feedback, many=True)
        return jsonify(recipes_data), 200
    elif request.method == 'POST':
        user_id = get_jwt().get('id', None)
        if request.is_json:
            message = request.json.get('message', '')
        else:
            message = request.form.get('message', '')
        if not message:
            return jsonify(message="Message cannot be empty")

        recipe_feedback = RecipeFeedback(
            recipe_id=id,
            user_id=user_id,
            message=message,
            ip=requests.get('https://api64.ipify.org?format=json').json().get('ip', 'Unknown')
        )
        db.session.add(recipe_feedback)
        db.session.commit()
        return jsonify(message='Feedback has been added')


@app.route('/api/login.html', methods=['GET'])
def api_login_view():
    return render_template('api-login.html')


@app.route('/api/register.html', methods=['GET'])
def api_register_view():
    return render_template('api-register.html')


@app.route('/')
@app.route('/index.html')
def index():
    """Index page returns a table with all recepies and ingridients. All recepies are hyperlinks to /recepies page
    All ingridients are hyperlinks to /search page """
    db_data = load_recepies_from_db()
    if 'username' in session:
        flash(f"Hello {session['username']}, only registered users can see this")
    else:
        flash(f"You are not registered")
    if make_response_geo_data(geo_request(), '/index'):
        visits = return_unique_visitors()
        return render_template('index.html', data=db_data, info=session, visits=visits, user=session.get('username', ''))
    return render_template('index.html', data=db_data, user=session.get('username', ''))


@app.route('/recipe/<string:page_name>', methods=['GET', 'POST'])
def load_recipe(page_name):
    """Function takes a name from the hyperlink, passes the request to the helper function to look for a recipe on file.
    Also a search is made in images on file, if found image will be loaded from file. If image not found, search will
    be performed on Flickr with API request. Found image will be loaded on webpage and saved on file."""
    name = page_name.replace('_', ' ')
    recipe = load_recepies_from_db(name)
    image = check_for_image(name)
    if request.method == 'GET':
        comments = feedback_loader(name)
        return render_template('recipe.html', title=name.upper(), recipe=recipe, image=image, comments=comments, pname=page_name, user=session.get('username', ''))
    elif request.method == 'POST':
        data = request.form
        response = feedback_saver(data, name)
        if response == 'success':
            flash('Feedback added succesfully')
            return redirect(url_for('load_recipe', page_name=page_name, user=session.get('username', '')))
        flash('Could not add Feedback')
        return redirect(url_for('load_recipe', page_name=page_name, user=session.get('username', '')))


@app.route('/search.html', methods=['POST', 'GET'])
def render_search():
    """This is a search from the 'search' page"""
    if request.method == 'GET':
        return render_template('search.html', user=session.get('username', ''))
    data = request.form.get('search', '')
    if not data:
        flash('You need to enter a search query')
        return redirect('/search.html')
    results = make_search(data)
    if not results:
        flash("Nothing found")
        return redirect(url_for('render_search'))
    return render_template('search_result.html', data=results, user=session.get('username', ''))


@app.route('/search/<string:search_query>', strict_slashes=False)
def search(search_query):
    """This is the search from ingridients links cross-reference"""
    results = make_search(search_query)
    return render_template('search_result.html', data=results, user=session.get('username', ''))


@app.route('/recepies.html')
def display_recepies():
    data = load_recepies_from_db()
    return render_template('recepies.html', data=data, user=session.get('username', ''))


@app.route('/ingridients.html')
def display_ingridients():
    data = return_ingridients()
    return render_template('ingridients.html', data=data, user=session.get('username', ''))


@app.route('/gallery.html')
def display_gallery():
    file_path = gallery_loader()
    return render_template('gallery.html', data=file_path, user=session.get('username', ''))


@app.route('/feedback.html', methods=['POST', 'GET'])
def feedback():
    if request.method == 'GET':
        data = feedback_loader()
        return render_template('feedback.html', data=data, user=session.get('username', ''))
    data = request.form
    response = feedback_saver(data)
    if response == 'success':
        flash('Feedback added successfully')
        return redirect(url_for('feedback'))
    flash('Could not add feedback!')
    return redirect(url_for('feedback'))


@app.route('/register.html', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if register_user():
        return redirect(url_for('login'))
    return redirect(url_for('register'))


@app.route('/login.html', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        if 'username' in session:
            return render_template('login.html', user=session.get('username', ''))
        return render_template('login.html')
    if login_user():
        return redirect(url_for('profile'))
    return redirect(url_for('login'))


@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile.html')
def profile():
    tdelta = calculate_timedelta()
    img = load_userpic()
    print(img)
    img_list = os.listdir(os.path.join(STATIC_PATH, 'usr'))
    print(img_list)
    if not img or img not in img_list:
        img = "img/nothing_to_display.jpg"
    else:
        img = "usr/" + img
    print(img)
    return render_template('profile.html', user=session.get('username', ''), tdelta=tdelta, img=img)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('userfile', None)
    if file and session.get('username', None):
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            abort(400)
        file_name = 'user_' + session.get('username', None) + file_ext.lower()
        file.save(os.path.join(STATIC_PATH, 'usr', file_name))
        flash("File uploaded successfully")
        try:
            db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
        except (FileNotFoundError, sqlite3.DatabaseError):
            return False
        try:
            db.execute('UPDATE users SET userpic=? WHERE name=?', (file_name, session.get('username', '')))
        except sqlite3.DatabaseError:
            flash('Could not update userpic information in DB')
        else:
            db.commit()
            db.close()
            return redirect(url_for('profile'))


@app.route('/api.html')
def api():
    return render_template('api.html')


@app.route('/api/recepies/<query>', strict_slashes=False)
@app.route('/api/recepies', strict_slashes=False)
def api_response(query=None):
    data = load_recepies_from_db_api(query)
    return data, 200


@app.errorhandler(413)
def file_size_error(error):
    flash("File too big, maximum allowed is 512 Kb")
    return redirect(url_for('profile'))


@app.errorhandler(400)
def file_type_error(error):
    flash("Wrong file type, only type .jpg/.jpeg/.png is allowed")
    return redirect(url_for('profile'))


@app.route('/aggregate', strict_slashes=False)
def aggregate():
    pass #TODO