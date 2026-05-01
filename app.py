from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"
DATABASE = "bank_site.db"

CATEGORIES = {
    "cards": "Банковские карты",
    "credits": "Кредиты",
    "deposits": "Вклады",
    "security": "Финансовая безопасность",
}

ARTICLES = [
    ("cards", "Как выбрать дебетовую карту", "Дебетовая карта подходит для ежедневных расчетов, хранения средств и получения кешбэка. При выборе важно учитывать стоимость обслуживания, лимиты переводов, условия снятия наличных и наличие программы лояльности."),
    ("cards", "Кредитная карта: правила безопасного использования", "Кредитная карта удобна при краткосрочной нехватке средств. Главное правило — соблюдать льготный период, не снимать наличные без необходимости и заранее рассчитывать обязательный платеж."),
    ("cards", "Виртуальная карта для онлайн-покупок", "Виртуальная карта помогает отделить основные деньги от интернет-платежей. Ее можно быстро выпустить в личном кабинете и установить отдельный лимит на покупки."),
    ("cards", "Кешбэк и бонусы: как получить выгоду", "Бонусные программы позволяют возвращать часть расходов. Наибольший эффект достигается при выборе категорий, соответствующих реальным тратам клиента."),
    ("cards", "Что делать при потере карты", "При потере карты необходимо сразу заблокировать ее в приложении, по телефону горячей линии или через сотрудника банка. После блокировки можно заказать перевыпуск."),
    ("credits", "Потребительский кредит: основные условия", "Потребительский кредит выдается на личные цели. Перед оформлением следует оценить полную стоимость кредита, срок, размер ежемесячного платежа и возможность досрочного погашения."),
    ("credits", "Ипотека: этапы оформления", "Оформление ипотеки включает предварительное одобрение, подбор недвижимости, оценку объекта, проверку документов и регистрацию сделки."),
    ("credits", "Автокредит: преимущества и ограничения", "Автокредит позволяет приобрести автомобиль с распределением платежей во времени. Обычно автомобиль находится в залоге до полного погашения долга."),
    ("credits", "Рефинансирование кредита", "Рефинансирование помогает объединить несколько кредитов или снизить ставку. Перед подачей заявки следует сравнить итоговую переплату и комиссии."),
    ("credits", "Как повысить вероятность одобрения кредита", "Банк оценивает доход, кредитную историю, долговую нагрузку и стабильность занятости. Аккуратное погашение текущих обязательств повышает шанс одобрения."),
    ("deposits", "Вклад как инструмент сбережений", "Банковский вклад позволяет сохранить средства и получить процентный доход. Важно учитывать ставку, срок, возможность пополнения и частичного снятия."),
    ("deposits", "Накопительный счет и его особенности", "Накопительный счет отличается гибкостью: клиент может пополнять и снимать деньги без закрытия продукта, а проценты начисляются по условиям банка."),
    ("deposits", "Капитализация процентов", "Капитализация означает присоединение начисленных процентов к сумме вклада. Это увеличивает итоговый доход при длительном сроке размещения."),
    ("deposits", "Как выбрать срок вклада", "Срок вклада зависит от финансовой цели. Для краткосрочного резерва лучше выбирать гибкие продукты, для долгосрочных накоплений — фиксированную ставку."),
    ("deposits", "Страхование вкладов", "Система страхования вкладов защищает средства физических лиц в пределах установленного лимита. Клиенту важно проверять участие банка в системе страхования."),
    ("security", "Как распознать телефонных мошенников", "Мошенники часто создают ощущение срочности и просят назвать код из СМС. Сотрудники банка никогда не запрашивают такие коды и пароли."),
    ("security", "Правила безопасного интернет-банка", "Для защиты интернет-банка следует использовать сложный пароль, двухфакторную аутентификацию и не входить в личный кабинет с чужих устройств."),
    ("security", "Фишинговые сайты банков", "Фишинговые сайты копируют интерфейс банка и собирают данные клиентов. Перед вводом логина и пароля необходимо проверять адрес сайта."),
    ("security", "Безопасность платежей по QR-коду", "QR-платежи удобны, но требуют проверки получателя и суммы. Не следует сканировать коды из сомнительных источников."),
    ("security", "Что делать при подозрительной операции", "При подозрительной операции нужно немедленно заблокировать карту, обратиться в банк и проверить историю входов в личный кабинет."),
]

NEWS = [
    ("Запущена новая программа вкладов", "БанкПлюс обновил линейку вкладов для клиентов, планирующих накопления на срок от трех месяцев."),
    ("Повышены лимиты переводов", "Для подтвержденных клиентов увеличены дневные лимиты переводов между своими счетами."),
    ("Открыта онлайн-заявка на ипотеку", "Теперь предварительное решение по ипотеке можно получить через сайт банка."),
    ("Обновлен раздел финансовой безопасности", "На сайте опубликованы новые материалы о защите от мошенничества."),
    ("Расширены возможности обратной связи", "Клиенты могут направлять сообщения сотрудникам банка через форму контактов."),
]

def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'client',
        created_at TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT NOT NULL,
        amount TEXT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    for username, password, role in [("employee", "employee123", "employee"), ("client", "client123", "client")]:
        try:
            conn.execute("INSERT INTO users(username,password,role,created_at) VALUES(?,?,?,?)",
                         (username, generate_password_hash(password), role, datetime.now().strftime("%d.%m.%Y %H:%M")))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

@app.context_processor
def inject_globals():
    return dict(categories=CATEGORIES, current_user=session.get("user"), style=session.get("style", "standard"))

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            flash("Войдите в систему.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def employee_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "employee":
            abort(403)
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return render_template("index.html", news=NEWS[:3], articles=ARTICLES[:4])

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/articles")
def articles():
    return render_template("articles.html", articles=ARTICLES, active=None)

@app.route("/articles/<category>")
def category(category):
    if category not in CATEGORIES:
        abort(404)
    items = [a for a in ARTICLES if a[0] == category]
    return render_template("articles.html", articles=items, active=category)

@app.route("/article/<int:item_id>")
def article(item_id):
    if item_id < 1 or item_id > len(ARTICLES):
        abort(404)
    cat, title, text = ARTICLES[item_id - 1]
    return render_template("article.html", item_id=item_id, cat=cat, title=title, text=text)

@app.route("/news")
def news():
    return render_template("news.html", news=NEWS)

@app.route("/contacts", methods=["GET", "POST"])
def contacts():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO messages(name,email,text,created_at) VALUES(?,?,?,?)",
                     (request.form["name"], request.form["email"], request.form["text"], datetime.now().strftime("%d.%m.%Y %H:%M")))
        conn.commit()
        conn.close()
        flash("Сообщение отправлено сотруднику банка.")
        return redirect(url_for("contacts"))
    return render_template("contacts.html")

@app.route("/apply", methods=["POST"])
def apply():
    conn = db()
    conn.execute("INSERT INTO applications(product,amount,name,phone,created_at) VALUES(?,?,?,?,?)",
                 (request.form["product"], request.form.get("amount", ""), request.form["name"], request.form["phone"], datetime.now().strftime("%d.%m.%Y %H:%M")))
    conn.commit()
    conn.close()
    flash("Заявка принята. Сотрудник банка свяжется с вами.")
    return redirect(url_for("services"))

@app.route("/search")
def search():
    q = request.args.get("q", "").lower().strip()
    results = []
    if q:
        for i, (cat, title, text) in enumerate(ARTICLES, start=1):
            if q in title.lower() or q in text.lower() or q in CATEGORIES[cat].lower():
                results.append((i, cat, title, text))
        for title, text in NEWS:
            if q in title.lower() or q in text.lower():
                results.append((None, "news", title, text))
    return render_template("search.html", q=q, results=results)

@app.route("/sitemap")
def sitemap():
    pages = [
        ("Главная", "index"), ("О банке", "about"), ("Услуги", "services"),
        ("Статьи", "articles"), ("Новости", "news"), ("Контакты", "contacts"),
        ("Поиск", "search"), ("Вход", "login"), ("Регистрация", "register")
    ]
    return render_template("sitemap.html", pages=pages)

@app.route("/style/<mode>")
def set_style(mode):
    session["style"] = "visually" if mode == "visually" else "standard"
    return redirect(request.referrer or url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        role = "client"
        try:
            conn = db()
            conn.execute("INSERT INTO users(username,password,role,created_at) VALUES(?,?,?,?)",
                         (username, generate_password_hash(password), role, datetime.now().strftime("%d.%m.%Y %H:%M")))
            conn.commit()
            conn.close()
            flash("Пользователь создан. Теперь можно войти.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Такой логин уже существует.")
    return render_template("register.html")

@app.route("/employee/create-user", methods=["GET", "POST"])
@login_required
@employee_required
def create_user():
    if request.method == "POST":
        try:
            conn = db()
            conn.execute("INSERT INTO users(username,password,role,created_at) VALUES(?,?,?,?)",
                         (request.form["username"], generate_password_hash(request.form["password"]), request.form["role"], datetime.now().strftime("%d.%m.%Y %H:%M")))
            conn.commit()
            conn.close()
            flash("Учетная запись создана сотрудником.")
            return redirect(url_for("admin"))
        except sqlite3.IntegrityError:
            flash("Такой логин уже существует.")
    return render_template("create_user.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (request.form["username"],)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], request.form["password"]):
            session["user"] = user["username"]
            session["role"] = user["role"]
            flash("Вход выполнен.")
            return redirect(url_for("profile"))
        flash("Неверный логин или пароль.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Вы вышли из системы.")
    return redirect(url_for("index"))

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/employee")
@login_required
@employee_required
def admin():
    conn = db()
    users = conn.execute("SELECT username, role, created_at FROM users ORDER BY id DESC").fetchall()
    messages = conn.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    applications = conn.execute("SELECT * FROM applications ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", users=users, messages=messages, applications=applications)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

import os

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
