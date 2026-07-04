import re, os

files = [
    os.path.join("templates", "edit_property.html"),
    os.path.join("templates", "edit_complex.html"),
    os.path.join("templates", "edit_unit.html"),
]

for path in files:
    if not os.path.exists(path):
        print(f"NOT FOUND: {path}")
        continue
    
    content = open(path, encoding="utf-8").read()
    original = content
    
    # Fix broken pattern: {%\nif\nprop.X=""\n="Y"\n%}
    # Replace with correct: {% if prop.X == Y %}
    content = re.sub(
        r'\{\%\s*\n\s*if\s*\n\s*(\w+)\.(\w+)=+["\']?["\']?\s*\n\s*=+["\']?(\w+)["\']?\s*\n\s*\%\}',
        r'{% if \1.\2 == \3 %}',
        content
    )
    
    # Fix broken pattern where variable name comes after =""
    content = re.sub(
        r'\{%\s*if\s+(\w+\.\w+)=+["\']+=+["\'](\w+)["\']?\s*%\}',
        r'{% if \1 == \2 %}',
        content
    )
    
    # More aggressive: find any {% if x="" ="y" %} pattern
    content = re.sub(
        r'\{%[-\s]*if\s+([\w.]+)=["\']?\s*=["\']?(\w+)["\']?\s*[-\s]*%\}',
        r'{% if \1 == \2 %}',
        content
    )
    
    if content != original:
        open(path, "w", encoding="utf-8").write(content)
        print(f"FIXED: {path}")
    else:
        print(f"NO CHANGE: {path}")
        # Check if broken pattern still exists
        if 'prop.property_type=""' in content or 'prop.status=""' in content:
            print(f"  WARNING: Still has broken Jinja!")

print("Done!")