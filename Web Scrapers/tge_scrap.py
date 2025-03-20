from datetime import date, timedelta

import requests
import pandas as pd
from bs4 import BeautifulSoup

from database import postgres_old_connection as conn


baseurl = 'https://www.tge.pl'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
}


def convert_to_float(value):
    if value == '-':
        return 0.0
    return float(value.replace(',', '.'))

def data_extraction(extraction_date: date):
    extraction_date_str = extraction_date.strftime('%d-%m-%Y')
    url = f'{baseurl}/energia-elektryczna-rdn?dateShow={extraction_date_str}'
    print(f'Attempting to fetch: {url}')
    
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            r = session.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.content, 'html.parser')
            tabela = soup.find('table', id='footable_kontrakty_godzinowe')
            
            if tabela:
                print("Successfully found the table")
               
                data_list = []
                rows = tabela.find('tbody').find_all('tr')
                
                for row in rows:
                    cols = row.find_all('td')
                    if cols:
                        time = cols[0].find('b').text.strip()
                        fixing_1_price = cols[1].text.strip()
                        fixing_1_volume = cols[2].text.strip()
                        fixing_2_price = cols[3].text.strip()
                        fixing_2_volume = cols[4].text.strip()
                        continuous_price = cols[5].text.strip()
                        continuous_volume = cols[6].text.strip()
                        
                        data_list.append({
                            'time': time,
                            'fixing_1': {'price': fixing_1_price, 'volume': fixing_1_volume},
                            'fixing_2': {'price': fixing_2_price, 'volume': fixing_2_volume},
                            'continuous': {'price': continuous_price, 'volume': continuous_volume}
                        })
                
                print("\nExtracted data:")
                for entry in data_list:
                    print(f"\nTime: {entry['time']}")
                    print(f"Fixing 1: Price: {entry['fixing_1']['price']}, Volume: {entry['fixing_1']['volume']}")
                    print(f"Fixing 2: Price: {entry['fixing_2']['price']}, Volume: {entry['fixing_2']['volume']}")
                    print(f"Continuous: Price: {entry['continuous']['price']}, Volume: {entry['continuous']['volume']}")
                
                return data_list
            else:
                print("Table not found in the response")
                print("Available tables:", [table.get('id', 'no-id') for table in soup.find_all('table')])
            break
            
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Could not fetch the data.")
                raise


def pobierz_cena_gaz(extraction_date):
    extraction_date_str = extraction_date.strftime('%d-%m-%Y')
    url = f'{baseurl}/gaz-rdn?dateShow={extraction_date_str}'
    print(url)
    print(f'Attempting to fetch: {url}')
    
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            r = session.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.content, 'html.parser')
            tabela = soup.find('table', id='footable_indeksy_0')
            
            if tabela:
                print("Successfully found the table")
                rows = tabela.find('tbody').find_all('tr')
                
                for row in rows:
                    cols = row.find_all('td')
                    if cols:
                        cena = cols[2].text.strip()
                        wolumen=cols[4].text.strip()
                        return convert_to_float(cena) , convert_to_float(wolumen)

                return convert_to_float(cena) , convert_to_float(wolumen)
            else:
                print("Table not found in the response")
                print("Available tables:", [table.get('id', 'no-id') for table in soup.find_all('table')])
            break
            
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
            else:
                print("Max retries reached. Could not fetch the data.")
                raise

def data_insertion(data, extraction_date: date):
    cur = conn.cursor()
    cena_gaz,wolumen_gaz=pobierz_cena_gaz(extraction_date)
    extraction_date=extraction_date+timedelta(1)
    extraction_date_str = extraction_date.strftime('%d-%m-%Y')
    cur.execute("""CREATE TABLE IF NOT EXISTS tge 
                (id SERIAL PRIMARY KEY, dzien DATE, time varchar, fixing_1_price DECIMAL, fixing_1_volume DECIMAL,
                fixing_2_price DECIMAL, fixing_2_volume DECIMAL, continuous_price DECIMAL, 
                continuous_volume DECIMAL,cena_gaz DECIMAL,wolumen_gaz DECIMAL)""")
    conn.commit()
    
    for entry in data:
        time = entry['time']
        fixing_1_price = convert_to_float(entry['fixing_1']['price'])
        fixing_1_volume = convert_to_float(entry['fixing_1']['volume'])
        fixing_2_price = convert_to_float(entry['fixing_2']['price'])
        fixing_2_volume = convert_to_float(entry['fixing_2']['volume'])
        continuous_price = convert_to_float(entry['continuous']['price'])
        continuous_volume = convert_to_float(entry['continuous']['volume'])

        cur.execute("""INSERT INTO tge (dzien, time, fixing_1_price, fixing_1_volume, 
                    fixing_2_price, fixing_2_volume, continuous_price, continuous_volume,cena_gaz,wolumen_gaz) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s,%s)""",
                    (extraction_date_str, time, fixing_1_price, fixing_1_volume, fixing_2_price, 
                     fixing_2_volume, continuous_price, continuous_volume,cena_gaz,wolumen_gaz))
        conn.commit()
    cur.close()
    

def get_last_tge_fetch_date():
    cur = conn.cursor()
    query = 'SELECT max(dzien) FROM tge'
    cur.execute(query)
    last_fetch_date = cur.fetchone()[0]
    return last_fetch_date


def tge_scraper_job():
    last_fetch_date = get_last_tge_fetch_date()
    start_date = last_fetch_date
    end_date = date.today()
    dates_to_extract = pd.date_range(start=start_date, end=end_date).tolist()
    for extraction_date in dates_to_extract:
        data=data_extraction(extraction_date)
        data_insertion(data, extraction_date)

