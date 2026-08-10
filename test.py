import re
names = ["John", "René", "José", "John's", "O'Connor", "Malinka-", "Dr.", "João", "John123", "User_", "John's"]
for n in names:
    res = re.sub(r"(?i)[’\'\`]s?$", "", n)
    res = re.sub(r"[\W\d_]+$", "", res)
    print(f"{n} -> {res}")
