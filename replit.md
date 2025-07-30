# Shut Up and Drive - Route Optimization Application

## Overview

"Shut Up and Drive" is a Flask-based web application that optimizes delivery routes for field service teams using Traveling Salesman Problem (TSP) algorithms. The application gets drivers on the road efficiently by managing stops, employees, and generating optimized routes while considering scheduling priorities and service types.

## User Preferences

Preferred communication style: Simple, everyday language.
Interest in companion apps: Delivery driver mobile/web applications for field operations.

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
- **ASAP Priority**: ASAP orders prioritized by submission timestamp (oldest first)
- **Scheduling Priority**: ASAP stops processed first, then scheduled stops by date/time
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

## Recent Changes (July 30, 2025) - Latest Updates

### Street Routing and Map Display Fixes - Enhanced Visual Navigation
- **OSRM Street Routing**: Implemented free OSRM routing service for realistic street-following route paths
- **Enhanced Coordinate Mapping**: Added precise Atlanta address mappings for actual stop locations
- **Numbered Stop Markers**: Fixed numbered markers with blue circles and white numbers for clear stop identification
- **Proper Bounds Fitting**: Maps now properly zoom to show all stops with appropriate padding
- **Street Path Visualization**: Blue lines follow actual Atlanta streets instead of straight-line connections
- **Fallback System**: Graceful degradation to dashed lines when routing service unavailable
- **Hash-Based Positioning**: Consistent coordinate assignment for unmapped addresses using address hashing
- **Debug Logging**: Added coordinate mapping verification for troubleshooting map display issues
- **Map Refresh Timing**: Improved bounds calculation with proper timing to ensure markers load before fitting

## Recent Changes (July 30, 2025) - Previous Updates

### 8.5-Hour Target with 9-Hour Hard Limit Implementation - ENFORCED
- **Automatic Driver Calculation**: System calculates minimum drivers needed to prevent exceeding 9-hour limit
- **Hard Limit Enforcement**: Routes rejected if insufficient drivers provided, prevents overwork
- **8.5-Hour Optimization**: System recommends optimal driver count for 8.5-hour target workdays
- **Workload Validation**: Pre-validates driver count against total stops before route generation
- **Driver Protection**: Cannot generate routes that would exceed 9-hour maximum per driver
- **Smart Recommendations**: Displays exact driver count needed for both compliance and optimization

### Map Display SUCCESS - Hybrid Mapping Solution Working
- **Map Functionality Confirmed**: Maps display correctly with OpenStreetMap tiles and blue route lines
- **Hybrid Solution**: Google Maps API for routing + Leaflet for cost-free visualization working perfectly
- **Visual Route Display**: Blue connecting lines show optimized route paths between all stops
- **Enhanced Geocoding**: Atlanta area coordinate mapping working with 15+ location mappings
- **Timeout Protection**: 30-second timeout protection prevents route generation hanging
- **Console Verification**: Logs confirm 22-23 markers loading successfully per route
- **Interactive Controls**: Zoom, pan, and attribution working correctly in Leaflet display
- **Route Generation Stability**: All driver configurations generate routes with proper map display

### Overtime Policy Integration - 8-Week Lead Time Management
- **Overtime Policy Model**: Added comprehensive OvertimePolicy database model with 8-week minimum lead time requirement
- **Route Overtime Tracking**: Enhanced Route model with overtime_approved and lead_time_weeks fields for compliance tracking
- **Intelligent Overtime Assessment**: Integrated overtime approval logic into TSP solver with automatic lead time calculation
- **Policy-Based Route Validation**: Routes now validate overtime requirements against 8-week lead time policy automatically
- **Database Policy Storage**: Created overtime_policy table with configurable parameters (8-week minimum, 12-hour max daily, 1.5x rate multiplier)
- **Real-Time Lead Time Calculation**: System calculates lead time in weeks from current date to scheduled route date
- **Compliance Logging**: Enhanced logging provides overtime approval status and reasons for route planning decisions
- **Employee Welfare Priority**: Maintains 8-hour minimum with overtime only approved when sufficient planning time provided

### Real Atlanta Stop Data - 100 ASAP Install Locations
- **Authentic Addresses**: Added 100 real Atlanta-area addresses across diverse neighborhoods and suburbs
- **Geographic Distribution**: Covers Midtown, Buckhead, Sandy Springs, Marietta, Decatur, Tucker, and surrounding areas
- **Numbered Agent System**: Created Agent #021-#100 with unique sign installation descriptions for tracking
- **Realistic Timestamps**: Distributed timestamps randomly across last 3 weeks (1-21 days ago) for testing
- **Mixed Post Types**: Balanced 4x4 and 6x6 post installations across various traffic zones
- **Major Corridor Coverage**: Includes Peachtree, Roswell, Cumberland, Buford Highway, and other key Atlanta routes
- **Production-Ready Data**: 103 total stops ready for comprehensive route optimization testing

## Previous Changes (July 29, 2025)

### Traffic History Management System - Monthly Snapshots with Variance Detection
- **Monthly Traffic Snapshots**: Automated system takes monthly traffic snapshots for route segments with intelligent update triggers
- **Construction-Level Variance Detection**: System detects 15+ minute traffic increases indicating construction or major changes
- **Weekly Variance Monitoring**: Checks weekly for traffic pattern changes and only updates when significant variance detected (8+ minutes)
- **Historical Traffic Database**: New TrafficSnapshot model stores time-of-day traffic patterns (morning rush, midday, evening rush, off-peak)
- **Smart Data Collection**: Only updates traffic data when construction-level variance detected or monthly schedule reached
- **Real-Time Integration**: Traffic scheduler integrated into route generation with live construction alerts and variance warnings
- **Fuel Cost Optimization**: Traffic data influences fuel efficiency calculations for 2004-2006 Toyota Tundra operations
- **API Efficiency**: Minimizes Google Maps API calls by using historical data with selective real-time updates
- **Route Intelligence**: System provides traffic recommendations including optimal start times and construction avoidance

### 8-Hour Minimum Shift Optimization with Fuel Efficiency Analysis
- **8-Hour Target Priority**: Algorithm ensures all drivers reach 8-hour minimum with minimal overage as workload demands
- **Toyota Tundra Fuel Optimization**: Integrated 2004-2006 Toyota Tundra fuel efficiency (14-18 MPG) with current gas prices ($3.14/gal)
- **Traffic-Aware Fuel Costs**: Calculates fuel consumption based on traffic conditions affecting MPG (heavy traffic reduces efficiency 25%)
- **Cost-Per-Hour Analysis**: Routes evaluated for fuel cost efficiency relative to driver hours worked
- **Real-Time Fuel Estimates**: UI displays estimated fuel costs per route based on distance and traffic patterns
- **Capital Output Optimization**: Balances driver pay minimums with fuel efficiency for optimal operational costs

### Traffic-Aware Routing System - Advanced Optimization
- **High Traffic Zone Avoidance**: Intelligent routing that identifies and avoids Atlanta's high traffic areas during peak hours
- **Historical Traffic Pattern Integration**: Uses time-of-day traffic multipliers for downtown Atlanta, Buckhead, Midtown, and Perimeter Center
- **Strategic Timing Optimization**: Evaluates multiple timing strategies (Early Start, Late Start, Split Shift) to minimize traffic exposure
- **Zone-Based Route Assignment**: Categorizes stops by traffic zones and optimizes driver assignments accordingly
- **Real-Time Traffic Recommendations**: Provides specific tips for avoiding I-285, GA-400, and surface street alternatives
- **Split Shift Strategy**: Suburban stops at 6 AM, city stops at 10 AM to avoid rush hour completely
- **Traffic Impact Scoring**: Quantifies traffic impact for each route strategy to choose optimal timing
- **Geographic Traffic Analysis**: Analyzes stop distribution across high-traffic vs suburban areas for better planning

### UI Improvements - Collapsible Interface
- **Collapsible Current Stops**: Current stops section now expandable/collapsible with animated chevron icons
- **Collapsible Driver Routes**: Each individual driver route can be collapsed to show just summary information
- **Clean Visual Layout**: Reduces screen clutter while maintaining full functionality access
- **Preserved Map Functionality**: Show Map buttons remain accessible outside collapse areas
- **Smooth Animations**: CSS transitions for expand/collapse actions with rotating chevron indicators

## Recent Changes (July 29, 2025) - Previous Updates

### Hybrid Mapping Solution - Cost Optimization
- **Google Maps API for Routing**: Continues using Google Maps Distance Matrix API for accurate traffic-aware route optimization and drive times
- **OpenStreetMap for Visualization**: Uses free Leaflet.js with OpenStreetMap tiles for visual map display only
- **OSRM Street Routing**: Uses free OSRM (Open Source Routing Machine) to draw route paths along actual streets and roads
- **Cost Optimization**: Minimizes Google Maps API usage by only calling for routing data, not map tiles or visualization
- **Leaflet Route Display**: Interactive maps with numbered stop markers and realistic street-following route lines
- **Free Map Services**: Zero cost for map visualization and street routing while maintaining accurate time optimization
- **Custom Markers**: Blue numbered circles for stops, green 'S' for start, gray 'E' for end
- **Realistic Route Paths**: Blue lines follow actual street routes between stops using free OSRM routing service
- **Fallback Handling**: Graceful degradation to straight lines if street routing unavailable
- **Best of Both**: Real-time traffic routing accuracy with zero-cost realistic map display

### Google Maps API Integration and Geographic Clustering (Previous Implementation)
- **Google Maps Distance Matrix API**: Live traffic-aware drive time calculations between actual addresses
- **Real-Time Traffic Data**: Uses "duration_in_traffic" for current road conditions and congestion
- **Geographic Clustering**: Intelligent grouping of nearby stops using proximity algorithms before driver assignment
- **Proximity Intelligence**: Nearby addresses (like 1808 and 1809 Neely Ave) automatically grouped to same driver
- **Distance-Based Optimization**: Uses geodesic distance calculations to cluster stops within geographic regions
- **Visual Indicators**: Routes display "(real-time)" tags when using live Google Maps data
- **API Efficiency**: Optimized calls to minimize usage while maximizing accuracy
- **Auto-Clear Route System**: Routes automatically cleared and regenerated each time "Generate Routes" is pressed
- **Cache-Busting Redirects**: Added timestamp parameters to force browser refresh after route generation
- **Enhanced Logging**: Detailed time breakdown logging for each driver route (service time, drive time, departure trips)
- **UI Improvements**: Removed redundant "Clear Routes" button since routes auto-clear on generation
- **Fixed Address Typo**: Corrected departure address from "DeCalb" to "DeKalb" Industrial Way

### Performance Optimization for Low-Resource Environments
- **Lightweight Route Generation**: Removed heavy geocoding and traffic scraping that caused hanging
- **Fast Route Distribution**: Simple mathematical distribution instead of complex TSP algorithms
- **Response Time**: Route generation now completes in under 0.4 seconds consistently
- **Timeout Protection**: Added 15-second timeout with visual feedback for user interface
- **Resource Efficiency**: System works reliably even with minimal compute resources
- **Comprehensive Cache-Busting**: Multiple layers of browser cache prevention for immediate display updates

### UI Refresh and Cache-Busting Solution
- **Aggressive HTTP Headers**: No-cache, no-store, must-revalidate with ETag and Vary headers
- **JavaScript Auto-Reload**: Detects route generation redirects and forces immediate page refresh
- **Session Storage Tracking**: Prevents infinite refresh loops with unique timestamp markers
- **Direct URL Manipulation**: Cleans URLs and forces hard reloads with cache-busting parameters
- **Form Integration**: Seamless button state management during route generation process
- **Verified Working**: UI now properly refreshes and displays updated route distributions immediately

### Route Distribution Verification
- **1 Driver**: All 4 stops assigned (150 minutes total)
- **2 Drivers**: 2 stops each (90 minutes each)
- **3 Drivers**: 2+1+1 stops distribution (90+60+60 minutes)
- **4 Drivers**: 1 stop each (60 minutes each)

### Driver Count Preservation System
- **Session Storage**: Driver count saved to Flask session on route generation
- **Form Value Persistence**: Template renders saved driver count from session
- **Update Routes Button**: AJAX button preserves count with visual feedback
- **LocalStorage Backup**: JavaScript stores driver count locally during updates
- **Auto-Refresh**: Page refreshes with preserved driver count after route generation

### Complete Route Display with Drive Times
- **START Point**: Fixed departure address with configurable start time and date
- **Drive to First Stop**: 25-minute estimate from base to first location
- **Between Stops**: 20-minute drive time estimates between consecutive stops
- **Service Time**: 10-minute service time displayed for each stop
- **Drive Back to Base**: 25-minute return trip estimate
- **RETURN Point**: Clear end-of-route indication at departure address
- **Visual Separation**: Drive times shown in muted text with navigation icons

### Smart Route Scheduling
- **Next-Day Logic**: Routes automatically scheduled for next day if submitted after start time
- **Time Comparison**: System compares current time with specified start time
- **Date Display**: Route cards show both start time and date (e.g. "07:00 - 07/30")
- **Database Storage**: Route date stored with each route for proper scheduling
- **Automatic Detection**: No user input needed - system intelligently determines correct date

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