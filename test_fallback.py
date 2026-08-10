import re

def clean_name(name):
    name = re.sub(r"(?i)\s*(is\s+)?open\s+to\s+work.*", "", name)
    name = re.sub(r"(?i)\s*follows this page.*", "", name)
    name = re.sub(r"(?i)\s*works here.*", "", name)
    name = re.sub(r"(?i)^view\s+(.*?)['’`]s\s+profile.*$", r"\1", name)
    name = re.sub(
        r"(?i)(?:[’\'\`]s?|\bs)?\s*\b(profile|graphic link|picture|photo|link)\b.*",
        "",
        name,
    )
    if name.lower().startswith("view "):
        name = re.sub(r"(?i)^view\s+", "", name)

    name = re.sub(r"(?i)^view\b\s*", "", name)
    name = name.strip()
    return name

print(clean_name("View"))
print(clean_name("view"))
print(clean_name("View "))
