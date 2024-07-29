import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd

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
    
    # Make meta title and description easily copyable
    st.text_area("Meta Title", value=meta_title, height=50)
    st.text_area("Meta Description", value=meta_description, height=100)

    # Heading Structure
    st.subheader('Heading Structure')
    headings = get_heading_structure(soup)
    for tag, texts in headings.items():
        with st.expander(tag):
            for text in texts:
                st.write(text)
    
    # Create a DataFrame and download button for heading structure
    heading_data = [(tag, text) for tag, texts in headings.items() for text in texts]
    df_headings = pd.DataFrame(heading_data, columns=['Heading Tag', 'Text'])
    csv_headings = df_headings.to_csv(index=False)
    st.download_button(
        label="Download Heading Structure as CSV",
        data=csv_headings,
        file_name='heading_structure.csv',
        mime='text/csv',
    )

    # Internal Links
    st.subheader('Internal Links')
    internal_links = get_internal_links(soup, domain)
    st.write(f"**Total Internal Links:** {len(internal_links)}")
    for link in internal_links:
        st.write(link)

    # Create a DataFrame and download button for internal links
    df_internal_links = pd.DataFrame(internal_links, columns=['Internal Links'])
    csv_internal_links = df_internal_links.to_csv(index=False)
    st.download_button(
        label="Download Internal Links as CSV",
        data=csv_internal_links,
        file_name='internal_links.csv',
        mime='text/csv',
    )

# To run the app, save this code to a file (e.g., app.py) and run it using the command:
# streamlit run app.py
