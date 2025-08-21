"""
Optimized Route Generation Module
Streamlined algorithm that eliminates redundancy and properly enforces 8-9 hour shifts
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from app import db
from models import Stop, Route, DriverDepartureAddress, DriverCount
from datetime import datetime, timedelta, date
import json
import logging
from google_maps_service import GoogleMapsService
from tsp_solver import TSPSolver
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell
import io
import base64

main = Blueprint('main', __name__)

def get_fixed_departure_address():
    """Get the fixed departure address"""
    return "183 DeKalb Industrial Way, Decatur, GA 30030"

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

@main.route('/')
def index():
    """Main page with route display"""
    stops = Stop.query.all()
    routes = Route.query.all()
    
    # Get stored driver count or default to 4
    driver_count_record = DriverCount.query.first()
    stored_driver_count = driver_count_record.count if driver_count_record else 4
    
    departure_address = get_fixed_departure_address()
    
    # Count stops by type
    total_stops = len(stops)
    asap_stops = sum(1 for stop in stops if stop.is_asap)
    scheduled_stops = sum(1 for stop in stops if stop.required_date and not stop.is_asap)
    regular_stops = total_stops - asap_stops - scheduled_stops
    
    return render_template('index.html', 
                         stops=stops, 
                         routes=routes,
                         stored_driver_count=stored_driver_count,
                         departure_address=departure_address,
                         total_stops=total_stops,
                         asap_stops=asap_stops,
                         scheduled_stops=scheduled_stops,
                         regular_stops=regular_stops,
                         datetime=datetime)

@main.route('/generate_routes', methods=['POST'])
def generate_routes():
    """
    Streamlined route generation with proper 8-9 hour shift enforcement
    Priority: Scheduled (today) → ASAP (by timestamp) → Regular stops
    """
    import time
    start_time = time.time()
    
    try:
        # Get parameters
        num_drivers = int(request.form.get('num_drivers', 1))
        route_start_time = request.form.get('start_time', '07:00')
        update_stored_driver_count(num_drivers)
        
        # Determine route date
        current_time = datetime.now().time()
        start_time_obj = datetime.strptime(route_start_time, '%H:%M').time()
        
        if current_time > start_time_obj:
            route_date = (datetime.now() + timedelta(days=1)).date()
            logging.info(f"Scheduling routes for tomorrow: {route_date}")
        else:
            route_date = datetime.now().date()
            logging.info(f"Scheduling routes for today: {route_date}")
        
        # Get all stops and validate
        all_stops = Stop.query.all()
        if not all_stops:
            flash('No stops available to route', 'error')
            return redirect(url_for('main.index'))
        
        if num_drivers < 1:
            flash('Number of drivers must be at least 1', 'error')
            return redirect(url_for('main.index'))
        
        departure_address = get_fixed_departure_address()
        
        # Clear existing routes
        Route.query.delete()
        logging.info(f"Cleared existing routes")
        
        # PHASE 1: Prioritize stops
        priority_list = []
        
        # Highest priority: Scheduled for today
        for stop in all_stops:
            if stop.required_date and stop.required_date.date() == route_date:
                priority_list.append({
                    'stop': stop,
                    'priority': 1,
                    'timestamp': stop.created_at
                })
        
        # Second priority: ASAP stops
        for stop in all_stops:
            if stop.is_asap and not (stop.required_date and stop.required_date.date() == route_date):
                priority_list.append({
                    'stop': stop,
                    'priority': 2,
                    'timestamp': stop.created_at
                })
        
        # Third priority: Regular stops
        for stop in all_stops:
            if not stop.is_asap and not (stop.required_date and stop.required_date.date() == route_date):
                priority_list.append({
                    'stop': stop,
                    'priority': 3,
                    'timestamp': stop.created_at
                })
        
        # Sort by priority, then by timestamp
        priority_list.sort(key=lambda x: (x['priority'], x['timestamp']))
        
        logging.info(f"Prioritized {len(priority_list)} stops: "
                    f"{sum(1 for x in priority_list if x['priority']==1)} scheduled, "
                    f"{sum(1 for x in priority_list if x['priority']==2)} ASAP, "
                    f"{sum(1 for x in priority_list if x['priority']==3)} regular")
        
        # PHASE 2: Smart distribution with real-time estimates
        maps_service = GoogleMapsService()
        driver_routes = [[] for _ in range(num_drivers)]
        driver_times = [0 for _ in range(num_drivers)]  # Track actual time per driver
        deferred_stops = []
        
        # Constants - calibrated for 8-9 hour shifts with real Google Maps times
        SERVICE_TIME = 10  # minutes per stop
        MAX_SHIFT = 540   # 9 hours in minutes
        MIN_SHIFT = 480   # 8 hours in minutes
        TARGET_SHIFT = 480  # 8 hours target - conservative to account for TSP overhead
        # Account for TSP reorganization adding distance
        # TSP optimization can add 15-20% to drive times by optimizing for geography
        REALISTIC_TIME_PER_STOP = 32  # Conservative estimate accounting for TSP overhead
        
        # Process stops in priority order
        for item in priority_list:
            stop = item['stop']
            assigned = False
            
            # Find driver with minimum time who can take this stop
            best_driver = -1
            best_time = float('inf')
            
            for driver_idx in range(num_drivers):
                # Skip if driver already at max capacity
                if driver_times[driver_idx] >= MAX_SHIFT:
                    continue
                
                # Estimate time if we add this stop using calibrated times
                if not driver_routes[driver_idx]:
                    # First stop includes round trip overhead
                    estimated_time = REALISTIC_TIME_PER_STOP + 25  # First stop + return trip
                else:
                    # Additional stops use calibrated average
                    estimated_time = REALISTIC_TIME_PER_STOP
                
                new_total = driver_times[driver_idx] + estimated_time
                
                # Prefer drivers under target shift, but allow up to max
                if new_total <= MAX_SHIFT:
                    # Prioritize filling drivers to target shift first
                    if driver_times[driver_idx] < TARGET_SHIFT:
                        if driver_times[driver_idx] < best_time or best_time >= TARGET_SHIFT:
                            best_driver = driver_idx
                            best_time = driver_times[driver_idx]
                    # Then consider drivers between target and max if no better option
                    elif best_driver == -1 and driver_times[driver_idx] < best_time:
                        best_driver = driver_idx
                        best_time = driver_times[driver_idx]
            
            if best_driver >= 0:
                driver_routes[best_driver].append(stop)
                # Update time estimate with calibrated values
                if len(driver_routes[best_driver]) == 1:
                    driver_times[best_driver] += REALISTIC_TIME_PER_STOP + 25
                else:
                    driver_times[best_driver] += REALISTIC_TIME_PER_STOP
                assigned = True
            
            if not assigned:
                deferred_stops.append(stop)
        
        # Log distribution results
        for i in range(num_drivers):
            hours = driver_times[i] / 60
            status = "✅" if MIN_SHIFT <= driver_times[i] <= MAX_SHIFT else "⚠️"
            logging.info(f"{status} Driver {i+1}: {len(driver_routes[i])} stops, "
                        f"~{driver_times[i]} min ({hours:.1f} hours)")
        
        if deferred_stops:
            deferred_asap = sum(1 for s in deferred_stops if s.is_asap)
            logging.warning(f"📅 Deferred {len(deferred_stops)} stops ({deferred_asap} ASAP) to maintain shift limits")
            flash(f'{len(deferred_stops)} stops deferred to tomorrow ({deferred_asap} ASAP) to maintain 9-hour limit', 'warning')
        
        # PHASE 3: Optimize each route with TSP and get accurate times
        routes_created = 0
        total_actual_time = 0
        
        for driver_num, route_stops in enumerate(driver_routes, 1):
            if not route_stops:
                logging.info(f"Driver {driver_num} has no stops assigned")
                continue
            
            # Use TSP to optimize stop order with efficient caching
            tsp_solver = TSPSolver()
            
            # Prepare stops for TSP optimization
            stops_data = []
            for stop in route_stops:
                stops_data.append({
                    'id': stop.id,
                    'address': stop.address,
                    'service_type': stop.service_type,
                    'is_asap': stop.is_asap,
                    'required_date': stop.required_date
                })
            
            try:
                # Get optimized order with timeout protection
                optimized_order = tsp_solver.solve_tsp_with_departure(stops_data, departure_address)
                optimized_stops = [route_stops[i] for i in optimized_order]
                logging.info(f"Driver {driver_num}: TSP optimization completed successfully")
            except Exception as e:
                logging.warning(f"TSP optimization failed: {e}, using priority order")
                optimized_stops = route_stops
            
            # Calculate actual time with Google Maps
            service_time = len(optimized_stops) * SERVICE_TIME
            
            try:
                drive_times_list, departure_to_first, last_to_departure = maps_service.get_route_drive_times(
                    departure_address, [s.address for s in optimized_stops]
                )
                
                if not any([departure_to_first, last_to_departure, drive_times_list]):
                    # Fallback if API fails
                    drive_times_list, departure_to_first, last_to_departure = maps_service.get_fallback_drive_times(
                        departure_address, [s.address for s in optimized_stops], route_start_time
                    )
                    data_source = "fallback estimates"
                else:
                    data_source = "Google Maps real-time"
                
                drive_time = sum(drive_times_list) + departure_to_first + last_to_departure
                total_time = service_time + drive_time
                
            except Exception as e:
                logging.error(f"Error calculating route times: {e}")
                # Use conservative fallback
                drive_time = len(optimized_stops) * 10 + 30  # 10 min between + 30 for departure
                total_time = service_time + drive_time
                data_source = "fallback estimates"
            
            total_actual_time += total_time
            
            # Log actual vs estimated
            hours = total_time / 60
            status = "✅" if MIN_SHIFT <= total_time <= MAX_SHIFT else "⚠️"
            logging.info(f"{status} Driver {driver_num} actual: {len(optimized_stops)} stops, "
                        f"{total_time} min ({hours:.1f} hours) via {data_source}")
            
            # Warn if exceeds limits
            if total_time > MAX_SHIFT:
                flash(f'Warning: Driver {driver_num} route exceeds 9 hours ({hours:.1f} hours)', 'warning')
            elif total_time < MIN_SHIFT:
                flash(f'Note: Driver {driver_num} route under 8 hours ({hours:.1f} hours) - not enough stops available', 'info')
            
            # Create route record
            stop_sequence = json.dumps([s.id for s in optimized_stops])
            google_maps_data = {
                'departure_to_first': departure_to_first,
                'between_stops': drive_times_list,
                'last_to_departure': last_to_departure,
                'data_source': data_source
            }
            
            route = Route(
                driver_number=driver_num,
                stop_sequence=stop_sequence,
                total_time_minutes=total_time,
                start_time=route_start_time,
                route_date=route_date,
                google_maps_data=json.dumps(google_maps_data)
            )
            
            db.session.add(route)
            routes_created += 1
        
        db.session.commit()
        
        # Summary statistics
        processing_time = time.time() - start_time
        avg_time = total_actual_time / num_drivers if num_drivers > 0 else 0
        
        logging.info(f"✅ Route generation complete: {routes_created} routes in {processing_time:.1f}s")
        logging.info(f"Average route time: {avg_time:.0f} min ({avg_time/60:.1f} hours)")
        
        flash(f'Successfully generated {routes_created} optimized routes', 'success')
        
        # Redirect with cache buster
        import time as t
        cache_buster = str(int(t.time() * 1000))
        return redirect(url_for('main.index') + f'?refresh=routes&v={cache_buster}')
        
    except Exception as e:
        logging.error(f"Route generation error: {e}")
        flash(f'Error generating routes: {str(e)}', 'error')
        db.session.rollback()
        return redirect(url_for('main.index'))

# Add remaining route handlers...
@main.route('/add_stop', methods=['POST'])
def add_stop():
    """Add a new stop"""
    try:
        stop = Stop(
            post_type=request.form.get('post_type'),
            address=request.form.get('address'),
            service_type=request.form.get('service_type'),
            is_asap=request.form.get('is_asap') == 'on',
            required_date=datetime.strptime(request.form.get('required_date'), '%Y-%m-%d') if request.form.get('required_date') else None,
            agent_sign_description=request.form.get('agent_sign_description'),
            has_riders_toppers=request.form.get('has_riders_toppers') == 'on',
            riders_toppers_description=request.form.get('riders_toppers_description'),
            has_shelter=request.form.get('has_shelter') == 'on'
        )
        
        db.session.add(stop)
        db.session.commit()
        
        flash('Stop added successfully', 'success')
    except Exception as e:
        flash(f'Error adding stop: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))

@main.route('/delete_stop/<int:stop_id>', methods=['POST'])
def delete_stop(stop_id):
    """Delete a stop"""
    try:
        stop = Stop.query.get_or_404(stop_id)
        db.session.delete(stop)
        db.session.commit()
        flash('Stop deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting stop: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))

@main.route('/clear_routes', methods=['POST'])
def clear_routes():
    """Clear all routes"""
    try:
        Route.query.delete()
        db.session.commit()
        flash('All routes cleared', 'success')
    except Exception as e:
        flash(f'Error clearing routes: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.index'))

@main.route('/export_route/<int:route_id>')
def export_route(route_id):
    """Export a route to Excel with stops in order and summary information"""
    try:
        route = Route.query.get_or_404(route_id)
        
        # Get stop IDs from the route
        stop_ids = json.loads(route.stop_sequence)
        
        # Create a new workbook
        wb = Workbook()
        
        # Sheet 1: Route Details with Stops in Order
        ws1 = wb.active
        ws1.title = f"Driver {route.driver_number} Route"
        
        # Header styling
        header_font = Font(bold=True, size=12, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Add route summary at the top
        ws1['A1'] = f"Route for Driver {route.driver_number}"
        ws1['A1'].font = Font(bold=True, size=14)
        ws1['A1'].alignment = Alignment(horizontal="center")
        ws1.merge_cells('A1:G1')
        
        departure_address = get_fixed_departure_address()
        ws1['A2'] = f"Departure: {departure_address}"
        ws1['A2'].alignment = Alignment(horizontal="center")
        ws1.merge_cells('A2:G2')
        
        total_hours = route.total_time_minutes / 60
        ws1['A3'] = f"Total Time: {route.total_time_minutes} minutes ({total_hours:.1f} hours)"
        ws1['A3'].alignment = Alignment(horizontal="center")
        ws1.merge_cells('A3:G3')
        
        ws1['A4'] = f"Start Time: {route.start_time} | Date: {route.route_date}"
        ws1['A4'].alignment = Alignment(horizontal="center")
        ws1.merge_cells('A4:G4')
        
        # Headers for stop details
        headers = ['Stop #', 'Address', 'Service Type', 'Post Type', 'Priority', 'Agent Sign', 'Notes']
        for col, header in enumerate(headers, 1):
            cell = ws1.cell(row=6, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border
        
        # Add stop details in order
        row = 7
        for idx, stop_id in enumerate(stop_ids, 1):
            stop = Stop.query.get(stop_id)
            if stop:
                # Determine priority
                priority = "Regular"
                # Handle both date and datetime objects
                route_date = route.route_date if isinstance(route.route_date, date) else route.route_date.date()
                stop_date = stop.required_date.date() if hasattr(stop.required_date, 'date') else stop.required_date
                if stop.required_date and stop_date == route_date:
                    priority = "Scheduled Today"
                elif stop.is_asap:
                    priority = "ASAP"
                
                # Build notes
                notes = []
                if stop.has_riders_toppers:
                    notes.append(f"Riders/Toppers: {stop.riders_toppers_description or 'Yes'}")
                if stop.has_shelter:
                    notes.append("Has Shelter")
                
                # Add row data
                row_data = [
                    idx,
                    stop.address,
                    stop.service_type or '',
                    stop.post_type or '',
                    priority,
                    stop.agent_sign_description or '',
                    '; '.join(notes)
                ]
                
                for col, value in enumerate(row_data, 1):
                    cell = ws1.cell(row=row, column=col, value=value)
                    cell.border = border
                    if col == 1:  # Stop number
                        cell.alignment = Alignment(horizontal="center")
                
                row += 1
        
        # Auto-size columns (skip merged cells)
        for column in ws1.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    # Skip merged cells and None values
                    if hasattr(cell, 'value') and cell.value is not None and not isinstance(cell, MergedCell):
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                except Exception as e:
                    logging.debug(f"Skipping cell in auto-size: {e}")
                    pass
            adjusted_width = min(max_length + 2, 50) if max_length > 0 else 15
            ws1.column_dimensions[column_letter].width = adjusted_width
        
        # Sheet 2: Route Summary
        ws2 = wb.create_sheet(title="Route Summary")
        
        # Summary statistics (starting from row 3 to leave room for title)
        summary_data = [
            ['Metric', 'Value'],
            ['Driver Number', route.driver_number],
            ['Total Stops', len(stop_ids)],
            ['Total Time (minutes)', route.total_time_minutes],
            ['Total Time (hours)', f"{total_hours:.1f}"],
            ['Start Time', route.start_time],
            ['Route Date', str(route.route_date)],
            ['Departure Address', departure_address],
            ['', ''],
            ['Stop Breakdown', ''],
            ['ASAP Stops', sum(1 for sid in stop_ids if Stop.query.get(sid) and Stop.query.get(sid).is_asap)],
            ['Scheduled Stops', sum(1 for sid in stop_ids if Stop.query.get(sid) and Stop.query.get(sid).required_date)],
            ['Regular Stops', sum(1 for sid in stop_ids if Stop.query.get(sid) and not Stop.query.get(sid).is_asap and not Stop.query.get(sid).required_date)],
            ['', ''],
            ['Service Types', ''],
        ]
        
        # Count service types
        service_counts = {}
        for stop_id in stop_ids:
            stop = Stop.query.get(stop_id)
            if stop and stop.service_type:
                service_counts[stop.service_type] = service_counts.get(stop.service_type, 0) + 1
        
        for service_type, count in service_counts.items():
            summary_data.append([service_type, count])
        
        # Add title row
        ws2['A1'] = f"Route Summary - Driver {route.driver_number}"
        ws2['A1'].font = Font(bold=True, size=14)
        ws2['A1'].alignment = Alignment(horizontal="center")
        ws2.merge_cells('A1:D1')
        
        # Add summary data to sheet (starting from row 3)
        for row_idx, row_data in enumerate(summary_data, 3):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws2.cell(row=row_idx, column=col_idx, value=value)
                if row_idx == 3 or row_idx == 12 or row_idx == 17:  # Header rows
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        
        # Auto-size columns for summary sheet (skip merged cells)
        for column in ws2.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    # Skip merged cells and None values
                    if hasattr(cell, 'value') and cell.value is not None and not isinstance(cell, MergedCell):
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                except Exception as e:
                    logging.debug(f"Skipping cell in auto-size: {e}")
                    pass
            adjusted_width = min(max_length + 2, 50) if max_length > 0 else 15
            ws2.column_dimensions[column_letter].width = adjusted_width
        
        # Sheet 3: Instructions for viewing map
        ws3 = wb.create_sheet(title="Map Instructions")
        
        # Instructions data (starting from row 3 to leave room for title)
        instructions = [
            ['Step', 'Instructions'],
            ['1', 'Return to the Route Optimizer web application'],
            ['2', f'Find Driver {route.driver_number} route in the Generated Routes section'],
            ['3', 'Click the "Show Map" button to view the interactive map'],
            ['4', 'The map will display:'],
            ['', '  • Numbered stops in optimized order'],
            ['', '  • Blue lines showing the route path'],
            ['', '  • Departure point marked with a special icon'],
            ['', '  • Click on any marker for stop details'],
            ['', ''],
            ['Note', 'Maps require an active internet connection to display properly'],
        ]
        
        # Add title row
        ws3['A1'] = "How to View the Route Map"
        ws3['A1'].font = Font(bold=True, size=14)
        ws3['A1'].alignment = Alignment(horizontal="center")
        ws3.merge_cells('A1:D1')
        
        # Add instructions data (starting from row 3)
        for row_idx, row_data in enumerate(instructions, 3):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws3.cell(row=row_idx, column=col_idx, value=value)
                if row_idx == 3:  # Header row
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        
        # Auto-size columns for instructions sheet (skip merged cells)
        for column in ws3.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    # Skip merged cells and None values
                    if hasattr(cell, 'value') and cell.value is not None and not isinstance(cell, MergedCell):
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                except Exception as e:
                    logging.debug(f"Skipping cell in auto-size: {e}")
                    pass
            adjusted_width = min(max_length + 2, 50) if max_length > 0 else 15
            ws3.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO object
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Create filename with date and driver number
        filename = f"route_driver_{route.driver_number}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        import traceback
        logging.error(f"Error exporting route: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Error exporting route: {str(e)}', 'error')
        return redirect(url_for('main.index'))