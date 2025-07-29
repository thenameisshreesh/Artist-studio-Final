import os
import sqlite3
from flask import Flask,render_template,redirect
from flask import Flask, render_template, request, redirect, url_for
import qrcode
from io import BytesIO
import base64
from flask_mail import Mail, Message
import uuid

import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader



app = Flask(__name__)

gmaill=""
gtdi=""
gmob=""
gnm=""
gpfo=""
ggen=""
gadd=""

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'shreeshpitambare084@gmail.com'
app.config['MAIL_PASSWORD'] = 'untk duvx aisq ssuq'  # ✅ App password, not your Gmail password
app.config['MAIL_DEFAULT_SENDER'] = 'shreeshpitambare084@gmail.com'
mail = Mail(app)
#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------- 

@app.route("/")
def index():
    return render_template("index.html")


#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------- 


@app.route("/register")
def filling():
    return render_template("register.html")



#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------- 


@app.route('/payment', methods=['POST'])
def pay():
    # Get form data (assume it's sent via POST)

    global gmob
    global gmaill
    global gtdi
    global gnm
    global gadd
    global ggen
    global gpfo

    name = request.form['name']
    gnm= request.form['name']

    gmaill=request.form['email']
    email=request.form['email']

    gmob = request.form['mobile']
    mobile = request.form['mobile']

    profession = request.form['profession']
    gpfo = request.form['profession']

    gender = request.form['gender']
    ggen = request.form['gender']

    address = request.form['address']
    gadd = request.form['address']
    
    transaction_id = str(uuid.uuid4())
    gtdi = transaction_id

    amount=1
    order_id = "Order" + str(uuid.uuid4())


    headers = {
    "x-client-id": "896457b3bd65c4bc202da34a48754698",
    "x-client-secret": "cfsk_ma_prod_58a4944f0018534a39d68c2e96a5337e_ca091af8",
    "x-api-version": "2022-01-01",  # or latest version per Cashfree docs
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

#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------- 
@app.route('/success', methods=['POST','GET'])
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
        # ✅ Generate QR Code
        qr_data = f"{name}|{email}|{mobile}"
        qr_img = qrcode.make(qr_data)
        buffered = BytesIO()
        qr_img.save(buffered, format="PNG")

        # ✅ Send Email to User
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
        msg.attach("qr.png", "image/png", buffered.getvalue())
        try:
            mail.send(msg)
        except Exception as e:
            return f"Error sending mail: {e}", 500

        # ✅ Mail 2 Generate PDF
        pdf_buffer = BytesIO()
        pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4

        # Company Logo (assume 'logo.png' is in static folder)
        logo_path = os.path.join("static", "/static/logopink.jpg")
        if os.path.exists(logo_path):
            pdf.drawImage(ImageReader(logo_path), x=50, y=height - 150, width=120, height=60)

        # Shop Info
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, height - 180, "VEERA'S NAIIL STUDIO")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, height - 200, "Near Gokul Hall, Sadar, Nagpur, Maharashtra")
        pdf.drawString(50, height - 215, "Contact: +91-9860585858")
        pdf.drawString(50, height - 230, f"Participant: {name}")
        pdf.drawString(50, height - 245, f"Transaction ID: {transaction_id}")
        pdf.drawString(50, height - 260, f"Status: {order_info.get('order_status')}")

        # QR Code
        qr_path = os.path.join("static", f"qr_{transaction_id}.png")
        with open(qr_path, "wb") as f:
            f.write(buffered.getvalue())

        pdf.drawImage(ImageReader(qr_path), x=50, y=height - 460, width=150, height=150)

        pdf.showPage()
        pdf.save()

        pdf_buffer.seek(0)

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

        # ✅ Send Email to Admin
        admin_msg = Message('New Customer Registered', recipients=['shreeshpitambare777@gmail.com'])
        admin_msg.body = f"""New Customer Registered:
        Name: {name}
        Email: {email}
        Transaction ID: {transaction_id}
        Mobile: {mobile}
        Profession: {profession}
        Address: {address}
        gender:{gender}
        Status: {order_info.get('order_status')}
        """
        try:
            mail.send(admin_msg)
        except Exception as e:
            return f"Error sending admin mail: {e}", 500

        
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

#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------- 


@app.route('/failure', methods=['GET'])
def fail():
    return render_template("failure.html")




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)