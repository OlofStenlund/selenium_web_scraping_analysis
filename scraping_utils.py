import locale
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def establish_driver(user_dir: str) -> webdriver.Chrome:
    """
    user_dir: directory leading to user info for Chrome
    Returns a chrome webdriver
    """
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={user_dir}")
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(options=chrome_options, service=service)
    return driver


def check_next(driver) -> bool:
    """
    Checks if the 'Nästa' button exists.
    driver: webdriver
    """
    pages_buttons = driver.find_elements(By.TAG_NAME, "digi-button")
    labels = [i.text for i in pages_buttons]
    if "Nästa" in labels:
        return True
    else:
        return False


def retrieve_urls_from_page(driver) -> list[str]:
    """
    When a page with adds has loaded, this function extracts the URLs and returns a list.
    driver: webdriver
    """
    links = driver.find_elements(By.TAG_NAME, "pb-feature-search-result-card") # Returns all tags in the result container

    # Must extract the urls and pass a get-request manually
    # Selenium cannot simply loop through tags and keep track of everything
    urls = []
    for link in links:
        urls.append(link.find_element(By.TAG_NAME, "a").get_attribute('href'))
    return urls

def parse_dates(date_text: str) -> pd.Timestamp:
    """
    Parse string into a pd.Timestamp object. The string found on the website
    has the form '11 september 2024, kl. 09:45', and thus this function reflects that.
    date_text: str 
    """
    _date, _time = date_text.split(sep=",")
    _time = _time.split(sep="kl. ")[1]
    _time = _time.replace(".", ":")
    locale.setlocale(locale.LC_TIME, "Swedish_Sweden")
    date_object = datetime.strptime(_date, "%d %B %Y").date()
    time_object = datetime.strptime(_time, "%H:%M").time()
    publish_datetime = pd.to_datetime(datetime.combine(date_object, time_object))
    return publish_datetime


def scrape_urls(urls: list, driver) -> list[dict]:
    """
    Looks for the job description text and returns a list with dicts.
    urls: list
    driver: webdriver
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

def fetch_continuous_data(job_title: str) -> tuple[pd.DataFrame, bool]:
    """
    All scraped data is stored in a 'continuous'-table, while the most recently scraped
    ads are stored in a 'snapshot'-table as well. This function fetches the continuous table is it exists.
    job_title: str, the title to look for.
    """
    try:
        old_continuous_data = pd.read_csv(f"data/ads/{job_title}_continuous_data.csv")
        old_continuous_data = old_continuous_data.sort_values(by="date", ascending=False)
        CONTINUOUS = True
        return old_continuous_data, CONTINUOUS
    except:
        CONTINUOUS = False
        return False, CONTINUOUS

# def fetch_old_snapshot(search_term: str) -> tuple[bool, pd.DataFrame]:
#     """
#     All scraped data is stored in a 'continuous'-table, while the most recently scraped
#     ads are stored in a 'snapshot'-table as well. This function fetches the most recent snapshot table, 
#     if it exists.
#     search_term: str, the title to look for.
#     """
#     try:
#         old_snapshot_data = pd.read_csv(f"{search_term}_snapshot_data.csv")
#         SNAPSHOT = True
#         return old_snapshot_data, SNAPSHOT
#     except:
#         SNAPSHOT = False
#         return False, False