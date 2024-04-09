import requests
from bs4 import BeautifulSoup
import pandas as pd

baseurl = 'https://rurex.pl/pl/produkty/1/rury-pvc-wavin-173219'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
}

link_end = ['kanalizacja-zewnetrzna-172906', 'armatura-wodociagowa-172908', 'kanalizacja-wewnetrzna-172917', 'systemy-wodociagowe-172907']


def link_extraction(link_end):
    product_links = []

    for end in link_end:
        r = requests.get(f'https://rurex.pl/pl/produkty/1/{end}', headers=headers)
        soup = BeautifulSoup(r.content, 'lxml')
        pagination = soup.find('ul', class_='pagination')
        print('Saving from ' + end)
        if pagination:
            li_elements = pagination.find_all('li')
            pg_num = len(li_elements)

            for x in range(1, pg_num):
                r = requests.get(f'https://rurex.pl/pl/produkty/{x}/{end}', headers=headers)
                soup = BeautifulSoup(r.content, 'lxml')
                product_list = soup.find_all('div', class_='product-image')
                for item in product_list:
                    for link in item.find_all('a', href=True):
                        product_links.append(link['href'])
    return product_links


def extract_product_data(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'lxml')

    # Extracting data
    name = soup.find('h1').text.strip()

    jm = soup.find('strong', text='J.m.:').find_next_sibling(text=True).strip()

    div = soup.find_all('div', class_='margin-bottom20')
    trade_index = None
    for paragraph in div[5]:
        if 'Symbol:' in paragraph.text:
            trade_index = paragraph.text.strip().split(':')[-1].strip()
            break
    if trade_index==None:
       for paragraph in div[6]:
        if 'Symbol:' in paragraph.text:
            trade_index =  paragraph.text.strip().split(':')[-1].strip()
            break       
    # Generating product dictionary
    print('Saving product:' + name)
    product = {
        'NAME': name,
        'NAME_ORG': name,
        'category': 'rurex',
        'JM': jm,
        'type': 'Towar',
        'trade_index': trade_index,
        'manufacturer_index': 'Rurex'
    }

    return product


# Extracting product links
product_links = link_extraction(link_end)

# Extracting product data
products_data = []
for link in product_links:
    product_data = extract_product_data(link)
    products_data.append(product_data)

# Converting to DataFrame
df = pd.DataFrame(products_data)

# Exporting to Excel
df.to_excel('productsRurex.xlsx', index=False)
