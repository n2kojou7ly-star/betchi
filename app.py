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

@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    student_id = session['student_id']
    if request.method == 'POST':
        if request.form.get('action') == 'delete':
            db.delete_availability(request.form['slot_id'], student_id)
        else:
            db.add_availability(
                student_id,
                request.form['date'],
                int(request.form['period'])
            )
        return redirect(url_for('teacher'))
    return render_template('teacher.html', slots=db.get_availabilities(student_id))

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

@app.before_request
def require_login():
    allowed = ('index', 'login', 'signup', 'static')
    if request.endpoint not in allowed and 'student_id' not in session:
        return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/settings')
def settings():
    user = db.get_user_by_id(session['student_id'])
    subjects = db.get_all_subjects()
    teaching_subject_ids = db.get_teaching_subject_ids(session['student_id'])
    return render_template(
        'settings.html',
        user=user,
        subjects=subjects,
        teaching_subject_ids=teaching_subject_ids
    )

@app.route('/points')
def points():
    balance = db.get_point_balance(session['student_id'])
    return render_template('points.html', balance=balance)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)