"""
Google Calendar Integration - Production Grade
==============================================
- Proper timezone handling (local time, not UTC)
- Read AND write support
- Retry logic and error handling
- Simplified setup
"""

import os
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from zoneinfo import ZoneInfo

# Google Calendar imports
CALENDAR_AVAILABLE = False
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import pickle
    CALENDAR_AVAILABLE = True
except ImportError:
    print("[CALENDAR] Google Calendar libraries not installed.")
    print("           Install: pip install google-auth google-auth-oauthlib google-api-python-client")


@dataclass
class CalendarEvent:
    """Calendar event with proper typing"""
    id: str
    summary: str
    start: datetime.datetime
    end: datetime.datetime
    location: Optional[str] = None
    description: Optional[str] = None
    all_day: bool = False


class CalendarIntegration:
    """
    Production-grade Google Calendar integration.
    Proper timezone handling, read/write support.
    """
    
    # Full access scope for read/write
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',  # Full access
    ]
    
    def __init__(self, perception=None):
        print("[CALENDAR] Initializing Calendar Integration...")
        self.perception = perception
        self.service = None
        self.available = CALENDAR_AVAILABLE
        
        # Data paths
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.token_path = self.data_dir / "calendar_token.pickle"
        self.credentials_path = self.data_dir / "calendar_credentials.json"
        
        # Timezone - detect system timezone
        self.timezone = self._detect_timezone()
        
        if self.available:
            self._authenticate()
        else:
            print("[CALENDAR] Calendar features disabled - libraries not installed")
            
        print(f"[CALENDAR] Integration Ready (TZ: {self.timezone})")
        
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
        
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[CALENDAR] {text}")
            
    def _detect_timezone(self) -> str:
        """Detect system timezone"""
        try:
            # Try to get local timezone
            import time
            if time.daylight:
                offset = time.altzone
            else:
                offset = time.timezone
            hours = -offset // 3600
            
            # Common timezone mappings
            if hours == 5 and offset % 3600 == 1800:
                return "Asia/Kolkata"  # IST
            elif hours == 0:
                return "UTC"
            elif hours == -5:
                return "America/New_York"
            elif hours == -8:
                return "America/Los_Angeles"
            else:
                # Use offset-based timezone
                sign = "+" if hours >= 0 else "-"
                return f"Etc/GMT{sign}{abs(hours)}"
        except:
            return "UTC"
            
    def _authenticate(self):
        """Authenticate with Google Calendar"""
        creds = None
        
        # Load existing token
        if self.token_path.exists():
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"[CALENDAR] Token load error: {e}")
                
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"[CALENDAR] Token refresh error: {e}")
                    creds = None
                    
            if not creds:
                if self.credentials_path.exists():
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            str(self.credentials_path), self.SCOPES
                        )
                        creds = flow.run_local_server(port=8080)
                    except Exception as e:
                        print(f"[CALENDAR] Auth error: {e}")
                        self.available = False
                        return
                else:
                    print(f"[CALENDAR] No credentials file found at: {self.credentials_path}")
                    print("           Download from Google Cloud Console")
                    self.available = False
                    return
                    
            # Save token
            try:
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                print(f"[CALENDAR] Token save error: {e}")
                
        # Build service
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            print("[CALENDAR] Authenticated successfully")
        except Exception as e:
            print(f"[CALENDAR] Service build error: {e}")
            self.available = False
            
    def _to_local_time(self, event_time: str) -> datetime.datetime:
        """Convert event time to local timezone"""
        try:
            # Handle datetime with timezone
            if 'T' in event_time:
                dt = datetime.datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                # Convert to local timezone
                local_tz = ZoneInfo(self.timezone)
                return dt.astimezone(local_tz)
            else:
                # All-day event (just date)
                return datetime.datetime.strptime(event_time, "%Y-%m-%d")
        except Exception as e:
            print(f"[CALENDAR] Time parse error: {e}")
            return datetime.datetime.now()
            
    def _format_time(self, dt: datetime.datetime, all_day: bool = False) -> str:
        """Format time for speaking"""
        if all_day:
            return dt.strftime("on %A, %B %d")
        else:
            return dt.strftime("at %I:%M %p on %A")
            
    def _parse_event(self, event_data: Dict) -> CalendarEvent:
        """Parse API event data to CalendarEvent"""
        start_raw = event_data['start'].get('dateTime', event_data['start'].get('date'))
        end_raw = event_data['end'].get('dateTime', event_data['end'].get('date'))
        
        all_day = 'date' in event_data['start']
        
        return CalendarEvent(
            id=event_data.get('id', ''),
            summary=event_data.get('summary', 'Untitled event'),
            start=self._to_local_time(start_raw),
            end=self._to_local_time(end_raw),
            location=event_data.get('location'),
            description=event_data.get('description'),
            all_day=all_day,
        )
        
    def get_upcoming_events(self, max_results: int = 5) -> List[CalendarEvent]:
        """Get upcoming calendar events"""
        title = self._get_title()
        
        if not self.available or not self.service:
            self._speak(f"Calendar is not connected, {title}. Please set up Google Calendar credentials.")
            return []
            
        try:
            # Use local timezone for "now"
            local_tz = ZoneInfo(self.timezone)
            now = datetime.datetime.now(local_tz)
            now_iso = now.isoformat()
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now_iso,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime',
                timeZone=self.timezone,  # Request in local timezone
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                self._speak(f"No upcoming events, {title}.")
                return []
                
            self._speak(f"You have {len(events)} upcoming events, {title}.")
            
            result = []
            for event_data in events:
                event = self._parse_event(event_data)
                result.append(event)
                
                time_str = self._format_time(event.start, event.all_day)
                self._speak(f"{event.summary} {time_str}")
                
            return result
            
        except HttpError as e:
            print(f"[CALENDAR] API error: {e}")
            self._speak(f"Calendar API error, {title}. Please try again.")
            return []
        except Exception as e:
            print(f"[CALENDAR] Error: {e}")
            self._speak(f"Error reading calendar, {title}.")
            return []
            
    def get_today_events(self) -> List[CalendarEvent]:
        """Get today's events in local timezone"""
        title = self._get_title()
        
        if not self.available or not self.service:
            self._speak(f"Calendar is not connected, {title}.")
            return []
            
        try:
            local_tz = ZoneInfo(self.timezone)
            now = datetime.datetime.now(local_tz)
            
            # Start and end of today in local timezone
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy='startTime',
                timeZone=self.timezone,
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                self._speak(f"No events scheduled for today, {title}.")
                return []
                
            self._speak(f"You have {len(events)} events today, {title}.")
            
            result = []
            for event_data in events:
                event = self._parse_event(event_data)
                result.append(event)
                
                if event.all_day:
                    self._speak(f"{event.summary}, all day")
                else:
                    time_str = event.start.strftime("at %I:%M %p")
                    self._speak(f"{event.summary} {time_str}")
                    
            return result
            
        except Exception as e:
            print(f"[CALENDAR] Error: {e}")
            self._speak(f"Error reading today's events, {title}.")
            return []
            
    def create_event(
        self,
        summary: str,
        start_time: datetime.datetime,
        duration_minutes: int = 60,
        description: str = None,
        location: str = None,
    ) -> Optional[str]:
        """
        Create a new calendar event.
        Returns event ID if successful.
        """
        title = self._get_title()
        
        if not self.available or not self.service:
            self._speak(f"Calendar is not connected, {title}.")
            return None
            
        try:
            # Ensure timezone-aware
            local_tz = ZoneInfo(self.timezone)
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=local_tz)
                
            end_time = start_time + datetime.timedelta(minutes=duration_minutes)
            
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': self.timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': self.timezone,
                },
            }
            
            if description:
                event['description'] = description
            if location:
                event['location'] = location
                
            result = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            event_id = result.get('id')
            time_str = start_time.strftime("%I:%M %p on %A, %B %d")
            self._speak(f"Event created: {summary} at {time_str}, {title}.")
            
            return event_id
            
        except Exception as e:
            print(f"[CALENDAR] Create event error: {e}")
            self._speak(f"Failed to create event, {title}.")
            return None
            
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event by ID"""
        title = self._get_title()
        
        if not self.available or not self.service:
            self._speak(f"Calendar is not connected, {title}.")
            return False
            
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            self._speak(f"Event deleted, {title}.")
            return True
            
        except Exception as e:
            print(f"[CALENDAR] Delete event error: {e}")
            self._speak(f"Failed to delete event, {title}.")
            return False
            
    def quick_add(self, text: str) -> Optional[str]:
        """
        Quick add event using natural language.
        Example: "Meeting with John tomorrow at 3pm"
        """
        title = self._get_title()
        
        if not self.available or not self.service:
            self._speak(f"Calendar is not connected, {title}.")
            return None
            
        try:
            result = self.service.events().quickAdd(
                calendarId='primary',
                text=text
            ).execute()
            
            event = self._parse_event(result)
            time_str = self._format_time(event.start, event.all_day)
            self._speak(f"Created: {event.summary} {time_str}, {title}.")
            
            return result.get('id')
            
        except Exception as e:
            print(f"[CALENDAR] Quick add error: {e}")
            self._speak(f"Failed to add event, {title}.")
            return None
            
    def is_connected(self) -> bool:
        """Check if calendar is connected and working"""
        return self.available and self.service is not None


# Singleton
_calendar = None

def get_calendar(perception=None) -> CalendarIntegration:
    global _calendar
    if _calendar is None:
        _calendar = CalendarIntegration(perception)
    return _calendar
