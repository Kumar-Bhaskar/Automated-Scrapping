# New environment configuration file
import os

# Directory configurations
BASE_DIR = os.path.abspath(r'C:\Work\Automated Scrapping')
SETTLEMENT_DIR = os.path.join(BASE_DIR, 'settlement')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
READY_DIR = os.path.join(BASE_DIR, 'BSE')
ARCHIVE_DIR = os.path.join(BASE_DIR,'archive')

# Chrome configuration
CHROME_OPTIONS = {
    'download.default_directory': OUTPUT_DIR,
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    'safebrowsing.enabled': True
}

# Browser settings
HEADLESS_MODE = True
WAIT_TIMEOUT = 10 

# Variables Settings
BASE_URL = "https://www.bseindia.com/markets/equity/EQReports/setcal.aspx"
PDF_URL = "https://nsearchives.nseindia.com/content/circulars/CMPT66953.pdf"
PDF_OUTBOUND_FOLDER = "NSE"
PDF_SETTLEMENT_COL = ['Settlement No.', 'Sett No']
PDF_SETTLEMENT_DATE_COL = ['Settlement Date', 'Daily Settlement Date', 'Obligation Date']
SETTLEMENT_COLUMN = 0
PAY_IN_OUT_COLUMN = 4

