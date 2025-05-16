#база данных
from server import app
from extensions import db
from models import Section, User

with app.app_context():
    db.create_all()


def add_sections():
    with app.app_context():
        db.session.commit()


if __name__ == '__main__':
    add_sections()