import requests
import pandas as pd 
from bs4 import BeautifulSoup

# Function to retrieve the list of UK cities from the government website
def get_uk_cities(base_url):
    url = f'{base_url}/government/publications/list-of-cities/list-of-cities-html'
    
    # Send a GET request to the URL
    page = requests.get(url)
    
    # Initialize an empty list to store city data
    data = []
    
    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(page.text, 'html.parser')

    # Extract the main content section that contains the city list
    content = soup.find('div', id='contents').find('div', class_='govspeak')

    # Extract territory names (e.g., England, Scotland)
    territory_names = content.find_all('h3')
    territory_names = [territory.text.strip() for territory in territory_names]

    # Extract territory, country, and city names
    territories = content.find_all('h3')
    countries = content.find_all('h4')
    cities = content.find_all('ul')

    for x in range(len(countries)):
        # Determine the territory for the current country
        territory = ''
        if x <= 3:
            territory = territories[0].text.strip()
        elif x == 4:
            territory = territories[1].text.strip()
        else:
            territory = territories[2].text.strip()
        
        # Get the country name
        country = countries[x].text.strip()
        
        # Extract each city within the country
        lis = cities[x].find_all('li')
        for li in lis:
            item = {}
            
            item['Territory'] = territory
            item['Country'] = country
            item['City'] = li.text.strip().replace('*', '')
            
            data.append(item)
    
    # Return the list of UK cities
    return data
        
# Function to retrieve the list of boroughs for a specific location from the NHS website
def get_boroughs(location, base_url):
    # Construct the URL to search for boroughs based on the location
    url = f'{base_url}/service-search/find-an-nhs-sight-test/disambiguation?SeoFriendlyUrl=find-an-nhs-sight-test&location={location.strip()}'
    
    # Initialize an empty list to store borough data
    data = []
    
    # Send a GET request to the URL
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    boroughs = []
    
    # Check if the list of boroughs is present on the page
    if soup.find('ul', class_='nhsuk-list'):
        boroughs = soup.find('ul', class_='nhsuk-list').find_all('li')
    
    for borough in boroughs:
        item = {}
        
        # Extract county, borough, and postal code from the borough information
        place = borough.find('a').text.split(', ')
        
        item['County'] = place[0]
        item['Borough'] = place[1]
        item['PostalCode'] = place[2]
        item['Link'] = f'{base_url}/{borough.find('a').attrs['href']}'
        
        data.append(item)
        
    # Return the list of boroughs
    return data

# Function to retrieve eye service centres within a specific borough
def get_eye_service_centres(borough):
    # Send a GET request to the borough's page
    page = requests.get(borough['Link'])
    
    # Initialize an empty list to store eye service centre data
    data = []
    
    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(page.text, 'html.parser')
    
    # Extract the list of eye service centres
    testCentres = soup.find('ol', class_='nhsuk-list results').find_all('li')
    
    for x in range(len(testCentres)):
        item = {}
        
        item['County'] = borough['County']
        item['Borough'] = borough['Borough']
        
        # Extract and clean the distance, centre name, address, and phone number
        li = testCentres[x]
        li.find('p', id=f'distance_{x}').span.decompose()
        item['Distance'] = li.find('p', id=f'distance_{x}').get_text(strip=True)
        li.find('h2', id=f'orgname_{x}').span.decompose()
        item['CentreName'] = li.find('h2', id=f'orgname_{x}').get_text(strip=True)
        li.find('p', id=f'address_{x}').span.decompose()
        item['Address'] = li.find('p', id=f'address_{x}').get_text(strip=True)
        if li.find('p', id=f'phone_{x}').span:
            li.find('p', id=f'phone_{x}').span.decompose()
        item['Phone'] = li.find('p', id=f'phone_{x}').get_text(strip=True)
        item['MapLink'] = li.find('a', id=f'map_link_{x}').attrs['href']
        
        data.append(item)
    
    # Return the list of eye service centres
    return data

# Main function to generate and save records of eye service centres for UK cities
def main():
    # Proxy (if needed for requests, currently unused)
    proxy = ''
    
    # Base URL for UK government site
    uk_gov_base_url = 'https://www.gov.uk'
    
    # Base URL for NHS site
    nhs_base_url = 'https://www.nhs.uk'

    # Retrieve the list of UK cities
    uk_cities = get_uk_cities(uk_gov_base_url)
    
    # Filter the list to include only cities in England
    england_cities = [city['City'] for city in uk_cities if city['Country'] == 'England']
    
    i = 0
    size = len(england_cities)
    
    # Loop through each city in England to generate and save the records
    while (i < size):
        city_name = england_cities[i]
        print(f'Generating record for {city_name}.')
        
        # Retrieve the list of boroughs for the city
        boroughs = get_boroughs(city_name, nhs_base_url)
        
        # Initialize an empty list to store all eye service centre data
        data = []
            
        for borough in boroughs:
            # Retrieve and append eye service centres for each borough
            eye_centres = get_eye_service_centres(borough)
            data.extend(eye_centres)
            
        # Create a DataFrame from the collected data and save it as a CSV file
        df = pd.DataFrame(data)
        df.to_csv(f'{city_name.lower()}.csv')
        i += 1
    
# Execute the main function
main()
