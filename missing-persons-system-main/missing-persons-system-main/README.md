# Missing Persons System

![Missing Persons System](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

A comprehensive web-based system for managing and tracking missing persons cases, featuring face recognition technology and advanced search capabilities.

## 📸 How It Works

### 1. System Dashboard
![Dashboard](screenshots/dashboard.png)
*The main dashboard provides a real-time overview of the system:*
- System status monitoring
- Quick statistics (Total Missing, Found Persons, Active Cases)
- Recent found persons list
- Active missing persons cases
- Real-time system clock

### 2. Registering a Missing Person
![Register Missing Person](screenshots/register-missing.png)
*Step-by-step process to register a new missing person:*
1. Click "Register Missing Person" in the sidebar
2. Fill in personal details (name, age, description)
3. Upload recent photos
4. Add last seen location and date
5. Submit for processing

### 3. Face Recognition System
![Face Recognition](screenshots/face-recognition.png)
*Advanced face matching technology:*
- Upload a photo for matching
- System processes facial features
- Compares against database
- Shows match probability
- Displays potential matches

### 4. Search and Filter
![Search Interface](screenshots/search.png)
*Powerful search capabilities:*
- Search by name, age, location
- Filter by date range
- Advanced filters (height, clothing, etc.)
- Real-time results
- Export functionality

### 5. Case Management
![Case Management](screenshots/case-management.png)
*Comprehensive case tracking:*
- Case status updates
- Timeline of events
- Contact information
- Related cases
- Document management

### 6. Found Persons
![Found Persons](screenshots/found-persons.png)
*Managing found persons:*
- Mark cases as resolved
- Update status
- Add recovery details
- Generate reports
- Archive cases

## 🌟 Features

* **User Authentication**
  * Secure login and registration system
  * Role-based access control (Admin/User)
  * Session management

* **Missing Persons Management**
  * Register new missing person cases
  * Upload and manage person details
  * Track case status and updates

* **Face Recognition**
  * Advanced face matching technology
  * Image comparison capabilities
  * Match probability scoring

* **Search & Filter**
  * Advanced search functionality
  * Multiple filter options
  * Real-time results

* **Case Management**
  * Track found persons
  * Update case status
  * Case history and timeline

## 🚀 Getting Started

### Prerequisites

* Python 3.8 or higher
* MySQL Server
* Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/missing-persons-system.git
cd missing-persons-system
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
# Windows
setup_database.bat

# Linux/Mac
mysql -u root -p < database_setup.sql
```

5. Run the application:
```bash
# Windows
run_flask.bat

# Linux/Mac
flask run
```

## 🛠️ Technology Stack

* **Backend**
  * Python
  * Flask Framework
  * SQLAlchemy ORM
  * Face Recognition Library

* **Frontend**
  * HTML5
  * CSS3
  * JavaScript
  * Bootstrap 5
  * Font Awesome Icons

* **Database**
  * MySQL

## 📁 Project Structure

```
missing-persons-system/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   └── templates/
├── core/
│   └── face_recognition/
├── migrations/
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/
├── templates/
├── .env.example
├── .gitignore
├── app.py
├── config.py
├── requirements.txt
└── README.md
```

## 🔒 Security Features

* Password hashing
* CSRF protection
* Session management
* Input validation
* Secure file uploads
* XSS prevention

## 📝 API Documentation

### Authentication Endpoints

* `POST /login` - User login
* `POST /register` - User registration
* `GET /logout` - User logout

### Missing Persons Endpoints

* `GET /missing-persons` - List all missing persons
* `POST /missing-persons` - Register new missing person
* `GET /missing-persons/<id>` - Get specific case
* `PUT /missing-persons/<id>` - Update case
* `DELETE /missing-persons/<id>` - Delete case

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

* Your Name - Initial work

## 🙏 Acknowledgments

* Thanks to all contributors
* Inspired by the need for better missing persons tracking
* Built with modern web technologies

## 📞 Support

For support, email support@missingpersonssystem.com or create an issue in the repository.

## 🔄 Updates

- Latest update: [Current Date]
- Version: 1.0.0
- Changelog: See [CHANGELOG.md](CHANGELOG.md)

---

Made with ❤️ for a better world
