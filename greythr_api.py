#!/usr/bin/env python3
"""
GreytHR Attendance Automation - API Version
Login with Selenium -> Use API calls for attendance marking
"""

import time
import requests
import json
import os
from dotenv import load_dotenv

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("❌ Selenium not installed! Run: pip install selenium webdriver-manager")

class GreytHRAttendanceAPI:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get configuration from environment variables
        self.base_url = os.getenv('GREYTHR_URL')
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        
        self.api_base = f"{self.base_url.rstrip('/')}/v3/api"
        self.attendance_api = f"{self.api_base}/attendance/mark-attendance"
        
        # Initialize requests session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })

    def login_and_get_cookies(self, username, password):
        """
        Login using Selenium and extract cookies for API calls
        """
        if not SELENIUM_AVAILABLE:
            return False

        print("🚀 Starting Login Process...")
        print("=" * 50)
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = None
        try:
            # Initialize WebDriver
            print("🔧 Setting up browser...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # Login process
            print(f"🔐 Logging in to: {self.base_url}")
            driver.get(self.base_url)
            time.sleep(5)  # Wait for JavaScript to load
            
            # Find and fill login fields
            print("🔍 Finding login fields...")
            
            # Find username field
            username_selectors = [
                "input[name*='user']",
                "input[name*='email']", 
                "input[type='email']",
                "input[type='text']:first-of-type"
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ Username field found")
                    break
                except:
                    continue
            
            if not username_field:
                print("❌ Could not find username field")
                return False
            
            # Find password field
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                print("✅ Password field found")
            except:
                print("❌ Could not find password field")
                return False
            
            # Fill credentials
            print("📝 Entering credentials...")
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit login
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_button.click()
            except:
                password_field.send_keys(Keys.RETURN)
            
            print("🔘 Login submitted, waiting...")
            time.sleep(5)
            
            # Check if login successful
            if "dashboard" in driver.current_url.lower() or "home" in driver.current_url.lower():
                print("✅ Login successful!")
            else:
                print(f"⚠️ Redirected to: {driver.current_url}")
            
            # Extract cookies
            print("🍪 Extracting cookies...")
            selenium_cookies = driver.get_cookies()
            
            # Transfer cookies to requests session
            for cookie in selenium_cookies:
                self.session.cookies.set(
                    cookie['name'], 
                    cookie['value'],
                    domain=cookie.get('domain'),
                    path=cookie.get('path', '/'),
                    secure=cookie.get('secure', False)
                )
            
            print(f"✅ Transferred {len(selenium_cookies)} cookies to session")
            
            # Print important cookies for debugging
            important_cookies = ['access_token', 'PLAY_SESSION']
            for cookie_name in important_cookies:
                cookie_value = self.session.cookies.get(cookie_name)
                if cookie_value:
                    print(f"🔑 {cookie_name}: {cookie_value[:20]}...")
                else:
                    print(f"⚠️ {cookie_name}: Not found")
            
            return True
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
            
        finally:
            if driver:
                driver.quit()

    def mark_attendance(self, action="Signin"):
        """
        Mark attendance using the API endpoint
        action can be "Signin" or "Signout"
        """
        print(f"\n🎯 MARKING ATTENDANCE: {action.upper()}")
        print("=" * 50)
        
        # Prepare API request
        url = f"{self.attendance_api}?action={action}"
        
        # Empty JSON payload as shown in your curl
        payload = {}
        
        print(f"📤 API Request:")
        print(f"   URL: {url}")
        print(f"   Method: POST")
        print(f"   Payload: {json.dumps(payload)}")
        
        try:
            # Make the API request
            response = self.session.post(
                url,
                json=payload,
                timeout=30
            )
            
            print(f"📥 Response:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            # Try to parse response as JSON
            try:
                response_data = response.json()
                print(f"   JSON Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"   Text Response: {response.text}")
            
            if response.status_code == 200:
                print(f"✅ {action} SUCCESSFUL!")
                return True
            else:
                print(f"❌ {action} FAILED! Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API request error: {e}")
            return False

    def run_full_automation(self, username, password, action="Signin"):
        """
        Complete flow: Login -> Mark Attendance via API
        """
        print("🚀 GreytHR API Attendance Automation")
        print("=" * 50)
        
        # Step 1: Login and get cookies
        login_success = self.login_and_get_cookies(username, password)
        
        if not login_success:
            print("❌ Login failed! Cannot proceed with attendance marking.")
            return False
        
        print(f"\n⏳ Waiting 3 seconds before API call...")
        time.sleep(3)
        
        # Step 2: Mark attendance via API
        attendance_success = self.mark_attendance(action)
        
        return attendance_success

def main():
    if not SELENIUM_AVAILABLE:
        return
    
    print("🎯 GreytHR API Attendance Automation")
    print("=" * 40)
    print("This uses the API endpoint you discovered!")
    print()
    
    # Get credentials from environment variables
    url = os.getenv('GREYTHR_URL')
    username = os.getenv('GREYTHR_USERNAME')
    password = os.getenv('GREYTHR_PASSWORD')
    
    if not url or not username or not password:
        print("❌ Credentials not found in environment!")
        print("Please create a .env file with:")
        print("GREYTHR_URL=https://company.greythr.com")
        print("GREYTHR_USERNAME=your_username")
        print("GREYTHR_PASSWORD=your_password")
        return
    
    # Choose action
    print("\nChoose action:")
    print("1. ✅ Sign In")
    print("2. ❌ Sign Out")
    print("3. 🔄 Test Both (Sign In, wait, then Sign Out)")
    
    choice = input("Choose (1-3): ").strip()
    
    # Create API automation instance
    greythr_api = GreytHRAttendanceAPI()
    
    if choice == "1":
        success = greythr_api.run_full_automation(username, password, "Signin")
        
    elif choice == "2":
        success = greythr_api.run_full_automation(username, password, "Signout")
        
    elif choice == "3":
        print("\n🔄 Testing both actions...")
        
        # Sign In
        signin_success = greythr_api.run_full_automation(username, password, "Signin")
        
        if signin_success:
            print("\n⏳ Waiting 30 seconds before sign out...")
            for i in range(30, 0, -1):
                print(f"⏰ {i} seconds remaining...", end='\r')
                time.sleep(1)
            print("\n")
            
            # Sign Out (reuse the same session)
            signout_success = greythr_api.mark_attendance("Signout")
            success = signin_success and signout_success
        else:
            success = False
    else:
        print("❌ Invalid choice!")
        return
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 AUTOMATION COMPLETED SUCCESSFULLY!")
    else:
        print("❌ AUTOMATION FAILED!")
    print("=" * 50)

if __name__ == "__main__":
    main()
