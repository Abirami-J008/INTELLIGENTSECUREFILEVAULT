from flask import Flask, render_template, request, redirect, session, send_from_directory, flash
import sqlite3
import os
import secrets
from datetime import datetime, timedelta
import bcrypt
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = "securevault123"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

download_history={}
security_alerts=[]
dept_icons = {

    "CSE":"💻",
    "ECE":"📡",
    "EEE":"⚡",
    "MECH":"⚙️",
    "CIVIL":"🏗️",
    "IT":"🌐",
    "COMMON":"☁️"

}
@app.before_request
def session_timeout_check():

    if "username" in session:

        last_activity = session.get("last_activity")

        if last_activity:

            last_time = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()

            if now - last_time > timedelta(minutes=10):

                # ✅ store message BEFORE clearing session
                flash("⏳ Session Timeout! Please login again")

                session.clear()

                return redirect("/login")

        session["last_activity"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# ---------------- FOLDERS ---------------- #

UPLOAD_FOLDER = "uploads"
COMMON_FOLDER = os.path.join(UPLOAD_FOLDER, "COMMON")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMMON_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- DATABASE ---------------- #

def get_db():
    
    conn = sqlite3.connect("vault.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- EMAIL FUNCTION ----------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # ONLY USERS TABLE UPDATED (SAFE ADD)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT,
        department TEXT,
        
        approved INTEGER DEFAULT 0,
        rejected INTEGER DEFAULT 0,
        failed_attempts INTEGER DEFAULT 0,
        lock_time TEXT,
        created_at TEXT
    )
    """)
    admin_password = bcrypt.hashpw(
    "Admin@123".encode(),
    bcrypt.gensalt()
    ).decode()

    cur.execute("""
    INSERT OR IGNORE INTO users(
    username,
    email,
    password,
    department,
    approved
    )
    VALUES(
    ?,
    ?,
    ?,
    ?,
    ?
    )
    """, (
    "admin",
    "admin123@gmail.com",
    admin_password,
    "COMMON",
    
    1
    ))


    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        department TEXT,
        activity TEXT,
        log_time TEXT
    )
    """)
    # Alerts table

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        department TEXT,

        email TEXT,

        alert_type TEXT,

        alert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)


    try:
        cur.execute("""
        ALTER TABLE users
        ADD COLUMN rejected INTEGER DEFAULT 0
        """)
    except:
        pass
    conn.commit()
    conn.close()
    

def get_key():
    if not os.path.exists("secret.key"):
        key = Fernet.generate_key()
        with open("secret.key", "wb") as f:
            f.write(key)
    else:
        with open("secret.key", "rb") as f:
            key = f.read()
    return key

fernet = Fernet(get_key())

# ---------------- LOG FUNCTION (UNCHANGED) ---------------- #

def add_log(username, department, activity):

    # 🧠 FIX: FORCE ADMIN COMMON ACTIVITY NOT TO MIX
    if department == "COMMON" and session.get("role") == "admin":
        department = "ADMIN_COMMON"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO logs(username, department, activity, log_time)
        VALUES (?, ?, ?, ?)
    """, (
        username,
        department,
        activity,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()
# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("home.html")

# ---------------- REGISTER (ONLY MODIFIED) ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        department = request.form.get("department")

        if not username or not email or not password or not confirm_password or not department:

            flash("All fields are required")
            return redirect("/register")

        if password != confirm_password:

            flash("Passwords do not match")
            return redirect("/register")

        conn = get_db()
        cur = conn.cursor()

        try:

            hashed_password = bcrypt.hashpw(
                password.encode(),
                bcrypt.gensalt()
            ).decode()

            cur.execute("""
            INSERT INTO users(
                username,
                email,
                password,
                department,
                approved,
                failed_attempts,
                lock_time,
                created_at
                
            )
            VALUES(
                ?, ?, ?, ?, 0, 0, NULL,?
            )
            """, (
                username,
                email,
                hashed_password,
                department,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()

            flash(
                "Registration submitted successfully. Waiting for Admin Approval."
            )

            return redirect("/login")

        except sqlite3.IntegrityError:

            flash("Email already registered")

            return redirect("/register")

        finally:

            conn.close()

    return render_template("register.html")
@app.route("/approve_user/<int:user_id>")
def approve_user(user_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET approved=1
    WHERE id=?
    """, (user_id,))

    conn.commit()
    conn.close()

    flash("User Approved Successfully")

    return redirect("/dashboard")
@app.route("/reject_user/<int:user_id>")
def reject_user(user_id):

    if session.get("username") != "admin":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET rejected=1
    WHERE id=?
    """,(user_id,))

    conn.commit()
    conn.close()

    flash("User Rejected ❌")

    return redirect("/pending_users")
@app.route("/login", methods=["GET", "POST"])
def login():

    msg = session.pop("timeout_msg", None)

    if msg:
        flash(msg)

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")
        department = request.form.get("department")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
        SELECT *
        FROM users
        WHERE email=?
        """, (email,))

        user = cur.fetchone()

        if not user:

            flash("User not found ❌")

            conn.close()

            return redirect("/login")

        
        # DEPARTMENT CHECK
        if user["department"] != department:

            flash("Department Mismatch ❌")

            conn.close()
            return redirect("/login")
        if user["rejected"] == 1:

            flash("Registration Rejected By Admin ❌")

            conn.close()

            return redirect("/login")

        if user["approved"] != 1:

            flash("Waiting For Admin Approval ⏳")

            conn.close()

            return redirect("/login")
            
        # ACCOUNT LOCK CHECK
        if user["lock_time"]:

            lock_until = datetime.strptime(
                user["lock_time"],
                "%Y-%m-%d %H:%M:%S"
            )

            if datetime.now() < lock_until:

                flash("Account Locked For 10 Minutes 🔒")

                conn.close()

                return redirect("/login")

            else:

                cur.execute("""
                UPDATE users
                SET failed_attempts=0,
                lock_time=NULL
                WHERE id=?
                """, (
                user["id"],
                ))

                cur.execute("""
                DELETE FROM alerts
                WHERE username=?
                AND alert_type='FAILED LOGIN 3 TIMES'
                """, (
                user["username"],
                ))

                conn.commit()
        # PASSWORD CHECK
        if not bcrypt.checkpw(
            password.encode(),
            user["password"].encode()
        ):

            attempts = (
                user["failed_attempts"] or 0
            ) + 1

            lock_time = None

            if attempts >= 3:

                lock_time = (
                    datetime.now()
                    + timedelta(minutes=10)
                ).strftime("%Y-%m-%d %H:%M:%S")

                cur.execute("""
                INSERT INTO alerts(
                    username,
                    alert_type
                )
                VALUES(?,?)
                """, (
                    user["username"],
                    "FAILED LOGIN 3 TIMES"
                ))

                flash(
                    "Account Locked For 10 Minutes 🔒"
                )

                attempts = 0

            else:

                flash(
                    f"Wrong Password ({attempts}/3)"
                )

            cur.execute("""
            UPDATE users
            SET failed_attempts=?,
                lock_time=?
            WHERE id=?
            """, (
                attempts,
                lock_time,
                user["id"]
            ))

            conn.commit()

            conn.close()

            return redirect("/login")

        # LOGIN SUCCESS

        cur.execute("""
        UPDATE users
        SET failed_attempts=0,
            lock_time=NULL
        WHERE id=?
        """, (
            user["id"],
        ))

        conn.commit()

        conn.close()
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        session["email"] = user["email"]

        session["department"] = user["department"]

        session.permanent = True

        session["last_activity"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        add_log(
            user["username"],
            user["department"],
            "LOGIN"
        )

        return redirect("/dashboard")

    return render_template("login.html")
@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "username" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM users
    WHERE id=?
    """, (
        session["user_id"],
    ))

    user = cur.fetchone()

    if not user:

        conn.close()

        flash("User Not Found ❌")

        return redirect("/dashboard")

    if request.method == "POST":

        current_password = request.form.get(
            "current_password"
        )

        new_password = request.form.get(
            "new_password"
        )

        confirm_password = request.form.get(
            "confirm_password"
        )

        # PASSWORD CHANGE

        if new_password:

            if not bcrypt.checkpw(
                current_password.encode(),
                user["password"].encode()
            ):

                flash(
                    "Current Password Incorrect ❌"
                )

                conn.close()

                return redirect("/profile")

            if new_password != confirm_password:

                flash(
                    "Passwords Do Not Match ❌"
                )

                conn.close()

                return redirect("/profile")

            hashed_password = bcrypt.hashpw(
                new_password.encode(),
                bcrypt.gensalt()
            ).decode()

            cur.execute("""
            UPDATE users
            SET password=?
            WHERE id=?
            """, (
                hashed_password,
                session["user_id"]
            ))

            conn.commit()

            add_log(
                session["username"],
                session["department"],
                "PASSWORD CHANGED"
            )

            flash(
                "Password Updated Successfully ✅"
            )

        conn.close()

        return redirect("/profile")

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    if "username" in session:
        add_log(session["username"], session["department"], "LOGOUT")

    session.clear()
    return redirect("/")


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    # ==========================
    # ADMIN DASHBOARD
    # ==========================

    if session["username"] == "admin":

        conn = get_db()
        cur = conn.cursor()
        today_uploads = cur.execute("""
        SELECT COUNT(*)
        FROM logs
        WHERE LOWER(activity) LIKE '%upload%'
        AND DATE(log_time)=DATE('now','localtime')
        """).fetchone()[0]


        today_downloads = cur.execute("""
        SELECT COUNT(*)
        FROM logs
        WHERE LOWER(activity) LIKE '%download%'
        AND DATE(log_time)=DATE('now','localtime')
                """).fetchone()[0]


        today_deletes = cur.execute("""
        SELECT COUNT(*)
        FROM logs
        WHERE LOWER(activity) LIKE '%delete%'
        AND DATE(log_time)=DATE('now','localtime')
        """).fetchone()[0]


        today_logins = cur.execute("""
        SELECT COUNT(*)
        FROM logs
        WHERE LOWER(activity) LIKE '%login%'
        AND DATE(log_time)=DATE('now','localtime')
        """).fetchone()[0]
        today_failed_logins = cur.execute("""
        SELECT COUNT(*)
        FROM alerts
        
        """).fetchone()[0]
        # Approved Users
        # Approved Users
        approved_count = conn.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE approved=1
        """).fetchone()[0]

        # Rejected Users
        rejected_count = conn.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE rejected=1
        """).fetchone()[0]
        pending_count = cur.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE approved=0
        AND rejected=0
        """).fetchone()[0]

        waiting_users = cur.execute("""
        SELECT *
        FROM users
        WHERE approved=0
        ORDER BY id DESC
        """).fetchall()

        total_users = cur.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE approved=1
        """).fetchone()[0]

        total_files = 0

        for root, dirs, files in os.walk(UPLOAD_FOLDER):
            total_files += len(files)

        user_counts = cur.execute("""
        SELECT department,
        COUNT(*) as user_count
        FROM users
        WHERE approved=1
        GROUP BY department
        """).fetchall()

        file_counts = {}

        if os.path.exists(UPLOAD_FOLDER):

            for dept in os.listdir(UPLOAD_FOLDER):

                dept_path = os.path.join(
                    UPLOAD_FOLDER,
                    dept
                )

                if os.path.isdir(dept_path):

                    file_counts[dept] = len(
                        os.listdir(dept_path)
                    )

        dept_stats = []

        for d in user_counts:

            dept_stats.append({

                "department": d["department"],
                "user_count": d["user_count"],
                "file_count": file_counts.get(
                    d["department"],
                    0
                )

            })

        
        login_count = cur.execute("""
        SELECT COUNT(*)
        FROM logs
        WHERE activity LIKE '%LOGIN%'
        """).fetchone()[0]

        upload_count = cur.execute("""
        SELECT COUNT(*)
        FROM logs
        WHERE activity LIKE '%UPLOAD%'
        """).fetchone()[0]

        download_count = cur.execute("""
        SELECT COUNT(*)
        FROM logs
        WHERE activity LIKE '%DOWNLOAD%'
        """).fetchone()[0]

        alert_count = cur.execute("""
        SELECT COUNT(*)
        FROM alerts
        """).fetchone()[0]

        recent_alerts = cur.execute("""
        SELECT *
        FROM alerts
        ORDER BY id DESC
        LIMIT 5
        """).fetchall()

        recent_logs = cur.execute("""
        SELECT *
        FROM logs
        ORDER BY id DESC
        LIMIT 5
        """).fetchall()

        conn.close()

        return render_template(

            "admin_dashboard.html",

            username=session["username"],

            
            total_users=total_users,

            total_admins=1,

            total_files=total_files,

            total_departments=len(dept_stats),

            dept_stats=dept_stats,

            login_count=login_count,

            upload_count=upload_count,
            pending_count=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
            today_uploads=today_uploads,
            today_downloads=today_downloads,
            today_deletes=today_deletes,
            today_logins=today_logins,
            today_failed_logins=today_failed_logins,
            waiting_users=waiting_users,
            download_count=download_count,

            alert_count=alert_count,
            security_alerts=security_alerts,
            recent_alerts=recent_alerts,

            recent_logs=recent_logs
        )

    # ==========================
    # USER DASHBOARD
    # ==========================

    conn = get_db()
    cur = conn.cursor()

    dept = session["department"]

    dept_user_count = cur.execute("""
    SELECT COUNT(*)
    FROM users
    WHERE department=?
    AND approved=1
    """, (dept,)).fetchone()[0]

    dept_path = os.path.join(
        UPLOAD_FOLDER,
        dept
    )

    if os.path.exists(dept_path):
        dept_file_count = len(
            os.listdir(dept_path)
        )
    else:
        dept_file_count = 0

    conn.close()

    return render_template(

        "user_dashboard.html",

        username=session["username"],

        department=dept,

        dept_user_count=dept_user_count,

        dept_file_count=dept_file_count
    )
@app.route("/pending_users")
def pending_users():

    if "username" not in session:
        return redirect("/login")

    if session["username"] != "admin":
        flash("Access Denied ❌")
        return redirect("/dashboard")

    search = request.args.get("search", "").strip()

    from_date = request.args.get("from_date", "").strip()

    to_date = request.args.get("to_date", "").strip()

    conn = get_db()
    cur = conn.cursor()

    query = """
    SELECT
        id,
        username,
        email,
        department,
        created_at,
        approved,
        rejected
    FROM users
    WHERE approved=0
    AND rejected=0
    """

    values = []

    # Search by Username / Email / Department

    if search:

        query += """
        AND (
            username LIKE ?
            OR email LIKE ?
            OR department LIKE ?
        )
        """

        values.extend([
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ])

    # From Date Filter

    if from_date:

        query += """
        AND date(created_at) >= date(?)
        """

        values.append(from_date)

    # To Date Filter

    if to_date:

        query += """
        AND date(created_at) <= date(?)
        """

        values.append(to_date)

    query += """
    ORDER BY department, id DESC
    """

    pending_users = cur.execute(
        query,
        values
    ).fetchall()

    conn.close()

    return render_template(
        "pending_users.html",
        pending_users=pending_users
    )
# ---------------- UPLOAD ---------------- #

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        file = request.files["file"]

        if file.filename == "":
            flash("No file selected")
            return redirect("/upload")

        dept = "COMMON" if session["username"] == "admin" else session["department"]

        folder = os.path.join(UPLOAD_FOLDER, dept)
        os.makedirs(folder, exist_ok=True)

        # ---------------- ENCRYPT FILE ---------------- #
        file_data = file.read()
        encrypted_data = fernet.encrypt(file_data)

        encrypted_filename = file.filename + ".enc"
        file_path = os.path.join(folder, encrypted_filename)

        with open(file_path, "wb") as f:
            f.write(encrypted_data)

        # ---------------- LOG ---------------- #
        add_log(
            session["username"],
            dept,
            f"UPLOAD (ENCRYPTED): {file.filename}"
        )

        flash("File Uploaded Successfully (Encrypted 🔐)")
        return redirect("/dashboard")

    return render_template(
        "upload.html",
        username=session["username"],
        email=session["email"],
        department=session["department"]
    )

# ---------------- FILES ---------------- #

@app.route("/files")
def files():

    if "username" not in session:
        return redirect("/login")

    search = request.args.get("search", "").strip().lower()

    if session["username"] == "admin":

        all_files = {}

        for dept in os.listdir(UPLOAD_FOLDER):

            path = os.path.join(UPLOAD_FOLDER, dept)

            if os.path.isdir(path):

                files = os.listdir(path)

                if search:
                    files = [f for f in files if search in f.lower()]

                all_files[dept] = files

        return render_template("files.html", all_files=all_files)

    dept = session["department"]

    dept_path = os.path.join(UPLOAD_FOLDER, dept)
    common_path = os.path.join(UPLOAD_FOLDER, "COMMON")

    dept_files = os.listdir(dept_path) if os.path.exists(dept_path) else []
    common_files = os.listdir(common_path) if os.path.exists(common_path) else []

    if search:
        dept_files = [f for f in dept_files if search in f.lower()]
        common_files = [f for f in common_files if search in f.lower()]

    return render_template(
        "files.html",
        files=dept_files,
        common_files=common_files,
        dept=dept
    )
@app.route("/download/<dept>/<filename>")
def download(dept, filename):

    if "username" not in session:
        return redirect("/login")

    username = session["username"]
    email = session["email"]
    user_department = session["department"]

    # ACCESS CONTROL

    if username == "admin":
        pass

    else:

        if dept.upper() == "COMMON":
            pass

        elif dept == user_department:
            pass

        else:
            flash("Access Denied ❌")
            return redirect("/files")

    # FILE PATH

    folder = os.path.join(UPLOAD_FOLDER, dept)
    file_path = os.path.join(folder, filename)

    if not os.path.exists(file_path):

        flash("File Not Found ❌")

        return redirect("/files")

    # BULK DOWNLOAD DETECTION

    now = datetime.now()

    if username not in download_history:
        download_history[username] = []

    download_history[username].append({
        "file": filename,
        "time": now
    })

    # last 2 minutes only

    download_history[username] = [

        x for x in download_history[username]

        if now - x["time"] <= timedelta(minutes=2)

    ]

    count = len(download_history[username])

    if count > 5:

        existing_alert = None

        for alert in security_alerts:

            if alert["name"] == username:

                existing_alert = alert
                break

        if existing_alert:

            existing_alert["count"] = count

            existing_alert["time"] = now.strftime(
                "%d-%m-%Y %H:%M:%S"
            )

        else:

            security_alerts.append({

                "icon": "🚨",

                "name": username,

                "email": email,

                "department": user_department,

                "dept_icon": dept_icons.get(
                    user_department,
                    "🏢"
                ),

                "count": count,

                "time": now.strftime(
                    "%d-%m-%Y %H:%M:%S"
                ),

                "message": "Bulk Download Detected"

            })

    # LOG EVERY DOWNLOAD

    add_log(
        username,
        dept,
        f"DOWNLOAD : {filename}"
    )

    # DECRYPT FILE

    if filename.endswith(".enc"):

        try:

            with open(file_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = fernet.decrypt(
                encrypted_data
            )

            response = app.response_class(
                decrypted_data,
                mimetype="application/octet-stream"
            )

            response.headers.set(
                "Content-Disposition",
                "attachment",
                filename=filename.replace(
                    ".enc",
                    ""
                )
            )

            return response

        except Exception as e:

            print("Decrypt Error :", e)

            flash("Decryption Failed ❌")

            return redirect("/files")

    return send_from_directory(
        folder,
        filename,
        as_attachment=True
    )

@app.route("/delete_file/<dept>/<filename>")
def delete_file(dept, filename):

    if "username" not in session:
        return redirect("/login")

    username = session["username"]

    # USER ACCESS CHECK
    if username != "admin":

        if dept != session["department"]:
            flash("Access Denied ❌")
            return redirect("/files")

    folder = os.path.join(
        UPLOAD_FOLDER,
        dept
    )

    file_path = os.path.join(
        folder,
        filename
    )

    if not os.path.exists(file_path):

        flash("File Not Found ❌")
        return redirect("/files")

    os.remove(file_path)

    add_log(
        username,
        dept,
        f"DELETE FILE : {filename}"
    )

    flash(
        f"{filename} Deleted Successfully ✅"
    )

    return redirect("/files")
# ---------------- LOGS ---------------- #

@app.route("/logs")
def logs():

    if "username" not in session:
        return redirect("/login")

    search = request.args.get("search", "").strip().lower()
    department = request.args.get("department", "").strip()
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()

    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT id, username, department, activity, log_time
        FROM logs
        WHERE 1=1
    """
    values = []

    if session["username"] != "admin":
        query += " AND department=?"
        values.append(session["department"])

    if session["username"] == "admin" and department:
        query += " AND department=?"
        values.append(department)

    if search:
        query += """
        AND (
            LOWER(username) LIKE ?
            OR LOWER(activity) LIKE ?
            OR LOWER(department) LIKE ?
        )
        """
        values += [f"%{search}%", f"%{search}%", f"%{search}%"]

    if from_date:
        query += " AND date(log_time) >= date(?)"
        values.append(from_date)

    if to_date:
        query += " AND date(log_time) <= date(?)"
        values.append(to_date)

    query += " ORDER BY id DESC"

    cur.execute(query, values)
    logs_data = cur.fetchall()
    conn.close()

    return render_template("logs.html", logs=logs_data)


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    init_db()
    app.run(debug=True)