import re

with open('job_scraper.py', 'r') as f:
    content = f.read()

old_lambda1 = 'title_elem = soup.find(class_=lambda x: x and ("title" in x.lower() or "sr-only" in x.lower()))'
new_lambda1 = 'title_elem = soup.find(class_=lambda x: x and isinstance(x, str) and ("title" in x.lower() or "sr-only" in x.lower()))'

old_lambda2 = 'comp_elem = soup.find(class_=lambda x: x and "subtitle" in x.lower())'
new_lambda2 = 'comp_elem = soup.find(class_=lambda x: x and isinstance(x, str) and "subtitle" in x.lower())'

old_lambda3 = 'comp_link = soup.find("a", href=lambda x: x and "/company/" in x)'
new_lambda3 = 'comp_link = soup.find("a", href=lambda x: x and isinstance(x, str) and "/company/" in x)'


if old_lambda1 in content:
    content = content.replace(old_lambda1, new_lambda1)
    content = content.replace(old_lambda2, new_lambda2)
    content = content.replace(old_lambda3, new_lambda3)
    with open('job_scraper.py', 'w') as f:
        f.write(content)
    print("Fixed job_scraper.py lambdas")
else:
    print("Could not find old lambda 1")
