import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import scraping_utils as su
from analysis_utils import find_qualifications
from job_titles import job_titles_list
from qualifications import QUALIFICATIONS


USER_DIR = r"C:\Users\olofs\AppData\Local\Google\Chrome\User Data"
URL = "https://arbetsformedlingen.se/platsbanken/"
driver = su.establish_driver(USER_DIR)


for JOB_TITLE in job_titles_list:
    ## 1: Get all URLS for the search
    driver.get(URL)

    search_window_id = "search_input"
    WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.ID, search_window_id)))
    input_box = driver.find_element(By.ID, search_window_id)
    input_box.clear()
    input_box.send_keys(JOB_TITLE + Keys.ENTER)

    search_results_cards = "card-container"
    WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.CLASS_NAME, search_results_cards)))
  
    all_scraped_urls = []
    stay = True
    while stay:
        urls = su.retrieve_urls_from_page(driver=driver)
        for url in urls: # Append to new list, as the above function can be run several times
            all_scraped_urls.append(url)
        # Click through pages, repeating the process
        if su.check_next(driver) == True:
            WebDriverWait(driver, 5).until(ec.visibility_of_element_located((By.TAG_NAME, "digi-navigation-pagination")))
            pages_buttons = driver.find_elements(By.TAG_NAME, "digi-button")
            for i in pages_buttons:
                try:
                    if i.text == "Nästa":
                        i.click()
                        WebDriverWait(driver, 5).until(ec.visibility_of_element_located((By.TAG_NAME, "digi-navigation-pagination")))
                        break
                except:
                    raise ValueError("digi-navigation-pagination tag was not found on page.")
        elif not su.check_next(driver):
            stay = False

    ## 2: Make sure only new urls are scraped
    old_continuous_data, CONTINUOUS = su.fetch_continuous_data(job_title=JOB_TITLE)

    if CONTINUOUS: # If old data exists, compare the old and new to extract only the new URLs
        old_urls = list(old_continuous_data["URL"].values)
        new_urls = [i for i in all_scraped_urls if i not in old_urls]
        print(f"{JOB_TITLE}: {len(new_urls)} new adds")
    else: 
        new_urls = all_scraped_urls.copy()
        print(f"{JOB_TITLE}: {len(new_urls)} new adds")

    ## 3: Scrape
    scraping_results = su.scrape_urls(new_urls, driver)

    rows_to_be_added = []       
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

    ## 4: Append the DF-data to csv-file
    new_df_rows.to_csv(
        f"data/ads/{JOB_TITLE}_snapshot_data.csv", 
        header=True, 
        index=False
        )

    if not CONTINUOUS:
        new_df_rows.to_csv(
            f"data/ads/{JOB_TITLE}_continuous_data.csv", 
            mode="a", 
            header=True, 
            index=False
            )
    else:
        new_df_rows.to_csv(
            f"data/ads/{JOB_TITLE}_continuous_data.csv", 
            mode="a", 
            header=False, 
            index=False
            )

    ## 5: Update the qualifications csv-file
    if len(new_df_rows) > 0:
        df, ids = find_qualifications(
            job_title=JOB_TITLE, 
            qualifications_list=QUALIFICATIONS,
            ids = list(new_df_rows["ID"]),
            jobs_dataframe = new_df_rows
            )
        try: 
            _ = pd.read_csv(f"data/qualifications_dfs/{JOB_TITLE}_qualifications.csv") # Check if DF allready exists
            df.to_csv(
                f"data/qualifications_dfs/{JOB_TITLE}_qualifications.csv", 
                mode="a", 
                header=False, 
                index=False
                )
        except:
            df.to_csv(
                f"data/qualifications_dfs/{JOB_TITLE}_qualifications.csv", 
                mode="a", 
                header=True, 
                index=False
                )
