# Import necessary libraries
import copernicusmarine
import json
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
import os
import openmeteo_requests
import requests_cache
from retry_requests import retry
from math import ceil


def fetch_atmospheric_temperature(longitude, latitude, date):
    """
        Fetches the mean daily atmospheric temperature for a given location and date.
        This uses the Open-Meteo API to fetch the data from an ERA5 reanalysis model.

        Parameters:
        - longitude (float): The longitude of the location.
        - latitude (float): The latitude of the location.
        - date (str): The date for which to fetch the temperature in GMT+0, in YYYY-MM-DD format.

        Returns:
        - numpy.ndarray: An array containing the mean daily atmospheric temperature.
        """
    # Define the Open-Meteo API endpoint and parameters for the request. Defaults to GMT+0
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date,
        "end_date": date,
        "daily": "temperature_2m_mean"
    }

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.openmeteo_sidrift_cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make the request to the Open-Meteo API
    responses = openmeteo.weather_api(url, params=params)

    # Extract the response for the given location and date
    response = responses[0]

    # Retrieve the daily mean atmospheric temperature
    daily = response.Daily()
    daily_temperature_2m_mean = daily.Variables(0).ValuesAsNumpy()

    return daily_temperature_2m_mean


def make_request(feature):
    """
    Processes a single feature from the input data to fetch sea-ice data and atmospheric temperature.

    Parameters:
    - feature (dict): A dictionary containing the longitude, latitude, and date for the request.

    Returns:
    - pandas.DataFrame: A DataFrame containing the fetched sea-ice data and atmospheric temperature.
    """
    # Extract longitude, latitude, and date from the feature
    longitude = feature['properties']['lon']
    latitude = feature['properties']['lat']
    date = feature['properties']['date']

    # Fetch sea-ice data using the Copernicus Marine service
    request_dataframe = copernicusmarine.read_dataframe(
        dataset_id="cmems_mod_arc_phy_anfc_6km_detided_P1D-m",
        minimum_longitude=longitude,
        maximum_longitude=longitude,
        minimum_latitude=latitude,
        maximum_latitude=latitude,
        maximum_depth=0,
        variables=["age_of_sea_ice", "surface_snow_thickness", "sea_ice_thickness", "sea_water_salinity",
                   "sea_water_potential_temperature"],
        start_datetime=date,
        end_datetime=date
    )

    # Flatten multi index and add atmospheric temperature
    record = pd.DataFrame(request_dataframe.to_records())
    record['atmospheric_temperature'] = fetch_atmospheric_temperature(longitude, latitude, date)

    return record

def load_or_fetch_data(json_path, data_csv_path):
    """
    Loads data from a JSON file and fetches associated environmental metadata.
    Checks for previously fetched data stored at data_csv_path to avoid duplicate work.

    Parameters:
    - json_path (string): A string describing a path to a JSON file containing the drift data.
    - data_csv_path (string): A string describing a path to the CSV file where metadata is cached.

    Returns:
    - pandas.DataFrame: A DataFrame containing the compiled data from all processed features.
    """
    # Load data from the specified JSON file
    with open(json_path, 'r') as file:
        data = json.load(file)

    # Initialize variables to store results
    results = []
    final_df = None

    # Check if the results file already exists and load it if so
    if os.path.exists(data_csv_path):
        final_df = pd.read_csv(data_csv_path)

        # If the DataFrame has the same number of rows as the data, return it
        if final_df.shape[0] == len(data['features']):
            return final_df

        # Otherwise, only process remaining features
        else:
            data['features'] = data['features'][final_df.shape[0]:]

    # Process each feature to fetch data and append to results
    for feature in data['features']:
        df = make_request(feature)
        results.append(df)

    # Concatenate all fetched data into a single DataFrame and save to CSV
    final_df = pd.concat(results, ignore_index=True) if final_df is None else pd.concat([final_df] + results, ignore_index=True)
    final_df.to_csv(data_csv_path, index=False)

    return final_df


def plot_drift_track(results_df, variables_to_plot, names, cmaps, legend_labels, save_path):
    """
    Plots the drift track of sea ice using given variables.
    Generates a multi-panel plot for visualizing different data aspects.

    Parameters:
    - results_df (pandas.DataFrame): The DataFrame containing the data to be plotted.
    - variables_to_plot (list of str): Column names from the DataFrame to plot.
    - names (list of str): Readable names for each variable, used in plot titles.
    - cmaps (list of str): Colormaps for each variable plot.
    - legend_labels (list of str): Labels for the colorbars of each plot.
    - save_path (str): The path to save the plot to.
    """
    # Determine the number of subplots needed
    n_rows = ceil(len(variables_to_plot)/3)
    n_cols = ceil(len(variables_to_plot)/n_rows)

    # Setup the figure layout
    fig, axs = plt.subplots(n_rows, n_cols, figsize=(10 * n_cols, 10 * n_rows),
                            subplot_kw={'projection': ccrs.NorthPolarStereo()})
    axs = axs.flatten()

    # Plot each variable on its own subplot
    for i, variable_to_plot in enumerate(variables_to_plot):
        ax = axs[i]
        ax.set_extent([-110, 130, 70, 180], crs=ccrs.PlateCarree())

        # Add map features
        ax.add_feature(cartopy.feature.LAND, edgecolor='black')
        ax.add_feature(cartopy.feature.OCEAN)
        ax.add_feature(cartopy.feature.COASTLINE)
        ax.add_feature(cartopy.feature.RIVERS)

        # Plot data
        scatter = ax.scatter(results_df['longitude'], results_df['latitude'], c=results_df[variable_to_plot],
                             cmap=cmaps[i], transform=ccrs.PlateCarree(), marker='o')

        # Annotate some points with the date
        for j, row in results_df.iterrows():
            if j % 100 == 0 or j == results_df.shape[0] - 1:
                ax.annotate(row['time'].split(" ")[0],  # Text to display
                            xy=(row['longitude'], row['latitude']),  # Point to annotate
                            xytext=(-40, 20),  # Position of text relative to the point
                            textcoords='offset points',  # Interpret xytext as offset in points
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3"),  # Style of the arrow
                            transform=ccrs.PlateCarree(),  # Coordinate system for the point
                            ha='right', va='bottom')  # Alignment of the text

        # Add a colorbar
        plt.colorbar(scatter, ax=ax, shrink=0.5, label=legend_labels[i])

        # Add grid lines and labels
        gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, linewidth=1, color='gray',
                          alpha=0.75)
        gl.top_labels = gl.right_labels = False  # Disable labels where not needed

        # Some ocean and sea labels
        sea_labels = {
            'Barents Sea': (40, 75),
            'Greenland Sea': (-5, 78),
            'Laptev Sea': (125, 75),
        }

        for sea, coordinates in sea_labels.items():
            ax.text(coordinates[0], coordinates[1], sea,
                    transform=ccrs.PlateCarree(),
                    horizontalalignment='center', verticalalignment='center',
                    color='blue', fontsize=8, weight='normal')

        # Title for each subplot
        ax.set_title(f'{names[i]} along floe drift path')

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Save the figure
    plt.savefig(save_path, format="pdf")


def generate_drift_track_plot(json_input, data_cache_path, save_path):
    """
    Generates a plot of the drift track of sea ice using data from the specified JSON file. Save the plot as a PDF.

    Parameters:
    - json_input (str): The JSON output from backtrack.
    - data_cache_path (str): A path to cache the network requests.
    - save_path (str): The path to save the PDF of the plot to.
    """
    data = load_or_fetch_data(json_input, data_cache_path)
    plot_drift_track(data, variables_to_plot=["sithick", "siage", "sisnthick", "so", "thetao", "atmospheric_temperature"],
                     names=["Sea-ice thickness", "Age of sea ice", "Sea-ice snow thickness", "Sea water salinity", "Sea water potential temperature", "Atmospheric temperature"],
                     cmaps=["Blues", "Blues", "Greys", "viridis", "coolwarm", "coolwarm"],
                     legend_labels=["Thickness (m)", "Age (days)", "Thickness (m)", "Salinity (PSU)", "Potential temperature (°C)", "Temperature (°C)"],
                     save_path=save_path)
