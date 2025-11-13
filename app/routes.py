from flask import render_template, redirect, url_for, flash, request, current_app, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User, RoleEnum, FollowUp, Product, Quotation, Invoice, Client
from .forms import LoginForm, UserCreateForm, FollowUpForm, ProductForm, QuotationForm, InvoiceForm
from .utils import role_required
import json, io
import os


from flask import current_app as app
from datetime import datetime
from sqlalchemy import func, extract



@app.route("/home")
@login_required
def home():
    return render_template("home.html")
@app.route("/contact")
@login_required
def contact():
    return render_template("contact.html")



# AUTH & DASH


@app.route('/')
@login_required
def dashboard():
    # totals
    total_clients = Client.query.count()
    total_followups = FollowUp.query.count()
    total_quotations = Quotation.query.count()
    total_invoices = Invoice.query.count()

    # helper: zero-filled 12-month list
    months = list(range(1, 13))
    followup_counts = [0] * 12
    invoice_counts = [0] * 12

    # follow-ups: group by month (works with SQLite and most DBs)
    # extract month via strftime('%m', datetime)
    followup_rows = db.session.query(
        func.strftime('%m', FollowUp.followup_datetime).label('m'),
        func.count(FollowUp.id)
    ).group_by('m').all()

    for m, cnt in followup_rows:
        # m is '01'..'12' (string) in sqlite
        idx = int(m) - 1
        followup_counts[idx] = int(cnt)

    # invoices: group by created_at month
    invoice_rows = db.session.query(
        func.strftime('%m', Invoice.created_at).label('m'),
        func.count(Invoice.id)
    ).group_by('m').all()

    for m, cnt in invoice_rows:
        idx = int(m) - 1
        invoice_counts[idx] = int(cnt)

    # recent followups for display (limit 5)
    recent_followups = FollowUp.query.order_by(FollowUp.followup_datetime.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        total_clients=total_clients,
        total_followups=total_followups,
        total_quotations=total_quotations,
        total_invoices=total_invoices,
        followup_counts=followup_counts,
        invoice_counts=invoice_counts,
        recent_followups=recent_followups
    )

@app.route("/login", methods=["GET","POST"])
def auth_login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(username=form.username.data).first()
        if u and u.check_password(form.password.data):
            login_user(u)
            flash("Welcome back, " + u.username, "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth_login"))

# USERS
@app.route("/users", methods=["GET","POST"])
@login_required
@role_required("Admin")
def users():
    form = UserCreateForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists", "warning")
        else:
            u = User(username=form.username.data, role=form.role.data)
            u.set_password(form.password.data)
            db.session.add(u)
            db.session.commit()
            flash("User created", "success")
            return redirect(url_for("users"))
    all_users = User.query.order_by(User.username).all()
    return render_template("users.html", users=all_users, form=form)

# FOLLOW-UPS
@app.route("/followups", methods=["GET", "POST"])
@login_required
@role_required("Sales", "Manager")
def followups():
    form = FollowUpForm()

    if form.validate_on_submit():
        from datetime import datetime

        followup_datetime = datetime.combine(form.followup_date.data, form.followup_time.data)

        new_followup = FollowUp(
            client_name=form.client_name.data,
            client_phone=form.client_phone.data,
            followup_datetime=followup_datetime,
            note=form.note.data,
            status="pending",
            user_id=current_user.id
        )

        db.session.add(new_followup)
        db.session.commit()
        flash("Follow-up scheduled successfully!", "success")
        return redirect(url_for("followups"))

    all_followups = FollowUp.query.order_by(FollowUp.followup_datetime.desc()).all()
    return render_template("followups.html", form=form, followups=all_followups)


@app.route("/followups/complete/<int:id>")
@login_required
def complete_followup(id):
    fu = FollowUp.query.get_or_404(id)
    fu.status = "Completed"
    db.session.commit()
    flash("Follow-up marked completed", "success")
    return redirect(url_for("followups"))

# PRODUCTS
@app.route("/products", methods=["GET","POST"])
@login_required
def products():
    form = ProductForm()
    if form.validate_on_submit():
        p = Product(name=form.name.data, details=form.details.data, website_price=form.website_price.data)
        db.session.add(p)
        db.session.commit()
        flash("Product saved", "success")
        return redirect(url_for("products"))
    prods = Product.query.order_by(Product.name).all()
    return render_template("products.html", prods=prods, form=form)

# QUOTATIONS
@app.route("/quotations", methods=["GET","POST"])
@login_required
def quotations():
    form = QuotationForm()
    if form.validate_on_submit():
        q = Quotation(
            client_name=form.client_name.data,
            client_phone=form.client_phone.data,
            product_name=form.product_name.data,
            product_details=form.product_details.data,
            website_price=form.website_price.data
        )
        db.session.add(q)
        db.session.commit()
        flash("Quotation created", "success")
        return redirect(url_for("quotations"))
    quotes = Quotation.query.order_by(Quotation.created_at.desc()).all()
    return render_template("quotations.html", quotes=quotes, form=form)


@app.route("/quotations/share/<int:q_id>")
@login_required
def share_quotation(q_id):
    q = Quotation.query.get_or_404(q_id)
    # Build text message (encode newlines)
    msg_lines = [
        f"Hello {q.client_name},",
        "Here is your quotation:",
        f"Product: {q.product_name}",
        f"Details: {q.product_details or '—'}",
        f"Price: {q.website_price}"
    ]
    text = "%0A".join([line.replace('\n',' ') for line in msg_lines])
    phone = q.client_phone.strip()
    # Accept +91, +country or 10-digit local numbers
    if phone.startswith("+"):
        phone_sanitized = phone[1:].replace(" ", "")
    else:
        digits = "".join(ch for ch in phone if ch.isdigit())
        if len(digits) == 10:
            phone_sanitized = "91" + digits  # default country code, adjust if needed
        else:
            phone_sanitized = digits
    wa_link = f"https://wa.me/{phone_sanitized}?text={text}"
    return redirect(wa_link)

# INVOICES - professional dynamic flow
@app.route("/invoices", methods=["GET", "POST"])
@login_required
@role_required("Accountant", "Manager")
def invoices():
    form = InvoiceForm()
    if form.validate_on_submit():
        items = [
            {
                "name": form.item_name.data,
                "qty": form.item_qty.data,
                "price": form.item_price.data,
                "total": form.item_qty.data * form.item_price.data,
            }
        ]
        subtotal = sum(item["total"] for item in items)
        tax_amount = subtotal * (form.tax_percent.data / 100)
        grand_total = subtotal + tax_amount

        inv = Invoice(
            client_name=form.client_name.data,
            items=json.dumps(items),
            tax_percent=form.tax_percent.data,
            subtotal=subtotal,
            total=grand_total,
        )
        db.session.add(inv)
        db.session.commit()
        flash("Invoice created successfully!", "success")
        return redirect(url_for("invoices"))

    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template("invoice.html", form=form, invoices=invoices)


@app.route("/invoices/view/<int:id>")
@login_required
def invoice_view(id):
    inv = Invoice.query.get_or_404(id)
    items = json.loads(inv.items or "[]")
    return render_template("invoice_view.html", inv=inv, items=items)

@app.route("/invoices/pdf/<int:id>")
@login_required
def invoice_pdf(id):
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    import os, json

    invoice = Invoice.query.get_or_404(id)
    items = json.loads(invoice.items or "[]")

    # ---------------- Correct PDF path (NO double app/app) ----------------
    folder_path = os.path.join(os.getcwd(), "app", "static", "invoices")
    os.makedirs(folder_path, exist_ok=True)

    pdf_path = os.path.join(folder_path, f"invoice_{invoice.id}.pdf")
    # ---------------------------------------------------------------------

    # Register Unicode font (₹ symbol)
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

    # PDF Document setup
    doc = SimpleDocTemplate(
        pdf_path, 
        pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=30, bottomMargin=30
    )

    styles = getSampleStyleSheet()
    story = []

    # ---------------- Title ----------------
    story.append(Paragraph(
        f"<para align='center'><font size=22><b>INVOICE</b></font></para>",
        styles["Title"]
    ))

    story.append(Spacer(1, 10))

    # ---------------- Client + Date ----------------
    story.append(Paragraph(
        f"<para align='center'><font size=12>Date: {invoice.created_at.strftime('%Y-%m-%d')}</font></para>",
        styles["Normal"]
    ))
    story.append(Paragraph(
        f"<para align='center'><font size=12>Client: <b>{invoice.client_name}</b></font></para>",
        styles["Normal"]
    ))

    story.append(Spacer(1, 20))

    # ---------------- Table Data ----------------
    data = [["#", "Item", "Qty", "Price", "Total"]]

    subtotal = 0
    for idx, item in enumerate(items, start=1):
        total = item["qty"] * item["price"]
        subtotal += total
        data.append([
            idx,
            item["name"],
            item["qty"],
            f"₹{item['price']:.2f}",
            f"₹{total:.2f}"
        ])

    tax_amount = subtotal * (invoice.tax_percent / 100)
    grand_total = subtotal + tax_amount

    # ---------------- Summary rows ----------------
    data.append(["", "", "", "Subtotal", f"₹{subtotal:.2f}"])
    data.append(["", "", "", f"Tax ({invoice.tax_percent}%)", f"₹{tax_amount:.2f}"])
    data.append(["", "", "", "<b>Grand Total</b>", f"<b>₹{grand_total:.2f}</b>"])

    # ---------------- Table Style ----------------
    table = Table(data, colWidths=[35, 220, 55, 90, 90])
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1976D2")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Body font
        ('FONTNAME', (0, 0), (-1, -1), 'HeiseiMin-W3'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.7, colors.grey),

        # Alignments
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (4, -1), 'CENTER'),

        # Highlight totals
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor("#E3F2FD")),
    ]))

    story.append(table)
    story.append(Spacer(1, 25))

    # ---------------- Footer ----------------
    story.append(Paragraph(
        "<para align='center'><font size=11>Thank you for doing business with us!</font></para>",
        styles["Normal"]
    ))

    doc.build(story)

    return send_file(pdf_path, as_attachment=True)






# REPORTS with chart data
@app.route("/reports")
@login_required
@role_required("Admin", "Manager")
def reports():
    # --- Follow-up stats ---
    total_followups = FollowUp.query.count()
    pending = FollowUp.query.filter_by(status="pending").count()
    completed = FollowUp.query.filter_by(status="completed").count()

    # --- Compute total sales dynamically from invoice.items ---
    invoices = Invoice.query.all()
    total_sales = 0
    monthly_sales = {}

    for inv in invoices:
        try:
            items = json.loads(inv.items or "[]")
        except Exception:
            items = []
        subtotal = sum(i.get("qty", 0) * i.get("price", 0) for i in items)
        total = subtotal + subtotal * (inv.tax_percent / 100.0)
        total_sales += total

        # Aggregate monthly totals using created_at
        if inv.created_at:
            month = inv.created_at.month
            monthly_sales[month] = monthly_sales.get(month, 0) + total

    # --- Prepare data for charts ---
    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    months = []
    sales_values = []

    for m in range(1, 13):
        months.append(month_names[m - 1])
        sales_values.append(monthly_sales.get(m, 0))

    # --- Prepare follow-up status chart data ---
    followup_status_labels = ["Pending", "Completed"]
    followup_status_data = [pending, completed]

    # --- Render template ---
    return render_template(
        "reports.html",
        total_followups=total_followups,
        pending=pending,
        completed=completed,
        total_sales=total_sales,
        months=months,
        sales_values=sales_values,
        followup_labels=followup_status_labels,
        followup_data=followup_status_data

    )
