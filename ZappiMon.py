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
import sys
from dotenv import load_dotenv
from database import ZappiDatabase
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Global variables for export tracking
excessive_export_start = None
notification_sent = False
last_notification_sent_at = {}


# DB-backed check for sustained excessive export over a rolling window
def has_sustained_excessive_export(
    db: ZappiDatabase,
    minutes: int = 15,
    threshold_watts: int = -1000,
    required_ratio: float = 0.8,
) -> bool:
    """
    Return True if, over the last `minutes`, ALL readings indicate export below the threshold.

    Notes:
    - Intended for cron-based runs where process memory does not persist.
    - Requires enough coverage in the window (at least 3 readings and span ~window).
    """
    try:
        readings = db.get_readings_since_minutes(minutes)
    except Exception as e:
        print(f"DEBUG: DB query failed for window check: {e}")
        return False

    if not readings:
        print("DEBUG: No readings in window; cannot confirm sustained export")
        return False

    # readings: List[Tuple(grd_value, timestamp)] ordered ASC by timestamp
    parsed = []
    for grd_value, ts in readings:
        ts_dt = ts
        if isinstance(ts, str):
            try:
                # SQLite stores as 'YYYY-MM-DD HH:MM:SS.SSSSSS'
                ts_dt = datetime.fromisoformat(ts)
            except ValueError:
                # Fallback parse without micros
                try:
                    ts_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    print(f"DEBUG: Unparseable timestamp: {ts}")
                    continue
        parsed.append((int(grd_value), ts_dt))

    if len(parsed) < 3:
        print(f"DEBUG: Only {len(parsed)} readings in window; need >= 3 for confidence")
        return False

    now = datetime.now()
    oldest_time = parsed[0][1]
    newest_time = parsed[-1][1]
    window_span_seconds = (newest_time - oldest_time).total_seconds()

    # Expect roughly full coverage of the window; allow 90s slack
    required_span = minutes * 60 - 90
    if window_span_seconds < required_span:
        print(
            f"DEBUG: Insufficient window span {window_span_seconds:.0f}s; need >= {required_span}s"
        )
        return False

    total = len(parsed)
    below = sum(1 for grd, _ in parsed if grd <= threshold_watts)
    ratio = below / total if total else 0.0

    if ratio >= required_ratio:
        print(
            f"DEBUG: Sustained export confirmed for {minutes}m; {below}/{total} ({ratio:.0%}) readings <= {threshold_watts}W"
        )
        return True

    print(
        f"DEBUG: Not enough excessive readings: {below}/{total} ({ratio:.0%}) <= {threshold_watts}W; need >= {required_ratio:.0%}"
    )
    return False


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
            print(f"DEBUG: Started tracking excessive export at {current_time}")

        # Check if we've been exporting for 15 minutes
        if excessive_export_start is not None:
            time_diff = current_time - excessive_export_start
            if time_diff.total_seconds() >= 900:  # 15 minutes = 900 seconds
                if not notification_sent:
                    notification_sent = True
                    print(f"DEBUG: Triggering notification after {time_diff.total_seconds()/60:.1f} minutes")
                    return True
                else:
                    print(f"DEBUG: Notification already sent, skipping")
            else:
                print(f"DEBUG: Export duration: {time_diff.total_seconds()/60:.1f} minutes (need 15)")
    else:
        # Reset tracking if not excessive export
        if excessive_export_start is not None:
            print(f"DEBUG: Resetting export tracking (current: {grd_value}W)")
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
    # Rate limit certain titles to avoid duplicate notifications (process-local)
    # Note: Persistent cooldowns are handled below via the database.
    rate_limited_titles = {}

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
        else:
            print(f"DEBUG: Rate limit check passed for '{title}'")

    # Persistent 2-hour cooldown for the sustained excessive export alert
    if title == "ZappiMon - Sustained Excessive Export Alert":
        try:
            db = ZappiDatabase()
            last_sent_raw = db.get_last_notification_sent_at(title)
            if last_sent_raw:
                try:
                    last_sent_dt = datetime.fromisoformat(last_sent_raw)
                except ValueError:
                    try:
                        last_sent_dt = datetime.strptime(last_sent_raw, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        last_sent_dt = None
                if last_sent_dt is not None:
                    elapsed = (now - last_sent_dt).total_seconds()
                    if elapsed < 7200:
                        print(
                            f"Skipping '{title}' due to persistent cooldown. Try again in {int(7200 - elapsed)}s."
                        )
                        return False
            print(f"DEBUG: Persistent cooldown check passed for '{title}'")
        except Exception as e:
            print(f"DEBUG: Persistent cooldown check failed: {e}")

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
                # Record send time for process-local rate-limiting
                last_notification_sent_at[title] = now
                # Record persistent cooldown for sustained excessive export
                if title == "ZappiMon - Sustained Excessive Export Alert":
                    try:
                        db = db if 'db' in locals() else ZappiDatabase()
                        db.set_last_notification_sent_at(title, now.isoformat(sep=' '))
                    except Exception as e:
                        print(f"DEBUG: Failed to store persistent cooldown: {e}")
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
                    print(f"\n{current_time.strftime('%Y-%m-%d %H:%M:%S')} Importing: {grd_value}W")
                elif grd_value < 0:
                    print(f"\n{current_time.strftime('%Y-%m-%d %H:%M:%S')} Exporting: {grd_value}W")
                    # DB-backed sustained excessive export over last 15 minutes
                    if has_sustained_excessive_export(db, minutes=15, threshold_watts=-1000, required_ratio=0.8):
                        print(">>>>>>>Excessive Export Alert<<<<<<<")
                        sendNotif(
                            message=f"Excessive export sustained in last 15m. Latest: {grd_value}W",
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
    # Check if "msg" parameter is provided
    if len(sys.argv) > 1 and sys.argv[1] == "msg":
        print("Sending test notification...")
        sendNotif("Just Testing", "ZappiMon Test", 0)
        print("Test notification sent!")
    else:
        main()
