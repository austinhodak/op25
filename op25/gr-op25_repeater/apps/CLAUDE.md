# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OP25 is a GNU Radio-based P25 receiver and digital radio signal processing system. The main applications are located in `/apps/` and provide P25 trunk tracking, digital audio decoding, and multi-receiver capabilities for public safety radio monitoring.

## Core Applications

### Primary Receivers
- `rx.py` - Single channel P25 receiver with terminal interface
- `multi_rx.py` - Multi-receiver system supporting multiple SDR devices and channels
- Both use the same Python launcher pattern (#!/bin/sh header for Python detection)

### Key Supporting Components
- `terminal.py` - Remote terminal client for receiver control
- `audio.py` / `sockaudio.py` - Audio server for UDP audio streaming
- `trunking.py` - P25 trunking system control logic
- `http_server.py` - HTTP dashboard for web-based monitoring

## Configuration

### JSON Configuration Files
Configuration is primarily JSON-based:
- `cfg.json` - Main multi_rx configuration template
- `p25_*_example.json` - Various P25 configuration examples
- `dmr_*_example.json` - DMR configuration examples
- `smartnet_example.json` - SmartNet system configuration

Key configuration sections:
- `channels[]` - Define demodulator channels and their properties
- `devices[]` - Configure SDR hardware (RTL-SDR, Airspy, etc.)
- `trunking{}` - P25 trunking system parameters
- `audio{}` - Audio routing and playback settings
- `terminal{}` - Interface configuration (curses or HTTP)

### Trunking Configuration
- `.tsv` files contain talkgroup and radio ID mappings
- `example_keys.json` - Encryption key format examples

## Common Commands

### Running Receivers
```bash
# Single receiver with RTL-SDR
./rx.py --args 'rtl' --gains 'lna:49' -T tsys.tsv -q -1 -2 -S 1000000 -P symbol -o 50000 -w

# Multi-receiver system
./multi_rx.py -c cfg.json -v 1

# Quick start script
./op25.sh
```

### Remote Terminal
```bash
# Start receiver with remote terminal on port 56111
./rx.py -l 56111 [other options]

# Connect to remote terminal
./terminal.py 127.0.0.1 56111
```

### HTTP Dashboard
```bash
# Enable HTTP interface on port 8080
./rx.py -l http:127.0.0.1:8080 [other options]
```

## Build System

This is a GNU Radio out-of-tree (OOT) module built with CMake:
- Main CMake configuration: `../CMakeLists.txt`
- Python apps CMake: `CMakeLists.txt` (uses GR_PYTHON_INSTALL)
- C++ components in `../lib/` with corresponding headers in `../include/`

Build process follows standard GNU Radio OOT module pattern:
```bash
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig
```

## Architecture

### Signal Processing Chain
1. **SDR Hardware Interface** - RTL-SDR, Airspy, USRP support via GNU Radio
2. **Demodulation** - FSK4 and CQPSK demodulators in C++
3. **Frame Assembly** - P25 frame synchronization and assembly
4. **Protocol Decode** - P25 Phase 1/2, DMR, SmartNet protocol handlers
5. **Audio Processing** - IMBE/AMBE vocoder integration
6. **Output** - UDP audio streams, Wireshark integration, HTTP interface

### Key Modules
- `p25_frame_assembler` - Core P25 frame processing (C++)
- `p25_demodulator.py` - Python demodulator wrapper
- `tk_p25.py` - P25 trunking protocol implementation
- `vocoder` - Audio codec implementation (C++)

### Multi-receiver Architecture
- Device management with automatic frequency assignment
- Channel-to-device mapping based on frequency coverage
- Modular trunking system support via plugin architecture
- Real-time audio streaming with multiple output destinations

## Development Notes

### Code Structure
- Python applications use hybrid shell/Python launcher for cross-platform Python detection
- GNU Radio flowgraph construction in Python
- Signal processing blocks implemented in C++
- Configuration-driven architecture with JSON files

### Testing
- No specific test framework detected in apps directory
- Example configurations serve as integration tests
- Manual testing typically done with SDR hardware

### Key Dependencies
- GNU Radio (core framework)
- Various SDR hardware libraries (RTL-SDR, Airspy, etc.)
- ALSA for audio (Linux)
- Python 2.7/3.x compatibility layer

### Audio Streaming
- UDP-based audio streaming to port 23456 (default)
- Multiple output formats supported
- Integration with external tools like VLC, aplay, liquidsoap

### Protocol Support
- P25 Phase 1 (FDMA) and Phase 2 (TDMA)
- DMR (Digital Mobile Radio)
- Motorola SmartNet/SmartZone
- Basic analog FM (NBFM)
