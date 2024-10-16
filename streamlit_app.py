import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
from googleapiclient.discovery import build
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

# Streamlit app layout
# Set the page configuration
st.set_page_config(page_title="URL Analyzer", page_icon=":mag:")

st.image('https://djeholdingscom.cachefly.net/sites/g/files/aatuss516/files/styles/holding_logo_original/public/2024-03/DXI-new-logo.png?itok=xaoiwJJ7', width=200)
st.title("URL Analyzer")

api_key = st.secrets["PAGESPEED_API_KEY"]
url = st.text_input('Enter URL:', 'https://www.example.com')

if 'soup' not in st.session_state:
    st.session_state['soup'] = None

if 'headings' not in st.session_state:
    st.session_state['headings'] = None

if 'internal_links' not in st.session_state:
    st.session_state['internal_links'] = None

if st.button('Analyze') and api_key:
    
        st.session_state['soup'] = soup
        domain = url.split('//')[-1].split('/')[0]
        
        # Meta Data
        st.subheader('Meta Data', divider=True)
        meta_title, meta_description = get_meta_data(soup)
        st.subheader('Title')
        st.text_input('Title:', meta_title)
        title_length = len(meta_title)
        if title_length > 60:
            st.warning(f"Title is too long: {title_length} characters (recommended: 55-60 characters)")
        else:
            st.success(f"Title length is good: {title_length} characters")
        
        st.subheader('Description')
        st.text_area('Description:', meta_description)
        description_length = len(meta_description)
        if description_length > 160:
            st.warning(f"Description is too long: {description_length} characters (recommended: 120-160 characters)")
        else:
            st.success(f"Description length is good: {description_length} characters")

        # Heading Structure
        st.subheader('Heading Structure')
        headings = get_heading_structure(soup)
        st.session_state['headings'] = headings
        heading_data = [(tag, text) for tag, texts in headings.items() for text in texts]
        df_headings = pd.DataFrame(heading_data, columns=['Heading Tag', 'Text'])
        st.dataframe(df_headings)
        csv_headings = df_headings.to_csv(index=False)
        st.download_button(
            label="Download Heading Structure as CSV",
            data=csv_headings,
            file_name='heading_structure.csv',
            mime='text/csv',
        )

        # Heading warnings and success messages
        if not heading_data:
            st.warning("No headings found on the page.")
        else:
            if len(headings['H1']) == 0:
                st.error("No H1 found on the page.")
            elif len(headings['H1']) > 1:
                st.error("Multiple H1s found on the page.")
            else:
                st.success("H1 structure looks good.")
            
            if len(headings['H2']) == 0:
                st.warning("No H2s found on the page.")
            else:
                st.success("H2 structure looks good.")
            
            if len(headings['H3']) == 0:
                st.warning("No H3s found on the page.")
            else:
                st.success("H3 structure looks good.")

        # Internal Links
        st.subheader('Internal Links')
        internal_links = get_internal_links(soup, domain)
        st.session_state['internal_links'] = internal_links
        st.write(f"**Total Internal Links:** {len(internal_links)}")
        df_internal_links = pd.DataFrame(internal_links, columns=['Internal Links'])
        st.dataframe(df_internal_links)
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
        with st.spinner('Collecting page speed metrics...'):
            try:
                pagespeed_metrics = get_pagespeed_metrics(url, api_key)
                lighthouse_result = pagespeed_metrics.get('lighthouseResult', {})
                categories = lighthouse_result.get('categories', {})
                performance_score = categories.get('performance', {}).get('score', 'N/A') * 100

                # Ensure performance_score is an integer
                performance_score = int(performance_score)

                # Performance Score Display
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=performance_score,
                    title={'text': "Performance Score"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                        'bar': {'color': "royalblue"},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, 50], 'color': "red"},
                            {'range': [50, 90], 'color': "orange"},
                            {'range': [90, 100], 'color': "green"}],
                    }
                ))

                fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)

                # Other Metrics Display
                st.subheader("Other PageSpeed Metrics")
                audits = lighthouse_result.get('audits', {})
                metrics = {
                    "First Contentful Paint": audits.get('first-contentful-paint', {}).get('displayValue', 'N/A'),
                    "Speed Index": audits.get('speed-index', {}).get('displayValue', 'N/A'),
                    "Largest Contentful Paint": audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A'),
                    "Time to Interactive": audits.get('interactive', {}).get('displayValue', 'N/A')
                }

                # Define desirable ranges
                desirable_ranges = {
                    "First Contentful Paint": 1.8,
                    "Speed Index": 3.4,
                    "Largest Contentful Paint": 2.5,
                    "Time to Interactive": 3.8
                }

                # Create 2x2 grid for other metrics
                col1, col2 = st.columns(2)
                
                for i, (metric, value) in enumerate(metrics.items()):
                    with col1 if i % 2 == 0 else col2:
                        st.metric(
                            label=metric,
                            value=value,
                            delta="Good" if float(value.replace('s', '')) <= desirable_ranges[metric] else "Needs Improvement",
                            delta_color="normal" if float(value.replace('s', '')) <= desirable_ranges[metric] else "inverse"
                        )

                # Display metric descriptions
                st.subheader("Metric Descriptions")
                descriptions = {
                    "Performance Score": "A weighted average of key performance metrics, ranging from 0 to 100. It assesses the overall speed and responsiveness of a webpage.",
                    "First Contentful Paint (FCP)": "Measures the time from when the page starts loading to when any part of the page's content is rendered on the screen.",
                    "Speed Index (SI)": "Measures how quickly the content of a page is visually displayed during load.",
                    "Largest Contentful Paint (LCP)": "Measures the time from when the page starts loading to when the largest text block or image is rendered on the screen.",
                    "Time to Interactive (TTI)": "Measures the time it takes for the page to become fully interactive."
                }

                for metric, description in descriptions.items():
                    with st.expander(metric):
                        st.write(description)

            except Exception as e:
                st.error(f"Error fetching PageSpeed Insights metrics: {e}")
