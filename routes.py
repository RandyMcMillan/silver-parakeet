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
    
    # Get active departure address
    departure_address = DriverDepartureAddress.query.filter_by(is_active=True).first()
    
    return render_template('index.html', 
                         stops=stops, 
                         routes=routes, 
                         agent_signs=agent_signs, 
                         datetime=datetime,
                         total_stops=total_stops,
                         stops_next_7_days=stops_next_7_days,
                         departure_address=departure_address)

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
        stop = Stop(
            post_type=post_type,
            address=address,
            service_type=service_type,
            is_asap=is_asap,
            required_date=required_date,
            agent_sign_description=agent_sign_description if service_type == 'install' else None,
            has_riders_toppers=has_riders_toppers,
            riders_toppers_description=riders_toppers_description if has_riders_toppers else None,
            has_shelter=has_shelter
        )
        
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
                agent_sign_history = AgentSignHistory(
                    address=address,
                    sign_description=agent_sign_description
                )
                db.session.add(agent_sign_history)
        
        db.session.commit()
        
        flash('Stop added successfully', 'success')
        return redirect(url_for('main.index', reset_form='true'))
        
    except Exception as e:
        logging.error(f"Error adding stop: {e}")
        flash('Error adding stop', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))

@main.route('/set_departure_address', methods=['POST'])
def set_departure_address():
    """Set or update the driver departure address"""
    try:
        new_address = request.form.get('departure_address', '').strip()
        
        if not new_address:
            flash('Please enter a departure address', 'error')
            return redirect(url_for('main.index'))
        
        # Deactivate existing departure addresses
        DriverDepartureAddress.query.update({'is_active': False})
        
        # Create new active departure address
        departure_address = DriverDepartureAddress(
            address=new_address,
            is_active=True
        )
        
        db.session.add(departure_address)
        db.session.commit()
        
        flash('Departure address updated successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error setting departure address: {e}")
        flash('Error updating departure address', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))

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
        
        # Get departure address
        departure_address = DriverDepartureAddress.query.filter_by(is_active=True).first()
        if not departure_address:
            flash('Please set a departure address first', 'error')
            return redirect(url_for('main.index'))
        
        # Clear existing routes
        Route.query.delete()
        
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
        
        # Optimize routes for 8-hour workday constraint
        optimized_routes = tsp_solver.optimize_for_8_hour_workday(all_stops_data, start_time, num_drivers)
        
        # Create route records for each driver
        for driver_num, route_indices in enumerate(optimized_routes, 1):
            if not route_indices:
                continue
            
            # Get stops for this route
            route_stops = [all_stops_data[i] for i in route_indices]
            
            # Calculate total time with traffic awareness
            total_time = tsp_solver.calculate_total_time_with_traffic(route_stops, list(range(len(route_stops))), start_time)
            
            # Add departure address travel time
            if route_stops:
                first_stop_address = route_stops[0]['address']
                traffic_data = traffic_scraper.get_best_traffic_estimate(departure_address.address, first_stop_address)
                if traffic_data:
                    total_time += traffic_data['travel_time_minutes']
                else:
                    # Fallback: estimate 30 minutes to first stop
                    total_time += 30
            
            # Check if route exceeds 8-hour limit and warn
            if total_time > 480:  # 8 hours = 480 minutes
                flash(f'Warning: Driver {driver_num} route exceeds 8 hours ({total_time//60}h {total_time%60}m)', 'warning')
            
            # Create route record
            stop_sequence = json.dumps([all_stops_data[i]['id'] for i in route_indices])
            route = Route(
                driver_number=driver_num,
                stop_sequence=stop_sequence,
                total_time_minutes=total_time,
                start_time=start_time
            )
            
            db.session.add(route)
        
        db.session.commit()
        flash(f'Routes generated successfully for {num_drivers} drivers', 'success')
        
    except Exception as e:
        logging.error(f"Error generating routes: {e}")
        flash('Error generating routes', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))

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
