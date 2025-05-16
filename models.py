#библиотеки
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from extensions import db


class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    topics = db.relationship('Topic', back_populates='user', lazy=True)
    is_admin = db.Column(db.Boolean, default=False)


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    topics = db.relationship('Topic', backref='section', lazy=True)


class Topic(db.Model):
    id = Column(Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    content = Column(Text, nullable=False)
    date_posted = Column(DateTime, nullable=False, default=datetime.utcnow)
    section_id = Column(Integer, ForeignKey('section.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='topics')
    image_filename = db.Column(db.String(128))
    # Путь к файлу изображения


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='messages')
