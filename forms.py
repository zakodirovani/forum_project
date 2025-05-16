#библиотеки
from wtforms import StringField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import Email, EqualTo
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms import FileField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired
from flask_wtf.file import FileRequired, FileAllowed
from models import Section

db = SQLAlchemy()


#кнопки
class QuestionForm(FlaskForm):
    content = TextAreaField('Содержание', validators=[DataRequired()])
    submit = SubmitField('Отправить')


#разделы
class SectionForm(FlaskForm):
    title = StringField('Название раздела', validators=[DataRequired()])
    description = TextAreaField('Описание')
    submit = SubmitField('Создать')


#регистрация
class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message='Некорректный email')])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите Пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Регистрация')


#вход
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='topics')


#темы
class ImageUploadForm(FlaskForm):
    section = QuerySelectField(
        'Выберите тему',
        query_factory=lambda: Section.query.all(),
        get_label='title',
        allow_blank=False
    )
    #изображение
    image = FileField('Выберите изображение',
                      validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Только изображения!')])
    submit = SubmitField('Загрузить')
