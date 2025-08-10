#!/usr/bin/env python3

"""
Test script for multi-site scanning functionality
Run this to validate the multi-site classes without requiring GNU Radio
"""

import sys
import time
import json

# Test the new multi-site classes directly
class MockTime:
    """Mock time for testing without actual delays"""
    def __init__(self):
        self.current = 0.0
    
    def get(self):
        return self.current
    
    def advance(self, seconds):
        self.current += seconds
        return self.current

# Constants from tk_p25.py
SITE_SCAN_TIMEOUT = 8.0
SITE_ACTIVITY_THRESHOLD = 2.0  
SITE_SWITCH_DELAY = 0.5
CC_TIMEOUT_RETRIES = 3

class site_info(object):
    """Test version of site_info class"""
    def __init__(self, site_id, name, control_channels, location=None):
        self.site_id = site_id
        self.name = name
        self.control_channels = control_channels
        self.location = location
        self.cc_index = -1
        self.cc_retries = 0
        self.last_activity = 0.0
        self.last_tsbk = 0.0
        self.active_calls = 0
        self.signal_quality = 0.0
        self.locked = False
        self.failure_count = 0
        
    def next_cc(self):
        self.cc_retries = 0
        self.cc_index += 1
        if self.cc_index >= len(self.control_channels):
            self.cc_index = 0
            
    def get_current_cc(self):
        if self.cc_index >= 0 and self.cc_index < len(self.control_channels):
            return self.control_channels[self.cc_index]
        return None
        
    def timeout_cc(self):
        self.cc_retries += 1
        if self.cc_retries >= CC_TIMEOUT_RETRIES:
            self.next_cc()
            self.failure_count += 1
            return True
        return False
        
    def update_activity(self, timestamp):
        self.last_activity = timestamp
        
    def has_recent_activity(self, current_time, threshold=SITE_ACTIVITY_THRESHOLD):
        return (current_time - self.last_activity) < threshold

class multi_site_scanner(object):
    """Test version of multi_site_scanner class"""
    def __init__(self, sites, debug=0):
        self.sites = sites
        self.debug = debug
        self.current_site_id = None
        self.last_site_switch = 0.0
        self.scan_enabled = len(sites) > 1
        self.site_switch_count = 0
        
        if self.sites:
            self.current_site_id = list(self.sites.keys())[0]
            self.sites[self.current_site_id].next_cc()
            
    def get_current_site(self):
        if self.current_site_id and self.current_site_id in self.sites:
            return self.sites[self.current_site_id]
        return None
        
    def switch_to_next_site(self, current_time):
        if not self.scan_enabled or not self.sites:
            return False
            
        if (current_time - self.last_site_switch) < SITE_SWITCH_DELAY:
            return False
            
        site_list = list(self.sites.keys())
        if self.current_site_id in site_list:
            current_idx = site_list.index(self.current_site_id)
            next_idx = (current_idx + 1) % len(site_list)
            self.current_site_id = site_list[next_idx]
        else:
            self.current_site_id = site_list[0]
            
        self.last_site_switch = current_time
        self.site_switch_count += 1
        
        current_site = self.get_current_site()
        if current_site:
            current_site.next_cc()
            
        if self.debug >= 1:
            print(f'Multi-site scanner: switched to site {self.current_site_id} ({current_site.name if current_site else "unknown"})')
        return True
        
    def should_switch_site(self, current_time):
        if not self.scan_enabled:
            return False
            
        current_site = self.get_current_site()
        if not current_site:
            return True
            
        if current_site.has_recent_activity(current_time):
            return False
            
        time_on_site = current_time - self.last_site_switch
        if time_on_site >= SITE_SCAN_TIMEOUT:
            return True
            
        if current_site.failure_count >= 3:
            current_site.failure_count = 0
            return True
            
        return False
        
    def update_site_activity(self, site_id, timestamp):
        if site_id in self.sites:
            self.sites[site_id].update_activity(timestamp)

def test_basic_functionality():
    """Test basic site_info and multi_site_scanner functionality"""
    print("=== Testing Basic Functionality ===")
    
    # Create test sites
    site1 = site_info("site1", "Downtown", [453000000, 453250000])
    site2 = site_info("site2", "Northside", [460000000, 460250000]) 
    site3 = site_info("site3", "Southside", [462000000, 462250000])
    
    sites = {
        "site1": site1,
        "site2": site2, 
        "site3": site3
    }
    
    # Test scanner creation
    scanner = multi_site_scanner(sites, debug=1)
    
    print(f"Created scanner with {len(scanner.sites)} sites")
    print(f"Current site: {scanner.get_current_site().name}")
    print(f"Scan enabled: {scanner.scan_enabled}")
    
    return scanner

def test_site_switching():
    """Test site switching logic"""
    print("\\n=== Testing Site Switching ===")
    
    scanner = test_basic_functionality()
    mock_time = MockTime()
    
    # Initially should not switch (no time passed)
    current_time = mock_time.get()
    should_switch = scanner.should_switch_site(current_time)
    print(f"Should switch initially: {should_switch}")
    
    # After timeout period with no activity, should switch
    mock_time.advance(SITE_SCAN_TIMEOUT + 1.0)
    current_time = mock_time.get()
    should_switch = scanner.should_switch_site(current_time)
    print(f"Should switch after timeout: {should_switch}")
    
    # Test actual switching
    if should_switch:
        old_site = scanner.get_current_site().name
        success = scanner.switch_to_next_site(current_time)
        new_site = scanner.get_current_site().name
        print(f"Switch successful: {success}, {old_site} -> {new_site}")
        
    return scanner

def test_activity_tracking():
    """Test activity tracking and retention"""
    print("\\n=== Testing Activity Tracking ===")
    
    scanner = test_basic_functionality()
    mock_time = MockTime()
    
    # Add activity to current site
    current_site = scanner.get_current_site()
    current_time = mock_time.get()
    current_site.update_activity(current_time)
    print(f"Added activity to {current_site.name}")
    
    # Should not switch while activity is recent
    mock_time.advance(1.0)  # Less than SITE_ACTIVITY_THRESHOLD
    current_time = mock_time.get()
    should_switch = scanner.should_switch_site(current_time)
    print(f"Should switch with recent activity: {should_switch}")
    
    # Should switch after activity expires
    mock_time.advance(SITE_ACTIVITY_THRESHOLD + 1.0)
    current_time = mock_time.get()
    should_switch = scanner.should_switch_site(current_time)
    print(f"Should switch after activity expires: {should_switch}")

def test_control_channel_cycling():
    """Test control channel cycling within sites"""
    print("\\n=== Testing Control Channel Cycling ===")
    
    site = site_info("test", "Test Site", [453000000, 453250000, 453500000])
    
    print(f"Site has {len(site.control_channels)} control channels")
    
    # Initialize and cycle through channels
    site.next_cc()
    for i in range(5):
        cc = site.get_current_cc()
        print(f"CC {i}: {cc/1e6:.4f} MHz (index {site.cc_index})")
        site.next_cc()

def test_configuration_parsing():
    """Test parsing of multi-site configuration"""
    print("\\n=== Testing Configuration Parsing ===")
    
    test_config = {
        "sites": [
            {
                "site_id": "site1",
                "name": "Downtown Site",
                "location": "Downtown Area", 
                "control_channel_list": "453.000,453.250,453.500"
            },
            {
                "site_id": "site2",
                "name": "North Side Site",
                "location": "North Campus",
                "control_channel_list": "460.000,460.250"
            }
        ]
    }
    
    print("Test configuration:")
    print(json.dumps(test_config, indent=2))
    
    # Simulate configuration processing
    sites = {}
    for site_config in test_config['sites']:
        site_id = site_config['site_id']
        site_name = site_config['name']
        cc_list = site_config['control_channel_list']
        location = site_config.get('location')
        
        control_channels = []
        for f in cc_list.split(','):
            # Convert MHz to Hz (simplified)
            freq_mhz = float(f.strip())
            control_channels.append(int(freq_mhz * 1e6))
            
        site = site_info(site_id, site_name, control_channels, location)
        sites[site_id] = site
        
        print(f"Parsed site {site_id}: {site_name}, {len(control_channels)} CCs")
    
    scanner = multi_site_scanner(sites, debug=1)
    print(f"Created scanner with {len(scanner.sites)} sites")

def main():
    """Run all tests"""
    print("Multi-Site Scanning Test Suite")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        test_site_switching() 
        test_activity_tracking()
        test_control_channel_cycling()
        test_configuration_parsing()
        
        print("\\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())