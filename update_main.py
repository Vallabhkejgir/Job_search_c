import os

with open('main.py', 'r') as f:
    content = f.read()

old_code = """    lock_file = "agent.lock"
    if os.path.exists(lock_file):
        print("Agent is already running (agent.lock exists). Exiting.")
        return

    try:
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))"""

new_code = """    lock_file = "agent.lock"
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
        except (ValueError, OSError):
            try:
                os.remove(lock_file)
            except OSError:
                pass

    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w") as f:
            f.write(str(os.getpid()))
    except FileExistsError:
        print("Agent is already running (agent.lock exists). Exiting.")
        return"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('main.py', 'w') as f:
        f.write(content)
    print("Updated main.py")
else:
    print("Old code not found in main.py")
