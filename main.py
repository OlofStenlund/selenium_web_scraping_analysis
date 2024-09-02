from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from datetime import datetime

import time
import pandas as pd
import os
import locale

# Define some terms
USER_DIR = r"C:\Users\olofs\AppData\Local\Google\Chrome\User Data"
URL = "https://arbetsformedlingen.se/platsbanken/"
SEARCH_TERM = "Datasamordnare"

# Establish driver
chrome_options = Options()
chrome_options.add_argument(f"--user-data-dir={USER_DIR}")
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(options=chrome_options, service=service)

# Open homepage
driver.get(URL)

# wait for search window to appear
search_window_id = "search_input"
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, search_window_id)))
input_box = driver.find_element(By.ID, search_window_id)
input_box.clear()
input_box.send_keys(SEARCH_TERM + Keys.ENTER)


# Wait for results to load
search_results_cards = "card-container"
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, search_results_cards)))


def click_next() -> bool:
    """
    Clicks the "Nästa" button. 
    Returns False if button cannot be retrieved
    """
    pages_buttons = driver.find_elements(By.TAG_NAME, "digi-button")
    for i in pages_buttons:
        try:
            if i.text == "Nästa":
                i.click()
                time.sleep(10)
                break
        except:
            # break
            print("Failed in retireving buttons")
            return False

def check_next() -> bool:
    """
    Checks if the 'Nästa' button exists.
    """
    pages_buttons = driver.find_elements(By.TAG_NAME, "digi-button")
    labels = [i.text for i in pages_buttons]
    if "Nästa" in labels:
        return True
    else:
        return False


def retrieve_urls_from_page(break_url: str) -> list:
    """
    When a page with adds has loaded, this function extracts the URLs and returns a list.
    """
    links = driver.find_elements(By.TAG_NAME, "pb-feature-search-result-card") # Returns all tags in the result container

    # Must extract the urls and pass a get-request manually
    # Selenium cannot simply loop through tags and keep track of everything
    urls = []
    for link in links:
        if link == break_url:
            break
        else: 
            urls.append(link.find_element(By.TAG_NAME, "a").get_attribute('href'))


    # urls = [link.find_element(By.TAG_NAME, "a").get_attribute('href') for link in links if link != break_url]
    return urls

def parse_dates(date_text: str):
    _date, _time = date_text.split(sep=",")
    _time = _time.split(sep="kl. ")[1]
    _time = _time.replace(".", ":")
    locale.setlocale(locale.LC_TIME, "Swedish_Sweden")
    date_object = datetime.strptime(_date, "%d %B %Y").date()
    time_object = datetime.strptime(_time, "%H:%M").time()
    publish_datetime = datetime.combine(date_object, time_object)
    return publish_datetime


def scrape_urls(urls) -> list:
    """
    Looks for the job description text and returns a list with text strings.
    """
    job_info = []
    for url in urls:
        driver.get(url)
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "jobb-page")))
        jobb_page = driver.find_element(By.CLASS_NAME, "jobb-page")
        ng_star_class = jobb_page.find_element(By.CLASS_NAME, "ng-star-inserted")

        # Extract info on hours, duration and employment
        short_info = ng_star_class.find_element(By.CLASS_NAME, "print-break-inside")
        short_info_text = short_info.text
        short_info_segmented = short_info_text.split("\n")[1:]

        short_info_dict = {
            "omfattning": "",
            "varaktighet": "", 
            "anställningsform": ""
            }
        for i in short_info_segmented:
            key, value = i.split(": ", 1)
            short_info_dict[key.lower()] = value.lower()

        # Extract add ID to use as ID in tables
        add_publ = ng_star_class.find_element(By.XPATH, ".//div[@class='extra-info-section pb-pb-32']")
        add_id = add_publ.text.split(sep="\n")[0]
        add_id = add_id.split(sep=": ")[1]

        # Extract publishing date
        publish_date = add_publ.text.split(sep="\n")[1]
        publish_date = publish_date.split(sep=": ")[1]
        publish_dt = parse_dates(publish_date)
        
        # Extraxt add text
        job_container = ng_star_class.find_element(By.XPATH, ".//div[@class='jobb-container container']")
        job_description = job_container.find_element(By.XPATH, ".//div[@class='section job-description']")
        job_description_text = job_description.text

        try:
            employer_name = driver.find_element(By.ID, "pb-company-name").text
        except:
            employer_name = ""
        try:
            city = driver.find_element(By.ID, "pb-job-location")
            city = city.text.split(sep=":")[1].strip()
        except:
            city = ""

        job = {
            "ID": add_id,
            "URL": url,
            "employer": employer_name,
            "city": city,
            "duration": short_info_dict["varaktighet"],
            "worktime": short_info_dict["omfattning"],
            "jobtype": short_info_dict["anställningsform"],
            "addtext": job_description_text,
            "date": publish_dt
        }

        job_info.append(job)        
    return job_info




stay = True
all_scraped_urls = []

# Define the last URL scraped
try:
    df = pd.read_csv(f"{SEARCH_TERM}_continuous_data.csv")
    last_url = list(df["ID"])[-1]
except:
    last_url = ""

while stay:
    urls = retrieve_urls_from_page(break_url=last_url)
    for url in urls:
        all_scraped_urls.append(url)

    if check_next() == True:
        print("Clicking next")
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.TAG_NAME, "digi-navigation-pagination")))
        pages_buttons = driver.find_elements(By.TAG_NAME, "digi-button")
        for i in pages_buttons:
            try:
                if i.text == "Nästa":
                    # print("clicking again...")
                    i.click()
                    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.TAG_NAME, "digi-navigation-pagination")))
                    break
            except:
                # break
                print("Failed in retireving buttons")
    elif not check_next():
        print("no more pages")
        stay = False



# Fetch old data (if exists)
# Set variable to True or False
try:
    old_snapshot_data = pd.read_csv(f"{SEARCH_TERM}_snapshot_data.csv")
    SNAPSHOT = True
except:
    SNAPSHOT = False

try:
    old_continuous_data = pd.read_csv(f"{SEARCH_TERM}_continuous_data.csv")
    CONTINUOUS = True
except:
    CONTINUOUS = False


# If old data exists, only new URLs will be added to the below list.
# Else, all URLs will be added, as they are indeed all new.
new_df_rows = []

if SNAPSHOT: # If old data exists, compare the old and new to extract only the new URLs
    old_urls = list(old_snapshot_data["URL"].values)
    new_urls = [i for i in all_scraped_urls if i not in old_urls]
else: # If not, add all URLs tot he list
    new_urls = all_scraped_urls.copy()


scraping_results = scrape_urls(new_urls)
    
# Placeholder. Create dictionary object of the data.
# Create dataframe 
for i in scraping_results:
    new_df_rows.append(
        {   
            "ID": i["ID"],
            "URL": i["URL"],
            "employer": i["employer"],
            "city": i["city"],
            "duration": i["duration"],
            "worktime": i["worktime"],
            "jobtype": i["jobtype"],
            "addtext": i["addtext"],
            "date": i["date"]
        }
    )
new_rows = pd.DataFrame(new_df_rows)

# Append the DF-data to csv-file
if not SNAPSHOT:
    new_rows.to_csv(f"{SEARCH_TERM}_snapshot_data.csv", mode="a", header=True, index=False)
else:
    new_rows.to_csv(f"{SEARCH_TERM}_snapshot_data.csv", mode="a", header=False, index=False)

new_rows.to_csv(f"{SEARCH_TERM}_continous_data.csv", mode="a", header=False, index=False)