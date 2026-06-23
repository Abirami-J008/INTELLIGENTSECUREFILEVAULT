# Intelligent Secure File Vault System

A secure web-based Flask application designed for educational institutions to securely store, manage, and protect departmental documents using encryption, authentication, and role-based access control.

## Features

### Secure File Encryption
- Uploaded files are encrypted before storage to protect confidential documents.
- Prevents unauthorized access to stored files.

### Department-Based File Management
- Files are organized according to user departments.
- Users can access only files related to their assigned department.

### Role-Based Access Control (RBAC)
- Provides separate privileges for Admin and User roles.
- Admin has complete system control.
- Users have restricted access based on department permissions.

### User Registration and Admin Approval System
- New users can register using email and password.
- Registered users require administrator approval before login access.
- Rejected users are prevented from accessing the system.

### Secure Authentication
- Email and password-based login system.
- Passwords are securely stored using bcrypt hashing.
- Password change functionality is provided for users and administrators.

### Admin Dashboard
The administrator dashboard provides:

- Total user count
- Approved users count
- Pending users count
- Rejected users count
- Department statistics
- File statistics
- Activity monitoring
- Security alerts
- Daily security reports

### User Dashboard
The user dashboard provides:

- Own department user count
- Own file count
- File upload
- File download
- File deletion
- Department file viewing
- Common file viewing
- Quick file search
- Activity log search
- Profile management
- Password change

### Audit Logging System
All important activities are recorded including:

- Login
- Logout
- File upload
- File download
- File deletion
- Password changes
- User activities

### Security Alert Monitoring
- Detects suspicious activities such as repeated failed login attempts.
- Displays security alerts for administrators.

### Search and Filtering
Supports searching and filtering of:

- Files by file name
- Activities by user name
- Department-wise records
- Activity type
- From date and To date filtering

### Daily Security Report
The system provides daily activity summaries including:

- Total uploads
- Total downloads
- Total deletions
- Successful logins
- Failed login attempts

### Common File Sharing
- Administrators can upload common files.
- Users from different departments can view common files.
- File management remains under administrator control.

---

# Quick Start

## 1. Install Required Packages

##Install the required Python libraries:

```bash
pip install flask
pip install bcrypt
pip install cryptography
## 2. Run Application
Start the Flask application:
Bash
py app.py
The application will be available at:

http://localhost:5000
Default Admin Login Credentials
Use the following credentials for the first login:

Email:
admin123@gmail.com

Password:
Admin@123
After the first login, it is recommended to change the password for security purposes.

# Project Structure

```text
IntelligentSecureFileVault/

├── app.py
│   └── Flask application, routes, authentication, database operations, file management, encryption, and security logic
│
├── templates/
│   ├── home.html
│   │   └── Home page
│   │
│   ├── login.html
│   │   └── User login page
│   │
│   ├── register.html
│   │   └── New user registration page
│   │
│   ├── pending_users.html
│   │   └── Admin page for managing pending user approvals
│   │
│   ├── admin_dashboard.html
│   │   └── Administrator dashboard with statistics and security monitoring
│   │
│   ├── user_dashboard.html
│   │   └── User dashboard with department-based file access
│   │
│   ├── files.html
│   │   └── File management and file listing page
│   │
│   ├── upload.html
│   │   └── Secure file upload page
│   │
│   ├── logs.html
│   │   └── Activity log monitoring and filtering page
|   ├──pending_users.html  
    |   └── User approval and registration management page
│   │
│   └── profile.html
│       └── User profile a  password change page
│
├── uploads/
│   ├── Civil/
│   │   └── Department-wise uploaded files
│   │
│   ├── CSE/
│   │   └── Department-wise uploaded files
│   │
│   ├── ECE/
│   │   └── Department-wise uploaded files
│   │
│   ├── EEE/
│   │   └── Department-wise uploaded files
│   │
│   ├── MECH/
│   │   └── Department-wise uploaded files
│   │
│   └── Common/
│       └── Common files uploaded by administrator
│
├── vault.db
│   └── SQLite database storing users, files, activity logs, and security alerts
│
└── secret.key
    └── Encryption key used for securing uploaded files
## Technologies Used

### Python
Used as the core programming language for developing the backend logic and application functionality.

### Flask
Used as the web framework for creating routes, authentication system, dashboards, and application flow.

### SQLite
Used as the database system for storing user details, file information, activity logs, and security alerts.

### bcrypt
Used for securely hashing user passwords and protecting authentication credentials.

### Cryptography
Used for encrypting uploaded files and protecting confidential documents from unauthorized access.

### HTML
Used for designing the structure of web pages including login pages, dashboards, and management pages.

### CSS
Used for styling and improving the appearance of the user interface.

### Bootstrap
Used for creating a responsive and user-friendly dashboard design.

### JavaScript
Used for interactive features such as filtering, searching, and dynamic page behavior.

### Git & GitHub
Used for version control, source code management, and project publishing.
###Security Features
Password hashing using bcrypt
Secure file encryption
Role-based access control
Department-based authorization
User approval mechanism
Failed login detection
Security alert monitoring
Audit trail logging
Secure file operations
Session management
## License

Copyright (c) 2026 ABIRAMI J

All Rights Reserved.

No part of this project may be copied, modified, distributed, or reused without prior written permission from the author.
###About
###Intelligent Secure File Vault System is a secure document management platform developed using Python Flask. The system focuses on protecting institutional documents by implementing cybersecurity concepts such as authentication, authorization, encryption, access control, audit logging, and security monitoring.
###The application provides a secure environment for educational institutions to manage departmental files efficiently while maintaining confidentiality, integrity, and accountability.
