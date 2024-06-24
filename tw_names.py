import requests
from bs4 import BeautifulSoup

def extract_words_from_html(html_content):
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all `a` tags with the `title` attribute ending in ".md"
    a_tags = soup.find_all('a', href=True, title=lambda x: x and x.endswith('.md'))

    # Extract the words and store them in a list
    words = [a_tag['title'].split('.md')[0] for a_tag in a_tags]

    return words

# To fetch the HTML content from a URL
def extract_words_from_url(url):
    # Send an HTTP request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        html_content = response.text
        return extract_words_from_html(html_content)
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return []

# Example URL of the page to scrape
url = 'https://git.door43.org/unfoldingWord/en_tw/src/branch/master/bible/names'

# Extract words from the URL
words_from_url = extract_words_from_url(url)
print(words_from_url)
