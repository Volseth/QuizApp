import copy
import random
import secrets
import os
from flask import render_template, flash, redirect, url_for, request, json
from sqlalchemy import or_, and_, func
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from quizapp import app

from quizapp.forms import LoginForm, RegisterForm, UpdateAccountForm, CategoryForm, QuestionForm, QuizForm
from quizapp.models import *
import datetime


# Views for web application
# Main view
@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')


# Login/Register
@app.route("/login/", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # Instance of LoginForm
    form = LoginForm(request.form)
    # Check that HTTP request is POST and form is valid
    if request.method == 'POST' and form.validate():
        # Check if user exists in database
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Nazwa użytkownika lub hasło jest niepoprawne', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html', form=form)


@app.route("/register/", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # Instance of RegisterForm
    form = RegisterForm(request.form)

    # Check that HTTP request is POST and form is valid
    if request.method == 'POST' and form.validate():
        # Generate hashed password for database
        password_hashed = generate_password_hash(form.password.data, method='sha256')

        # Model object
        new_user = User(
            name=form.name.data,
            username=form.username.data,
            email=form.email.data,
            password=password_hashed
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Zarejestrowano pomyślnie!", 'success')
        # Redirect to login page
        return redirect(url_for('login'))
    else:
        return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# Functional Views

# Function to save user-profile and category picture on local-disk
def save_picture(form_picture, path):
    hex_picture = secrets.token_hex(8)
    _, file_extension = os.path.splitext(form_picture.filename)
    picture_filename = hex_picture + file_extension
    picture_path = os.path.join(app.root_path, path, picture_filename)
    form_picture.save(picture_path)

    return picture_filename


def get_stats():
    stats = Statistic.query.filter(Statistic.createdBy == current_user.id).all()
    quizes_solved = 0
    total_score = 0
    total_good = 0
    total_wrong = 0
    total_time = 0
    for stat in stats:
        quizes_solved += 1
        total_score += stat.score
        total_good += stat.goodAnswers
        total_wrong += stat.wrongAnswers
        total_time += stat.timeInSeconds
    total_answers = total_good + total_wrong
    if total_answers == 0:
        total_answers = 1
    return quizes_solved, total_score, \
        total_good, str(round((total_good / total_answers) * 100, 2)) + "%", \
        datetime.timedelta(seconds=total_time), total_wrong


# User profile
@app.route('/<username>/profile/', methods=['GET', 'POST'])
@login_required
def profile(username):
    form_update = UpdateAccountForm()
    # Get the actual data for forms
    all_categories = Category.query.filter_by(parentCategory=None).order_by(Category.categoryName).all()
    interest_categories = current_user.interests
    names = []
    for category in interest_categories:
        names.append(category.categoryName)
    if request.method == 'GET':
        form_update.name.data = current_user.name
        form_update.email.data = current_user.email

    # Get statistics
    quizes, score, good, percentage, time, wrong = get_stats()

    # Update user profile
    if form_update.submit.data and form_update.validate_on_submit():
        if form_update.picture.data:
            picture_file = save_picture(form_update.picture.data, 'static/images/profile_pics')
            current_user.image_file = picture_file
        current_user.name = form_update.name.data
        current_user.email = form_update.email.data
        db.session.commit()
        flash('Twój profil został uaktualniony!', 'success')
        return redirect(url_for('profile', username=username))

    # Update user interests
    if request.method == 'POST':
        for name in all_categories:
            checkbox_name = 'check_' + name.categoryName
            checkbox_value = request.form.get(checkbox_name)
            if checkbox_value is not None:
                # Check if interest exists in database
                obj = User.query.filter_by(username=current_user.username).join(User.interests).filter_by(
                    categoryName=checkbox_value).first()
                if obj is None:
                    query = user_interests.insert().values(username=current_user.username, category=checkbox_value)
                    db.session.execute(query)
                    db.session.commit()
            else:
                query = user_interests.delete().where(user_interests.c.category == name.categoryName).where(
                    user_interests.c.username == current_user.username)
                db.session.execute(query)
                db.session.commit()
        flash('Twoje zainteresowania zostały uaktualnione!', 'success')
        return redirect(url_for('profile', username=username))
    image_file = url_for('static', filename='images/profile_pics/' + current_user.image_file)
    return render_template('profile.html', image_file=image_file, form=form_update, all_categories=all_categories,
                           names=names, quizes=quizes, score=score, good=good, precentage=percentage, time=time,
                           wrong=wrong)


# get categories for user
def get_categories():
    # Get all categories created by user or main categories
    all_categories = Category.query.filter(
        or_(Category.createdBy.is_(None), Category.createdBy == current_user.id)).order_by(
        Category.categoryName).all()
    # Get names of user interests
    interest_categories = current_user.interests
    names = []
    ids = []
    for category in interest_categories:
        names.append(category.categoryName)
        ids.append(category.categoryId)
    # Get main interests and child interests categories
    main = Category.query.filter(Category.categoryName.in_(names)).all()
    recommended = Category.query.filter(and_(or_(Category.parentCategory.in_(names), Category.categoryId.in_(ids)),
                                             Category.createdBy.in_([None, current_user.id]))).order_by(
        Category.categoryName).all()
    for category in main:
        recommended.append(category)
    return all_categories, recommended


# Categories for users
@app.route('/<username>/categories')
@login_required
def categories(username):
    all_categories, recommended = get_categories()
    return render_template('categories.html', recommended=recommended, all_categories=all_categories, username=username)


@app.route('/<username>/categories/add_category', methods=['GET', 'POST'])
@login_required
def add_category(username):
    # Form object, dropdown for menu choices
    form_update = CategoryForm()
    choices = Category.query.filter(Category.parentCategory.is_(None)).order_by(Category.categoryName).all()
    form_update.parent_category.choices = choices
    if form_update.submit.data and form_update.validate_on_submit():
        # Category name validation:
        category_name = Category.query.filter(
            and_(or_(Category.createdBy.is_(None), Category.createdBy == current_user.id),
                 Category.categoryName == form_update.category_name.data)).first()
        if category_name:
            flash('Taka kategoria już istnieje! Wprowadź inna nazwę', 'danger')
            return redirect(
                url_for('add_category', username=username, form=form_update))
        else:
            new_category = Category(
                categoryName=form_update.category_name.data,
                image_file=save_picture(form_update.picture.data, 'static/images/category_pics'),
                parentCategory=form_update.parent_category.data,
                createdBy=current_user.id
            )
            db.session.add(new_category)
            db.session.commit()
            flash("Kategoria utworzona pomyślnie!", 'success')
            # Redirect to all categories page
            return redirect(url_for('categories', username=username))
    return render_template('add_category.html', username=username, form=form_update)


@app.route('/<username>/categories/<category>/edit_category', methods=['GET', 'POST'])
@login_required
def edit_category(username, category):
    # Form data, edited category selection, dropdown from menu choices, category form information
    form_update = CategoryForm()
    category_query = Category.query.filter(
        and_(Category.categoryName == category, Category.createdBy == current_user.id)).first()
    choices = Category.query.filter(Category.parentCategory.is_(None)).order_by(Category.categoryName).all()
    form_update.parent_category.choices = choices
    if request.method == 'GET':
        form_update.category_name.data = category_query.categoryName
        form_update.parent_category.data = category_query.parentCategory

    # Update category info
    if form_update.submit.data and form_update.validate_on_submit():
        # Category name validation:
        category_name = Category.query.filter(
            and_(or_(Category.createdBy.is_(None), Category.createdBy == current_user.id),
                 Category.categoryName == form_update.category_name.data)).first()
        # If category exists check name change in form
        if category_name and (
                form_update.category_name.data != category_query.categoryName
                or form_update.parent_category.data != category_query.parentCategory):
            if category_name.categoryName == form_update.category_name.data:
                flash('Taka kategoria już istnieje! Wprowadź inna nazwę', 'danger')
                return redirect(
                    url_for('edit_category', username=username, category=category_query.categoryName, form=form_update))
        else:
            # Update category image
            if form_update.picture.data:
                picture_file = save_picture(form_update.picture.data, 'static/images/category_pics')
                category_query.image_file = picture_file

            # Update questions associated with given category
            questions_associated = Question.query.filter(and_(Question.categoryId == category_query.categoryName,
                                                              Question.createdBy == current_user.id))
            for question in questions_associated:
                question.categoryId = category_query.categoryId
                db.session.commit()

            # Update category information
            category_query.categoryName = form_update.category_name.data
            category_query.parentCategory = form_update.parent_category.data
            db.session.commit()
            flash('Kategoria została uaktualniona!', 'success')
            return redirect(
                url_for('categories', username=username))
    return render_template('edit_category.html', username=username, category=category_query.categoryName,
                           form=form_update)


# Show categories for questions
@app.route('/<username>/categories_questions')
@login_required
def categories_questions(username):
    # Get all categories created by user or main categories
    all_categories, recommended = get_categories()

    return render_template('categories_questions.html', username=username, user_categories=all_categories,
                           recommended=recommended)


# Questions for users in selected category
@app.route('/<username>/questions/<category>')
@login_required
def questions(username, category):
    # Get all questions for selected category, created by current user
    category = Category.query.filter(Category.categoryName == category,
                                     or_(Category.createdBy == current_user.id, Category.createdBy == None)).first()
    category_questions = Question.query.filter(Question.categoryId == category.categoryId,
                                               Question.createdBy == current_user.id).all()
    return render_template('questions.html', questions=category_questions, username=username, category=category)


# Add new question in selected category
@app.route('/<username>/questions/<category>/add_question', methods=['GET', 'POST'])
@login_required
def add_question(username, category):
    # Form object
    form = QuestionForm()
    # Form validation
    if form.validate_on_submit():
        # Add question and answer object to database
        category = Category.query.filter(Category.categoryName == category,
                                         or_(Category.createdBy == current_user.id, Category.createdBy == None)).first()

        new_question = Question(
            questionText=form.question_text.data,
            categoryId=category.categoryId,
            createdBy=current_user.id
        )
        new_answer = Answer(
            answerText=form.answer_text.data
        )
        new_question.answers = new_answer
        db.session.add(new_question)
        db.session.commit()
        flash('Pytanie utworzone!', 'success')
        return redirect(url_for('questions', username=username, category=category))
    return render_template('add_question.html', username=username, category=category, form=form)


# Edit question
@app.route('/<username>/questions/<category>/<questionId>/edit_question', methods=['GET', 'POST'])
@login_required
def edit_question(username, category, questionId):
    form = QuestionForm()
    question = Question.query.filter(Question.questionId == questionId).first()
    # Get data for selected question
    if request.method == 'GET':
        form.question_text.data = question.questionText
        form.answer_text.data = question.answers.answerText

    if form.validate_on_submit():
        question.questionText = form.question_text.data
        question.answers.answerText = form.answer_text.data
        db.session.commit()
        flash('Pytanie zaktualizowane pomyślnie', 'success')
        return redirect(url_for('edit_question', username=username, category=category, questionId=questionId))
    return render_template('edit_question.html', username=username, category=category, questionId=questionId, form=form)


# Delete selected question
@app.route('/<username>/questions/<category>/<questionId>/delete_question')
@login_required
def delete_question(username, category, questionId):
    question = Question.query.filter(Question.questionId == questionId).first()
    db.session.delete(question)
    db.session.commit()
    flash('Pytanie zostało usunięte', 'success')
    return redirect(url_for('questions', username=username, category=category))


# Categories for quizzes
@app.route('/<username>/prepare_quiz', methods=['GET', 'POST'])
@login_required
def quiz_categories(username):
    form = QuizForm()
    count_query = (db.session.query(Category)
                   .join(Question)
                   .filter(Question.createdBy == current_user.id)
                   .group_by(Category)
                   .having(func.count(Category.categoryName) > 4)
                   ).all()
    all_categories, recommended = get_categories()
    form.time_select.choices = [i for i in range(15, 125, 5)]
    learn_categories = []
    for category in recommended:
        if category in count_query:
            learn_categories.append(category)
    for category in all_categories:
        if category in count_query and category not in learn_categories:
            learn_categories.append(category)
    form.category.choices = learn_categories

    if form.validate_on_submit():
        return redirect(
            url_for('learn', username=username, category=form.category.data, time=int(form.time_select.data)))

    return render_template('prepare_quiz.html', username=username, form=form)


# Quiz generated for user
@app.route('/<username>/<category>/<time>/learn', methods=['GET', 'POST'])
@login_required
def learn(username, category, time):
    # Get all questions and answers for selected category, created by current user
    selected_category = Category.query.filter(Category.categoryName == category,
                                              or_(Category.createdBy == current_user.id,
                                                  Category.createdBy == None)).first()

    category_questions = Question.query.filter(
        and_(Question.categoryId == selected_category.categoryId, Question.createdBy == current_user.id)).all()

    answers = []
    # Make questions randomly shuffled
    random.shuffle(category_questions)
    # Json format for questions
    questions_json = []
    for question in category_questions:
        answers.append(question.answers.answerText)
        questions_json.append(json.dumps(question.serialize()))

    # Json format for questions with options
    questions_with_options = []
    question_number = 1
    for question in questions_json:
        decoded_question = json.loads(question)
        options_available = copy.deepcopy(answers)
        options_available.remove(decoded_question.get('answer'))

        # Add answer to options
        options = [decoded_question.get('answer')]
        random.shuffle(options_available)
        while len(options) < 4:
            item = options_available.pop()
            options.append(item)
        # Make options randomly shuffled
        random.shuffle(options)

        # Update json object with question number and shuffled options
        decoded_question['numb'] = question_number
        decoded_question['options'] = options
        question_number += 1
        questions_with_options.append(decoded_question)

    # Get statistics from finished quiz
    if request.method == 'POST':
        stats = request.get_json()
        category = Category.query.filter(Category.categoryName == category,
                                         or_(Category.createdBy == current_user.id, Category.createdBy == None)).first()
        user_stats = Statistic(
            categoryId=category.categoryId,
            goodAnswers=stats['good'],
            wrongAnswers=stats['wrong'],
            score=stats['totalScore'],
            date=datetime.datetime.utcnow(),
            timeInSeconds=stats['totalTime']
        )
        current_user.statistics.append(user_stats)
        db.session.commit()
    if request.method == 'GET':
        redirect(
            url_for('learn', username=username, category=category, questions_json=questions_with_options, time=time))
    return render_template('learn.html', username=username, category=category, questions_json=questions_with_options,
                           time=time)
