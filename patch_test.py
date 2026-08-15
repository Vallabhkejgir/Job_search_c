import re
with open("test_message.py", "r") as f:
    content = f.read()

content = content.replace('if path == "agent.lock": return False\n', '')
with open("test_message.py", "w") as f:
    f.write(content)
