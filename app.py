import os
import sqlite3
from flask import Flask, render_template, request, redirect
import qrcode
from io import BytesIO
from flask_mail import Mail, Message
import uuid
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter

app = Flask(__name__)

# Global variables to temporarily store form data
gmaill = ""
gtdi = ""
gmob = ""
gnm = ""
gpfo = ""
ggen = ""
gadd = ""

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'veerasnail@gmail.com'
app.config['MAIL_PASSWORD'] = 'hscw wcwt qsbt sjus'  # App password
app.config['MAIL_DEFAULT_SENDER'] = 'shreeshpitambare084@gmail.com'
mail = Mail(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def filling():
    return render_template("register.html")

@app.route('/payment', methods=['POST'])
def pay():
    global gmob, gmaill, gtdi, gnm, gadd, ggen, gpfo

    name = request.form['name']
    gnm = name
    gmaill = request.form['email']
    email = gmaill
    gmob = request.form['mobile']
    mobile = gmob
    gpfo = request.form['profession']
    ggen = request.form['gender']
    gadd = request.form['address']
    
    transaction_id = str(uuid.uuid4())
    gtdi = transaction_id

    amount = 1
    order_id = "Order" + str(uuid.uuid4())

    headers = {
        "x-client-id": "896457b3bd65c4bc202da34a48754698",
        "x-client-secret": "cfsk_ma_prod_58a4944f0018534a39d68c2e96a5337e_ca091af8",
        "x-api-version": "2022-01-01",
        "Content-Type": "application/json"
    }

    data = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": mobile,
            "customer_name": name,
            "customer_email": email,
            "customer_phone": mobile
        },
        "order_meta": {
            "return_url": f"https://artist-studio-final-production.up.railway.app/success?order_id={order_id}"
        }
    }

    res = requests.post("https://api.cashfree.com/pg/orders", json=data, headers=headers)
    res_data = res.json()

    if 'payment_link' in res_data:
        return redirect(res_data['payment_link'])
    else:
        return f"Error: {res_data}"

@app.route('/success', methods=['POST', 'GET'])
def sucs():
    ois = request.args.get('order_id')

    name = gnm
    email = gmaill
    mobile = gmob
    transaction_id = gtdi
    profession = gpfo
    gender = ggen
    address = gadd

    hs = {
        "x-client-id": "896457b3bd65c4bc202da34a48754698",
        "x-client-secret": "cfsk_ma_prod_58a4944f0018534a39d68c2e96a5337e_ca091af8",
        "x-api-version": "2022-01-01",
    }

    resf = requests.get(f"https://api.cashfree.com/pg/orders/{ois}", headers=hs)
    order_info = resf.json()

    if order_info.get('order_status') == 'PAID':
        # Generate QR Code
        qr_data = f"{name}|{email}|{mobile}"
        qr_img = qrcode.make(qr_data)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        # Send QR Email
        msg = Message('Payment Confirmation - Your QR Code', recipients=[email])
        msg.body = f"""Dear {name},

Thank you for registering for our event.
Transaction ID: {transaction_id}
Please find your unique QR code below. Show this at the entry gate🚨.
Status: {order_info.get('order_status')}

Regards,    
Event Team VEERA's NAIIL 💅
https://www.instagram.com/veeras_naiil_?igsh=MXIzMTJtZTB4c3V0NQ==
"""
        msg.attach("qr.png", "image/png", qr_buffer.getvalue())
        mail.send(msg)

        # Generate entry pass from base Ticket.pdf
        base_pdf_path = "/static/Ticket.pdf"
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)

        # Positions — adjust for your ticket template
        can.setFont("Helvetica-Bold", 12)
        can.drawString(150, 500, name)
        can.drawString(150, 480, email)
        can.drawString(150, 460, transaction_id)

        # Place QR code
        can.drawImage(ImageReader(qr_buffer), x=200, y=300, width=150, height=150)

        can.save()
        packet.seek(0)

        existing_pdf = PdfReader(open(base_pdf_path, "rb"))
        overlay_pdf = PdfReader(packet)
        output = PdfWriter()

        page = existing_pdf.pages[0]
        page.merge_page(overlay_pdf.pages[0])
        output.add_page(page)

        pdf_buffer = BytesIO()
        output.write(pdf_buffer)
        pdf_buffer.seek(0)

        # Send ticket PDF
        msg = Message('Payment Confirmation - Your QR Pass', recipients=[email])
        msg.body = f"""Dear {name},

Thank you for registering for our event.

We've attached your unique QR code pass with shop details.
Please show this pass at the entry.

Regards,    
VEERA's NAIIL 💅
Instagram: https://www.instagram.com/veeras_naiil_?igsh=MXIzMTJtZTB4c3V0NQ==
"""
        msg.attach("entry_pass.pdf", "application/pdf", pdf_buffer.getvalue())
        mail.send(msg)

        # Send admin notification
        admin_msg = Message('New Customer Registered', recipients=['shreeshpitambare777@gmail.com'])
        admin_msg.body = f"""New Customer Registered:
Name: {name}
Email: {email}
Transaction ID: {transaction_id}
Mobile: {mobile}
Profession: {profession}
Address: {address}
Gender: {gender}
Status: {order_info.get('order_status')}
"""
        mail.send(admin_msg)

        # Save to DB
        conn = sqlite3.connect('customers.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS customers
                        (name TEXT, email TEXT, mobile TEXT, profession TEXT, gender TEXT,
                         address TEXT, transaction_id TEXT)''')
        c.execute('INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (name, email, mobile, profession, gender, address, transaction_id))
        conn.commit()
        conn.close()

        return render_template("success.html")
    else:
        return render_template("failure.html")

@app.route('/failure', methods=['GET'])
def fail():
    return render_template("failure.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
