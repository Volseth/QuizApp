from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import Form, BooleanField, StringField, PasswordField, validators, TextAreaField, SubmitField, SelectField
from wtforms.validators import ValidationError

from quizapp.models import User


class QuizForm(FlaskForm):
    time_select = SelectField(label='Czas na odpowiedź w sekundach', coerce=int, validators=[validators.DataRequired("Wybierz czas na odpowiedź")])

    category = SelectField(label='Kategoria quizu', validators=[validators.DataRequired("Wybierz kategorię quizu")])

    submit = SubmitField("")


class QuestionForm(FlaskForm):
    question_text = TextAreaField("Pytanie", validators=[validators.DataRequired("Wprowadź treść pytania")])

    answer_text = TextAreaField("Odpowiedź", validators=[validators.DataRequired("Wprowadź odpowiedź")])

    submit = SubmitField("")


class CategoryForm(FlaskForm):
    category_name = StringField("Nazwa kategorii", validators=[validators.Length(min=3, max=25),
                                                               validators.DataRequired("Wprowadź nazwę")])

    parent_category = SelectField(label="Kategoria nadrzędna")

    picture = FileField('Zaktualizuj zdjęcie kategorii',
                        validators=[FileAllowed(['jpg', 'png'], "Zły format pliku! Dozwolone formaty to jpg lub png")])

    submit = SubmitField("")


class UpdateAccountForm(FlaskForm):
    name = StringField("Nazwa profilu", validators=[validators.Length(min=3, max=20),
                                                    validators.DataRequired("Wprowadź nazwę")])

    email = StringField("Email", validators=[validators.Email(message="Prosze wprowadzić poprawny adres email")])

    picture = FileField('Zaktualizuj zdjęcie profilowe',
                        validators=[FileAllowed(['jpg', 'png'], "Zły format pliku! Dozwolone formaty to jpg lub png")])

    submit = SubmitField("")

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email jest już w użyciu. Proszę wybrać inny.')


class LoginForm(Form):
    username = StringField("Nazwa użytkownika", validators=[validators.Length(min=3, max=25),
                                                            validators.DataRequired(
                                                                message="Proszę uzupełnić pole email!")])
    password = PasswordField("Hasło", validators=[validators.DataRequired(message="Nie podałeś hasła!")])

    remember = BooleanField("Zapamiętaj mnie!")

    submit = SubmitField("")


class RegisterForm(Form):
    name = StringField("Nazwa profilu", validators=[validators.Length(min=3, max=20),
                                                    validators.DataRequired("Wprowadź nazwę")])
    username = StringField("Nazwa użytkownika", validators=[validators.Length(min=3, max=20),
                                                            validators.DataRequired(
                                                                message="Wprowadź nazwę użytkownika")])

    email = StringField("Email", validators=[validators.Email(message="Prosze wprowadzić poprawny adres email")])

    password = PasswordField("Hasło", validators=[
        validators.DataRequired(message="Proszę wprowadzić hasło dla konta"),
        validators.equal_to(fieldname="confirm_password", message="Twoje hasła muszą się zgadzać")
    ])

    confirm_password = PasswordField("Potwierdź hasło",
                                     validators=[validators.DataRequired(message="Proszę potwierdzić hasło")])

    submit = SubmitField("")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Użytkownik o takiej nazwie już istnieje. Proszę wybrać inną nazwę.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email jest już w użyciu. Proszę wybrać inny.')
