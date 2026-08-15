import re

with open("messenger.py", "r") as f:
    code = f.read()

# modal locator
code = code.replace('''            modal = page.locator("div[role='dialog']").first''', '''            modal = page.locator("div[role='dialog']:visible").first''')

with open("messenger.py", "w") as f:
    f.write(code)

print("Done")
