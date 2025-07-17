from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
from models import Stop, Employee, Route, db
from tsp_solver import TSPSolver
import json
import logging

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Main page with route optimization interface"""
    stops = Stop.query.all()
    employees = Employee.query.all()
    routes = Route.query.all()
    
    return render_template('index.html', stops=stops, employees=employees, routes=routes, datetime=datetime)

@main.route('/add_stop', methods=['POST'])
def add_stop():
    """Add a new stop"""
    try:
        post_type = request.form.get('post_type')
        address = request.form.get('address')
        service_type = request.form.get('service_type')
        is_asap = request.form.get('is_asap') == 'on'
        required_date_str = request.form.get('required_date')
        
        # Validate required fields
        if not post_type or not address or not service_type:
            flash('Please fill in all required fields', 'error')
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

@main.route('/add_employee', methods=['POST'])
def add_employee():
    """Add a new employee"""
    try:
        name = request.form.get('name')
        
        if not name:
            flash('Employee name is required', 'error')
            return redirect(url_for('main.index'))
        
        # Check if employee already exists
        if Employee.query.filter_by(name=name).first():
            flash('Employee with this name already exists', 'error')
            return redirect(url_for('main.index'))
        
        employee = Employee(name=name)
        db.session.add(employee)
        db.session.commit()
        
        flash('Employee added successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error adding employee: {e}")
        flash('Error adding employee', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))

@main.route('/generate_routes', methods=['POST'])
def generate_routes():
    """Generate optimized routes for all employees"""
    try:
        # Get all stops and employees
        stops = Stop.query.all()
        employees = Employee.query.all()
        
        if not stops:
            flash('No stops available to route', 'error')
            return redirect(url_for('main.index'))
        
        if not employees:
            flash('No employees available for routing', 'error')
            return redirect(url_for('main.index'))
        
        # Clear existing routes
        Route.query.delete()
        
        # Separate scheduled and ASAP stops
        scheduled_stops = [s for s in stops if not s.is_asap and s.required_date]
        asap_stops = [s for s in stops if s.is_asap or not s.required_date]
        
        # Sort scheduled stops by required date
        scheduled_stops.sort(key=lambda x: x.required_date or datetime.max)
        
        # Initialize TSP solver
        tsp_solver = TSPSolver()
        
        # Initialize employee workloads
        employee_routes = {emp.id: [] for emp in employees}
        employee_times = {emp.id: 0 for emp in employees}
        
        # First, assign scheduled stops (priority)
        for stop in scheduled_stops:
            # Find employee with least current workload
            min_time_employee = min(employee_times.keys(), key=lambda k: employee_times[k])
            employee_routes[min_time_employee].append(stop)
            employee_times[min_time_employee] += 10  # Base service time
        
        # Then, assign ASAP stops to balance workloads
        for stop in asap_stops:
            # Find employee with least current workload
            min_time_employee = min(employee_times.keys(), key=lambda k: employee_times[k])
            employee_routes[min_time_employee].append(stop)
            employee_times[min_time_employee] += 10  # Base service time
        
        # Optimize each employee's route using TSP
        for employee in employees:
            route_stops = employee_routes[employee.id]
            
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
            
            # Solve TSP for this employee's stops
            if len(stop_data) > 1:
                optimal_order = tsp_solver.solve_tsp(stop_data)
                # Reorder stops based on TSP solution
                ordered_stops = [route_stops[i] for i in optimal_order]
            else:
                ordered_stops = route_stops
            
            # Calculate total time including travel
            total_time = tsp_solver.calculate_total_time(stop_data, list(range(len(stop_data))))
            
            # Create route record
            stop_sequence = json.dumps([stop.id for stop in ordered_stops])
            route = Route(
                employee_id=employee.id,
                stop_sequence=stop_sequence,
                total_time_minutes=total_time
            )
            
            db.session.add(route)
        
        db.session.commit()
        flash('Routes generated successfully', 'success')
        
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

@main.route('/delete_employee/<int:employee_id>')
def delete_employee(employee_id):
    """Delete an employee"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        # Delete associated routes
        Route.query.filter_by(employee_id=employee_id).delete()
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully', 'success')
    except Exception as e:
        logging.error(f"Error deleting employee: {e}")
        flash('Error deleting employee', 'error')
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
