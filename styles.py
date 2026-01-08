MOBILE_CSS = """
<style>
/* Hide Streamlit top bar and hamburger menu */
.css-1d391kg {
    display: none !important;
}
.css-1lcbmhc {
    display: none !important;
}

/* Force Dark Mode Colors */
.stApp {
    background-color: #0E1117 !important;
    color: white !important;
}

[data-testid="stSidebar"] {
    background-color: #1A1B23 !important;
    border-right: 1px solid #262730 !important;
}

/* Style metrics as big bold buttons */
[data-testid="metric-container"] {
    background-color: #262730 !important;
    border: 2px solid #3A3B47 !important;
    border-radius: 16px !important;
    padding: 20px !important;
    margin: 10px 0 !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
}

[data-testid="metric-label"] {
    color: #B8BCC8 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

[data-testid="metric-value"] {
    color: #FFFFFF !important;
    font-size: 32px !important;
    font-weight: 700 !important;
}

/* Pulsing green animation for GO NOW */
@keyframes pulse-green {
    0% {
        background-color: #28a745 !important;
        box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7) !important;
    }
    70% {
        background-color: #28a745 !important;
        box-shadow: 0 0 0 10px rgba(40, 167, 69, 0) !important;
    }
    100% {
        background-color: #28a745 !important;
        box-shadow: 0 0 0 0 rgba(40, 167, 69, 0) !important;
    }
}

.go-now-pulse {
    animation: pulse-green 2s infinite !important;
    background-color: #28a745 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    font-weight: 600 !important;
}

/* Increase font sizes for mobile readability */
h1 {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
}

h2 {
    font-size: 22px !important;
    font-weight: 600 !important;
    color: #FFFFFF !important;
}

/* Dataframe styling */
[data-testid="stDataFrame"] {
    background-color: #262730 !important;
    border: 1px solid #3A3B47 !important;
    border-radius: 8px !important;
}

[data-testid="stDataFrame"] table {
    color: #FFFFFF !important;
    font-size: 14px !important;
}

[data-testid="stDataFrame"] th {
    background-color: #1A1B23 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

[data-testid="stDataFrame"] td {
    border-bottom: 1px solid #3A3B47 !important;
}
</style>
"""
