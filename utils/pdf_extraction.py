import pdfplumber
import pandas as pd
import requests 
import io 
import os
from datetime import datetime
import logging
from settings import (PDF_URL,PDF_OUTBOUND_FOLDER,PDF_SETTLEMENT_COL,PDF_SETTLEMENT_DATE_COL)

logger = logging.getLogger(__name__)

def extract_pdf_data(pdf_file, pdf_file_name, outbound=PDF_OUTBOUND_FOLDER):

    folder_path = f"{PDF_OUTBOUND_FOLDER}/{pdf_file_name}"
    os.makedirs(folder_path, exist_ok=True)
    try:
        with pdfplumber.open(pdf_file) as pdf:
            logging.info("Initializing PDF extraction...")
            for page_index, page in enumerate(pdf.pages):
                if page_index == 0:  # Skip the first page
                    continue

                # Extract the text to check if this is Annexure A (which has different structure)
                text = page.extract_text()
                is_annexure_a = "Annexure 'A'" in text
                
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if len(table) < 4:
                            continue  # Skip if not enough rows for header + data

                        # Clean header: use 3rd row, replace '\n' with space, handle None
                        raw_header = table[2]
                        header = [(col or '').replace('\n', ' ').strip() for col in raw_header]
                        
                        # For Annexure A, we need to handle the extra columns
                        if is_annexure_a:
                            header = [item for item in header if item != '']
                            table[-1][0], table[-1][1] = table[-1][1], None

                        # Normalize rows to header length
                        data_rows = []
                        for row in table[3:]:
                            if not any(row):
                                continue
                                
                            # For Annexure A, clean up the row structure
                            if is_annexure_a:
        
                                clean_row = [row[0]]  # Start with 'M'
                                rest = [x for x in row[1:] if x and str(x).strip()]
                                clean_row.extend(rest[:5])  # Take next 5 elements
                                row = clean_row
                            
            
                            row = row[:len(header)]
                            data_rows.append(row)

                        df = pd.DataFrame(data_rows, columns=header)
                        
                        # For Annexure A, drop any empty columns
                        if is_annexure_a:
                            df = df.dropna(axis=1, how='all')
                    

                        last_value = str(df.iloc[-1, -1]).strip()
                        exempt = str(df.iloc[-1, 0]).strip()

                        # If the last value is blank, drop the last row
                        if last_value is None or last_value == 'None':
                            df = df.iloc[:-1]
                            with open(f"{PDF_OUTBOUND_FOLDER}/{pdf_file_name}/{pdf_file_name}_{table[0][0]}_exempt.txt", 'w') as file:
                                file.write(exempt)

                        # Extract settlement number and date from the first record
                        settlement_no_cols = PDF_SETTLEMENT_COL
                        settlement_date_cols = PDF_SETTLEMENT_DATE_COL
                        settlement_no_col = next((col for col in settlement_no_cols if col in df.columns), None)
                        settlement_date_col = next((col for col in settlement_date_cols if col in df.columns), None)

                        if settlement_no_col and settlement_date_col:
                            first_row = df.iloc[0]
                            settlement_no = str(first_row[settlement_no_col])
                            original_date = str(first_row[settlement_date_col])
                            try:
                                date_obj = datetime.strptime(original_date, "%d-%b-%y")
                                formatted_date = date_obj.strftime("%d-%m-%Y")
                            except ValueError:
                                formatted_date = original_date  # fallback if parsing fails
                            # annexure_name = str(table[0][0])
                            settlement_type = str(first_row[df.columns[0]])
                            csv_filename = f"{PDF_OUTBOUND_FOLDER}/{pdf_file_name}/publish_settlement_number_edis nse_cm '{settlement_no}' '{formatted_date}' '{settlement_type}'.csv"
                            
                        else:
                            # fallback to old naming if columns not found
                            csv_filename = f"{PDF_OUTBOUND_FOLDER}/{pdf_file_name}/{pdf_file_name}{table[0][0]}{table[1][0]}.csv"

                        df.to_csv(csv_filename, index=False)
    except Exception as e:
        logging.error(f"Failed PDF extraction! Error : {e}")

def load_pdf(pdf_url,pdf_file_name):

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(headers=headers, url=pdf_url)
        pdf_file = io.BytesIO(response.content) 
        logging.info("Loading PDF")
        extract_pdf_data(pdf_file, pdf_file_name) 
        extract_first_record_settlement_info(PDF_OUTBOUND_FOLDER)
        return True
    except Exception as e:
        logger.error(f"Failed to load PDF : {e}")


def extract_first_record_settlement_info(folder_path):
    # Possible column names for each field
    settlement_no_cols = PDF_SETTLEMENT_COL
    settlement_date_cols = PDF_SETTLEMENT_DATE_COL
    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    df = pd.read_csv(file_path)
                    if df.shape[0] == 0:
                        continue  # skip empty files

                    # Find the correct columns
                    settlement_no_col = next((col for col in settlement_no_cols if col in df.columns), None)
                    settlement_date_col = next((col for col in settlement_date_cols if col in df.columns), None)

                    if settlement_no_col and settlement_date_col:
                        first_row = df.iloc[0]
                        # Format the date
                        original_date = str(first_row[settlement_date_col])
                        try:
                            formatted_date = datetime.strptime(original_date, "%d-%b-%y").strftime("%d-%m-%y")
                        except ValueError:
                            formatted_date = original_date  # fallback if parsing fails
                    else:
                        logger.error(f"\nFile: {file} - Required columns not found.")
    except Exception as e:
        logger.error(f"Error extracting information columns {e}")


if __name__ == "__main__":  
    pdf_url = PDF_URL
    pdf_file_name = pdf_url.split("/")[-1].split(".")[0]
    pdf_file = load_pdf(pdf_url,pdf_file_name)
    if pdf_file:
        logger.info("Extraction Complete")
    else:
        logger.error("PDF Extraction Failed")
