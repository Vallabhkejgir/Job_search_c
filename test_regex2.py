import re
print("René:", repr(re.sub(r"[\W\d_]+$", "", "René")))
print("John-Doe:", repr(re.sub(r"[\W\d_]+$", "", "John-Doe")))
print("John_Doe:", repr(re.sub(r"[\W\d_]+$", "", "John_Doe")))
print("John Doe:", repr(re.sub(r"[\W\d_]+$", "", "John Doe")))
print("John.:", repr(re.sub(r"[\W\d_]+$", "", "John.")))
print("John123:", repr(re.sub(r"[\W\d_]+$", "", "John123")))
