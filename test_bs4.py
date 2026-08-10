from bs4 import BeautifulSoup
html = '<div>Hello</div><p>World</p>'
soup = BeautifulSoup(html, 'html.parser')
def test_class(x):
    print("Type of x:", type(x), repr(x))
    return False
soup.find(class_=test_class)
