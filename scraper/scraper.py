"""
Gmail Inbox Scraper using Playwright
Extracts email metadata (sender, subject, timestamp) and stores in PostgreSQL
Runs once with manual login - does not run continuously
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from datetime import datetime
import time
import re
from database import create_table, insert_emails_batch, get_email_count

# Configuration
GMAIL_URL = "https://mail.google.com/mail/u/0/#inbox"
LOGIN_WAIT_TIME = 180  # seconds to wait for manual login (increased to 3 minutes)
MAX_SCROLL_ATTEMPTS = 20  # Maximum number of scrolls to load emails


def parse_timestamp(timestamp_text):
    """
    Parse Gmail timestamp text to datetime object
    Handles various Gmail timestamp formats:
    - "12:30 PM" (today)
    - "Jan 15" (this year)
    - "1/15/24" (specific date)
    
    Args:
        timestamp_text (str): Raw timestamp from Gmail
    
    Returns:
        datetime: Parsed datetime object
    """
    timestamp_text = timestamp_text.strip()
    current_year = datetime.now().year
    
    try:
        # Format: "12:30 PM" or "12:30 AM" (today)
        if "AM" in timestamp_text or "PM" in timestamp_text:
            time_obj = datetime.strptime(timestamp_text, "%I:%M %p")
            return datetime.now().replace(
                hour=time_obj.hour,
                minute=time_obj.minute,
                second=0,
                microsecond=0
            )
        
        # Format: "Jan 15" or "Feb 3" (this year)
        elif len(timestamp_text.split()) == 2 and timestamp_text.split()[0].isalpha():
            return datetime.strptime(f"{timestamp_text} {current_year}", "%b %d %Y")
        
        # Format: "1/15/24" or "12/25/23"
        elif "/" in timestamp_text:
            # Handle 2-digit year
            parts = timestamp_text.split("/")
            if len(parts) == 3 and len(parts[2]) == 2:
                year = int(parts[2])
                # Assume 20xx for years 00-99
                full_year = 2000 + year
                return datetime.strptime(f"{parts[0]}/{parts[1]}/{full_year}", "%m/%d/%Y")
            else:
                return datetime.strptime(timestamp_text, "%m/%d/%Y")
        
        # Default: try ISO format
        else:
            return datetime.fromisoformat(timestamp_text)
            
    except Exception as e:
        print(f"Warning: Could not parse timestamp '{timestamp_text}': {e}")
        # Return current time as fallback
        return datetime.now()


def extract_email_data(page):
    """
    Extract email metadata from the Gmail inbox page
    
    Args:
        page: Playwright page object
    
    Returns:
        list: List of tuples (sender, subject, timestamp)
    """
    emails = []
    
    try:
        # Wait for email rows to load
        page.wait_for_selector('tr.zA', timeout=10000)
        
        # Get all email rows
        email_rows = page.query_selector_all('tr.zA')
        print(f"Found {len(email_rows)} email rows")
        
        for row in email_rows:
            try:
                # Extract sender - look for the sender name/email
                sender_elem = row.query_selector('span[email]')
                if sender_elem:
                    sender = sender_elem.get_attribute('email')
                else:
                    # Fallback: get sender name from the row
                    sender_name_elem = row.query_selector('td.yX.xY span')
                    sender = sender_name_elem.inner_text() if sender_name_elem else "Unknown"
                
                # Extract subject
                subject_elem = row.query_selector('span.bog')
                subject = subject_elem.inner_text() if subject_elem else "(No Subject)"
                
                # Extract timestamp
                timestamp_elem = row.query_selector('td.xW.xY span')
                timestamp_text = timestamp_elem.get_attribute('title') or timestamp_elem.inner_text()
                timestamp = parse_timestamp(timestamp_text)
                
                # Add to list
                emails.append((sender, subject, timestamp))
                
            except Exception as e:
                print(f"Error extracting email row: {e}")
                continue
        
    except Exception as e:
        print(f"Error extracting emails: {e}")
    
    return emails


def scroll_to_load_more(page, max_scrolls=MAX_SCROLL_ATTEMPTS):
    """
    Scroll down to load more emails in Gmail
    
    Args:
        page: Playwright page object
        max_scrolls: Maximum number of scroll attempts
    
    Returns:
        int: Total number of emails loaded
    """
    print("Scrolling to load more emails...")
    
    previous_count = 0
    scroll_count = 0
    
    while scroll_count < max_scrolls:
        # Get current email count
        current_count = len(page.query_selector_all('tr.zA'))
        
        # If no new emails loaded, we've reached the end
        if current_count == previous_count:
            print(f"No more emails to load (total: {current_count})")
            break
        
        previous_count = current_count
        scroll_count += 1
        
        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        # Wait for new emails to load
        time.sleep(2)
        
        print(f"Scroll {scroll_count}/{max_scrolls}: Loaded {current_count} emails")
    
    return previous_count


def scrape_gmail():
    """
    Main scraping function
    Launches browser, waits for manual login, extracts emails, and stores in database
    """
    print("=" * 60)
    print("Gmail Inbox Scraper")
    print("=" * 60)
    
    # Create database table if it doesn't exist
    print("\n[1/5] Setting up database...")
    create_table()
    
    print("\n[2/5] Launching browser...")
    with sync_playwright() as p:
        # Launch browser in headed mode with arguments to bypass automation detection
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        # Create context with additional settings to appear like a regular browser
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Remove webdriver property
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        try:
            # Navigate to Gmail
            print(f"\n[3/5] Navigating to Gmail...")
            page.goto(GMAIL_URL)
            
            # Wait for manual login
            print(f"\n⚠️  MANUAL LOGIN REQUIRED ⚠️")
            print(f"Please log in to your Gmail account in the browser window.")
            print(f"Waiting up to {LOGIN_WAIT_TIME} seconds for login...")
            print(f"The scraper will continue automatically once the inbox loads.\n")
            
            # Wait for inbox to load (indicated by presence of email rows)
            try:
                page.wait_for_selector('tr.zA', timeout=LOGIN_WAIT_TIME * 1000)
                print("✓ Inbox loaded successfully!")
            except PlaywrightTimeout:
                print("✗ Timeout waiting for inbox. Please ensure you're logged in.")
                return
            
            # Scroll to load more emails
            print("\n[4/5] Loading emails...")
            scroll_to_load_more(page)
            
            # Extract email data
            print("\n[5/5] Extracting email data...")
            emails = extract_email_data(page)
            
            if not emails:
                print("✗ No emails found. Please check if inbox is loaded correctly.")
                return
            
            print(f"✓ Extracted {len(emails)} emails")
            
            # Insert into database
            print("\nInserting emails into database...")
            inserted_count = insert_emails_batch(emails)
            
            print(f"\n✓ Successfully inserted {inserted_count} new emails")
            print(f"✓ Skipped {len(emails) - inserted_count} duplicates")
            
            # Show final count
            total_count = get_email_count()
            print(f"\n✓ Total emails in database: {total_count}")
            
            print("\n" + "=" * 60)
            print("Scraping completed successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ Error during scraping: {e}")
            raise
        
        finally:
            # Keep browser open for a moment to see results
            print("\nClosing browser in 3 seconds...")
            time.sleep(3)
            browser.close()


if __name__ == "__main__":
    try:
        scrape_gmail()
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
