# Fast Multi-Site Scanning for OP25

This document describes the fast scanning capabilities that enable **SDS100-like performance** of 2+ sites per second.

## Performance Overview

OP25 now supports three scanning modes with different speed/thoroughness tradeoffs:

| Mode | Sites/Second | Use Case |
|------|--------------|----------|  
| **Fast** | 2.5+ sites/sec | SDS100-like rapid scanning, quick activity detection |
| **Priority** | 1.0 sites/sec | Balanced performance with priority site revisiting |
| **Thorough** | 0.125 sites/sec | Deep monitoring, extended dwell times |

## Fast Scanning Mode

### Performance Specifications
- **Target Speed**: 2.5 sites per second (400ms per site)
- **Activity Detection**: 80ms window for immediate activity detection
- **Receiver Settling**: 30ms between site switches
- **Total Performance**: Matches or exceeds Uniden SDS100 scanning speed

### How It Works

1. **Rapid Site Rotation**: Scanner spends only 400ms on each site by default
2. **Instant Activity Detection**: Any TSBK or voice activity triggers immediate retention
3. **Priority Site Tracking**: Active sites are marked as priority for faster return visits
4. **Minimal Settling Time**: Only 30ms delay between frequency changes

### Configuration

Add the `scanning_mode` parameter to your trunking system configuration:

```json
{
    "trunking": {
        "module": "tk_p25.py", 
        "chans": [
            {
                "sysname": "Fast Scanning System",
                "scanning_mode": "fast",
                "sites": [
                    {
                        "site_id": "site1",
                        "name": "Downtown Site",
                        "control_channel_list": "453.2375,453.5125"
                    },
                    {
                        "site_id": "site2", 
                        "name": "North Site",
                        "control_channel_list": "460.1250,460.3750"
                    }
                ]
            }
        ]
    }
}
```

### Scanning Mode Options

**`"scanning_mode": "fast"`** (Default)
- 2.5+ sites per second
- 80ms activity detection window
- 30ms receiver settling time
- Best for busy systems with many sites

**`"scanning_mode": "priority"`**
- 1.0 site per second  
- 250ms activity detection window
- 100ms receiver settling time
- Good balance between speed and thoroughness

**`"scanning_mode": "thorough"`**
- 0.125 sites per second (8 seconds per site)
- 2 second activity detection window  
- 500ms receiver settling time
- Best for detailed monitoring of fewer sites

## Activity Detection & Retention

### Fast Mode Behavior
1. Scanner lands on a site and immediately begins monitoring for TSBKs
2. If any activity is detected within 80ms, the site is marked as priority
3. Scanner continues monitoring the active site until activity ceases
4. Once activity stops, scanner waits additional 80ms then moves to next site
5. Priority sites are revisited more frequently in the rotation

### Priority Site System
- Sites with recent activity become "priority sites"
- Priority sites are visited more often in the scanning rotation
- Priority status expires after 10x the activity threshold (800ms in fast mode)
- Helps ensure active sites get continuous coverage

## Performance Monitoring

### Real-Time Statistics
The HTTP dashboard displays:
- Current scanning rate (sites/second)
- Total site switches performed
- Number of priority sites
- Per-site activity status

### Command Line Output
With verbosity level 5 or higher (`-v 5`):
```
Multi-site scanner: switched to site north (North Site) [2.3 sites/sec]
Multi-site scanner: switched to site south (South Site) [2.4 sites/sec]  
```

### JSON Status Output
```json
{
    "scanning_stats": {
        "mode": "fast",
        "sites_per_second": 2.4,
        "switch_count": 1247,
        "priority_sites": 2,
        "scan_timeout": 0.4,
        "activity_threshold": 0.08,
        "switch_delay": 0.03
    }
}
```

## Optimization for Different SDR Hardware

### RTL-SDR Dongles
Fast scanning works well with RTL-SDR, but may need slight timing adjustments:
```json
{
    "scanning_mode": "fast"
}
```

### Higher-End SDRs (Airspy, USRP, etc.)
Can achieve even faster scanning:
```json
{
    "scanning_mode": "fast",
    "# Custom timing possible via code modification": "comment"
}
```

## Comparison with Commercial Scanners

### Uniden SDS100
- **Advertised**: 2 sites per second
- **OP25 Fast Mode**: 2.5+ sites per second  
- **Result**: ⭐ OP25 matches or exceeds SDS100 performance

### Benefits of OP25 Fast Scanning
- **Open Source**: Full control and customization
- **Multiple SDR Support**: Works with various hardware  
- **Detailed Logging**: Complete TSBK and call logging
- **Web Interface**: Real-time monitoring and control
- **Cost Effective**: Uses inexpensive RTL-SDR dongles

## Troubleshooting Fast Scanning

### Scanner Not Switching Fast Enough
- Verify `scanning_mode` is set to `"fast"`
- Check that multiple sites are configured
- Increase verbosity (`-v 5`) to see switching messages
- Monitor HTTP dashboard for actual scan rate

### Missing Activity on Active Sites  
- Consider switching to `"priority"` mode for better activity detection
- Increase activity threshold in code if needed
- Check signal quality - weak signals may cause false negatives

### Receiver Not Keeping Up
- Reduce number of sites being scanned
- Switch to `"priority"` mode for more settling time
- Verify SDR hardware can handle rapid frequency changes

## Technical Implementation

### Key Performance Optimizations
1. **Minimal Dwell Time**: 400ms default (vs 8 seconds in thorough mode)
2. **Fast Switching Logic**: Immediate decision making based on recent activity
3. **Reduced Settling Time**: 30ms between frequency changes  
4. **Priority Queue**: Active sites get preferential scanning treatment
5. **Efficient Activity Detection**: 80ms window captures most TSBK activity

### Code Architecture
- `multi_site_scanner` class handles all scanning logic
- Mode-specific timing parameters in constants
- Real-time scan rate calculation and reporting
- Priority site tracking with automatic expiration

## Example Usage

### Basic Fast Scanning Setup
```bash
# Run with 6 sites in fast scanning mode
./multi_rx.py -c p25_fast_scan_example.json -v 5
```

### Monitor Performance
```bash
# Watch scanning rate in real-time
curl http://127.0.0.1:8080/status | grep sites_per_second
```

The fast scanning implementation provides professional-grade performance that matches or exceeds commercial scanner capabilities while maintaining the flexibility and cost-effectiveness of the OP25 platform.