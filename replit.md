# Route Optimizer Application

## Overview

This is a Flask-based web application that optimizes delivery routes for field service teams using Traveling Salesman Problem (TSP) algorithms. The application allows users to manage stops, employees, and generate optimized routes while considering scheduling priorities and service types.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite (configurable to PostgreSQL via DATABASE_URL)
- **Route Optimization**: Custom TSP solver with geocoding capabilities
- **Session Management**: Flask sessions with configurable secret key

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme
- **Styling**: Custom CSS with Bootstrap framework
- **JavaScript**: Vanilla JavaScript for form validation and UI interactions
- **Icons**: Feather icons for UI elements

### Database Schema
- **Stop Model**: Stores delivery/pickup locations with post type, address, service type, scheduling info
- **Employee Model**: Basic employee information for route assignment
- **Route Model**: Generated routes with employee assignments and stop sequences

## Key Components

### Core Models
1. **Stop**: Represents a delivery/pickup location with scheduling priorities
   - Supports ASAP vs scheduled stops
   - Tracks service type (install/pickup)
   - Stores address and post type information

2. **Employee**: Basic employee records for route assignment

3. **Route**: Generated route assignments linking employees to ordered stop sequences

### TSP Solver
- **Geocoding**: Uses Nominatim (OpenStreetMap) for address-to-coordinate conversion
- **Distance Calculation**: Geodesic distance calculation with caching
- **Route Optimization**: Implements TSP algorithm for optimal stop ordering
- **Fallback Handling**: Graceful degradation when geocoding fails

### Web Interface
- **Dashboard**: Central interface for managing stops, employees, and routes
- **Form Validation**: Client-side and server-side validation
- **Responsive Design**: Bootstrap-based responsive UI
- **Real-time Feedback**: Flash messages for user actions

## Data Flow

1. **Stop Creation**: Users input stop details through web form
2. **Validation**: Server validates required fields and date constraints
3. **Storage**: Stop data persisted to SQLite database
4. **Route Generation**: TSP solver processes stops to create optimized routes
5. **Assignment**: Routes assigned to available employees
6. **Display**: Generated routes displayed in web interface

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **geopy**: Geocoding and distance calculations
- **Werkzeug**: WSGI utilities and proxy handling

### Frontend Dependencies
- **Bootstrap 5**: CSS framework with dark theme
- **Feather Icons**: Icon library for UI elements
- **Vanilla JavaScript**: Form validation and interactions

### External Services
- **Nominatim**: OpenStreetMap geocoding service
- **No API keys required**: Uses free geocoding service

## Deployment Strategy

### Configuration
- **Environment Variables**: DATABASE_URL, SESSION_SECRET
- **Database**: SQLite for development, PostgreSQL-ready for production
- **Logging**: Configurable logging levels
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxy

### Development Setup
- **Local Development**: SQLite database with debug mode
- **Hot Reload**: Flask development server with auto-reload
- **Static Files**: Served directly by Flask in development

### Production Considerations
- **Database**: Configured for PostgreSQL with connection pooling
- **Security**: Environment-based secret key management
- **Scalability**: Connection pool settings for concurrent users
- **Proxy Support**: Ready for deployment behind nginx/Apache

## Key Features

### Route Optimization
- **TSP Algorithm**: Optimizes stop order for minimum travel time
- **Scheduling Priority**: Scheduled stops take precedence over ASAP
- **Load Balancing**: Distributes stops across available employees
- **Time Estimation**: 10-minute service time per stop

### User Interface
- **Intuitive Forms**: Easy stop entry with validation
- **Real-time Updates**: Immediate feedback on actions
- **Responsive Design**: Works on desktop and mobile
- **Dark Theme**: Modern Bootstrap dark theme

### Data Management
- **Flexible Storage**: SQLite for development, PostgreSQL for production
- **Data Validation**: Server-side validation for all inputs
- **Error Handling**: Graceful error handling with user feedback
- **Caching**: Distance calculation caching for performance