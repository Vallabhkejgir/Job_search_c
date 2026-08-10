import re

cases = [
    "John Doe's profile",
    "John Doe’s Profile",
    "John Doe profile",
    "John Doe s profile",
    "John Doe graphic link",
    "John Doe picture",
    "John Doe",
]

for c in cases:
    name = re.sub(
        r"(?i)(?:[’\'\`]s?|\bs)?\s*\b(profile|graphic link|picture|photo|link)\b.*",
        "",
        c,
    )
    print(f"{c} -> {name}")
