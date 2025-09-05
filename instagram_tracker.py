from flask import Flask, render_template_string, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import os

app = Flask(__name__)

HTML_FORM = """
<!doctype html>
<title>Instagram Reels Tracker</title>
<h2>Enter your Instagram Credentials and Target</h2>
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

def scan_reels(username, password, target):
    # ✅ Headless Chrome options for Railway
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.instagram.com/")
    time.sleep(2)

    # login
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password + Keys.RETURN)
    time.sleep(5)

    # go to reels explore
    driver.get("https://www.instagram.com/explore/reels/")
    time.sleep(5)

    results = []
    checked = set()

    # scan reels
    for _ in range(10):  # number of scrolls
        reels = driver.find_elements(By.XPATH, "//a[contains(@href, '/reel/')]")
        for reel in reels:
            url = reel.get_attribute("href")
            if url in checked:
                continue
            checked.add(url)

            driver.get(url)
            time.sleep(2)

            # likes
            try:
                likes_button = driver.find_element(By.XPATH, "//button[contains(text(),' likes')]")
                likes_button.click()
                time.sleep(1.5)
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

        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(2)

    driver.quit()
    return results


@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        target = request.form["target"]
        results = scan_reels(username, password, target)
    return render_template_string(HTML_FORM, results=results)


# ✅ FIXED FOR RAILWAY
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
