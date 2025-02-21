from flask import Blueprint, render_template, request, jsonify, session
from app.models import Patient, Technician, Appointment, Availability
from app.utils import process_appointment_request, get_gemini_suggestion
from app import db
from datetime import datetime, time
from sqlalchemy import func
import random
import google.generativeai as genai
from config import Config

main = Blueprint('main', __name__)

def is_time_slot_available(slot, preferred_time):
    try:
        preferred_datetime = datetime.strptime(preferred_time, '%Y-%m-%d %H:%M')
        slot_day = slot.day_of_week
        preferred_day = preferred_datetime.weekday() + 1  # Adding 1 to match our day_of_week format
        
        if slot_day != preferred_day:
            return False
            
        preferred_time = preferred_datetime.time()
        return slot.start_time <= preferred_time <= slot.end_time
    except Exception as e:
        print(f"Error checking time slot: {e}")
        return False

def initialize_technicians():
    if Technician.query.first() is not None:
        return

    technicians_data = [
        {
            "name": "Dr. Sarah Johnson",
            "email": "sarah.j@healthcare.com",
            "phone": "555-0101",
            "location": "Manhattan Medical Center",
            "specialization": "Cardiology",
            "hours": [(1, "09:00", "17:00"), (2, "09:00", "17:00"), (3, "09:00", "17:00")]
        },
        {
            "name": "Dr. Michael Chen",
            "email": "m.chen@healthcare.com",
            "phone": "555-0102",
            "location": "Brooklyn Health Hub",
            "specialization": "Orthopedics",
            "hours": [(1, "08:00", "16:00"), (3, "08:00", "16:00"), (5, "08:00", "16:00")]
        },
        {
            "name": "Dr. Emily Rodriguez",
            "email": "e.rodriguez@healthcare.com",
            "phone": "555-0103",
            "location": "Queens Medical Plaza",
            "specialization": "Neurology",
            "hours": [(2, "10:00", "18:00"), (4, "10:00", "18:00"), (6, "10:00", "16:00")]
        },
        {
            "name": "Dr. James Wilson",
            "email": "j.wilson@healthcare.com",
            "phone": "555-0104",
            "location": "Bronx Care Center",
            "specialization": "Pediatrics",
            "hours": [(1, "09:00", "17:00"), (3, "09:00", "17:00"), (5, "09:00", "15:00")]
        },
        {
            "name": "Dr. Lisa Patel",
            "email": "l.patel@healthcare.com",
            "phone": "555-0105",
            "location": "Staten Island Medical",
            "specialization": "Dermatology",
            "hours": [(2, "08:30", "16:30"), (4, "08:30", "16:30"), (6, "09:00", "14:00")]
        },
        {
            "name": "Dr. Robert Kim",
            "email": "r.kim@healthcare.com",
            "phone": "555-0106",
            "location": "Manhattan Medical Center",
            "specialization": "Ophthalmology",
            "hours": [(1, "09:00", "17:00"), (2, "09:00", "17:00"), (4, "09:00", "17:00")]
        },
        {
            "name": "Dr. Maria Santos",
            "email": "m.santos@healthcare.com",
            "phone": "555-0107",
            "location": "Brooklyn Health Hub",
            "specialization": "Cardiology",
            "hours": [(2, "08:00", "16:00"), (4, "08:00", "16:00"), (6, "08:00", "14:00")]
        },
        {
            "name": "Dr. David Cohen",
            "email": "d.cohen@healthcare.com",
            "phone": "555-0108",
            "location": "Queens Medical Plaza",
            "specialization": "Orthopedics",
            "hours": [(1, "10:00", "18:00"), (3, "10:00", "18:00"), (5, "10:00", "18:00")]
        },
        {
            "name": "Dr. Anna Lee",
            "email": "a.lee@healthcare.com",
            "phone": "555-0109",
            "location": "Bronx Care Center",
            "specialization": "Neurology",
            "hours": [(2, "09:00", "17:00"), (4, "09:00", "17:00"), (6, "09:00", "15:00")]
        },
        {
            "name": "Dr. Thomas Brown",
            "email": "t.brown@healthcare.com",
            "phone": "555-0110",
            "location": "Staten Island Medical",
            "specialization": "Pediatrics",
            "hours": [(1, "08:30", "16:30"), (3, "08:30", "16:30"), (5, "08:30", "16:30")]
        },
        {
            "name": "Dr. Rachel Green",
            "email": "r.green@healthcare.com",
            "phone": "555-0111",
            "location": "Manhattan Lab Center",
            "specialization": "Blood Tests",
            "hours": [(1, "07:00", "19:00"), (2, "07:00", "19:00"), (3, "07:00", "19:00")]
        },
        {
            "name": "Dr. Alex Turner",
            "email": "a.turner@healthcare.com",
            "phone": "555-0112",
            "location": "Brooklyn Diagnostic Hub",
            "specialization": "X-Ray & Imaging",
            "hours": [(1, "08:00", "20:00"), (3, "08:00", "20:00"), (5, "08:00", "20:00")]
        },
        {
            "name": "Dr. Maya Patel",
            "email": "m.patel@healthcare.com",
            "phone": "555-0113",
            "location": "Queens Lab Services",
            "specialization": "Pathology",
            "hours": [(2, "07:00", "19:00"), (4, "07:00", "19:00"), (6, "07:00", "15:00")]
        },
        {
            "name": "Dr. John Smith",
            "email": "j.smith@healthcare.com",
            "phone": "555-0114",
            "location": "Bronx Diagnostic Center",
            "specialization": "General Health Checkup",
            "hours": [(1, "09:00", "18:00"), (3, "09:00", "18:00"), (5, "09:00", "18:00")]
        },
        {
            "name": "Dr. Sarah Miller",
            "email": "s.miller@healthcare.com",
            "phone": "555-0115",
            "location": "Staten Island Lab",
            "specialization": "ECG & Cardiac Tests",
            "hours": [(2, "08:00", "17:00"), (4, "08:00", "17:00"), (6, "08:00", "14:00")]
        }
    ]

    for tech_data in technicians_data:
        technician = Technician(
            name=tech_data["name"],
            email=tech_data["email"],
            phone=tech_data["phone"],
            location=tech_data["location"],
            specialization=tech_data["specialization"]
        )
        db.session.add(technician)
        db.session.flush()  # Get ID without committing

        # Add availability
        for day, start, end in tech_data["hours"]:
            availability = Availability(
                technician_id=technician.id,
                day_of_week=day,
                start_time=datetime.strptime(start, "%H:%M").time(),
                end_time=datetime.strptime(end, "%H:%M").time()
            )
            db.session.add(availability)

    db.session.commit()

@main.route('/')
def home():
    today_date = datetime.now().strftime('%Y-%m-%d')
    initialize_technicians()
    return render_template('chat.html', today_date=today_date)

@main.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_input = data.get('message')
        user_type = data.get('user_type', 'patient')
        current_step = data.get('current_step', 'initial')  # Add default step
        user_data = data.get('user_data', {})
        
        print(f"Received chat request: {data}")  # Debug log
        
        # Process the response
        response = process_appointment_request(user_input, user_type, current_step, user_data)
        
        # Use Gemini API for natural conversation
        if response.get('response'):
            genai.configure(api_key=Config.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            chat_prompt = f"""
            As a friendly healthcare assistant, make this response more conversational:
            Original: {response['response']}
            User's name: {user_data.get('name', '')}
            Current step: {current_step}
            """
            enhanced_response = model.generate_content(chat_prompt).text
            response['response'] = enhanced_response.strip()
        
        print(f"Sending response: {response}")  # Debug log
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in chat route: {str(e)}")
        return jsonify({
            'response': "I apologize, but I'm having trouble processing your request. Could you please try again?",
            'next_step': current_step,
            'user_data': user_data
        })

@main.route('/get-random-technician', methods=['POST'])
def get_random_technician():
    data = request.json
    
    # Get a random technician
    technician = Technician.query.order_by(func.random()).first()
    
    # Get their availability
    availability = Availability.query.filter_by(technician_id=technician.id).first()
    
    return jsonify({
        'name': technician.name,
        'specialization': technician.specialization,
        'location': technician.location,
        'available_time': f"{availability.start_time} - {availability.end_time}"
    })

@main.route('/find-match', methods=['POST'])
def find_match():
    try:
        data = request.json
        concern = data.get('concern', '').lower()
        preferred_time = data.get('preferred_time')
        
        # Try database match first
        matching_technicians = Technician.query.filter(
            func.lower(Technician.specialization).contains(concern)
        ).all()
        
        matches = []
        if matching_technicians:
            for tech in matching_technicians:
                availability = Availability.query.filter_by(technician_id=tech.id).all()
                for slot in availability:
                    if is_time_slot_available(slot, preferred_time):
                        matches.append({
                            'name': tech.name,
                            'specialization': tech.specialization,
                            'location': tech.location,
                            'available_time': f"{slot.start_time} - {slot.end_time}"
                        })
                        break
        
        # If no matches found, use Gemini API to suggest alternatives
        if not matches:
            suggested_match = get_gemini_suggestion(concern, preferred_time)
            if suggested_match:
                # Check if technician with similar email already exists
                email = f"{suggested_match['name'].lower().replace(' ', '.')}@healthcare.com"
                existing_tech = Technician.query.filter_by(email=email).first()
                
                if existing_tech:
                    # Use existing technician if found
                    matches.append({
                        'name': existing_tech.name,
                        'specialization': existing_tech.specialization,
                        'location': existing_tech.location,
                        'available_time': "09:00 - 17:00",
                        'ai_suggested': True
                    })
                else:
                    # Create new technician with unique email
                    email_base = email.split('@')[0]
                    count = 1
                    while Technician.query.filter_by(email=email).first():
                        email = f"{email_base}{count}@healthcare.com"
                        count += 1
                    
                    new_tech = Technician(
                        name=suggested_match['name'],
                        email=email,
                        phone=f"555-{str(random.randint(1000,9999))}",
                        location=suggested_match['location'],
                        specialization=suggested_match['specialization']
                    )
                    db.session.add(new_tech)
                    db.session.flush()
        
                    # Add availability
                    availability = Availability(
                        technician_id=new_tech.id,
                        day_of_week=datetime.strptime(preferred_time, '%Y-%m-%d %H:%M').weekday() + 1,
                        start_time=datetime.strptime("09:00", "%H:%M").time(),
                        end_time=datetime.strptime("17:00", "%H:%M").time()
                    )
                    db.session.add(availability)
                    db.session.commit()
        
                    matches.append({
                        'name': new_tech.name,
                        'specialization': new_tech.specialization,
                        'location': new_tech.location,
                        'available_time': "09:00 - 17:00",
                        'ai_suggested': True
                    })
        
        return jsonify({'matches': matches})
        
    except Exception as e:
        print(f"Error in find_match: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to find matches'}), 500
@main.route('/confirm-booking', methods=['POST'])
def confirm_booking():
    try:
        data = request.json
        selected_index = data.get('selected_index')
        user_data = data.get('user_data')
        matches = data.get('matches')
        
        if not all([selected_index, user_data, matches]) or selected_index > len(matches):
            return jsonify({'error': 'Invalid selection'}), 400
        
        selected_match = matches[selected_index - 1]
        
        # Create or get patient
        patient = Patient.query.filter_by(email=user_data.get('email')).first()
        if not patient:
            patient = Patient(
                name=user_data.get('name'),
                email=user_data.get('email'),
                phone=user_data.get('contact'),
                location=user_data.get('location')
            )
            db.session.add(patient)
        
        # Get technician
        technician = Technician.query.filter_by(name=selected_match['name']).first()
        
        # Create appointment
        appointment = Appointment(
            patient_id=patient.id,
            technician_id=technician.id,
            datetime=datetime.strptime(user_data.get('preferred_time'), '%Y-%m-%d %H:%M'),
            notes=f"Medical concern: {user_data.get('concern')}"
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment booked successfully!',
            'details': {
                'technician': technician.name,
                'date_time': user_data.get('preferred_time'),
                'location': technician.location
            }
        })
        
    except Exception as e:
        print(f"Error in confirm booking: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to book appointment'}), 500