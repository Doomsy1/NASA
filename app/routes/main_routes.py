# app/routes/main_routes.py
from flask import Blueprint, render_template, session, request, jsonify
import sqlite3
from app.utils import login_required
import openai
import os

# Additional imports for the new plotting functionality
import numpy as np
from netCDF4 import Dataset
import pandas as pd
import plotly.express as px

main_bp = Blueprint('main', __name__)

# Routes
@main_bp.route('/')
def home():
    if 'logged_in' not in session:
        return render_template("logged_out_home.html")
    else:
        return render_template("logged_in_home.html")

@main_bp.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if 'conversation' not in session:
        session['conversation'] = []

    if request.method == 'POST':
        data = request.get_json()
        user_input = data.get('user_input', '').strip()
        # Append the user's message to the conversation
        session['conversation'].append({"role": "user", "content": user_input})
        openai.api_key = os.getenv('OPENAI_API_KEY')

        try:
            # OpenAI API call using the updated ChatCompletion endpoint
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Or "gpt-4" if you have access
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are AgroAssist, an intelligent and friendly farming assistant chatbot designed to help "
                            "farmers and agricultural enthusiasts. Your expertise spans crop cultivation, soil health, "
                            "irrigation techniques, pest and disease management, livestock care, weather forecasting, "
                            "and sustainable farming practices. You provide clear, concise, and actionable advice tailored "
                            "to the user's specific location, climate, and farming conditions. When giving recommendations, "
                            "consider factors like seasonality, local regulations, and the latest advancements in agricultural "
                            "technology. Your goal is to support users in optimizing their farming operations while promoting "
                            "environmental sustainability and efficiency."
                        ),
                    },
                    *session['conversation'],
                ],
                max_tokens=150,
                temperature=0.7,
            )

            ai_response = response['choices'][0]['message']['content'].strip()
            # Append the assistant's response to the conversation
            session['conversation'].append({"role": "assistant", "content": ai_response})
        except Exception as e:
            print(f"OpenAI API error: {e}")
            ai_response = "Sorry, I'm having trouble accessing the AI service at the moment."
            session['conversation'].append({"role": "assistant", "content": ai_response})

        # Return the assistant's response as JSON
        return jsonify({'assistant_response': ai_response})

    else:
        return render_template('chat.html')

@main_bp.route('/forecast')
@login_required
def forecast():
    return render_template("forecast.html")

@main_bp.route('/farmer_discussion')
@login_required
def farmer_discussion():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, username, message, timestamp FROM messages ORDER BY timestamp ASC")
    messages = c.fetchall()
    conn.close()
    return render_template('farmer_discussion.html', username=session['user_name'], messages=messages)

@main_bp.route('/about')
def about():
    return render_template("about.html")

# New route for plotting
@main_bp.route('/plot/soil')
def plotS():
    
    dataReq = "SoilMoist_S_tavg"
    # Map data type to a friendly name
    data_types = {
        "SoilMoist_S_tavg": "Soil Moisture",
        "AvgSurfT_tavg": "Average Surface Temperature",
        "Qs_tavg": "Surface Runoff",
    }

    name = data_types.get(dataReq, "Data")

    # Open the NC4 file
    nc_file = 'GLDAS_CLSM025_DA1_D.A20240529.022.nc4'
    try:
        dataset = Dataset(nc_file, 'r')
    except FileNotFoundError:
        return "Data file not found!", 500

    # Access data
    data = dataset.variables[dataReq][:][0]

    lat = dataset.variables['lat'][:]
    lon = dataset.variables['lon'][:]

    # Downsample the data for performance
    lat = lat[::2]
    lon = lon[::2]
    data = data[::2, ::2]

    # Create lat-lon grid
    lon_grid, lat_grid = np.meshgrid(lon, lat)

    # Flatten arrays
    data = data.flatten()
    lat = lat_grid.flatten()
    lon = lon_grid.flatten()

    datafig = pd.DataFrame({
        'Latitude': lat,
        'Longitude': lon,
        name: data
    })

    # Filter out NaN values
    datafig = datafig.dropna()

    # Create the map
    fig = px.scatter_mapbox(
        datafig,
        lat='Latitude',
        lon='Longitude',
        color=name,
        color_continuous_scale=px.colors.sequential.Viridis,
        mapbox_style='carto-positron',
        zoom=3,
        title=f"{name} Map",
        hover_name=name,
        hover_data=['Latitude', 'Longitude'],
        size_max=50
    )

    plot_html = fig.to_html(full_html=False)

    return plot_html


@main_bp.route('/plot/temp')
def plot():
    
    dataReq = "AvgSurfT_tavg"
    # Map data type to a friendly name
    data_types = {
        "SoilMoist_S_tavg": "Soil Moisture",
        "AvgSurfT_tavg": "Average Surface Temperature",
        "Qs_tavg": "Surface Runoff",
    }

    name = data_types.get(dataReq, "Data")

    # Open the NC4 file
    nc_file = 'GLDAS_CLSM025_DA1_D.A20240529.022.nc4'
    try:
        dataset = Dataset(nc_file, 'r')
    except FileNotFoundError:
        return "Data file not found!", 500

    # Access data
    data = dataset.variables[dataReq][:][0]

    lat = dataset.variables['lat'][:]
    lon = dataset.variables['lon'][:]

    # Downsample the data for performance
    lat = lat[::2]
    lon = lon[::2]
    data = data[::2, ::2]

    # Create lat-lon grid
    lon_grid, lat_grid = np.meshgrid(lon, lat)

    # Flatten arrays
    data = data.flatten()
    lat = lat_grid.flatten()
    lon = lon_grid.flatten()

    datafig = pd.DataFrame({
        'Latitude': lat,
        'Longitude': lon,
        name: data
    })

    # Filter out NaN values
    datafig = datafig.dropna()

    # Create the map
    fig = px.scatter_mapbox(
        datafig,
        lat='Latitude',
        lon='Longitude',
        color=name,
        color_continuous_scale=px.colors.sequential.Viridis,
        mapbox_style='carto-positron',
        zoom=3,
        title=f"{name} Map",
        hover_name=name,
        hover_data=['Latitude', 'Longitude'],
        size_max=50
    )

    plot_html = fig.to_html(full_html=False)

    return plot_html


@main_bp.route('/plot/sr')
def plotSr():
    
    dataReq = "Qs_tavg"
    # Map data type to a friendly name
    data_types = {
        "SoilMoist_S_tavg": "Soil Moisture",
        "AvgSurfT_tavg": "Average Surface Temperature",
        "Qs_tavg": "Surface Runoff",
    }

    name = data_types.get(dataReq, "Data")

    # Open the NC4 file
    nc_file = 'GLDAS_CLSM025_DA1_D.A20240529.022.nc4'
    try:
        dataset = Dataset(nc_file, 'r')
    except FileNotFoundError:
        return "Data file not found!", 500

    # Access data
    data = dataset.variables[dataReq][:][0]

    lat = dataset.variables['lat'][:]
    lon = dataset.variables['lon'][:]

    # Downsample the data for performance
    lat = lat[::2]
    lon = lon[::2]
    data = data[::2, ::2]

    # Create lat-lon grid
    lon_grid, lat_grid = np.meshgrid(lon, lat)

    # Flatten arrays
    data = data.flatten()
    lat = lat_grid.flatten()
    lon = lon_grid.flatten()

    datafig = pd.DataFrame({
        'Latitude': lat,
        'Longitude': lon,
        name: data
    })

    # Filter out NaN values
    datafig = datafig.dropna()

    # Create the map
    fig = px.scatter_mapbox(
        datafig,
        lat='Latitude',
        lon='Longitude',
        color=name,
        color_continuous_scale=px.colors.sequential.Viridis,
        mapbox_style='carto-positron',
        zoom=3,
        title=f"{name} Map",
        hover_name=name,
        hover_data=['Latitude', 'Longitude'],
        size_max=50
    )

    plot_html = fig.to_html(full_html=False)

    return plot_html