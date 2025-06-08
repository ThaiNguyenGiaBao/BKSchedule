from flask import Blueprint, request, jsonify, redirect, session
import os 
import json
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow


from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from flask_session import Session



load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

print(f"CLIENT_ID: {CLIENT_ID}")
print(f"CLIENT_SECRET: {CLIENT_SECRET}")


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')



flow = Flow.from_client_secrets_file(
    'auth.json',
    scopes=[     # these will get overridden
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'
    ],
    redirect_uri='http://localhost:8080/api/auth/callback'  # Adjust this to your actual callback URL
)

flow.scope = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/calendar'
]

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Enable insecure transport for local testing




def require_auth(function):
    def wrapper(*arg, **kwargs):
        if "google_id" in session:
            return function(*arg, **kwargs)
        else:
            return jsonify({"message": "Authentication required"}), 401
    return wrapper

@auth_bp.route('/login', methods=['GET'])
def login():
    authorization_url, state = flow.authorization_url(
        access_type='offline',   
        include_granted_scopes='true',
        prompt='consent'  # Force the user to re-consent
    )
    session['state'] = state
    return redirect(authorization_url)

@auth_bp.route('/callback', methods=['GET'])
def callback():
    flow.fetch_token(authorization_response=request.url)
    

    creds = flow.credentials
    oauth2 = build('oauth2', 'v2', credentials=creds)
    userinfo = oauth2.userinfo().get().execute()
    google_user_id = userinfo['id']
    
    session['google_tokens'] = {
        'access_token':  creds.token,
        'refresh_token': creds.refresh_token
    }
    
    #Print session data for debugging
    print("Session data:")
    for key, value in session.items():
        print(f"{key}: {value}")
    
    
    # return jsonify({
    #     "message": "Login successful",
    #     "google_id": google_user_id,
    #     "email": userinfo['email'],
    #     "name": userinfo['name']
    # }), 200

    return jsonify({
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "google_id": google_user_id,
        "email": userinfo['email'],
        "name": userinfo['name']
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    pass

@auth_bp.route('/', methods=['GET'])
def index():
    return "Welcome to the Auth API, <a href='/api/auth/login'>Login</a>", 200


@auth_bp.route('/protected', methods=['GET'])
@require_auth
def protected():
    return jsonify({"message": "This is a protected route"}), 200

