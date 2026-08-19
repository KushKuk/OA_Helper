# OA Assistant

A Windows desktop AI assistant for learning OS-level programming and AI integration.

## Overview

OA Assistant is a Windows desktop application that provides screen capture, optical character recognition (OCR), and AI-powered analysis capabilities through a convenient overlay interface. The application uses global hotkeys to toggle an overlay window where users can capture screen regions, extract text from those captures using OCR, and get AI analysis of the extracted content.

## Features

- **Global Hotkey Activation**: Use `Ctrl+Space` to toggle the overlay interface
- **Screen Capture**: Capture full screen or selected regions
- **OCR Processing**: Extract text from captured images using Tesseract OCR
- **AI Analysis**: Send extracted text to AI models (Gemini/Nemotron) for analysis
- **Overlay Interface**: Non-intrusive UI that appears on demand
- **Text Extraction & Copy**: Copy extracted text or AI responses to clipboard
- **Retake/Cancel Functionality**: Easily retake captures or cancel operations
- **Background Processing**: All intensive operations run in separate threads to maintain UI responsiveness

## Setup Instructions

### Prerequisites

- Windows 10 or Windows 11
- Python 3.12 or higher
- Git (for cloning the repository)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/oa-assistant.git
   cd oa-assistant
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Install Tesseract OCR (required for text extraction):
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install and note the installation path (typically `C:\Program Files\Tesseract-OCR\tesseract.exe`)
   - Add Tesseract to your PATH or set the `TESSERACT_CMD` environment variable

4. Configure API keys (optional but recommended for AI features):
   - Create a `.env` file in the project root
   - Add your API keys:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     NEMOTRON_API_KEY=your_nemotron_api_key_here
     # Or other AI provider keys as needed
     ```

### Configuration

The application can be configured through:
- Environment variables (loaded from `.env` file)
- Modifying values in `oa_assistant/core/config.py`

Key configuration options:
- `AI_PROVIDER`: Choose between "gemini" or "nemotron"
- `HOTKEY_TOGGLE_OVERLAY`: Change the hotkey to show/hide the overlay (default: `ctrl+space`)
- `HOTKEY_CAPTURE_REGION`: Change the hotkey for region capture (default: `ctrl+shift+c`)
- `OVERLAY_OPACITY`, `OVERLAY_WIDTH`, `OVERLAY_HEIGHT`: Adjust overlay appearance

## Usage

### Basic Workflow

1. **Activate the Overlay**: Press `Ctrl+Space` (default hotkey) to show/hide the overlay window
2. **Capture Screen**: Click the capture button in the overlay or use `Ctrl+Shift+C` to capture your screen
3. **Extract Text**: The application automatically performs OCR on the captured image
4. **Get AI Analysis**: Click the analyze button to send the extracted text to an AI model for analysis
5. **Copy Results**: Use the copy buttons to extract text or AI responses to your clipboard
6. **Retake/Cancel**: Use the retake button to capture again or cancel to return to the idle state

### Overlay Interface Elements

- **Capture Button**: Initiates screen capture process
- **Extract Text Button**: Shows the full extracted text in a dialog
- **Copy Text Button**: Copies extracted text to clipboard
- **Analyze Button**: Sends extracted text to AI model for analysis
- **Copy AI Response Button**: Copies AI analysis to clipboard
- **Retry Button**: Repeats the last operation
- **Retake Button**: Allows you to capture a new screen region
- **Cancel Button**: Returns to idle state without saving

## Project Structure

```
oa-assistant/
├── oa_assistant/
│   ├── app/                 # Application entry point and main controller
│   ├── core/                # Configuration, logging, and shared utilities
│   ├── capture/             # Screen capture functionality
│   ├── ocr/                 # Optical character recognition services
│   ├── ai/                  # AI analysis services
│   ├── ui/                  # User interface components (overlay, etc.)
│   └── windows/             # Windows-specific implementations (hotkeys, window management)
├── tests/                   # Unit tests
├── docs/                    # Documentation files
└── pyproject.toml           # Project configuration and dependencies
```

## How It Works

### Architecture

1. **Application Controller** (`oa_assistant/app/application.py`):
   - Coordinates all components (overlay, window manager, hotkeys)
   - Manages worker threads for background processing
   - Handles state management for captures, OCR results, and AI results

2. **Overlay Window** (`oa_assistant/ui/overlay.py`):
   - Provides the graphical interface that appears on screen
   - Emits signals for user interactions (capture, extract, analyze, etc.)
   - Displays processing states and results

3. **Hotkey Manager** (`oa_assistant/windows/hotkeys.py`):
   - Registers global hotkeys using Win32 API
   - Communicates hotkey presses to the application via Qt signals

4. **Screen Capture** (`oa_assistant/capture/screen_capture.py`):
   - Uses MSS library for efficient screen capture
   - Supports full-screen and region-based capture

5. **OCR Service** (`oa_assistant/ocr/service.py`):
   - Interface for OCR providers (currently Tesseract)
   - Preprocesses images for better OCR accuracy
   - Returns structured OCR results with text and metadata

6. **AI Service** (`oa_assistant/ai/service.py`):
   - Interface for AI providers (Gemini, Nemotron)
   - Sends analysis requests and processes responses
   - Handles rate limiting and error cases

### Threading Model

To maintain UI responsiveness, intensive operations run in separate QThreads:
- **CaptureWorker**: Handles screen capture operations
- **OCRWorker**: Performs OCR on captured images
- **AIWorker**: Sends requests to AI models and processes responses

Each worker follows the same pattern:
1. Move to a separate thread
2. Connect signals for start, completion, and cleanup
3. Emit results when finished
4. Properly clean up resources

## Development

### Running Tests

```bash
pytest
```

### Code Style

The project follows standard Python conventions with type hints where beneficial.

### Adding New Features

1. **New OCR Provider**: Implement the `OCRServiceInterface` in `oa_assistant/ocr/service.py`
2. **New AI Provider**: Implement the `AIServiceInterface` in `oa_assistant/ai/service.py`
3. **New UI Component**: Add to `oa_assistant/ui/` and connect signals appropriately
4. **New Hotkey**: Add to `oa_assistant/windows/hotkeys.py` and register in `_register_configured_hotkeys()`

## License

This project is proprietary software. See the LICENSE file for details.

## Acknowledgments

- Built with PySide6 for the graphical interface
- Uses MSS for efficient screen capture
- Uses Tesseract for OCR capabilities
- Integrates with various AI providers for intelligent analysis

--- 
*OA Assistant - Making AI accessible right on your desktop*