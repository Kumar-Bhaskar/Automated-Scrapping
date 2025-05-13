# Automated Scraping Project

## Overview

This project automates the scraping of settlement calendar data from the BSE India website using Selenium and BeautifulSoup. The scraped data is processed and saved in CSV format for further analysis. The project also includes functionality for cleaning and validating the data.

## Features

- Scrapes settlement calendar data from the BSE India website.
- Downloads XLSX files and converts them to CSV format.
- Cleans date columns in CSV files.
- Validates the output against expected settlement files.
- Scrapes the pdf data for the NSE India
- Logs all operations for debugging and tracking purposes.

## Requirements

- Python 3.x
- Selenium
- BeautifulSoup
- Pandas
- WebDriver Manager
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have the necessary directories set up in the `settings.py` file:
   - `SETTLEMENT_DIR`: Directory for storing settlement CSV files.
   - `OUTPUT_DIR`: Directory for storing downloaded XLSX files.
   - `LOGS_DIR`: Directory for storing log files.
   - `READY_DIR`: Directory for processed files ready for loading.
   - `PDF_OUTBOUND_FOLDER` : Directory for processed files of NSE

## Usage

1. Open the `main.py` file and set the desired year and month for scraping (optional):
   ```python
   # YEAR = 2025 
   # MONTH = "4"
   ```

2. Run the script:
   ```bash
   python main.py
   ```

3. The script will:
   - Open the specified URL in an incognito Chrome browser.
   - Scrape the settlement data and save it to CSV files.
   - Clean the CSV files by removing anomalies in date columns.
   - Validate the output against the expected settlement files.
   - Scrapes the pdf data for the NSE India

## Logging

All operations are logged in the `logs` directory. You can check `scrape.log` for scraping operations and `validation.log` for validation results.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any bugs or feature requests.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Acknowledgments

- [Selenium](https://www.selenium.dev/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Pandas](https://pandas.pydata.org/)