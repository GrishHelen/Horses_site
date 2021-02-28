from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_restful import abort, Resource
from flask import jsonify
from .db_session import SqlAlchemyBase, create_session
import sqlalchemy
from flask_login import UserMixin


def abort_if_note_not_found(note_id):
    session = create_session()
    notes = session.query(Note).get(note_id)
    if not notes:
        abort(404, message=f"Note {note_id} not found")


class Note(SqlAlchemyBase, UserMixin):
    __tablename__ = 'notes'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    date = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    time = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    horse = sqlalchemy.Column(sqlalchemy.Text, nullable=True)

    def __repr__(self):
        session = create_session()
        for note in session.query(Note).all():
            print(note)


class OneNote(FlaskForm):
    date = StringField('Дата', validators=[DataRequired()])
    time = StringField('Время', validators=[DataRequired()])
    text = StringField('Имя ребенка', validators=[DataRequired()])
    horse = StringField('')
    submit = SubmitField('Сохранить изменения')


class NoteResource(Resource):
    def get(self, note_id):
        abort_if_note_not_found(note_id)
        session = create_session()
        note = session.query(Note).get(note_id)
        return jsonify({'note': note.to_dict(only=('name', 'surname', 'login'))})

    def delete(self, note_id):
        abort_if_note_not_found(note_id)
        session = create_session()
        note = session.query(Note).get(note_id)
        session.delete(note)
        session.commit()
