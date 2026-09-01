from flask import Flask, render_template, redirect, url_for, session, request
from werkzeug.security import check_password_hash
import db

app = Flask(__name__)
app.secret_key = "betchi-dev-key"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/role', methods=['GET', 'POST'])
def role():
    if request.method == 'POST':
        session['role'] = request.form['role']
        if session['role'] == 'teacher':
            return redirect(url_for('teacher'))
        return redirect(url_for('student'))
    return render_template('role.html')

@app.route('/student')
def student():
    return render_template('student.html')

@app.route('/teacher')
def teacher():
    return render_template('teacher.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        user = db.get_user_by_id(student_id)
        if user and check_password_hash(user['password_hash'], password):
            session['student_id'] = student_id
            return redirect(url_for('role'))
        return render_template('login.html', error='学番かパスワードが違います')
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/points')
def points():
    return render_template('points.html')

if __name__ == '__main__':
    app.run(debug=True)