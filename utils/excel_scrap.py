import os
import pandas as pd
from bs4 import BeautifulSoup
import csv
import logging
from settings import OUTPUT_DIR, LOGS_DIR

logger = logging.getLogger(__name__)

def clean_xls_files():
    """
    Converts all XLS files in output folder to CSVs with cleaned data, replacing original files
    """
    output_folder = OUTPUT_DIR
    
    for filename in os.listdir(output_folder):
        if filename.endswith('.xls'):
            file_path = os.path.join(output_folder, filename)
            csv_filename = filename.replace('.xls', '.csv')
            csv_path = os.path.join(output_folder, csv_filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Extract year and month from filename
                year = filename.split('_')[1]
                month = filename.split('_')[2].split('.')[0]
                
                # Parse HTML tables
                soup = BeautifulSoup(html_content, 'html.parser')
                tables = soup.find_all('table')
                
                # Process main table
                main_table_data = []
                main_table = tables[0]
                main_table_data.append([
                    th.get_text(strip=True)
                    .replace('\n', ' ')
                    for th in main_table.find('tr').find_all('th')
                ])
                for row in main_table.find_all('tr')[1:]:
                    main_table_data.append([
                        td.get_text(strip=True) 
                        for td in row.find_all('td')
                    ])
                
                # Process timing table
                timing_table_data = []
                if len(tables) > 1:
                    timing_table = tables[1]
                    timing_table_data.append([
                        th.get_text(strip=True)
                        .replace('\n', ' ')
                        .replace(',', ';')
                        for th in timing_table.find('tr').find_all('th')
                    ])
                    for row in timing_table.find_all('tr')[1:]:
                        timing_table_data.append([
                            td.get_text(strip=True) 
                            for td in row.find_all('td')
                        ])
                
                # Write to CSV with proper formatting
                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                    writer.writerows(main_table_data)
                    
                    if timing_table_data:
                        writer.writerow([])  # Empty row separator
                        writer.writerows(timing_table_data)
                
                # Remove original XLS file
                os.remove(file_path)
                logger.info(f"Converted and replaced {filename} with {csv_filename}")
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}", exc_info=True)

if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(LOGS_DIR, 'excel_processing.log'),
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    clean_xls_files()
