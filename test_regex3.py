import re

first_name = "John's,"
first_name = re.sub(r"(?i)[’\'\`]s?$", "", first_name)
first_name = re.sub(r"[\W\d_]+$", "", first_name)

print(first_name)
