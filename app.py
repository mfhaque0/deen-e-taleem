import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, abort, flash, get_flashed_messages
from werkzeug.utils import secure_filename
import json
import random
import markdown
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'a_very_secret_key_for_deen_e_taleem'

# Define base directory for content files (relative to app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_POSTS_DIR = os.path.join(BASE_DIR, 'blog_posts')
DOWNLOADABLE_FILES_DIR = os.path.join(BASE_DIR, 'downloadable_files')
STATIC_DIR = os.path.join(BASE_DIR, 'static') # Path for static assets like CSS, JS, images

# Paths to your JSON data files
QUESTIONS_DATA_FILE = os.path.join(STATIC_DIR, 'questions.json') 
BOOKS_DATA_FILE = os.path.join(BASE_DIR, 'books_data.json')
BLOGS_DATA_FILE = os.path.join(BASE_DIR, 'blogs_data.json')
WALLPAPERS_DATA_FILE = os.path.join(BASE_DIR, 'wallpapers_data.json')
HADITH_DATA_FILE = os.path.join(BASE_DIR, 'hadith.json')
DUA_DATA_FILE = os.path.join(BASE_DIR, 'dua.json')


# --- Quiz Configuration ---
QUESTION_SEGMENT_SIZE = 10 # Number of questions per segment/round


# --- Data Loading Section (Global Variables) ---
# Load all data once at startup
try:
    with open(QUESTIONS_DATA_FILE, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)
except Exception as e:
    print(f"Error loading questions.json: {e}")
    all_questions = []

try:
    with open(BOOKS_DATA_FILE, 'r', encoding='utf-8') as f:
        all_books = json.load(f)
except Exception:
    all_books = []

try:
    with open(WALLPAPERS_DATA_FILE, 'r', encoding='utf-8') as f:
        all_wallpapers = json.load(f)
except Exception:
    all_wallpapers = []

try:
    with open(BLOGS_DATA_FILE, 'r', encoding='utf-8') as f:
        all_blog_posts = json.load(f)
except Exception:
    all_blog_posts = []

try:
    with open(HADITH_DATA_FILE, 'r', encoding='utf-8') as f:
        all_hadith = json.load(f)
except Exception:
    all_hadith = []

def load_duas_data():
    """Loads Dua data from the JSON file."""
    try:
        with open(DUA_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

DUAS_DATA = load_duas_data()

# --- Helper Function ---
def get_questions_for_quiz_id(quiz_id):
    """Filters all questions by the quiz_id slug and returns the list."""
    if not all_questions:
        return []
    target_level = quiz_id.replace('_', ' ').title()
    # Returns the full list of question objects for that level
    return [q for q in all_questions if q.get('level') == target_level]


# --- Context Processor ---
@app.context_processor
def inject_current_year():
    """Injects the current year into all templates for the footer."""
    return {'current_year': datetime.now().year}

# --- Main Routes ---
@app.route('/')
def home():
    """Renders the main home page and passes a daily Hadith."""
    daily_hadith = None
    if all_hadith:
        day_of_year = datetime.now().timetuple().tm_yday
        hadith_index = (day_of_year - 1) % len(all_hadith)
        daily_hadith = all_hadith[hadith_index]
    return render_template('home.html', daily_hadith=daily_hadith)

@app.route('/quiz-selection')
@app.route('/quiz') 
def quiz_selection():
    """Renders the quiz selection page."""
    # Clear any previous quiz session data on selection page visit
    session.pop('quiz_id', None)
    # session.pop('full_quiz_questions', None) # REMOVED: This is no longer stored
    session.pop('shuffled_indices', None)
    session.pop('current_global_index', None)
    session.pop('segment_score', None)
    session.pop('total_score', None)
    session.pop('current_q_num_in_segment', None)
    return render_template('quiz_selection.html')


# --- START Quiz Segmented Logic ---

@app.route('/start-specific-quiz/<string:quiz_id>')
def start_specific_quiz(quiz_id):
    """Initializes a new quiz session for a specific level."""
    level_questions = get_questions_for_quiz_id(quiz_id)
    
    if not level_questions:
        flash(f"No questions found for the '{quiz_id.replace('_', ' ').title()}' level.", 'error')
        return redirect(url_for('quiz_selection'))

    # Store the index of the full question list for the current quiz_id (level)
    full_indices = list(range(len(level_questions)))
    random.shuffle(full_indices)

    # Initialize the session for the quiz
    session['quiz_id'] = quiz_id                 # The level slug (e.g., 'easy')
    # session['full_quiz_questions'] = level_questions # <--- REMOVED: Too big for cookie
    session['shuffled_indices'] = full_indices   # The randomized order of all question indices (small)
    
    session['current_global_index'] = 0          
    session['segment_score'] = 0                 
    session['total_score'] = 0                   
    session['current_q_num_in_segment'] = 0      
    
    flash(f"Starting the {quiz_id.replace('_', ' ').title()} Quiz!", 'success')
    return redirect(url_for('quiz_play'))


@app.route('/start-next-segment')
def start_next_segment():
    """Starts the next 10-question segment of the current quiz level."""
    if 'quiz_id' not in session or 'shuffled_indices' not in session:
        flash('Quiz session expired or invalid. Please select a quiz again.', 'error')
        return redirect(url_for('quiz_selection'))

    shuffled_indices = session.get('shuffled_indices', [])
    current_global_index = session.get('current_global_index', 0)
    
    if current_global_index >= len(shuffled_indices):
        flash("Masha'Allah! You have completed all questions in this level.", 'info')
        return redirect(url_for('quiz_selection'))

    # Reset segment-specific state
    session['segment_score'] = 0
    session['current_q_num_in_segment'] = 0 
    
    flash(f"Starting the next {min(QUESTION_SEGMENT_SIZE, len(shuffled_indices) - current_global_index)} questions!", 'success')
    return redirect(url_for('quiz_play'))


@app.route('/quiz/play')
def quiz_play():
    """Renders the main quiz interface."""
    # Check if the necessary minimal session data exists
    if 'quiz_id' not in session or 'shuffled_indices' not in session:
        flash("Please select a quiz to start.", 'info')
        # This redirect is the fix for the reported issue.
        return redirect(url_for('quiz_selection'))
    
    if 'current_q_num_in_segment' not in session:
        session['current_q_num_in_segment'] = 0
    
    _ = get_flashed_messages()

    return render_template('quiz.html')


@app.route('/api/question', methods=['GET'])
def get_question():
    """API endpoint to get the current question in the segment."""
    quiz_id = session.get('quiz_id')
    shuffled_indices = session.get('shuffled_indices', [])
    
    if not quiz_id or not shuffled_indices:
         return jsonify(error="No active quiz session found."), 400

    full_questions = get_questions_for_quiz_id(quiz_id) # <-- FETCH QUESTIONS HERE

    start_index = session.get('current_global_index', 0)
    current_q_index_in_segment = session.get('current_q_num_in_segment', 0)

    # Calculate the segment
    segment_end = min(start_index + QUESTION_SEGMENT_SIZE, len(shuffled_indices))
    current_segment_indices = shuffled_indices[start_index:segment_end]

    if current_q_index_in_segment >= len(current_segment_indices):
        return jsonify({'finished': True})

    # Get the index in the FULL list
    global_question_index = current_segment_indices[current_q_index_in_segment]
    
    # Retrieve the actual question data from the global list
    question_data = full_questions[global_question_index]

    # Store necessary info for submit in session
    session['current_correct_answer_index'] = int(question_data['correct'])
    session['current_explanation'] = question_data['explanation']

    return jsonify({
        'finished': False,
        'q_num': current_q_index_in_segment + 1,        # 1-based index for display
        'total': len(current_segment_indices),          # Total questions in this segment
        'question': question_data['question'],
        'options': list(question_data.get('options', []))
    })


@app.route('/api/submit', methods=['POST'])
def submit_answer():
    """API endpoint to submit an answer and get feedback."""
    data = request.get_json()
    selected_option = data.get('selected_option')

    correct_answer_index = session.get('current_correct_answer_index')
    explanation = session.get('current_explanation', 'No explanation provided.')
    
    if correct_answer_index is None:
        return jsonify({'error': 'No active question in session.'}), 400

    is_correct = (selected_option == correct_answer_index)

    if is_correct:
        session['segment_score'] = session.get('segment_score', 0) + 1
        session['total_score'] = session.get('total_score', 0) + 1

    session['current_q_num_in_segment'] = session.get('current_q_num_in_segment', 0) + 1

    return jsonify({
        'correct': is_correct,
        'correct_answer_index': correct_answer_index,
        'explanation': explanation
    })


@app.route('/result')
def result():
    """Displays the segment quiz results and sets up the next segment."""
    segment_score = session.get('segment_score', 0)
    shuffled_indices = session.get('shuffled_indices', [])
    start_index = session.get('current_global_index', 0)
    
    segment_total = session.get('current_q_num_in_segment', 0) 

    # Update the global index tracking to point to the start of the next segment
    session['current_global_index'] = start_index + segment_total
    
    # Reset temporary session data
    session.pop('current_q_num_in_segment', None)
    session.pop('current_correct_answer_index', None)
    session.pop('current_explanation', None)

    # Determine if there are more questions remaining in the quiz level
    current_global_index = session.get('current_global_index', 0)
    total_questions_in_level = len(shuffled_indices)
    has_more_questions = current_global_index < total_questions_in_level
    
    quiz_id = session.get('quiz_id')
    
    # Handle end of quiz level
    if not has_more_questions:
        total_cumulative_score = session.get('total_score', 0)
        flash("Masha'Allah! You have completed all segments for this quiz level. Your total score was {}/{}.".format(total_cumulative_score, total_questions_in_level), 'info')
        
        # Clear all quiz-related session data
        session.pop('quiz_id', None)
        session.pop('shuffled_indices', None)
        session.pop('current_global_index', None)
        session.pop('segment_score', None)
        session.pop('total_score', None)
        quiz_id = None

    # Pass data to the result page
    return render_template(
        'result.html',
        score=segment_score, 
        total=segment_total,
        has_more_questions=has_more_questions,
        quiz_id=quiz_id,
        current_year=datetime.now().year
    )

# --- END Quiz Segmented Logic ---


@app.route('/books')
def books():
    """Renders the books page with optional search functionality."""
    search_query = request.args.get('query', '').lower()
    filtered_books = []

    if search_query:
        for book in all_books:
            if search_query in book.get('title', '').lower() or \
               search_query in book.get('author', '').lower() or \
               search_query in book.get('description', '').lower():
                filtered_books.append(book)
    else:
        filtered_books = all_books

    return render_template('books.html', books=filtered_books, query=search_query)

@app.route('/wallpapers')
def wallpapers():
    """Renders the wallpapers page with data."""
    return render_template('wallpapers.html', wallpapers=all_wallpapers)

@app.route('/content-wait/<content_type>/<path:filename>')
def content_wait(content_type, filename):
    """Renders a waiting page before a download."""
    valid_content_types = ['book', 'wallpaper']
    if content_type not in valid_content_types:
        abort(400, "Invalid content type specified for download.")

    item_found = False
    source_data = []

    if content_type == 'book':
        source_data = all_books
    elif content_type == 'wallpaper':
        source_data = all_wallpapers
    
    for item in source_data:
        if item['filename'] == filename:
            item_found = True
            if filename.startswith('http://') or filename.startswith('https://'):
                return redirect(filename)
            break
    
    if not item_found:
        abort(404, "File not found in our records.")

    session['can_download'] = True
    session['download_filename'] = filename
    session['download_content_type'] = content_type

    return render_template('wait_and_download.html', 
                           filename=filename, 
                           content_type=content_type)

@app.route('/download/<content_type>/<path:filename>')
def download_file(content_type, filename):
    """Serves the actual file for download."""
    if not session.get('can_download') or \
       session.get('download_filename') != filename or \
       session.get('download_content_type') != content_type:
        flash("Unauthorized download attempt. Please access content through the website.", 'error')
        return redirect(url_for('home'))

    session.pop('can_download', None)
    session.pop('download_filename', None)
    session.pop('download_content_type', None)

    safe_filename = secure_filename(filename)
    directory = os.path.join(DOWNLOADABLE_FILES_DIR, content_type + 's')

    item_found_in_data = False
    source_data_list = []
    expected_extensions = []

    if content_type == 'book':
        source_data_list = all_books
        expected_extensions = ['.pdf']
    elif content_type == 'wallpaper':
        source_data_list = all_wallpapers
        expected_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    else:
        abort(400, "Invalid content type for download.")

    for item in source_data_list:
        if item['filename'].lower() == safe_filename.lower():
            item_found_in_data = True
            break
    
    if not item_found_in_data:
        abort(404, "Requested file not found in database or not authorized.")

    file_ext = os.path.splitext(safe_filename)[1].lower()
    if file_ext not in expected_extensions:
        abort(400, "Invalid file type extension.")

    try:
        return send_from_directory(directory, safe_filename, as_attachment=True)
    except FileNotFoundError:
        print(f"Server Error: File not found on disk: {os.path.join(directory, safe_filename)}")
        abort(404, "File not found on server.")

# --- Dua Logic and Routes ---
def get_duas_by_category(category):
    """Fetches a list of duas based on the given category key from the loaded data."""
    return DUAS_DATA.get(category, [])

@app.route('/dua')
def dua():
    """Renders the main dua category selection page."""
    return render_template('dua.html', categories=DUAS_DATA.keys(), current_year=datetime.now().year) 

@app.route('/dua/<category>')
def dua_detail(category):
    """Renders the page showing all duas for a specific category."""
    duas = get_duas_by_category(category) 
    return render_template('dua_detail.html', category=category, duas=duas)

# --- Blog Routes ---
@app.route('/blog')
def blog_index():
    """Renders the blog index page, listing all blog posts."""
    sorted_posts = sorted(all_blog_posts, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)
    return render_template('blog_index.html', posts=sorted_posts)

@app.route('/blog/<string:post_id>')
def blog_post(post_id):
    """Renders a single blog post."""
    post = next((p for p in all_blog_posts if p['id'] == post_id), None)
    if post is None:
        abort(404, description="Blog post not found.")

    content_file_path = os.path.join(BLOG_POSTS_DIR, post['content_file'])
    
    try:
        with open(content_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
            html_content = markdown.markdown(markdown_content)
        return render_template('blog_post.html', post=post, content=html_content)
    except FileNotFoundError:
        print(f"Error: Content file not found for post ID {post_id}: {content_file_path}")
        abort(500, description="Blog post content file not found on server.")
    except Exception as e:
        print(f"Error reading or processing Markdown for post ID {post_id}: {e}")
        abort(500, description="Error processing blog post content.")

# --- Contact Route ---
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Renders the contact page and handles form submissions."""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        print(f"--- NEW CONTACT FORM SUBMISSION ---\nName: {name}\nEmail: {email}\nSubject: {subject}\nMessage: {message}\n-----------------------------------")
        
        flash('Thank you for your message! We will get back to you soon, In Sha Allah.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

# --- Main entry point for running the Flask app ---
if __name__ == '__main__':
    os.makedirs(BLOG_POSTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(DOWNLOADABLE_FILES_DIR, 'books'), exist_ok=True)
    os.makedirs(os.path.join(DOWNLOADABLE_FILES_DIR, 'wallpapers'), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'book_covers'), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'wallpaper_thumbnails'), exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))