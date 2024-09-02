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

def establish_driver(user_dir) -> webdriver:
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={user_dir}")
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(options=chrome_options, service=service)
    return driver

def click_next(driver) -> bool:
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

def check_next(driver) -> bool:
    """
    Checks if the 'Nästa' button exists.
    """
    pages_buttons = driver.find_elements(By.TAG_NAME, "digi-button")
    labels = [i.text for i in pages_buttons]
    if "Nästa" in labels:
        return True
    else:
        return False


def retrieve_urls_from_page(break_url: str, driver) -> list:
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


def scrape_urls(urls, driver) -> list:
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