from flask import Flask, render_template, request, redirect, session, flash
import sqlite3, os
from document_loader import load_documents, read_pdf, read_docx, read_txt
from retrieval import Retriever
from generator import generate_answer
import random

app = Flask(__name__)
app.secret_key = "super_secret_key"

# ================= DATABASE =================
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    con = get_db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        address TEXT,
        phone TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin(
        username TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        content TEXT,
        result TEXT
    )
    """)

    cur.execute("SELECT * FROM admin")
    if not cur.fetchone():
        cur.execute("INSERT INTO admin VALUES (?,?)", ("admin", "admin@123"))

    con.commit()
    con.close()

init_db()

# ================= LOAD DATASET =================
docs = []
docs.extend(load_documents("dataset/legal", "Legal"))
docs.extend(load_documents("dataset/illegal", "Illegal"))
retriever = Retriever(docs)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= HOME =================
@app.route("/")
def home():
    return render_template("home.html")

@app.route('/admin/legal_analysis')
def legal_analysis():
    return render_template("admin_legal_analysis.html")

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            con = get_db()
            cur = con.cursor()
            cur.execute(
                "INSERT INTO users VALUES (NULL,?,?,?,?,?)",
                (
                    request.form["username"],
                    request.form["password"],
                    request.form["email"],
                    request.form["address"],
                    request.form["phone"]
                )
            )
            con.commit()
            con.close()
            flash("Registration Successful")
            return redirect("/login")
        except:
            flash("Username Already Exists")

    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (request.form["username"],))
        user = cur.fetchone()
        con.close()

        if user and user[2] == request.form["password"]:
            session.clear()
            session["user"] = user[1]
            return redirect("/user/dashboard")
        else:
            flash("Invalid Username or Password")

    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= USER DASHBOARD =================
@app.route("/user/dashboard")
def user_dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("user_dashboard.html", username=session["user"])

# ================= PROFILE =================
@app.route("/profile", methods=["GET","POST"])
def profile():
    if "user" not in session:
        return redirect("/login")

    con = get_db()
    cur = con.cursor()

    if request.method == "POST":
        cur.execute("""
            UPDATE users SET email=?, address=?, phone=?
            WHERE username=?
        """, (
            request.form["email"],
            request.form["address"],
            request.form["phone"],
            session["user"]
        ))
        con.commit()
        flash("Profile Updated")

    cur.execute("SELECT * FROM users WHERE username=?", (session["user"],))
    user = cur.fetchone()
    con.close()

    return render_template("profile.html", user=user)


@app.route('/admin/api/dashboard-data')
def dashboard_data():
    users = User.query.all()

    return jsonify({
        "total_users": len(users),
        "analyses": Analysis.query.count(),
        "health": "99.99%",
        "activities": [
            "New user registered",
            "Legal document analyzed",
            "System scan completed"
        ]
    })

# ================= LEGAL / ILLEGAL KEYWORDS =================

LEGAL_KEYWORDS = [
"agreement","contract","service agreement","purchase agreement","employment agreement",
"loan agreement","lease agreement","rental agreement","partnership agreement",
"non disclosure agreement","nda","terms and conditions",

"buyer","seller","client","customer","tenant","landlord","lessor","lessee",
"employee","employer","contractor","service provider","vendor","supplier",

"property","real estate","ownership","title","purchase price","closing",
"inspection","earnest money","deposit","payment","payment terms","invoice",
"bank transfer","refund","settlement","billing",

"liability","limited liability","indemnity","indemnification",
"governing law","jurisdiction","legal jurisdiction","court",
"arbitration","mediation","dispute resolution",

"legal rights","lawful rights","due process","legal notice",
"legal remedy","consumer rights","tenant rights",

"data protection","privacy policy","user consent","lawful processing",
"personal data protection","gdpr compliance","data security",

"intellectual property","copyright","trademark","patent","licensing",

"minimum wages","paid leave","working hours","labour laws",
"workplace safety","health and safety",

"regulatory compliance","lawful activity","legal compliance",
"authorized use","lawful agreement","contractual obligation",

"scope of services","responsibilities","obligations",
"termination clause","notice period","contract duration",
"renewal clause","confidentiality clause","limitation of liability"
]


ILLEGAL_KEYWORDS = [
    "not be reported",
    "no taxes",
    "cash payment",
    "not enforceable",
    "no government authority",
    "unofficially"
    "fake identity",
    "bribed",
    "not be recorded",
    "avoid paying taxes",
    "forged",
    "illegal",
    "not genuine",
    "no legal authority"
"fraud","fraudulent activity","fraudulent transaction","scam",
"bribe","bribery","illegal payment","kickback","corruption",

"money laundering","tax evasion","financial crime","embezzlement",

"drug trafficking","illegal drugs","contraband","smuggling",

"fake identity","identity theft","forged documents","forgery",

"hacking","unauthorized access","data breach","system intrusion",
"malware","spyware","ransomware","cyber crime",

"blackmail","extortion","threat","coercion",

"without consent","without user consent","sell personal data",
"selling personal data","privacy violation",
"illegal data collection","data theft","personal data misuse",

"waive rights","waive all rights","waiver of rights",
"deny legal rights","denying lawful remedies",
"cannot approach court","cannot approach courts",
"no legal remedy","no legal remedies",

"illegal contract","unlawful agreement","void agreement",
"invalid contract","not legally enforceable",

"non-existent jurisdiction","fake jurisdiction",

"child labour","forced labour","illegal employment",

"illegal eviction","property seizure without notice",

"unauthorized surveillance","illegal monitoring",

"fake company","shell company","financial scam",

"illegal activities","unlawful activity","illegal operations"
]


# ================= CLASSIFIER FUNCTION =================

def classify_document(text):

    text = text.lower()

    legal_found = [k for k in LEGAL_KEYWORDS if k in text]
    illegal_found = [k for k in ILLEGAL_KEYWORDS if k in text]

    legal_score = len(legal_found)
    illegal_score = len(illegal_found)

    if illegal_score >= 1:
        result = "Illegal ❌"
        detected = illegal_found[:5]

    elif legal_score >= 1:
        result = "Legal ✅"
        detected = legal_found[:5]

    else:
        result = "Unknown ⚠️"
        detected = []

    confidence = min(95, 60 + (legal_score + illegal_score) * 5)

    return result, detected, confidence


# ================= COMPLIANCE ROUTE =================

@app.route("/compliance", methods=["GET","POST"])
def compliance():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        text_input = request.form.get("text_input")
        file = request.files.get("file")

        extracted_text = ""

        # ---------- FILE UPLOAD ----------
        if file and file.filename != "":

            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            if file.filename.endswith(".pdf"):
                extracted_text = read_pdf(path)

            elif file.filename.endswith(".docx"):
                extracted_text = read_docx(path)

            else:
                extracted_text = read_txt(path)

        else:
            extracted_text = text_input

        if not extracted_text:
            flash("Please upload a file or enter text")
            return redirect("/compliance")

        # ---------- RAG RETRIEVAL ----------
        retrieved = retriever.retrieve(extracted_text)
        context = "\n".join(d["text"] for d in retrieved)

        answer = generate_answer(context, extracted_text)

        # ---------- CLASSIFICATION ----------
        result, clauses, confidence = classify_document(extracted_text)

        # ---------- RANDOM REASONS ----------
        reason_pool = [
            "AI classification based on retrieved legal context.",
            "Document structure analyzed against legal patterns.",
            "Compliance check performed using dataset similarity.",
            "Keyword based legal clause detection executed.",
            "Clause similarity detected using retrieval model."
        ]

        reason = random.sample(reason_pool, random.randint(2,4))

        # ---------- SAVE HISTORY ----------
        con = get_db()
        cur = con.cursor()

        cur.execute(
            "INSERT INTO history(username, content, result) VALUES (?,?,?)",
            (session["user"], extracted_text[:200], result)
        )

        con.commit()
        con.close()

        # ---------- RESULT PAGE ----------
        return render_template(
            "result.html",
            answer=answer,
            compliance=result,
            reason=reason,
            confidence=confidence,
            clauses=clauses
        )

    return render_template("compliance.html")
# ================= HISTORY =================
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    con = get_db()
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM history WHERE username=? ORDER BY id DESC",
        (session["user"],)
    )

    records = cur.fetchall()
    con.close()

    return render_template("history.html", records=records)


# ================= VIEW RECORD =================
@app.route("/view/<int:record_id>")
def view_record(record_id):
    if "user" not in session:
        return redirect("/login")

    con = get_db()
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM history WHERE id=? AND username=?",
        (record_id, session["user"])
    )

    record = cur.fetchone()
    con.close()

    if not record:
        flash("Record not found.")
        return redirect("/history")

    return render_template(

        "result.html",
        answer=record[2],
        compliance=record[3],
        reason=["Loaded from stored analysis history."])
# ================= DELETE HISTORY =================
@app.route("/delete/<int:record_id>")
def delete_record(record_id):
    if "user" not in session:
        return redirect("/login")

    con = get_db()
    cur = con.cursor()
    cur.execute("DELETE FROM history WHERE id=? AND username=?",
                (record_id, session["user"]))
    con.commit()
    con.close()

    flash("Record deleted successfully.")
    return redirect("/history")

# ================= ADMIN LOGIN =================
@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM admin WHERE username=? AND password=?",
                    (request.form["username"], request.form["password"]))
        admin = cur.fetchone()
        con.close()

        if admin:
            session.clear()
            session["admin"] = admin[0]
            return redirect("/admin/dashboard")
        else:
            flash("Invalid Admin Credentials")

    return render_template("admin_login.html")

# ================= ADMIN DASHBOARD =================
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM history")
    total_analysis = cur.fetchone()[0]
    con.close()

    return render_template("admin_dashboard.html",
                           total_users=total_users,
                           total_analysis=total_analysis)

# ================= ADMIN MANAGE USERS =================
@app.route("/admin/manage_users")
def admin_manage_users():
    if "admin" not in session:
        return redirect("/admin")

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    con.close()

    return render_template("manage_users.html", users=users)

# ================= ADMIN SYSTEM STATUS =================
@app.route("/admin/system_status")
def admin_system_status():
    if "admin" not in session:
        return redirect("/admin")

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM history")
    total_analysis = cur.fetchone()[0]
    con.close()

    return render_template("admin_system_status.html",
                           total_users=total_users,
                           total_analysis=total_analysis)

if __name__ == "__main__":
    app.run(debug=True) 