# Deen-e-Taleem 📘

**Deen-e-Taleem** is an Islamic educational platform built using Flask.  
It includes Islamic books, Hadiths, wallpapers, blogs, and quizzes – all aimed at spreading authentic knowledge in a beautiful and accessible way.

---

## 🌐 Live Website

👉 [Visit Live Site](https://deen-e-taleem.onrender.com)  


---

## 📚 Features

- 📘 Downloadable Islamic books (linked via Google Drive)
- 💬 Beautiful Islamic blogs and articles
- 🖼️ Islamic wallpapers with download option
- ❓ Quiz feature for learning and engagement
- 🔎 Simple, mobile-responsive user interface

---

## 🛠️ Built With

- 🐍 Python (Flask)
- 🧾 HTML5, CSS3
- ⚙️ JavaScript (vanilla)
- 🚀 Render for deployment
- 🔁 Git + GitHub for version control

---

## 📁 Folder Structure

Deen-e-Taleem/
├── app.py
├── requirements.txt
├── runtime.txt
├── Procfile
├── books_data.json
├── hadith.json
├── blogs_data.json
├── wallpapers_data.json
├── questions.json
├── static/
│ ├── style.css
│ ├── script.js
│ └── ...
├── templates/
│ ├── home.html
│ ├── books.html
│ ├── blog_post.html
│ └── ...
├── downloadable_files/
│ ├── books/
│ └── wallpapers/
└── blog_posts/


---

## 🚀 Deployment Instructions (Render)

1. Push your project to GitHub.
2. Go to [Render.com](https://render.com/) → Create a **New Web Service**.
3. Fill out the details:
   - **Build Command**:  
     ```
     pip install -r requirements.txt
     ```
   - **Start Command**:  
     ```
     gunicorn app:app
     ```
4. Done! Your Flask website will be auto-deployed on every push.

---

## 🤝 Contribution

Pull requests are welcome!  
For major changes, please open an issue first to discuss what you’d like to improve.

---

## 📜 License

This project is intended for **Islamic education and da’wah**.  
Free to use, share, and improve – all for the sake of Allah.

---

##  Developed By

**Md Faizanul Haque**  
🔗 [GitHub Profile](https://github.com/mfhaque0)
