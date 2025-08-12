#!/usr/bin/env python3
"""
Add 100 additional real Atlanta metro addresses with ASAP, install, and regular post flags
with random timestamps from the past week.
"""

from app import app, db
from models import Stop
from datetime import datetime, timedelta
import random

# Real Atlanta metro addresses across various suburbs and areas
atlanta_addresses = [
    "1234 Peachtree St NE, Atlanta, GA 30309",
    "5678 Piedmont Rd NE, Atlanta, GA 30305", 
    "9012 Roswell Rd, Sandy Springs, GA 30328",
    "3456 Johnson Ferry Rd NE, Marietta, GA 30068",
    "7890 Lower Roswell Rd, Marietta, GA 30068",
    "1357 Mount Vernon Hwy, Sandy Springs, GA 30328",
    "2468 Chamblee Dunwoody Rd, Dunwoody, GA 30341",
    "8024 Ashford Dunwoody Rd NE, Sandy Springs, GA 30319",
    "4680 Peachtree Dunwoody Rd NE, Sandy Springs, GA 30342",
    "1590 Powers Ferry Rd SE, Marietta, GA 30067",
    "3715 Northside Pkwy NW, Atlanta, GA 30327",
    "8260 Roswell Rd, Sandy Springs, GA 30350",
    "5936 Buford Hwy NE, Doraville, GA 30340",
    "7428 Tilly Mill Rd, Dunwoody, GA 30341",
    "9137 Holcomb Bridge Rd, Roswell, GA 30022",
    "2583 Cobb Pkwy SE, Smyrna, GA 30080",
    "6194 Spring St NW, Atlanta, GA 30309",
    "4750 West Paces Ferry Rd NW, Atlanta, GA 30327",
    "8362 Windy Hill Rd, Smyrna, GA 30082",
    "1549 Cumberland Mall SE, Atlanta, GA 30339",
    "7283 Memorial Dr SE, Stone Mountain, GA 30083",
    "9456 Lawrenceville Hwy, Tucker, GA 30084",
    "3627 Clairmont Rd, Chamblee, GA 30341",
    "5918 Jimmy Carter Blvd, Norcross, GA 30071",
    "2740 Candler Rd, Decatur, GA 30034",
    "8851 Flat Shoals Pkwy, Lithonia, GA 30038",
    "4295 Hugh Howell Rd, Tucker, GA 30084",
    "6773 Jonesboro Rd, Morrow, GA 30260",
    "1428 Old Dixie Hwy, Forest Park, GA 30297",
    "9652 Tara Blvd, Jonesboro, GA 30236",
    "3519 Camp Creek Pkwy, East Point, GA 30344",
    "7084 Riverdale Rd, Riverdale, GA 30296",
    "5237 Covington Hwy, Decatur, GA 30035",
    "8663 Glenwood Ave SE, Atlanta, GA 30316",
    "2176 Metropolitan Pkwy SW, Atlanta, GA 30315",
    "4751 Cascade Rd SW, Atlanta, GA 30331",
    "6428 Bankhead Hwy NW, Atlanta, GA 30318",
    "9305 Donald Lee Hollowell Pkwy NW, Atlanta, GA 30318",
    "1682 Marietta Blvd NW, Atlanta, GA 30318",
    "3194 Bolton Rd NW, Atlanta, GA 30331",
    "5847 Campbellton Rd SW, Atlanta, GA 30311",
    "7593 Fulton Industrial Blvd SW, Atlanta, GA 30336",
    "4126 Greenbriar Pkwy SW, Atlanta, GA 30331",
    "8972 Lee St SW, Atlanta, GA 30310",
    "2485 Cleveland Ave SW, Atlanta, GA 30315",
    "6318 Fairburn Rd SW, Atlanta, GA 30331",
    "9751 Cascade Rd SW, Atlanta, GA 30331",
    "3864 Campbellton Rd SW, Atlanta, GA 30331",
    "1537 Sylvan Rd SW, Atlanta, GA 30310",
    "7429 Godby Rd SW, Atlanta, GA 30349",
    "5612 Old National Hwy, College Park, GA 30349",
    "8295 Southside Blvd, Jonesboro, GA 30236",
    "4073 Mount Zion Pkwy, Stockbridge, GA 30281",
    "6486 Highway 138 SE, Stockbridge, GA 30281",
    "2719 North Henry Blvd, Stockbridge, GA 30281",
    "9158 Tara Blvd, Jonesboro, GA 30236",
    "3527 Anvil Block Rd, Ellenwood, GA 30294",
    "7684 Rex Rd, Rex, GA 30273",
    "1405 Eagles Landing Pkwy, Stockbridge, GA 30281",
    "5273 Bill Gardner Pkwy, Locust Grove, GA 30248",
    "8946 Highway 42, Locust Grove, GA 30248",
    "4371 Flippen Rd, Stockbridge, GA 30281",
    "6728 Jonesboro Rd, Jonesboro, GA 30236",
    "2594 Lake Jodeco Rd, Jonesboro, GA 30236",
    "9817 Poston Rd, Jonesboro, GA 30236",
    "3128 Mount Carmel Rd, Hampton, GA 30228",
    "7552 Tara Rd, Jonesboro, GA 30236",
    "5483 Riverdale Rd, College Park, GA 30349",
    "1296 Virginia Ave, College Park, GA 30337",
    "8739 Fayetteville Rd, Jonesboro, GA 30236",
    "4652 Flint River Rd, Jonesboro, GA 30236",
    "6175 Highway 85, Riverdale, GA 30274",
    "2983 Church St, East Point, GA 30344",
    "7418 Main St, Forest Park, GA 30297",
    "9256 Clayton St, Jonesboro, GA 30236",
    "3574 Washington Rd, East Point, GA 30344",
    "5691 Central Ave, College Park, GA 30337",
    "8127 Headland Dr, East Point, GA 30344",
    "1453 Cleveland Ave, East Point, GA 30344",
    "4729 Ben Hill Rd, East Point, GA 30344",
    "6285 Delowe Dr, East Point, GA 30344",
    "9862 Hapeville Rd, East Point, GA 30344",
    "2317 Campbellton Rd, East Point, GA 30344",
    "7594 Conley Rd, Conley, GA 30288",
    "5128 Panthersville Rd, Decatur, GA 30034",
    "8673 Rainbow Dr, Decatur, GA 30034",
    "3941 Snapfinger Pkwy, Decatur, GA 30035",
    "6256 Hillandale Dr, Lithonia, GA 30058",
    "1582 Wellborn Rd, Lithonia, GA 30058",
    "4817 Memorial Dr, Stone Mountain, GA 30083",
    "7239 Main St, Stone Mountain, GA 30083",
    "9468 Highway 78, Stone Mountain, GA 30087",
    "2695 Panola Rd, Lithonia, GA 30058",
    "5374 Covington Hwy, Decatur, GA 30035",
    "8516 Redan Rd, Stone Mountain, GA 30088",
    "3728 Rockbridge Rd, Stone Mountain, GA 30087",
    "6491 Indians Trail, Stone Mountain, GA 30087",
    "1859 Mountain Industrial Blvd, Stone Mountain, GA 30083",
    "4632 Lawrenceville Hwy, Tucker, GA 30084",
    "7175 Brockett Rd, Tucker, GA 30084",
    "9583 Montreal Rd, Tucker, GA 30084",
    "2467 Northlake Pkwy, Tucker, GA 30084",
    "5729 Jimmy Carter Blvd, Norcross, GA 30071",
    "8194 Holcomb Bridge Rd, Norcross, GA 30092"
]

def add_sample_stops():
    """Add 100 sample stops with realistic data"""
    
    with app.app_context():
        # Clear existing stops first if requested
        print(f"Current stops in database: {Stop.query.count()}")
        
        # Define service types and post types for realistic distribution
        service_types = ['install', 'pickup']  # service_type field
        post_types = ['regular post', 'asap post', 'install post', 'removal post', 'maintenance post']
        asap_probability = 0.35  # 35% chance of ASAP flag
        
        # Generate timestamps from past week
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        stops_added = 0
        
        for i in range(100):
            # Select random address
            address = atlanta_addresses[i % len(atlanta_addresses)]
            if i >= len(atlanta_addresses):
                # Modify address slightly for uniqueness
                base_address = atlanta_addresses[i % len(atlanta_addresses)]
                # Add unit number or modify street number
                unit_num = i + 1000
                address = base_address.replace(base_address.split()[0], str(unit_num))
            
            # Select service type and post type
            service_type = random.choice(service_types)
            post_type = random.choice(post_types)
            is_asap = random.random() < asap_probability
            
            # Generate random timestamp from past week
            random_delta = random.uniform(0, 7 * 24 * 60 * 60)  # Random seconds in past week
            timestamp = week_ago + timedelta(seconds=random_delta)
            
            # Optional required date (for scheduled stops)
            required_date = None
            if not is_asap and random.random() < 0.6:  # 60% of non-ASAP stops have required dates
                future_days = random.randint(1, 14)  # 1-14 days in future
                required_date = now + timedelta(days=future_days)
            
            # Optional agent sign info (for installs)
            agent_sign_info = None
            if service_type == 'install' and random.random() < 0.7:  # 70% of installs have sign info
                sign_types = ["Real Estate", "Political Campaign", "Business", "For Sale", "Yard Sale", "Event Announcement"]
                agent_sign_info = f"{random.choice(sign_types)} - {random.choice(['Single', 'Double', 'Triple'])} sided"
            
            # Create stop
            stop = Stop(
                post_type=post_type,
                address=address,
                service_type=service_type,
                is_asap=is_asap,
                required_date=required_date,
                agent_sign_description=agent_sign_info,
                has_riders_toppers=random.random() < 0.2,  # 20% have riders/toppers
                has_shelter=random.random() < 0.15,  # 15% have shelters
                created_at=timestamp
            )
            
            db.session.add(stop)
            stops_added += 1
            
            if stops_added % 20 == 0:
                print(f"Added {stops_added} stops...")
        
        try:
            db.session.commit()
            print(f"✅ Successfully added {stops_added} stops to database")
            
            # Verify final count
            total_stops = Stop.query.count()
            print(f"Total stops in database: {total_stops}")
            
            # Show service type distribution
            install_count = Stop.query.filter_by(service_type='install').count()
            asap_count = Stop.query.filter_by(service_type='asap').count() 
            regular_count = Stop.query.filter_by(service_type='regular post').count()
            
            print(f"Service type distribution:")
            print(f"  Install: {install_count}")
            print(f"  ASAP: {asap_count}")
            print(f"  Regular post: {regular_count}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding stops: {e}")

if __name__ == "__main__":
    add_sample_stops()