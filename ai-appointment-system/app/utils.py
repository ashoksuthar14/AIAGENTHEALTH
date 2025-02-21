import google.generativeai as genai
from config import Config
import json
import random
from flask_babel import _
from datetime import datetime

# Add language translations
TRANSLATIONS = {
    'en': {
        'name_q': 'What is your full name?',
        'contact_q': 'What is your contact number?',
        'email_q': 'What is your email address?',
        'location_q': 'What is your location/address?',
        'specialization_q': 'What is your specialization?',
        'hours_q': 'Please provide your available working hours (e.g., Mon-Fri 9AM-5PM):',
        'concern_q': 'What is your medical concern/required specialization?',
        'time_q': 'Please select your preferred appointment time.',
        'complete': 'Thank you for registering! You can now receive appointment requests.',
        'match_search': 'Thank you! I will now look for available technicians matching your requirements.'
    },
    'es': {
        'name_q': '¿Cuál es su nombre completo?',
        'contact_q': '¿Cuál es su número de contacto?',
        'email_q': '¿Cuál es su dirección de correo electrónico?',
        'location_q': '¿Cuál es su ubicación/dirección?',
        'specialization_q': '¿Cuál es su especialización?',
        'hours_q': 'Por favor, indique su horario disponible (ej. Lun-Vie 9AM-5PM):',
        'concern_q': '¿Cuál es su problema médico/especialización requerida?',
        'time_q': 'Por favor, seleccione su hora de cita preferida.',
        'complete': '¡Gracias por registrarse! Ahora puede recibir solicitudes de citas.',
        'match_search': '¡Gracias! Ahora buscaré técnicos disponibles que coincidan con sus requisitos.'
    }
}

def get_text(key, lang='en'):
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, TRANSLATIONS['en'][key])

def get_gemini_suggestion(concern, preferred_time):
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""As a healthcare expert, suggest a suitable medical professional for:
        Medical concern: {concern}
        Appointment time: {preferred_time}
        
        Respond in this exact JSON format:
        {{
            "name": "Dr. [Full Name]",
            "specialization": "[Most relevant specialization]",
            "location": "[One of: Manhattan Medical Center, Brooklyn Health Hub, Queens Medical Plaza, Bronx Care Center, Staten Island Medical]"
        }}
        """
        
        response = model.generate_content(prompt)
        suggestion = json.loads(response.text)
        
        # Validate required fields
        required_fields = ['name', 'specialization', 'location']
        if all(field in suggestion for field in required_fields):
            return suggestion
        else:
            raise ValueError("Missing required fields in suggestion")
            
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        # Fallback suggestion if API fails
        return {
            'name': f"Dr. {random.choice(['Sarah Johnson', 'Michael Chen', 'Emily Rodriguez'])}",
            'specialization': 'General Health Checkup',
            'location': random.choice([
                'Manhattan Medical Center',
                'Brooklyn Health Hub',
                'Queens Medical Plaza',
                'Bronx Care Center',
                'Staten Island Medical'
            ])
        }

def get_next_question(current_step, user_type, user_data):
    name = user_data.get('name', '')
    lang = user_data.get('language', 'en')
    
    questions = {
        'name': {
            'patient': f"Nice to meet you! Could you please share your contact number so I can reach you if needed?"
        },
        'contact': {
            'patient': "Great! And what's your email address?"
        },
        'email': {
            'patient': "Thanks! To help find a nearby provider, what's your location or preferred area for the appointment?"
        },
        'location': {
            'patient': f"Thank you {name}! Could you tell me what brings you in today? Please describe your medical concern or the type of care you're looking for."
        },
        'concern': {
            'patient': "I understand. Let's find you an appointment. When would be the best time for you?"
        },
        'preferred_time': {
            'patient': f"Perfect! I'll search for the best healthcare provider matching your needs, {name}."
        }
    }
    
    return questions.get(current_step, {}).get(user_type)

def process_appointment_request(user_input, user_type, current_step, user_data):
    user_data[current_step] = user_input
    
    next_step = {
        'name': 'contact',
        'contact': 'email',
        'email': 'location',
        'location': 'concern',
        'concern': 'preferred_time',
        'preferred_time': 'complete'
    }.get(current_step, 'complete')
    
    next_question = get_next_question(current_step, user_type, user_data)
    show_calendar = current_step == 'concern'
    
    return {
        'response': next_question,
        'next_step': next_step,
        'user_data': user_data,
        'show_calendar': show_calendar
    }