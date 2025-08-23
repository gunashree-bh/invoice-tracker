from flask import Flask, render_template, request, jsonify
from datetime import date, datetime
import mysql.connector

app = Flask(__name__)

# ----------------- Database Connection -----------------
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Gagu@1529",
        database="invoice_db"
    )
    return conn

# ----------------- Aging Bucket -----------------
def compute_aging_bucket(due_date, today):
    delta = (today - due_date).days
    if delta < 0:
        return "Not Due"
    elif delta <= 30:
        return "0-30"
    elif delta <= 60:
        return "31-60"
    elif delta <= 90:
        return "61-90"
    else:
        return "90+"

# ----------------- Routes -----------------

@app.route("/")
def home():
    return "Invoice Tracker API is running! Go to /dashboard to see the dashboard."

@app.route("/dashboard")
def dashboard():
    today_date = date.today()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Fetch customers
    cursor.execute("SELECT customer_id, name FROM customers")
    customers = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("index.html", customers=customers, today=today_date)

# ----------------- Invoices API -----------------
@app.route("/invoices")
def get_invoices():
    today_date = date.today()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("""
        SELECT i.invoice_id, i.customer_id, c.name AS customer_name,
               i.invoice_date, i.due_date, i.amount AS invoice_amount
        FROM invoices i
        JOIN customers c ON i.customer_id = c.customer_id
    """)
    invoices = cursor.fetchall()

    # Fetch payments per invoice
    for invoice in invoices:
        cursor.execute("SELECT SUM(amount) AS total_paid FROM payments WHERE invoice_id=%s", (invoice['invoice_id'],))
        res = cursor.fetchone()
        total_paid = res['total_paid'] if res['total_paid'] else 0
        invoice['total_paid'] = float(total_paid)
        invoice['outstanding'] = float(invoice['invoice_amount']) - invoice['total_paid']
        invoice['aging_bucket'] = compute_aging_bucket(invoice['due_date'], today_date)

    cursor.close()
    conn.close()
    return jsonify(invoices)

# ----------------- Payments API -----------------
@app.route("/payments", methods=["POST"])
def add_payment():
    data = request.get_json()
    invoice_id = data['invoice_id']
    amount = data['amount']
    payment_date = data['payment_date']

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)
    cursor.execute(
        "INSERT INTO payments (invoice_id, amount, payment_date) VALUES (%s, %s, %s)",
        (invoice_id, amount, payment_date)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Payment added successfully!"})

# ----------------- KPIs API -----------------
@app.route("/kpis")
def kpis():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("SELECT SUM(amount) AS total_invoiced FROM invoices")
    total_invoiced = cursor.fetchone()['total_invoiced'] or 0

    cursor.execute("SELECT SUM(amount) AS total_received FROM payments")
    total_received = cursor.fetchone()['total_received'] or 0

    total_outstanding = total_invoiced - total_received

    cursor.execute("SELECT due_date, SUM(amount - IFNULL((SELECT SUM(p.amount) FROM payments p WHERE p.invoice_id=i.invoice_id),0)) AS outstanding \
                    FROM invoices i GROUP BY i.invoice_id")
    overdue_rows = cursor.fetchall()
    overdue_count = sum(1 for row in overdue_rows if row['outstanding'] > 0 and row['due_date'] < date.today())
    percent_overdue = round((overdue_count / len(overdue_rows) * 100), 2) if overdue_rows else 0

    cursor.close()
    conn.close()

    return jsonify({
        "total_invoiced": float(total_invoiced),
        "total_received": float(total_received),
        "total_outstanding": float(total_outstanding),
        "percent_overdue": percent_overdue
    })

# ----------------- Top Customers API -----------------
@app.route("/top-customers")
def top_customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("""
        SELECT c.customer_id, c.name AS customer_name, 
               SUM(i.amount - IFNULL((SELECT SUM(p.amount) FROM payments p WHERE p.invoice_id=i.invoice_id),0)) AS outstanding
        FROM customers c
        JOIN invoices i ON c.customer_id = i.customer_id
        GROUP BY c.customer_id
        ORDER BY outstanding DESC
        LIMIT 5
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    # Ensure numeric conversion
    for r in result:
        r['outstanding'] = float(r['outstanding']) if r['outstanding'] else 0
    return jsonify(result)

# ----------------- Run App -----------------
if __name__ == "__main__":
    app.run(debug=True)
