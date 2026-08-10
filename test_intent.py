import re

def get_first_name(raw_name):
    name_parts = [p for p in raw_name.split() if p.strip()]
    if len(name_parts) > 1 and name_parts[0].lower().replace(".", "") in [
        "mr", "ms", "mrs", "dr", "prof", "er"
    ]:
        first_name = name_parts[1]
    elif len(name_parts) > 0:
        first_name = name_parts[0]
    else:
        first_name = raw_name
        
    first_name = re.sub(r"(?i)[’\'\`]s?$", "", first_name)
    first_name = re.sub(r"[\W\d_]+$", "", first_name)
    
    if not first_name.strip():
        first_name = raw_name.strip() or "there"
    return first_name

print(f"John -> {get_first_name('John')}")
print(f"John  Doe -> {get_first_name('John  Doe')}")
print(f"Dr. John -> {get_first_name('Dr. John')}")
print(f"Mr. View -> {get_first_name('Mr. View')}")
print(f"View -> {get_first_name('View')}")
print(f"  -> {get_first_name('  ')}")
print(f"View profile -> {get_first_name('View profile')}")
