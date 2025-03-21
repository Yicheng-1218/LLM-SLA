# LLM-SLA
<a href="./readme_tw.md">中文說明</a>

## Introduction
LLM-SLA is a versatile application designed for managing and testing AI services. It leverages Playwright for automated web interactions, providing a flexible framework that can be extended to various web applications by simply adding a corresponding configuration file for each service. With a user-friendly Flask web interface, users can easily manage configurations, execute tests, and view results. Additionally, the framework allows users to customize the runner to adjust pre- and post-test processing logic.


## Features
- **Web Interface**: Utilizes Flask to provide a simple web interface where users can manage configurations, execute tests, and view usage instructions.
- **Configuration Management**: Users can add and modify configurations for AI services.
- **Test Execution**: Provides testing functionality and displays test results.
- **Log Management**: Uses a custom Logger class to manage and beautify log outputs.

## Installation
1. Clone this repository to your local machine:
   ```bash
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```bash
   cd <project-directory>
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   or
   ```bash
   uv add -r requirements.txt
   ```

## Usage
### Starting the Application
- You can use the `start.bat` file to automatically open the browser and start the `app.py` application. Simply double-click the `start.bat` file in the project directory.

### Manual Start
1. Start the application manually:
   ```bash
   python app.py
   ```
2. Open your browser and go to `http://localhost:5000` to access the application.

## Configuration
- Configuration files are located in the `configs` directory and are in JSON format.
- You can add or update the config files through the web interface.
- Each configuration file should include the following required fields:
  - AI Service Name
  - AI Service URL
  - Input Selector
  - Response Selector
  - Test Prompt
  - Number of Concurrent Users
  - Test Duration (seconds)
- Example
```json
{
    "name": "service",
    "url": "https://example.com",
    "input_selector": "textarea[placeholder='Talk to Bot']",
    "response_selector": ".bot-message",
    "test_prompts": [
        "what is LLM?"
    ],
    "headless": false,
    "concurrency": 5,
    "test_duration": 60
}
```

## Testing
- Users can select a configuration and execute tests. The test results will be displayed within the application.

## Logging
- Log files are stored in the `logs` directory and are managed using the `CustomLogger`.

## Contribution
Feel free to submit issues and requests, or directly send a Pull Request.

## License
This project is licensed under the MIT License.
