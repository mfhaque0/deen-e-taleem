import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, abort, flash
from werkzeug.utils import secure_filename
import json
import random
import markdown
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)
# IMPORTANT: In a production environment, use a strong, randomly generated secret key
# and store it securely (e.g., as an environment variable).
app.secret_key = 'a_very_secret_key_for_deen_e_taleem'

# Define base directory for content files (relative to app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_POSTS_DIR = os.path.join(BASE_DIR, 'blog_posts')
DOWNLOADABLE_FILES_DIR = os.path.join(BASE_DIR, 'downloadable_files')
STATIC_DIR = os.path.join(BASE_DIR, 'static') # Path for static assets like CSS, JS, images

# Paths to your JSON data files (assuming they are in the root directory)
QUESTIONS_DATA_FILE = os.path.join(BASE_DIR, 'questions.json')
BOOKS_DATA_FILE = os.path.join(BASE_DIR, 'books_data.json')
BLOGS_DATA_FILE = os.path.join(BASE_DIR, 'blogs_data.json')
WALLPAPERS_DATA_FILE = os.path.join(BASE_DIR, 'wallpapers_data.json')
HADITH_DATA_FILE = os.path.join(BASE_DIR, 'hadith.json')

# --- Data Loading Section ---
# Load all questions from the JSON file once at startup
try:
    with open(QUESTIONS_DATA_FILE, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)
except FileNotFoundError:
    print(f"Error: {QUESTIONS_DATA_FILE} not found. Please ensure it exists.")
    all_questions = []
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {QUESTIONS_DATA_FILE}. Check file for syntax errors.")
    all_questions = []

# Load books data from the JSON file once at startup
try:
    with open(BOOKS_DATA_FILE, 'r', encoding='utf-8') as f:
        all_books = json.load(f)
except FileNotFoundError:
    print(f"Error: {BOOKS_DATA_FILE} not found. Please ensure it exists.")
    all_books = []
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {BOOKS_DATA_FILE}. Check file for syntax errors.")
    all_books = []

# Load wallpapers data from the JSON file once at startup
try:
    with open(WALLPAPERS_DATA_FILE, 'r', encoding='utf-8') as f:
        all_wallpapers = json.load(f)
except FileNotFoundError:
    print(f"Error: {WALLPAPERS_DATA_FILE} not found. Please ensure it exists.")
    all_wallpapers = []
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {WALLPAPERS_DATA_FILE}. Check file for syntax errors.")
    all_wallpapers = []

# Load blogs data from the JSON file once at startup
try:
    with open(BLOGS_DATA_FILE, 'r', encoding='utf-8') as f:
        all_blog_posts = json.load(f)
except FileNotFoundError:
    print(f"Error: {BLOGS_DATA_FILE} not found. Please ensure it exists.")
    all_blog_posts = []
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {BLOGS_DATA_FILE}. Check file for syntax errors.")
    all_blog_posts = []

# Load Hadith data from the JSON file once at startup
try:
    with open(HADITH_DATA_FILE, 'r', encoding='utf-8') as f:
        all_hadith = json.load(f)
except FileNotFoundError:
    print(f"Error: {HADITH_DATA_FILE} not found. Please ensure it exists.")
    all_hadith = []
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {HADITH_DATA_FILE}. Check file for syntax errors.")
    all_hadith = []

# Placeholder for quiz topics if you want to expand beyond general quiz
QUIZ_TOPICS = [
    {"quiz_id": "general", "title": "General Islamic Knowledge", "topic": "various Islamic topics", "num_questions": min(10, len(all_questions))}
    # Add more quiz topics here if desired, e.g., "Quran", "Hadith", "Seerah"
]

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
        # Calculate a daily Hadith based on the day of the year for a simple rotation
        day_of_year = datetime.now().timetuple().tm_yday
        hadith_index = (day_of_year - 1) % len(all_hadith)
        daily_hadith = all_hadith[hadith_index]
    return render_template('home.html', daily_hadith=daily_hadith)

@app.route('/quiz-selection')
@app.route('/quiz') # Point /quiz to quiz selection for clearer flow
def quiz_selection():
    """Renders the quiz selection page."""
    # This route will list available quizzes.
    # For now, it just offers the general quiz.
    # If you have more types of quizzes, you would list them here.
    return render_template('quiz_selection.html', quiz_topics=QUIZ_TOPICS)

@app.route('/start-specific-quiz/<string:quiz_id>')
def start_specific_quiz(quiz_id):
    """Initializes a new quiz session for a specific quiz ID."""
    # For simplicity, we only have one type of quiz ('general') using all_questions.
    # In a more complex app, you'd load questions based on quiz_id.
    
    # Ensure all_questions has content before proceeding
    if not all_questions:
        flash("No quiz questions available. Please check the 'questions.json' file.", 'error')
        return redirect(url_for('home'))

    num_questions_to_load = 10 # Default number of questions per quiz

    if quiz_id == 'general':
        # Shuffle all questions and pick the desired number
        session['quiz_questions'] = random.sample(all_questions, min(num_questions_to_load, len(all_questions)))
        session['current_index'] = 0
        session['score'] = 0
        # Store quiz_id in session if needed for result page or other logic
        session['active_quiz_id'] = quiz_id
        return redirect(url_for('quiz_play'))
    else:
        flash("Selected quiz not found.", 'error')
        return redirect(url_for('quiz_selection'))

@app.route('/quiz/play')
def quiz_play():
    """Renders the main quiz interface after a quiz has been initialized."""
    # Ensure a quiz session exists before rendering the quiz page
    if 'quiz_questions' not in session or not session['quiz_questions']:
        # If no active quiz, redirect to selection or home
        flash("Please select a quiz to start.", 'info')
        return redirect(url_for('quiz_selection'))
    return render_template('quiz.html')

@app.route('/api/question', methods=['GET'])
def get_question():
    """API endpoint to get the current question."""
    questions = session.get('quiz_questions', [])
    index = session.get('current_index', 0)

    if index >= len(questions):
        # If all questions are answered, indicate quiz finished
        return jsonify({'finished': True})

    question_data = questions[index]
    # Ensure options are always a list, even if coming from old data
    options = list(question_data.get('options', []))
    
    return jsonify({
        'finished': False,
        'q_num': index + 1,
        'total': len(questions),
        'question': question_data['question'],
        'options': options
    })

@app.route('/api/submit', methods=['POST'])
def submit_answer():
    """API endpoint to submit an answer and get feedback."""
    data = request.get_json()
    selected_option = data.get('selected_option')

    questions = session.get('quiz_questions', [])
    index = session.get('current_index', 0)

    # Basic validation
    if index >= len(questions) or selected_option is None:
        return jsonify({'error': 'Invalid request or quiz finished'}), 400

    question = questions[index]
    # Ensure correct answer index is an integer for comparison
    correct_answer_index = int(question['correct'])
    is_correct = (selected_option == correct_answer_index)

    if is_correct:
        session['score'] = session.get('score', 0) + 1
    
    # Increment the current_index for the next question
    session['current_index'] = index + 1

    return jsonify({
        'correct': is_correct,
        'correct_answer_index': correct_answer_index, # Send back the correct index
        'explanation': question['explanation']
    })

@app.route('/result')
def result():
    """Displays the final quiz results."""
    score = session.get('score', 0)
    total = len(session.get('quiz_questions', [])) # Use quiz_questions from session for total
    
    # Clear quiz session data after displaying results
    session.pop('quiz_questions', None)
    session.pop('current_index', None)
    session.pop('score', None)
    session.pop('active_quiz_id', None) # Clear active quiz ID as well

    return render_template('result.html', score=score, total=total)

@app.route('/books')
def books():
    """Renders the books page with optional search functionality."""
    search_query = request.args.get('query', '').lower()
    filtered_books = []

    if search_query:
        for book in all_books:
            # Check title, author, and description for the search query
            if search_query in book.get('title', '').lower() or \
               search_query in book.get('author', '').lower() or \
               search_query in book.get('description', '').lower():
                filtered_books.append(book)
    else:
        filtered_books = all_books # Show all books if no search query

    return render_template('books.html', books=filtered_books, query=search_query)

@app.route('/wallpapers')
def wallpapers():
    """Renders the wallpapers page with data."""
    return render_template('wallpapers.html', wallpapers=all_wallpapers)

@app.route('/content-wait/<content_type>/<path:filename>')
def content_wait(content_type, filename):
    """
    Renders a waiting page before a download, passing content type and filename.
    Sets a session flag to allow the subsequent direct download.
    This route is crucial for preventing direct hotlinking/scraping of downloadable files.
    """
    valid_content_types = ['book', 'wallpaper']
    if content_type not in valid_content_types:
        abort(400, "Invalid content type specified for download.")

    item_found = False
    source_data = []

    if content_type == 'book':
        source_data = all_books
    elif content_type == 'wallpaper':
        source_data = all_wallpapers
    
    # Check if the filename exists in our data
    for item in source_data:
        # For books_data.json, some filenames are full URLs (Google Drive).
        # We only handle local files for secure_filename and send_from_directory.
        # For external URLs, we redirect directly.
        if item['filename'] == filename:
            item_found = True
            # If it's an external URL, bypass the wait page and redirect directly
            if filename.startswith('http://') or filename.startswith('https://'):
                return redirect(filename)
            break
    
    if not item_found:
        abort(404, "File not found in our records.")

    # Set a session flag to authorize the actual download
    session['can_download'] = True
    session['download_filename'] = filename
    session['download_content_type'] = content_type

    return render_template('wait_and_download.html', 
                           filename=filename, 
                           content_type=content_type)

@app.route('/download/<content_type>/<path:filename>')
def download_file(content_type, filename):
    """
    Serves the actual file for download, but only if initiated from the content-wait page
    and the session flag is set.
    """
    # Check if the download was authorized by the content-wait page
    if not session.get('can_download') or \
       session.get('download_filename') != filename or \
       session.get('download_content_type') != content_type:
        flash("Unauthorized download attempt. Please access content through the website.", 'error')
        return redirect(url_for('home'))

    # Clear the session flags immediately after authorization check
    session.pop('can_download', None)
    session.pop('download_filename', None)
    session.pop('download_content_type', None)

    # Sanitize filename to prevent directory traversal attacks
    safe_filename = secure_filename(filename)
    
    # Determine the correct directory based on content_type
    directory = os.path.join(DOWNLOADABLE_FILES_DIR, content_type + 's') # 'books' or 'wallpapers'

    # Optional: Further validate filename against expected types/patterns
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
        # This should ideally be caught earlier by content_wait, but as a safeguard
        abort(400, "Invalid content type for download.")

    for item in source_data_list:
        # Check if the filename from the request matches an allowed filename in our data
        if item['filename'].lower() == safe_filename.lower():
            item_found_in_data = True
            break
    
    if not item_found_in_data:
        abort(404, "Requested file not found in database or not authorized.")

    # Check file extension for extra security
    file_ext = os.path.splitext(safe_filename)[1].lower()
    if file_ext not in expected_extensions:
        abort(400, "Invalid file type extension.")

    # Serve the file securely
    try:
        return send_from_directory(directory, safe_filename, as_attachment=True)
    except FileNotFoundError:
        # Log this error as it indicates a discrepancy between data and actual files
        print(f"Server Error: File not found on disk: {os.path.join(directory, safe_filename)}")
        abort(404, "File not found on server.")


# --- Blog Routes ---
@app.route('/blog')
def blog_index():
    """Renders the blog index page, listing all blog posts."""
    # Sort posts by date in reverse chronological order (newest first)
    sorted_posts = sorted(all_blog_posts, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)
    return render_template('blog_index.html', posts=sorted_posts)

@app.route('/blog/<string:post_id>')
def blog_post(post_id):
    """Renders a single blog post."""
    # Find the post by its ID
    post = next((p for p in all_blog_posts if p['id'] == post_id), None)
    if post is None:
        abort(404, description="Blog post not found.")

    content_file_path = os.path.join(BLOG_POSTS_DIR, post['content_file'])
    
    try:
        with open(content_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
            # Convert Markdown content to HTML for rendering
            html_content = markdown.markdown(markdown_content)
        return render_template('blog_post.html', post=post, content=html_content)
    except FileNotFoundError:
        print(f"Error: Content file not found for post ID {post_id}: {content_file_path}")
        # Abort with a 500 error if the content file itself is missing
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

        # In a real application, you would send an email, save to DB, etc.
        # For this example, we'll just print to console and flash a message.
        print(f"--- NEW CONTACT FORM SUBMISSION ---\nName: {name}\nEmail: {email}\nSubject: {subject}\nMessage: {message}\n-----------------------------------")
        
        flash('Thank you for your message! We will get back to you soon, In Sha Allah.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

# --- Main entry point for running the Flask app ---
if __name__ == '__main__':
    # Ensure necessary directories exist at startup for file storage and static assets
    os.makedirs(BLOG_POSTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(DOWNLOADABLE_FILES_DIR, 'books'), exist_ok=True)
    os.makedirs(os.path.join(DOWNLOADABLE_FILES_DIR, 'wallpapers'), exist_ok=True)
    # The 'static' directory and its sub-directories (like 'book_covers', 'wallpaper_thumbnails')
    # should be managed by you, ensuring images are placed there.
    os.makedirs(os.path.join(STATIC_DIR, 'book_covers'), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'wallpaper_thumbnails'), exist_ok=True)
    
    # Run the Flask app in debug mode.
    # debug=True allows automatic reloading on code changes and provides a debugger.
    # host='0.0.0.0' makes the app accessible from outside the container/localhost.
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
