import PySimpleGUI as sg
from Series import *
from SerializeFile import *
import re
import operator
import os

# File path for storing series data
f_series = 'series.csv'
# List to store series objects
l_series = []
# Regular expressions for patterns
pattern_season = r"\d+"
pattern_date_creation = r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4}$"
pattern_id = r"\d{1,3}"

# Function to save the series list to a CSV file
def save_series_list(file, series_list):
    with open(file, 'w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(Series.headings)

        for series in series_list:
            if not series.erased:
                csv_writer.writerow(series.to_row())

# Function to move and clear a file
def clean_and_move_file(original_file, new_file):
    os.rename(original_file, new_file)
    try:
        os.remove(original_file)
    except OSError as e:
        print(f"Failed to remove the old file: {e}")
    os.rename(new_file, original_file)

# Function to add a new series to the list and update the interface
def add_series(series_list, interface_list, series_data, window):
    try:
        # Extract series data from the input dictionary
        ID = series_data['-ID-']
        name = series_data['-Name-']
        datecreation = series_data['-DateCreation-']
        season = series_data['-Season-']
        director = series_data['-Director-']
        posFile = series_data['-PosFile-']
        erased = 0  # Default value for erased

        if not re.match(pattern_id, ID):
            raise ValueError("Invalid ID format. It must be a positive integer with at most 3 digits.")

        if not name:
            raise ValueError("Name cannot be empty.")

        if not re.match(pattern_date_creation, datecreation):
            raise ValueError("Invalid date creation format. It must be in DD/MM/YYYY format.")

        if not re.match(pattern_season, season):
            raise ValueError("Invalid season format. It must be a non-negative integer.")

        # Check if the ID is already in the list
        if any(existing_series.ID == ID for existing_series in series_list):
            raise ValueError("ID must be unique. This ID is already in use.")

        # Create a new series object and add it to the list
        series = Series(ID, name, datecreation, season, director, posFile, erased)
        series_list.append(series)

        # Update the CSV file with the new series
        save_series(f_series, series)
        # Update the interface list and table
        interface_list.append([series.ID, series.name, series.datecreation, series.season, series.director, series.posFile, series.erased])
        window['-table-'].update(values=interface_list)
    except ValueError as e:
        sg.popup_error(f'Error adding the series: {e}')

# Function to update the interface with the current series list
def update_interface(window, l_series):
    interface_list = []
    for o in l_series:
        if not o.erased:
            interface_list.append([o.ID, o.name, o.datecreation, o.season, o.director, o.posFile])

    window['-table-'].update(values=interface_list)

# Function to delete a series from the list and update the interface
def delete_series(l_series, f_series, selected_row_index, table_data, window):
    if 0 <= selected_row_index < len(l_series):
        pos_in_file = l_series[selected_row_index].posFile

        if pos_in_file is not None and pos_in_file != 0:
            series_to_delete = find_series_by_pos(l_series, pos_in_file)

            if series_to_delete is not None:
                series_to_delete.erased = -1
                modify_series(f_series, series_to_delete)

                l_series.remove(series_to_delete)  # Remove directly from the list

                # Update the table and interface
                table_data = update_table_data(l_series)
                window['-table-'].update(values=table_data)
                update_interface(window, l_series)

# Function to update series data in the list based on position in the file
def update_customer(l_series, t_row_customer_interface, pos_in_file):
    try:
        pos_in_file = int(pos_in_file)
        selected_series = None
        for o in l_series:
            if o.series_in_pos(pos_in_file):
                selected_series = o
                break

        if selected_series is not None:
            # Update the selected series with new values
            selected_series.set_series(
                t_row_customer_interface[0], t_row_customer_interface[1],
                t_row_customer_interface[2], t_row_customer_interface[3],
                t_row_customer_interface[4], t_row_customer_interface[5],
                t_row_customer_interface[6]
            )
            modify_series(f_series, selected_series)
    except ValueError:
        sg.popup_error('Select a valid row to update.')

# Function to update the table data based on the series list
def update_table_data(l_series):
    total_rows = len(l_series)
    table_data = []

    for i, o in enumerate(l_series):
        if not o.erased:
            color = get_color(i, total_rows)
            table_data.append([o.ID, o.name, o.datecreation, o.season, o.director, o.posFile, color])

    return table_data

# Function to purge deleted series from the list and update the interface
def purge_deleted_series(l_series, f_series, interface_list, window):
    erased_list = list(filter(lambda c: c.erased, l_series))

    for c in erased_list:
        pos_in_file = c.posFile
        if pos_in_file is not None and pos_in_file != 0:
            c_del = find_series_by_pos(l_series, pos_in_file)
            if c_del is not None:
                l_series.remove(c_del)  # Remove directly from the list

    try:
        # Filter rows that do not have erased set to -1
        filtered_rows = [c.to_row() for c in l_series if not c.erased]

        # Overwrite the CSV file with the filtered rows
        with open(f_series, 'w', newline='', encoding='utf-8') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(Series.headings)
            csv_writer.writerows(filtered_rows)

        # Clear the list of deleted series
        l_series = [c for c in l_series if not c.erased]
    except Exception as e:
        sg.popup_error(f'Error writing to the CSV file: {e}')

    # Update the interface and table after deleting rows
    table_data = update_table_data(l_series)
    window['-table-'].update(values=table_data)
    update_interface(window, l_series)

# Function to find a series in the list based on position in the file
def find_series_by_pos(series_list, pos):
    for series in series_list:
        if series.series_in_pos(pos):
            return series
    return None

# Function to modify a series in the file
def modify_series(file, series):
    temp_file = file + '.temp'
    with open(file, 'r', newline='', encoding='utf-8') as f, open(temp_file, 'w', newline='', encoding='utf-8') as temp:
        reader = csv.reader(f)
        writer = csv.writer(temp)

        for row in reader:
            if row and row[0].isdigit():
                if row[5] == str(series.posFile):
                    writer.writerow(series.to_row())
                else:
                    writer.writerow(row)

    os.remove(file)
    os.rename(temp_file, file)

# Function to find a series in the list based on ID
def find_series_by_id(series_list, series_id):
    for series in series_list:
        if series.ID == series_id:
            return series
    return None

# Function to move and clear a file
def move_and_clear_file(file):
    new_file = 'newseries.csv'
    os.rename(file, new_file)

    if os.path.exists(file):  # Check if the original file still exists
        try:
            os.remove(file)
        except OSError as e:
            print(f"Failed to remove the old file: {e}")
    os.rename(new_file, file)

# Custom sorting function for sorting series based on date_creation
def custom_sort(row):
    date_creation_index = Series.headings.index('-DateCreation-')
    date_creation = datetime.strptime(row[date_creation_index], '%d/%m/%Y')
    return date_creation

# Function to sort the series file based on specified columns
def sort_series(file_path, columns):
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)
        data = [row for row in reader]

    # Create a custom sorting function
    def custom_sort(row):
        return tuple(int(row[header.index(column)]) if column == 'ID' else row[header.index(column)] for column in columns)

    # Apply the sorting
    data = sorted(data, key=custom_sort)

    # Save the sorted data to a new file
    new_file_path = 'newseries.csv'
    with open(new_file_path, 'w', newline='', encoding='utf-8') as new_file:
        writer = csv.writer(new_file)
        writer.writerow(header)
        writer.writerows(data)

    # Remove the original file and rename the new file
    os.remove(file_path)
    os.rename(new_file_path, file_path)

# Function to update a series in the list with new data
def update_series(series_list, row_to_update, posinfile):
    try:
        # Get the ID of the series to update
        series_id = int(row_to_update[0])

        # Find the series in the list by ID
        series = find_series_by_id(series_list, series_id)

        if series:
            # Update the series values with the new values from the interface
            series.name = row_to_update[1]
            series.datecreation = row_to_update[2]
            series.season = row_to_update[3]
            series.director = row_to_update[4]
            series.posFile = posinfile

    except ValueError:
        print("Error updating the series: Invalid ID.")

# Function to handle the modify event for updating a series
def handle_modify_event(event, values, series_list, table_data, window):
    # Input validation
    valid = False
    if re.match(pattern_id, values['-ID-']):
        # Add more validation conditions as needed
        valid = True

    if valid:
        row_to_update = None
        for t in table_data:
            if str(t[0]) == values['-ID-']:
                row_to_update = t
                # Update series data with new values
                t[1], t[2], t[3], t[4], t[5] = values['-Name-'], values['-DateCreation-'], values['-Season-'], values['-Director-'], values['-PosFile-']
                posinfile = values['-PosFile-']
                break

        if row_to_update is None:
            print("Error: No series found with the provided ID in the event.")
            return

        # Update the series list
        update_series(series_list, row_to_update, posinfile)

        # Update the CSV file with the changes
        modify_series(f_series, find_series_by_id(series_list, int(values['-ID-'])))

        # Update the table interface
        window['-table-'].update(table_data)
        window['-ID-'].update(disabled=False)

# Function to display a window for sorting the series file
def sort_series_window():
    sg.theme('DarkGrey5')

    layout = [
        [sg.Text('Select columns to sort by:', font=('Arial', 14), text_color='white')],
        [sg.Checkbox(column, key=f'-{column}-', font=('Arial', 12), text_color='white', background_color='black') for column in Series.headings[:-1]],
        [sg.Button('Sort', button_color=('black', 'red')), sg.Button('Cancel', button_color=('black', 'red'))]
    ]

    window = sg.Window('Sort File', layout, finalize=True, background_color='black')

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Cancel':
            break

        if event == 'Sort':
            selected_columns = [column for column in Series.headings[:-1] if values[f'-{column}-']]
            if selected_columns:
                sort_series(f_series, selected_columns)
                read_series(f_series, l_series)  # Reload the list after sorting
                window.close()
                break

    window.close()

# Function to get color based on row index and total rows
def get_color(i, total_rows):
    r = int(255 - i / total_rows * 255)
    return f'#{r:02X}0000'

# Main interface function
def interface():
    # Define color variables
    background_color = '#000000'  # Black
    input_background_color = '#FF0000'  # Red
    text_color = '#000000'  # Black

    # Set the theme colors for the GUI
    sg.theme_input_background_color(color=input_background_color)
    sg.theme_text_element_background_color(color=input_background_color)
    sg.theme_background_color(background_color)

    # Set font options
    font1, font2 = ('Arial', 14), ('Arial', 16)
    sg.set_options(font=font1)

    # Initialize table data
    table_data = []
    row_to_update = []
    read_series(f_series, l_series)
    total_rows = len(l_series)

    # Populate table data with series information, excluding those with erased set to -1
    for i, o in enumerate(l_series):
        if o.erased != -1:
            color = get_color(i, total_rows)
            table_data.append([o.ID, o.name, o.datecreation, o.season, o.director, o.posFile, color])

    # Define the layout of the GUI
    layout = [
        [sg.Column(
            [[sg.Text(text, background_color=get_color(0, 1), text_color='black'),
              sg.Input(key=key, text_color='black')] for key, text in
             Series.fields.items()],
            justification='right', background_color=get_color(0, 1)),
         sg.Table(values=table_data, headings=Series.headings[:-1], max_col_width=50, num_rows=10,
                  display_row_numbers=False, justification='center', enable_events=True,
                  enable_click_events=True,
                  vertical_scroll_only=False, select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                  expand_x=True, bind_return_key=True, key='-table-')],
        [sg.Push(background_color)] +
        [sg.Button(button, button_color=('black', 'red')) for button in ('Purge','Add', 'Delete', 'Modify', 'Clear', 'Clean Cells','Sort File')] +
        [sg.Push(background_color)],
    ]

    # Set the GUI theme and create the window
    sg.theme('DarkGreen3')
    window = sg.Window('Series Management with Files', layout, finalize=True,
                       background_color=get_color(0, 1))
    window['-table-'].bind("<Double-Button-1>", " Double")

    # Event loop for handling user interactions
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        # Handle various button events
        if event == 'Add':
            add_series(l_series, table_data, values, window)
        elif event == 'Delete':
            delete_series(l_series, f_series, values['-table-'][0], table_data, window)
        elif event == 'Modify':
            handle_modify_event(event, values, l_series, table_data, window)
        elif event == 'Clear':
            move_and_clear_file(f_series)
            read_series(f_series, l_series)
            window['-table-'].update(values=update_table_data(l_series))
            window['-ID-'].update('')
            window['-Name-'].update('')
            window['-DateCreation-'].update('')
            window['-Season-'].update('')
            window['-Director-'].update('')
            window['-PosFile-'].update('')
        elif event == 'Clean Cells':
            # Clear input cells in the interface
            window['-ID-'].update('')
            window['-Name-'].update('')
            window['-DateCreation-'].update('')
            window['-Season-'].update('')
            window['-Director-'].update('')
            window['-PosFile-'].update('')
        elif event == 'Purge':
            purge_deleted_series(l_series, f_series, table_data, window)
        elif event == 'Sort File':
            sort_series_window()
            read_series(f_series, l_series)
            update_interface(window, l_series)
        elif event == '-table-':
            # Handle double-click event on the table to display selected data in the input cells
            if values[event] and len(values[event]) > 0:
                selected_row_index = values[event][0]
                selected_series = l_series[selected_row_index]
                # Update the input cells with the selected series data
                window['-ID-'].update(selected_series.ID)
                window['-Name-'].update(selected_series.name)
                window['-DateCreation-'].update(selected_series.datecreation)
                window['-Season-'].update(selected_series.season)
                window['-Director-'].update(selected_series.director)
                window['-PosFile-'].update(selected_series.posFile)

    # Close the window when the event loop exits
    window.close()

# Call the interface function to run the GUI
interface()
