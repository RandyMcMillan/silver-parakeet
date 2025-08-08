from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, date, timedelta
from models import Stop, Route, AgentSignHistory, DriverCount, DriverDepartureAddress, TrafficData, db
from tsp_solver import TSPSolver
from traffic_scraper import TrafficDataScraper
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
    
    # Get stored driver count from database
    current_driver_count = get_stored_driver_count()
    saved_driver_count = current_driver_count
    
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
def add_stop():
    """Add a new stop"""
    try:
        # Combine address fields into a single address string
        street_address = request.form.get('street_address', '').strip()
        apt_unit = request.form.get('apt_unit', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        
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
        
        # Validate required fields
        if not street_address or not city or not state or not zip_code or not service_type:
            flash('Please fill in all required address fields and service type', 'error')
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
        stop.post_type = post_type
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

def get_stored_driver_count():
    """Get the currently stored driver count from database"""
    driver_count_record = DriverCount.query.first()
    if driver_count_record:
        return driver_count_record.count
    else:
        # Initialize with 1 driver if no record exists
        new_record = DriverCount(count=1)
        db.session.add(new_record)
        db.session.commit()
        return 1

def update_stored_driver_count(count):
    """Update the stored driver count in database"""
    driver_count_record = DriverCount.query.first()
    if driver_count_record:
        driver_count_record.count = count
        driver_count_record.updated_at = datetime.utcnow()
    else:
        driver_count_record = DriverCount(count=count)
        db.session.add(driver_count_record)
    db.session.commit()
    logging.info(f"Updated stored driver count to: {count}")

@main.route('/generate_routes', methods=['POST'])
def generate_routes():
    """Generate optimized routes for specified number of drivers with 8-hour workday goals"""
    import time
    start_processing_time = time.time()
    
    print("🚀 STARTING ROUTE GENERATION")
    logging.info("🚀 STARTING ROUTE GENERATION")
    
    try:
        # Get form data and update stored driver count
        num_drivers = int(request.form.get('num_drivers', 1))
        start_time = request.form.get('start_time', '07:00')
        update_stored_driver_count(num_drivers)
        
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
        
        # Use geographic clustering for optimal route distribution
        print(f"🌍 STARTING GEOGRAPHIC OPTIMIZATION FOR {len(stops)} STOPS")
        logging.info(f"Starting geographic route optimization for {len(stops)} stops")
        
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
        
        # Filter stops to prevent routes over 9 hours and defer ASAP stops if needed
        asap_stops = [stop for stop in all_stops_data if stop.get('is_asap', False)]
        scheduled_stops = [stop for stop in all_stops_data if not stop.get('is_asap', False)]
        
        logging.info(f"Stop breakdown: {len(scheduled_stops)} scheduled, {len(asap_stops)} ASAP")
        
        # DEBUG: Always apply 8-hour balancing regardless of overtime estimate
        print("🔧 ALWAYS BYPASSING CLUSTERING - USING SIMPLE DISTRIBUTION + 8-HOUR BALANCING")
        logging.info("🔧 ALWAYS BYPASSING CLUSTERING - USING SIMPLE DISTRIBUTION + 8-HOUR BALANCING")
        
        # Estimate if adding all stops would create excessive overtime
        estimated_total_minutes = len(all_stops_data) * 25  # Rough per-stop estimate
        minutes_per_driver = estimated_total_minutes / num_drivers
        logging.info(f"Estimated {minutes_per_driver:.1f} minutes per driver ({minutes_per_driver/60:.1f} hours)")
        
        if minutes_per_driver > 540:  # Over 9 hours average
            # Calculate how many stops we can fit within 9-hour limits
            max_stops_for_9h = int((num_drivers * 540) / 25)  # 9 hours * drivers / 25min per stop
            
            # Always include ALL scheduled stops (they have priority)
            stops_to_process = scheduled_stops.copy()
            
            # Add ASAP stops only if they fit within 9-hour limits
            remaining_capacity = max_stops_for_9h - len(scheduled_stops)
            if remaining_capacity > 0 and asap_stops:
                stops_to_add = asap_stops[:remaining_capacity]
                stops_deferred = asap_stops[remaining_capacity:]
                stops_to_process.extend(stops_to_add)
                
                if stops_deferred:
                    flash(f'Route optimization: {len(stops_deferred)} ASAP stops deferred to next day to keep all drivers within 9-hour limit', 'info')
                    logging.info(f"Deferred {len(stops_deferred)} ASAP stops to prevent excessive overtime")
            elif remaining_capacity <= 0:
                flash(f'Warning: {len(asap_stops)} ASAP stops deferred - all scheduled stops already fill 9-hour capacity', 'warning')
                stops_deferred = asap_stops
            else:
                stops_to_process.extend(asap_stops)
                
            all_stops_data = stops_to_process
        else:
            # No overtime limiting needed - use all stops
            all_stops_data = all_stops_data
            
        # Skip clustering completely and go straight to simple distribution + balancing
        logging.info("🔧 BYPASSING CLUSTERING - USING SIMPLE DISTRIBUTION + 8-HOUR BALANCING")
        
        # Simple distribution
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
        
        logging.info(f"Simple distribution complete: {[len(route) for route in optimized_routes]} stops per driver")
        
        # MANDATORY: Apply 8-hour balancing - Import and create clusterer first
        from geographic_clustering import GeographicClusterer
        clusterer = GeographicClusterer()
        
        print("🔥 STARTING AGGRESSIVE 8-HOUR REDISTRIBUTION 🔥")
        logging.info("🔥 STARTING AGGRESSIVE 8-HOUR REDISTRIBUTION 🔥")
        
        # Log the current route distribution before balancing
        route_lengths_before = [len(route) for route in optimized_routes]
        print(f"Routes BEFORE balancing: {route_lengths_before} stops")
        
        try:
            optimized_routes = clusterer.balance_workload_for_8_hours(optimized_routes, all_stops_data)
            route_lengths_after = [len(route) for route in optimized_routes]
            print(f"Routes AFTER balancing: {route_lengths_after} stops")
            print("✅ 8-HOUR BALANCING COMPLETED SUCCESSFULLY")
            logging.info("✅ 8-HOUR BALANCING COMPLETED SUCCESSFULLY")
        except Exception as balance_error:
            print(f"❌ 8-HOUR BALANCING FAILED: {balance_error}")
            logging.error(f"❌ 8-HOUR BALANCING FAILED: {balance_error}")
            import traceback
            traceback.print_exc()
            logging.error(f"Balancing traceback: {traceback.format_exc()}")
        
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
                
                logging.info(f"Driver {driver_num} route time breakdown ({traffic_description}): "
                           f"Service: {service_time}min, "
                           f"Between stops: {drive_time_between_stops}min, "
                           f"Departure trips: {departure_to_first + last_to_departure}min, "
                           f"Total: {total_time}min")
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
            
            route = Route()
            route.driver_number = driver_num
            route.stop_sequence = stop_sequence
            route.total_time_minutes = total_time
            route.start_time = start_time
            route.route_date = route_date
            route.google_maps_data = json.dumps(google_maps_data)
            
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
