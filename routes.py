from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date, timedelta
from models import Stop, Route, AgentSignHistory, DriverDepartureAddress, TrafficData, db
from tsp_solver import TSPSolver
from traffic_scraper import TrafficDataScraper
import json
import logging

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Main page with route optimization interface"""
    stops = Stop.query.all()
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
    
    return render_template('index.html', 
                         stops=stops, 
                         routes=routes, 
                         agent_signs=agent_signs, 
                         datetime=datetime,
                         total_stops=total_stops,
                         stops_next_7_days=stops_next_7_days,
                         departure_address=departure_address_str)

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
def generate_routes():
    """Generate optimized routes for specified number of drivers with 8-hour workday goals"""
    try:
        # Get form data
        num_drivers = int(request.form.get('num_drivers', 1))
        start_time = request.form.get('start_time', '07:00')
        
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
        
        # Initialize TSP solver and traffic scraper
        tsp_solver = TSPSolver()
        traffic_scraper = TrafficDataScraper()
        
        # Convert all stops to format for TSP solver
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
        
        # Simple route distribution without external geocoding
        # Distribute stops evenly among drivers
        stops_per_driver = len(all_stops_data) // num_drivers
        remainder = len(all_stops_data) % num_drivers
        
        optimized_routes = []
        current_index = 0
        
        for driver in range(num_drivers):
            driver_stops = stops_per_driver + (1 if driver < remainder else 0)
            route = list(range(current_index, current_index + driver_stops))
            optimized_routes.append(route)
            current_index += driver_stops
        
        # Create route records for each driver
        for driver_num, route_indices in enumerate(optimized_routes, 1):
            if not route_indices:
                continue
            
            # Get stops for this route (ensure indices are valid)
            valid_indices = [i for i in route_indices if i < len(all_stops_data)]
            route_stops = [all_stops_data[i] for i in valid_indices]
            
            # Calculate estimated time with realistic drive times
            if route_stops:
                # Service time: 10 minutes per stop
                service_time = len(route_stops) * 10
                
                # Drive time between stops: 20 minutes average (city driving)
                drive_time_between_stops = (len(route_stops) - 1) * 20 if len(route_stops) > 1 else 0
                
                # Drive time from departure to first stop: 25 minutes average
                departure_to_first = 25
                
                # Drive time from last stop back to departure: 25 minutes average  
                last_to_departure = 25
                
                total_time = service_time + drive_time_between_stops + departure_to_first + last_to_departure
                
                logging.info(f"Driver {driver_num} route time breakdown: "
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
            route = Route()
            route.driver_number = driver_num
            route.stop_sequence = stop_sequence
            route.total_time_minutes = total_time
            route.start_time = start_time
            
            db.session.add(route)
        
        db.session.commit()
        total_routes = len([r for r in optimized_routes if r])
        flash(f'Routes generated successfully for {total_routes} driver(s). Previous routes cleared and replaced.', 'success')
        
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
    
    # Add cache-busting parameter to force browser refresh
    return redirect(url_for('main.index', refresh=True, t=int(datetime.now().timestamp())))

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
