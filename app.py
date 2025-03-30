import streamlit as st
import sqlite3
import os
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from datetime import datetime
import secrets
import re
import time

# Set sqlite connection timeout to avoid database locked errors
sqlite3.connect(':memory:', timeout=30)

# Set page config
st.set_page_config(
    page_title="ClaudeNation ID System",
    page_icon="🌈",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize database
def init_db():
    conn = sqlite3.connect('claudenation.db', timeout=30)
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS pending_registrations (
        email TEXT PRIMARY KEY,
        token TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        verified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS citizens (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        full_name TEXT NOT NULL,
        date_of_birth TEXT NOT NULL,
        id_number TEXT UNIQUE NOT NULL,
        theme TEXT DEFAULT 'light',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (email) REFERENCES users(email)
    )
    ''')
    
    # Create ID counter if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS id_counter (
        id INTEGER PRIMARY KEY,
        last_id INTEGER DEFAULT 0
    )
    ''')
    
    # Initialize counter if empty
    c.execute('SELECT COUNT(*) FROM id_counter')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO id_counter (last_id) VALUES (0)')
    
    conn.commit()
    conn.close()

# Initialize session state
def init_session():
    # Use a dictionary to define all session state variables
    default_values = {
        'user_email': None,
        'user_verified': False,
        'user_registered': False,
        'current_step': 'welcome',
        'id_created': False,
        'id_card_image': None,
        'form_key': 0  # Used to create unique keys for forms
    }
    
    # Initialize each session state variable if not present
    for key, default_value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Load images
@st.cache_data
def load_images():
    light_theme = Image.open('claudenation01light.jpg')
    dark_theme = Image.open('claudenation02dark.jpg')
    return light_theme, dark_theme

# Email validation
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

# Generate verification token
def generate_token():
    return secrets.token_urlsafe(32)

# Register email and send verification link (simulated)
def register_email(email):
    conn = sqlite3.connect('claudenation.db', timeout=30)
    c = conn.cursor()
    
    # Check if email already registered and verified
    c.execute('SELECT verified FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    
    if result and result[0] == 1:
        conn.close()
        return False, "This email is already registered and verified."
    
    # Generate verification token
    token = generate_token()
    
    # Add to pending registrations
    try:
        c.execute('INSERT OR REPLACE INTO pending_registrations (email, token) VALUES (?, ?)',
                  (email, token))
        
        # Add to users if not exists
        c.execute('INSERT OR IGNORE INTO users (email) VALUES (?)', (email,))
        
        conn.commit()
        conn.close()
        
        # In a real app, send email with token
        # For simulation, we'll just return the token
        verification_link = f"?email={email}&token={token}"
        return True, verification_link
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error: {str(e)}"

# Verify email with token
def verify_email(email, token):
    conn = sqlite3.connect('claudenation.db', timeout=30)
    c = conn.cursor()
    
    # Check token
    c.execute('SELECT token FROM pending_registrations WHERE email = ?', (email,))
    result = c.fetchone()
    
    if not result or result[0] != token:
        conn.close()
        return False
    
    # Update user as verified
    c.execute('UPDATE users SET verified = 1 WHERE email = ?', (email,))
    
    # Clean up pending registration
    c.execute('DELETE FROM pending_registrations WHERE email = ?', (email,))
    
    conn.commit()
    conn.close()
    return True

# Login user
def login_user(email):
    conn = sqlite3.connect('claudenation.db', timeout=30)
    c = conn.cursor()
    
    # Check if user exists and is verified
    c.execute('SELECT verified FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return False, "Email not registered."
    
    if result[0] == 0:
        conn.close()
        return False, "Email not verified."
    
    # Check if user already has an ID
    c.execute('SELECT id FROM citizens WHERE email = ?', (email,))
    citizen = c.fetchone()
    
    conn.close()
    
    if citizen:
        st.session_state.user_registered = True
    
    return True, None

# Generate next ID number
def generate_id_number():
    conn = sqlite3.connect('claudenation.db', timeout=30)
    c = conn.cursor()
    
    # Start transaction to safely increment counter
    c.execute('BEGIN TRANSACTION')
    c.execute('SELECT last_id FROM id_counter WHERE id = 1')
    last_id = c.fetchone()[0]
    new_id = last_id + 1
    c.execute('UPDATE id_counter SET last_id = ? WHERE id = 1', (new_id,))
    conn.commit()
    
    # Format as 10-digit number with leading zeros
    id_number = f"{new_id:010d}"
    
    conn.close()
    return id_number

# Register citizen
def register_citizen(email, full_name, date_of_birth, theme):
    # Generate ID number
    id_number = generate_id_number()
    
    conn = sqlite3.connect('claudenation.db', timeout=30)
    c = conn.cursor()
    
    try:
        c.execute('''
        INSERT INTO citizens (email, full_name, date_of_birth, id_number, theme)
        VALUES (?, ?, ?, ?, ?)
        ''', (email, full_name, date_of_birth, id_number, theme))
        
        conn.commit()
        conn.close()
        return True, id_number
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

# Get citizen data
def get_citizen_data(email):
    conn = sqlite3.connect('claudenation.db', timeout=30)
    c = conn.cursor()
    
    c.execute('''
    SELECT full_name, date_of_birth, id_number, theme
    FROM citizens WHERE email = ?
    ''', (email,))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'full_name': result[0],
            'date_of_birth': result[1],
            'id_number': result[2],
            'theme': result[3]
        }
    return None

# Generate ID card
def generate_id_card(full_name, date_of_birth, id_number, photo, theme='light'):
    light_theme, dark_theme = load_images()
    
    # Choose base image based on theme
    if theme == 'dark':
        base_img = dark_theme.copy()
    else:
        base_img = light_theme.copy()
    
    # Resize image to ID card dimensions
    base_img = base_img.resize((800, 500))
    draw = ImageDraw.Draw(base_img)
    
    # Try to load fonts, use default if not available
    try:
        name_font = ImageFont.truetype("arial.ttf", 36)
        info_font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        name_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
    
    # Adjust text color based on theme
    text_color = (255, 255, 255) if theme == 'dark' else (0, 0, 0)
    
    # Add ID information
    y_offset = 300
    draw.text((50, y_offset), f"Name: {full_name}", text_color, font=name_font)
    draw.text((50, y_offset + 50), f"DOB: {date_of_birth}", text_color, font=info_font)
    draw.text((50, y_offset + 100), f"ID#: {id_number}", text_color, font=info_font)
    
    # Add current date as issue date
    issue_date = datetime.now().strftime('%Y-%m-%d')
    draw.text((50, y_offset + 150), f"Issued: {issue_date}", text_color, font=info_font)
    
    # If photo provided, add it to the card
    if photo is not None:
        try:
            # Open and process uploaded photo
            user_img = Image.open(photo)
            user_img = user_img.resize((150, 150))
            
            # Paste photo onto card (position depends on theme)
            photo_pos = (600, 300) if theme == 'dark' else (600, 300)
            base_img.paste(user_img, photo_pos)
        except Exception as e:
            st.error(f"Error processing photo: {e}")
    
    # Return image as bytes for display
    buffered = io.BytesIO()
    base_img.save(buffered, format="JPEG")
    return buffered.getvalue()

# Create download link for image
def get_image_download_link(img, filename, text):
    b64 = base64.b64encode(img).decode()
    href = f'<a href="data:file/jpg;base64,{b64}" download="{filename}">**{text}**</a>'
    return href

# Main app
def main():
    init_db()
    init_session()
    
    # Check for verification parameters in URL
    params = st.query_params
    if 'email' in params and 'token' in params:
        email = params['email']
        token = params['token']
        if verify_email(email, token):
            st.session_state.user_email = email
            st.session_state.user_verified = True
            st.session_state.current_step = 'profile'
            st.query_params.clear()
    
    # Display header
    st.title("ClaudeNation ID System")
    
    # Process based on current step
    if st.session_state.current_step == 'welcome':
        show_welcome_screen()
    elif st.session_state.current_step == 'login':
        show_login_screen()
    elif st.session_state.current_step == 'register':
        show_register_screen()
    elif st.session_state.current_step == 'verify':
        show_verification_screen()
    elif st.session_state.current_step == 'profile':
        show_profile_screen()
    elif st.session_state.current_step == 'id_card':
        show_id_card_screen()
    
    # Footer
    st.markdown("---")
    st.markdown("ClaudeNation - The First AI-Governed Digital Nation")

# Welcome screen
def show_welcome_screen():
    st.markdown("""
    ## Welcome to ClaudeNation
    The world's first AI-governed digital nation, led by Claude AI as president.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Login", use_container_width=True):
            st.session_state.current_step = 'login'
            st.rerun()
    
    with col2:
        if st.button("Register", use_container_width=True):
            st.session_state.current_step = 'register'
            st.rerun()
    
    # Show images of both themes
    light_theme, dark_theme = load_images()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(light_theme, caption="Light Theme ID Card", use_container_width=True)
    
    with col2:
        st.image(dark_theme, caption="Dark Theme ID Card", use_container_width=True)

# Login screen
def show_login_screen():
    st.markdown("## Login to ClaudeNation")
    
    # Use form to prevent rerun issues
    with st.form(key=f"login_form_{st.session_state.form_key}"):
        email = st.text_input("Email Address")
        submit_button = st.form_submit_button("Login")
    
    if submit_button:
        if not is_valid_email(email):
            st.error("Please enter a valid email address.")
            return
        
        success, error = login_user(email)
        if success:
            st.session_state.user_email = email
            st.session_state.user_verified = True
            
            # Check if user has registered profile
            citizen_data = get_citizen_data(email)
            if citizen_data:
                st.session_state.user_registered = True
                st.session_state.current_step = 'id_card'
            else:
                st.session_state.current_step = 'profile'
            
            st.rerun()
        else:
            st.error(error)
    
    if st.button("← Back"):
        st.session_state.current_step = 'welcome'
        st.rerun()

# Registration screen
def show_register_screen():
    st.markdown("## Register for ClaudeNation Citizenship")
    
    # Use form to prevent rerun issues
    with st.form(key=f"register_form_{st.session_state.form_key}"):
        email = st.text_input("Email Address")
        submit_button = st.form_submit_button("Register")
    
    if submit_button:
        if not is_valid_email(email):
            st.error("Please enter a valid email address.")
            return
        
        success, result = register_email(email)
        if success:
            st.session_state.user_email = email
            st.session_state.current_step = 'verify'
            
            # In a real app, we would send an email
            # For demo, show verification link
            st.info("Verification email sent! Check your inbox.")
            st.code(f"Verification Link (for demo): {result}")
            
            st.rerun()
        else:
            st.error(result)
    
    if st.button("← Back"):
        st.session_state.current_step = 'welcome'
        st.rerun()

# Verification screen
def show_verification_screen():
    st.markdown("## Verify Your Email")
    
    st.info(f"A verification link has been sent to {st.session_state.user_email}")
    st.markdown("For this demo, you can manually verify:")
    
    if st.button("Simulate Email Verification"):
        # For demo purposes, auto-verify
        st.session_state.user_verified = True
        
        # Update database to mark as verified
        conn = sqlite3.connect('claudenation.db')
        c = conn.cursor()
        c.execute('UPDATE users SET verified = 1 WHERE email = ?', (st.session_state.user_email,))
        conn.commit()
        conn.close()
        
        st.session_state.current_step = 'profile'
        st.rerun()
    
    if st.button("← Back"):
        st.session_state.current_step = 'welcome'
        st.rerun()

# Profile completion screen
def show_profile_screen():
    st.markdown("## Complete Your Citizen Profile")
    
    # Use form to prevent rerun issues
    with st.form(key=f"profile_form_{st.session_state.form_key}"):
        full_name = st.text_input("Full Name")
        dob = st.date_input("Date of Birth", min_value=datetime(1900, 1, 1))
        
        # Theme selection
        theme = st.radio(
            "Select ID Card Theme",
            ["Light Theme", "Dark Theme"],
            horizontal=True
        )
        
        # Photo upload
        st.markdown("### Upload Photo for ID Card")
        photo = st.file_uploader("Choose photo...", type=['jpg', 'jpeg', 'png'])
        
        submit_button = st.form_submit_button("Create ID Card")
    
    selected_theme = "light" if theme == "Light Theme" else "dark"
    
    if submit_button:
        if not full_name:
            st.error("Please enter your full name")
            return
        
        # Format date as string
        date_of_birth = dob.strftime("%Y-%m-%d")
        
        # Register citizen in database
        success, id_number = register_citizen(
            st.session_state.user_email,
            full_name,
            date_of_birth,
            selected_theme
        )
        
        if success:
            # Generate ID card with photo if provided
            id_card = generate_id_card(
                full_name,
                date_of_birth,
                id_number,
                photo,
                selected_theme
            )
            
            # Store in session state for display
            st.session_state.id_card_image = id_card
            st.session_state.id_created = True
            st.session_state.current_step = 'id_card'
            st.rerun()
        else:
            st.error(f"Error creating ID: {id_number}")

# ID Card display screen
def show_id_card_screen():
    st.markdown("## Your ClaudeNation ID Card")
    
    # If ID was just created, display from session state
    if st.session_state.id_created and st.session_state.id_card_image:
        st.image(st.session_state.id_card_image, caption="Your ClaudeNation ID", use_container_width=True)
        
        # Download link
        st.markdown(
            get_image_download_link(
                st.session_state.id_card_image,
                'claudenation_id.jpg',
                'Download Your ID Card'
            ),
            unsafe_allow_html=True
        )
        
        st.warning("Please download your ID card now. For privacy reasons, we don't store your photo.")
    
    # If returning user, regenerate ID from stored data
    else:
        citizen_data = get_citizen_data(st.session_state.user_email)
        
        if citizen_data:
            st.write("Your information:")
            st.write(f"Name: {citizen_data['full_name']}")
            st.write(f"Date of Birth: {citizen_data['date_of_birth']}")
            st.write(f"ID Number: {citizen_data['id_number']}")
            
            st.markdown("### Re-generate Your ID Card")
            st.write("Upload your photo to regenerate your ID card:")
            
            photo = st.file_uploader("Choose photo...", type=['jpg', 'jpeg', 'png'])
            
            if photo and st.button("Generate ID Card"):
                id_card = generate_id_card(
                    citizen_data['full_name'],
                    citizen_data['date_of_birth'],
                    citizen_data['id_number'],
                    photo,
                    citizen_data['theme']
                )
                
                st.image(id_card, caption="Your regenerated ClaudeNation ID", use_container_width=True)
                
                # Download link
                st.markdown(
                    get_image_download_link(
                        id_card,
                        'claudenation_id.jpg',
                        'Download Your ID Card'
                    ),
                    unsafe_allow_html=True
                )
        else:
            st.error("User profile not found. Please log out and register again.")
    
    if st.button("Logout"):
        # Clear session state
        for key in st.session_state.keys():
            del st.session_state[key]
        
        # Reinitialize session
        init_session()
        st.rerun()

if __name__ == "__main__":
    main()