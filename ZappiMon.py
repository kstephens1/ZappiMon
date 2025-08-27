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
from database import ZappiDatabase
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Global variables for export tracking
excessive_export_start = None
notification_sent = False
last_notification_sent_at = {}


def check_excessive_export(grd_value, current_time):
    """
    Check if we have been exporting more than 1000W for 15 consecutive minutes
    Returns True if notification should be sent
    """
    global excessive_export_start, notification_sent

    # Check if current reading is excessive export (>1000W)
    if grd_value < -1000:
        # If this is the start of excessive export
        if excessive_export_start is None:
            excessive_export_start = current_time
            notification_sent = False

        # Check if we've been exporting for 15 minutes
        if excessive_export_start is not None:
            time_diff = current_time - excessive_export_start
            if time_diff.total_seconds() >= 900:  # 15 minutes = 900 seconds
                if not notification_sent:
                    notification_sent = True
                    return True
    else:
        # Reset tracking if not excessive export
        excessive_export_start = None
        notification_sent = False

    return False


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
    # Rate limit certain titles to avoid duplicate notifications
    rate_limited_titles = {
        # Do not send this alert more than once per hour
        "ZappiMon - Sustained Excessive Export Alert": 3600,
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
    # Initialize database
    db = ZappiDatabase()

    # API endpoint and credentials
    url = "https://director.myenergi.net/cgi-jstatus-Z"
    username = os.getenv("MYENERGI_USERNAME")
    password = os.getenv("MYENERGI_PASSWORD")

    # Headers
    headers = {"accept": "application/json", "content-type": "application/json"}

    try:
        # Make the API call with digest authentication
        response = requests.get(
            url, auth=HTTPDigestAuth(username, password), headers=headers, timeout=30
        )

        # Check if the request was successful
        response.raise_for_status()

        # Parse the JSON response
        try:
            json_response = response.json()

            # Check if zappi data exists
            if "zappi" in json_response and len(json_response["zappi"]) > 0:
                zappi_data = json_response["zappi"][0]

                # Get the 'grd' value
                grd_value = zappi_data.get("grd", 0)

                # Store the reading in database with current timestamp
                current_time = datetime.now()
                db.store_grid_reading(grd_value, current_time)

                # Check if grd is positive (importing) or negative (exporting)
                if grd_value > 0:
                    print(f"\n{current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Importing: {grd_value}W")
                elif grd_value < 0:
                    print(f"\n{current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Exporting: {grd_value}W")
                    # Check if export is excessive (more than 1000)
                    if abs(grd_value) > 1000:
                        print(">>>>>>>Excessive Export Alert<<<<<<<")

                        # Show export tracking status
                        if excessive_export_start is not None:
                            time_diff = current_time - excessive_export_start
                            minutes_elapsed = time_diff.total_seconds() / 60
                            print(
                                f"Excessive export duration: {minutes_elapsed:.1f} minutes"
                            )

                        # Check for consecutive 15-minute excessive export
                        if check_excessive_export(grd_value, current_time):
                            # Send notification for sustained excessive export
                            sendNotif(
                                message=f"Excessive export detected: {grd_value}W",
                                title="ZappiMon - Sustained Excessive Export Alert",
                                priority=1,
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
