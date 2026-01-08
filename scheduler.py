import schedule
import time
import logging
from scraper import main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def run_job():
    """
    Execute the scraper job with error handling.
    """
    try:
        logger.info("Starting scheduled scrape...")
        
        # Call the scraper main function
        main()
        
        logger.info("Scrape complete. Next run in 15 minutes.")
        
    except Exception as e:
        logger.error(f"Scrape failed with error: {e}")
        logger.error("Continuing scheduler - will try again in 15 minutes.")

def main_scheduler():
    """
    Main scheduler function that sets up and runs the job scheduling.
    """
    logger.info("Disney World Wait Time Scheduler starting...")
    
    # Schedule the job to run every 15 minutes
    schedule.every(15).minutes.do(run_job)
    
    logger.info("Scheduler configured. Running job immediately, then every 15 minutes.")
    
    # Run the job immediately once
    run_job()
    
    # Run the infinite loop to keep the scheduler alive
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main_scheduler()
