#!/usr/bin/env python3
"""
EddiMon - Monitor MyEnergi Eddi temperature
Queries the MyEnergi API to get Eddi temperature data
"""

import os
import json
import requests
from requests.auth import HTTPDigestAuth
from dotenv import load_dotenv
from datetime import datetime

def get_eddi_temperature():
    """
    Query the MyEnergi API to get Eddi temperature data
    Returns the tp1 temperature value or None if error
    """
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    username = os.getenv('MYENERGI_USERNAME')
    password = os.getenv('MYENERGI_PASSWORD')
    
    if not username or not password:
        print("Error: MYENERGI_USERNAME and MYENERGI_PASSWORD must be set in .env file")
        return None
    
    # API endpoint for Eddi status
    url = "https://s18.myenergi.net/cgi-jstatus-E"
    
    try:
        # Make request with digest authentication
        response = requests.get(
            url,
            auth=HTTPDigestAuth(username, password),
            timeout=30
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Extract temperature from response
        # The API returns data in format: {"eddi": [{"tp1": value, ...}]}
        if 'eddi' in data and isinstance(data['eddi'], list) and len(data['eddi']) > 0:
            # Get the first Eddi device which contains current status
            eddi_status = data['eddi'][0]
            if 'tp1' in eddi_status:
                return eddi_status['tp1']
        
        print("Error: No temperature data found in response")
        print(f"Response structure: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def main():
    """
    Main function to get and display Eddi temperature
    """
    temperature = get_eddi_temperature()
    
    if temperature is not None:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} Eddi Temperature: {temperature}")
        print()
    else:
        print("Failed to retrieve Eddi temperature")

if __name__ == "__main__":
    main()
