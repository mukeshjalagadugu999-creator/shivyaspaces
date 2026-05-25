import sqlite3
import json
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("properties.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS enquiries")
cursor.execute("DROP TABLE IF EXISTS properties")
cursor.execute("DROP TABLE IF EXISTS owners")
cursor.execute("DROP TABLE IF EXISTS admins")

# ADMINS
cursor.execute("""
CREATE TABLE admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# OWNERS
cursor.execute("""
CREATE TABLE owners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    phone TEXT,
    slug TEXT UNIQUE NOT NULL,
    brand_name TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# PROPERTIES
cursor.execute("""
CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT,
    location TEXT,
    rent TEXT,
    status TEXT,
    beds INTEGER,
    baths INTEGER,
    sqft INTEGER,
    image TEXT,
    property_type TEXT,
    security_deposit TEXT,
    facing TEXT,
    maintenance TEXT,
    floor TEXT,
    built TEXT,
    description TEXT,
    amenities TEXT,
    gallery_images TEXT,
    is_complex INTEGER DEFAULT 0,
    parent_id INTEGER DEFAULT NULL,
    FOREIGN KEY (owner_id) REFERENCES owners(id)
)
""")

# ENQUIRIES — full rental application
cursor.execute("""
CREATE TABLE enquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,

    -- Personal details
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    date_of_birth TEXT,
    nationality TEXT,

    -- Professional details
    profession TEXT,
    employer TEXT,
    monthly_income TEXT,

    -- Rental intent
    tenant_type TEXT,
    num_occupants TEXT,
    move_in_date TEXT,
    lease_duration TEXT,
    have_pets TEXT,
    pet_details TEXT,

    -- Message
    message TEXT,

    -- Agreement
    agreed_to_terms INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id)
)
""")

# INSERT ADMIN
cursor.execute("INSERT INTO admins (name, email, password) VALUES (?,?,?)", (
    "Admin", "admin@platform.com", generate_password_hash("admin123")
))

# INSERT MUKESH
cursor.execute("INSERT INTO owners (name, email, password, phone, slug, brand_name) VALUES (?,?,?,?,?,?)", (
    "Mukesh", "mukesh@shivya.com", generate_password_hash("password123"),
    "+91 98765 43210", "shivya-properties", "Shivya Properties"
))
mukesh_id = cursor.lastrowid

# INSERT PRIYA
cursor.execute("INSERT INTO owners (name, email, password, phone, slug, brand_name) VALUES (?,?,?,?,?,?)", (
    "Priya", "priya@priya.com", generate_password_hash("priya123"),
    "+91 91234 56789", "priya-properties", "Priya Properties"
))
priya_id = cursor.lastrowid


def add_property(data):
    cursor.execute("""INSERT INTO properties
        (owner_id, title, location, rent, status, beds, baths, sqft, image,
         property_type, security_deposit, facing, maintenance, floor, built,
         description, amenities, gallery_images, is_complex, parent_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", data)
    return cursor.lastrowid


shivya_id = add_property((mukesh_id, "Shivya Heights", "Whitefield, Bangalore", "₹32,000", "Available", 3, 2, 1800, "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "Mixed Use Property", "₹1,50,000", "North East Facing", "Included", "Multiple", "2022", "Shivya Heights is a premium apartment community in Whitefield with residential and commercial spaces.", json.dumps(["Swimming Pool","Gym","24/7 Security","Power Backup","Clubhouse","Children's Play Area","Visitor Parking","CCTV Surveillance"]), json.dumps(["https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800","https://images.unsplash.com/photo-1494526585095-c41746248156?w=800","https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800","https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800"]), 1, None))
add_property((mukesh_id, "Shivya 1BHK", "Shivya Heights, Whitefield", "₹32,000", "Available", 1, 1, 850, "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", "1BHK Apartment", "₹64,000", "East Facing", "₹2,000/month", "2nd Floor", "2022", "Modern 1BHK with balcony, modular kitchen and premium fittings.", json.dumps(["Lift Access","Power Backup","Parking","Security","Balcony","WiFi Ready"]), json.dumps(["https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800","https://images.unsplash.com/photo-1494526585095-c41746248156?w=800"]), 0, shivya_id))
add_property((mukesh_id, "Shivya 2BHK", "Shivya Heights, Whitefield", "₹52,000", "Available", 2, 2, 1800, "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800", "2BHK Apartment", "₹1,04,000", "North East Facing", "₹3,500/month", "3rd Floor", "2022", "Spacious 2BHK with dual balconies and premium fittings.", json.dumps(["Lift Access","Power Backup","Covered Parking","24/7 Security","Dual Balconies","WiFi Ready"]), json.dumps(["https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800","https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800"]), 0, shivya_id))
add_property((mukesh_id, "Shivya Shop", "Shivya Heights, Whitefield", "₹75,000", "Available", 0, 2, 1200, "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800", "Commercial Retail", "₹2,25,000", "East Facing", "₹5,000/month", "Ground Floor", "2022", "Premium ground-floor commercial shop with glass frontage.", json.dumps(["Glass Frontage","High Ceiling","Power Backup","24/7 Security","CCTV","Dedicated Parking"]), json.dumps(["https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800"]), 0, shivya_id))
add_property((mukesh_id, "Brigade Bricklane", "Kogilu Main Road, Bangalore", "₹48,000", "Available", 2, 2, 1450, "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800", "Apartment", "₹1,20,000", "East Facing", "Included", "3rd Floor", "2023", "Modern apartment with premium clubhouse and landscaped gardens.", json.dumps(["Swimming Pool","Gym","Clubhouse","24/7 Security","Jogging Track","Covered Parking"]), json.dumps(["https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800","https://images.unsplash.com/photo-1494526585095-c41746248156?w=800"]), 0, None))
add_property((mukesh_id, "Brigade Utopia", "Varthur Road, Bangalore", "₹65,000", "Available", 3, 3, 2100, "https://images.unsplash.com/photo-1494526585095-c41746248156?w=800", "Apartment", "₹2,00,000", "North Facing", "Included", "5th Floor", "2023", "Luxury township with smart living spaces and premium finishes.", json.dumps(["Swimming Pool","Gym","Clubhouse","24/7 Security","Jogging Track","Covered Parking"]), json.dumps(["https://images.unsplash.com/photo-1494526585095-c41746248156?w=800","https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800"]), 0, None))
add_property((mukesh_id, "NH Residency", "Electronic City, Bangalore", "₹38,000", "Available", 2, 2, 1200, "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800", "Apartment", "₹90,000", "West Facing", "Included", "4th Floor", "2021", "Premium apartment with excellent IT hub connectivity.", json.dumps(["Swimming Pool","Gym","Clubhouse","24/7 Security","Power Backup","Jogging Track"]), json.dumps(["https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800","https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800"]), 0, None))
add_property((priya_id, "Priya Garden Villas", "Koramangala, Bangalore", "₹85,000", "Available", 3, 3, 2400, "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800", "Villa", "₹2,50,000", "South Facing", "Included", "Ground + 1", "2021", "Luxurious garden villa in Koramangala with private garden and premium finishes.", json.dumps(["Private Garden","Swimming Pool","Gym","24/7 Security","Covered Parking","Smart Home"]), json.dumps(["https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800","https://images.unsplash.com/photo-1494526585095-c41746248156?w=800"]), 0, None))
add_property((priya_id, "Priya Studio Loft", "Indiranagar, Bangalore", "₹28,000", "Available", 1, 1, 600, "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "Studio Apartment", "₹56,000", "East Facing", "₹1,500/month", "4th Floor", "2023", "Stylish studio loft in Indiranagar, perfect for young professionals.", json.dumps(["Fully Furnished","High Speed WiFi","Power Backup","24/7 Security","Rooftop Access"]), json.dumps(["https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800","https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800"]), 0, None))

conn.commit()
conn.close()
print("✅ Database created!")
print("Admin: admin@platform.com / admin123")
print("Mukesh: mukesh@shivya.com / password123")
print("Priya: priya@priya.com / priya123")