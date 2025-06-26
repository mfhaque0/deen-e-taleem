// Ensure DOM content is fully loaded before executing scripts
document.addEventListener('DOMContentLoaded', () => {
    // Check if we are on the quiz playing page before executing quiz logic
    if (document.getElementById('quiz-container')) {
        console.log("Quiz container detected. Loading question...");
        loadQuestion(); // Load the first question when the quiz page loads
        // Attach event listeners for quiz buttons
        document.getElementById('submit-btn')?.addEventListener('click', handleSubmit);
        document.getElementById('next-btn')?.addEventListener('click', loadQuestion);
    }

    // Handle navbar search form submission (Frontend only for now, redirects to /books route)
    const navbarSearchForm = document.getElementById('navbarSearchForm');
    if (navbarSearchForm) {
        navbarSearchForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission to handle with JS
            const searchQueryInput = this.querySelector('input[type="search"]');
            const searchQuery = searchQueryInput ? searchQueryInput.value.trim() : '';

            if (searchQuery !== '') {
                // Redirect to the /books route with the search query as a parameter
                window.location.href = `/books?query=${encodeURIComponent(searchQuery)}`;
            } else {
                // Provide user feedback for empty search term without using alert()
                showFeedbackMessage('Please enter a search term.', 'info');
                searchQueryInput?.focus(); // Focus back on the search input
            }
        });
    }

    // Handle flashes/messages from Flask
    // This listener should be general and run on every page.
    const flashMessagesContainer = document.getElementById('flash-messages');
    if (flashMessagesContainer) {
        // Find all alert elements within the container
        const alerts = flashMessagesContainer.querySelectorAll('.alert');
        alerts.forEach(alertDiv => {
            // Automatically hide each alert after a few seconds
            setTimeout(() => {
                const bsAlert = bootstrap.Alert.getInstance(alertDiv) || new bootstrap.Alert(alertDiv);
                bsAlert.dispose(); // Use Bootstrap's dispose method to remove the alert
            }, 5000); // 5 seconds
        });
    }
});

// Quiz state variables
let selectedOption = null; // Stores the index of the currently selected option by the user
let correctAnswerIndex = null; // Stores the index of the correct answer for the current question
let isAnswerSubmitted = false; // Flag to prevent multiple submissions

/**
 * Loads a new question from the backend API.
 * Resets the UI and state for the new question.
 */
function loadQuestion() {
    console.log("Attempting to load new question...");
    // Reset state for the new question
    selectedOption = null;
    correctAnswerIndex = null;
    isAnswerSubmitted = false;

    // Reset UI elements
    document.getElementById('feedback-area').style.display = 'none';
    document.getElementById('next-btn').style.display = 'none';
    document.getElementById('submit-btn').style.display = 'block'; // Show submit button for new question

    // Remove any previous highlighting from options
    const options = document.querySelectorAll('.option');
    options.forEach(opt => {
        opt.classList.remove('selected', 'correct-answer', 'wrong-answer');
        opt.style.pointerEvents = 'auto'; // Re-enable clicks
    });

    // Fetch the next question from the Flask API
    fetch('/api/question')
        .then(res => {
            console.log("Received response from /api/question:", res);
            if (!res.ok) {
                // Handle HTTP errors
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            console.log("Parsed data from /api/question:", data);
            if (data.finished) {
                // If the quiz is finished, redirect to the result page
                console.log("Quiz finished. Redirecting to /result.");
                window.location.href = '/result';
                return;
            }

            // Populate question and counter display
            document.getElementById('quiz-counter').innerText = `Question ${data.q_num} of ${data.total}`;
            document.getElementById('question').innerText = data.question;

            // Populate options dynamically
            const optionsGrid = document.getElementById('options-grid');
            optionsGrid.innerHTML = ""; // Clear previous options

            data.options.forEach((opt, idx) => {
                const button = document.createElement('button');
                button.className = 'option btn btn-outline-success w-100 mb-2'; // Bootstrap styling
                button.setAttribute('data-index', idx); // Store option index for easy lookup
                button.innerText = opt;
                
                // Add click listener for selecting options
                button.addEventListener('click', () => selectOption(button, idx));
                optionsGrid.appendChild(button);
            });
        })
        .catch(error => {
            console.error("Error loading question:", error);
            showFeedbackMessage(`Failed to load question. Please try starting the quiz again. Details: ${error.message}`, 'error');
            // In case of error, disable controls or provide retry option
            document.getElementById('submit-btn').style.display = 'none';
            document.getElementById('next-btn').style.display = 'none';
            document.getElementById('quiz-counter').innerText = 'Error loading quiz.';
            document.getElementById('question').innerText = 'Could not load quiz questions.';
        });
}

/**
 * Handles the selection of a quiz option.
 * @param {HTMLElement} clickedButton The button element that was clicked.
 * @param {number} index The index of the selected option.
 */
function selectOption(clickedButton, index) {
    if (isAnswerSubmitted) return; // Prevent selection after submission

    // Remove 'selected' class from previously selected option
    const currentSelected = document.querySelector('.option.selected');
    if (currentSelected) {
        currentSelected.classList.remove('selected');
    }

    // Add 'selected' class to the newly clicked option
    clickedButton.classList.add('selected');
    selectedOption = index; // Update the selected option index

    // Show submit button once an option is selected
    document.getElementById('submit-btn').style.display = 'block';
}

/**
 * Handles the submission of the selected answer to the backend.
 * Sends the selected option index to the API and updates UI based on feedback.
 *ß
 */
function handleSubmit() {
    if (selectedOption === null || isAnswerSubmitted) {
        // Inform user if no option is selected
        showFeedbackMessage('Please select an answer before submitting.', 'info');
        return;
    }

    isAnswerSubmitted = true; // Set flag to prevent double submission

    // Disable all options and submit button immediately to prevent further interaction
    document.querySelectorAll('.option').forEach(opt => opt.style.pointerEvents = 'none');
    document.getElementById('submit-btn').style.display = 'none';

    console.log("Submitting answer:", selectedOption);
    // Send the selected option to the backend
    fetch('/api/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ selected_option: selectedOption })
    })
    .then(res => {
        console.log("Received response from /api/submit:", res);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        console.log("Parsed data from /api/submit:", data);
        correctAnswerIndex = data.correct_answer_index; // Store the correct answer index
        const resultEl = document.getElementById('result');
        const explanationEl = document.getElementById('explanation');

        // Display feedback message and styling
        if (data.correct) {
            resultEl.innerHTML = "<h4>✓ Masha'Allah, Correct!</h4>";
            resultEl.className = 'text-success fw-bold'; // Use Bootstrap classes for text color
        } else {
            resultEl.innerHTML = "<h4>✗ Incorrect</h4>";
            resultEl.className = 'text-danger fw-bold'; // Use Bootstrap classes for text color
        }
        
        explanationEl.innerText = data.explanation;
        document.getElementById('feedback-area').style.display = 'block';

        // Visually update the options to show correct/wrong answers
        updateOptionsUI();

        // Show next question button
        document.getElementById('next-btn').style.display = 'block';
    })
    .catch(error => {
        console.error("Error submitting answer:", error);
        showFeedbackMessage(`An error occurred while submitting your answer. Please try again. Details: ${error.message}`, 'error');
        // Re-enable submit or allow retry if an error occurs
        isAnswerSubmitted = false;
        document.getElementById('submit-btn').style.display = 'block';
        document.getElementById('next-btn').style.display = 'none';
        // Re-enable options in case of a submission error
        document.querySelectorAll('.option').forEach(opt => opt.style.pointerEvents = 'auto');
    });
}

/**
 * Updates the visual styling of the quiz options after an answer has been submitted.
 * Highlights correct and incorrect choices.
 */
function updateOptionsUI() {
    const options = document.querySelectorAll('.option');
    options.forEach(opt => {
        const optIndex = parseInt(opt.dataset.index, 10); // Get the index of the current option button
        
        // Disable further clicks on all options to lock the answer
        opt.style.pointerEvents = 'none';

        // Highlight the correct answer in green
        if (optIndex === correctAnswerIndex) {
            opt.classList.add('correct-answer');
        }
        
        // If a wrong answer was selected, highlight it in red
        // This condition checks if this option was the selected one AND it was NOT the correct one
        if (optIndex === selectedOption && optIndex !== correctAnswerIndex) {
            opt.classList.add('wrong-answer');
        }
    });
    console.log("Options UI updated.");
}

/**
 * Displays a temporary feedback message to the user within the dedicated container.
 * This replaces standard browser alerts.
 * @param {string} message The message to display.
 * @param {string} type The type of message (e.g., 'success', 'info', 'error', 'warning').
 */
function showFeedbackMessage(message, type) {
    const container = document.getElementById('flash-messages'); // Use the common flash message container
    if (!container) {
        console.warn("Flash message container not found. Message: " + message);
        return; // Exit if the container doesn't exist
    }

    // Create alert element
    const alertDiv = document.createElement('div');
    // Using Bootstrap classes for alerts
    alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    container.innerHTML = ''; // Clear previous messages in this container
    container.appendChild(alertDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        // Try to get an existing Bootstrap Alert instance or create a new one
        const bsAlert = bootstrap.Alert.getInstance(alertDiv) || new bootstrap.Alert(alertDiv);
        bsAlert.dispose(); // Use Bootstrap's dispose method to remove the alert cleanly
    }, 5000); // 5 seconds
}
