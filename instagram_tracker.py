import asyncio
from flask import Flask, render_template_string, request
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver
import time

app = Flask(__name__)

HTML_FORM = """
<!doctype html>
<title>Friends Reels Tracker</title>
<h2>Track Target Likes/Comments on Friend Reels</h2>
<form method="post">
  <label>Username:</label><br>
  <input type="text" name="username"><br>
  <label>Password:</label><br>
  <input type="password" name="password"><br>
  <label>Target Username:</label><br>
  <input type="text" name="target"><br>
  <input type="submit" value="Start Tracking">
</form>
{% if results %}
  <h3>Results</h3>
  <ul>
  {% for r in results %}
    <li>{{ r["type"] }} on <a href="{{ r["reel"] }}" target="_blank">{{ r["reel"] }}</a></li>
  {% endfor %}
  </ul>
{% endif %}
"""

def login_session(username, password) -> WebDriver:
    driver = webdriver.Chrome()
    driver.get("https://www.instagram.com/")
    time.sleep(2)
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password + Keys.RETURN)
    time.sleep(5)
    return driver

def collect_friend_reels(driver: WebDriver):
    # open your profile > “Following activity” or “Friends’ Reels”
    driver.get("https://www.instagram.com/friends/reels/")  
    time.sleep(5)
    reels = set()
    for _ in range(5):
        for link in driver.find_elements(By.XPATH, "//a[contains(@href,'/reel/')]"):
            reels.add(link.get_attribute("href"))
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(1)
    return list(reels)

async def check_reel(driver: WebDriver, url: str, target: str):
    driver.get(url)
    await asyncio.sleep(1.5)
    results = []

    # likes
    try:
        likes_button = driver.find_element(By.XPATH, "//button[contains(text(),' likes')]")
        likes_button.click()
        await asyncio.sleep(1)
        likers = driver.find_elements(By.XPATH, "//div[@role='dialog']//a[contains(@href,'/')]")
        if any(liker.get_attribute("href").endswith(f"/{target}/") for liker in likers):
            results.append({"type": "like", "reel": url})
        driver.find_element(By.XPATH, "//div[@role='dialog']//button").click()
    except:
        pass

    # comments
    comments = driver.find_elements(By.CSS_SELECTOR, "ul ul li div span a")
    if any(c.get_attribute("href").endswith(f"/{target}/") for c in comments):
        results.append({"type": "comment", "reel": url})

    return results

async def scan_reels_async(username, password, target):
    driver = login_session(username, password)
    urls = collect_friend_reels(driver)

    tasks = [check_reel(driver, url, target) for url in urls]
    all_results = await asyncio.gather(*tasks)
    driver.quit()

    results = []
    for r in all_results:
        results.extend(r)
    return results

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        target = request.form["target"]
        results = asyncio.run(scan_reels_async(username, password, target))
    return render_template_string(HTML_FORM, results=results)

if __name__ == "__main__":
    app.run(debug=True)
