with open("messenger.py", "r") as f:
    code = f.read()

import re

# 1. connect_selectors
code = code.replace('''        connect_selectors = [
            "button.pvs-profile-actions__action:has-text('Connect')",
            "button[aria-label*='Invite']",
            "button[aria-label*='Connect']",
            "main button:has-text('Connect')",
            "main a:has-text('Connect')",
        ]''', '''        connect_selectors = [
            "button.pvs-profile-actions__action:has-text('Connect'):visible",
            "button[aria-label*='Invite']:visible",
            "button[aria-label*='Connect']:visible",
            "main button:has-text('Connect'):visible",
            "main a:has-text('Connect'):visible",
        ]''')

# 2. more_selectors
code = code.replace('''            more_selectors = [
                "button.pvs-profile-actions__action:has-text('More')",
                "button[aria-label='More actions']",
                "button[aria-label='More']",
                "main button:has-text('More')",
            ]''', '''            more_selectors = [
                "button.pvs-profile-actions__action:has-text('More'):visible",
                "button[aria-label='More actions']:visible",
                "button[aria-label='More']:visible",
                "main button:has-text('More'):visible",
            ]''')

# 3. dropdown_connect
code = code.replace('''                dropdown_connect = [
                    "div.artdeco-dropdown__content button:has-text('Connect')",
                    "div.artdeco-dropdown__content span:has-text('Connect')",
                    "ul *:has-text('Connect')",
                    "div[role='menu'] *:has-text('Connect')",
                ]''', '''                dropdown_connect = [
                    "div.artdeco-dropdown__content button:has-text('Connect'):visible",
                    "div.artdeco-dropdown__content span:has-text('Connect'):visible",
                    "ul *:has-text('Connect'):visible",
                    "div[role='menu'] *:has-text('Connect'):visible",
                ]''')

# 4. add_note_selectors
code = code.replace('''        add_note_selectors = [
            "button[aria-label='Add a note']",
            "button:has-text('Add a note')",
            "button:has-text('Add note')",
            "button.artdeco-button--secondary:has-text('Add a note')",
        ]''', '''        add_note_selectors = [
            "button[aria-label='Add a note']:visible",
            "button:has-text('Add a note'):visible",
            "button:has-text('Add note'):visible",
            "button.artdeco-button--secondary:has-text('Add a note'):visible",
        ]''')

# 5. send_selectors
code = code.replace('''                send_selectors = [
                    "button[aria-label='Send invitation']",
                    "button[aria-label='Send now']",
                    "button:has-text('Send')",
                    "button:has-text('Send without a note')",  # Sometimes the button text changes
                ]''', '''                send_selectors = [
                    "button[aria-label='Send invitation']:visible",
                    "button[aria-label='Send now']:visible",
                    "button:has-text('Send'):visible",
                    "button:has-text('Send without a note'):visible",  # Sometimes the button text changes
                ]''')

# 6. msg_box
code = code.replace('''                msg_box = page.locator(
                    "textarea[name='message'], textarea#custom-message, div[role='dialog'] textarea"
                ).first''', '''                msg_box = page.locator(
                    "textarea[name='message']:visible, textarea#custom-message:visible, div[role='dialog'] textarea:visible"
                ).first''')

code = code.replace('''            msg_box = page.locator(
                "textarea[name='message'], textarea#custom-message, div[role='dialog'] textarea"
            ).first''', '''            msg_box = page.locator(
                "textarea[name='message']:visible, textarea#custom-message:visible, div[role='dialog'] textarea:visible"
            ).first''')

with open("messenger.py", "w") as f:
    f.write(code)

print("Done")
