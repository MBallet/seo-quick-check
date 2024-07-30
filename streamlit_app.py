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
st.image('https://djeholdingscom.cachefly.net/sites/g/files/aatuss516/files/styles/holding_logo_original/public/2024-03/DXI-new-logo.png?itok=xaoiwJJ7', width=200)
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
        ## Title
        st.code(meta_title)
        st.write(f"{len(meta_title)} characters")
        ## Description
        st.code(meta_description)
        st.write(f"{len(meta_description)} characters")

        # Heading Structure
        st.subheader('Heading Structure')
        headings = get_heading_structure(soup)
        
        # Create a DataFrame for heading structure
        heading_data = [(tag, text) for tag, texts in headings.items() for text in texts]
        df_headings = pd.DataFrame(heading_data, columns=['Heading Tag', 'Text'])
        st.dataframe(df_headings)  # Display DataFrame
        
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
        
        # Create a DataFrame for internal links and display it
        df_internal_links = pd.DataFrame(internal_links, columns=['Internal Links'])
        st.dataframe(df_internal_links)  # Display DataFrame
        
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

    # Create a subplot with 1 row and 2 columns
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]],
        column_widths=[0.5, 0.5],
        subplot_titles=("Performance Score", "Key Metrics")
    )

    # Add Performance Score gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=performance_score,
        title={'text': "Performance Score"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': "red"},
                {'range': [50, 90], 'color': "orange"},
                {'range': [90, 100], 'color': "green"}],
        }
    ), row=1, col=1)

    # Get metrics
    audits = lighthouse_result.get('audits', {})
    metrics = {
        "FCP": float(audits.get('first-contentful-paint', {}).get('displayValue', 'N/A').replace('s', '')),
        "SI": float(audits.get('speed-index', {}).get('displayValue', 'N/A').replace('s', '')),
        "LCP": float(audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A').replace('s', '')),
        "TTI": float(audits.get('interactive', {}).get('displayValue', 'N/A').replace('s', ''))
    }

    # Add Key Metrics bullet chart
    fig.add_trace(go.Indicator(
        mode="number+gauge+delta",
        value=metrics["FCP"],
        title={'text': "First Contentful Paint"},
        delta={'reference': 1.8, 'position': "top"},
        gauge={
            'axis': {'range': [None, 5], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 1.8], 'color': "lightgreen"},
                {'range': [1.8, 3], 'color': "orange"},
                {'range': [3, 5], 'color': "red"}],
        }
    ), row=1, col=2)

    # Update layout
    fig.update_layout(
        height=500,
        font={'color': "#444", 'size': 10},
        margin=dict(l=70, r=70, t=50, b=50),
        paper_bgcolor="white",
        plot_bgcolor='rgba(0,0,0,0)',
    )

    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

    # Display metrics table
    st.markdown("""
    <style>
    .metric-row {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #f0f0f0;
    }
    .metric-name {
        font-weight: bold;
    }
    .metric-value {
        color: #1f77b4;
    }
    .metric-status {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
    }
    .good { background-color: green; }
    .needs-improvement { background-color: orange; }
    .poor { background-color: red; }
    </style>
    """, unsafe_allow_html=True)

    def get_status(metric, value):
        thresholds = {
            "FCP": [1.8, 3],
            "SI": [3.4, 5.8],
            "LCP": [2.5, 4],
            "TTI": [3.8, 7.3]
        }
        if value <= thresholds[metric][0]:
            return "good"
        elif value <= thresholds[metric][1]:
            return "needs-improvement"
        else:
            return "poor"

    for metric, value in metrics.items():
        status = get_status(metric, value)
        st.markdown(f"""
        <div class="metric-row">
            <span class="metric-name"><span class="metric-status {status}"></span>{metric}</span>
            <span class="metric-value">{value:.2f}s</span>
        </div>
        """, unsafe_allow_html=True)

    # Add metric descriptions
    with st.expander("Metric Descriptions"):
        st.markdown("""
        - **FCP (First Contentful Paint)**: Time when the first text or image is painted.
        - **SI (Speed Index)**: How quickly the contents of a page are visibly populated.
        - **LCP (Largest Contentful Paint)**: Time when the largest text or image is painted.
        - **TTI (Time to Interactive)**: Time when the page becomes fully interactive.
        """)

except Exception as e:
    st.error(f"Error fetching PageSpeed Insights metrics: {e}")
