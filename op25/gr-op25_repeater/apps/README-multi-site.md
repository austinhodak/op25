# Multi-Site Scanning for OP25

This document describes the multi-site scanning feature for OP25, which allows monitoring multiple P25 sites with a single SDR by automatically rotating between sites based on activity.

## Overview

Multi-site scanning enables OP25 to monitor multiple P25 sites within the same trunking system, similar to how commercial scanners like the Uniden SDS100 operate. The system will:

1. Start monitoring the first configured site
2. Listen for activity (talkgroups, TSBKs, voice traffic)  
3. If no activity is detected within the scan timeout period, switch to the next site
4. Continue rotating through all configured sites
5. When activity is detected on a site, stay on that site until the activity ends

## Configuration

### New Multi-Site Format

Add a `sites` array to your trunking system configuration instead of using the single `control_channel_list`:

```json
{
    "trunking": {
        "module": "tk_p25.py",
        "chans": [
            {
                "sysname": "Multi-Site System",
                "nac": "0x123",
                "sysid": "0x4a2", 
                "wacn": "0xbee00",
                "sites": [
                    {
                        "site_id": "site1",
                        "name": "Downtown Site",
                        "location": "Downtown Area",
                        "control_channel_list": "453.2375,453.5125,453.7875"
                    },
                    {
                        "site_id": "site2", 
                        "name": "North Side Site",
                        "location": "North Campus",
                        "control_channel_list": "460.1250,460.3750,460.6250"
                    },
                    {
                        "site_id": "site3",
                        "name": "South Side Site",
                        "location": "South Industrial", 
                        "control_channel_list": "462.0125,462.2625,462.5125"
                    }
                ]
            }
        ]
    }
}
```

### Site Configuration Parameters

Each site in the `sites` array supports the following parameters:

- **`site_id`** (required): Unique identifier for the site
- **`name`** (required): Human-readable name for the site
- **`control_channel_list`** (required): Comma-separated list of control channel frequencies for this site
- **`location`** (optional): Geographic description of the site location

### Backward Compatibility

The legacy single-site format using `control_channel_list` directly in the system configuration is still supported:

```json
{
    "control_channel_list": "453.2375,453.5125,453.7875"
}
```

## Scanning Parameters

The following constants in `tk_p25.py` control scanning behavior:

- **`SITE_SCAN_TIMEOUT`** (default: 8.0 seconds): How long to wait on a site before switching if no traffic is detected
- **`SITE_ACTIVITY_THRESHOLD`** (default: 2.0 seconds): Minimum duration of recent activity to consider a site active
- **`SITE_SWITCH_DELAY`** (default: 0.5 seconds): Minimum delay between site switches to allow receiver to settle

## Operation

### Activity Detection

The scanner considers a site "active" when any of the following occur:
- TSBKs (Trunking System Blocks) are received
- Voice calls are active
- Recent talkgroup activity within the activity threshold

### Site Switching Logic

1. **Stay on active site**: If the current site has recent activity, remain tuned to it
2. **Timeout switching**: After `SITE_SCAN_TIMEOUT` seconds with no activity, switch to the next site
3. **Failure switching**: If a site's control channels repeatedly fail, move to the next site
4. **Round-robin**: Sites are scanned in the order they appear in the configuration

### Control Channel Hunting

Within each site, the normal P25 control channel hunting logic applies:
- If the current control channel fails, try the next one in that site's list
- After exhausting all control channels in a site, the site is marked as failed temporarily

## Monitoring and Status

### HTTP Dashboard

The HTTP dashboard displays multi-site scanning information:
- Current active site name and location
- Number of configured sites
- Site switch count
- Per-site activity and status information

### Terminal Interface

The terminal interface shows:
- Current site name in the status line
- Site switching events in debug output (verbosity >= 5)

### JSON Status Output

The system status JSON includes new fields:
- `multi_site_scanning`: Boolean indicating if multi-site scanning is active
- `current_site_id`: ID of the currently active site  
- `current_site_name`: Name of the currently active site
- `site_switch_count`: Total number of site switches performed
- `sites_configured`: Number of sites configured
- `sites`: Detailed per-site status information

## Example Usage

### Basic Multi-Site Configuration

See `p25_multi_site_example.json` for a complete configuration example.

### Running Multi-Site Scanning

```bash
./multi_rx.py -c p25_multi_site_example.json -v 5
```

The `-v 5` verbosity level will show site switching events in the log output.

### Monitoring via HTTP

Access `http://127.0.0.1:8080` (or your configured HTTP port) to view the dashboard with multi-site information.

## Troubleshooting

### No Site Switching

- Check that multiple sites are configured in the `sites` array
- Verify that `SITE_SCAN_TIMEOUT` is appropriate for your system
- Increase verbosity (`-v 5` or higher) to see site switching debug messages

### Frequent Site Switching

- Increase `SITE_ACTIVITY_THRESHOLD` to require longer activity periods
- Increase `SITE_SCAN_TIMEOUT` to wait longer on each site
- Check signal quality - weak signals may cause false timeouts

### Sites Not Responding

- Verify control channel frequencies are correct for each site
- Check that your SDR can tune to all configured frequencies
- Use the HTTP dashboard to monitor per-site failure counts

## Technical Details

### Classes Added

- **`site_info`**: Manages information about individual sites including control channels, activity tracking, and failure counts
- **`multi_site_scanner`**: Handles site rotation logic and activity-based switching decisions

### Files Modified

- **`tk_p25.py`**: Added multi-site scanning classes and integrated scanning logic into the P25 system class

### Files Added

- **`p25_multi_site_example.json`**: Example configuration showing multi-site setup
- **`README-multi-site.md`**: This documentation file

The implementation maintains full backward compatibility with existing single-site configurations while adding powerful new multi-site scanning capabilities.