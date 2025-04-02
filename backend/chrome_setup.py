def setup_chrome_driver():
    """
    Set up Chrome WebDriver with specific Chrome binary path
    """
    chrome_options = Options()
    
    # Explicitly set the Chrome binary location
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    # Add additional options for headless and stability
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")
    
    try:
        # Use WebDriver Manager to handle driver installation
        service = Service(ChromeDriverManager().install())
        
        # Create and return the driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        
        # Additional diagnostic print to help troubleshoot
        print("Detailed exception information:")
        import traceback
        traceback.print_exc()
        
        raise