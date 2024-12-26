from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import random
import csv

# Создание приложения Flask
app = Flask(__name__)

# Конфигурация базы данных (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quotes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель таблицы для цитат
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, default=0)
    times_competed = db.Column(db.Integer, default=0)

# Модель таблицы для сохранённых результатов
class SessionResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_data = db.Column(db.Text, nullable=False)

# Обнуляем таблицу цитат
def reset_quotes():
    for quote in Quote.query.all():
        quote.points = 0
        quote.times_competed = 0
    db.session.commit()

# Функция импорта данных из CSV
def import_csv_to_db():
    with open('quotes.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            new_quote = Quote(text=row[0])
            db.session.add(new_quote)
        db.session.commit()

# Настройка базы данных
with app.app_context():
    db.create_all()
    reset_quotes()  # Обнуляем данные
    if Quote.query.count() == 0:  # Если таблица пуста
        import_csv_to_db()

# Главная страница
@app.route('/')
def index():
    quotes_need_more = Quote.query.filter(Quote.times_competed < 2).all()
    if len(quotes_need_more) < 2:
        return redirect(url_for('save_results'))
    random_quotes = random.sample(quotes_need_more, 2)
    return render_template('index.html', quote1=random_quotes[0], quote2=random_quotes[1])

# Маршрут для голосования
@app.route('/vote/<int:winner_id>/<int:loser_id>')
def vote(winner_id, loser_id):
    winner = Quote.query.get_or_404(winner_id)
    loser = Quote.query.get_or_404(loser_id)
    winner.points += 1
    winner.times_competed += 1
    loser.times_competed += 1
    db.session.commit()
    return redirect(url_for('index'))

# Сохранение результатов
@app.route('/save-results')
def save_results():
    quotes = Quote.query.order_by(Quote.points.desc()).all()
    result_text = "\n".join([f"{quote.text} — {quote.points} очков" for quote in quotes])
    new_result = SessionResult(result_data=result_text)
    db.session.add(new_result)
    db.session.commit()
    return redirect(url_for('session_list'))

# Страница со всеми сохранёнными результатами
@app.route('/sessions')
def session_list():
    sessions = SessionResult.query.all()
    return render_template('sessions.html', sessions=sessions)

# Страница с деталями конкретной сессии
@app.route('/session/<int:session_id>')
def session_detail(session_id):
    session = SessionResult.query.get_or_404(session_id)
    return f"<pre>{session.result_data}</pre>"

# Запуск приложения
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)