import re

name = "Charles profile"
new_name = re.sub(
    r"(?i)(?:[’\'\`]s?|\bs)?\s*\b(profile|graphic link|picture|photo|link)\b.*",
    "",
    name,
)
print(f"'{name}' -> '{new_name}'")

name = "Charles's profile"
new_name = re.sub(
    r"(?i)(?:[’\'\`]s?|\bs)?\s*\b(profile|graphic link|picture|photo|link)\b.*",
    "",
    name,
)
print(f"'{name}' -> '{new_name}'")

