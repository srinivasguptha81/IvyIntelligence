# 🎓 Ivy Intelligence — Real-Time Ivy League Opportunity Intelligence System

> AI-powered platform that monitors Ivy League university websites in real-time, classifies opportunities using NLP/ML, and ranks students via the InCoScore algorithm.

---

## 📌 Project Overview

Students often miss high-quality opportunities like workshops, hackathons, research internships, scholarships, and conferences from top universities. **Ivy Intelligence** solves this by:

- **Real-time scraping** of Harvard, MIT, Yale, Stanford, Princeton, and more
- **AI-based domain classification** (AI, Law, Biomedical, ECE, CS, Business, etc.)
- **Personalized opportunity feeds** based on student interests
- **Auto-application system** with form detection and profile pre-fill
- **Academic social network** with posts, comments, likes, and real-time group chat
- **InCoScore ranking engine** to rank students by verified academic achievements
- **Modern Authentication UI** built completely on top of Bootstrap 5

---

## 🏗️ System Architecture

```text
ivy_intelligence/
├── config/                    # Django project settings
│   ├── settings.py            # All configuration (In-Memory Channels fallback added)
│   ├── urls.py                # Root URL routing
│   ├── asgi.py                # ASGI config (WebSockets via Channels)
│   └── celery.py              # Celery task queue setup
│
├── apps/
│   ├── opportunities/         # Module 1 & 2: Scraper + AI Classifier
│   │   ├── scraper.py         # BeautifulSoup4 web scrapers per university
│   │   ├── classifier.py      # TF-IDF + Logistic Regression classifier
│   │   ├── tasks.py           # Celery periodic tasks
│   │   └── management/commands/seed_data.py
│   │
│   ├── profiles/              # Module 3: Student profiles + personalization
│   ├── applications/          # Module 4: Application tracking + auto-fill
│   ├── community/             # Module 5: Social network + WebSocket chat
│   │   ├── consumers.py       # Django Channels WebSocket consumer
│   │   └── routing.py         # WebSocket URL routing
│   └── incoscore/             # Module 6: InCoScore ranking engine
│       └── engine.py          # Score calculation formula
│
├── templates/                 # HTML templates (Bootstrap 5)
│   ├── account/               # Custom Authentication templates
│   └── base/                  # Core layouts
├── static/                    # CSS, JS, images
└── media/                     # User uploaded files
```

---

## ⚙️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Django 4.2 | Core framework, ORM, Auth |
| REST API | Django REST Framework | JSON API endpoints |
| Auth | Django AllAuth + Crispy Forms | Registration, login, styled UI |
| Task Queue | Celery + Redis | Async scraping, scheduling |
| Scraping | BeautifulSoup4 + Requests | Opportunity extraction |
| AI/NLP | scikit-learn (TF-IDF + LR) | Domain classification |
| Real-time | Django Channels + WebSocket | Live chat (Auto DB/Mem fallback) |
| Frontend | Bootstrap 5 + Vanilla JS | UI |
| Database | SQLite (dev) / PostgreSQL (prod) | Data storage |

---

## 🚀 How to Run

### 1. Clone and construct Environment
```bash
git clone <your-repo-url>
cd ivy_intelligence
python -m venv venv
```

**CRITICAL: Activate your Virtual Environment!**
If you do not activate the environment, you will face `ImportError: Couldn't import Django` errors.
```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# Mac/Linux
source venv/bin/activate
```

Once activated, install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure environment
Create a `.env` file in the root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
REDIS_URL=redis://localhost:6379/0
```

### 3. Set up database
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data        # Creates sample data + demo users
```

### 4. Run the server

**For standard development (Includes In-Memory WebSockets):**
```bash
# We recommend using Daphne to support the local in-memory WebSockets!
daphne -p 8000 config.asgi:application

# Or standard runserver if you don't need WebSockets testing:
python manage.py runserver
```

**⚠️ For Background Celery Scraping Tasks (Redis Required):**
Since Celery requires a message broker, you must have Redis installed on your system (via WSL, Docker, or Memurai on Windows).
```bash
# In a separate terminal (with venv activated!) — start Celery worker:
celery -A config worker -l info

# In another terminal — start Celery Beat (periodic scraping):
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 5. Access the platform
- Site: http://localhost:8000 (or whichever port you specify)
- Admin: http://localhost:8000/admin
- Login: `admin` / `admin123` (or `student1` / `student123`)

---

## 🤖 How the AI Classifier Works

The domain classifier uses a **TF-IDF + Logistic Regression pipeline**:

1. **TF-IDF Vectorizer** converts opportunity text to a numerical vector. Words common in one domain (e.g., "neural network" → AI) get higher weights.
2. **Logistic Regression** then classifies the vector into one of 8 domain labels.
3. The model is trained on a labeled seed dataset and saved using `joblib`.
4. On startup, the model is loaded once into memory and reused for fast classification.

---

## 🏆 InCoScore Formula

InCoScore is calculated as:

```
InCoScore = Σ (raw_score / 100) × category_weight × 100
```

| Category | Weight |
|----------|--------|
| Research Papers | 30% |
| Hackathon Wins | 25% |
| Internships | 20% |
| Competitive Coding | 15% |
| Conferences | 10% |

- CGPA ≥ 9.0 → +5 bonus points
- CGPA ≥ 8.0 → +3 bonus points
- Maximum score: 100.0

---

## 🔄 Real-Time Scraping

Celery Beat triggers `scrape_all_universities()` every 6 hours. Each scraper:
1. Fetches the university events/opportunities page using `requests`
2. Parses HTML with `BeautifulSoup4`
3. Extracts: title, description, deadline, URL
4. Checks if URL already exists (change detection — no duplicates)
5. Classifies domain using the AI classifier
6. Saves new opportunities to the database

---

## 💬 WebSocket Chat & Channels Fallback

Built with Django Channels. Each domain group has a live chat room:
- User connects to `ws://localhost:8000/ws/chat/<group_id>/`
- **Smart Fallback**: If you are running locally (`DEBUG=True`), the system uses `InMemoryChannelLayer` so your WebSockets will work seamlessly **even without Redis installed!** 
- In Production, messages are broadcast to all connected users via Redis channel layer.

---

## 📂 Submission Info

- **Framework:** Django 4.2
- **University:** Lovely Professional University
- **Course:** Python and Full Stack
- **Project:** III — Real-Time Ivy League Opportunity Intelligence
