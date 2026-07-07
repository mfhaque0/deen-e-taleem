import os
from io import BytesIO
from html import escape
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, abort, flash, get_flashed_messages, make_response
from werkzeug.utils import secure_filename
import json
import random
import markdown
from datetime import datetime
from functools import wraps

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'a_very_secret_key_for_deen_e_taleem'

ADMIN_PASSWORD = 'Slimelayer@1029'

# Define base directory for content files (relative to app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_POSTS_DIR = os.path.join(BASE_DIR, 'blog_posts')
DOWNLOADABLE_FILES_DIR = os.path.join(BASE_DIR, 'downloadable_files')
STATIC_DIR = os.path.join(BASE_DIR, 'static') # Path for static assets like CSS, JS, images
QURAN_VERSES_FILE = os.path.join(BASE_DIR, 'quran_verses.json')

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

try:
    with open(QURAN_VERSES_FILE, 'r', encoding='utf-8') as f:
        all_quran_verses = json.load(f)
except Exception:
    all_quran_verses = []

def load_duas_data():
    """Loads Dua data from the JSON file."""
    try:
        with open(DUA_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

DUAS_DATA = load_duas_data()

# --- Helper Functions ---

def save_json_file(path, data):
    """Save JSON data back to a file."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving {path}: {e}")


def get_quran_verse(verse_id):
    return next((v for v in all_quran_verses if str(v.get('id')) == str(verse_id)), None)


def _wrap_svg_lines(text, max_chars=40):
    words = text.split()
    lines = []
    current_line = ''
    for word in words:
        if len(current_line) + len(word) + 1 > max_chars and current_line:
            lines.append(current_line.strip())
            current_line = word + ' '
        else:
            current_line += word + ' '
    if current_line:
        lines.append(current_line.strip())
    return lines


def create_quran_svg(verse):
    title = escape(verse.get('reference', 'Quran Verse'))
    arabic = escape(verse.get('arabic', ''))
    transliteration = escape(verse.get('transliteration', ''))
    translation = escape(verse.get('translation', ''))
    translation_ref = escape(verse.get('translation_reference', ''))

    arabic_lines = _wrap_svg_lines(arabic, max_chars=22)
    transliteration_lines = _wrap_svg_lines(transliteration, max_chars=48)
    translation_lines = _wrap_svg_lines(translation, max_chars=50)

    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg width="1200" height="1500" viewBox="0 0 1200 1500" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        '  <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">',
        '    <stop offset="0%" stop-color="#0a3f32"/>',
        '    <stop offset="100%" stop-color="#1f7c5c"/>',
        '  </linearGradient>',
        '  <linearGradient id="cardGradient" x1="0%" y1="0%" x2="100%" y2="100%">',
        '    <stop offset="0%" stop-color="#ffffff"/>',
        '    <stop offset="100%" stop-color="#f3faf7"/>',
        '  </linearGradient>',
        '  <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">',
        '    <feDropShadow dx="0" dy="18" stdDeviation="24" flood-color="#000000" flood-opacity="0.12"/>',
        '  </filter>',
        '</defs>',
        '<rect width="1200" height="1500" rx="55" fill="url(#bgGradient)"/>',
        '<rect x="70" y="90" width="1060" height="1280" rx="45" fill="url(#cardGradient)" filter="url(#softShadow)"/>',
        '<g opacity="0.13">',
        '  <circle cx="220" cy="170" r="90" fill="#ffffff"/>',
        '  <circle cx="980" cy="200" r="65" fill="#ffffff"/>',
        '  <circle cx="930" cy="350" r="35" fill="#ffffff"/>',
        '</g>',
        '<text x="600" y="165" text-anchor="middle" font-family="Poppins, Arial, sans-serif" font-size="46" font-weight="700" fill="#0d4f35">' + title + '</text>',
        '<text x="600" y="205" text-anchor="middle" font-family="Poppins, Arial, sans-serif" font-size="22" fill="#2f6b56">' + translation_ref + '</text>',
        '<g transform="translate(120, 260)">',
    ]

    y_offset = 0
    svg_lines.append('  <rect x="0" y="0" width="960" height="560" rx="38" fill="#f5fbf7" stroke="#cde6d7" stroke-width="1.5"/>')
    svg_lines.append('  <line x1="40" y1="80" x2="920" y2="80" stroke="#81b89d" stroke-width="2" opacity="0.35"/>')
    svg_lines.append('  <text x="880" y="58" text-anchor="end" font-family="Scheherazade, serif" font-size="58" fill="#11412c" direction="rtl">')

    for idx, line in enumerate(arabic_lines):
        y = 120 + idx * 82
        svg_lines.append('    <tspan x="880" dy="' + str(0 if idx == 0 else 82) + '">' + line + '</tspan>')

    svg_lines.append('  </text>')
    y_offset = 620
    svg_lines.append('  <line x1="40" y1="' + str(y_offset - 20) + '" x2="920" y2="' + str(y_offset - 20) + '" stroke="#0d6e56" stroke-width="1.5" opacity="0.25"/>')
    svg_lines.append('  <text x="40" y="' + str(y_offset + 40) + '" font-family="Poppins, Arial, sans-serif" font-size="26" fill="#0d4f35">Transliteration</text>')

    line_y = y_offset + 80
    for line in transliteration_lines:
        svg_lines.append('  <text x="40" y="' + str(line_y) + '" font-family="Poppins, Arial, sans-serif" font-size="24" fill="#2f6b56">' + line + '</text>')
        line_y += 36

    y_offset = line_y + 24
    svg_lines.append('  <text x="40" y="' + str(y_offset) + '" font-family="Poppins, Arial, sans-serif" font-size="26" fill="#0d4f35">Translation</text>')
    y_offset += 40
    for line in translation_lines:
        svg_lines.append('  <text x="40" y="' + str(y_offset) + '" font-family="Poppins, Arial, sans-serif" font-size="24" fill="#2f6b56">' + line + '</text>')
        y_offset += 36

    svg_lines.append('  <text x="40" y="' + str(y_offset + 40) + '" font-family="Poppins, Arial, sans-serif" font-size="20" fill="#5f7d6c">Downloaded from Deen-e-Taleem</text>')
    svg_lines.append('  <text x="40" y="' + str(y_offset + 72) + '" font-family="Poppins, Arial, sans-serif" font-size="18" fill="#8a9a8b">Share with family, friends, and loved ones.</text>')
    svg_lines.append('</g>')
    svg_lines.append('</svg>')

    return '\n'.join(svg_lines)


def is_allowed_book_file(filename):
    """Allow only PDF uploads for books."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


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

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Renders the admin login page and handles authentication."""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Successfully logged in to the admin panel.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Incorrect admin password.', 'error')

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out of admin panel.', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    """Renders the admin dashboard."""
    return render_template(
        'admin_dashboard.html',
        total_books=len(all_books),
        total_blogs=len(all_blog_posts),
        total_questions=len(all_questions),
        total_wallpapers=len(all_wallpapers),
        total_quran_verses=len(all_quran_verses)
    )


@app.route('/admin/books', methods=['GET', 'POST'])
@admin_required
def admin_books():
    """Manage books from the admin panel."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        description = request.form.get('description', '').strip()
        external_link = request.form.get('external_link', '').strip()
        cover_name = request.form.get('cover_name', '').strip()

        pdf_file = request.files.get('pdf_file')
        cover_file = request.files.get('cover_file')

        if not title or not author:
            flash('Title and author are required for a book.', 'error')
            return redirect(url_for('admin_books'))

        filename = None
        if pdf_file and pdf_file.filename:
            if not is_allowed_book_file(pdf_file.filename):
                flash('Only PDF files are allowed for books.', 'error')
                return redirect(url_for('admin_books'))
            filename = secure_filename(pdf_file.filename)
            pdf_file.save(os.path.join(DOWNLOADABLE_FILES_DIR, 'books', filename))
        elif external_link:
            filename = external_link
        else:
            flash('Please provide either a PDF upload or an external download link.', 'error')
            return redirect(url_for('admin_books'))

        cover_image = ''
        if cover_file and cover_file.filename:
            cover_image = secure_filename(cover_file.filename)
            cover_file.save(os.path.join(STATIC_DIR, 'book_covers', cover_image))
        elif cover_name:
            cover_image = cover_name

        new_book = {
            'title': title,
            'filename': filename,
            'author': author,
            'description': description,
            'cover_image': cover_image
        }
        all_books.append(new_book)
        save_json_file(BOOKS_DATA_FILE, all_books)
        flash('Book added successfully.', 'success')
        return redirect(url_for('admin_books'))

    return render_template('admin_books.html', books=all_books)


@app.route('/admin/books/edit/<int:index>', methods=['GET', 'POST'])
@admin_required
def admin_edit_book(index):
    if index < 0 or index >= len(all_books):
        abort(404)
    book = all_books[index]

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        description = request.form.get('description', '').strip()
        external_link = request.form.get('external_link', '').strip()
        cover_name = request.form.get('cover_name', '').strip()

        pdf_file = request.files.get('pdf_file')
        cover_file = request.files.get('cover_file')

        if title:
            book['title'] = title
        if author:
            book['author'] = author
        book['description'] = description

        if pdf_file and pdf_file.filename:
            if not is_allowed_book_file(pdf_file.filename):
                flash('Only PDF files are allowed for books.', 'error')
                return redirect(url_for('admin_edit_book', index=index))
            filename = secure_filename(pdf_file.filename)
            pdf_file.save(os.path.join(DOWNLOADABLE_FILES_DIR, 'books', filename))
            book['filename'] = filename
        elif external_link:
            book['filename'] = external_link

        if cover_file and cover_file.filename:
            cover_image = secure_filename(cover_file.filename)
            cover_file.save(os.path.join(STATIC_DIR, 'book_covers', cover_image))
            book['cover_image'] = cover_image
        elif cover_name:
            book['cover_image'] = cover_name

        save_json_file(BOOKS_DATA_FILE, all_books)
        flash('Book updated successfully.', 'success')
        return redirect(url_for('admin_books'))

    return render_template('admin_book_edit.html', book=book, index=index)


@app.route('/admin/books/delete/<int:index>', methods=['POST'])
@admin_required
def admin_delete_book(index):
    if index < 0 or index >= len(all_books):
        abort(404)
    deleted_book = all_books.pop(index)
    save_json_file(BOOKS_DATA_FILE, all_books)
    flash(f'Book "{deleted_book.get("title", "Untitled")}" deleted successfully.', 'success')
    return redirect(url_for('admin_books'))


@app.route('/admin/blogs')
@admin_required
def admin_blogs():
    return render_template('admin_blogs.html', posts=all_blog_posts)


@app.route('/admin/blogs/new', methods=['GET', 'POST'])
@admin_required
def admin_new_blog():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        date = request.form.get('date', '').strip()
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()

        if not title or not author or not date or not summary or not content:
            flash('All blog fields are required.', 'error')
            return redirect(url_for('admin_new_blog'))

        new_id = str(max([int(p['id']) for p in all_blog_posts] + [0]) + 1)
        safe_filename = secure_filename(title.lower().replace(' ', '_'))
        content_file = f'{safe_filename}_{new_id}.md'

        with open(os.path.join(BLOG_POSTS_DIR, content_file), 'w', encoding='utf-8') as f:
            f.write(content)

        new_post = {
            'id': new_id,
            'title': title,
            'author': author,
            'date': date,
            'summary': summary,
            'content_file': content_file
        }
        all_blog_posts.append(new_post)
        save_json_file(BLOGS_DATA_FILE, all_blog_posts)
        flash('Blog post created successfully.', 'success')
        return redirect(url_for('admin_blogs'))

    return render_template('admin_blog_edit.html', post=None)


@app.route('/admin/blogs/edit/<string:post_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_blog(post_id):
    post = next((p for p in all_blog_posts if p['id'] == post_id), None)
    if post is None:
        abort(404)

    content_file_path = os.path.join(BLOG_POSTS_DIR, post['content_file'])
    content_text = ''
    try:
        with open(content_file_path, 'r', encoding='utf-8') as f:
            content_text = f.read()
    except FileNotFoundError:
        content_text = ''

    if request.method == 'POST':
        post['title'] = request.form.get('title', '').strip()
        post['author'] = request.form.get('author', '').strip()
        post['date'] = request.form.get('date', '').strip()
        post['summary'] = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()

        with open(content_file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        save_json_file(BLOGS_DATA_FILE, all_blog_posts)
        flash('Blog post updated successfully.', 'success')
        return redirect(url_for('admin_blogs'))

    return render_template('admin_blog_edit.html', post=post, content=content_text)


@app.route('/admin/blogs/delete/<string:post_id>', methods=['POST'])
@admin_required
def admin_delete_blog(post_id):
    post = next((p for p in all_blog_posts if p['id'] == post_id), None)
    if post is None:
        abort(404)

    if post.get('content_file'):
        try:
            os.remove(os.path.join(BLOG_POSTS_DIR, post['content_file']))
        except OSError:
            pass

    all_blog_posts[:] = [p for p in all_blog_posts if p['id'] != post_id]
    save_json_file(BLOGS_DATA_FILE, all_blog_posts)
    flash('Blog post deleted successfully.', 'success')
    return redirect(url_for('admin_blogs'))


@app.route('/admin/questions')
@admin_required
def admin_questions():
    return render_template('admin_questions.html', questions=all_questions)


@app.route('/admin/questions/new', methods=['GET', 'POST'])
@admin_required
def admin_new_question():
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        options = [request.form.get(f'option_{i}', '').strip() for i in range(4)]
        correct = request.form.get('correct', '').strip()
        explanation = request.form.get('explanation', '').strip()
        level = request.form.get('level', '').strip()

        if not question or not all(options) or correct == '' or not explanation or not level:
            flash('All question fields are required.', 'error')
            return redirect(url_for('admin_new_question'))

        all_questions.append({
            'question': question,
            'options': options,
            'correct': int(correct),
            'explanation': explanation,
            'level': level
        })
        save_json_file(QUESTIONS_DATA_FILE, all_questions)
        flash('Question added successfully.', 'success')
        return redirect(url_for('admin_questions'))

    return render_template('admin_question_edit.html', question=None, index=None)


@app.route('/admin/questions/edit/<int:index>', methods=['GET', 'POST'])
@admin_required
def admin_edit_question(index):
    if index < 0 or index >= len(all_questions):
        abort(404)
    question = all_questions[index]

    if request.method == 'POST':
        question['question'] = request.form.get('question', '').strip()
        question['options'] = [request.form.get(f'option_{i}', '').strip() for i in range(4)]
        question['correct'] = int(request.form.get('correct', '0'))
        question['explanation'] = request.form.get('explanation', '').strip()
        question['level'] = request.form.get('level', '').strip()

        save_json_file(QUESTIONS_DATA_FILE, all_questions)
        flash('Question updated successfully.', 'success')
        return redirect(url_for('admin_questions'))

    return render_template('admin_question_edit.html', question=question, index=index)


@app.route('/admin/questions/delete/<int:index>', methods=['POST'])
@admin_required
def admin_delete_question(index):
    if index < 0 or index >= len(all_questions):
        abort(404)
    deleted_question = all_questions.pop(index)
    save_json_file(QUESTIONS_DATA_FILE, all_questions)
    flash('Question deleted successfully.', 'success')
    return redirect(url_for('admin_questions'))


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


@app.route('/quran')
def quran():
    """Renders a page with Quran verses."""
    return render_template('quran.html', verses=all_quran_verses)


@app.route('/download/quran/<string:verse_id>')
def download_quran_verse(verse_id):
    verse = get_quran_verse(verse_id)
    if not verse:
        abort(404)

    svg = create_quran_svg(verse)
    response = make_response(svg)
    response.headers['Content-Type'] = 'image/svg+xml; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=quran_verse_{verse_id}.svg'
    return response


@app.route('/admin/wallpapers', methods=['GET', 'POST'])
@admin_required
def admin_wallpapers():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        image_file = request.files.get('image_file')
        thumbnail_file = request.files.get('thumbnail_file')
        thumbnail_name = request.form.get('thumbnail_name', '').strip()

        if not title or not description:
            flash('Title and description are required.', 'error')
            return redirect(url_for('admin_wallpapers'))
        if not image_file or not image_file.filename:
            flash('Wallpaper image file is required.', 'error')
            return redirect(url_for('admin_wallpapers'))

        image_filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(DOWNLOADABLE_FILES_DIR, 'wallpapers', image_filename))

        thumbnail_image = ''
        if thumbnail_file and thumbnail_file.filename:
            thumbnail_image = secure_filename(thumbnail_file.filename)
            thumbnail_file.save(os.path.join(STATIC_DIR, 'wallpaper_thumbnails', thumbnail_image))
        elif thumbnail_name:
            thumbnail_image = thumbnail_name

        new_id = str(max([int(item['id']) for item in all_wallpapers] + [0]) + 1)
        all_wallpapers.append({
            'id': new_id,
            'title': title,
            'description': description,
            'filename': image_filename,
            'thumbnail_image': thumbnail_image or image_filename
        })
        save_json_file(WALLPAPERS_DATA_FILE, all_wallpapers)
        flash('Wallpaper added successfully.', 'success')
        return redirect(url_for('admin_wallpapers'))

    return render_template('admin_wallpapers.html', wallpapers=all_wallpapers)


@app.route('/admin/wallpapers/edit/<int:index>', methods=['GET', 'POST'])
@admin_required
def admin_edit_wallpaper(index):
    if index < 0 or index >= len(all_wallpapers):
        abort(404)
    wallpaper = all_wallpapers[index]

    if request.method == 'POST':
        wallpaper['title'] = request.form.get('title', '').strip() or wallpaper['title']
        wallpaper['description'] = request.form.get('description', '').strip() or wallpaper['description']

        image_file = request.files.get('image_file')
        thumbnail_file = request.files.get('thumbnail_file')
        thumbnail_name = request.form.get('thumbnail_name', '').strip()

        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(DOWNLOADABLE_FILES_DIR, 'wallpapers', image_filename))
            wallpaper['filename'] = image_filename

        if thumbnail_file and thumbnail_file.filename:
            thumbnail_image = secure_filename(thumbnail_file.filename)
            thumbnail_file.save(os.path.join(STATIC_DIR, 'wallpaper_thumbnails', thumbnail_image))
            wallpaper['thumbnail_image'] = thumbnail_image
        elif thumbnail_name:
            wallpaper['thumbnail_image'] = thumbnail_name

        save_json_file(WALLPAPERS_DATA_FILE, all_wallpapers)
        flash('Wallpaper updated successfully.', 'success')
        return redirect(url_for('admin_wallpapers'))

    return render_template('admin_wallpaper_edit.html', wallpaper=wallpaper, index=index)


@app.route('/admin/wallpapers/delete/<int:index>', methods=['POST'])
@admin_required
def admin_delete_wallpaper(index):
    if index < 0 or index >= len(all_wallpapers):
        abort(404)
    deleted = all_wallpapers.pop(index)
    save_json_file(WALLPAPERS_DATA_FILE, all_wallpapers)
    flash(f"Wallpaper '{deleted.get('title', 'Untitled')}' deleted successfully.", 'success')
    return redirect(url_for('admin_wallpapers'))


@app.route('/admin/quran')
@admin_required
def admin_quran():
    return render_template('admin_quran.html', verses=all_quran_verses)


@app.route('/admin/quran/new', methods=['GET', 'POST'])
@admin_required
def admin_new_quran():
    if request.method == 'POST':
        reference = request.form.get('reference', '').strip()
        transliteration = request.form.get('transliteration', '').strip()
        translation = request.form.get('translation', '').strip()
        translation_reference = request.form.get('translation_reference', '').strip()
        arabic = request.form.get('arabic', '').strip()

        if not reference or not arabic or not translation or not translation_reference:
            flash('Reference, Arabic, translation, and translation reference are required.', 'error')
            return redirect(url_for('admin_new_quran'))

        new_id = str(max([int(v['id']) for v in all_quran_verses] + [0]) + 1)
        all_quran_verses.append({
            'id': new_id,
            'reference': reference,
            'arabic': arabic,
            'transliteration': transliteration,
            'translation': translation,
            'translation_reference': translation_reference
        })
        save_json_file(QURAN_VERSES_FILE, all_quran_verses)
        flash('Quran verse added successfully.', 'success')
        return redirect(url_for('admin_quran'))

    return render_template('admin_quran_edit.html', verse=None)


@app.route('/admin/quran/edit/<string:verse_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_quran(verse_id):
    verse = get_quran_verse(verse_id)
    if verse is None:
        abort(404)

    if request.method == 'POST':
        verse['reference'] = request.form.get('reference', '').strip() or verse['reference']
        verse['arabic'] = request.form.get('arabic', '').strip() or verse['arabic']
        verse['transliteration'] = request.form.get('transliteration', '').strip() or verse['transliteration']
        verse['translation'] = request.form.get('translation', '').strip() or verse['translation']
        verse['translation_reference'] = request.form.get('translation_reference', '').strip() or verse.get('translation_reference', '')
        save_json_file(QURAN_VERSES_FILE, all_quran_verses)
        flash('Quran verse updated successfully.', 'success')
        return redirect(url_for('admin_quran'))

    return render_template('admin_quran_edit.html', verse=verse)


@app.route('/admin/quran/delete/<string:verse_id>', methods=['POST'])
@admin_required
def admin_delete_quran(verse_id):
    verse = get_quran_verse(verse_id)
    if verse is None:
        abort(404)
    all_quran_verses[:] = [v for v in all_quran_verses if str(v.get('id')) != str(verse_id)]
    save_json_file(QURAN_VERSES_FILE, all_quran_verses)
    flash('Quran verse deleted successfully.', 'success')
    return redirect(url_for('admin_quran'))

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

    filename = os.path.basename(filename)
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
        if item['filename'].lower() == filename.lower():
            item_found_in_data = True
            break

    if not item_found_in_data:
        abort(404, "Requested file not found in database or not authorized.")

    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in expected_extensions:
        abort(400, "Invalid file type extension.")

    try:
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        print(f"Server Error: File not found on disk: {os.path.join(directory, filename)}")
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