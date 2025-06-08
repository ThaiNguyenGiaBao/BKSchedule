from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from utils import transform_to_calendar_events



celandar_bp = Blueprint('calendar', __name__, url_prefix='/api/calendar')

def getCalendarService(access_token, refresh_token):
    client_id = "1148541732725-usgt189nmop22b764l5c27msugm7rmji.apps.googleusercontent.com"
    client_secret = "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"
    token_uri = "https://oauth2.googleapis.com/token"
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    service = build('calendar', 'v3', credentials=creds)
    print("Google Calendar service created successfully")
    return service








@celandar_bp.route('', methods=['GET'])
def getEvents():
    """
    Fetches events from the Google Calendar API within the specified date range.
    
    :param startDate: The start date in ISO format (YYYY-MM-DD).
    :param endDate: The end date in ISO format (YYYY-MM-DD).
    :return: A list of events within the specified date range.
    """

    # Get Tokens from session or request args
    tokens = session.get('google_tokens')
    print("tokens:", tokens)
   
    access_token = tokens.get('access_token') if tokens else request.args.get('access_token')
    refresh_token = tokens.get('refresh_token') if tokens else request.args.get('refresh_token')
    
        
        
   
    if not access_token or not refresh_token:
        return jsonify({"error": "Access token and refresh token are required"}), 401
    
    service = getCalendarService(access_token, refresh_token)
    if not service:
        return jsonify({"error": "Failed to create calendar service"}), 500
    
    now       = datetime.now(timezone.utc)
    startDate = request.args.get('startDate') or (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    endDate   = request.args.get('endDate')   or (now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

         
    print(f"Fetching events from {startDate} to {endDate}")
   
    events_result = service.events().list(
        calendarId='primary',
        timeMin=startDate,
        timeMax=endDate,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    revents = events_result.get('items', [])
    if not revents:
        print('No upcoming events found.')
    else:
        print('Upcoming events:')
        for event in revents:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            print(f"{start} - {end}: {event['summary']}")
            
    return jsonify(revents), 200
    
    
        

@celandar_bp.route('/', methods=['POST'])
def create_event(): 
    # Get events from request body
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload provided"}), 400
    
    # Get Tokens from session or request args
    tokens = session.get('google_tokens')
    print("tokens:", tokens)
   
    access_token = tokens.get('access_token') if tokens else request.args.get('access_token')
    refresh_token = tokens.get('refresh_token') if tokens else request.args.get('refresh_token')
    
        
    if not access_token or not refresh_token:
        return jsonify({"error": "Access token and refresh token are required"}), 401

    service = getCalendarService(access_token, refresh_token)
    if not service:
        return jsonify({"error": "Failed to create calendar service"}), 500 
    
    events = transform_to_calendar_events(payload)
    for event in events:
        try:
            service.events().insert(calendarId='primary', body=event).execute()
        except Exception as e:
            return jsonify({"error": f"Failed to create event: {str(e)}"}), 500
        
    return jsonify({"message": "Events created successfully"}), 201
   
    