from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
from models import Stop, Route, db
from tsp_solver import TSPSolver
import json
import logging

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Main page with route optimization interface"""
    stops = Stop.query.all()
    routes = Route.query.all()
    
    return render_template('index.html', stops=stops, routes=routes, datetime=datetime)

@main.route('/add_stop', methods=['POST'])
def add_stop():
    """Add a new stop"""
    try:
        address = request.form.get('address')
        service_type = request.form.get('service_type')
        is_asap = request.form.get('is_asap') == 'on'
        required_date_str = request.form.get('required_date')
        
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
        if not address or not service_type:
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('main.index'))
            
        if service_type == 'install' and not post_type:
            flash('Please select a post type for installation', 'error')
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
            required_date=required_date
        )
        
        db.session.add(stop)
        db.session.commit()
        
        flash('Stop added successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error adding stop: {e}")
        flash('Error adding stop', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))



@main.route('/generate_routes', methods=['POST'])
def generate_routes():
    """Generate optimized routes for specified number of drivers"""
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
        
        # Clear existing routes
        Route.query.delete()
        
        # Separate scheduled and ASAP stops
        scheduled_stops = [s for s in stops if not s.is_asap and s.required_date]
        asap_stops = [s for s in stops if s.is_asap or not s.required_date]
        
        # Sort scheduled stops by required date
        scheduled_stops.sort(key=lambda x: x.required_date or datetime.max)
        
        # Initialize TSP solver with start time
        tsp_solver = TSPSolver()
        
        # Initialize driver workloads
        driver_routes = {i: [] for i in range(1, num_drivers + 1)}
        driver_times = {i: 0 for i in range(1, num_drivers + 1)}
        
        # First, assign scheduled stops (priority)
        for stop in scheduled_stops:
            # Find driver with least current workload
            min_time_driver = min(driver_times.keys(), key=lambda k: driver_times[k])
            driver_routes[min_time_driver].append(stop)
            driver_times[min_time_driver] += 10  # Base service time
        
        # Then, assign ASAP stops to balance workloads
        for stop in asap_stops:
            # Find driver with least current workload
            min_time_driver = min(driver_times.keys(), key=lambda k: driver_times[k])
            driver_routes[min_time_driver].append(stop)
            driver_times[min_time_driver] += 10  # Base service time
        
        # Optimize each driver's route using TSP
        for driver_num in range(1, num_drivers + 1):
            route_stops = driver_routes[driver_num]
            
            if not route_stops:
                continue
            
            # Convert stops to format for TSP solver
            stop_data = []
            for stop in route_stops:
                stop_data.append({
                    'id': stop.id,
                    'address': stop.address,
                    'post_type': stop.post_type,
                    'service_type': stop.service_type,
                    'is_asap': stop.is_asap
                })
            
            # Solve TSP for this driver's stops with traffic consideration
            if len(stop_data) > 1:
                optimal_order = tsp_solver.solve_tsp_with_traffic(stop_data, start_time)
                # Reorder stops based on TSP solution
                ordered_stops = [route_stops[i] for i in optimal_order]
            else:
                ordered_stops = route_stops
            
            # Calculate total time including travel with traffic
            total_time = tsp_solver.calculate_total_time_with_traffic(stop_data, list(range(len(stop_data))), start_time)
            
            # Create route record
            stop_sequence = json.dumps([stop.id for stop in ordered_stops])
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
