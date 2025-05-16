# библиотеки
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from forms import RegistrationForm, LoginForm, SectionForm
from forms import QuestionForm
from flask import flash
from forms import ImageUploadForm
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
from extensions import db

db.init_app(app)

with app.app_context():
    db.create_all()

from models import User, Section, Topic, Message

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# модерация
# плохие слова
banned_words = [
    "блин",
]


# если плохие слова есть
def contains_banned_word(text, banned_words):
    for word in banned_words:
        if word in text.lower():
            return True
    return False


@app.route('/')
@app.route('/index')
def index():
    sections = Section.query.all()
    return render_template("index.html", sections=sections)



@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_image():
    form = ImageUploadForm()
    if form.validate_on_submit():
        if contains_banned_word(form.image.data.filename, banned_words):
            flash('Название файла содержит неприемлемое слово и не может быть использовано.', 'danger')
            return render_template('upload_image.html', form=form)
        # Сохранение изображения
        image_data = request.files[form.image.name]
        filename = secure_filename(image_data.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_data.save(image_path)

        # Создание нового сообщения в теме с изображением
        topic = Topic(

            content=filename,
            section_id=form.section.data.id,
            user_id=current_user.id,
            # Сохранение информации о пользователе
            image_filename=filename
        )
        db.session.add(topic)
        db.session.commit()

        flash('Изображение успешно загружено.', 'success')
        return redirect(url_for('section', section_id=form.section.data.id))
    return render_template('upload_image.html', form=form)


@app.route('/ask_question', methods=['GET', 'POST'])
@login_required
def ask_question():
    form = QuestionForm()
    if form.validate_on_submit():
        if contains_banned_word(form.content.data, banned_words):
            flash('Ваш вопрос содержит неприемлемое слово и не может быть опубликован.', 'danger')
            return render_template('ask_question.html', form=form)

        # Генерация заголовка из содержания вопроса
        title = form.content.data[:50] if len(form.content.data) > 50 else form.content.data

        # Заголовок не пустой
        title = title or "Без заголовка"

        new_topic = Topic(title=title, content=form.content.data, section_id=1, user_id=current_user.id)
        db.session.add(new_topic)
        db.session.commit()
        flash('Вопрос добавлен.')
        return redirect(url_for('index'))
    return render_template('ask_question.html', form=form)


@app.route('/sections/<int:section_id>', methods=['GET', 'POST'])
@login_required
def section(section_id):
    form = QuestionForm()
    section = Section.query.get_or_404(section_id)
    if form.validate_on_submit():
        # Проверка на плохие слова
        if contains_banned_word(form.content.data, banned_words):
            flash('Вопрос содержит неприемлемые слова.', 'danger')
            return redirect(url_for('section', section_id=section_id))

        # Создание нового вопроса
        new_topic = Topic(
            content=form.content.data,
            section_id=section_id,
            user_id=current_user.id,
            # связывает вопрос с пользователем
            # не нужно передавать user_email, потому что мы уже передали user_id
        )
        db.session.add(new_topic)
        db.session.commit()
        flash('Вопрос добавлен.', 'success')
        return redirect(url_for('section', section_id=section_id))
    topics = Topic.query.filter_by(section_id=section_id).order_by(Topic.date_posted.desc()).all()
    users = {u.id: u for u in User.query.all()}
    return render_template('section.html', section=section, form=form, topics=topics, users=users)


@app.route('/topics/<int:topic_id>')
def topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    user_email = topic.user.email
    # У объекта Topic есть связь 'user'
    messages = [
        {
            'content': message.content,
            'image_filename': url_for('static',
                                      filename='uploads/' + message.image_filename) if message.image_filename else None,
            'user_email': message.user.email
            # у объекта Message тоже есть связь 'user'
        }
        for message in user_email

    ]
    return render_template('topic.html', topic=topic, user_email=user_email, messages=messages)


@app.route('/create_section', methods=['GET', 'POST'])
@login_required
def create_section():
    form = SectionForm()
    if form.validate_on_submit():
        # Проверка названия и описания раздела на запрещенные слова
        if contains_banned_word(form.title.data, banned_words) or contains_banned_word(form.description.data,
                                                                                       banned_words):
            flash('Название или описание раздела содержат неприемлемые слова.', 'danger')
            return render_template('create_section.html', form=form)

        new_section = Section(title=form.title.data, description=form.description.data)
        db.session.add(new_section)
        db.session.commit()
        flash('Новый раздел успешно создан.', 'success')
        return redirect(url_for('index'))
    return render_template('create_section.html', form=form)


@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))

    topics = Topic.query.all()
    section_topics = dict()
    sections = Section.query.all()
    for t in topics:
        section_topics[t.id] = Section.query.get(t.section_id).title
    print(section_topics)
    print(topics[0].section)
    messages = Message.query.all()
    return render_template('admin_dashboard.html', topics=topics, messages=messages, sections=sections,
                           section_topics=section_topics)




@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email уже зарегистрирован.')
            return redirect(url_for('register_user'))
        new_user = User(email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация прошла успешно.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверный логин или пароль.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Вход', form=form)


@app.route('/delete_topic/<int:topic_id>', methods=['POST'])
@login_required
def delete_topic(topic_id):
    if not current_user.is_admin:
        flash('У вас нет прав для выполнения этого действия.', 'danger')
        return redirect(url_for('index'))
    topic = Topic.query.get_or_404(topic_id)
    db.session.delete(topic)
    db.session.commit()
    flash('Тема успешно удалена.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_section/<int:section_id>', methods=['POST'])
@login_required
def delete_section(section_id):
    if not current_user.is_admin:
        flash('У вас нет прав для выполнения этого действия.', 'danger')
        return redirect(url_for('index'))
    section = Section.query.get_or_404(section_id)
    db.session.delete(section)
    db.session.commit()
    flash('Тема успешно удалена.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    if not current_user.is_admin:
        flash('У вас нет прав администратора для выполнения этой операции.', 'danger')
        return redirect(url_for('index'))

    topic = Topic.query.get_or_404(question_id)
    db.session.delete(topic)
    db.session.commit()
    flash('Вопрос успешно удалён.', 'success')
    return redirect(url_for('index'))



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5003)
