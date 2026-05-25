from werkzeug.security import generate_password_hash
import sqlite3

new_password = "ShivyaAdmin2024"  # change this to whatever you want

conn = sqlite3.connect('properties.db')
conn.execute("UPDATE admins SET password=? WHERE email='admin@platform.com'",
             (generate_password_hash(new_password),))
conn.commit()
conn.close()
print("Done! New password:", new_password)