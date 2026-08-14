import os

with open('dashboard.py', 'r') as f:
    content = f.read()

old_code = """def is_agent_running():
    global AGENT_PROCESS
    if AGENT_PROCESS is not None and AGENT_PROCESS.poll() is None:
        return True
    if os.path.exists("agent.lock"):
        return True
    return False"""

new_code = """def is_agent_running():
    global AGENT_PROCESS
    if AGENT_PROCESS is not None and AGENT_PROCESS.poll() is None:
        return True
    if os.path.exists("agent.lock"):
        try:
            with open("agent.lock", "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, OSError):
            return False
    return False"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('dashboard.py', 'w') as f:
        f.write(content)
    print("Updated dashboard.py")
else:
    print("Old code not found in dashboard.py")
