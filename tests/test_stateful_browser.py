import sys
import os
import inspect
TEST_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))
PROJ_DIR = os.path.dirname(TEST_DIR)
sys.path.insert(0, PROJ_DIR)

import mechanicalsoup
import re
from bs4 import BeautifulSoup


def test_submit_online():
    """Complete and submit the pizza form at http://httpbin.org/forms/post """
    browser = mechanicalsoup.StatefulBrowser()
    browser.set_user_agent('testing https://github.com/hickford/MechanicalSoup')
    browser.open("http://httpbin.org/")
    for link in browser.links():
        if link["href"] == "/":
            browser.follow_link(link)
            break
    browser.follow_link("forms/post")
    assert browser.get_url() == "http://httpbin.org/forms/post"
    browser.select_form("form")
    browser["custname"] = "Customer Name Here"
    browser["size"] = "medium"
    browser["topping"] = ("cheese")
    browser["comments"] = "Some comment here"
    browser.get_current_form().set("nosuchfield", "new value", True)
    response = browser.submit_selected()
    json = response.json()
    data = json["form"]
    assert data["custname"] == "Customer Name Here"
    assert data["custtel"] == ""  # web browser submits "" for input left blank
    assert data["size"] == "medium"
    assert data["topping"] == "cheese"
    assert data["comments"] == "Some comment here"
    assert data["nosuchfield"] == "new value"

    assert (json["headers"]["User-Agent"] ==
            'testing https://github.com/hickford/MechanicalSoup')
    # Ensure we haven't blown away any regular headers
    assert set(('Content-Length', 'Host', 'Content-Type', 'Connection', 'Accept',
            'User-Agent', 'Accept-Encoding')).issubset(json["headers"].keys())


def test_no_404():
    browser = mechanicalsoup.StatefulBrowser()
    resp = browser.open("http://httpbin.org/nosuchpage")
    assert resp.status_code == 404

def test_404():
    browser = mechanicalsoup.StatefulBrowser(raise_on_404=True)
    try:
        resp = browser.open("http://httpbin.org/nosuchpage")
    except mechanicalsoup.LinkNotFoundError:
        pass
    else:
        assert False
    resp = browser.open("http://httpbin.org/")
    assert resp.status_code == 200

def test_user_agent():
    browser = mechanicalsoup.StatefulBrowser(user_agent='007')
    resp = browser.open("http://httpbin.org/user-agent")
    assert resp.json() == {'user-agent': '007'}

def test_open_relative():
    # Open an arbitrary httpbin page to set the current URL
    browser = mechanicalsoup.StatefulBrowser()
    browser.open("http://httpbin.org/html")

    # Open a relative page and make sure remote host and browser agree on URL
    resp = browser.open_relative("/get")
    assert resp.json()['url'] == "http://httpbin.org/get"
    assert browser.get_url() == "http://httpbin.org/get"

    # Test passing additional kwargs to the session
    resp = browser.open_relative("/basic-auth/me/123", auth=('me', '123'))
    assert browser.get_url() == "http://httpbin.org/basic-auth/me/123"
    assert resp.json() == {"authenticated": True, "user": "me"}

def test_links():
    browser = mechanicalsoup.StatefulBrowser()
    html = '<a class="bluelink" href="/blue" id="blue_link">A Blue Link</a>'
    expected = [BeautifulSoup(html).a]
    browser.open_fake_page(html)

    # Test StatefulBrowser.links url_regex argument
    assert browser.links(url_regex="bl") == expected
    assert browser.links(url_regex="bluish") == []

    # Test StatefulBrowser.links link_text argument
    assert browser.links(link_text="A Blue Link") == expected
    assert browser.links(link_text="Blue") == []

    # Test StatefulBrowser.links kwargs passed to BeautifulSoup.find_all
    assert browser.links(string=re.compile('Blue')) == expected
    assert browser.links(class_="bluelink") == expected
    assert browser.links(id="blue_link") == expected
    assert browser.links(id="blue") == []

if __name__ == '__main__':
    test_submit_online()
    test_no_404()
    test_404()
    test_user_agent()
    test_open_relative()
    test_links()
