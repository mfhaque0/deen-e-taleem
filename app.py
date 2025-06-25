import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, abort, flash # Added flash
from werkzeug.utils import secure_filename
import json
import random
import markdown
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'a_very_secret_key_for_deen_e_taleem' # Keep this secret key for session management

# Define base directory for content files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_POSTS_DIR = os.path.join(BASE_DIR, 'blog_posts')
DOWNLOADABLE_FILES_DIR = os.path.join(BASE_DIR, 'downloadable_files')
HADITH_DATA_FILE = os.path.join(BASE_DIR, 'hadith.json')

# Load all questions from the JSON file once at startup
with open('questions.json', 'r', encoding='utf-8') as f:
    all_questions = json.load(f)

# Load books data from the JSON file once at startup
try:
    with open('books_data.json', 'r', encoding='utf-8') as f:
        all_books = json.load(f)
except FileNotFoundError:
    all_books = []
except json.JSONDecodeError:
    all_books = []

# Load wallpapers data from the JSON file once at startup
try:
    with open('wallpapers_data.json', 'r', encoding='utf-8') as f:
        all_wallpapers = json.load(f)
except FileNotFoundError:
    all_wallpapers = []
except json.JSONDecodeError:
    all_wallpapers = []

# Load blogs data from the JSON file once at startup
try:
    with open('blogs_data.json', 'r', encoding='utf-8') as f:
        all_blog_posts = json.load(f)
except FileNotFoundError:
    print(f"Error: blogs_data.json not found. Please ensure it exists.")
    all_blog_posts = []
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from blogs_data.json. Check file for syntax errors.")
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


@app.context_processor
def inject_current_year():
    """Injects the current year into all templates for the footer."""
    return {'current_year': datetime.now().year}


@app.route('/')
def home():
    """Renders the main home page and passes a daily Hadith."""
    daily_hadith = None
    if all_hadith:
        day_of_year = datetime.now().timetuple().tm_yday
        hadith_index = (day_of_year - 1) % len(all_hadith)
        daily_hadith = all_hadith[hadith_index]
    return render_template('home.html', daily_hadith=daily_hadith)


@app.route('/quiz')
def quiz():
    """Renders the main quiz interface."""
    if 'quiz_questions' not in session or not session['quiz_questions']:
        return redirect(url_for('home'))
    return render_template('quiz.html')


@app.route('/start-quiz')
def start_quiz():
    """Initializes a new quiz session."""
    num_questions = min(10, len(all_questions))
    session['quiz_questions'] = random.sample(all_questions, num_questions)
    session['current_index'] = 0
    session['score'] = 0
    return redirect(url_for('quiz'))


@app.route('/api/question', methods=['GET'])
def get_question():
    """API endpoint to get the current question."""
    questions = session.get('quiz_questions', [])
    index = session.get('current_index', 0)

    if index >= len(questions):
        return jsonify({'finished': True})

    question_data = questions[index]
    return jsonify({
        'finished': False,
        'q_num': index + 1,
        'total': len(questions),
        'question': question_data['question'],
        'options': question_data['options']
    })


@app.route('/api/submit', methods=['POST'])
def submit_answer():
    """API endpoint to submit an answer and get feedback."""
    data = request.get_json()
    selected_option = data.get('selected_option')

    questions = session.get('quiz_questions', [])
    index = session.get('current_index', 0)

    if index >= len(questions) or selected_option is None:
        return jsonify({'error': 'Invalid request or quiz finished'}), 400

    question = questions[index]
    is_correct = (selected_option == question['correct'])

    if is_correct:
        session['score'] = session.get('score', 0) + 1
    
    session['current_index'] = index + 1

    return jsonify({
        'correct': is_correct,
        'correct_answer': question['correct'],
        'explanation': question['explanation']
    })


@app.route('/result')
def result():
    """Displays the final quiz results."""
    score = session.get('score', 0)
    total = len(session.get('quiz_questions', []))
    session.pop('quiz_questions', None)
    session.pop('current_index', None)
    session.pop('score', None)
    return render_template('result.html', score=score, total=total)


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


@app.route('/content-wait/<content_type>/<filename>')
def content_wait(content_type, filename):
    """
    Renders a waiting page before a download, passing content type and filename.
    Sets a session flag to allow the subsequent direct download.
    """
    valid_content_types = ['book', 'wallpaper']
    if content_type not in valid_content_types:
        return "Invalid content type.", 400

    item_found = False
    source_data = []
    if content_type == 'book':
        source_data = all_books
    elif content_type == 'wallpaper':
        source_data = all_wallpapers
    
    for item in source_data:
        if item['filename'] == filename:
            item_found = True
            break
    
    if not item_found:
        return "File not found.", 404

    session['can_download'] = True
    return render_template('wait_and_download.html', 
                           filename=filename, 
                           content_type=content_type)


@app.route('/download/<content_type>/<filename>')
def download_file(content_type, filename):
    """
    Serves the actual file for download, but only if initiated from the content-wait page.
    """
    if not session.get('can_download'):
        return redirect(url_for('home'))

    session.pop('can_download', None)

    directory = os.path.join(DOWNLOADABLE_FILES_DIR, content_type + 's')
    safe_filename = secure_filename(filename)
    
    item_found = False
    source_data = []
    expected_extensions = []

    if content_type == 'book':
        source_data = all_books
        expected_extensions = ['.pdf']
    elif content_type == 'wallpaper':
        source_data = all_wallpapers
        expected_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    else:
        return "Invalid content type.", 400

    for item in source_data:
        if item['filename'].lower() == safe_filename.lower(): 
            item_found = True
            break
    
    if not item_found:
        return "File not found in database.", 404

    file_ext = os.path.splitext(safe_filename)[1].lower()
    if file_ext not in expected_extensions:
        return "Invalid file type.", 400

    try:
        return send_from_directory(directory, safe_filename, as_attachment=True)
    except FileNotFoundError:
        return "File not found on server.", 404


# --- Blog Routes ---
@app.route('/blog')
def blog_index():
    """Renders the blog index page, listing all blog posts."""
    sorted_posts = sorted(all_blog_posts, key=lambda x: x['date'], reverse=True)
    return render_template('blog_index.html', posts=sorted_posts)

@app.route('/blog/<string:post_id>')
def blog_post(post_id):
    """Renders a single blog post."""
    post = next((p for p in all_blog_posts if p['id'] == post_id), None)
    if post is None:
        abort(404)

    content_file_path = os.path.join(BLOG_POSTS_DIR, post['content_file'])
    
    try:
        with open(content_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
            html_content = markdown.markdown(markdown_content)
        return render_template('blog_post.html', post=post, content=html_content)
    except FileNotFoundError:
        print(f"Error: Content file not found for post ID {post_id}: {content_file_path}")
        abort(500, description="Blog post content file not found.")
    except Exception as e:
        print(f"Error reading or processing Markdown for post ID {post_id}: {e}")
        abort(500, description="Error processing blog post content.")

# --- Contact Route ---
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Renders the contact page and handles form submissions."""
    if request.method == 'POST':
        # In a real application, you would process this form data:
        # - Send an email (e.g., using Flask-Mail)
        # - Save to a database
        # - Validate inputs
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        print(f"New contact form submission:\nName: {name}\nEmail: {email}\nSubject: {subject}\nMessage: {message}")
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)
