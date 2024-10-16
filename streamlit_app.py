import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
from googleapiclient.discovery import build
import plotly.graph_objects as go

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

# Store data in session state to prevent app reruns
if 'data' not in st.session_state:
    st.session_state.data = {}

if st.button('Analyze') and api_key:
    with st.spinner('Collecting page speed metrics...'):
        soup = fetch_url(url)
        domain = url.split('//')[-1].split('/')[0]
        
        # Meta Data
        st.session_state.data['meta_title'], st.session_state.data['meta_description'] = get_meta_data(soup)

        # Heading Structure
        headings = get_heading_structure(soup)
        heading_data = [(tag, text) for tag, texts in headings.items() for text in texts]
        df_headings = pd.DataFrame(heading_data, columns=['Heading Tag', 'Text'])
        st.session_state.data['df_headings'] = df_headings

        # Internal Links
        internal_links = get_internal_links(soup, domain)
        df_internal_links = pd.DataFrame(internal_links, columns=['Internal Links'])
        st.session_state.data['df_internal_links'] = df_internal_links

        # Body Text
        st.session_state.data['body_text'] = get_body_text(soup)

        # PageSpeed Insights Metrics
        try:
            st.session_state.data['pagespeed_metrics'] = get_pagespeed_metrics(url, api_key)
        except Exception as e:
            st.error(f"Error fetching PageSpeed Insights metrics: {e}")

# Display cached data without rerunning the analysis
if 'meta_title' in st.session_state.data:
    st.subheader('Meta Data', divider=True)
    st.subheader('Title')
    st.code(st.session_state.data['meta_title'])
    st.write(f"{len(st.session_state.data['meta_title'])} characters")
    st.subheader('Description')
    st.code(st.session_state.data['meta_description'])
    st.write(f"{len(st.session_state.data['meta_description'])} characters")

if 'df_headings' in st.session_state.data:
    st.subheader('Heading Structure')
    st.dataframe(st.session_state.data['df_headings'])
    csv_headings = st.session_state.data['df_headings'].to_csv(index=False)
    st.download_button(
        label="Download Heading Structure as CSV",
        data=csv_headings,
        file_name='heading_structure.csv',
        mime='text/csv',
    )

if 'df_internal_links' in st.session_state.data:
    st.subheader('Internal Links')
    st.write(f"**Total Internal Links:** {len(st.session_state.data['df_internal_links'])}")
    st.dataframe(st.session_state.data['df_internal_links'])
    csv_internal_links = st.session_state.data['df_internal_links'].to_csv(index=False)
    st.download_button(
        label="Download Internal Links as CSV",
        data=csv_internal_links,
        file_name='internal_links.csv',
        mime='text/csv',
    )

if 'body_text' in st.session_state.data:
    st.subheader('Body Text')
    st.write(f"{st.session_state.data['body_text']}")

# Display PageSpeed metrics if available
if 'pagespeed_metrics' in st.session_state.data:
    pagespeed_metrics = st.session_state.data['pagespeed_metrics']
    lighthouse_result = pagespeed_metrics.get('lighthouseResult', {})
    categories = lighthouse_result.get('categories', {})
    performance_score = categories.get('performance', {}).get('score', 'N/A') * 100
    performance_score = int(performance_score)

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
