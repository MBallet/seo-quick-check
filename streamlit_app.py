import streamlit as st
from bs4 import BeautifulSoup
import requests

# Function to fetch and parse URL content
def fetch_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

# Function to extract meta data
def get_meta_data(soup):
    meta_title = soup.title.string if soup.title else 'No title found'
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_description = meta_description['content'] if meta_description else 'No description found'
    return meta_title, meta_description

# Function to extract heading structure
def get_heading_structure(soup):
    headings = {}
    for i in range(1, 5):
        headings[f'H{i}'] = [heading.get_text() for heading in soup.find_all(f'h{i}')]
    return headings

# Function to extract internal links
def get_internal_links(soup, domain):
    internal_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if domain in href:
            internal_links.append(href)
    return internal_links

# Streamlit app layout
st.title('URL Analyzer')

url = st.text_input('Enter URL:', 'https://www.example.com')

if st.button('Analyze'):
    soup = fetch_url(url)
    domain = url.split('//')[-1].split('/')[0]
    
    # Meta Data
    st.subheader('Meta Data')
    meta_title, meta_description = get_meta_data(soup)
    st.write(f"**Title:** {meta_title} ({len(meta_title)} characters)")
    st.write(f"**Description:** {meta_description} ({len(meta_description)} characters)")

    # Heading Structure
    st.subheader('Heading Structure')
    headings = get_heading_structure(soup)
    for tag, texts in headings.items():
        with st.expander(tag):
            for text in texts:
                st.write(text)

    # Internal Links
    st.subheader('Internal Links')
    internal_links = get_internal_links(soup, domain)
    for link in internal_links:
        st.write(link)

# To run the app, save this code to a file (e.g., app.py) and run it using the command:
# streamlit run app.py
