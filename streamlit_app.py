import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
from googleapiclient.discovery import build

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

# Function to color code the performance score
def color_code_performance_score(score):
    if score >= 90:
        return 'green'
    elif score >= 50:
        return 'orange'
    else:
        return 'red'

# Function to color code the PageSpeed metrics
def color_code_metric(value, desirable_range):
    if value <= desirable_range:
        return 'green'
    else:
        return 'red'

# Streamlit app layout
st.title('URL Analyzer')

api_key = st.secrets["PAGESPEED_API_KEY"]
url = st.text_input('Enter URL:', 'https://www.example.com')

if st.button('Analyze') and api_key:
    with st.spinner('Loading data...'):
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
        internal_links

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
        st.write(f"{body_text}")

        # PageSpeed Insights
        st.subheader('PageSpeed Insights')
        try:
            pagespeed_metrics = get_pagespeed_metrics(url, api_key)
            lighthouse_result = pagespeed_metrics.get('lighthouseResult', {})
            categories = lighthouse_result.get('categories', {})
            performance_score = categories.get('performance', {}).get('score', 'N/A') * 100

            # Ensure performance_score is an integer
            performance_score = int(performance_score)

            # Color code for the performance score
            score_color = color_code_performance_score(performance_score)
            st.markdown(
                f'<div style="text-align:center; font-size:50px; color:{score_color}">{performance_score}</div>',
                unsafe_allow_html=True
            )

            # Display additional PageSpeed metrics
            audits = lighthouse_result.get('audits', {})
            first_contentful_paint = audits.get('first-contentful-paint', {}).get('displayValue', 'N/A').replace('s', '')
            speed_index = audits.get('speed-index', {}).get('displayValue', 'N/A').replace('s', '')
            largest_contentful_paint = audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A').replace('s', '')
            time_to_interactive = audits.get('interactive', {}).get('displayValue', 'N/A').replace('s', '')

            # Ensure the metrics are floats
            first_contentful_paint = float(first_contentful_paint) if first_contentful_paint != 'N/A' else 'N/A'
            speed_index = float(speed_index) if speed_index != 'N/A' else 'N/A'
            largest_contentful_paint = float(largest_contentful_paint) if largest_contentful_paint != 'N/A' else 'N/A'
            time_to_interactive = float(time_to_interactive) if time_to_interactive != 'N/A' else 'N/A'

            # Define desirable ranges
            desirable_ranges = {
                "First Contentful Paint": 1.8,
                "Speed Index": 3.4,
                "Largest Contentful Paint": 2.5,
                "Time to Interactive": 3.8
            }

            # Display metrics with color coding
            fcp_color = color_code_metric(first_contentful_paint, desirable_ranges["First Contentful Paint"])
            si_color = color_code_metric(speed_index, desirable_ranges["Speed Index"])
            lcp_color = color_code_metric(largest_contentful_paint, desirable_ranges["Largest Contentful Paint"])
            tti_color = color_code_metric(time_to_interactive, desirable_ranges["Time to Interactive"])

            st.markdown(
                f'<div style="color:{fcp_color}">First Contentful Paint: {first_contentful_paint} seconds</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div style="color:{si_color}">Speed Index: {speed_index} seconds</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div style="color:{lcp_color}">Largest Contentful Paint: {largest_contentful_paint} seconds</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div style="color:{tti_color}">Time to Interactive: {time_to_interactive} seconds</div>',
                unsafe_allow_html=True
            )

        except Exception as e:
            st.error(f"Error fetching PageSpeed Insights metrics: {e}")

# To run the app, save this code to a file (e.g., app.py) and run it using the command:
# streamlit run app.py
