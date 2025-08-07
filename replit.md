# Route Optimizer Application

## Overview

This Flask-based web application optimizes delivery routes for field service teams using Traveling Salesman Problem (TSP) algorithms. It enables users to manage stops and employees, and generate optimized routes considering scheduling priorities and service types. The project aims to provide an efficient and cost-effective solution for logistics, leveraging real-time traffic data and sophisticated optimization techniques to enhance operational efficiency and customer satisfaction in service delivery.

## User Preferences

Preferred communication style: Simple, everyday language.
Interest in companion apps: Delivery driver mobile/web applications for field operations.
Driver scheduling priority: Minimum 8 hours per driver as demand allows, can be minimally over but ideally minimum 8 hours.

## System Architecture

### Design Philosophy
The application prioritizes a responsive, intuitive user interface with a dark theme, built on Bootstrap 5. It integrates advanced route optimization with real-time traffic awareness and flexible scheduling. The architecture supports scalability and maintainability, with clear separation of concerns between frontend and backend.

### Backend
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite (default for development, configurable to PostgreSQL for production)
- **Route Optimization**: Custom TSP solver incorporating geocoding and traffic-aware routing. It includes an 8-hour workday goal optimization with demand-based flexibility and intelligent traffic avoidance strategies for high-traffic zones.
- **Session Management**: Flask sessions for state management.

### Frontend
- **Template Engine**: Jinja2 templates for dynamic content.
- **Styling**: Bootstrap 5 dark theme with custom CSS.
- **JavaScript**: Vanilla JavaScript for client-side interactions, form validation, and UI enhancements like collapsible sections and real-time feedback.
- **Icons**: Feather icons for UI elements.
- **Mapping**: Hybrid mapping solution using Leaflet.js with OpenStreetMap for visualization, OSRM for street routing, and Google Maps API specifically for traffic-aware drive time calculations.

### Key Features
- **Route Optimization**: Implements TSP for optimal stop ordering, integrates real-time and historical traffic data, and considers scheduling priorities (ASAP vs. scheduled stops). It supports configurable departure addresses and aims for balanced workloads among employees.
- **Traffic Data Integration**: Scrapes traffic data from multiple sources and uses historical patterns with time-of-day multipliers for accurate estimates, including rush hour awareness.
- **User Interface**: Provides a dashboard for managing stops and employees, features responsive design, form validation, real-time feedback via flash messages, and UI improvements like collapsible sections and dynamic stop counters.
- **Data Management**: Supports PostgreSQL for production-ready data storage, including caching of historical traffic patterns and tracking of departure addresses.

## External Dependencies

### Python Packages
- **Flask**: Core web framework.
- **SQLAlchemy**: ORM for database interactions.
- **geopy**: Geocoding and distance calculations.
- **Werkzeug**: WSGI utilities.

### Frontend Libraries
- **Bootstrap 5**: CSS framework.
- **Feather Icons**: Icon library.
- **Leaflet.js**: Interactive maps.

### External Services
- **Nominatim**: OpenStreetMap geocoding service (no API keys required).
- **Google Maps Distance Matrix API**: Used specifically for accurate traffic-aware drive time calculations.
- **OpenStreetMap**: Provides map tiles for visual display.
- **OSRM (Open Source Routing Machine)**: Used for drawing route paths along streets.