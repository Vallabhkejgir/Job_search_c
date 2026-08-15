import re

with open("messenger.py", "r") as f:
    code = f.read()

# other_reason_btn
code = code.replace('''        other_reason_btn = page.locator(
            "button[aria-label*='Other'], button:has-text('Other')"
        ).first''', '''        other_reason_btn = page.locator(
            "button[aria-label*='Other']:visible, button:has-text('Other'):visible"
        ).first''')

# modal_connect
code = code.replace('''                modal_connect = page.locator(
                    "button[aria-label='Connect'], div[role='dialog'] button.artdeco-button--primary"
                ).first''', '''                modal_connect = page.locator(
                    "button[aria-label='Connect']:visible, div[role='dialog'] button.artdeco-button--primary:visible"
                ).first''')

# send_btn fallback
code = code.replace('''                    send_btn = page.locator(
                        "button[aria-label='Send'], button:has-text('Send')"
                    ).first''', '''                    send_btn = page.locator(
                        "button[aria-label='Send']:visible, button:has-text('Send'):visible"
                    ).first''')

with open("messenger.py", "w") as f:
    f.write(code)

print("Done")
