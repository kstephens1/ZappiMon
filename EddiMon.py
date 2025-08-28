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

# Global variables for notification tracking
last_notification_sent_at = {}

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

def sendNotif(message, title="EddiMon Alert", priority=0):
    """
    Send a notification using Pushover API

    Args:
        message (str): The message to send
        title (str): The title of the message (default: "EddiMon Alert")
        priority (int): Priority level (-2 to 2, default: 0)

    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    # Rate limit certain titles to avoid duplicate notifications
    rate_limited_titles = {
        # Do not send this alert more than once per hour
        "EddiMon - Low water temperature": 3600,
    }

    now = datetime.now()
    if title in rate_limited_titles:
        cooldown_seconds = rate_limited_titles[title]
        last_sent = last_notification_sent_at.get(title)
        if last_sent is not None and (now - last_sent).total_seconds() < cooldown_seconds:
            remaining = cooldown_seconds - (now - last_sent).total_seconds()
            print(
                f"Skipping notification '{title}' due to rate limit. Try again in {int(remaining)}s."
            )
            return False

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
        "priority": priority,
    }

    try:
        # Make the API call
        response = requests.post(pushover_url, data=data, timeout=30)

        # Check response status
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get("status") == 1:
                print(f"Notification sent successfully: {title}")
                # Record send time for rate-limited titles
                last_notification_sent_at[title] = now
                return True
            else:
                print(
                    f"Pushover API error: "
                    f"{json_response.get('errors', ['Unknown error'])}"
                )
                return False
        elif response.status_code == 429:
            print(
                "Pushover API: Rate limit exceeded. Please wait before sending more notifications."
            )
            return False
        elif response.status_code >= 400 and response.status_code < 500:
            # Client error - don't retry
            json_response = response.json()
            print(
                f"Pushover API client error: {json_response.get('errors', ['Unknown error'])}"
            )
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
    """
    Main function to get and display Eddi temperature
    """
    temperature = get_eddi_temperature()
    
    if temperature is not None:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} Eddi Temperature: {temperature}")
        
        # Check if temperature is below 41 degrees and send notification
        if temperature <= 41:
            message = f"Low water temp detected {temperature}"
            sendNotif(message, "EddiMon - Low water temperature")
    else:
        print("Failed to retrieve Eddi temperature")

if __name__ == "__main__":
    main()
