import os
import csv
import shutil
from datetime import datetime
import time
import logging
from settings import SETTLEMENT_DIR, READY_DIR, SETTLEMENT_COLUMN, PAY_IN_OUT_COLUMN
import re


logger = logging.getLogger(__name__)

def clean_csv_date_columns(folder='settlement'):
    """
    Cleans date columns in CSV files by removing '@' suffix and reports anomalies
    """
    logger.info(f"Cleaning CSV files in folder: {folder}")
    
    for filename in os.listdir(folder):
        if filename.endswith('.csv'):
            file_path = os.path.join(folder, filename)
            cleaned_rows = []
            anomaly_columns = set()
            
            logger.info(f"Processing file: {filename}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                cleaned_rows.append(headers)
                
                for row in reader:
                    cleaned_row = []
                    for idx, value in enumerate(row):
                        # Clean date values ending with '@'
                        if value.endswith('@'):
                            cleaned_value = value.rstrip('@')
                            anomaly_columns.add(headers[idx])
                        else:
                            cleaned_value = value
                        
                        # Validate date format (optional)
                        try:
                            datetime.strptime(cleaned_value, '%d/%m/%Y')
                        except ValueError:
                            pass  # Not a date field or already cleaned
                            
                        cleaned_row.append(cleaned_value)
                    
                    cleaned_rows.append(cleaned_row)
            
            # Log the number of rows processed
            logger.info(f"Total rows processed (including header): {len(cleaned_rows)}")
            
            # Write cleaned data back to file
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(cleaned_rows)
            
            # Print anomalies report
            if anomaly_columns:
                logger.info(f"Cleaned {filename} - Anomalies found in columns:")
                for col in anomaly_columns:
                    logger.debug(f"Found anomaly in column: {col}")
            else:
                logger.info(f"Processed {filename} - No anomalies found")

def convert_date_format(filename, source_folder=SETTLEMENT_DIR, dest_folder=READY_DIR):
    """Converts dates and saves to ready_to_load folder with a new naming format."""
    os.makedirs(dest_folder, exist_ok=True)
    
    # Define the source path for the original file
    source_path = os.path.join(source_folder, filename)
    
    # Read the original file to extract the first row for naming
    with open(source_path, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        headers = next(reader)
        first_row = next(reader)

        # Extract the required values
        settlement_no = first_row[SETTLEMENT_COLUMN]
        pay_in_out = first_row[PAY_IN_OUT_COLUMN]

        # Remove any prefix consisting of letters followed by a hyphen
        settlement_no = re.sub(r'^[A-Za-z]+-', '', settlement_no)  # Remove prefix like DR- or MJ-

        # Sanitize the filename to remove invalid characters
        settlement_no = settlement_no.replace("'", "").replace("/", "-")
        pay_in_out = pay_in_out.replace("'", "").replace("/", "-")

        # Format the new filename
        new_filename = f"publish_settlement_number_edis bse_cm '{settlement_no}' '{pay_in_out}'.csv"
        dest_path = os.path.join(dest_folder, new_filename)

    date_columns = set()
    
    # Now, process the file to convert date formats
    with open(source_path, 'r', encoding='utf-8') as infile, \
         open(dest_path, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        writer.writerow(headers)

        for row in reader:
            modified_row = []
            for idx, value in enumerate(row):
                try:
                    date_obj = datetime.strptime(value, '%d/%m/%Y')
                    modified_value = date_obj.strftime('%d-%m-%Y')
                    date_columns.add(headers[idx])
                except ValueError:
                    modified_value = value
                modified_row.append(modified_value)
            
            if modified_row != headers:
                writer.writerow(modified_row)

    logger.debug(f"Converted date columns: {', '.join(date_columns)}" if date_columns else "No date columns found")
    return date_columns
