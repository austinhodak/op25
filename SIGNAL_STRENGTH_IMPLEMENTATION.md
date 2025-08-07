# Signal Strength Implementation for OP25 HTTP Interface

## Overview

This implementation adds signal strength visualization to the OP25 HTTP web interface, allowing users to see a visual signal strength bar that shows both signal quality and lock status.

## Changes Made

### 1. Backend Changes (multi_rx.py)

#### Added Signal Quality Methods to Channel Class
- `get_signal_quality()`: Returns the demodulator's signal quality metric (0-1 or 0-100 range)
- `get_signal_locked()`: Returns the demodulator's lock status (0 or 1)

Both methods include error handling to return 0 if the demodulator is unavailable or idle.

#### Updated ui_freq_update() Method
- Added `signal_quality` and `signal_locked` fields to the JSON data sent to the HTTP interface
- These values are extracted from each channel and included in the channel status updates

### 2. Backend Changes (rx.py)

#### Updated process_ajax() Method
- Added signal quality and lock status to the `rx_update` JSON message
- Includes the same error handling as multi_rx.py for compatibility

### 3. Frontend Changes (index.html)

#### Added Signal Strength Display Area
- Added a "Signal:" label and display area (`signalStrength`) next to the existing error display
- Positioned in the tuning controls section of the main interface

### 4. Frontend Changes (main.js)

#### Created createSignalBar() Function
- Normalizes signal quality to 0-100% range (handles both 0-1 and 0-100 input ranges)
- Creates a visual progress bar with color coding:
  - **Green**: Signal quality > 70%
  - **Orange**: Signal quality 40-70%  
  - **Red**: Signal quality < 40%
- Includes a lock indicator (🔒) when the signal is locked
- Returns HTML for a responsive signal strength bar

#### Updated channel_table() Function
- Added "Signal" column to the channels table
- Each channel row now displays its signal strength bar

#### Updated rx_update() Function
- Handles signal strength data from single-receiver mode (rx.py)
- Updates the main display signal strength indicator

## Signal Quality Interpretation

The signal quality value comes from the GNU Radio demodulator's `quality()` method, which typically represents:
- **Clock recovery quality** for timing synchronization
- **Values range** from 0 (poor) to 1 (excellent) or 0 to 100
- **Lock status** indicates whether the demodulator has achieved symbol timing lock

## Visual Design

- **Bar Width**: 50px with responsive fill based on signal quality percentage
- **Bar Height**: 12px for compact display in table rows
- **Colors**: Traffic light system (red/orange/green) for intuitive understanding
- **Lock Indicator**: Small lock icon (🔒) appears when signal is locked
- **Minimum Width**: 5% to ensure visibility even with very weak signals
- **Smooth Transitions**: CSS transitions for smooth bar updates

## Compatibility

- Works with both `multi_rx.py` (multi-receiver) and `rx.py` (single receiver) modes
- Graceful fallback when signal data is unavailable (shows empty bar)
- Maintains backward compatibility with existing HTTP interface functionality

## Usage

1. Start OP25 with HTTP interface enabled: `-l http:127.0.0.1:8080`
2. Open web browser to the configured address
3. Signal strength bars will appear in:
   - **Channels table** (multi-receiver mode): Shows signal strength for each channel
   - **Main display** (single-receiver mode): Shows signal strength in tuning section

## Technical Notes

- Signal quality updates occur with the same frequency as other status updates
- Error handling prevents crashes when demodulator methods are unavailable
- The implementation leverages existing GNU Radio demodulator quality metrics
- CSS styling is inline for maximum compatibility across different web browsers
