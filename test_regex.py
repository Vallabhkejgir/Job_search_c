import re
print("Match W on René:", re.sub(r"[\W\d_]+$", "", "René"))
print("Match W on John-Doe:", re.sub(r"[\W\d_]+$", "", "John-Doe"))
