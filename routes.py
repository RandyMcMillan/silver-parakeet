from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, date, timedelta
from models import Stop, Route, AgentSignHistory, DriverDepartureAddress, TrafficData, TrafficSnapshot, db
from tsp_solver import TSPSolver
from traffic_scraper import TrafficDataScraper
from traffic_scheduler import traffic_scheduler
from security_enhancements import SecurityValidator, require_rate_limit
import json
import logging
import os

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Main page with route optimization interface"""
    # Order stops by priority: Scheduled stops first, then ASAP stops (both FIFO)
    stops = Stop.query.order_by(
        Stop.is_asap.asc(),   # Scheduled stops first (is_asap=False comes before is_asap=True)
        Stop.required_date.asc().nulls_last(),  # Scheduled stops by required date
        Stop.created_at.asc()  # Then by entry date (FIFO) for same dates or ASAP stops
    ).all()
    routes = Route.query.all()
    agent_signs = AgentSignHistory.query.all()
    
    # Calculate stop counts
    total_stops = len(stops)
    
    # Calculate stops for next 7 days
    next_7_days = datetime.now() + timedelta(days=7)
    stops_next_7_days = Stop.query.filter(
        Stop.required_date <= next_7_days,
        Stop.required_date >= datetime.now().date()
    ).count()
    
    # Add ASAP stops to the 7-day count
    asap_stops = Stop.query.filter(Stop.is_asap == True).count()
    stops_next_7_days += asap_stops
    
    # Use fixed departure address  
    departure_address_str = get_fixed_departure_address()
    
    # Preserve driver count from session or calculate from current routes
    current_driver_count = len(set(route.driver_number for route in routes)) if routes else 1
    saved_driver_count = session.get('last_driver_count', current_driver_count)
    
    return render_template('index.html', 
                         stops=stops, 
                         routes=routes, 
                         agent_signs=agent_signs, 
                         datetime=datetime,
                         total_stops=total_stops,
                         stops_next_7_days=stops_next_7_days,
                         departure_address=departure_address_str,
                         current_driver_count=saved_driver_count,
                         google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY', ''))

@main.route('/add_stop', methods=['POST'])
@require_rate_limit('add_stop')
def add_stop():
    """Add a new stop"""
    try:
        # Validate and sanitize form data
        is_valid, errors = SecurityValidator.validate_form_data(request.form)
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('main.index'))
        
        # Combine address fields into a single address string
        street_address = SecurityValidator.sanitize_input(request.form.get('street_address', '').strip())
        apt_unit = SecurityValidator.sanitize_input(request.form.get('apt_unit', '').strip())
        city = SecurityValidator.sanitize_input(request.form.get('city', '').strip())
        state = SecurityValidator.sanitize_input(request.form.get('state', '').strip())
        zip_code = SecurityValidator.sanitize_input(request.form.get('zip_code', '').strip())
        
        # Build full address
        address_parts = [street_address]
        if apt_unit:
            address_parts.append(apt_unit)
        address_parts.extend([city, state, zip_code])
        address = ', '.join(part for part in address_parts if part)
        
        service_type = request.form.get('service_type')
        is_asap = request.form.get('is_asap') == 'on'
        required_date_str = request.form.get('required_date')
        agent_sign_description = request.form.get('agent_sign_description', '').strip()
        has_riders_toppers = request.form.get('has_riders_toppers') == 'on'
        riders_toppers_description = request.form.get('riders_toppers_description', '').strip()
        has_shelter = request.form.get('has_shelter') == 'on'
        
        # Handle manual timestamp override
        manual_timestamp_override = request.form.get('manual_timestamp_override') == 'on'
        manual_timestamp = None
        if manual_timestamp_override:
            manual_timestamp_str = request.form.get('manual_timestamp')
            if manual_timestamp_str:
                try:
                    manual_timestamp = datetime.strptime(manual_timestamp_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash('Invalid timestamp format', 'error')
                    return redirect(url_for('main.index'))
            else:
                flash('Manual timestamp is required when override is checked', 'error')
                return redirect(url_for('main.index'))
        
        # Handle post type and notes based on service type
        post_type = None
        post_type_notes = None
        deliver_notes = None
        
        if service_type == 'install':
            post_type = request.form.get('post_type')
            if post_type == 'Other':
                post_type_notes = request.form.get('post_type_notes')
                if not post_type_notes:
                    flash('Please provide notes for "Other" post type', 'error')
                    return redirect(url_for('main.index'))
                post_type = f"Other - {post_type_notes}"
        elif service_type == 'deliver':
            deliver_notes = request.form.get('deliver_notes')
            if not deliver_notes:
                flash('Please provide delivery notes', 'error')
                return redirect(url_for('main.index'))
            post_type = f"Delivery - {deliver_notes}"
        elif service_type == 'remove':
            post_type = "Removal"
        
        # Validate required fields with specific error messages
        missing_fields = []
        if not street_address:
            missing_fields.append('Street Address')
        if not city:
            missing_fields.append('City')
        if not state:
            missing_fields.append('State')
        if not zip_code:
            missing_fields.append('ZIP Code')
        if not service_type:
            missing_fields.append('Service Type')
        
        if missing_fields:
            flash(f'Please fill in the following required fields: {", ".join(missing_fields)}', 'error')
            return redirect(url_for('main.index'))
            
        if service_type == 'install' and not post_type:
            flash('Please select a post type for installation', 'error')
            return redirect(url_for('main.index'))
        
        if has_riders_toppers and not riders_toppers_description:
            flash('Please provide a description for riders/toppers', 'error')
            return redirect(url_for('main.index'))
        
        # Parse required date
        required_date = None
        if required_date_str and not is_asap:
            try:
                required_date = datetime.strptime(required_date_str, '%Y-%m-%d')
                # Check if date is in the future
                if required_date.date() < date.today():
                    flash('Required date must be in the future', 'error')
                    return redirect(url_for('main.index'))
            except ValueError:
                flash('Invalid date format', 'error')
                return redirect(url_for('main.index'))
        
        # Create new stop
        stop = Stop()
        stop.post_type = post_type or "Unknown"  # Ensure non-null value
        stop.address = address
        stop.service_type = service_type
        stop.is_asap = is_asap
        stop.required_date = required_date
        stop.agent_sign_description = agent_sign_description if service_type == 'install' else None
        stop.has_riders_toppers = has_riders_toppers
        stop.riders_toppers_description = riders_toppers_description if has_riders_toppers else None
        stop.has_shelter = has_shelter
        
        # Set manual timestamp if provided, otherwise use default (current time)
        if manual_timestamp:
            stop.created_at = manual_timestamp
        
        db.session.add(stop)
        
        # Save agent sign description to history if this is an install with a sign description
        if service_type == 'install' and agent_sign_description:
            # Check if there's already a sign history for this address
            existing_sign = AgentSignHistory.query.filter_by(address=address).first()
            if existing_sign:
                # Update existing record
                existing_sign.sign_description = agent_sign_description
                existing_sign.updated_at = datetime.utcnow()
            else:
                # Create new record
                agent_sign_history = AgentSignHistory()
                agent_sign_history.address = address
                agent_sign_history.sign_description = agent_sign_description
                db.session.add(agent_sign_history)
        
        db.session.commit()
        
        flash('Stop added successfully', 'success')
        # Return redirect with both URL parameter and localStorage trigger
        return redirect(url_for('main.index', reset_form='true', form_reset_trigger='true'))
        
    except Exception as e:
        logging.error(f"Error adding stop: {e}")
        flash('Error adding stop', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))

@main.route('/api/stop_counters')
def api_stop_counters():
    """API endpoint to get current stop counters"""
    stops = Stop.query.all()
    total_stops = len(stops)
    
    # Calculate stops for next 7 days
    next_7_days = datetime.now() + timedelta(days=7)
    stops_next_7_days = Stop.query.filter(
        Stop.required_date <= next_7_days,
        Stop.required_date >= datetime.now().date()
    ).count()
    
    # Add ASAP stops to the 7-day count
    asap_stops = Stop.query.filter(Stop.is_asap == True).count()
    stops_next_7_days += asap_stops
    
    # Use fixed departure address
    departure_address_str = get_fixed_departure_address()
    
    return jsonify({
        'total_stops': total_stops,
        'stops_next_7_days': stops_next_7_days,
        'departure_address': departure_address_str
    })

def get_fixed_departure_address():
    """Get the fixed departure address"""
    return "183 DeKalb Industrial Way, Decatur, GA 30030"

@main.route('/generate_routes', methods=['POST'])
@require_rate_limit('generate_routes')
def generate_routes():
    """Generate optimized routes for specified number of drivers with 8-hour workday goals"""
    import time
    start_processing_time = time.time()
    
    try:
        # Get form data and save driver count to session
        num_drivers = int(request.form.get('num_drivers', 1))
        start_time = request.form.get('start_time', '07:00')
        session['last_driver_count'] = num_drivers
        
        # Determine route date - if current time is past start time, schedule for next day
        current_time = datetime.now().time()
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        
        if current_time > start_time_obj:
            route_date = (datetime.now() + timedelta(days=1)).date()
            logging.info(f"Current time {current_time} is past start time {start_time_obj}, scheduling routes for next day: {route_date}")
        else:
            route_date = datetime.now().date()
            logging.info(f"Current time {current_time} is before start time {start_time_obj}, scheduling routes for today: {route_date}")
        
        # Get all stops
        stops = Stop.query.all()
        
        if not stops:
            flash('No stops available to route', 'error')
            return redirect(url_for('main.index'))
        
        # Update traffic data for route segments (monthly snapshots with variance detection)
        stop_addresses = [stop.address for stop in stops]
        traffic_updates = traffic_scheduler.update_route_traffic_data(stop_addresses)
        
        # Log traffic data update results
        if traffic_updates['updates_performed'] > 0:
            logging.info(f"Updated traffic data for {traffic_updates['updates_performed']} route segments")
        
        if traffic_updates['construction_detected']:
            logging.warning(f"Construction detected on {len(traffic_updates['construction_detected'])} route segments")
            for alert in traffic_updates['construction_detected']:
                flash(f"Construction detected: {alert['origin']} to {alert['destination']} (+{alert['variance_minutes']:.1f} min)", 'warning')
        
        if traffic_updates['variance_alerts']:
            logging.info(f"Traffic variance detected on {len(traffic_updates['variance_alerts'])} route segments")
            for alert in traffic_updates['variance_alerts']:
                flash(f"Traffic change: {alert['origin']} to {alert['destination']} (+{alert['variance_minutes']:.1f} min)", 'info')
        
        if num_drivers < 1:
            flash('Number of drivers must be at least 1', 'error')
            return redirect(url_for('main.index'))
        
        # Use fixed departure address
        departure_address_str = get_fixed_departure_address()
        
        # Always clear existing routes before generating new ones
        deleted_count = Route.query.delete()
        logging.info(f"Cleared {deleted_count} existing routes")
        
        # Separate scheduled and ASAP stops
        scheduled_stops = [s for s in stops if not s.is_asap and s.required_date]
        asap_stops = [s for s in stops if s.is_asap or not s.required_date]
        
        # Sort scheduled stops by required date
        scheduled_stops.sort(key=lambda x: x.required_date or datetime.max)
        
        # Use geographic clustering for optimal route distribution with fuel efficiency
        logging.info(f"Starting geographic route optimization for {len(stops)} stops (Toyota Tundra fuel analysis)")
        
        # Convert all stops to format for geographic clustering
        all_stops_data = []
        for stop in stops:
            stop_data = {
                'id': stop.id,
                'address': stop.address,
                'post_type': stop.post_type,
                'service_type': stop.service_type,
                'is_asap': stop.is_asap,
                'required_date': stop.required_date
            }
            all_stops_data.append(stop_data)
        
        if len(all_stops_data) == 0:
            flash('No active stops found to generate routes.', 'warning')
            return redirect(url_for('main.index'))
        
        # Use geographic clustering to group nearby stops
        from geographic_clustering import GeographicClusterer
        clusterer = GeographicClusterer()
        
        try:
            optimized_routes = clusterer.get_optimized_stop_distribution(all_stops_data, num_drivers)
            logging.info(f"Generated {len([r for r in optimized_routes if r])} geographically optimized routes")
        except Exception as e:
            logging.error(f"Geographic clustering failed: {e}, using simple distribution")
            # Fallback to simple distribution
            stops_per_driver = len(all_stops_data) // num_drivers
            remainder = len(all_stops_data) % num_drivers
            
            optimized_routes = []
            current_index = 0
            
            for driver in range(num_drivers):
                driver_stops = stops_per_driver + (1 if driver < remainder else 0)
                if driver_stops > 0:
                    route = list(range(current_index, current_index + driver_stops))
                    optimized_routes.append(route)
                    current_index += driver_stops
                else:
                    optimized_routes.append([])  # Empty route for excess drivers
        
        # Create route records for each driver (skip empty routes)
        routes_created = 0
        for driver_num, route_indices in enumerate(optimized_routes, 1):
            if not route_indices:
                logging.info(f"Skipping empty route for driver {driver_num}")
                continue
            
            # Get stops for this route (ensure indices are valid)
            valid_indices = [i for i in route_indices if i < len(all_stops_data)]
            route_stops = [all_stops_data[i] for i in valid_indices]
            
            # Calculate estimated time with Google Maps API or fallback estimates
            if route_stops:
                # Service time: 10 minutes per stop (install/pickup/removal)
                service_time = len(route_stops) * 10
                
                # Get real drive times using Google Maps API
                from google_maps_service import GoogleMapsService
                maps_service = GoogleMapsService()
                
                # Extract addresses from route stops
                stop_addresses = [stop['address'] for stop in route_stops]
                departure_address = get_fixed_departure_address()
                
                # Get drive times from Google Maps or fallback estimates
                try:
                    drive_times_list, departure_to_first, last_to_departure = maps_service.get_route_drive_times(
                        departure_address, stop_addresses
                    )
                    
                    # If Google Maps API failed, use fallback estimates
                    if departure_to_first == 0 and last_to_departure == 0 and not drive_times_list:
                        drive_times_list, departure_to_first, last_to_departure = maps_service.get_fallback_drive_times(
                            departure_address, stop_addresses, start_time
                        )
                        traffic_description = "fallback estimates"
                    else:
                        traffic_description = "Google Maps real-time"
                        
                    drive_time_between_stops = sum(drive_times_list) if drive_times_list else 0
                    
                except Exception as e:
                    logging.warning(f"Google Maps service error: {e}, using fallback estimates")
                    # Use fallback estimates if Google Maps fails
                    drive_times_list, departure_to_first, last_to_departure = maps_service.get_fallback_drive_times(
                        departure_address, stop_addresses, start_time
                    )
                    drive_time_between_stops = sum(drive_times_list) if drive_times_list else 0
                    traffic_description = "fallback estimates"
                
                total_time = service_time + drive_time_between_stops + departure_to_first + last_to_departure
                
                # Calculate fuel cost for this route using Toyota Tundra efficiency
                from fuel_efficiency import TundraFuelCalculator
                fuel_calc = TundraFuelCalculator()
                
                route_stops_for_fuel = [{'address': stop['address']} for stop in route_stops]
                fuel_data = fuel_calc.calculate_route_fuel_efficiency(
                    route_stops_for_fuel, departure_address, int(start_time.split(':')[0])
                )
                
                fuel_cost = fuel_data.get('total_fuel_cost', 0)
                estimated_miles = fuel_data.get('total_distance_miles', 0)
                cost_per_hour = fuel_cost / (total_time / 60) if total_time > 0 else 0
                
                logging.info(f"Driver {driver_num} route breakdown ({traffic_description}): "
                           f"Service: {service_time}min, Drive: {drive_time_between_stops}min, "
                           f"Departure: {departure_to_first + last_to_departure}min, "
                           f"Total: {total_time}min, Distance: {estimated_miles:.1f}mi, "
                           f"Fuel: ${fuel_cost:.2f} (${cost_per_hour:.2f}/hr, 2004-2006 Tundra)")
            else:
                total_time = 0
            
            # Check if route exceeds 8-hour limit and warn
            if total_time > 480:  # 8 hours = 480 minutes
                flash(f'Warning: Driver {driver_num} route exceeds 8 hours ({total_time//60}h {total_time%60}m)', 'warning')
            
            # Create route record
            stop_sequence = json.dumps([all_stops_data[i]['id'] for i in valid_indices])
            
            # Store Google Maps drive time data for UI display
            google_maps_data = {
                'departure_to_first': departure_to_first,
                'between_stops': drive_times_list,
                'last_to_departure': last_to_departure,
                'data_source': traffic_description
            }
            
            # Calculate lead time in weeks from today to route date
            today = date.today()
            days_ahead = (route_date - today).days
            lead_time_weeks = max(0, days_ahead // 7)  # Convert days to weeks
            
            # Check overtime approval using TSP solver logic
            from tsp_solver import TSPSolver
            tsp_solver = TSPSolver()
            overtime_approved, overtime_reason = tsp_solver.check_overtime_approval(
                total_time, lead_time_weeks, allow_overtime=True
            )
            
            # Log overtime information
            if total_time > 480:  # Over 8 hours
                overtime_hours = (total_time - 480) / 60
                logging.info(f"Driver {driver_num} overtime: {overtime_hours:.1f} hours, {overtime_reason}")
            
            route = Route()
            route.driver_number = driver_num
            route.stop_sequence = stop_sequence
            route.total_time_minutes = total_time
            route.start_time = start_time
            route.route_date = route_date
            route.google_maps_data = json.dumps(google_maps_data)
            route.overtime_approved = overtime_approved
            route.lead_time_weeks = lead_time_weeks
            
            db.session.add(route)
            routes_created += 1
            logging.info(f"Created route for driver {driver_num}: {len(valid_indices)} stops, {total_time} minutes")
        
        db.session.commit()
        processing_time = time.time() - start_processing_time
        total_routes = routes_created
        flash(f'Routes generated successfully for {total_routes} driver(s) in {processing_time:.1f} seconds. Previous routes cleared and replaced.', 'success')
        logging.info(f"Route generation completed in {processing_time:.2f} seconds")
        
        # Add logging to verify routes were created
        final_routes = Route.query.all()
        logging.info(f"Final route count after generation: {len(final_routes)}")
        for route in final_routes:
            logging.info(f"Route {route.driver_number}: {len(route.stop_sequence) if route.stop_sequence else 0} stops, {route.total_time_minutes} minutes")
        
    except Exception as e:
        import traceback
        logging.error(f"Error generating routes: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Error generating routes: {str(e)}', 'error')
        db.session.rollback()
    
    # Direct redirect with multiple cache-busting parameters
    from flask import make_response
    import time as time_module
    timestamp = int(time_module.time() * 1000)
    
    # Create response with multiple URL parameters to ensure cache bypass
    redirect_url = url_for('main.index', 
                          refresh='routes', 
                          v=timestamp, 
                          update='true',
                          cache_bust=timestamp,
                          _external=False)
    
    response = make_response(redirect(redirect_url))
    
    # Maximum strength cache prevention headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['ETag'] = f'"{timestamp}"'
    response.headers['Vary'] = '*'
    response.headers['X-Cache-Control'] = 'no-cache'
    
    logging.info(f"Redirecting to: {redirect_url}")
    return response

@main.route('/delete_stop/<int:stop_id>')
def delete_stop(stop_id):
    """Delete a stop"""
    try:
        stop = Stop.query.get_or_404(stop_id)
        db.session.delete(stop)
        db.session.commit()
        flash('Stop deleted successfully', 'success')
    except Exception as e:
        logging.error(f"Error deleting stop: {e}")
        flash('Error deleting stop', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))



@main.route('/clear_routes')
def clear_routes():
    """Clear all generated routes"""
    try:
        Route.query.delete()
        db.session.commit()
        flash('All routes cleared', 'success')
    except Exception as e:
        logging.error(f"Error clearing routes: {e}")
        flash('Error clearing routes', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))

@main.route('/get_agent_sign/<path:address>')
def get_agent_sign(address):
    """Get agent sign description for a given address"""
    agent_sign = AgentSignHistory.query.filter_by(address=address).first()
    if agent_sign:
        return jsonify({
            'found': True,
            'description': agent_sign.sign_description,
            'updated_at': agent_sign.updated_at.strftime('%Y-%m-%d')
        })
    return jsonify({'found': False})
