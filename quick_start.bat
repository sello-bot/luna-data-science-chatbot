@echo off
echo ====================================
echo Data Science Chatbot - Quick Start
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Make sure Python is installed and in PATH
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo.
echo Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
) else (
    echo Dependencies already installed.
)

REM Run setup verification
echo.
echo Running setup verification...
python test_setup.py
if errorlevel 1 (
    echo.
    echo WARNING: Some checks failed. You can still try to run the app.
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" (
        pause
        exit /b 1
    )
)

REM Start the application
echo.
echo ====================================
echo Starting Data Science Chatbot...
echo ====================================
echo.
echo Server will start at: http://127.0.0.1:5000
echo Press CTRL+C to stop the server
echo.

python app.py




pause