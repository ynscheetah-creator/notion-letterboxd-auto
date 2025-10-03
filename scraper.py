name: Letterboxd Scraper

on:
  schedule:
    - cron: '*/30 * * * *'
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        pip install requests
        
    - name: Run scraper
      env:
        NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
        FILMS_DB_ID: ${{ secrets.FILMS_DB_ID }}
      run: python scraper.py
