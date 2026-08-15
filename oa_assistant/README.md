# OA Assistant

A Windows desktop AI assistant for learning OS-level programming and AI integration.

## Overview

OA Assistant is a floating overlay application designed to help with coding practice, studying, debugging, and general productivity. It captures screen regions, extracts text using OCR, sends structured context to an AI backend, and displays responses in the overlay.

## Features (Planned)

- Floating always-on-top overlay window
- Global hotkey system for triggering actions
- Screen capture with interactive region selection
- OCR (Optical Character Recognition) for text extraction
- AI integration for contextual assistance
- Modular and extensible architecture
- Settings management for providers and preferences

## Current Status

This is Phase 7 of implementation, providing:
- Basic project structure
- Configuration management
- Logging setup
- PySide6 application with overlay window
- Global hotkey system
- Screen capture with interactive region selection
- OCR (Optical Character Recognition) for text extraction using Tesseract
- Text extraction and copy functionality
- AI integration for contextual assistance using Google Gemini
- AI provider abstraction layer for extensibility
- User-triggered AI analysis via "Analyze" button
- Background processing for AI operations to prevent GUI blocking
- Copy AI response functionality

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Install Tesseract OCR engine (required for OCR functionality):
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr` or equivalent for your distribution
6. Copy `.env.example` to `.env` and fill in required values

## Usage

Run the application:
```bash
python -m oa_assistant.app.main
```

## Project Structure

```
oa_assistant/
    app/                  # Application entry points and main windows
        main.py           # Main application entry point
    ui/                   # User interface components
        overlay.py        # Overlay window (to be implemented)
        settings_window.py # Settings dialog (to be implemented)
        widgets/          # Custom widgets
    core/                 # Core functionality
        config.py         # Configuration management
        logging.py        # Logging setup
        models.py         # Data models (to be implemented)
        events.py         # Event system (to be implemented)
    capture/              # Screen capture functionality
        interface.py      # Abstract interface for screen capture
        screen_capture.py # Concrete implementation (to be implemented)
        region_selector.py # Region selection tool (to be implemented)
    ocr/                  # OCR functionality
        interface.py      # Abstract interface for OCR
        service.py        # Concrete implementation (to be implemented)
    ai/                   # AI integration
        interface.py      # Abstract interface for AI providers
        client.py         # Concrete implementation (to be implemented)
        context.py        # Context preparation (to be implemented)
        prompts.py        # Prompt templates (to be implemented)
    windows/              # Windows-specific functionality
        window_manager.py # Window management utilities (to be implemented)
        hotkeys.py        # Global hotkey handling (to be implemented)
    services/             # Business logic services
        assistant_service.py # Main assistant logic (to be implemented)
    tests/                # Unit tests
    scripts/              # Utility scripts
```

## Configuration

Configuration is managed through environment variables loaded from a `.env` file. See `.env.example` for available settings.

## Logging

Logging is configured to output to both console and file (if LOG_FILE is set). The log level can be adjusted via the LOG_LEVEL environment variable.

## License

This project is proprietary and intended for educational purposes.

## Disclaimer

This application is intended for legitimate use cases such as coding practice, mock online assessments, studying, debugging, and general productivity. Do not use this application to evade proctoring, monitoring, or assessment security systems.