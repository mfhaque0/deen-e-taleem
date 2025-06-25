document.addEventListener('DOMContentLoaded', () => {
    // Check if we are on the quiz page before executing quiz logic
    if (document.getElementById('quiz-container')) {
        loadQuestion();
    }
});

let selectedOption = null;
let correctAnswerIndex = null;
let isAnswerSubmitted = false;

function loadQuestion() {
    // Reset state for the new question
    selectedOption = null;
    correctAnswerIndex = null;
    isAnswerSubmitted = false;

    // UI resets
    document.getElementById('feedback-area').style.display = 'none';
    document.getElementById('next-btn').style.display = 'none';
    document.getElementById('submit-btn').style.display = 'none';

    fetch('/api/question')
        .then(res => res.json())
        .then(data => {
            if (data.finished) {
                // If the quiz is finished, redirect to the result page
                window.location.href = '/result';
                return;
            }

            // Populate question and counter
            document.getElementById('quiz-counter').innerText = `Question ${data.q_num} of ${data.total}`;
            document.getElementById('question').innerText = data.question;

            // Populate options
            const optionsGrid = document.getElementById('options-grid');
            optionsGrid.innerHTML = ""; // Clear previous options
            data.options.forEach((opt, idx) => {
                const button = document.createElement('button');
                button.className = 'option';
                button.innerText = opt;
                button.dataset.index = idx;
                button.onclick = () => selectOption(idx, button);
                optionsGrid.appendChild(button);
            });
        })
        .catch(error => {
            console.error("Failed to load question:", error);
            document.getElementById('question').innerText = "Error loading question. Please try starting the quiz again.";
        });
}

function selectOption(index, element) {
    // Prevent selection if an answer has already been submitted
    if (isAnswerSubmitted) return;

    selectedOption = index;

    // Update UI to show selection
    document.querySelectorAll('.option').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');

    // Show the submit button
    document.getElementById('submit-btn').style.display = 'block';
}

document.getElementById('submit-btn')?.addEventListener('click', () => {
    if (selectedOption === null) return;

    isAnswerSubmitted = true; // Lock the options

    fetch('/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_option: selectedOption })
    })
    .then(res => res.json())
    .then(data => {
        correctAnswerIndex = data.correct_answer;
        const resultEl = document.getElementById('result');

        // Display feedback
        if (data.correct) {
            resultEl.innerHTML = "<h4>✓ Masha'Allah, Correct!</h4>";
            resultEl.className = 'correct';
        } else {
            resultEl.innerHTML = "<h4>✗ Incorrect</h4>";
            resultEl.className = 'wrong';
        }
        
        document.getElementById('explanation').innerText = data.explanation;
        document.getElementById('feedback-area').style.display = 'block';

        // Visually update the options to show correct/wrong answers
        updateOptionsUI();

        // Hide submit, show next
        document.getElementById('submit-btn').style.display = 'none';
        document.getElementById('next-btn').style.display = 'block';
    });
});

function updateOptionsUI() {
    const options = document.querySelectorAll('.option');
    options.forEach(opt => {
        const optIndex = parseInt(opt.dataset.index, 10);
        
        // Disable further clicks
        opt.style.pointerEvents = 'none';

        // Highlight the correct answer in green
        if (optIndex === correctAnswerIndex) {
            opt.classList.add('correct-answer');
        }
        
        // If a wrong answer was selected, highlight it in red
        if (optIndex === selectedOption && optIndex !== correctAnswerIndex) {
            opt.classList.add('wrong-answer');
        }
    });
}

document.getElementById('next-btn')?.addEventListener('click', loadQuestion);