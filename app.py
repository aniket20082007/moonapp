from flask import Flask, request, render_template, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from flask_cors import CORS  # ✅ Import CORS to allow frontend access
import os

app = Flask(__name__, template_folder="templates")  
CORS(app)  # ✅ Enable CORS for all origins

# ✅ ChromeDriver path (Make sure it's accessible)
chrome_driver_path = "/app/.chromedriver/bin/chromedriver" if os.getenv("RAILWAY_ENVIRONMENT") else "C:\\Users\\anike\\Desktop\\chromedriver.exe"

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--log-level=3")

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# ✅ Function to fetch moon visibility percentage
def get_moon_visibility(date1, date2):
    url = f"https://phasesmoon.com/birthdaymoon{date1}and{date2}.html"
    
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Visible')]"))
        )
        illumination_values = driver.find_elements(By.XPATH, "//td[contains(text(), 'Visible')]")

        if len(illumination_values) >= 2:
            return float(illumination_values[0].text.strip().replace("% Visible", ""))
        else:
            return None
    except Exception as e:
        print(f"Error fetching moon visibility: {e}")  # ✅ Debugging log
        return None

@app.route("/")
def home():
    return render_template("index.html")  # ✅ Loads frontend

@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        birthdate_input = request.form["birthdate"]
        start_date_input = request.form["start_date"]
        end_date_input = request.form["end_date"]

        birthdate = datetime.strptime(birthdate_input, "%Y-%m-%d")
        start_date = datetime.strptime(start_date_input, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_input, "%Y-%m-%d")
        dummy_date = birthdate + timedelta(days=1)

        birthdate_str = birthdate.strftime("%d%B%Y")
        dummy_date_str = dummy_date.strftime("%d%B%Y")

        # ✅ Fetch birthdate moon visibility
        birth_moon_visibility = get_moon_visibility(birthdate_str, dummy_date_str)
        if birth_moon_visibility is None:
            return jsonify({"error": "Could not fetch moon visibility data for birthdate."})

        tbf = round(100 - birth_moon_visibility, 2)

        # ✅ Find closest date to `tbf`
        closest_date = None
        closest_diff = float("inf")
        exact_matches = []

        current_date = start_date
        while current_date < end_date:
            next_date = current_date + timedelta(days=1)
            date1 = current_date.strftime("%d%B%Y")
            date2 = next_date.strftime("%d%B%Y")

            visibility = get_moon_visibility(date1, date2)
            if visibility is not None:
                difference = abs(visibility - tbf)

                if difference < closest_diff:
                    closest_diff = difference
                    closest_date = current_date.strftime("%d-%m-%Y")
                    exact_matches = [closest_date]

                elif difference == closest_diff:
                    exact_matches.append(current_date.strftime("%d-%m-%Y"))

            current_date = next_date  # Move to next date

        # ✅ Return JSON response
        return jsonify({
            "birthdate_visibility": birth_moon_visibility,
            "tbf": tbf,
            "closest_dates": exact_matches if exact_matches else [closest_date]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # ✅ Handle errors

# ✅ Deployment-ready run command
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
