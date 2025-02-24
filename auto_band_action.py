name: Band Auto Posting

on:
  workflow_dispatch:
  schedule:
    - cron: '0 */1 * * *'

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
        
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y unzip
        pip install selenium requests beautifulsoup4 webdriver_manager
        
    - name: Setup Chrome
      uses: browser-actions/setup-chrome@latest

    - name: Install Chrome and ChromeDriver
      run: |
        wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
        sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
        sudo apt-get update
        sudo apt-get install -y google-chrome-stable
        
        CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
        CHROME_MAJOR_VERSION=$(echo "$CHROME_VERSION" | cut -d. -f1)
        
        API_URL="https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        MATCHING_DRIVER=$(curl -s "$API_URL" | \
          jq -r ".versions[] | 
          select(.version | startswith(\"$CHROME_MAJOR_VERSION.\")) |
          .downloads.chromedriver[] | 
          select(.platform==\"linux64\").url" | head -1)
        
        wget -q "$MATCHING_DRIVER" -O chromedriver.zip
        unzip -o chromedriver.zip
        sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
        sudo chmod +x /usr/local/bin/chromedriver

    - name: Extract Chrome Profile
      run: |
        unzip chrome_profile.zip -d chrome-profile
        chmod -R 777 chrome-profile
        echo "CHROME_PROFILE_DIR=$(pwd)/chrome-profile" >> $GITHUB_ENV
        ls -la chrome-profile/Default/

    - name: Start Xvfb
      run: Xvfb :99 -screen 0 1920x1080x24 &

    - name: Set Display
      run: echo "DISPLAY=:99" >> $GITHUB_ENV

    - name: Run Auto Posting
      env:
        DISPLAY: :99
        PYTHONUNBUFFERED: 1
        TZ: "Asia/Seoul"
      run: |
        python auto_band_action.py 2>&1 | tee band_auto.log
