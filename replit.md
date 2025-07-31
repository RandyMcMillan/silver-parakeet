# Shut Up and Drive - Route Optimization Application

## Overview
"Shut Up and Drive" is a Flask-based web application designed to optimize delivery routes for field service teams. It addresses the Traveling Salesman Problem (TSP) to efficiently manage stops, employees, and generate optimized routes. The application aims to get drivers on the road efficiently by considering scheduling priorities, service types, and real-time traffic data, balancing workloads to meet 8-hour daily targets, and integrating with actual street routing. The vision is to provide a robust solution for logistics and field service management, ensuring operational efficiency and cost optimization.

## User Preferences
Preferred communication style: Simple, everyday language.
Interest in companion apps: Delivery driver mobile/web applications for field operations.

## System Architecture

### Design Principles
- **Route Optimization**: Implements TSP algorithms with advanced features like traffic-aware routing, 8-hour workday goal, ASAP priority, scheduling priority, and load balancing.
- **Traffic Integration**: Utilizes real-time traffic data scraping and historical patterns, including rush hour awareness and construction-level variance detection.
- **User Interface**: Features a responsive design with Bootstrap 5 dark theme, Jinja2 templates, Feather icons, and JavaScript for dynamic interactions. Includes collapsible sections for improved readability, stop counters, and workday indicators.
- **Data Management**: Focuses on robust data storage for stops, employees, routes, and traffic patterns, with a PostgreSQL-ready database.
- **Cost Optimization**: Integrates fuel efficiency analysis (e.g., for Toyota Tundra) and minimizes API calls for external services.

### Technical Implementation
- **Backend**: Flask (Python), SQLAlchemy ORM, custom TSP solver, Nominatim for geocoding, geopy for distance calculations.
- **Frontend**: Jinja2, Bootstrap 5, Custom CSS, Vanilla JavaScript, Feather Icons.
- **Database**: SQLAlchemy ORM with SQLite for development, configured for PostgreSQL for production.
- **Route Generation**: Employs an intelligent TSP solver that considers real-time traffic, historical patterns, and load balancing, ensuring optimal stop ordering and driver assignment.
- **Mapping**: Utilizes a hybrid mapping solution combining Google Maps API for routing and accurate traffic-aware drive times with Leaflet.js and OpenStreetMap tiles for cost-free visual display. OSRM is used for realistic street-following route paths.

### Feature Specifications
- **Route Optimization**: TSP algorithm optimizes stop order for minimum travel time, considering 8-hour workday goals, real-time traffic, ASAP priority, and scheduling.
- **Traffic Awareness**: Scrapes traffic data from multiple sources, uses historical patterns, and avoids high-traffic zones during peak hours.
- **User Interface**: Dashboard for managing stops, employees, and routes; form validation; responsive design; flash messages; stop counters; automatic form reset; color-coded route times; departure management; agent sign memory.
- **Data Management**: PostgreSQL for production, traffic data caching, departure address tracking, agent sign history.
- **Overtime Policy**: Integration of an OvertimePolicy database model with 8-week lead time management and automatic calculation.

## External Dependencies

### Python Packages
- **Flask**: Web framework
- **SQLAlchemy**: ORM for database interactions
- **geopy**: Geocoding and distance calculations
- **Werkzeug**: WSGI utilities

### Frontend Libraries
- **Bootstrap 5**: CSS framework
- **Feather Icons**: Icon library
- **Vanilla JavaScript**: For UI interactions

### External Services
- **Nominatim (OpenStreetMap)**: Free geocoding service
- **Google Maps API**: Primarily for accurate routing and real-time traffic data (Distance Matrix API)
- **OSRM (Open Source Routing Machine)**: Free service for street-level route path visualization