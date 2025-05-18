# Missing Persons System

![Missing Persons System](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

A comprehensive web-based system for managing and tracking missing persons cases, featuring face recognition technology and advanced search capabilities.

## 📸 Screenshots

### Dashboard
![Dashboard](screenshots/dashboard.png)
*Main dashboard showing system status, statistics, and recent cases*

### Missing Persons List
![Missing Persons](screenshots/missing-persons.png)
*List of all missing persons with search and filter options*

### Found Persons
![Found Persons](screenshots/found-persons.png)
*List of found persons with status updates*

### Face Match
![Face Match](screenshots/face-match.png)
*Face recognition interface for matching missing persons*

### Search Interface
![Search](screenshots/search.png)
*Advanced search interface with multiple filters*

### Case Details
![Case Details](screenshots/case-details.png)
*Detailed view of a missing person case*

## 🌟 Features

- **User Authentication**
  - Secure login and registration system
  - Role-based access control
  - Session management

- **Missing Persons Management**
  - Register new missing person cases
  - Upload and manage person details
  - Track case status and updates

- **Face Recognition**
  - Advanced face matching technology
  - Image comparison capabilities
  - Match probability scoring

- **Search & Filter**
  - Advanced search functionality
  - Multiple filter options
  - Real-time results

- **Case Management**
  - Track found persons
  - Update case status
  - Case history and timeline

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SadaamHassan68/missing-persons-system.git
   cd missing-persons-system
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the application:
   ```bash
   flask run
   ```

## 🛠️ Technology Stack

- **Backend**
  - Python
  - Flask Framework
  - SQLAlchemy ORM
  - Face Recognition Library

- **Frontend**
  - HTML5
  - CSS3
  - JavaScript
  - Bootstrap 5
  - Font Awesome Icons

- **Database**
  - SQLite (Development)
  - PostgreSQL (Production)

## 📁 Project Structure

```
missing-persons-system/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   └── templates/
├── migrations/
├── tests/
├── screenshots/          # Project screenshots
├── .env.example
├── .gitignore
├── config.py
├── requirements.txt
├── README.md
└── run.py
```

## 🔒 Security Features

- Password hashing
- CSRF protection
- Session management
- Input validation
- Secure file uploads
- XSS prevention

## 📝 API Documentation

### Authentication Endpoints

- `POST /api/login` - User login
- `POST /api/register` - User registration
- `POST /api/logout` - User logout

### Missing Persons Endpoints

- `GET /api/missing-persons` - List all missing persons
- `POST /api/missing-persons` - Register new missing person
- `GET /api/missing-persons/<id>` - Get specific case
- `PUT /api/missing-persons/<id>` - Update case
- `DELETE /api/missing-persons/<id>` - Delete case

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Sadaam Hassan - Initial work - [SadaamHassan68](https://github.com/SadaamHassan68)

## 🙏 Acknowledgments

- Thanks to all contributors
- Inspired by the need for better missing persons tracking
- Built with modern web technologies

## 📞 Support

For support, email support@missingpersonssystem.com or create an issue in the repository.

## 🔄 Updates

- Latest update: [Current Date]
- Version: 1.0.0
- Changelog: See [CHANGELOG.md](CHANGELOG.md)

---

Made with ❤️ for a better world
