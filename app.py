from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'sharik_beaz'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_users_df():
    excel_file = 'users.xlsx'
    if os.path.exists(excel_file):
        try:
            df = pd.read_excel(excel_file, engine='openpyxl')
        except Exception:
            df = pd.DataFrame(columns=['Логин', 'Пароль'])
    else:
        df = pd.DataFrame(columns=['Логин', 'Пароль'])
    return df

def save_user(username, password):
    excel_file = 'users.xlsx'
    df = get_users_df()
    new_row = pd.DataFrame({'Логин': [username], 'Пароль': [password]})
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(excel_file, index=False, engine='openpyxl')

def user_exists(username):
    df = get_users_df()
    return username in df['Логин'].values

def check_password(username, password):
    df = get_users_df()
    user_row = df[df['Логин'] == username]
    if not user_row.empty:
        stored_password = user_row.iloc[0]['Пароль']
        return stored_password == password
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if user_exists(username):
            flash('Логин уже занят. Придумайте другой.', 'error')
            return redirect(url_for('register'))

        save_user(username, password)
        flash('Регистрация успешна!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if check_password(username, password):
            session['user'] = username
            return redirect(url_for('apply'))
        else:
            flash('Неверный логин или пароль', 'error')

    return render_template('login.html')

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        weight = request.form.get('weight')
        height = request.form.get('height')
        transport = request.form.get('transport')
        notes = request.form.get('notes')

        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_path = filename

        # Запись в Excel
        excel_file = 'data.xlsx'
        df = pd.DataFrame([{
            'Имя': name,
            'Вес': weight,
            'Рост': height,
            'Транспорт': transport,
            'Примечания': notes,
            'Фото': photo_path
        }])

        if os.path.exists(excel_file):
            try:
                existing_df = pd.read_excel(excel_file, engine='openpyxl')
            except Exception:
                existing_df = pd.DataFrame(columns=['Имя', 'Вес', 'Рост', 'Транспорт', 'Примечания', 'Фото'])
            new_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            new_df = df

        new_df.to_excel(excel_file, index=False, engine='openpyxl')

        return redirect(url_for('success'))

    return render_template('apply.html')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Неверный логин или пароль', 'error')
    return render_template('admin_login.html')

@app.route('/admin_panel')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    excel_file = 'data.xlsx'
    if os.path.exists(excel_file):
        try:
            df = pd.read_excel(excel_file, engine='openpyxl')
        except Exception:
            df = pd.DataFrame(columns=['Имя', 'Вес', 'Рост', 'Транспорт', 'Примечания', 'Фото'])
    else:
        df = pd.DataFrame(columns=['Имя', 'Вес', 'Рост', 'Транспорт', 'Примечания', 'Фото'])

    return render_template('admin_panel.html', data=df.to_html(index=False, escape=False))

if __name__ == '__main__':
    app.run(debug=True)