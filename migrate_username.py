"""
Run this ONCE to add the username column to your existing database.
Command: python migrate_username.py
"""
import sqlite3

conn = sqlite3.connect("properties.db")
conn.row_factory = sqlite3.Row

# Add username column if it doesn't exist
try:
    conn.execute("ALTER TABLE owners ADD COLUMN username TEXT")
    conn.commit()
    print("Added username column.")
except Exception as e:
    print(f"Column may already exist: {e}")

# For existing owners, set username from their email prefix
owners = conn.execute("SELECT id, email FROM owners").fetchall()
for owner in owners:
    username = owner["email"].split("@")[0].lower()
    conn.execute("UPDATE owners SET username=? WHERE id=?", (username, owner["id"]))
    print(f"Set username '{username}' for owner id {owner['id']}")

conn.commit()
conn.close()
print("\nDone! Usernames have been set.")
print("e.g. mukesh@shivya.com → username is 'mukesh'")