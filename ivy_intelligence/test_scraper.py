import os
import django
import sys

# Set up Django environment manually
project_path = r'c:\Users\srini\Downloads\ivy_intelligence_project\ivy_intelligence'
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.opportunities.scraper import run_scraper
print("Testing HARVARD scraper:", run_scraper('HARVARD'))
print("Testing MIT scraper:", run_scraper('MIT'))
