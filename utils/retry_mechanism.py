import logging


logger = logging.getLogger(__name__)
def run_with_retries(func, max_retries=3):
    """
    Runs a function with a specified number of retries in case of failure.
    
    Args:
        func (callable): The function to run.
        max_retries (int): The maximum number of retries. Defaults to 3.
    
    Returns:
        bool: True if the function succeeded, False if it failed after retries.
    """
    for attempt in range(max_retries):
        try:
            func()  # Call the function
            return True  # If successful, return True
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                logger.info("Retrying...")
    return False  # If all attempts fail, return False