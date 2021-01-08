from quizapp import db
from quizapp import login_manager
from flask_login import UserMixin


# Method for login sessions
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


user_interests = db.Table('user_interests',
                          db.Column('username', db.String(20), db.ForeignKey('users.username'), primary_key=True),
                          db.Column('category', db.String(25), db.ForeignKey('categories.categoryName'),
                                    primary_key=True))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=False)
    username = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(256), unique=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.png')
    categories = db.relationship('Category', backref='categories_created', lazy=True)
    statistics = db.relationship('Statistic', backref='quiz_results', lazy=True)
    questions = db.relationship('Question', backref='questions_added', lazy=True)
    interests = db.relationship('Category', secondary=user_interests, lazy='joined', backref='interests_checked')

    def __repr__(self):
        return str(self.name + " " + self.username)


class Category(db.Model):
    __tablename__ = 'categories'
    categoryId = db.Column(db.Integer, primary_key=True)
    categoryName = db.Column(db.String(25), unique=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.png')
    parentCategory = db.Column(db.String(25), unique=False, nullable=True)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_questions = db.relationship('Question', backref='category_questions', lazy='joined')

    def __repr__(self):
        return str(self.categoryName)


class Answer(db.Model):
    __tablename__ = 'answers'
    answerId = db.Column(db.Integer, primary_key=True)
    answerText = db.Column(db.String(100), unique=False)
    questionId = db.Column(db.Integer, db.ForeignKey('questions.questionId', ondelete="CASCADE"), nullable=False, unique=False)


class Question(db.Model):
    __tablename__ = 'questions'
    questionId = db.Column(db.Integer, primary_key=True)
    questionText = db.Column(db.String(100), nullable=False, unique=False)
    categoryId = db.Column(db.Integer, db.ForeignKey('categories.categoryId'))
    createdBy = db.Column(db.Integer, db.ForeignKey('users.id'))
    answers = db.relationship('Answer', backref='answers', lazy=True, uselist=False, cascade="all,delete")

    def serialize(self):
        return {"questionId": self.questionId,
                "question": self.questionText,
                "answer": self.answers.answerText
                }


class Statistic(db.Model):
    __tablename__ = 'statistics'
    statId = db.Column(db.Integer, primary_key=True)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.id'))
    categoryId = db.Column(db.Integer, db.ForeignKey('categories.categoryId'))
    goodAnswers = db.Column(db.Integer, nullable=False)
    wrongAnswers = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    timeInSeconds = db.Column(db.Integer, nullable=False)
