# Campus Clinic Appointment Management System (CCAMS)

A comprehensive Django web application for managing clinic appointments in a university campus setting. The system supports multiple user roles (students, staff, administrators) and provides complete appointment scheduling, management, and reporting capabilities.

## Features

### User Roles
- **Students**: Book, cancel, and reschedule appointments; view appointment history
- **Staff (Nurses/Psychologists)**: Manage availability, view appointments, update statuses
- **Administrators**: Manage users, generate reports, view audit logs

### Core Functionality
- **Appointment Booking**: Multi-step booking process with real-time availability checking
- **Schedule Management**: Staff can define weekly availability and block periods
- **Auto No-Show Detection**: Automatically marks appointments as no-show after 15 minutes
- **Notifications**: Email and SMS notifications for appointments (booking, cancellation, reminders)
- **Reporting**: Generate PDF and CSV reports with statistics
- **Audit Logging**: Complete audit trail of all system actions
- **Role-Based Access Control**: Secure access control based on user roles

### Technical Features
- **Responsive Design**: Mobile-friendly Bootstrap 5 interface
- **Real-time Updates**: AJAX-powered dynamic content
- **Security**: Account lockout, session management, CSRF protection
- **Database Support**: SQLite (development) and PostgreSQL (production) ready
- **Background Tasks**: Management commands for automated tasks

## System Requirements

- Python 3.8+
- Django 4.2+
- Modern web browser
- 2GB RAM minimum
- 1GB disk space

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ccams_project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create initial data
python manage.py seed_data
```

### 3. Create Superuser

```bash
# Create admin user
python manage.py createsuperuser

# Or use the seeded admin account:
# Username: admin
# Password: admin123
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## Demo Credentials

The system comes with pre-configured demo accounts:

| Role | Username | Password |
|------|----------|----------|
| Administrator | admin | admin123 |
| Nurse | nurse01 | nurse123 |
| Psychologist | psych01 | psych123 |
| Student | student01 | student123 |
| Student | student02 | student123 |
| Student | student03 | student123 |

## Project Structure

```
ccams_project/
|-- manage.py
|-- ccams/                    # Django project settings
|   |-- __init__.py
|   |-- settings.py
|   |-- urls.py
|   |-- wsgi.py
|   `-- asgi.py
|-- apps/                     # Django applications
|   |-- accounts/             # User management and authentication
|   |-- appointments/         # Appointment booking and management
|   |-- dashboard/            # Role-based dashboards
|   |-- availability/         # Staff schedule management
|   |-- notifications/        # Email and SMS services
|   |-- reports/              # Report generation
|   `-- audit/                # Audit logging
|-- static/                   # Static files (CSS, JS, images)
|   |-- css/
|   |-- js/
|   `-- images/
|-- templates/                # HTML templates
|   |-- base.html
|   |-- accounts/
|   |-- appointments/
|   |-- dashboard/
|   |-- availability/
|   |-- reports/
|   `-- admin_custom/
|-- media/                    # User uploaded files
`-- requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost/ccams_db

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Clinic System <noreply@clinic.edu>

# SMS Settings (Africa's Talking)
AFRICASTALKING_USERNAME=your-username
AFRICASTALKING_API_KEY=your-api-key

# Security
SESSION_COOKIE_AGE=900
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=15
APPOINTMENT_REMINDER_HOURS=24
NOSHOW_GRACE_MINUTES=15
```

### Production Settings

For production deployment:

1. Set `DEBUG=False`
2. Configure proper database (PostgreSQL recommended)
3. Set up email backend
4. Configure static file serving
5. Set up SSL/TLS
6. Configure logging
7. Set up monitoring

## Management Commands

### Seed Initial Data

```bash
python manage.py seed_data
```

Creates initial users, availability, and sample appointments.

### Check No-Shows

```bash
python manage.py check_no_shows
```

Automatically marks appointments as no-show if they're more than 15 minutes past the scheduled time.

### Run Periodically

Set up a cron job to run the no-show check every 10 minutes:

```bash
*/10 * * * * /path/to/venv/bin/python /path/to/project/manage.py check_no_shows
```

## User Guide

### Student Workflow

1. **Login**: Use student number and password
2. **Book Appointment**: 
   - Select provider type (Nurse/Psychologist)
   - Choose available date/time
   - Provide reason for visit
   - Confirm booking
3. **Manage Appointments**:
   - View upcoming and past appointments
   - Cancel appointments (if allowed)
   - Reschedule appointments (if allowed)
4. **Receive Notifications**: Email/SMS confirmations and reminders

### Staff Workflow

1. **Login**: Use employee ID and password
2. **View Dashboard**: Today's appointments and statistics
3. **Manage Schedule**:
   - Set weekly availability
   - Block periods (vacation, sick leave)
4. **Manage Appointments**:
   - View assigned appointments
   - Update appointment status (completed, no-show, cancelled)
   - Add notes to appointments

### Administrator Workflow

1. **Login**: Use admin credentials
2. **User Management**:
   - Create, edit, deactivate user accounts
   - Assign roles and permissions
3. **Reports**:
   - Generate appointment reports (PDF/CSV)
   - View statistics and trends
   - Export data as needed
4. **Audit**: View system audit logs

## API Endpoints

The system provides RESTful endpoints for integration:

### Authentication
- `POST /accounts/login/` - User login
- `POST /accounts/logout/` - User logout
- `POST /accounts/password-reset/` - Password reset

### Appointments
- `GET /appointments/` - List appointments
- `POST /appointments/book/` - Book appointment
- `GET /appointments/{id}/` - Get appointment details
- `PUT /appointments/{id}/cancel/` - Cancel appointment
- `PUT /appointments/{id}/reschedule/` - Reschedule appointment

### Availability
- `GET /availability/` - List available slots
- `POST /availability/` - Create availability
- `GET /availability/api/available-slots/` - Get available time slots

## Testing

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.accounts
python manage.py test apps.appointments

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Coverage

The system includes tests for:
- User authentication and authorization
- Appointment booking and management
- Role-based access control
- Data validation
- Business logic

## Deployment

### Using Docker

```bash
# Build image
docker build -t ccams .

# Run container
docker run -p 8000:8000 ccams
```

### Manual Deployment

1. **Server Setup**:
   - Install Python 3.8+
   - Install PostgreSQL (production)
   - Configure Nginx/Apache
   - Set up SSL certificates

2. **Application Setup**:
   - Clone repository
   - Install dependencies
   - Configure environment variables
   - Run migrations
   - Collect static files
   - Set up systemd service

3. **Database**:
   - Create database and user
   - Run migrations
   - Seed initial data

4. **Web Server**:
   - Configure Nginx/Apache to serve static files
   - Set up reverse proxy to Django
   - Configure SSL

## Security Considerations

- **Authentication**: Secure password handling, account lockout
- **Session Management**: 15-minute session timeout
- **CSRF Protection**: All forms protected
- **SQL Injection**: Django ORM prevents injection
- **XSS Protection**: Content Security Policy, input sanitization
- **HTTPS**: Enforce SSL in production
- **Audit Logging**: Complete audit trail

## Performance Optimization

- **Database**: Optimized queries, indexing
- **Caching**: Redis support for caching
- **Static Files**: Efficient serving with whitenoise
- **Pagination**: Large datasets paginated
- **Lazy Loading**: Content loaded as needed

## Troubleshooting

### Common Issues

1. **Migration Errors**:
   ```bash
   python manage.py migrate --fake-initial
   ```

2. **Static Files Not Loading**:
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Permission Errors**:
   ```bash
   chmod 755 /path/to/project
   ```

4. **Database Connection**:
   - Check database credentials
   - Ensure database server is running
   - Verify network connectivity

### Logging

Check logs for errors:
```bash
tail -f logs/django.log
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## Support

For support and questions:
- Email: support@clinic.edu
- Documentation: [Link to docs]
- Issues: [Link to issue tracker]

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- Complete appointment management system
- Multi-role support
- Reporting and audit features
- Mobile-responsive design
