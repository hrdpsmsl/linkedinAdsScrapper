import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import pandas as pd
import time
import re

# Function to set up Selenium WebDriver
def setup_driverss():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    #service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),options=chrome_options)
    return driver

@st.cache_resource
def setup_driver():
    return webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),options=options)
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--headless")
driver = get_driver()


# Function to scrape ad data
def scrape_ad_data(driver, url):
    driver.get(url)
    time.sleep(3)  # Allow time for the page to load
    
    ad_data = {"url": url, "body_text": "", "company_name": "", "image_url": "", "paid_by": ""}
    
    try:
        body_text_element = driver.find_element(By.CSS_SELECTOR, "p.commentary__content")
        body_text = body_text_element.text
        cleaned_text = re.sub(r'\s+', ' ', body_text.strip())
        ad_data["body_text"] = cleaned_text
    except:
        ad_data["body_text"] = "Not Found"
    
    try:
        company_name_element = driver.find_element(By.XPATH, "/html/body/div/main/section/div/div/div[1]/div[1]/div/div/div[1]/div/div/a")
        ad_data["company_name"] = company_name_element.text
    except:
        ad_data["company_name"] = "Not Found"
    
    try:
        image_element = driver.find_element(By.CSS_SELECTOR, "img.ad-preview__dynamic-dimensions-image")
        ad_data["image_url"] = image_element.get_attribute("src")
    except:
        ad_data["image_url"] = "Not Found"
    
    try:
        paid_by_element = driver.find_element(By.CSS_SELECTOR, "p.about-ad__paying-entity")
        ad_data["paid_by"] = paid_by_element.text
    except:
        ad_data["paid_by"] = "Not Found"
    
    return ad_data

# Function to scrape all ads
def scrape_ads(company, keyword, country, start_date, end_date):
    url = f"https://www.linkedin.com/ad-library/search?accountOwner={company.replace(' ', '+')}&keyword={keyword.replace(' ', '+')}&countries={country}&dateOption=custom-date-range&startdate={start_date}&enddate={end_date}"
    print(url)
    driver = setup_driver()
    driver.get(url)
    time.sleep(5)  # Allow time for the page to load
    
    ads = driver.find_elements(By.CLASS_NAME, "search-result-item")
    ad_links = []

    for ad in ads:
        try:
            anchor_element = ad.find_element(By.CSS_SELECTOR, "div.flex.justify-center a")
            ad_links.append(anchor_element.get_attribute("href"))
        except Exception:
            continue
    st.info("Found " + str(len(ad_links)) + " Ads for " + str(company)+ ". Please wait!")        
    all_ads_data = []
    for link in ad_links:
        ad_info = scrape_ad_data(driver, link)
        all_ads_data.append(ad_info)
    
    driver.quit()
    return all_ads_data

# Streamlit UI
st.title("LinkedIn Ad Scraper")

# Input fields
company = st.text_input("Company Name", "Startup Mahakumbh")
keyword = st.text_input("Keyword", "startup")
country = st.text_input("Country Code (e.g., IN, US)", "IN")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")

# Scrape button
if st.button("Scrape Ads"):
    if start_date and end_date:
        st.info("Scraping LinkedIn Ads... Please wait.")
        ads_data = scrape_ads(company, keyword, country,start_date, end_date)

        if ads_data:
            df = pd.DataFrame(ads_data)
            st.success(f"Scraped {len(df)} ads successfully!")
            st.dataframe(df)  # Show data in Streamlit

            # Download button for Excel file
            excel_file = "linkedin_ads.xlsx"
            df.to_excel(excel_file, index=False)
            with open(excel_file, "rb") as f:
                st.download_button("Download Excel File", f, file_name="linkedin_ads.xlsx", mime="application/vnd.ms-excel")
        else:
            st.warning("No ads found!")
    else:
        st.error("Please select a valid date range.")

