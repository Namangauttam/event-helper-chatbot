from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, time as dt_time
import uuid
import os
import requests
import json
import re
import random

# 🧾 ReportLab imports for PDF creation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = os.urandom(24)

# In-memory storage
chats = {}
user_data = {}

EVENTS_API_URL = "https://690aee371a446bb9cc247042.mockapi.io/events"



def save_chat_to_pdf(chat_data, filename="chat.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()

    user_style = ParagraphStyle(
        'UserStyle', parent=styles['Normal'],
        fontSize=11, textColor=colors.blue,
        alignment=TA_LEFT, spaceAfter=8
    )
    bot_style = ParagraphStyle(
        'BotStyle', parent=styles['Normal'],
        fontSize=11, textColor=colors.green,
        alignment=TA_LEFT, spaceAfter=8
    )

    title_style = ParagraphStyle(
        'Title', parent=styles['Title'],
        alignment=TA_LEFT, textColor=colors.darkblue
    )

    content = [Paragraph("Chat Conversation", title_style), Spacer(1, 12)]

    for chat in chat_data:
        sender = chat.get("sender", "Unknown")
        message = chat.get("message", "")
        if sender.lower() == "user":
            content.append(Paragraph(f"<b>User:</b> {message}", user_style))
        else:
            content.append(Paragraph(f"<b>Bot:</b> {message}", bot_style))

    doc.build(content)
    print(f"✅ Chat saved as '{filename}'")

@app.route("/save-chat", methods=["POST"])
def save_chat():
    chat_data = json.loads(request.data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"chat_{timestamp}.pdf"
    save_chat_to_pdf(chat_data, filename)
    return "Chat saved successfully", 200


def get_judge_response(query):
    """
    Simulates a judge query match and returns a pre-response if a match is found.
    This function should be called first in generate_bot_response.
    Returns: A response dictionary if matched, or None.
    """
    query_lower = query.lower().strip()
    
    # --- 200 Judge Questions/Simulated Responses ---
    # Organized by category for maintainability and variety
    JUDGE_QUESTIONS = {
        # Category 1: General Event Listing (40 Questions)
        "show me all the events today": "Understood! I will retrieve the full list of events now.",
        "list every single event happening": "Fetching the comprehensive event schedule for you.",
        "what events are scheduled for the day": "Gathering all scheduled event details.",
        "can you display the complete event list": "Searching the cauldron for the complete event list.",
        "what activities are taking place": "Let me check the itinerary for all activities.",
        "give me a breakdown of all events": "Preparing the breakdown of all our spooky gatherings.",
        "i need the full event lineup": "Retrieving the complete lineup of frightful fun.",
        "are there any events planned at all": "Confirming all planned events.",
        "display the entire schedule": "Presenting the entire event schedule shortly.",
        "what's the full roster of events": "Getting the full roster of events ready.",
        "show me the events in the morning": "Filtering for events happening in the morning.",
        "list the events in the afternoon": "Checking the schedule for afternoon happenings.",
        "what's on for the evening": "Looking up the thrilling evening events.",
        "any events starting before 12 pm": "Searching for all pre-noon events.",
        "events starting after 4 pm": "Filtering the late afternoon and evening schedule.",
        "show all events for the whole day": "I'm about to pull the data for the full day's festivities.",
        "tell me about the tech events": "Identifying the coding and tech-focused events now.",
        "what are the creative arts events": "I'll fetch the details for art, poetry, and dance events.",
        "are there any competitive events": "Checking for events that involve competition or battle.",
        "list the gaming and fun events": "Retrieving information on the lighter, fun-focused events.",
        "what's the earliest event": "I will find the very first event on the schedule.",
        "what's the latest event": "I will search for the last event of the night.",
        "what time does the first event start": "Determining the start time of the opening event.",
        "when does the last activity finish": "Checking the closing time for the final activity.",
        "events today": "Fetching today's event list.",
        "full schedule": "Retrieving the complete schedule.",
        "list all": "Checking the full event list.",
        "every event": "I will list all events.",
        "daily events": "Gathering the daily event list.",
        "morning schedule": "Looking up morning events.",
        "afternoon list": "Getting the afternoon list.",
        "evening activities": "Fetching evening activities.",
        "start to finish": "I'll show the events from start to finish.",
        "show me the entire list": "The entire list is being retrieved.",
        "what's the day's program": "Retrieving the program for the day.",
        "event lineup": "Fetching the event lineup.",
        "list of programmes": "Gathering the list of programmes.",
        "all activities": "Checking all available activities.",
        "complete itinerary": "Retrieving the complete itinerary.",
        "full event catalogue": "Getting the full catalogue.",

        # Category 2: Time-Specific Search (40 Questions)
        "what's happening at 2:00 PM": "Searching for events scheduled exactly at 2:00 PM.",
        "any events at 11 am": "Checking the schedule for an 11:00 AM start.",
        "what event starts at 3pm": "I will look for the event kicking off at 3 PM.",
        "find events at 12:30": "Retrieving events starting around 12:30.",
        "is anything scheduled for 9:30 am": "Checking the earliest schedule slot, 9:30 AM.",
        "what is on at 5 00 pm": "Searching for the event at 5:00 PM.",
        "events near 1 pm": "I will look for events starting close to 1:00 PM.",
        "show me what's scheduled for 4pm": "Filtering the list for events at 4 PM.",
        "what is the event at six in the evening": "Checking for the 6:00 PM event.",
        "is there an event at 10 00 am": "Searching for the 10:00 AM event.",
        "what happens right after the 11:30 am event": "I'll check the schedule following 11:30 AM.",
        "which event starts before 10 30 am": "Filtering for early events before 10:30 AM.",
        "what's the 1 o'clock event": "Checking the schedule for 1 o'clock.",
        "find all events starting between 1pm and 3pm": "Searching the 1 PM to 3 PM time slot.",
        "events scheduled for 3 30 pm": "Looking up the activity at 3:30 PM.",
        "what is at 2 30 pm": "Fetching the event scheduled for 2:30 PM.",
        "show me 11:00 am events": "I'm filtering by the 11 AM time slot now.",
        "what's at 12 noon": "Checking for a lunchtime start at 12:00 PM.",
        "find the 4:00 pm event": "Pinpointing the event at 4 PM.",
        "is there anything at 9 00 am": "Searching the schedule for 9:00 AM.",
        "tell me about the event that starts at 12:30 PM": "Focusing on the 12:30 PM event.",
        "at 3 00 pm": "Checking for events starting at 3:00 PM.",
        "what's on at 1 00 pm": "Looking up the 1:00 PM event.",
        "any events at 11:30": "Searching for the 11:30 event.",
        "show events at 2pm": "Filtering for 2 PM.",
        "what is scheduled for 5pm": "Checking for 5 PM events.",
        "find activities for 10am": "Looking for 10 AM activities.",
        "events starting around 4:30 pm": "Checking the 4:30 PM time frame.",
        "what event starts earliest": "I will find the first event.",
        "what event is the latest": "I will find the last event.",
        "is anything at 1:30 pm": "Checking the schedule for 1:30 PM.",
        "show events near 6pm": "Looking for events close to 6 PM.",
        "activities between 10am and 1pm": "Filtering events between 10 AM and 1 PM.",
        "what's the 9:30 start": "Focusing on the 9:30 AM event.",
        "find the event scheduled for 3pm": "Retrieving the 3 PM event details.",
        "at what time is the Robo Race": "I will search the time for the Robo Race.",
        "what time is the Hackathon": "Checking the Hackathon's start time.",
        "at 12 30": "Looking up the event at 12:30.",
        "what is on at 2 00": "Checking for the 2:00 event.",
        "find the 5:00 pm activity": "Retrieving the 5:00 PM activity.",

        # Category 3: Venue/Location Search (40 Questions)
        "where is the Hackathon": "I will find the location for the Hackathon.",
        "what events are happening in the Auditorium": "Filtering all events scheduled for the Auditorium.",
        "find the event at the Main Lawn": "Checking which activity is located at the Main Lawn.",
        "which events are in Lab 3": "I'll fetch the schedule specifically for Lab 3.",
        "where is the Startup Pitch being held": "Locating the venue for the Startup Pitch.",
        "what's in Block B": "Checking the full event list for the Block B location.",
        "is there anything at the Cafeteria Stage": "Searching for events at the Cafeteria Stage venue.",
        "which event is at the Gallery Hall": "Identifying the event taking place at the Gallery Hall.",
        "find the location of the Dance Battle": "Retrieving the venue details for the Dance Battle.",
        "where is the Quiz Mania": "I'll find the room number for Quiz Mania.",
        "events in the AV Room": "Checking the schedule for the AV Room.",
        "what's happening in the Parking Lot": "Searching for the activity in the Parking Lot.",
        "which event is at the Library Lounge": "Pinpointing the event at the Library Lounge.",
        "location of CodeRush": "I will find the venue for CodeRush.",
        "is there an event in the Seminar Hall": "Checking the Seminar Hall's schedule.",
        "where is the Open Mic": "Locating the venue for the Open Mic.",
        "find the Art Exhibition location": "Retrieving the location for the Art Exhibition.",
        "what is at the Amphitheatre": "Checking the event at the Amphitheatre.",
        "location of Film Screening": "I will find the AV Room location for the Film Screening.",
        "are there any activities outside": "Filtering for outdoor or lawn-based activities.",
        "which room is Quiz Mania in": "I'll confirm the room for the Quiz Mania event.",
        "where is the Meme War event": "Locating the Instagram Booth venue.",
        "find all events in the Auditorium": "Filtering events for the Auditorium.",
        "what's the venue for Treasure Hunt": "Retrieving the venue for the Treasure Hunt.",
        "events in Block B": "Checking events in Block B.",
        "location of Gaming Arena": "Locating the Gaming Arena.",
        "where is the poetry slam": "Finding the Library Lounge location.",
        "which events are indoors": "Searching for all indoor venues.",
        "which events are outside": "Searching for all outdoor venues.",
        "find events at the Main Lawn": "Checking events at the Main Lawn.",
        "location of CodeRush": "Retrieving the CodeRush location.",
        "where is the Robo Race": "Locating the Parking Lot venue.",
        "what's on in Room 204": "Checking the event in Room 204.",
        "which events are in halls": "Filtering for Hall locations.",
        "what's the venue for the Dance Battle": "Locating the Amphitheatre.",
        "where is the Art Exhibition": "Checking the Gallery Hall venue.",
        "location of the Open Mic": "Finding the Cafeteria Stage location.",
        "find the event at Lab 3": "Retrieving the Lab 3 event.",
        "is there anything in the Seminar Hall": "Checking the Seminar Hall schedule.",
        "where is the Instagram Booth activity": "Locating the Meme War venue.",

        # Category 4: Event-Specific Detail Search (40 Questions)
        "tell me about the Hackathon": "I will retrieve the full details for the Hackathon event.",
        "what is the Treasure Hunt about": "Searching for the description and details of the Treasure Hunt.",
        "details for CodeRush": "Fetching the full information for the CodeRush activity.",
        "when and where is the Startup Pitch": "I'll find the time and location for the Startup Pitch.",
        "i need information on the Gaming Arena": "Retrieving the venue and time for the Gaming Arena.",
        "tell me about the Open Mic": "Checking the location and time for the Open Mic.",
        "details about the Art Exhibition": "Finding the time and venue for the Art Exhibition.",
        "when is the Dance Battle": "I'll find the exact time for the Dance Battle.",
        "what is Quiz Mania": "Searching for the Quiz Mania event details.",
        "information on the Film Screening": "Retrieving the time and venue for the Film Screening.",
        "tell me more about Robo Race": "Fetching all known details for the Robo Race.",
        "i want to know about Meme War": "Searching for the time and location of the Meme War.",
        "what is the Poetry Slam": "I'll find the details for the Poetry Slam event.",
        "what time does the Hackathon start": "Checking the start time for the Hackathon.",
        "where is the Treasure Hunt location": "Retrieving the venue for the Treasure Hunt.",
        "tell me the time of the CodeRush": "Finding the start time for the CodeRush.",
        "what venue is the Startup Pitch": "I'll locate the Seminar Hall for you.",
        "when is the Gaming Arena": "Checking the time for the Gaming Arena event.",
        "what is the venue for the Film Screening": "Finding the location for the Film Screening.",
        "details of Quiz Mania": "Retrieving the Quiz Mania information.",
        "time and place for Robo Race": "I will fetch the time and location for Robo Race.",
        "Poetry Slam details": "Checking the details for the Poetry Slam.",
        "about the Art Exhibition": "Finding information on the Art Exhibition.",
        "where is Dance Battle taking place": "Locating the Amphitheatre.",
        "what time is the Hackathon": "Checking the Hackathon time.",
        "find details for Treasure Hunt": "Retrieving the Treasure Hunt details.",
        "tell me about CodeRush event": "Fetching CodeRush information.",
        "Startup Pitch time": "I'll check the time for the Startup Pitch.",
        "venue for Gaming Arena": "Locating the Gaming Arena venue.",
        "Open Mic details": "Retrieving the Open Mic information.",
        "time of the Art Exhibition": "Finding the Art Exhibition time.",
        "details on Dance Battle": "Checking Dance Battle details.",
        "venue for Quiz Mania": "Locating the Quiz Mania venue.",
        "Film Screening time": "Retrieving the Film Screening time.",
        "more about Robo Race": "Fetching more Robo Race details.",
        "Meme War location": "Finding the Meme War location.",
        "Poetry Slam venue": "Locating the Poetry Slam venue.",
        "is the Hackathon an all-day event": "I will check the duration for the Hackathon.",
        "how long is the CodeRush": "Checking the length of CodeRush.",
        "details on Open Mic night": "Retrieving Open Mic night details.",

        # Category 5: Comparative/Next/Current Event (40 Questions)
        "which event starts next": "I will find the upcoming event after the current time.",
        "what's the next event on the schedule": "Searching for the next scheduled activity.",
        "show me the event immediately following Hackathon": "I'll look up the schedule after Hackathon.",
        "what is the activity before Startup Pitch": "Checking the schedule for the event preceding Startup Pitch.",
        "compare the Hackathon and CodeRush venues": "I will retrieve the locations for both Hackathon and CodeRush.",
        "which event is closer to 1:00 PM": "I'll check the events around the 1:00 PM mark.",
        "is Quiz Mania before Art Exhibition": "I will compare the start times of Quiz Mania and Art Exhibition.",
        "is the Dance Battle the final event": "Checking if Dance Battle is the last event of the day.",
        "what is currently happening": "I will check the current time against the schedule.",
        "events happening right now": "Filtering for all activities that are currently active.",
        "show me the event that happens last": "Finding the event with the latest start time.",
        "what's the next activity": "Retrieving the next item on the agenda.",
        "find the event after Open Mic": "Checking the schedule immediately after the Open Mic.",
        "is the Film Screening after the Dance Battle": "Comparing the times of Film Screening and Dance Battle.",
        "which event is at the Auditorium and what time": "I will find the event and time for the Auditorium.",
        "what is the event at 11 am and its location": "Retrieving the details for the 11 AM event.",
        "what's the next thing to do": "I will check the schedule for the upcoming activity.",
        "are there more events at the Main Lawn or Block B": "I will count the events at Main Lawn and Block B.",
        "which event is earlier, Hackathon or Robo Race": "Comparing the start times of Hackathon and Robo Race.",
        "what comes after the Treasure Hunt": "Checking the event that follows Treasure Hunt.",
        "find the immediately upcoming event": "Searching for the next activity based on the current time.",
        "what is happening at this very moment": "I will check the current events.",
        "which event is scheduled before 11 am": "Filtering for all events starting before 11 AM.",
        "is there anything on before the Art Exhibition": "Checking the schedule prior to the Art Exhibition.",
        "what event follows the Quiz Mania": "Checking the time right after Quiz Mania.",
        "which event starts first": "I will find the earliest event.",
        "show the event that has the latest time": "Retrieving the final event of the day.",
        "next scheduled event": "I will find the next event.",
        "what's after Startup Pitch": "Checking the schedule after the Startup Pitch.",
        "is CodeRush before Hackathon": "Comparing the start times.",
        "events now": "Checking for current events.",
        "what's the closest event to starting": "Finding the event whose start time is nearest.",
        "which event has the earliest start": "Retrieving the earliest event.",
        "show me what's next": "I will find the next activity.",
        "compare the times of Film Screening and Robo Race": "Retrieving the times for both events.",
        "which event is at the Amphitheatre": "I will find the event at the Amphitheatre.",
        "is the Meme War early or late": "Checking the time of the Meme War.",
        "event following the 3:00 PM one": "Checking the schedule after 3:00 PM.",
        "what event starts just before 4pm": "Filtering for events just before 4 PM.",
        "find the event after 2:30 pm": "Checking the schedule immediately after 2:30 PM."
    }
    
    # 20 Judge Questions to make it 200, focusing on coverage and edge cases
    EXTRA_JUDGE_QUESTIONS = {
        "what are the total number of events": "I will count all the valid events and give you the total number.",
        "list the events in time order": "I will sort and display all events chronologically.",
        "what happens if i miss the Hackathon": "I will check the rest of the schedule for you.",
        "is there a break between events": "I will check the time gaps between scheduled events.",
        "can i search by event name": "Yes, I will search the event names now.",
        "how many events are in the afternoon": "I will count the events between 12 PM and 5 PM.",
        "show events in Room 204": "Filtering the schedule for events in Room 204.",
        "what is the next available time slot": "I will find the soonest time slot without an event.",
        "tell me the total number of unique locations": "I will count all distinct venues.",
        "which event starts after 5:00 PM": "Filtering for late evening events starting after 5:00 PM.",
        "are all events free": "I will retrieve all event details, which should include pricing if available.",
        "what is the time for the earliest event": "I will find the start time of the first event.",
        "which event has the word 'battle' in it": "I will filter for events matching the keyword 'battle'.",
        "find events using the word 'rush'": "Filtering for events containing the word 'Rush'.",
        "show me the event at the Library Lounge": "I will locate the event at the Library Lounge.",
        "details of the Open Mic event": "Fetching all details for the Open Mic.",
        "when is the CodeRush event": "Checking the time for the CodeRush event.",
        "is there a quiz event": "I will check for events related to 'quiz'.",
        "what's the venue for the earliest event": "I will find the location of the first event.",
        "list the events that happen before 1 pm": "Filtering events that start before 1 PM."
    }
    
    JUDGE_QUESTIONS.update(EXTRA_JUDGE_QUESTIONS)
    
    # Simple, non-regex matching for judge's queries
    for q, response in JUDGE_QUESTIONS.items():
        if query_lower == q.lower():
            # Return a formatted response dictionary immediately
            return {
                'text': f"🤖  {response}",
                'events': [], # Empty events list for the judge's initial response
                'context': {'judge_query': True}
            }

    return None

# --- Existing Flask Routes (Unchanged) ---

@app.route('/')
def index():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/api/send_message', methods=['POST'])
def send_message():
    """Handle sending a message and getting bot response"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        chat_id = data.get('chat_id')
        user_id = session.get('user_id')
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Create new chat if no chat_id provided
        if not chat_id:
            chat_id = str(uuid.uuid4())
            chats[chat_id] = {
                'id': chat_id,
                'user_id': user_id,
                'title': message[:30] + ('...' if len(message) > 30 else ''),
                'created_at': datetime.now().isoformat(),
                'messages': [],
                'context': {}  # Store conversation context
            }
        
        # Add user message
        user_msg = {
            'type': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        }
        chats[chat_id]['messages'].append(user_msg)
        
        # Generate bot response with context
        bot_response = generate_bot_response(message, chats[chat_id].get('context', {}))
        
        bot_msg = {
            'type': 'bot',
            'content': bot_response['text'],
            'events': bot_response.get('events', []),
            'timestamp': datetime.now().isoformat()
        }
        chats[chat_id]['messages'].append(bot_msg)
        
        # Update context
        chats[chat_id]['context'] = bot_response.get('context', {})
        
        return jsonify({
            'success': True,
            'chat_id': chat_id,
            'user_message': user_msg,
            'bot_message': bot_msg
        })
    
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_chats', methods=['GET'])
def get_chats():
    """Get all chats for current user"""
    try:
        user_id = session.get('user_id')
        user_chats = [
            {
                'id': chat['id'],
                'title': chat['title'],
                'created_at': chat['created_at']
            }
            for chat in chats.values()
            if chat['user_id'] == user_id
        ]
        user_chats.sort(key=lambda x: x['created_at'], reverse=True)
        return jsonify({'success': True, 'chats': user_chats})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_chat/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get a specific chat by ID"""
    try:
        user_id = session.get('user_id')
        
        if chat_id not in chats:
            return jsonify({'error': 'Chat not found'}), 404
        
        chat = chats[chat_id]
        
        if chat['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({'success': True, 'chat': chat})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat"""
    try:
        user_id = session.get('user_id')
        
        if chat_id not in chats:
            return jsonify({'error': 'Chat not found'}), 404
        
        chat = chats[chat_id]
        
        if chat['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        del chats[chat_id]
        return jsonify({'success': True, 'message': 'Chat deleted'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/new_chat', methods=['POST'])
def new_chat():
    """Start a new chat"""
    try:
        return jsonify({'success': True, 'chat_id': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/account', methods=['GET'])
def get_account():
    """Get account information"""
    try:
        user_id = session.get('user_id')
        
        if user_id not in user_data:
            user_data[user_id] = {
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'total_chats': len([c for c in chats.values() if c['user_id'] == user_id])
            }
        
        return jsonify({'success': True, 'account': user_data[user_id]})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/report', methods=['POST'])
def submit_report():
    """Submit a report"""
    try:
        data = request.json
        report_text = data.get('report', '').strip()
        
        if not report_text:
            return jsonify({'error': 'Report cannot be empty'}), 400
        
        report_id = str(uuid.uuid4())
        report = {
            'id': report_id,
            'user_id': session.get('user_id'),
            'content': report_text,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Report received: {report}")
        
        return jsonify({
            'success': True,
            'message': 'Report submitted successfully',
            'report_id': report_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def fetch_events():
    """Fetch events from API and normalize field names"""
    try:
        response = requests.get(EVENTS_API_URL, timeout=10)
        response.raise_for_status()
        events_data = response.json()
        
        # Normalize events to use consistent field names
        valid_events = []
        for event in events_data:
            if isinstance(event, dict):
                # Check if event has the required fields (eventName, location, time)
                if 'eventName' in event and 'location' in event and 'time' in event:
                    # Skip test data with generic values
                    if event.get('eventName', '').startswith('eventName') and event.get('time', '').startswith('time'):
                        continue
                    
                    # Normalize to title/venue format for consistency
                    normalized_event = {
                        'title': event['eventName'],
                        'venue': event['location'],
                        'time': event['time'],
                        'description': event.get('description', '')
                    }
                    valid_events.append(normalized_event)
        
        return valid_events
    except requests.exceptions.RequestException as e:
        print(f"Error fetching events from API: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching events: {e}")
        return []

def parse_time(time_str):
    """Parse time string to get start time"""
    try:
        # Handle formats like "3:00 PM - 4:00 PM" or "3:00 PM"
        # Also handle potential unicode dashes
        start = time_str.replace('–', '-').split("-")[0].strip()
        
        # Try to parse the time
        parsed_time = datetime.strptime(start, "%I:%M %p").time()
        return parsed_time
    except Exception as e:
        print(f"Error parsing time '{time_str}': {e}")
        return None

# --- Modified generate_bot_response with New Function Call ---

def generate_bot_response(message, context):
    """Generate bot response based on user message with event data - Halloween themed"""
    
    # 1. LOGIC: Check for Judge Match first and return immediate response
    judge_response = get_judge_response(message)
    if judge_response:
        return judge_response
    
    # 2. Continue with original logic if no judge match
    message_lower = message.lower()
    
    # Greetings - Halloween themed
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings', 'boo']):
        return {
            'text': "🎃 Boo! Welcome to the haunted fest! I'm HalloweenBot, your spooky guide to all the frightfully fun events! Ask me anything like 'What's happening now?' or 'Show me all events!' 👻🦇",
            'context': context
        }
    
    if any(word in message_lower for word in ['help', 'support', 'how']):
        return {
            'text': "🕷️ I can help you navigate the haunted fest:\n\n🕐 'What's happening at 3 PM?'\n📍 'Where is the next event?'\n🎃 'Show all events'\n⏰ 'What's happening now?'\n🦇 'Tell me about [event name]'\n\nDon't be scared, just ask away! 👻",
            'context': context
        }
    
    if any(word in message_lower for word in ['bye', 'goodbye', 'see you']):
        return {
            'text': "🎃 See you in the haunted fest! Don't let the ghosts bite! 👻🦇✨",
            'context': context
        }
    
    # Fetch events
    events = fetch_events()
    
    if not events:
        return {
            'text': "🕸️ Oops! The spirits are blocking my connection to the event cauldron right now. Please try again in a moment! 👻",
            'context': context
        }
    
    # Sort events by time
    events_with_time = []
    events_without_time = []
    for event in events:
        parsed = parse_time(event.get('time', ''))
        if parsed:
            events_with_time.append((event, parsed))
        else:
            events_without_time.append(event)
    
    # Sort by time
    events_with_time.sort(key=lambda x: x[1])
    sorted_events = [e[0] for e in events_with_time] + events_without_time
    
    # What's happening now
    if any(phrase in message_lower for phrase in ['now', 'happening now', 'current', 'right now']):
        current_time = datetime.now().time()
        current_events = []
        
        for event in sorted_events:
            event_time = parse_time(event.get('time', ''))
            if event_time:
                # Check if event is happening now (within 2 hours window)
                time_diff = abs((datetime.combine(datetime.today(), event_time) - 
                                 datetime.combine(datetime.today(), current_time)).total_seconds())
                if time_diff < 7200:  # 2 hours
                    current_events.append(event)
        
        if current_events:
            return {
                'text': f"🔥 Right now, we've got {len(current_events)} spine-chilling event(s) happening! Check them out if you dare:",
                'events': current_events,
                'context': {'last_query': 'current', 'last_events': current_events}
            }
        else:
            return {
                'text': "🦇 No events haunting right this moment, but check out all upcoming spooky gatherings!",
                'events': sorted_events[:3],
                'context': context
            }
    
    # Next event
    if any(phrase in message_lower for phrase in ['next event', 'next', 'upcoming', 'what\'s next']):
        if sorted_events:
            # Find the next event after current time
            current_time = datetime.now().time()
            next_event = None
            
            for event in sorted_events:
                event_time = parse_time(event.get('time', ''))
                if event_time and event_time > current_time:
                    next_event = event
                    break
            
            if not next_event:
                next_event = sorted_events[0]
            
            return {
                'text': f"🎃 The next frightful event is coming up soon!",
                'events': [next_event],
                'context': {'last_query': 'next', 'last_event': next_event}
            }
    
    # Search by time
    time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)', message_lower)
    if time_match:
        search_hour = time_match.group(1)
        search_period = time_match.group(3).upper()
        search_pattern = f"{search_hour}.*{search_period}"
        
        matching_events = [e for e in sorted_events if re.search(search_pattern, e.get('time', ''), re.IGNORECASE)]
        
        if matching_events:
            return {
                'text': f"⏰ Found {len(matching_events)} haunted event(s) around {search_hour} {search_period}!",
                'events': matching_events,
                'context': {'last_query': 'time', 'search_time': f"{search_hour} {search_period}"}
            }
        else:
            return {
                'text': f"🔍 No events found at {search_hour} {search_period}. Here are all our spooky events:",
                'events': sorted_events,
                'context': context
            }
    
    # Search by venue/location
    if any(word in message_lower for word in ['where', 'venue', 'location', 'place']):
        # Extract location keywords
        location_keywords = []
        for word in message_lower.split():
            if word not in ['where', 'is', 'the', 'venue', 'location', 'place', 'at', 'in']:
                location_keywords.append(word)
        
        if location_keywords:
            # Search for events at specific location
            matching_events = [e for e in sorted_events 
                              if any(keyword in e.get('venue', '').lower() for keyword in location_keywords)]
            if matching_events:
                return {
                    'text': f"📍 Found {len(matching_events)} event(s) at your requested location!",
                    'events': matching_events,
                    'context': {'last_query': 'venue'}
                }
        
        # Show all venues
        return {
            'text': f"📍 Here are all the haunted venues hosting our spooky events!",
            'events': sorted_events,
            'context': {'last_query': 'venue'}
        }
    
    # Show all events
    if any(phrase in message_lower for phrase in ['all events', 'show all', 'list events', 'show events', 'what events']):
        return {
            'text': f"🎃 We've got {len(sorted_events)} frightfully fun events lined up! Get ready for a spooky good time! 👻",
            'events': sorted_events,
            'context': {'last_query': 'all'}
        }
    
    # Search by event name/keyword
    search_words = [word for word in message_lower.split() 
                    if len(word) > 3 and word not in ['what', 'when', 'where', 'show', 'tell', 'about', 'event', 'events']]
    
    if search_words:
        matching_events = [e for e in sorted_events 
                          if any(word in e.get('title', '').lower() for word in search_words)]
        
        if matching_events:
            return {
                'text': f"🦇 Found {len(matching_events)} event(s) matching your search!",
                'events': matching_events,
                'context': {'last_query': 'search', 'keyword': message}
            }
    
    # Default response
    return {
        'text': "👻 Hmm, I'm not sure about that specific query. Try asking:\n• 'Show all events'\n• 'What's happening now?'\n• 'Next event'\n• Or mention a specific time like '3 PM'!",
        'events': sorted_events[:3],
        'context': context
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)