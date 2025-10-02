import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def get_cookies_from_env():
    """Get cookies from environment variables - only essential cookie required"""
    cookies = {}
    
    # Essential cookie (required for authentication)
    mostaqlweb = os.getenv('MOSTAQLWEB')
    if mostaqlweb:
        cookies['mostaqlweb'] = mostaqlweb
    else:
        # Fallback to default for testing
        print("Warning: MOSTAQLWEB environment variable is not set")
        print("Please set the MOSTAQLWEB environment variable in your .env file")
        print("Open mostaql.com in your browser and login")
        print("Then open the developer tools and copy the mostaqlweb cookie")
        print("Paste it in your docker-compose.yml file")
        print("Save and restart the container")
        print("Exiting...")
        exit(1)
    
    # Optional cookies (for better compatibility, but not required)
    optional_cookies = {
        'XSRF-TOKEN': os.getenv('XSRF_TOKEN'),
        'AWSALB': os.getenv('AWSALB'),
        'AWSALBCORS': os.getenv('AWSALBCORS'),
        'notification_count': os.getenv('NOTIFICATION_COUNT', '0'),
        '_ga': os.getenv('GA_ID'),
        '_ga_SPLJ01EF84': os.getenv('GA_SPLJ01EF84'),
        '_gid': os.getenv('GID'),
        '__stripe_mid': os.getenv('STRIPE_MID')
    }
    
    # Add optional cookies if they exist
    for key, value in optional_cookies.items():
        if value:
            cookies[key] = value
    
    return cookies

def save_last_seen_projects(projects):
    """Save the last seen projects to a JSON file"""
    state_file = '/app/logs/last_seen_projects.json'
    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'projects': projects
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving last seen projects: {e}")

def load_last_seen_projects():
    """Load the last seen projects from JSON file"""
    state_file = '/app/logs/last_seen_projects.json'
    try:
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('projects', [])
    except Exception as e:
        print(f"Error loading last seen projects: {e}")
    return []

def get_new_projects(current_projects, last_seen_projects):
    """Compare current projects with last seen and return only new ones"""
    if not last_seen_projects:
        return current_projects  # If no previous data, return all projects
    
    # Create sets of project links for comparison
    last_seen_links = {project['link'] for project in last_seen_projects}
    new_projects = []
    
    for project in current_projects:
        if project['link'] not in last_seen_links:
            new_projects.append(project)
    
    return new_projects

def create_notification_file(new_projects):
    """Create a notification file that can be monitored externally"""
    notification_file = '/app/logs/new_projects_notification.json'
    try:
        with open(notification_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'new_projects_count': len(new_projects),
                'new_projects': new_projects,
                'notification_sent': True
            }, f, ensure_ascii=False, indent=2)
        print(f"📄 Notification file created: {notification_file}")
    except Exception as e:
        print(f"Error creating notification file: {e}")

def play_notification_sound():
    """Play a notification sound when new projects are found"""
    # Since Docker containers can't access host audio directly,
    # we'll use multiple notification methods
    
    # Method 1: Visual notification with colors and emojis
    print("\n" + "="*60)
    print("🔔🔔🔔 NEW PROJECTS ALERT! 🔔🔔🔔")
    print("="*60)
    
    # Method 2: Create notification file for external monitoring
    # This will be handled in the main function
    
    # Method 3: Try system bell (works in some terminals)
    print('\a', end='', flush=True)
    
    # Method 4: Try to use terminal bell sequences
    print('\033[5;31m', end='')  # Blinking red text
    print("🚨 ATTENTION: NEW PROJECTS DETECTED! 🚨")
    print('\033[0m', end='')  # Reset text formatting
    
    # Method 5: Create a simple beep sound using Python
    try:
        # Generate a simple tone using print statements
        for i in range(3):
            print(f"BEEP {i+1}!", end=' ', flush=True)
            import time
            time.sleep(0.1)
        print()
    except Exception:
        pass

def get_mostaql_dashboard():
    """Make a request to mostaql.com and extract dashboard project data"""
    
    # Headers and cookies from request.sh
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'dnt': '1',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Not=A?Brand";v="24", "Chromium";v="140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    }
    
    # Get cookies from environment variables
    cookies = get_cookies_from_env()
    print("Using cookies from environment variables")
    
    try:
        # Make the request
        response = requests.get('https://mostaql.com/', headers=headers, cookies=cookies)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the dashboard section with id "dashboard__latest-published"
        dashboard_div = soup.find('div', id='dashboard__latest-published')
        
        # If not found, try the panel version
        if not dashboard_div:
            dashboard_div = soup.find('div', id='dashboard__latest-published-panel')
            if dashboard_div:
                # Look for the inner div with the actual content
                dashboard_div = dashboard_div.find('div', id='dashboard__latest-published')
        
        if not dashboard_div:
            print("Dashboard section not found")
            return []
        
        # Extract project data
        projects = []
        
        # Find all h5 elements with project titles and links
        h5_elements = dashboard_div.find_all('h5', class_='listing__title project__title mrg--bt-reset')
        
        # If not found with exact class, try partial match
        if len(h5_elements) == 0:
            h5_elements = dashboard_div.find_all('h5', class_=lambda x: x and 'listing__title' in x and 'project__title' in x)
        
        for h5 in h5_elements:
            # Find the anchor tag within h5
            link_element = h5.find('a')
            
            if link_element:
                title = link_element.get_text(strip=True)
                link = link_element.get('href', '')
                
                # Make sure link is absolute
                if link.startswith('/'):
                    link = 'https://mostaql.com' + link
                
                projects.append({
                    'title': title,
                    'link': link
                })
        
        return projects
        
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return []
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return []

def main():
    print("Fetching Mostaql dashboard projects...")
    
    # Load last seen projects
    last_seen_projects = load_last_seen_projects()
    
    # Get current projects
    current_projects = get_mostaql_dashboard()
    
    if current_projects:
        # Find only new projects
        new_projects = get_new_projects(current_projects, last_seen_projects)
        
        # Save current projects as the new baseline
        save_last_seen_projects(current_projects)
        
        if new_projects:
            # Play notification sound for new projects
            play_notification_sound()
            
            # Create notification file for external monitoring
            create_notification_file(new_projects)
            
            print(f"\n🆕 Found {len(new_projects)} NEW projects:")
            print("=" * 50)
            
            for i, project in enumerate(new_projects, 1):
                print(f"{i}. {project['title']}")
                print(f"   Link: {project['link']}")
                print()
            
            print("New projects stored in array:")
            print(json.dumps(new_projects, ensure_ascii=False, indent=2))
        else:
            print(f"\n✅ No new projects found. (Total projects checked: {len(current_projects)})")
            print("All projects have been seen before.")
    else:
        print("No projects found or error occurred")

if __name__ == "__main__":
    main()