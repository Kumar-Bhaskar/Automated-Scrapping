from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import csv
import os 
import shutil
from bs4 import BeautifulSoup
import logging
from settings import (SETTLEMENT_DIR, LOGS_DIR, OUTPUT_DIR, ARCHIVE_DIR,
                     CHROME_OPTIONS, HEADLESS_MODE, WAIT_TIMEOUT, BASE_URL, PDF_URL)
from selenium.webdriver.common.action_chains import ActionChains

# Import functions from helper modules
from utils.excel_scrap import clean_xls_files
from utils.clean_csv import clean_csv_date_columns
from utils.validation import compare_folders
from utils.pdf_extraction import load_pdf
from utils.retry_mechanism import run_with_retries

# Initialize logger at the top
logger = logging.getLogger(__name__)

def scrape_table_data(driver):
    """
    Scrapes table data from a web page using Selenium and BeautifulSoup.
    Args:
        driver: Selenium WebDriver instance used to interact with the webpage
    Returns:
        list: A list of lists containing table data, including headers from both main and timing tables (if present)
    Raises:
        TimeoutException: If the main table element is not found within 10 seconds
    """

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_dgSettle"))
    )
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    main_table = soup.find('table', {'id': 'ContentPlaceHolder1_dgSettle'})
    data = []
    
    # Get headers
    headers = [th.get_text(strip=True) for th in main_table.find('tr').find_all('th')]
    data.append(headers)
    
    # Get rows
    for row in main_table.find_all('tr')[1:]: 
        cols = [td.get_text(strip=True) for td in row.find_all('td')]
        data.append(cols)
    
    timing_table = soup.find('table', {'id': 'ContentPlaceHolder1_dg1'})
    if timing_table:
        timing_headers = [th.get_text(strip=True) for th in timing_table.find('tr').find_all('th')]
        data.append([])  
        data.append(timing_headers)
        
        for row in timing_table.find_all('tr')[1:]:  # Skip header row
            cols = [td.get_text(strip=True) for td in row.find_all('td')]
            data.append(cols)
    
    return data

def save_to_csv(data, filename='settlement_calendar.csv'):
    """
    Saves the scraped data to a CSV file.
    Args:
        data (list): A list of lists containing the data to be saved.
        filename (str): The name of the file to save the data to. Defaults to 'settlement_calendar.csv'.
    Returns:
        None
    """
    folder = SETTLEMENT_DIR
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)
    logger.info(f"Data saved to {filepath}")

def download_xlsx_file(driver, year, month):
    """
    Downloads the XLSX file by clicking the download icon and saves it to the output directory.
    Args:
        driver: Selenium WebDriver instance
        year (int): The year for the filename
        month (int): The month for the filename
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Configure Chrome to automatically download files without dialog
        driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {
            'cmd': 'Page.setDownloadBehavior',
            'params': {
                'behavior': 'allow',
                'downloadPath': os.path.abspath(OUTPUT_DIR)
            }
        }
        driver.execute("send_command", params)
        
        # Find and click the download link
        download_link = driver.find_element(By.ID, "ContentPlaceHolder1_imgDownload")
        download_link.click()
        
        # Wait for download to complete
        time.sleep(WAIT_TIMEOUT)
        
        # Define filenames
        original_filename = f"SettlementCalendar{month:02d}{year}.xls"
        new_filename = f"settlement_{year}_{month:02d}.xls"
        original_path = os.path.join('output', original_filename)
        new_path = os.path.join('output', new_filename)
        
        # Rename the downloaded file
        if os.path.exists(original_path):
            os.rename(original_path, new_path)
            logger.info(f"Successfully saved as {new_filename}")
        else:
            logger.warning(f"Expected file {original_filename} not found")
        
        logger.info(f"XLSX file downloaded for {year}-{month:02d}")
        
    except Exception as e:
        logger.error(f"Error downloading XLSX file: {str(e)}", exc_info=True)


def open_site_in_incognito(url, year=datetime.now().year, month=datetime.now().month):
    """
    Opens a specified URL in an incognito Chrome browser window, selects the settlement month and year,
    scrapes the table data, and saves it to CSV files for the specified month and the next month.
    Args:
        url (str): The URL of the website to scrape.
        year (int): The year for which to scrape the data.
        month (str): The month for which to scrape the data (1-12).
    Raises:
        ValueError: If the month is not between 1 and 12.
    """
    month_int = int(month)
    if not (1 <= month_int <= 12):
        raise ValueError(f"Invalid month '{month}'. Please enter a value between 1 and 12.")
    if month_int == 12:
        month_year_pairs = [(month_int, year), (1, year + 1)]
    else:
        month_year_pairs = [(month_int, year), (month_int + 1, year)]

    options = Options()
    options.add_argument("--incognito")
    options.add_argument("--headless=new" if HEADLESS_MODE else "--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Setting desired resolution
    options.add_argument("window-size=1920,1080")  
    # Add these new preferences for automatic downloads
    options.add_experimental_option("prefs", CHROME_OPTIONS)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Equity T + 1
        settlement_dropdown = Select(driver.find_element(By.ID, "ContentPlaceHolder1_ddlsetllementcal"))
        settlement_dropdown.select_by_value("0")

        for m, y in month_year_pairs:
            # Select year
            year_dropdown = Select(driver.find_element(By.ID, "ContentPlaceHolder1_ddlYear"))
            year_dropdown.select_by_value(str(y))

            # Select month
            month_dropdown = Select(driver.find_element(By.ID, "ContentPlaceHolder1_ddlMonth"))
            month_dropdown.select_by_value(str(m).zfill(2))

            # Click Go
            go_button = driver.find_element(By.ID, "ContentPlaceHolder1_btnGo")

            # Wait until the button is clickable
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_btnGo")))

            # Scroll to the button and click
            driver.execute_script("arguments[0].scrollIntoView();", go_button)
            go_button.click()
            time.sleep(5)

            # Scrape and save
            try:
                table_data = scrape_table_data(driver)

                # Check if table_data is empty or if the expected table is not found
                if not table_data or len(table_data) <= 1:
                    logger.warning(f"No data available for {y}-{str(m).zfill(2)}. Skipping download.")
                    continue

                download_xlsx_file(driver, y, m)
                save_to_csv(table_data, filename=f'settlement_{y}_{str(m).zfill(2)}.csv')

            except Exception as e:
                logger.error(f"Error while scraping data for {y}-{str(m).zfill(2)}: {str(e)}", exc_info=True)
                continue
    finally:
        driver.quit()

if __name__ == "__main__":
    try:
        # Create logs directory
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            filename=os.path.join(LOGS_DIR, 'scrape.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='a'
        )
        
        logger.info("Starting scraping process...")
        URL = BASE_URL
        pdf_url = PDF_URL
        pdf_file_name = pdf_url.split("/")[-1].split(".")[0]
        # year = YEAR
        # month = MONTH
        
        # Open the site and download the XLS file
        # success = run_with_retries(lambda: open_site_in_incognito(URL, year, month))
        success = run_with_retries(lambda: open_site_in_incognito(URL))
        if success:
            # Process XLS files to CSV
            logger.info("\nProcessing XLS files...")
            clean_xls_files()
            
            # Clean CSV files
            logger.info("\nCleaning CSV files...")
            clean_csv_date_columns(folder=SETTLEMENT_DIR)
            
            # Validate against settlement folder
            logger.info("\nValidating files...")
            mismatch_count = compare_folders(output_folder=OUTPUT_DIR, settlement_folder=SETTLEMENT_DIR)

            logger.info("\n Starting PDF extraction")
            pdf_file = load_pdf(pdf_url,pdf_file_name)
            if pdf_file:
                logger.info("Extraction Complete")
            else:
                logger.error("PDF Extraction Failed")

            if mismatch_count == 0:
                logger.info("\nAll files match successfully!")
                os.makedirs(ARCHIVE_DIR, exist_ok=True)
                shutil.move(SETTLEMENT_DIR, os.path.join(ARCHIVE_DIR, "settlement"))
                shutil.move(OUTPUT_DIR, os.path.join(ARCHIVE_DIR, "output"))
            else:
                logger.error(f"\n{mismatch_count} files have mismatches. Please check the validation report.")
        else:
            logger.error("All attempts to run the scraping process failed.")
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}", exc_info=True)