from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import pandas as pd
import os
import locale
from datetime import datetime

from searches import titles_list
import scraping_utils as su
from analysis_utils import find_old_qual_ids, find_qualifications
from qualifications import QUALIFICATIONS

# Define some terms
USER_DIR = r"C:\Users\olofs\AppData\Local\Google\Chrome\User Data"
URL = "https://arbetsformedlingen.se/platsbanken/"


driver = su.establish_driver(USER_DIR)


for title in titles_list:
    SEARCH_TERM = title

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

    # Gather URLs    
    all_scraped_urls = []
    stay = True
    while stay:
        urls = su.retrieve_urls_from_page(driver=driver)
        for url in urls: # Append to new list, as the above function can be run several times
            all_scraped_urls.append(url)

        # Click through pages, repeating the process
        if su.check_next(driver) == True:
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.TAG_NAME, "digi-navigation-pagination")))
            pages_buttons = driver.find_elements(By.TAG_NAME, "digi-button")
            for i in pages_buttons:
                try:
                    if i.text == "Nästa":
                        i.click()
                        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.TAG_NAME, "digi-navigation-pagination")))
                        break
                except:
                    raise ValueError("digi-navigation-pagination tag was not found on page.")
        elif not su.check_next(driver):
            stay = False



    # Fetch old data (if exists)
    # Set variable to True or False
    old_snapshot_data, SNAPSHOT = su.fetch_old_snapshot(SEARCH_TERM)
    old_continuous_data, CONTINUOUS = su.fetch_continuous_data(SEARCH_TERM)


    

    if CONTINUOUS: # If old data exists, compare the old and new to extract only the new URLs
        old_urls = list(old_continuous_data["URL"].values)
        new_urls = [i for i in all_scraped_urls if i not in old_urls]
        print(f"{SEARCH_TERM}: {len(new_urls)} new adds")
    else: # If not, add all URLs tot he list
        new_urls = all_scraped_urls.copy()

    # If old data exists, only new URLs will be added to the below list.
    # Else, all URLs will be added, as they are indeed all new.
    rows_to_be_added = []

    # Scrape only the relevant URLs
    scraping_results = su.scrape_urls(new_urls, driver)
        
    for i in scraping_results:
        rows_to_be_added.append(
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

    rows_to_be_added = sorted(rows_to_be_added, key=lambda x: x["date"])
    new_df_rows = pd.DataFrame(rows_to_be_added)

    # Append the DF-data to csv-file
    new_df_rows.to_csv(f"{SEARCH_TERM}_snapshot_data.csv", header=True, index=False)

    if not CONTINUOUS:
        new_df_rows.to_csv(f"{SEARCH_TERM}_continuous_data.csv", mode="a", header=True, index=False)
    else:
        new_df_rows.to_csv(f"{SEARCH_TERM}_continuous_data.csv", mode="a", header=False, index=False)


    # Update the qualifications csv-file
    df, ids = find_qualifications(search_term=SEARCH_TERM, qualifications_list=QUALIFICATIONS)
    try: 
        old_df = pd.read_csv(f"qualifications_dfs/{SEARCH_TERM}_qualifications.csv")
        df.to_csv(f"qualifications_dfs/{SEARCH_TERM}_qualifications.csv", mode="a", header=False, index=False)
    except:
        df.to_csv(f"qualifications_dfs/{SEARCH_TERM}_qualifications.csv", mode="a", header=True, index=False)
