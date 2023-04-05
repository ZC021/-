from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user,  logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

def get_plant_info(plant_name):
    data_file = os.path.join(os.path.dirname(__file__), 'herbs.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if plant_name in data:
            return data[plant_name]
    return None

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    plants = db.relationship('Plant', backref='user', lazy=True)

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, default=1)
    temperature_min = db.Column(db.Float, nullable=False)
    temperature_max = db.Column(db.Float, nullable=False)
    humidity_min = db.Column(db.Float, nullable=False)
    humidity_max = db.Column(db.Float, nullable=False)
    soil_moisture_min = db.Column(db.Float, nullable=False)
    soil_moisture_max = db.Column(db.Float, nullable=False)


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('dashboard', first_time=True))
            else:
                flash("비밀번호가 틀렸습니다.")
        else:
            flash("아이디가 맞지 않습니다.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("이미 존재하는 사용자명입니다. 다른 사용자명을 입력해주세요.")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("회원가입이 완료되었습니다. 로그인 해주세요.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    first_time = request.args.get('first_time', False)
    if request.method == 'POST':
        plant_name = request.form['plant']

        # Get plant info from file
        plant_info = get_plant_info(plant_name)
        if plant_info:
            # Pass plant info to template
            return render_template('plant_info.html', plant_name=plant_name, plant_info=plant_info)
        else:
            flash("해당하는 식물 정보가 없습니다.")
            return redirect(url_for('dashboard', first_time=False))

    return render_template('dashboard.html', first_time=first_time)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)