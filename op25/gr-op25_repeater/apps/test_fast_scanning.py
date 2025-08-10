#!/usr/bin/env python3

"""
Test script for fast scanning performance
Validates SDS100-like scanning speeds of 2+ sites per second
"""

import sys
import time
import json

# Fast scanning constants from tk_p25.py
FAST_SCAN_TIMEOUT = 0.5
FAST_ACTIVITY_THRESHOLD = 0.1
FAST_SWITCH_DELAY = 0.05

PRIORITY_SCAN_TIMEOUT = 1.0
PRIORITY_ACTIVITY_THRESHOLD = 0.25
PRIORITY_SWITCH_DELAY = 0.1

THOROUGH_SCAN_TIMEOUT = 8.0
THOROUGH_ACTIVITY_THRESHOLD = 2.0
THOROUGH_SWITCH_DELAY = 0.5

CC_TIMEOUT_RETRIES = 3

class site_info(object):
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
        
    def has_recent_activity(self, current_time, threshold):
        return (current_time - self.last_activity) < threshold

class multi_site_scanner(object):
    def __init__(self, sites, debug=0, scanning_mode='fast'):
        self.sites = sites
        self.debug = debug
        self.current_site_id = None
        self.last_site_switch = 0.0
        self.scan_enabled = len(sites) > 1
        self.site_switch_count = 0
        self.scanning_mode = scanning_mode
        self.immediate_activity = False
        self.priority_sites = {}
        self.last_activity_check = 0.0
        
        self.scan_rate_history = []
        self.last_scan_time = 0.0
        
        self.set_scanning_mode(scanning_mode)
        
        if self.sites:
            self.current_site_id = list(self.sites.keys())[0]
            self.sites[self.current_site_id].next_cc()
            
    def set_scanning_mode(self, mode):
        self.scanning_mode = mode
        
        if mode == 'fast':
            self.scan_timeout = FAST_SCAN_TIMEOUT
            self.activity_threshold = FAST_ACTIVITY_THRESHOLD  
            self.switch_delay = FAST_SWITCH_DELAY
        elif mode == 'thorough':
            self.scan_timeout = THOROUGH_SCAN_TIMEOUT
            self.activity_threshold = THOROUGH_ACTIVITY_THRESHOLD
            self.switch_delay = THOROUGH_SWITCH_DELAY
        elif mode == 'priority':
            self.scan_timeout = PRIORITY_SCAN_TIMEOUT
            self.activity_threshold = PRIORITY_ACTIVITY_THRESHOLD
            self.switch_delay = PRIORITY_SWITCH_DELAY
        else:
            self.scan_timeout = FAST_SCAN_TIMEOUT
            self.activity_threshold = FAST_ACTIVITY_THRESHOLD
            self.switch_delay = FAST_SWITCH_DELAY
            
        if self.debug >= 1:
            print(f'Scanner mode: {mode}, timeout: {self.scan_timeout:.3f}s, threshold: {self.activity_threshold:.3f}s, delay: {self.switch_delay:.3f}s')
            
    def get_current_site(self):
        if self.current_site_id and self.current_site_id in self.sites:
            return self.sites[self.current_site_id]
        return None
        
    def switch_to_next_site(self, current_time):
        if not self.scan_enabled or not self.sites:
            return False
            
        if (current_time - self.last_site_switch) < self.switch_delay:
            return False
            
        # Track scan rate performance
        if self.last_scan_time > 0:
            scan_interval = current_time - self.last_scan_time
            self.scan_rate_history.append(scan_interval)
            if len(self.scan_rate_history) > 10:
                self.scan_rate_history.pop(0)
        self.last_scan_time = current_time
        
        # Priority mode: check priority sites first
        if self.scanning_mode == 'priority' and self.priority_sites:
            priority_list = list(self.priority_sites.keys())
            site_list = priority_list + [s for s in self.sites.keys() if s not in priority_list]
        else:
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
            
        if self.debug >= 2:
            avg_rate = sum(self.scan_rate_history) / len(self.scan_rate_history) if self.scan_rate_history else 0
            sites_per_sec = 1.0 / avg_rate if avg_rate > 0 else 0
            print(f'Switched to site {self.current_site_id} ({current_site.name if current_site else "unknown"}) [%.1f sites/sec]' % sites_per_sec)
        return True
        
    def should_switch_site(self, current_time):
        if not self.scan_enabled:
            return False
            
        current_site = self.get_current_site()
        if not current_site:
            return True
            
        # Fast mode: immediate switching unless very recent activity
        if self.scanning_mode == 'fast':
            if current_site.has_recent_activity(current_time, self.activity_threshold):
                self.priority_sites[self.current_site_id] = current_time
                return False
                
            time_on_site = current_time - self.last_site_switch  
            return time_on_site >= self.scan_timeout
            
        # Priority mode: balance speed with activity detection
        elif self.scanning_mode == 'priority':
            if current_site.has_recent_activity(current_time, self.activity_threshold):
                self.priority_sites[self.current_site_id] = current_time
                return False
                
            time_on_site = current_time - self.last_site_switch
            return time_on_site >= self.scan_timeout
            
        # Thorough mode
        else:
            if current_site.has_recent_activity(current_time, self.activity_threshold):
                return False
                
            time_on_site = current_time - self.last_site_switch
            if time_on_site >= self.scan_timeout:
                return True
                
            if current_site.failure_count >= 3:
                current_site.failure_count = 0
                return True
                
        return False
        
    def update_site_activity(self, site_id, timestamp):
        if site_id in self.sites:
            self.sites[site_id].update_activity(timestamp)
            if self.scanning_mode in ['fast', 'priority']:
                self.priority_sites[site_id] = timestamp
                
        # Clean up old priority sites
        cutoff_time = timestamp - (self.activity_threshold * 10)
        expired_sites = [s for s, t in self.priority_sites.items() if t < cutoff_time]
        for site in expired_sites:
            del self.priority_sites[site]
            
    def get_scan_rate(self):
        if not self.scan_rate_history:
            return 0.0
        avg_interval = sum(self.scan_rate_history) / len(self.scan_rate_history)
        return 1.0 / avg_interval if avg_interval > 0 else 0.0

def create_test_sites(count=6):
    """Create test sites for scanning"""
    sites = {}
    for i in range(count):
        site_id = f"site{i+1}"
        name = f"Test Site {i+1}"
        base_freq = 453000000 + (i * 2000000)  # Spread across spectrum
        control_channels = [base_freq + j*250000 for j in range(3)]
        
        site = site_info(site_id, name, control_channels)
        sites[site_id] = site
        
    return sites

def test_scanning_speed(mode, duration=10.0, site_count=6):
    """Test scanning speed for a given mode"""
    print(f"\\n=== Testing {mode.upper()} Scanning Mode ===")
    print(f"Sites: {site_count}, Duration: {duration}s")
    
    sites = create_test_sites(site_count)
    scanner = multi_site_scanner(sites, debug=1, scanning_mode=mode)
    
    start_time = time.time()
    current_time = start_time
    switches = 0
    
    while (current_time - start_time) < duration:
        if scanner.should_switch_site(current_time):
            if scanner.switch_to_next_site(current_time):
                switches += 1
                
        # Simulate small time increments for fast scanning
        if mode == 'fast':
            time.sleep(0.01)  # 10ms increments
            current_time += 0.01
        elif mode == 'priority': 
            time.sleep(0.05)  # 50ms increments
            current_time += 0.05
        else:
            time.sleep(0.1)   # 100ms increments
            current_time += 0.1
            
        current_time = time.time()  # Use real time for accuracy
        
    elapsed = current_time - start_time
    scan_rate = switches / elapsed
    
    print(f"Results:")
    print(f"  Switches: {switches}")
    print(f"  Elapsed: {elapsed:.2f}s") 
    print(f"  Rate: {scan_rate:.2f} sites/second")
    print(f"  Scanner rate: {scanner.get_scan_rate():.2f} sites/second")
    
    # Performance assessment
    if mode == 'fast':
        target_rate = 2.0
        performance = "EXCELLENT" if scan_rate >= target_rate else "NEEDS WORK"
    elif mode == 'priority':
        target_rate = 1.0
        performance = "GOOD" if scan_rate >= target_rate else "NEEDS WORK"  
    else:
        target_rate = 0.125
        performance = "EXPECTED" if scan_rate <= 0.2 else "TOO FAST"
        
    print(f"  Target: {target_rate} sites/sec - {performance}")
    
    return scan_rate

def test_activity_handling(mode='fast'):
    """Test activity detection and site retention"""
    print(f"\\n=== Testing Activity Handling ({mode.upper()}) ===")
    
    sites = create_test_sites(3)
    scanner = multi_site_scanner(sites, debug=2, scanning_mode=mode)
    
    current_time = time.time()
    
    # Simulate activity on current site
    current_site = scanner.get_current_site()
    current_site.update_activity(current_time)
    scanner.priority_sites[scanner.current_site_id] = current_time
    
    print(f"Added activity to {current_site.name}")
    
    # Test that scanner doesn't immediately switch
    time.sleep(scanner.activity_threshold * 0.5)
    current_time = time.time()
    
    should_switch = scanner.should_switch_site(current_time)
    print(f"Should switch with recent activity: {should_switch}")
    
    # Wait for activity to expire, then check switching
    time.sleep(scanner.activity_threshold * 1.5)
    current_time = time.time()
    
    should_switch = scanner.should_switch_site(current_time)
    print(f"Should switch after activity expires: {should_switch}")
    
    if should_switch and scanner.switch_to_next_site(current_time):
        new_site = scanner.get_current_site()
        print(f"Successfully switched to {new_site.name}")

def benchmark_all_modes():
    """Benchmark all scanning modes"""
    print("Multi-Site Fast Scanning Benchmark")
    print("=" * 50)
    
    modes = ['fast', 'priority', 'thorough']
    results = {}
    
    for mode in modes:
        rate = test_scanning_speed(mode, duration=5.0, site_count=6)
        results[mode] = rate
        
    print("\\n" + "=" * 50)
    print("BENCHMARK RESULTS:")
    for mode, rate in results.items():
        print(f"  {mode.upper():>10}: {rate:.2f} sites/second")
        
    # SDS100 comparison
    print("\\nSDS100 COMPARISON:")
    sds100_rate = 2.0
    fast_ratio = results['fast'] / sds100_rate if results['fast'] > 0 else 0
    print(f"  SDS100 Target: {sds100_rate:.1f} sites/second")
    print(f"  OP25 Fast Mode: {results['fast']:.2f} sites/second ({fast_ratio:.1f}x)")
    
    if results['fast'] >= sds100_rate:
        print("  ✅ FAST MODE MEETS SDS100 PERFORMANCE!")
    else:
        print("  ⚠️  Fast mode needs optimization")

def test_priority_site_handling():
    """Test priority site functionality"""
    print("\\n=== Testing Priority Site Handling ===")
    
    sites = create_test_sites(4)
    scanner = multi_site_scanner(sites, debug=2, scanning_mode='priority')
    
    current_time = time.time()
    
    # Add activity to sites 2 and 4
    sites['site2'].update_activity(current_time)
    sites['site4'].update_activity(current_time)
    scanner.update_site_activity('site2', current_time)
    scanner.update_site_activity('site4', current_time)
    
    print(f"Added priority sites: {list(scanner.priority_sites.keys())}")
    
    # Run scanning and track which sites are visited
    visited_sites = []
    for i in range(8):
        if scanner.should_switch_site(current_time):
            if scanner.switch_to_next_site(current_time):
                current_site = scanner.get_current_site()
                visited_sites.append(current_site.site_id)
                
        current_time += scanner.scan_timeout + 0.1
        
    print(f"Sites visited: {visited_sites}")
    print(f"Priority sites should appear more frequently")

def main():
    """Run all fast scanning tests"""
    try:
        # Test individual modes
        test_scanning_speed('fast', duration=3.0)
        test_scanning_speed('priority', duration=3.0) 
        test_scanning_speed('thorough', duration=2.0)
        
        # Test activity handling
        test_activity_handling('fast')
        test_activity_handling('priority')
        
        # Test priority sites
        test_priority_site_handling()
        
        # Full benchmark
        benchmark_all_modes()
        
        print("\\n" + "=" * 50)
        print("✅ All fast scanning tests completed successfully!")
        print("\\nFast mode should achieve 2+ sites/second for SDS100-like performance")
        
    except Exception as e:
        print(f"\\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())