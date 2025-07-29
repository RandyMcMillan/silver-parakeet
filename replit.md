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
- **TSP Algorithm**: Optimizes stop order for minimum travel time with traffic-aware routing
- **8-Hour Workday Goal**: Automatically balances workloads to meet 8-hour daily targets
- **Traffic Integration**: Real-time traffic data scraping for accurate time estimates
- **Scheduling Priority**: Scheduled stops take precedence over ASAP
- **Load Balancing**: Distributes stops across available drivers intelligently
- **Departure Address**: Configurable starting point for all driver routes

### Traffic Data Integration
- **Real-time Traffic**: Scrapes traffic data from multiple sources (Google Maps, Bing, MapQuest patterns)
- **Historical Patterns**: Uses time-of-day traffic multipliers for accurate estimates
- **Rush Hour Awareness**: Factors morning (7-10am) and evening (4-8pm) rush periods
- **Fallback Geocoding**: Graceful degradation when traffic data unavailable

### User Interface
- **Stop Counters**: Dashboard shows total stops and next 7-day schedule with dynamic updates
- **Form Reset**: Fully automated form clearing after successful stop submission using localStorage triggers
- **Workday Indicators**: Color-coded route times with 8-hour goal tracking
- **Departure Management**: Easy setting and updating of driver departure address with persistence
- **Agent Sign Memory**: Remembers and displays sign descriptions for removal jobs
- **Adblocker Compatibility**: Form reset system works even with browser adblockers interfering

### Data Management
- **PostgreSQL Database**: Production-ready database with traffic data storage
- **Traffic Data Caching**: Stores historical traffic patterns for route optimization
- **Departure Address Tracking**: Manages driver starting locations
- **Agent Sign History**: Maintains installation history for efficient removal service

## Recent Changes (July 29, 2025)

### Route Generation and Drive Time Improvements
- **Realistic Drive Time Calculations**: Updated to include 20 minutes between stops (city driving), 25 minutes from departure to first stop, and 25 minutes back to departure
- **Auto-Clear Route System**: Routes automatically cleared and regenerated each time "Generate Routes" is pressed
- **Cache-Busting Redirects**: Added timestamp parameters to force browser refresh after route generation
- **Enhanced Logging**: Detailed time breakdown logging for each driver route (service time, drive time, departure trips)
- **UI Improvements**: Removed redundant "Clear Routes" button since routes auto-clear on generation
- **Fixed Address Typo**: Corrected departure address from "DeCalb" to "DeKalb" Industrial Way

### Route Distribution Verification
- **1 Driver**: All 4 stops assigned (150 minutes total)
- **2 Drivers**: 2 stops each (90 minutes each)
- **3 Drivers**: 2+1+1 stops distribution (90+60+60 minutes)
- **4 Drivers**: 1 stop each (60 minutes each)

### Technical Improvements
- **Offline Operation**: System works without external geocoding dependencies
- **Database Integration**: Routes properly saved and displayed with accurate time calculations
- **Error Handling**: Improved error logging and graceful degradation when network unavailable

## Previous Changes (July 27, 2025)

### Fixed Departure Address Implementation
- **Departure Address System**: Changed from user-configurable to fixed address "183 DeCalb Industrial Way, Decatur, GA 30030"
- **UI Simplification**: Removed departure address form and replaced with read-only display
- **Code Architecture**: Updated all routes to use `get_fixed_departure_address()` function instead of database queries
- **Database Update**: Set the fixed address as active in the database for system consistency
- **Form Removal**: Eliminated the ability to modify departure address through the web interface

## Previous Changes (July 18, 2025)

### Form Reset System Implementation
- **Dual Trigger System**: Implemented both localStorage and URL parameter triggers for maximum reliability
- **Adblocker Resistance**: System works even when browser extensions interfere with redirects
- **Field Preservation**: Departure address field preserved during form resets
- **Dynamic Counter Updates**: Stop counters update automatically after form submission
- **Comprehensive Debugging**: Added detailed console logging for troubleshooting form reset process
- **Multiple Event Handlers**: Form submission captured through onsubmit attribute, addEventListener, and button click handlers

### Departure Address Persistence
- **Database Integration**: Departure address stored in DriverDepartureAddress model with active status tracking
- **API Integration**: Departure address included in stop counter API endpoint
- **Template Rendering**: Address properly displayed in form field on page load
- **Form Preservation**: Address maintained across form resets and page navigation