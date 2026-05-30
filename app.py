from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
import sqlite3
import json
import os
import re
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

app = Flask(__name__)
app.secret_key = "shivya_secret_key_2024"
app.config["WTF_CSRF_TIME_LIMIT"] = None
csrf = CSRFProtect(app)
@app.errorhandler(500)
def internal_error(e):
    import traceback
    return "<pre style='padding:20px;background:#111;color:#f87171;font-size:13px;'>" + traceback.format_exc() + "</pre>", 500


limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

# -----------------------------------------------
# EMAIL CONFIG — change these to your Gmail details
# -----------------------------------------------
app.config["MAIL_SERVER"]   = "smtp.hostinger.com"
app.config["MAIL_PORT"]     = 465
app.config["MAIL_USE_TLS"]  = False
app.config["MAIL_USE_SSL"]  = True
app.config["MAIL_USERNAME"] = "hello@shivyaspaces.com"
app.config["MAIL_PASSWORD"] = "Shivya@768"
app.config["MAIL_DEFAULT_SENDER"] = ("ShivyaSpaces", "hello@shivyaspaces.com")

# -----------------------------------------------
# SITE URL — change this after hosting
# -----------------------------------------------
SITE_URL = os.environ.get("SITE_URL", "https://www.shivyaspaces.com")
mail = Mail(app)

# ── Cloudinary config (optional - set env vars to enable) ──
if CLOUDINARY_AVAILABLE:
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(
        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
        api_key    = os.environ.get("CLOUDINARY_API_KEY", ""),
        api_secret = os.environ.get("CLOUDINARY_API_SECRET", ""),
        secure     = True
    )

# ── Upload folder for local image storage (fallback) ──
# Use /tmp for Railway (persistent static dir may not be writable)
_static_uploads = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
_tmp_uploads = "/tmp/shivyaspaces_uploads"
try:
    os.makedirs(_static_uploads, exist_ok=True)
    # Test write
    _test = os.path.join(_static_uploads, ".test")
    open(_test, "w").close()
    os.remove(_test)
    UPLOAD_FOLDER = _static_uploads
    UPLOAD_URL_BASE = "/static/uploads"
except Exception:
    os.makedirs(_tmp_uploads, exist_ok=True)
    UPLOAD_FOLDER = _tmp_uploads
    UPLOAD_URL_BASE = "/tmp-uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "bmp", "tiff", "tif", "heic", "heif", "avif", "svg"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


# -----------------------------------------------
# HELPERS
# -----------------------------------------------

def get_db():
    conn = sqlite3.connect("properties.db", timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_setting(key, default=""):
    """Read a setting from the database."""
    try:
        conn = sqlite3.connect("properties.db", timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("""CREATE TABLE IF NOT EXISTS settings
            (key TEXT PRIMARY KEY, value TEXT)""")
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
        return row["value"] if row else default
    except Exception:
        return default


def save_setting(key, value):
    """Save a setting to the database."""
    try:
        conn = sqlite3.connect("properties.db", timeout=10)
        conn.execute("""CREATE TABLE IF NOT EXISTS settings
            (key TEXT PRIMARY KEY, value TEXT)""")
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_mail_config():
    """Get current mail config from DB, fallback to hardcoded defaults."""
    return {
        "username": get_setting("mail_username", app.config["MAIL_USERNAME"]),
        "password": get_setting("mail_password", app.config["MAIL_PASSWORD"]),
        "sender_name": get_setting("mail_sender_name", "ShivyaSpaces"),
    }


def send_welcome_email(owner_name, owner_email, username, password, slug):
    """Send welcome email using mail config from database."""
    try:
        cfg = get_mail_config()
        # Update mail config live from DB
        app.config["MAIL_USERNAME"]       = cfg["username"]
        app.config["MAIL_PASSWORD"]       = cfg["password"]
        app.config["MAIL_DEFAULT_SENDER"] = (cfg["sender_name"], cfg["username"])
        mail.init_app(app)

        msg = Message(
            subject="Your ShivyaSpaces Account is Ready",
            recipients=[owner_email]
        )
        msg.html = f"""
        <div style="font-family:Inter,Arial,sans-serif;max-width:520px;margin:0 auto;padding:32px 24px;color:#111827;">
            <h2 style="font-size:22px;font-weight:800;margin-bottom:4px;">Welcome to ShivyaSpaces</h2>
            <p style="color:#6b7280;font-size:14px;margin-bottom:28px;">Your account has been created. Here are your login credentials.</p>
            <div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin-bottom:24px;">
                <p style="font-size:12px;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:16px;">Your Credentials</p>
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td style="font-size:13px;color:#6b7280;padding:8px 0;width:40%;">Login URL</td><td style="font-size:13px;font-weight:600;color:#111827;">/login</td></tr>
                    <tr><td style="font-size:13px;color:#6b7280;padding:8px 0;">Email</td><td style="font-size:13px;font-weight:600;color:#111827;">{owner_email}</td></tr>
                    <tr><td style="font-size:13px;color:#6b7280;padding:8px 0;">Password</td><td style="font-size:13px;font-weight:600;color:#111827;">{password}</td></tr>
                    <tr><td style="font-size:13px;color:#6b7280;padding:8px 0;">Your Page</td><td style="font-size:13px;font-weight:600;color:#111827;">/{slug}</td></tr>
                </table>
            </div>
            <p style="font-size:13px;color:#6b7280;line-height:1.7;">Log in to your dashboard to start adding your properties. Your public page will be live as soon as you add your first listing.</p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;" />
            <p style="font-size:12px;color:#9ca3af;">This email was sent by {cfg["sender_name"]}. Please keep your credentials safe.</p>
        </div>
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


def parse_property(row):
    if row is None:
        return None
    p = dict(row)
    p["amenities"]      = json.loads(p["amenities"])      if p.get("amenities")      else []
    p["gallery_images"] = json.loads(p["gallery_images"]) if p.get("gallery_images") else []
    # Safe defaults for optional fields
    for field in ["title","location","rent","status","description","property_type",
                  "facing","maintenance","floor","built","security_deposit","image"]:
        if field not in p or p[field] is None:
            p[field] = ""
    for field in ["beds","baths","sqft","is_complex","parent_id"]:
        if field not in p or p[field] is None:
            p[field] = 0
    return p


def clean_phone(phone):
    """
    Returns digits only for wa.me links e.g. 919876543210
    Strips +, spaces, dashes — everything except digits.
    """
    if not phone:
        return ""
    phone = phone.strip()
    # Strip everything except digits
    digits = re.sub(r"[^\d]", "", phone)
    # Handle 00-prefix international numbers
    if digits.startswith("00"):
        digits = digits[2:]
    # Bare 10 digits = assume India
    if len(digits) == 10:
        digits = "91" + digits
    return digits


def format_phone_display(phone):
    """
    Returns phone for display with + prefix e.g. +91 98765 43210
    """
    if not phone:
        return ""
    digits = clean_phone(phone)
    if digits:
        return "+" + digits
    return phone


def validate_phone(phone):
    """
    Accepts international formats:
    - With country code: +91 98765 43210, +1 415 555 0132 etc.
    - Without country code: 9876543210 (assumed India)
    - Must have at least 10 digits after stripping formatting
    - Must have at most 15 digits (international standard E.164)
    """
    if not phone:
        return False, "Phone number is required."
    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) < 10:
        return False, "Phone number must have at least 10 digits."
    if len(digits) > 15:
        return False, "Phone number is too long. Maximum 15 digits."
    return True, ""


def validate_email(email):
    """
    Checks:
    - Has exactly one @
    - Has a domain with at least one dot after @
    - No spaces
    - Local part (before @) is not empty
    - Domain part has valid characters
    """
    if not email:
        return False, "Email address is required."
    if " " in email:
        return False, "Email address cannot contain spaces."
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Please enter a valid email address (e.g. name@example.com)."
    return True, ""


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "owner_id" not in session:
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            flash("Admin access required.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


def nocache(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"]        = "no-cache"
    resp.headers["Expires"]       = "0"
    return resp


# -----------------------------------------------
# 404 HANDLER
# -----------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(429)
def rate_limit_exceeded(e):
    return render_template("login.html", rate_limited=True), 429


# ===============================================
# PUBLIC ROUTES
# ===============================================

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/search")
def search():
    return render_template("tenant_start.html")


@app.route("/results")
def search_results():
    conn = get_db()

    prop_type = request.args.get("type", "").strip()
    beds      = request.args.get("beds", "").strip()
    min_rent  = request.args.get("min_rent", "").strip()
    max_rent  = request.args.get("max_rent", "").strip()
    group_by  = request.args.get("group", "").strip()

    query = """
        SELECT p.*,
               o.slug, o.name as owner_name, o.brand_name as owner_brand
        FROM properties p
        JOIN owners o ON p.owner_id = o.id
        WHERE o.is_active = 1
        AND (p.parent_id IS NULL OR p.parent_id = 0)
    """
    params = []

    if prop_type:
        query += " AND p.property_type = ?"
        params.append(prop_type)

    if beds:
        if beds == "4":
            query += " AND p.beds >= 4"
        else:
            query += " AND p.beds = ?"
            params.append(int(beds))

    query += " ORDER BY p.id DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    conn2 = get_db()
    properties = []
    for r in rows:
        p = parse_property(r)
        p["display_title"] = p["title"]
        # For complexes, load sub-unit summary
        if p.get("is_complex"):
            units = conn2.execute(
                "SELECT title, beds, status FROM properties WHERE parent_id=? ORDER BY id",
                (p["id"],)
            ).fetchall()
            p["unit_count"] = len(units)
            p["unit_available"] = sum(1 for u in units if u["status"] == "Available")
            # Show unit names (up to 5 then ...)
            names = [u["title"] for u in units if u["title"]]
            if len(names) <= 5:
                p["unit_labels"] = ", ".join(names)
            else:
                p["unit_labels"] = ", ".join(names[:5]) + "..."
        else:
            if min_rent or max_rent:
                rent_num = int("".join(filter(str.isdigit, p["rent"] or "0")))
                if min_rent and rent_num < int(min_rent):
                    continue
                if max_rent and rent_num > int(max_rent):
                    continue
        properties.append(p)
    conn2.close()

    grouped = {}
    if group_by == "type":
        for p in properties:
            key = p.get("property_type") or "Other"
            grouped.setdefault(key, []).append(p)

    elif group_by == "owner":
        for p in properties:
            key = p.get("owner_brand") or p.get("owner_name") or "Unknown"
            grouped.setdefault(key, []).append(p)

    elif group_by == "beds":
        order = ["Studio", "1 Bedroom", "2 Bedrooms", "3 Bedrooms", "4+ Bedrooms"]
        for p in properties:
            b = p.get("beds") or 0
            if b == 0:   key = "Studio"
            elif b == 1: key = "1 Bedroom"
            elif b == 2: key = "2 Bedrooms"
            elif b == 3: key = "3 Bedrooms"
            else:        key = "4+ Bedrooms"
            grouped.setdefault(key, []).append(p)
        grouped = {k: grouped[k] for k in order if k in grouped}

    elif group_by == "status":
        order = ["Available", "Rented", "Maintenance"]
        for p in properties:
            key = p.get("status") or "Other"
            grouped.setdefault(key, []).append(p)
        grouped = {k: grouped[k] for k in order if k in grouped}

    return render_template("search_results.html",
                           properties=properties,
                           grouped=grouped,
                           group_by=group_by,
                           prop_type=prop_type,
                           beds=beds,
                           min_rent=min_rent,
                           max_rent=max_rent)


RESERVED = {"admin", "login", "logout", "dashboard", "create", "edit",
            "delete", "enquiries", "enquire", "static", "favicon.ico",
            "search", "results"}


@app.route("/<slug>")
def owner_portal(slug):
    if slug in RESERVED:
        return redirect(url_for("landing"))

    conn = get_db()
    owner = conn.execute(
        "SELECT * FROM owners WHERE slug=? AND is_active=1", (slug,)
    ).fetchone()

    if not owner:
        conn.close()
        return render_template("404.html"), 404

    properties = [parse_property(r) for r in conn.execute("""
        SELECT * FROM properties
        WHERE owner_id=? AND (parent_id IS NULL OR parent_id=0)
        ORDER BY id DESC
    """, (owner["id"],)).fetchall()]
    conn.close()

    return render_template("owner_portal.html", owner=dict(owner), properties=properties)


@app.route("/<slug>/property/<int:prop_id>")
def property_detail(slug, prop_id):
    conn = get_db()
    owner = conn.execute(
        "SELECT * FROM owners WHERE slug=? AND is_active=1", (slug,)
    ).fetchone()
    if not owner:
        conn.close()
        return render_template("404.html"), 404

    prop = parse_property(conn.execute(
        "SELECT * FROM properties WHERE id=? AND owner_id=?",
        (prop_id, owner["id"])
    ).fetchone())

    if not prop:
        conn.close()
        return render_template("404.html"), 404

    sub_units = []
    if prop.get("is_complex"):
        sub_units = [parse_property(r) for r in conn.execute(
            "SELECT * FROM properties WHERE parent_id=? ORDER BY id",
            (prop_id,)
        ).fetchall()]

    conn.close()
    return render_template("property_detail.html",
                           prop=prop, owner=dict(owner),
                           sub_units=sub_units, slug=slug,
                           whatsapp_phone=clean_phone(owner["phone"] or ""))


# ===============================================
# OWNER AUTH
# ===============================================

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if "owner_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        conn     = get_db()
        owner    = conn.execute(
            "SELECT * FROM owners WHERE LOWER(username)=? AND is_active=1", (username,)
        ).fetchone()
        conn.close()

        if owner and check_password_hash(owner["password"], password):
            session.clear()
            session["owner_id"]   = owner["id"]
            session["owner_name"] = owner["name"]
            session["owner_slug"] = owner["slug"]
            session["brand_name"] = owner["brand_name"]
            flash(f"Welcome back, {owner['name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Incorrect username or password.", "danger")

    return render_template("login.html")


@app.route("/logout", methods=["GET","POST"])
def logout():
    session.clear()
    resp = make_response(redirect("/"))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"]        = "no-cache"
    resp.headers["Expires"]       = "0"
    return resp


# ===============================================
# OWNER DASHBOARD
# ===============================================

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()

    owner = conn.execute(
        "SELECT * FROM owners WHERE id=? AND is_active=1",
        (session["owner_id"],)
    ).fetchone()

    if not owner:
        conn.close()
        session.clear()
        flash("Your account is no longer active.", "danger")
        return redirect(url_for("login"))

    session["brand_name"] = owner["brand_name"]
    session["owner_slug"] = owner["slug"]
    session["owner_name"] = owner["name"]

    all_props = [parse_property(r) for r in conn.execute(
        "SELECT * FROM properties WHERE owner_id=? ORDER BY id DESC",
        (session["owner_id"],)
    ).fetchall()]

    # For complexes, attach unit summary
    for p in all_props:
        if p.get("is_complex"):
            units = conn.execute(
                "SELECT title, beds, status FROM properties WHERE parent_id=? ORDER BY id",
                (p["id"],)
            ).fetchall()
            p["unit_count"] = len(units)
            p["unit_available"] = sum(1 for u in units if u["status"] == "Available")
            names = [u["title"] for u in units if u["title"]]
            p["unit_names"] = " · ".join(names[:5]) + ("..." if len(names) > 5 else "")
        else:
            p["unit_count"] = 0

    properties = all_props

    enquiries = {}
    for row in conn.execute(
        "SELECT property_id, COUNT(*) as cnt FROM enquiries WHERE property_id IN "
        "(SELECT id FROM properties WHERE owner_id=?) GROUP BY property_id",
        (session["owner_id"],)
    ).fetchall():
        enquiries[row["property_id"]] = row["cnt"]

    conn.close()

    resp = make_response(render_template("dashboard.html",
                           properties=properties,
                           enquiries=enquiries,
                           owner_name=session["owner_name"],
                           brand_name=session["brand_name"],
                           owner_slug=session["owner_slug"]))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"]        = "no-cache"
    resp.headers["Expires"]       = "0"
    return resp


@app.route("/create", methods=["GET", "POST"])
@login_required
def create_property():
    if request.method == "POST":
        is_complex     = request.form.get("is_complex") == "1"
        gallery_raw    = request.form.get("gallery_images", "")
        gallery_images = json.dumps([g.strip() for g in gallery_raw.splitlines() if g.strip()])
        images_list    = [g.strip() for g in gallery_raw.splitlines() if g.strip()]
        first_image    = images_list[0] if images_list else ""

        conn = get_db()

        if is_complex:
            # Complex: minimal fields, no rent/beds/baths
            amenities = json.dumps([])
            conn.execute("""INSERT INTO properties
                (owner_id, title, location, rent, status, beds, baths, sqft, image,
                 property_type, security_deposit, facing, maintenance, floor, built,
                 description, amenities, gallery_images, is_complex)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)""", (
                session["owner_id"],
                request.form.get("title"),
                request.form.get("location"),
                "", "Available", 0, 0, 0, first_image,
                request.form.get("property_type"),
                "", request.form.get("facing"), "", "",
                request.form.get("built"),
                request.form.get("description"),
                amenities, gallery_images
            ))
            complex_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            # Save inline units submitted with complex form
            unit_names    = request.form.getlist("unit_title[]")
            unit_rents    = request.form.getlist("unit_rent[]")
            unit_beds     = request.form.getlist("unit_beds[]")
            unit_baths    = request.form.getlist("unit_baths[]")
            unit_sqfts    = request.form.getlist("unit_sqft[]")
            unit_statuses = request.form.getlist("unit_status[]")
            unit_floors   = request.form.getlist("unit_floor[]")
            unit_galleries       = request.form.getlist("unit_gallery_images[]")
            unit_sec_deposits    = request.form.getlist("unit_security_deposit[]")
            unit_maintenances    = request.form.getlist("unit_maintenance[]")

            for i, name in enumerate(unit_names):
                if not name.strip():
                    continue
                # Parse unit gallery images
                ugallery_raw = unit_galleries[i] if i < len(unit_galleries) else ""
                ugallery_list = [g.strip() for g in ugallery_raw.splitlines() if g.strip()]
                ugallery_json = json.dumps(ugallery_list)
                ufirst_image = ugallery_list[0] if ugallery_list else first_image

                conn.execute("""INSERT INTO properties
                    (owner_id, parent_id, title, location, rent, status, beds, baths,
                     sqft, image, property_type, floor, security_deposit, maintenance,
                     description, amenities, gallery_images, is_complex)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)""", (
                    session["owner_id"], complex_id,
                    name.strip(),
                    request.form.get("location"),
                    unit_rents[i] if i < len(unit_rents) else "",
                    unit_statuses[i] if i < len(unit_statuses) else "Available",
                    int(unit_beds[i]) if i < len(unit_beds) and unit_beds[i] else 0,
                    int(unit_baths[i]) if i < len(unit_baths) and unit_baths[i] else 0,
                    int(unit_sqfts[i]) if i < len(unit_sqfts) and unit_sqfts[i] else 0,
                    ufirst_image, request.form.get("property_type"),
                    unit_floors[i] if i < len(unit_floors) else "",
                    unit_sec_deposits[i] if i < len(unit_sec_deposits) else "",
                    unit_maintenances[i] if i < len(unit_maintenances) else "",
                    "", json.dumps([]), ugallery_json
                ))

            conn.commit()
            conn.close()
            flash(f"Complex '{request.form.get('title')}' created with {len([n for n in unit_names if n.strip()])} units!", "success")
            return redirect(url_for("dashboard"))

        else:
            # Single property — all fields
            amenities_raw  = request.form.get("amenities", "")
            amenities      = json.dumps([a.strip() for a in amenities_raw.split(",") if a.strip()])
            conn.execute("""INSERT INTO properties
                (owner_id, title, location, rent, status, beds, baths, sqft, image,
                 property_type, security_deposit, facing, maintenance, floor, built,
                 description, amenities, gallery_images, is_complex)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)""", (
                session["owner_id"],
                request.form.get("title"),
                request.form.get("location"),
                request.form.get("rent"),
                request.form.get("status"),
                request.form.get("beds") or 0,
                request.form.get("baths") or 0,
                request.form.get("sqft") or 0,
                first_image,
                request.form.get("property_type"),
                request.form.get("security_deposit"),
                request.form.get("facing"),
                request.form.get("maintenance"),
                request.form.get("floor"),
                request.form.get("built"),
                request.form.get("description"),
                amenities, gallery_images
            ))
            conn.commit()
            conn.close()
            flash(f"'{request.form.get('title')}' created successfully!", "success")
            return redirect(url_for("dashboard"))

    return render_template("create_property.html", brand_name=session["brand_name"])



@app.route("/add-unit/<int:complex_id>", methods=["GET", "POST"])
@login_required
def add_unit(complex_id):
    """Add a unit to an existing complex property."""
    conn = get_db()
    parent = parse_property(conn.execute(
        "SELECT * FROM properties WHERE id=? AND owner_id=? AND is_complex=1",
        (complex_id, session["owner_id"])
    ).fetchone())

    if not parent:
        flash("Complex not found.", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        gallery_raw    = request.form.get("gallery_images", "")
        amenities_raw  = request.form.get("amenities", "")
        gallery_images = json.dumps([g.strip() for g in gallery_raw.splitlines() if g.strip()])
        amenities      = json.dumps([a.strip() for a in amenities_raw.split(",") if a.strip()])
        images_list    = [g.strip() for g in gallery_raw.splitlines() if g.strip()]
        first_image    = images_list[0] if images_list else parent.get("image", "")

        conn.execute("""INSERT INTO properties
            (owner_id, parent_id, title, location, rent, status, beds, baths, sqft,
             image, property_type, security_deposit, facing, maintenance, floor,
             description, amenities, gallery_images, is_complex)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)""", (
            session["owner_id"],
            complex_id,
            request.form.get("title"),
            parent["location"],   # inherit parent location
            request.form.get("rent"),
            request.form.get("status", "Available"),
            request.form.get("beds") or 0,
            request.form.get("baths") or 0,
            request.form.get("sqft") or 0,
            first_image,
            request.form.get("property_type") or parent.get("property_type"),
            request.form.get("security_deposit"),
            request.form.get("facing"),
            request.form.get("maintenance"),
            request.form.get("floor"),
            request.form.get("description"),
            amenities,
            gallery_images
        ))
        conn.commit()
        conn.close()
        flash(f"Unit added to {parent['title']}!", "success")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("add_unit.html",
                           parent=parent,
                           brand_name=session["brand_name"])



@app.route("/edit-complex/<int:prop_id>", methods=["GET", "POST"])
@login_required
def edit_complex(prop_id):
    conn = get_db()
    prop = parse_property(conn.execute(
        "SELECT * FROM properties WHERE id=? AND owner_id=? AND is_complex=1",
        (prop_id, session["owner_id"])
    ).fetchone())

    if not prop:
        flash("Complex not found.", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        gallery_raw    = request.form.get("gallery_images", "")
        gallery_images = json.dumps([g.strip() for g in gallery_raw.splitlines() if g.strip()])
        images_list    = [g.strip() for g in gallery_raw.splitlines() if g.strip()]
        first_image    = images_list[0] if images_list else prop.get("image", "")

        conn.execute("""UPDATE properties SET
            title=?, location=?, property_type=?, facing=?, built=?,
            description=?, image=?, gallery_images=?
            WHERE id=? AND owner_id=?""", (
            request.form.get("title"),
            request.form.get("location"),
            request.form.get("property_type"),
            request.form.get("facing"),
            request.form.get("built"),
            request.form.get("description"),
            first_image, gallery_images,
            prop_id, session["owner_id"]
        ))
        conn.commit()
        conn.close()
        flash(f"'{request.form.get('title')}' updated!", "success")
        return redirect(url_for("dashboard"))

    sub_units = [parse_property(r) for r in conn.execute(
        "SELECT * FROM properties WHERE parent_id=? ORDER BY id",
        (prop_id,)
    ).fetchall()]
    conn.close()
    prop["gallery_images_str"] = "\n".join(prop["gallery_images"])
    return render_template("edit_complex.html", prop=prop, sub_units=sub_units,
                           brand_name=session["brand_name"])


@app.route("/edit/<int:prop_id>", methods=["GET", "POST"])
@login_required
def edit_property(prop_id):
    conn = get_db()
    prop = parse_property(conn.execute(
        "SELECT * FROM properties WHERE id=? AND owner_id=?",
        (prop_id, session["owner_id"])
    ).fetchone())

    if not prop:
        flash("Property not found.", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    # Units go to edit_unit, complexes go to edit_complex
    if prop.get("parent_id"):
        conn.close()
        return redirect(url_for("edit_unit", unit_id=prop_id))
    if prop.get("is_complex"):
        conn.close()
        return redirect(url_for("edit_complex", prop_id=prop_id))

    if request.method == "POST":
        amenities_raw  = request.form.get("amenities", "")
        gallery_raw    = request.form.get("gallery_images", "")
        amenities      = json.dumps([a.strip() for a in amenities_raw.split(",") if a.strip()])
        gallery_images = json.dumps([g.strip() for g in gallery_raw.splitlines() if g.strip()])
        images_list    = [g.strip() for g in gallery_raw.splitlines() if g.strip()]
        first_image    = images_list[0] if images_list else prop.get("image", "")

        conn.execute("""UPDATE properties SET
            title=?, location=?, rent=?, status=?, beds=?, baths=?, sqft=?, image=?,
            floor=?, built=?, property_type=?, security_deposit=?, facing=?,
            maintenance=?, description=?, amenities=?, gallery_images=?
            WHERE id=? AND owner_id=?""", (
            request.form.get("title"),
            request.form.get("location"),
            request.form.get("rent"),
            request.form.get("status"),
            request.form.get("beds") or 0,
            request.form.get("baths") or 0,
            request.form.get("sqft") or 0,
            first_image,
            request.form.get("floor"),
            request.form.get("built"),
            request.form.get("property_type"),
            request.form.get("security_deposit"),
            request.form.get("facing"),
            request.form.get("maintenance"),
            request.form.get("description"),
            amenities,
            gallery_images,
            prop_id,
            session["owner_id"]
        ))
        conn.commit()
        conn.close()
        flash(f"'{request.form.get('title')}' updated successfully!", "success")
        return redirect(url_for("dashboard"))

    sub_units = []
    if prop.get("is_complex"):
        sub_units = [parse_property(r) for r in conn.execute(
            "SELECT * FROM properties WHERE parent_id=? ORDER BY id",
            (prop_id,)
        ).fetchall()]
        for u in sub_units:
            u["gallery_images_str"] = "\n".join(u["gallery_images"])

    conn.close()
    prop["amenities_str"]      = ", ".join(prop["amenities"])
    prop["gallery_images_str"] = "\n".join(prop["gallery_images"])
    return render_template("edit_property.html", prop=prop, sub_units=sub_units,
                           brand_name=session["brand_name"])



@app.route("/edit-unit/<int:unit_id>", methods=["GET", "POST"])
@login_required
def edit_unit(unit_id):
    conn = get_db()
    unit = parse_property(conn.execute(
        "SELECT * FROM properties WHERE id=? AND owner_id=? AND parent_id IS NOT NULL AND parent_id != 0",
        (unit_id, session["owner_id"])
    ).fetchone())

    if not unit:
        flash("Unit not found.", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    parent = parse_property(conn.execute(
        "SELECT * FROM properties WHERE id=?", (unit["parent_id"],)
    ).fetchone())

    if request.method == "POST":
        gallery_raw    = request.form.get("gallery_images", "")
        amenities_raw  = request.form.get("amenities", "")
        gallery_images = json.dumps([g.strip() for g in gallery_raw.splitlines() if g.strip()])
        amenities      = json.dumps([a.strip() for a in amenities_raw.split(",") if a.strip()])
        images_list    = [g.strip() for g in gallery_raw.splitlines() if g.strip()]
        first_image    = images_list[0] if images_list else unit.get("image", "")

        conn.execute("""UPDATE properties SET
            title=?, rent=?, status=?, beds=?, baths=?, sqft=?, image=?,
            floor=?, facing=?, security_deposit=?, maintenance=?,
            description=?, amenities=?, gallery_images=?
            WHERE id=? AND owner_id=?""", (
            request.form.get("title"),
            request.form.get("rent"),
            request.form.get("status"),
            request.form.get("beds") or 0,
            request.form.get("baths") or 0,
            request.form.get("sqft") or 0,
            first_image,
            request.form.get("floor"),
            request.form.get("facing"),
            request.form.get("security_deposit"),
            request.form.get("maintenance"),
            request.form.get("description"),
            amenities, gallery_images,
            unit_id, session["owner_id"]
        ))
        conn.commit()
        conn.close()
        flash(f"Unit updated!", "success")
        return redirect(url_for("edit_complex", prop_id=unit["parent_id"]))

    conn.close()
    unit["gallery_images_str"] = "\n".join(unit["gallery_images"])
    unit["amenities_str"] = ", ".join(unit["amenities"])
    return render_template("edit_unit.html", unit=unit, parent=parent,
                           brand_name=session["brand_name"])


@app.route("/delete/<int:prop_id>", methods=["POST"])
@login_required
def delete_property(prop_id):
    conn = get_db()
    prop = conn.execute(
        "SELECT * FROM properties WHERE id=? AND owner_id=?",
        (prop_id, session["owner_id"])
    ).fetchone()
    if not prop:
        flash("Property not found.", "danger")
        conn.close()
        return redirect(url_for("dashboard"))
    title = prop["title"]
    sub_ids = [r["id"] for r in conn.execute(
        "SELECT id FROM properties WHERE parent_id=?", (prop_id,)
    ).fetchall()]
    for sid in sub_ids:
        conn.execute("DELETE FROM enquiries WHERE property_id=?", (sid,))
        conn.execute("DELETE FROM properties WHERE id=?", (sid,))
    conn.execute("DELETE FROM enquiries WHERE property_id=?", (prop_id,))
    conn.execute("DELETE FROM properties WHERE id=? AND owner_id=?",
                 (prop_id, session["owner_id"]))
    conn.commit()
    conn.close()
    flash(f"'{title}' deleted.", "info")
    return redirect(url_for("dashboard"))


@app.route("/enquiries")
@login_required
def enquiries():
    conn = get_db()
    rows = conn.execute("""
        SELECT e.*, p.title as property_title
        FROM enquiries e JOIN properties p ON e.property_id = p.id
        WHERE p.owner_id=? ORDER BY e.created_at DESC
    """, (session["owner_id"],)).fetchall()
    conn.close()
    return render_template("enquiries.html", enquiries=rows,
                           owner_name=session["owner_name"],
                           brand_name=session["brand_name"])


# ===============================================
# ADMIN AUTH
# ===============================================

@app.route("/admin/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def admin_login():
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn     = get_db()
        admin    = conn.execute(
            "SELECT * FROM admins WHERE LOWER(email)=?", (email,)
        ).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session.clear()
            session["admin_id"]   = admin["id"]
            session["admin_name"] = admin["name"]
            flash(f"Welcome, {admin['name']}!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Incorrect admin credentials.", "danger")

    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["GET","POST"])
def admin_logout():
    session.clear()
    resp = make_response(redirect("/"))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"]        = "no-cache"
    resp.headers["Expires"]       = "0"
    return resp


# ===============================================
# ADMIN DASHBOARD
# ===============================================

@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db()
    owners           = conn.execute("SELECT * FROM owners ORDER BY created_at DESC").fetchall()
    total_owners     = conn.execute("SELECT COUNT(*) FROM owners").fetchone()[0]
    active_owners    = conn.execute("SELECT COUNT(*) FROM owners WHERE is_active=1").fetchone()[0]
    total_properties = conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
    total_enquiries  = conn.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0]

    prop_counts = {}
    for row in conn.execute(
        "SELECT owner_id, COUNT(*) as cnt FROM properties GROUP BY owner_id"
    ).fetchall():
        prop_counts[row["owner_id"]] = row["cnt"]

    enq_counts = {}
    for row in conn.execute("""
        SELECT p.owner_id, COUNT(*) as cnt FROM enquiries e
        JOIN properties p ON e.property_id = p.id GROUP BY p.owner_id
    """).fetchall():
        enq_counts[row["owner_id"]] = row["cnt"]

    conn.close()

    resp = make_response(render_template("admin_dashboard.html",
                           owners=owners,
                           prop_counts=prop_counts,
                           enq_counts=enq_counts,
                           total_owners=total_owners,
                           active_owners=active_owners,
                           total_properties=total_properties,
                           total_enquiries=total_enquiries,
                           admin_name=session["admin_name"]))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"]        = "no-cache"
    resp.headers["Expires"]       = "0"
    return resp


@app.route("/admin/create-owner", methods=["GET", "POST"])
@admin_required
@csrf.exempt
def admin_create_owner():
    if request.method == "POST":
        name       = request.form.get("name", "").strip()
        username   = request.form.get("username", "").strip().lower()
        email      = request.form.get("email", "").strip().lower()
        password   = request.form.get("password", "").strip()
        phone_raw  = request.form.get("phone", "").strip()
        brand_name = request.form.get("brand_name", "").strip()
        slug       = request.form.get("slug", "").strip().lower().replace(" ", "-")

        if not all([name, username, email, password, brand_name, slug]):
            flash("All fields are required.", "danger")
            return render_template("admin_create_owner.html",
                                   admin_name=session["admin_name"])

        # Validate email
        email_ok, email_err = validate_email(email)
        if not email_ok:
            flash(email_err, "danger")
            return render_template("admin_create_owner.html",
                                   admin_name=session["admin_name"])

        # Validate phone if provided
        if phone_raw:
            phone_ok, phone_err = validate_phone(phone_raw)
            if not phone_ok:
                flash(phone_err, "danger")
                return render_template("admin_create_owner.html",
                                       admin_name=session["admin_name"])

        phone = clean_phone(phone_raw)

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM owners WHERE LOWER(username)=? OR LOWER(email)=? OR slug=?",
            (username, email, slug)
        ).fetchone()

        if existing:
            flash("An owner with that username, email or URL already exists.", "danger")
            conn.close()
            return render_template("admin_create_owner.html",
                                   admin_name=session["admin_name"])

        conn.execute("""INSERT INTO owners
            (name, username, email, password, phone, slug, brand_name, is_active)
            VALUES (?,?,?,?,?,?,?,1)""",
            (name, username, email, generate_password_hash(password), phone, slug, brand_name))
        conn.commit()
        conn.close()
        flash(f"Owner '{name}' created successfully!", "success")

        # Send welcome email with credentials
        email_sent = send_welcome_email(name, email, username, password, slug)
        if email_sent:
            flash(f"Welcome email sent to {email}.", "info")
        else:
            flash("Account created but welcome email could not be sent. Share credentials manually.", "warning")

        return redirect(url_for("admin_dashboard"))

    return render_template("admin_create_owner.html", admin_name=session["admin_name"])


@app.route("/admin/owner/<int:owner_id>")
@admin_required
@csrf.exempt
def admin_view_owner(owner_id):
    conn = get_db()
    owner = conn.execute("SELECT * FROM owners WHERE id=?", (owner_id,)).fetchone()
    if not owner:
        flash("Owner not found.", "danger")
        conn.close()
        return redirect(url_for("admin_dashboard"))

    properties = [parse_property(r) for r in conn.execute(
        "SELECT * FROM properties WHERE owner_id=? ORDER BY id DESC", (owner_id,)
    ).fetchall()]

    enqs = conn.execute("""
        SELECT e.*, p.title as property_title FROM enquiries e
        JOIN properties p ON e.property_id = p.id
        WHERE p.owner_id=? ORDER BY e.created_at DESC
    """, (owner_id,)).fetchall()

    conn.close()
    return render_template("admin_view_owner.html",
                           owner=dict(owner),
                           properties=properties,
                           enquiries=enqs,
                           admin_name=session["admin_name"])


@app.route("/admin/edit-owner/<int:owner_id>", methods=["GET", "POST"])
@admin_required
@csrf.exempt
def admin_edit_owner(owner_id):
    conn = get_db()
    owner = conn.execute("SELECT * FROM owners WHERE id=?", (owner_id,)).fetchone()
    if not owner:
        flash("Owner not found.", "danger")
        conn.close()
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        name       = request.form.get("name", "").strip()
        email      = request.form.get("email", "").strip().lower()
        phone_raw  = request.form.get("phone", "").strip()
        brand_name = request.form.get("brand_name", "").strip()
        slug       = request.form.get("slug", "").strip().lower().replace(" ", "-")

        if not all([name, email, brand_name, slug]):
            flash("All fields are required.", "danger")
            conn.close()
            return redirect(url_for("admin_edit_owner", owner_id=owner_id))

        # Validate email
        email_ok, email_err = validate_email(email)
        if not email_ok:
            flash(email_err, "danger")
            conn.close()
            return redirect(url_for("admin_edit_owner", owner_id=owner_id))

        # Validate phone if provided
        if phone_raw:
            phone_ok, phone_err = validate_phone(phone_raw)
            if not phone_ok:
                flash(phone_err, "danger")
                conn.close()
                return redirect(url_for("admin_edit_owner", owner_id=owner_id))

        phone = clean_phone(phone_raw)

        conflict = conn.execute(
            "SELECT id FROM owners WHERE (LOWER(email)=? OR slug=?) AND id != ?",
            (email, slug, owner_id)
        ).fetchone()

        if conflict:
            flash("That email or URL slug is already used by another owner.", "danger")
            conn.close()
            return redirect(url_for("admin_edit_owner", owner_id=owner_id))

        conn.execute("""UPDATE owners SET
            name=?, email=?, phone=?, brand_name=?, slug=?
            WHERE id=?""",
            (name, email, phone, brand_name, slug, owner_id))
        conn.commit()
        conn.close()
        flash(f"Owner '{name}' updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    return render_template("admin_edit_owner.html",
                           owner=dict(owner),
                           admin_name=session["admin_name"])


@app.route("/admin/toggle-owner/<int:owner_id>", methods=["POST"])
@admin_required
@csrf.exempt
def admin_toggle_owner(owner_id):
    conn = get_db()
    owner = conn.execute("SELECT * FROM owners WHERE id=?", (owner_id,)).fetchone()
    if owner:
        new_status = 0 if owner["is_active"] else 1
        conn.execute("UPDATE owners SET is_active=? WHERE id=?", (new_status, owner_id))
        conn.commit()
        flash(f"Owner '{owner['name']}' {'activated' if new_status else 'deactivated'}.", "success")
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-owner/<int:owner_id>", methods=["POST"])
@admin_required
@csrf.exempt
def admin_delete_owner(owner_id):
    conn = get_db()
    owner = conn.execute("SELECT * FROM owners WHERE id=?", (owner_id,)).fetchone()
    if not owner:
        flash("Owner not found.", "danger")
        conn.close()
        return redirect(url_for("admin_dashboard"))
    name = owner["name"]
    conn.execute("""DELETE FROM enquiries WHERE property_id IN
        (SELECT id FROM properties WHERE owner_id=?)""", (owner_id,))
    conn.execute("DELETE FROM properties WHERE owner_id=?", (owner_id,))
    conn.execute("DELETE FROM owners WHERE id=?", (owner_id,))
    conn.commit()
    conn.close()
    flash(f"Owner '{name}' permanently deleted.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reset-password/<int:owner_id>", methods=["POST"])
@admin_required
@csrf.exempt
def admin_reset_password(owner_id):
    new_password = request.form.get("new_password", "").strip()
    if not new_password:
        flash("Please enter a new password.", "danger")
        return redirect(url_for("admin_view_owner", owner_id=owner_id))
    conn = get_db()
    conn.execute("UPDATE owners SET password=? WHERE id=?",
                 (generate_password_hash(new_password), owner_id))
    conn.commit()
    conn.close()
    flash("Password reset successfully!", "success")
    return redirect(url_for("admin_view_owner", owner_id=owner_id))


@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
@csrf.exempt
def admin_settings():
    if request.method == "POST":
        username       = request.form.get("mail_username", "").strip()
        password       = request.form.get("mail_password", "").strip()
        sender_name    = request.form.get("mail_sender_name", "").strip()
        admin_whatsapp = request.form.get("admin_whatsapp", "").strip()

        if not username or not sender_name:
            flash("Email address and sender name are required.", "danger")
            return redirect(url_for("admin_settings"))

        save_setting("mail_username",    username)
        save_setting("mail_sender_name", sender_name)
        save_setting("admin_whatsapp",   admin_whatsapp)
        if password:
            save_setting("mail_password", password)

        flash("Settings updated successfully!", "success")
        return redirect(url_for("admin_settings"))

    cfg = get_mail_config()
    admin_whatsapp = get_setting("admin_whatsapp", "")
    return render_template("admin_settings.html",
                           admin_name=session["admin_name"],
                           cfg=cfg,
                           admin_whatsapp=admin_whatsapp)



@app.route("/admin/change-password", methods=["POST"])
@admin_required
@csrf.exempt
def admin_change_password():
    current  = request.form.get("current_password", "").strip()
    new_pw   = request.form.get("new_password", "").strip()
    confirm  = request.form.get("confirm_password", "").strip()

    if not current or not new_pw or not confirm:
        flash("All three fields are required.", "danger")
        return redirect(url_for("admin_settings"))

    if new_pw != confirm:
        flash("New password and confirmation do not match.", "danger")
        return redirect(url_for("admin_settings"))

    if len(new_pw) < 8:
        flash("New password must be at least 8 characters.", "danger")
        return redirect(url_for("admin_settings"))

    # Verify current password
    conn  = get_db()
    admin = conn.execute("SELECT * FROM admins WHERE id=1").fetchone()
    conn.close()

    if not admin or not check_password_hash(admin["password"], current):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("admin_settings"))

    # Update password
    conn = get_db()
    conn.execute("UPDATE admins SET password=? WHERE id=1",
                 (generate_password_hash(new_pw),))
    conn.commit()
    conn.close()

    flash("Password changed successfully!", "success")
    return redirect(url_for("admin_settings"))


@app.route("/owner-signup", methods=["GET", "POST"])
@csrf.exempt
def owner_signup():
    if request.method == "POST":
        name       = request.form.get("name", "").strip()
        email      = request.form.get("email", "").strip()
        phone      = request.form.get("phone", "").strip()
        profession = request.form.get("profession", "").strip()
        city       = request.form.get("city", "").strip()
        properties = request.form.get("properties", "").strip()
        message    = request.form.get("message", "").strip()

        if not all([name, email, phone]):
            flash("Name, email and phone are required.", "danger")
            return render_template("owner_signup.html")

        # Send email to admin
        try:
            cfg = get_mail_config()
            app.config["MAIL_USERNAME"]       = cfg["username"]
            app.config["MAIL_PASSWORD"]       = cfg["password"]
            app.config["MAIL_DEFAULT_SENDER"] = (cfg["sender_name"], cfg["username"])
            mail.init_app(app)

            admin_email = cfg["username"]
            msg = Message(
                subject=f"New Owner Signup — {name}",
                recipients=[admin_email]
            )
            msg.html = (
                '<div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;'
                'background:#ffffff;border:1px solid #e5e7eb;border-radius:16px;overflow:hidden;">'
                '<div style="background:#7c3aed;padding:24px 32px;">'
                '<h1 style="color:white;font-size:18px;font-weight:800;margin:0;">New Owner Signup Request</h1>'
                '</div>'
                '<div style="padding:28px;">'
                f'<p style="font-size:14px;color:#6b7280;margin-bottom:20px;">A new owner has signed up on ShivyaSpaces and is waiting for an account.</p>'
                '<table style="width:100%;border-collapse:collapse;">'
                f'<tr style="border-bottom:1px solid #e5e7eb;"><td style="font-size:13px;color:#6b7280;padding:10px 0;width:38%;">Full Name</td><td style="font-size:13px;font-weight:700;color:#111827;padding:10px 0;">{name}</td></tr>'
                f'<tr style="border-bottom:1px solid #e5e7eb;"><td style="font-size:13px;color:#6b7280;padding:10px 0;">Email</td><td style="font-size:13px;font-weight:700;color:#111827;padding:10px 0;">{email}</td></tr>'
                f'<tr style="border-bottom:1px solid #e5e7eb;"><td style="font-size:13px;color:#6b7280;padding:10px 0;">Phone</td><td style="font-size:13px;font-weight:700;color:#111827;padding:10px 0;">{phone}</td></tr>'
                f'<tr style="border-bottom:1px solid #e5e7eb;"><td style="font-size:13px;color:#6b7280;padding:10px 0;">Profession</td><td style="font-size:13px;font-weight:700;color:#111827;padding:10px 0;">{profession or "Not specified"}</td></tr>'
                f'<tr style="border-bottom:1px solid #e5e7eb;"><td style="font-size:13px;color:#6b7280;padding:10px 0;">City</td><td style="font-size:13px;font-weight:700;color:#111827;padding:10px 0;">{city or "Not specified"}</td></tr>'
                f'<tr style="border-bottom:1px solid #e5e7eb;"><td style="font-size:13px;color:#6b7280;padding:10px 0;">No. of Properties</td><td style="font-size:13px;font-weight:700;color:#111827;padding:10px 0;">{properties or "Not specified"}</td></tr>'
                f'<tr><td style="font-size:13px;color:#6b7280;padding:10px 0;">Message</td><td style="font-size:13px;font-weight:700;color:#111827;padding:10px 0;">{message or "None"}</td></tr>'
                '</table>'
                f'<div style="margin-top:24px;padding:16px;background:#f3f0ff;border-radius:10px;">'
                f'<p style="font-size:13px;color:#6d28d9;font-weight:600;margin:0;">Go to your admin dashboard to create an account for this owner and send them their credentials.</p>'
                '</div>'
                '</div></div>'
            )
            mail.send(msg)
        except Exception as e:
            print(f"Admin email failed: {e}")

        # Send WhatsApp to admin
        admin_whatsapp = get_setting("admin_whatsapp", "")
        whatsapp_sent = False
        whatsapp_url = ""
        if admin_whatsapp:
            clean = re.sub(r"[^\d]", "", admin_whatsapp)
            wa_text = (
                f"New Owner Signup on ShivyaSpaces!%0A%0A"
                f"Name: {name}%0A"
                f"Email: {email}%0A"
                f"Phone: {phone}%0A"
                f"Profession: {profession or 'N/A'}%0A"
                f"City: {city or 'N/A'}%0A"
                f"Properties: {properties or 'N/A'}%0A"
                f"Message: {message or 'None'}"
            )
            whatsapp_url = f"https://wa.me/{clean}?text={wa_text}"
            whatsapp_sent = True

        flash("Thank you! Your signup request has been submitted. We'll contact you within 24 hours.", "success")
        return render_template("owner_signup.html",
                               submitted=True,
                               whatsapp_sent=whatsapp_sent,
                               whatsapp_url=whatsapp_url if whatsapp_sent else "")

    return render_template("owner_signup.html", submitted=False)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/termsandconditions")
def termsandconditions():
    return render_template("termsandconditions.html")




@app.route("/tmp-uploads/<filename>")
def serve_tmp_upload(filename):
    """Serve uploaded files from /tmp if static/uploads not writable."""
    from flask import send_from_directory
    import re as _re
    # Security: only allow safe filenames
    if not _re.match(r'^[a-f0-9]{32}\.(jpg|jpeg|png|webp|gif)$', filename):
        from flask import abort
        abort(404)
    return send_from_directory(_tmp_uploads, filename)


@app.route("/upload-image", methods=["POST"])
@csrf.exempt
def upload_image():
    """Upload image — uses Cloudinary if configured, else local static/uploads."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Validate - accept any image type
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    mime = file.content_type or ""
    if not mime.startswith("image/") and ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Please upload an image file (JPG, PNG, WEBP, etc)"}), 400
    if not ext:
        ext = "jpg"

    # Validate size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_UPLOAD_SIZE:
        return jsonify({"error": "Image must be under 5MB"}), 400

    # Try Cloudinary first
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    if CLOUDINARY_AVAILABLE and cloud_name:
        try:
            result = cloudinary.uploader.upload(
                file,
                folder="shivyaspaces",
                transformation=[{"width": 1200, "height": 800, "crop": "limit", "quality": "auto"}]
            )
            return jsonify({"url": result["secure_url"]}), 200
        except Exception as e:
            pass  # Fall through to local storage

    # Local storage fallback
    try:
        import uuid
        filename = f"{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.seek(0)
        file.save(save_path)
        url = f"{UPLOAD_URL_BASE}/{filename}"
        return jsonify({"url": url}), 200
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)