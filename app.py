"""
Fraud Detection System - Complete Flask Application
With authentication, admin dashboard, CSV batch processing, and model metrics
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, pickle, numpy as np, os, io, csv
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "fraud_detection_key_2024"
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# ── Database Functions ──────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect('fraud.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'pending',
            organization TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            hour INTEGER,
            location INTEGER,
            device INTEGER,
            payment INTEGER,
            is_new_account INTEGER,
            num_items INTEGER,
            ml_score REAL,
            rule_boost REAL,
            final_score REAL,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS batch_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            total_transactions INTEGER,
            fraud_count INTEGER,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit(); conn.close()

# ── Load Model ──────────────────────────────────────────────────────────────
with open("model.pkl", "rb") as f:
    mdl = pickle.load(f)
rf, gb, scaler = mdl["rf"], mdl["gb"], mdl["scaler"]
MODEL_AUC = mdl.get("auc", 0)
print(f"Model loaded | AUC: {MODEL_AUC}")

# ── Hybrid Detection ────────────────────────────────────────────────────────
def hybrid_detect(amount, hour, location, device, is_new, num_items, payment):
    X = scaler.transform([[amount, hour, location, device, is_new, num_items, payment]])
    rf_p = rf.predict_proba(X)[0][1]
    gb_p = gb.predict_proba(X)[0][1]
    ml_score = 0.55 * rf_p + 0.45 * gb_p

    rule_boost = 0.0
    if amount > 20000: rule_boost += 0.18
    elif amount > 12000: rule_boost += 0.10
    if location == 3 and device == 3: rule_boost += 0.20
    elif location == 3: rule_boost += 0.10
    if device == 3: rule_boost += 0.12
    elif device == 2 and is_new == 1: rule_boost += 0.10
    if hour in range(0, 5): rule_boost += 0.07
    if num_items > 12: rule_boost += 0.08
    if payment == 4 and amount > 5000: rule_boost += 0.08

    final_score = min(ml_score + rule_boost, 1.0)
    result = "Fraud" if final_score >= 0.5 else "Legit"

    return {
        "ml_score": round(ml_score * 100, 1),
        "rule_boost": round(rule_boost * 100, 1),
        "final_score": round(final_score * 100, 1),
        "result": result
    }

# ── Auth Decorators ────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        conn = get_db()
        user = conn.execute("SELECT role FROM users WHERE id=?", (session['user_id'],)).fetchone()
        conn.close()
        if not user or user['role'] != 'admin':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ── Routes ────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        org = request.form.get('organization', 'N/A')

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, email, password, organization, status) VALUES (?,?,?,?,?)",
                (username, email, generate_password_hash(password), org, 'pending')
            )
            conn.commit()
            flash('Registration successful! Pending admin approval.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!', 'error')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            if user['status'] == 'rejected':
                flash('Your account has been rejected.', 'error')
            elif user['status'] == 'pending':
                flash('Your account is pending admin approval.', 'warning')
            else:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                flash(f'Welcome {username}!', 'success')
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# ── Admin Dashboard ─────────────────────────────────────────────────────────
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM users WHERE status='pending'").fetchone()[0]
    total_txn = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    
    pending_users = conn.execute(
        "SELECT id, username, email, organization FROM users WHERE status='pending'"
    ).fetchall()
    
    all_users = conn.execute(
        "SELECT id, username, email, organization, status FROM users ORDER BY created_at DESC"
    ).fetchall()
    
    transactions = conn.execute(
        "SELECT t.*, u.username FROM transactions t LEFT JOIN users u ON t.user_id=u.id ORDER BY t.id DESC LIMIT 50"
    ).fetchall()
    
    conn.close()

    return render_template('admin_dashboard.html',
                          total_users=total_users,
                          pending=pending,
                          total_txn=total_txn,
                          pending_users=pending_users,
                          all_users=all_users,
                          transactions=transactions)

@app.route('/admin/approve/<int:user_id>', methods=['POST'])
@admin_required
def approve_user(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET status='approved', role='user' WHERE id=?", (user_id,))
    conn.commit(); conn.close()
    flash('User approved!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:user_id>', methods=['POST'])
@admin_required
def reject_user(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET status='rejected' WHERE id=?", (user_id,))
    conn.commit(); conn.close()
    flash('User rejected!', 'success')
    return redirect(url_for('admin_dashboard'))

# ── User Dashboard ────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    user_txns = conn.execute(
        "SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (session['user_id'],)
    ).fetchall()
    
    total = conn.execute("SELECT COUNT(*) FROM transactions WHERE user_id=?",
                        (session['user_id'],)).fetchone()[0]
    fraud = conn.execute("SELECT COUNT(*) FROM transactions WHERE user_id=? AND result='Fraud'",
                        (session['user_id'],)).fetchone()[0]
    legit = total - fraud
    avg_score = conn.execute("SELECT AVG(final_score) FROM transactions WHERE user_id=?",
                            (session['user_id'],)).fetchone()[0] or 0
    conn.close()

    return render_template('dashboard.html',
                          transactions=user_txns,
                          total=total, fraud=fraud, legit=legit,
                          avg_score=round(avg_score, 1))

# ── Predict Page (Single Transaction) ─────────────────────────────────────
@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            hour = int(request.form['hour'])
            location = int(request.form['location'])
            device = int(request.form['device'])
            payment = int(request.form['payment'])
            is_new = int(request.form.get('is_new', 0))
            num_items = int(request.form['num_items'])

            result = hybrid_detect(amount, hour, location, device, is_new, num_items, payment)

            conn = get_db()
            conn.execute(
                "INSERT INTO transactions (user_id,amount,hour,location,device,payment,is_new_account,num_items,ml_score,rule_boost,final_score,result) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (session['user_id'], amount, hour, location, device, payment, is_new, num_items,
                 result['ml_score'], result['rule_boost'], result['final_score'], result['result'])
            )
            conn.commit(); conn.close()

            flash(f"Prediction: {result['result']} (Score: {result['final_score']}%)", 'success')
            return render_template('predict.html', result=result)
        except Exception as e:
            flash(f"Error: {e}", 'error')

    return render_template('predict.html')

# ── CSV Batch Upload ──────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/analytics', methods=['GET', 'POST'])
@login_required
def analytics():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)

        file = request.files['file']
        if not file or not allowed_file(file.filename):
            flash('Invalid file format! Please upload a CSV.', 'error')
            return redirect(request.url)

        try:
            stream = io.StringIO(file.stream.read().decode('UTF8'), newline=None)
            csv_reader = csv.DictReader(stream)

            total_txn = 0
            fraud_count = 0

            for row in csv_reader:
                amount = float(row['amount'])
                hour = int(row.get('hour', 12))
                location = int(row.get('location', 1))
                device = int(row.get('device', 1))
                payment = int(row.get('payment', 1))
                is_new = int(row.get('is_new', 0))
                num_items = int(row.get('num_items', 1))

                result = hybrid_detect(amount, hour, location, device, is_new, num_items, payment)
                
                conn = get_db()
                conn.execute(
                    "INSERT INTO transactions (user_id,amount,hour,location,device,payment,is_new_account,num_items,ml_score,rule_boost,final_score,result) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (session['user_id'], amount, hour, location, device, payment, is_new, num_items,
                     result['ml_score'], result['rule_boost'], result['final_score'], result['result'])
                )
                conn.commit(); conn.close()

                total_txn += 1
                if result['result'] == 'Fraud':
                    fraud_count += 1

            conn = get_db()
            conn.execute(
                "INSERT INTO batch_uploads (user_id,filename,total_transactions,fraud_count,status) VALUES (?,?,?,?,?)",
                (session['user_id'], secure_filename(file.filename), total_txn, fraud_count, 'completed')
            )
            conn.commit(); conn.close()

            flash(f"CSV processed! {total_txn} transactions, {fraud_count} frauds detected.", 'success')

        except Exception as e:
            flash(f"Error processing CSV: {e}", 'error')

    return render_template('analytics.html')

# ── Model Info Page ───────────────────────────────────────────────────────
@app.route('/model-info')
def model_info():
    # Calculate metrics from test set (simulated)
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    from sklearn.model_selection import train_test_split

    # Regenerate test data for metrics
    np.random.seed(42)
    n_legit, n_fraud = 8000, 2000
    
    la = np.random.lognormal(6.5, 0.8, n_legit).clip(50, 8000)
    lh = np.random.choice(range(24), n_legit)
    ll = np.random.choice([1,2,3], n_legit, p=[0.70,0.20,0.10])
    ld = np.random.choice([1,2,3], n_legit, p=[0.80,0.15,0.05])
    ln = np.random.choice([0,1], n_legit, p=[0.90,0.10])
    li = np.random.randint(1, 8, n_legit)
    lp = np.random.choice([1,2,3,4], n_legit, p=[0.50,0.25,0.15,0.10])

    fa = np.random.lognormal(8.5, 1.0, n_fraud).clip(500, 30000)
    fh = np.random.choice(range(24), n_fraud)
    fl = np.random.choice([1,2,3], n_fraud, p=[0.10,0.25,0.65])
    fd = np.random.choice([1,2,3], n_fraud, p=[0.10,0.30,0.60])
    fn = np.random.choice([0,1], n_fraud, p=[0.30,0.70])
    fi = np.random.randint(1, 20, n_fraud)
    fp = np.random.choice([1,2,3,4], n_fraud, p=[0.20,0.15,0.20,0.45])

    X = np.column_stack([
        np.concatenate([la, fa]),
        np.concatenate([lh, fh]),
        np.concatenate([ll, fl]),
        np.concatenate([ld, fd]),
        np.concatenate([ln, fn]),
        np.concatenate([li, fi]),
        np.concatenate([lp, fp]),
    ])
    y = np.concatenate([np.zeros(n_legit, dtype=int), np.ones(n_fraud, dtype=int)])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_test_s = scaler.transform(X_test)

    rf_p = rf.predict_proba(X_test_s)[:, 1]
    gb_p = gb.predict_proba(X_test_s)[:, 1]
    hybrid = 0.55 * rf_p + 0.45 * gb_p
    y_pred = (hybrid >= 0.5).astype(int)

    accuracy = round(accuracy_score(y_test, y_pred) * 100, 1)
    precision = round(precision_score(y_test, y_pred) * 100, 1)
    recall = round(recall_score(y_test, y_pred) * 100, 1)
    f1 = round(f1_score(y_test, y_pred) * 100, 1)

    # Confusion matrix
    from sklearn.metrics import confusion_matrix
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    # Classification report
    from sklearn.metrics import classification_report
    report = classification_report(y_test, y_pred, output_dict=True)

    return render_template('model_info.html',
                          accuracy=accuracy, precision=precision,
                          recall=recall, f1=f1,
                          tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp),
                          auc=MODEL_AUC,
                          report=report)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    init_db()
    print("Starting server at http://127.0.0.1:5000")
    app.run(debug=True)