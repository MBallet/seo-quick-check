import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io

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

# Function to extract body text
def get_body_text(soup):
    paragraphs = soup.find_all('p')
    body_text = ' '.join([p.get_text() for p in paragraphs])
    return body_text[:500]

# Function to get PageSpeed Insights metrics
def get_pagespeed_metrics(url, api_key):
    service = build('pagespeedonline', 'v5', developerKey=api_key)
    request = service.pagespeedapi().runpagespeed(url=url)
    response = request.execute()
    return response

# Function to capture screenshot
def capture_screenshot(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    screenshot = driver.get_screenshot_as_png()
    driver.quit()
    return Image.open(io.BytesIO(screenshot))

# Streamlit app layout
st.title('URL Analyzer')

api_key = st.text_input('Enter your Google PageSpeed API Key:')
url = st.text_input('Enter URL:', 'https://www.example.com')

if st.button('Analyze') and api_key:
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
    
    # Create a DataFrame for heading structure
    heading_data = [(tag, text) for tag, texts in headings.items() for text in texts]
    df_headings = pd.DataFrame(heading_data, columns=['Heading Tag', 'Text'])
    csv_headings = df_headings.to_csv(index=False)
    st.download_button(
        label="Download Heading Structure as CSV",
        data=csv_headings,
        file_name='heading_structure.csv',
        mime='text/csv',
    )

    # Display heading structure in expandable format
    for tag, texts in headings.items():
        with st.expander(tag):
            for text in texts:
                st.write(text)
    
    # Internal Links
    st.subheader('Internal Links')
    internal_links = get_internal_links(soup, domain)
    st.write(f"**Total Internal Links:** {len(internal_links)}")
    for link in internal_links:
        st.write(link)

    # Create a DataFrame for internal links and add download button
    df_internal_links = pd.DataFrame(internal_links, columns=['Internal Links'])
    csv_internal_links = df_internal_links.to_csv(index=False)
    st.download_button(
        label="Download Internal Links as CSV",
        data=csv_internal_links,
        file_name='internal_links.csv',
        mime='text/csv',
    )

    # Body Text
    st.subheader('Body Text')
    body_text = get_body_text(soup)
    st.write(f"**First 500 characters of body text:** {body_text}")

    # PageSpeed Insights
    st.subheader('PageSpeed Insights')
    try:
        pagespeed_metrics = get_pagespeed_metrics(url, api_key)
        lighthouse_result = pagespeed_metrics.get('lighthouseResult', {})
        categories = lighthouse_result.get('categories', {})
        performance_score = categories.get('performance', {}).get('score', 'N/A') * 100
        st.write(f"**Performance Score:** {performance_score}")

        # Display additional PageSpeed metrics if needed
        audits = lighthouse_result.get('audits', {})
        first_contentful_paint = audits.get('first-contentful-paint', {}).get('displayValue', 'N/A')
        speed_index = audits.get('speed-index', {}).get('displayValue', 'N/A')
        largest_contentful_paint = audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A')
        time_to_interactive = audits.get('interactive', {}).get('displayValue', 'N/A')

        st.write(f"**First Contentful Paint:** {first_contentful_paint}")
        st.write(f"**Speed Index:** {speed_index}")
        st.write(f"**Largest Contentful Paint:** {largest_contentful_paint}")
        st.write(f"**Time to Interactive:** {time_to_interactive}")

    except Exception as e:
        st.error(f"Error fetching PageSpeed Insights metrics: {e}")

    # Screenshot
    st.subheader('Website Screenshot')
    try:
        screenshot = capture_screenshot(url)
        st.image(screenshot, caption='Website Screenshot', use_column_width=True)
    except Exception as e:
        st.error(f"Error capturing screenshot: {e}")

# To run the app, save this code to a file (e.g., app.py) and run it using the command:
# streamlit run app.py
