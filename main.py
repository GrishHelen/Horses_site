import datetime
from data import db_session
from data.users import User, LoginForm
from data.notes import Note, NoteResource, OneNote
from data.db_session import create_session
from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, logout_user, login_user, login_required, current_user


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

now = datetime.datetime.now()
today_date = '.'.join(str(datetime.datetime.now()).split()[0].split('-')[::-1])
WEEK = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']


def check_dates():
    try:
        session = db_session.create_session()
        all_notes = session.query(Note).all()
        for i in all_notes:
            if i.date == '' or i.time == '':
                session.delete(i)
                continue
            date = str(i.date).split('.')
            d = datetime.datetime(year=int(date[2]), month=int(date[1]), day=int(date[0]))
            a = d - now
            if abs(a.days) > 15:
                try:
                    note = session.query(Note).get(i.id)
                    session.delete(note)
                except Exception:
                    pass
        session.commit()
        all_notes = session.query(Note).all()
        kol = 0
        for _ in all_notes:
            kol += 1
        for i in range(-14, 15):
            d = str(now - datetime.timedelta(days=i)).split()[0].split('-')[::-1]
            date = datetime.date(year=int(d[-1]), month=int(d[1]), day=int(d[0]))
            if date.weekday() == 2:
                continue
            d = '.'.join(d)
            for time in range(8, 21):
                time = str(time) + ':00'
                empty_time_1 = session.query(Note).filter(Note.date == d).filter(Note.time == time).filter(
                    Note.text == '-')
                empty_time_2 = session.query(Note).filter(Note.date == d).filter(Note.time == time).filter(
                    Note.text == '')
                kolvo_1 = 0
                for _ in empty_time_1:
                    kolvo_1 += 1
                kolvo_2 = 0
                for _ in empty_time_2:
                    kolvo_2 += 1
                kolvo = kolvo_1 + kolvo_2
                if kolvo == 0:
                    note = Note(
                        date=d,
                        time=time,
                        text='-',
                        horse='-'
                    )
                    session.add(note)
        session.commit()
    except Exception as ex:
        print(ex)
        return redirect('/error')


@login_manager.user_loader
def load_user(user_id):
    try:
        session = db_session.create_session()
        return session.query(User).get(user_id)
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/change_note/<int:id>', methods=['GET', 'POST'])
def change_note(id):
    try:
        avialable_dates = []
        for i in range(-14, 15):
            d = '.'.join(str(now - datetime.timedelta(days=i)).split()[0].split('-')[::-1])
            avialable_dates.append(d)

        form = OneNote()
        if request.method == "GET":
            session = db_session.create_session()
            note = session.query(Note).filter(Note.id == id).first()
            if note:
                form.date.data = note.date
                form.time.data = note.time
                form.text.data = note.text
                form.horse.data = note.horse
            else:
                abort(404)
        if form.is_submitted():
            session = db_session.create_session()
            if str(form.date.data).strip() == '':
                return render_template('change_note.html', message='Введите дату', title='Редактирование записи',
                                       form=form, id=id, dates=avialable_dates)
            if str(form.time.data).strip() == '':
                return render_template('change_note.html', message='Введите время', title='Редактирование записи',
                                       form=form, id=id, dates=avialable_dates)
            if str(form.text.data).strip() == '-' or str(form.text.data).strip() == '':
                return render_template('change_note.html', message='Введите имя ребенка', title='Редактирование записи',
                                       form=form, id=id, dates=avialable_dates)
            note = session.query(Note).filter(Note.id == id).first()
            check_horse = list(session.query(Note).filter(Note.date == note.date, Note.time == note.time,
                                                          Note.horse == form.horse.data))
            is_horse = False
            for nn in check_horse:
                if nn.id != note.id:
                    is_horse = True
            if is_horse:
                return render_template('change_note.html', message='Эта лошадь уже занята. Выберите другую',
                                       title='Редактирование записи', form=form, id=id, dates=avialable_dates)

            if note:
                note.date = form.date.data
                note.time = form.time.data
                note.text = form.text.data
                note.horse = form.horse.data
                session.commit()
                return redirect(f'/one_day/{note.date}')
            else:
                abort(404)
        return render_template('change_note.html', title='Редактирование записи', form=form, id=id,
                               dates=avialable_dates)
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/del_note/<int:id>', methods=['GET', 'POST'])
def del_note(id):
    try:
        session = db_session.create_session()
        note = session.query(Note).filter(Note.id == id).first()
        date = today_date
        if note:
            date = note.date
            session.delete(note)
            session.commit()
        else:
            pass
        return redirect(f'/one_day/{date}')
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/add_note')
def add_note():
    try:
        session = db_session.create_session()
        note = Note(
            date='',
            time='',
            text='-',
            horse='-'
        )
        session.add(note)
        session.commit()
        return redirect(f'/change_note/{note.id}')
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        form = LoginForm()
        if form.validate_on_submit():
            session = db_session.create_session()
            user = session.query(User).filter(User.login == form.login.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
        return render_template('login.html', title='Авторизация', form=form)
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        return redirect("/")
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/')
@app.route('/today')
def today():
    try:
        if current_user.is_authenticated:
            return redirect('/today_admin')
        t = today_date.split('.')
        d = datetime.date(year=int(t[-1]), month=int(t[1]), day=int(t[0]))
        date_weekday = today_date + ', ' + WEEK[d.weekday()]
        if d.weekday() == 2:
            d = date_weekday + '. Выходной'
            return render_template('today.html', title='Сегодня', date=d, dict={})

        session = create_session()
        notes = session.query(Note).filter(Note.date == today_date)
        diction = {}
        for note in notes:
            if note.time in diction:
                diction[note.time].append(note)
            else:
                diction[note.time] = [note]
        dict = {}
        k = sorted(list(diction.keys()))
        k.sort(key=lambda a: int(a.split(':')[0]))
        for i in k:
            dict[i] = diction[i]
        return render_template('today.html', title='Сегодня', date=date_weekday, dict=dict)
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/one_day/<date>')
def one_day(date):
    try:
        if current_user.is_authenticated:
            return redirect(f'one_day_admin/{date}')
        dd = date.split('.')
        d = datetime.datetime(year=int(dd[2]), month=int(dd[1]), day=int(dd[0]))
        date_weekday = date + ', ' + WEEK[d.weekday()]
        a = now - d
        if abs(a.days) >= 15:
            date = date + '. Этот день недоступен'
            return render_template('one_day.html', title=date_weekday, date=date, dict={})

        if d.weekday() == 2:
            date = '.'.join(date.split('.')[:2]) + '. Выходной'
            return render_template('one_day.html', title=date_weekday, date=date, dict={})

        session = create_session()
        notes = session.query(Note).filter(Note.date == date)
        diction = {}
        for note in notes:
            if note.time in diction:
                diction[note.time].append(note)
            else:
                diction[note.time] = [note]
        dict = {}
        k = sorted(list(diction.keys()))
        k.sort(key=lambda x: int(x.split(':')[0]))
        for i in k:
            dict[i] = diction[i]
        return render_template('one_day.html', title=date, date=date_weekday, dict=dict)
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/ago')
def ago():
    try:
        check_dates()
        dates = []
        for i in range(-14, 0):
            d = str(now + datetime.timedelta(days=i)).split()[0].split('-')[::-1]
            date = datetime.date(year=int(d[-1]), month=int(d[1]), day=int(d[0]))
            a = ['.'.join(d), WEEK[date.weekday()]]
            dates.append(a)
        return render_template('ago.html', title='Прошлые 2 недели.html', first=dates[:7], second=dates[7:])
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/next')
def next():
    try:
        check_dates()
        dates = []
        for i in range(1, 15):
            d = str(now + datetime.timedelta(days=i)).split()[0].split('-')[::-1]
            date = datetime.date(year=int(d[-1]), month=int(d[1]), day=int(d[0]))
            a = ['.'.join(d), WEEK[date.weekday()]]
            dates.append(a)
        return render_template('next.html', title='Следующие 2 недели.html', first=dates[:7], second=dates[7:])
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/one_day_admin/<date>')
def one_day_admin(date):
    try:
        dd = date.split('.')
        d = datetime.datetime(year=int(dd[2]), month=int(dd[1]), day=int(dd[0]))
        date_weekday = date + ', ' + WEEK[d.weekday()]
        a = now - d
        if abs(a.days) >= 15:
            date = date_weekday + '. Этот день недоступен'
            return render_template('one_day.html', title=date_weekday, date=date, dict={})

        d = datetime.date(year=int(dd[-1]), month=int(dd[1]), day=int(dd[0]))
        if d.weekday() == 2:
            date = date_weekday + '. Выходной'
            return render_template('one_day.html', title=date_weekday, date=date, dict={})

        session = create_session()
        notes = session.query(Note).filter(Note.date == date)
        diction = {}
        for note in notes:
            if note.time in diction:
                diction[note.time].append(note)
            else:
                diction[note.time] = [note]
        dict = {}
        k = sorted(list(diction.keys()))
        k.sort(key=lambda a: int(a.split(':')[0]))
        for i in k:
            dict[i] = diction[i]
        return render_template('one_day_admin.html', title=date_weekday, date=date_weekday, dict=dict)
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/today_admin', methods=['GET', 'POST'])
def today_admin():
    try:
        t = today_date.split('.')
        d = datetime.date(year=int(t[-1]), month=int(t[1]), day=int(t[0]))
        date_weekday = today_date + ', ' + WEEK[d.weekday()]
        if d.weekday() == 2:
            d = date_weekday + '. Выходной'
            return render_template('today_admin.html', title='Сегодня', date=d, dict={})
        session = create_session()
        notes = session.query(Note).filter(Note.date == today_date)
        diction = {}
        for note in notes:
            if note.time in diction:
                diction[note.time].append(note)
            else:
                diction[note.time] = [note]
        dict = {}
        k = sorted(list(diction.keys()))
        k.sort(key=lambda a: int(a.split(':')[0]))
        for i in k:
            dict[i] = diction[i]
        return render_template('today_admin.html', title='Сегодня', date=date_weekday, dict=dict)
    except Exception as ex:
        print(ex)
        return redirect('/error')


@app.route('/one_day/one_day_admin/<date>')
def smth(date):
    return redirect(f'/one_day_admin/{date}')


@app.route('/error')
def error():
    return render_template('error.html')


def main():
    db_session.global_init("db/blogs.sqlite")
    check_dates()
    app.run()


if __name__ == '__main__':
    main()
