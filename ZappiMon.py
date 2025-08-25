#!/usr/bin/env python3
"""
ZappiMon - MyEnergi API Client
Makes API calls to the MyEnergi director endpoint using digest authentication
"""

import requests
from requests.auth import HTTPDigestAuth
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def sendNotif(message, title="ZappiMon Alert", priority=0):
    """
    Send a notification using Pushover API
    
    Args:
        message (str): The message to send
        title (str): The title of the message (default: "ZappiMon Alert")
        priority (int): Priority level (-2 to 2, default: 0)
    
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    # Pushover API configuration
    pushover_url = "https://api.pushover.net/1/messages.json"
    app_token = os.getenv("PUSHOVER_APP_TOKEN")
    user_key = os.getenv("PUSHOVER_USER_KEY")
    

    # Prepare the request data
    data = {
        "token": app_token,
        "user": user_key,
        "message": message,
        "title": title,
        "priority": priority
    }
    
    try:
        # Make the API call
        response = requests.post(pushover_url, data=data, timeout=30)
        
        # Check response status
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get("status") == 1:
                print(f"Notification sent successfully: {title}")
                return True
            else:
                print(f"Pushover API error: {json_response.get('errors', ['Unknown error'])}")
                return False
        elif response.status_code == 429:
            print("Pushover API: Rate limit exceeded. Please wait before sending more notifications.")
            return False
        elif response.status_code >= 400 and response.status_code < 500:
            # Client error - don't retry
            json_response = response.json()
            print(f"Pushover API client error: {json_response.get('errors', ['Unknown error'])}")
            return False
        else:
            # Server error - could retry later
            print(f"Pushover API server error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending notification: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error sending notification: {e}")
        return False

def main():
    # API endpoint and credentials
    url = 'https://director.myenergi.net/cgi-jstatus-Z'
    username = os.getenv("MYENERGI_USERNAME")
    password = os.getenv("MYENERGI_PASSWORD")
    
    # Headers
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json'
    }
    
    try:
        # Make the API call with digest authentication
        response = requests.get(
            url,
            auth=HTTPDigestAuth(username, password),
            headers=headers,
            timeout=30
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        try:
            json_response = response.json()
            
            # Check if zappi data exists
            if 'zappi' in json_response and len(json_response['zappi']) > 0:
                zappi_data = json_response['zappi'][0]
                
                # Get the 'grd' value
                grd_value = zappi_data.get('grd', 0)
                
                # Check if grd is positive (importing) or negative (exporting)
                if grd_value > 0:
                    print(f"Importing: {grd_value}")
                elif grd_value < 0:
                    print(f"Exporting: {grd_value}")
                    # Check if export is excessive (more than 1000)
                    if abs(grd_value) > 1000:
                        print(">>>>>>>Excessive Export Alert<<<<<<<")
                        # Send notification for excessive export
                        sendNotif(
                            message=f"Excessive export detected: {grd_value}W",
                            title="ZappiMon - Excessive Export Alert",
                            priority=1
                        )
                else:
                    print(f"Grid: {grd_value} (neutral)")
            else:
                print("No zappi data found in response")
                
        except json.JSONDecodeError:
            print("Error: Response is not valid JSON")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
