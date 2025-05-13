import os
import csv
from utils.clean_csv import convert_date_format
import logging
from settings import READY_DIR, LOGS_DIR, OUTPUT_DIR, SETTLEMENT_DIR

logger = logging.getLogger(__name__)

def compare_folders(output_folder=OUTPUT_DIR, settlement_folder=SETTLEMENT_DIR):
    """
    Compares CSV files and handles matched/mismatched files
    Returns count of mismatched files
    """
    mismatches = 0
    matches = 0
    missing_files = 0
    matched_files = []
    mismatched_files = []

    # Get all settlement files
    settlement_files = {f for f in os.listdir(settlement_folder) if f.endswith('.csv')}
    
    # Get all output files
    output_files = {f for f in os.listdir(output_folder) if f.endswith('.csv')}
    
    # Files present in both folders
    common_files = settlement_files & output_files
    
    # Compare common files
    for filename in sorted(common_files):
        settlement_path = os.path.join(settlement_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        with open(settlement_path, 'r', encoding='utf-8') as f1, \
             open(output_path, 'r', encoding='utf-8') as f2:
            
            reader1 = csv.reader(f1)
            reader2 = csv.reader(f2)
            
            settlement_data = list(reader1)
            output_data = list(reader2)
            
            if settlement_data == output_data:
                logger.info(f"Exact match: {filename}")
                matches += 1
                matched_files.append(filename)
                
                # Convert and save to ready_to_load
                date_cols = convert_date_format(filename, settlement_folder)
                logger.debug(f"Converted dates in {filename} (columns: {', '.join(date_cols)})")
                
            else:
                logger.error(f"Mismatch found: {filename}")
                mismatches += 1
                mismatched_files.append(filename)
                
                max_diffs = 5
                diff_count = 0
                total_diffs = 0
                
                # Compare line by line
                for i, (line1, line2) in enumerate(zip(settlement_data, output_data)):
                    if line1 != line2:
                        total_diffs += 1
                        if diff_count < max_diffs:
                            logger.debug(f"\nDifference at line {i+1}:")
                            # Find differing columns
                            diffs = []
                            for col, (val1, val2) in enumerate(zip(line1, line2)):
                                if val1 != val2:
                                    diffs.append((col+1, val1, val2))
                            
                            # Print line comparison
                            logger.debug(f"Settlement >> {line1}")
                            logger.debug(f"Output     << {line2}")
                            
                            # Print column differences
                            if diffs:
                                logger.debug("Differing columns:")
                                for col, v1, v2 in diffs:
                                    logger.debug(f"    Column {col}: '{v1}' vs '{v2}'")
                            
                            diff_count += 1
                
                # Handle different line counts
                len_diff = len(settlement_data) - len(output_data)
                if len_diff != 0:
                    logger.debug(f"\nLine count difference: {len(settlement_data)} vs {len(output_data)} lines")
                    if len_diff > 0:
                        extra_lines = settlement_data[len(output_data):]
                        logger.debug(f"Extra lines in settlement file: {len(extra_lines)}")
                    else:
                        extra_lines = output_data[len(settlement_data):]
                        logger.debug(f"Extra lines in output file: {abs(len_diff)}")
                
                # Show remaining diffs count
                if total_diffs > max_diffs:
                    logger.debug(f"\n... and {total_diffs - max_diffs} more differences")
                
                logger.debug(f"Total differences found: {total_diffs}")

    # Files only in settlement
    only_in_settlement = settlement_files - output_files
    if only_in_settlement:
        logger.warning("\n* Files only in settlement folder:")
        for f in sorted(only_in_settlement):
            logger.warning(f"  - {f}")
        missing_files += len(only_in_settlement)
        mismatched_files.extend(only_in_settlement)

    # Files only in output
    only_in_output = output_files - settlement_files
    if only_in_output:
        logger.warning("\n* Files only in output folder:")
        for f in sorted(only_in_output):
            logger.warning(f"  - {f}")
        missing_files += len(only_in_output)

    # Modified summary
    logger.info(f"\nValidation Complete:")
    logger.info(f"Matching files: {matches}")
    logger.warning(f"Mismatched files: {mismatches}")
    logger.warning(f"Unique files: {missing_files}")
    logger.info(f"\nValidated files available in: {os.path.abspath(READY_DIR)}")
    
    # Process matched files
    for filename in matched_files:
        date_cols = convert_date_format(filename, settlement_folder)
        logger.debug(f"Converted dates in {filename} (columns: {', '.join(date_cols)})" if date_cols else f"No dates found in {filename}")

    return mismatches

if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(LOGS_DIR, 'validation.log'),
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    compare_folders()
