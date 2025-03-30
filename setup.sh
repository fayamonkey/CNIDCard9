#!/bin/bash

echo "ClaudeNation ID App Setup"
echo "========================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python 3.8 or newer."
    echo "For Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo "For Fedora: sudo dnf install python3 python3-pip"
    echo "For macOS: brew install python3"
    exit 1
fi

echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo
echo "Creating startup script..."
echo

# Create the run script
cat > run_app.sh << 'EOL'
#!/bin/bash
source venv/bin/activate
echo "Starting ClaudeNation ID App..."
echo
echo "Please wait, the app will open in your browser shortly."
echo
streamlit run app.py
EOL

# Make the run script executable
chmod +x run_app.sh

# Create desktop shortcut if on Linux with desktop environment
if [[ "$OSTYPE" == "linux-gnu"* ]] && [ -d "$HOME/Desktop" ]; then
    echo "Creating desktop shortcut..."
    
    # Create .desktop file
    cat > "$HOME/Desktop/ClaudeNation ID App.desktop" << EOL
[Desktop Entry]
Type=Application
Name=ClaudeNation ID App
Comment=Digital ID System for ClaudeNation
Exec=$(pwd)/run_app.sh
Icon=$(pwd)/claudenation01light.jpg
Terminal=true
Categories=Utility;
EOL
    
    chmod +x "$HOME/Desktop/ClaudeNation ID App.desktop"
    echo "Desktop shortcut created."
fi

echo
echo "Setup complete!"
if [[ "$OSTYPE" == "linux-gnu"* ]] && [ -d "$HOME/Desktop" ]; then
    echo "A shortcut 'ClaudeNation ID App' has been created on your desktop."
else
    echo "You can start the app by running: ./run_app.sh"
fi
echo

read -p "Would you like to start the app now? (y/N) " choice
case "$choice" in
  y|Y ) ./run_app.sh ;;
  * ) echo "You can start the app later by running: ./run_app.sh" ;;
esac