import csv
import pandas as pd
from Series import Series  # Assuming Series class is defined in 'Series' module
import os

# Function to save a series instance to a CSV file
def save_series(file, series_instance):
    with open(file, 'a', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(series_instance.to_row())

# Function to read series data from a CSV file and populate a list
def read_series(file, list_of_series):
    try:
        # Clear the set of used IDs to avoid conflicts
        Series.used_ids = set()

        # Read CSV file into a pandas DataFrame
        df = pd.read_csv(file)

        # Clear the existing list of series
        list_of_series.clear()

        # Convert DataFrame to a list of lists and create Series instances
        data = df.values.tolist()
        for series_data in data:
            series_instance = Series(series_data[0], series_data[1], series_data[2], series_data[3], series_data[4], series_data[5], series_data[6])
            list_of_series.append(series_instance)
            print(f"Added Series: {series_instance}")

    except pd.errors.EmptyDataError:
        print("The CSV file is empty.")
