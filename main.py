from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


chrome_options = Options()

user_dir = r"C:\Users\olofs\AppData\Local\Google\Chrome\User Data"

chrome_options.add_argument(f"--user-data-dir={user_dir}")


URL = "https://arbetsformedlingen.se/platsbanken/"

service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(options=chrome_options, service=service)



driver.get(URL)

# wait for search window to appear
search_window_id = "search_input"
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, search_window_id)))
input_box = driver.find_element(By.ID, search_window_id)
input_box.clear()
input_box.send_keys("data engineer" + Keys.ENTER)


# Wait for results to load
search_results_cards = "card-container"
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, search_results_cards)))


def click_next():
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

def check_next():
    pages_buttons = driver.find_elements(By.TAG_NAME, "digi-button")
    labels = [i.text for i in pages_buttons]
    if "Nästa" in labels:
        return True
    else:
        return False


job_descriptions = []

def retrieve_urls_from_page():
    links = driver.find_elements(By.TAG_NAME, "pb-feature-search-result-card") # Returns all tags in the result container

    # Must extract the urls and pass a get-request manually
    # Selenium cannot simply loop through tags and keep track of everything
    urls = [link.find_element(By.TAG_NAME, "a").get_attribute('href') for link in links]
    return urls

def scrape_urls(urls):
    
    job_texts = []
    for url in urls:
        driver.get(url)
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "jobb-page")))
        jobb_page = driver.find_element(By.CLASS_NAME, "jobb-page")
        ng_star_class = jobb_page.find_element(By.CLASS_NAME, "ng-star-inserted")
        job_container = ng_star_class.find_element(By.XPATH, ".//div[@class='jobb-container container']")
        job_description = job_container.find_element(By.XPATH, ".//div[@class='section job-description']")
        job_description_text = job_description.text
        job_texts.append(job_description_text)

    # pages_buttons = driver.find_elements(By.TAG_NAME, "digi-button")
    # for button in pages_buttons:
    #     if button.text == "Nästa":
    #         print("button exists")
    #         button.click()
            # time.sleep(10)
        
    return job_texts

stay = True
all_urls = []
while stay:
    urls = retrieve_urls_from_page()
    for url in urls:
        all_urls.append(url)
    # driver.back()

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

job_texts = scrape_urls(all_urls)

python = 0

for job in job_texts:
    if "Python" in job:
        python += 1

print(f"Python efterfrågades i {python} anonser.")











