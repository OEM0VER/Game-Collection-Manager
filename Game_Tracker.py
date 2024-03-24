import tkinter as tk
from tkinter import messagebox, filedialog
import configparser
from PIL import Image, ImageTk, ImageDraw
import requests
from io import BytesIO
import webbrowser
import shutil
import os
import os.path
import tkinter.simpledialog
import tkinter.simpledialog as simpledialog
from tkinter import simpledialog
import validators
import threading
import csv
import atexit
import urllib.request

misc_info = ""  # Define misc_info as a global variable

MAX_RETRIES = 5
BASE_DELAY = 3  # Initial delay in seconds

def fetch_image(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    request = urllib.request.Request(url, headers=headers)
    retries = 0
    
    while retries < MAX_RETRIES:
        try:
            with urllib.request.urlopen(request) as response:
                return response.read()
        except Exception as e:
            print(f"Error fetching image: {e}")
            retries += 1
            if retries < MAX_RETRIES:
                print(f"Retrying in {BASE_DELAY} seconds...")
                time.sleep(BASE_DELAY)
    
    print("Max retries reached. Unable to fetch image.")
    return None

# Function to create the INI file if it doesn't exist
def create_ini_if_not_exists():
    config_file = "game_tracker.ini"
    config = configparser.ConfigParser()

    if os.path.exists(config_file):
        # Read the existing configuration
        config.read(config_file)

        # Add missing sections if they don't exist
        if 'Games' not in config:
            config['Games'] = {}
        if 'Hidden' not in config:
            config['Hidden'] = {}
        if 'StatsToBuy' not in config:
            config['StatsToBuy'] = {}
        if 'StatsToComplete' not in config:
            config['StatsToComplete'] = {}
        if 'Currency' not in config:
            config['Currency'] = {'currency': 'GBP'}  # Default currency to GBP
    else:
        # Create a new ConfigParser object and add sections
        config['Games'] = {}
        config['Hidden'] = {}
        config['StatsToBuy'] = {}
        config['StatsToComplete'] = {}
        config['Currency'] = {'currency': 'GBP'}  # Default currency to GBP

    # Save the configuration to the INI file
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def populate_listbox(listbox, games):
    # Clear the listbox
    listbox.delete(0, tk.END)
    # Sort the games alphabetically
    games.sort()
    # Populate the listbox with sorted games
    for game in games:
        listbox.insert(tk.END, game)

def remove_empty_equal_sign(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            lines = file.readlines()
        
        with open(filename, 'w') as file:
            for line in lines:
                # Remove any leading commas from the line
                line = line.lstrip(',')
                # Remove any leading or trailing whitespace
                line = line.strip()
                if line != '=':
                    file.write(line + '\n')  # Add newline after writing each line

# Define function remove_from_buy first
def remove_from_buy():
    global buy_games, stats_to_buy_dict

    # Print the contents of global variables
    print("Global Variables:")
    print("buy_games:", buy_games)
    print("to_complete_games:", to_complete_games)
    print("completed_games:", completed_games)
    print("misc_info:", misc_info)
    print("additional_info_dict:", additional_info_dict)
    print("stats_to_buy_dict:", stats_to_buy_dict)
    print("stats_to_complete_dict:", stats_to_complete_dict)

    # Get the selected game from the listbox
    selected_game_index = listbox.curselection()
    if selected_game_index:
        selected_game = listbox.get(selected_game_index).strip().split(" - ")[0]  # Extract only the game name
        
        # Ask for confirmation
        confirmation = messagebox.askyesno("Confirmation", f"Are you sure you want to remove '{selected_game}' from the 'To Buy' list?")
        
        if confirmation:
            # Remove from GUI
            listbox.delete(selected_game_index)
            
            # Remove from buy_games list
            buy_games.remove(selected_game)
            
            # Remove from stats_to_buy_dict
            if selected_game in stats_to_buy_dict:
                del stats_to_buy_dict[selected_game]

            # Remove the game from the [Games] section
            existing_config = configparser.ConfigParser()
            existing_config.read('game_tracker.ini', encoding='utf-8')
            existing_games = existing_config['Games'].get('Buy', '').split(',')
            existing_games = [game.strip().split(" - ")[0] for game in existing_games if game.strip().split(" - ")[0] != selected_game]
            existing_config['Games']['Buy'] = ','.join(existing_games)

            # Remove the corresponding entry from the [StatsToBuy] section
            if 'StatsToBuy' in existing_config:
                existing_config.remove_option('StatsToBuy', selected_game)

            # Save the updated configuration
            with open('game_tracker.ini', 'w', encoding='utf-8') as configfile:
                existing_config.write(configfile)
        else:
            return
    else:
        print("No game selected.")

# Function to check if a string contains any invalid characters
def contains_invalid_characters(text):
    invalid_characters = {'"', 'é', ',', "'", ':', '$', '€', '£', '¥'}
    return any(char in invalid_characters for char in text)

def add_to_buy():
    # Clear the stats_to_buy_dict before importing games
    stats_to_buy_dict.clear()

    # Remove empty equal sign lines from the INI file
    remove_empty_equal_sign('game_tracker.ini')

    game_name = buy_game_entry.get().strip()
    if game_name:
        # Check if the game name contains any invalid characters
        if contains_invalid_characters(game_name):
            messagebox.showwarning("Invalid Characters", "Game name cannot contain characters like 'é', ',', ''', ':', '$', '€', '£', or '¥'")
            return
        
        # Check if the game name already exists in the INI file
        try:
            config = configparser.ConfigParser()
            config.read('game_tracker.ini')
            
            if 'Games' in config:
                games_section = config['Games']
                existing_games = [name.strip() for name in games_section.get('buy', '').split(',')]
                if game_name.lower() in [name.lower() for name in existing_games]:
                    messagebox.showwarning("Duplicate Game", f"The game '{game_name}' already exists.")
                    return
        except Exception as e:
            print("An error occurred while reading the INI file:", e)
            messagebox.showerror("Error", "Failed to read the configuration file.")
            return
        
        # Prompt for platform
        platform = simpledialog.askstring("Platform", f"Enter platform for '{game_name}':")
        if platform is None:  # Check if the user canceled the platform input
            return  # Exit the function if platform input is canceled
        if contains_invalid_characters(platform):
            messagebox.showwarning("Invalid Characters", "Platform cannot contain characters like 'é', ',', ''', ':', '$', '€', '£', or '¥'")
            return
        if contains_currency_symbols(platform):
            messagebox.showwarning("Invalid Characters", "Platform cannot contain characters like 'é', ',', ''', ':', '$', '€', '£', or '¥'")
            return
        
        # Create a Toplevel window for the price input
        price_dialog = tk.Toplevel()
        price_dialog.title(f"Enter price for '{game_name}'")
        price_dialog.geometry("180x80")
        
        # Make the price dialog stay on top of all other windows
        price_dialog.lift()
        price_dialog.grab_set()
        
        # Function to center the price dialog on the screen
        def center_window(window):
            window.update_idletasks()
            width = window.winfo_width()
            height = window.winfo_height()
            x = (window.winfo_screenwidth() // 2) - (width // 2)
            y = (window.winfo_screenheight() // 2) - (height // 2)
            window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Center the price dialog on the screen
        center_window(price_dialog)
        
        # Prompt for price
        price_label = tk.Label(price_dialog, text="Enter price:")
        price_label.pack()
        price_entry = tk.Entry(price_dialog)
        price_entry.pack()
        
        def submit_price():
            price = price_entry.get()
            if price:
                if contains_currency_symbols(price):
                    messagebox.showwarning("Invalid Characters", "Price cannot contain characters like 'é', ',', ''', ':', '$', '€', '£', or '¥'")
                    return
                
                price_dialog.destroy()  # Close the price dialog
                # Construct the display string with only the game name
                display_text = game_name
                
                # Insert the display string into the listbox
                listbox.insert(tk.END, display_text)
                
                # Append the non-empty game name to buy_games
                buy_games.append(game_name)
                
                # Store platform and price in stats_to_buy_dict
                stats_to_buy_dict[game_name] = (platform, price)
                
                # Save configuration after adding a game
                save_configuration()
                
                # Clean up the INI file to remove empty lines
                remove_empty_equal_sign('game_tracker.ini')
                
                # Debug print to check stats_to_buy_dict contents
                print("Stats to buy:", stats_to_buy_dict)

                # Debug print to check stats_to_buy_dict contents
                print("Stats to complete:", stats_to_complete_dict)
        
        submit_button = tk.Button(price_dialog, text="Submit", command=submit_price, cursor="hand2")
        submit_button.pack()
        
    # Clear the entry widget after adding the game
    buy_game_entry.delete(0, tk.END)


def reset_global_variables():
    global buy_games
    global to_complete_games
    global completed_games
    global misc_info
    global additional_info_dict
    global stats_to_buy_dict
    global stats_to_complete_dict

    # Reset all global variables and dictionaries
    buy_games = []
    to_complete_games = []
    completed_games = []
    misc_info = ""
    additional_info_dict = {}
    stats_to_complete_dict = {}

buy_games = []  # Initialize buy_games as an empty list

def mark_as_bought_new():
    global config, buy_games, to_complete_games

    # Get selected games from the listbox
    selected_indices = listbox.curselection()
    for index in selected_indices[::-1]:
        selected_game = listbox.get(index).strip()  # Get selected game

        # Prompt user to enter miscellaneous stats
        misc_stats = ask_misc_stats(selected_game)
        
        # Check if user entered miscellaneous stats
        if misc_stats is not None:  
            # Remove the game from the "Buy" section
            config = configparser.ConfigParser()
            config.read('game_tracker.ini')

            if 'Games' not in config:
                config['Games'] = {}

            if 'Buy' not in config['Games']:
                config['Games']['Buy'] = ''

            if 'ToComplete' not in config['Games']:
                config['Games']['ToComplete'] = ''

            games_to_buy = [game.strip() for game in config['Games']['Buy'].split(',') if game.strip()]
            if selected_game in games_to_buy:
                games_to_buy.remove(selected_game)
                config['Games']['Buy'] = ','.join(games_to_buy)

                # Update the buy_games variable
                buy_games = games_to_buy

            # Save the updated configuration
            with open('game_tracker.ini', 'w') as configfile:
                config.write(configfile)

            # Add the game to the "ToComplete" section
            games_to_complete = [game.strip() for game in config['Games']['ToComplete'].split(',') if game.strip()]
            if selected_game not in games_to_complete:
                games_to_complete.append(selected_game)
                config['Games']['ToComplete'] = ','.join(games_to_complete)

                # Update the to_complete_games variable
                to_complete_games = games_to_complete

                # Update the to_complete_listbox
                to_complete_listbox.insert(tk.END, selected_game)

            # If there are no existing stats for the game, create default stats
            if 'StatsToComplete' not in config:
                config['StatsToComplete'] = {}

            # Add the game to the StatsToComplete section with platform and misc stats
            config['StatsToComplete'][selected_game] = f"Platform=none, Misc={misc_stats}"

            # Save the updated configuration
            with open('game_tracker.ini', 'w') as configfile:
                config.write(configfile)

            # Update the listbox
            repopulate_listbox_from_ini()

def ask_misc_stats(game):
    # Prompt user to enter miscellaneous stats for the game
    misc_stats = simpledialog.askstring("Miscellaneous Stats", f"Enter miscellaneous stats for '{game}':")
    return misc_stats  # Return the entered misc stats or None if canceled

def repopulate_to_complete_listbox():
    global to_complete_listbox

    # Clear the existing items
    to_complete_listbox.delete(0, tk.END)

    # Read games from the INI file and populate the to-complete listbox
    config = configparser.ConfigParser()
    config.read('game_tracker.ini')
    if 'Games' in config and 'ToComplete' in config['Games']:
        to_complete_games = [game.strip() for game in config['Games']['ToComplete'].split(',') if game.strip()]
        for game in to_complete_games:
            to_complete_listbox.insert(tk.END, game)

def repopulate_listbox_from_ini():
    global listbox, to_complete_listbox

    # Load the configuration file
    config = configparser.ConfigParser()
    config.read('game_tracker.ini')

    # Clear the listboxes
    listbox.delete(0, tk.END)
    to_complete_listbox.delete(0, tk.END)

    # Repopulate the listbox with games from the "Buy" section
    if 'Games' in config and 'Buy' in config['Games']:
        buy_games = [game.strip() for game in config['Games']['Buy'].split(',') if game.strip()]
        for game in buy_games:
            listbox.insert(tk.END, game)

    # Repopulate the to_complete_listbox with games from the "ToComplete" section
    if 'Games' in config and 'ToComplete' in config['Games']:
        to_complete_games = [game.strip() for game in config['Games']['ToComplete'].split(',') if game.strip()]
        for game in to_complete_games:
            to_complete_listbox.insert(tk.END, game)

    # Load the config
    load_configuration_at_startup()   

def ask_misc_info(game_name):
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Ask for miscellaneous information
    misc_info = simpledialog.askstring("Miscellaneous Info", f"Enter miscellaneous information for {game_name}:")

    # Check if the user inputted anything
    if misc_info:
        return misc_info.strip()  # Remove leading and trailing whitespace
    else:
        return None

# Define config as a global variable
config = configparser.ConfigParser()

# Define global variables and dictionaries
additional_info_dict = {}
stats_to_complete_dict = {}

# Function to check if a string contains any currency symbols
def contains_currency_symbols(text):
    currency_symbols = {'"', 'é', ',', "'", ':', '$', '€', '£', '¥'}
    return any(char in currency_symbols for char in text)

def add_to_complete():
    global config

    # Remove empty equal sign lines from the INI file
    remove_empty_equal_sign('game_tracker.ini')

    game_name = to_complete_game_entry.get().strip()
    if game_name:
        # Check if the game name contains any invalid characters
        if contains_invalid_characters(game_name):
            messagebox.showwarning("Invalid Characters", "Game name cannot contain characters like 'é', ',', ''', ':', '$', '€', '£', or '¥'")
            return
        
        # Check if the game name already exists in the INI file
        try:
            config = configparser.ConfigParser()
            config.read('game_tracker.ini')
            
            if 'Games' in config:
                games_section = config['Games']
                existing_games = [name.strip() for name in games_section.get('tocomplete', '').split(',')]
                if game_name.lower() in [name.lower() for name in existing_games]:
                    messagebox.showwarning("Duplicate Game", f"The game '{game_name}' already exists.")
                    return
        except Exception as e:
            print("An error occurred while reading the INI file:", e)
            messagebox.showerror("Error", "Failed to read the configuration file.")
            return
        
        # Prompt for platform
        platform = tk.simpledialog.askstring("Platform", f"Enter platform for '{game_name}':")
        if platform is None:  # Check if the user canceled the input dialog
            return  # Exit the function if the user canceled
        if contains_invalid_characters(platform):
            messagebox.showwarning("Invalid Characters", "Platform cannot contain characters like 'é', ',', ''', ':', '$', '€', '£', or '¥'")
            return
        if contains_currency_symbols(platform):
            messagebox.showwarning("Invalid Characters", "Platform cannot contain characters like 'é', ',', ''', ':', '$', '€', '£', or '¥'")
            return

        # Define variables for window width and height
        window_width = 400
        window_height = 80

        # Create a Toplevel window for the miscellaneous data input dialog
        misc_dialog = tk.Toplevel()
        misc_dialog.title("Miscellaneous Data")
        misc_dialog.resizable(False, False)
        
        # Set the window on top of all other applications
        misc_dialog.lift()
        misc_dialog.attributes('-topmost', True)
        
        # Get the screen width and height
        screen_width = misc_dialog.winfo_screenwidth()
        screen_height = misc_dialog.winfo_screenheight()
        
        # Calculate the x and y coordinates to center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Set the window size and position
        misc_dialog.geometry("{}x{}+{}+{}".format(window_width, window_height, x, y))
        
        # Prompt for miscellaneous data
        misc_label = tk.Label(misc_dialog, text=f"Enter miscellaneous data for '{game_name}':")
        misc_label.pack()
        
        misc_data_entry = tk.Entry(misc_dialog)
        misc_data_entry.pack()
        
        # Function to handle button click
        def save_misc_data():
            global config  # Declare config as a global variable
            misc_data = misc_data_entry.get()
            if misc_data:
                # Check if the miscellaneous data contains any invalid characters
                if contains_invalid_characters(misc_data):
                    messagebox.showwarning("Invalid Characters", "Miscellaneous data cannot contain characters like 'é', ',', ''', ':', '$', '€', '£', or '¥'")
                    return

                # Clear the additional_info_dict and stats_to_complete_dict
                additional_info_dict.clear()
                stats_to_complete_dict.clear()

                # Add game name to the listbox and to_complete_games list
                to_complete_listbox.insert(tk.END, game_name)
                to_complete_games.append(game_name)
                
                # Load existing configuration
                config.read('game_tracker.ini', encoding='utf-8')
                
                # Save platform and misc data to [StatsToComplete] section
                if 'StatsToComplete' not in config:
                    config.add_section('StatsToComplete')
                config.set('StatsToComplete', game_name, f"Platform={platform}, Misc={misc_data}")
                
                # Update the [Games] section with the new game name
                if 'Games' not in config:
                    config['Games'] = {}
                if 'tocomplete' not in config['Games']:
                    config['Games']['tocomplete'] = ""
                if game_name not in config['Games']['tocomplete']:
                    config['Games']['tocomplete'] += f",{game_name}"
                
                # Save the updated configuration
                with open('game_tracker.ini', 'w', encoding='utf-8') as configfile:
                    config.write(configfile)

                # Save configuration after adding a game
                save_configuration()

                # Remove stats for games not in [Games] or [Hidden]
                #remove_stats_not_in_sections()
                save_configuration()
                
                # Clear the entry widget after adding
                to_complete_game_entry.delete(0, tk.END)
                
                # Close the miscellaneous data dialog
                misc_dialog.destroy()
        
        # Add button to save miscellaneous data
        save_button = tk.Button(misc_dialog, text="Save", command=save_misc_data, cursor="hand2")
        save_button.pack()

additional_info_dict = {}

def show_additional_info():
    # Check which listbox is currently selected
    if listbox.curselection():
        selected_widget = listbox
    elif to_complete_listbox.curselection():
        selected_widget = to_complete_listbox
    else:
        messagebox.showinfo("Additional Info", "Please select a game to view its additional info.")
        return

    selected_game_index = selected_widget.curselection()
    selected_game = selected_widget.get(selected_game_index)

    additional_info = config.get('Info', selected_game, fallback=None)
    if additional_info:
        dialog = tk.Toplevel(root)
        dialog.title("Additional Info")
        dialog.attributes("-topmost", True)  # Make the window stay on top

        # Calculate window position to center it on the screen
        window_height = 200
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Initialize window width
        window_width = 450

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        dialog.geometry(f"+{x}+{y}")

        # Make the additional info window resizable
        dialog.resizable(True, True)

        # Create a Canvas widget to hold the additional info labels
        canvas = tk.Canvas(dialog)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a Frame inside the Canvas to contain the labels
        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor=tk.NW)

        # Add scrollbar to the right side of the Canvas
        scrollbar = tk.Scrollbar(dialog, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.config(yscrollcommand=scrollbar.set)

        # Function to update the scroll region when the frame size changes
        def update_scroll_region(event):
            canvas.config(scrollregion=canvas.bbox("all"))

        frame.bind("<Configure>", update_scroll_region)

        max_label_width = max([len(info) for info in additional_info.split(',')])

        # Adjust window width based on label length
        window_width = 200 + max_label_width * 4

        dialog.geometry(f"{window_width}x{window_height}")

        for info in additional_info.split(','):
            # Check if the info is a URL or file path
            if validators.url(info):
                def open_url(url):
                    webbrowser.open(url)

                url_label = tk.Label(frame, text=info, fg="blue", cursor="hand2", wraplength=window_width - 20)
                url_label.pack(padx=10, pady=5)
                url_label.bind("<Button-1>", lambda event, url=info: open_url(url))
            else:
                def open_file(file_path):
                    os.startfile(file_path)

                file_label = tk.Label(frame, text=info, fg="green", cursor="hand2", wraplength=window_width - 20)
                file_label.pack(padx=10, pady=5)
                file_label.bind("<Button-1>", lambda event, file_path=info: open_file(file_path))

        # Bind mouse wheel events to the Canvas for scrolling
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * (event.delta // 120), "units"))

        # Function to unbind the mouse wheel event when the window is destroyed
        def on_close():
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)  # Bind the close event to the on_close function

    else:
        messagebox.showinfo("Additional Info", "No additional info available for this game.")


def show_completed_info():

    selected_index = completed_listbox.curselection()
    if selected_index:
        selected_game = completed_listbox.get(selected_index)
        
        # Read additional info directly from the INI file
        config = configparser.ConfigParser()
        config.read('game_tracker.ini', encoding='utf-8')
        additional_info = config.get('Info', selected_game, fallback=None)
        
        if additional_info:
            dialog = tk.Toplevel(root)
            dialog.title("Additional Info")
            dialog.attributes("-topmost", True)  # Make the window stay on top

            # Calculate window position to center it on the screen
            window_width = 450
            window_height = 200
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Make the additional info window resizable
            dialog.resizable(True, True)

            # Create a Canvas widget to hold the additional info labels
            canvas = tk.Canvas(dialog)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Create a Frame inside the Canvas to contain the labels
            frame = tk.Frame(canvas)
            canvas.create_window((0, 0), window=frame, anchor=tk.NW)

            # Add scrollbar to the right side of the Canvas
            scrollbar = tk.Scrollbar(dialog, command=canvas.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            canvas.config(yscrollcommand=scrollbar.set)

            # Function to update the scroll region when the frame size changes
            def update_scroll_region(event):
                canvas.config(scrollregion=canvas.bbox("all"))

            frame.bind("<Configure>", update_scroll_region)

            # Split the additional info into separate lines
            info_lines = additional_info.split('\n')
            for info in info_lines:
                # Check if the info is a URL
                if validators.url(info):
                    def open_url(url):
                        webbrowser.open(url)

                    url_label = tk.Label(frame, text=info, fg="blue", cursor="hand2")
                    url_label.pack(padx=10, pady=5)
                    url_label.bind("<Button-1>", lambda event, url=info: open_url(url))
                else:
                    def open_file(file_path):
                        os.startfile(file_path)

                    file_label = tk.Label(frame, text=info, fg="green", cursor="hand2")
                    file_label.pack(padx=10, pady=5)
                    file_label.bind("<Button-1>", lambda event, file_path=info: open_file(file_path))
        else:
            messagebox.showinfo("Additional Info", "No additional info available for this game.")

def remove_from_complete():
    global to_complete_games, additional_info_dict, stats_to_complete_dict

    # Get the selected game from the listbox
    selected_game_index = to_complete_listbox.curselection()
    if selected_game_index:
        selected_game = to_complete_listbox.get(selected_game_index).strip()  # Strip whitespace from selected_game
        
        # Ask for confirmation
        confirmation = messagebox.askyesno("Confirmation", f"Are you sure you want to remove '{selected_game}' from the 'To Complete' list?")
        
        if confirmation:
            # Remove from GUI
            to_complete_listbox.delete(selected_game_index)
            
            # Remove from to_complete_games list
            to_complete_games.remove(selected_game)

            # Load existing configuration to preserve other sections
            existing_config = configparser.ConfigParser()

            # Load existing INI file
            existing_config.read('game_tracker.ini', encoding='utf-8')

            # Remove the game from the [Games] section
            existing_games = existing_config['Games'].get('ToComplete', '').split(',')
            existing_games = [game.strip() for game in existing_games if game.strip() != selected_game]
            existing_config['Games']['ToComplete'] = ','.join(existing_games)

            # Remove the game's entry from the [Info] section
            if selected_game in additional_info_dict:
                del additional_info_dict[selected_game]
                if 'Info' in existing_config:
                    existing_config.remove_option('Info', selected_game)

            # Remove the game's entry from the [StatsToComplete] section
            if 'StatsToComplete' in existing_config and selected_game in existing_config['StatsToComplete']:
                existing_config.remove_option('StatsToComplete', selected_game)
                
            # Clear the stats_to_complete_dict
            if selected_game in stats_to_complete_dict:
                del stats_to_complete_dict[selected_game]

            # Save the updated configuration
            with open('game_tracker.ini', 'w', encoding='utf-8') as configfile:
                existing_config.write(configfile)

        else:
            return
    else:
        print("No game selected.")

def remove_from_completed(completed_listbox):
    global completed_games, additional_info_dict

    # Remove empty equal sign lines from the INI file
    remove_empty_equal_sign('game_tracker.ini')

    selected_indices = completed_listbox.curselection()
    for i in selected_indices[::-1]:
        selected_game = completed_listbox.get(i)
        if selected_game in completed_games:  # Check if the selected game exists in the list
            # Ask for confirmation before removing the game
            confirmation = messagebox.askyesno("Confirmation", f"Are you sure you want to remove '{selected_game}' from the completed games list?")
            if confirmation:
                completed_listbox.delete(i)
                completed_games.remove(selected_game)  # Remove the selected game from the completed_games list
                if selected_game.strip() != '':  # Check if the selected game is not an empty string
                    # Remove the game's stats from StatsToComplete section in the INI file
                    config = configparser.ConfigParser()
                    config.read('game_tracker.ini', encoding='utf-8')
                    if 'StatsToComplete' in config and selected_game in config['StatsToComplete']:
                        del config['StatsToComplete'][selected_game]

                    # Remove the game's info from the Info section in the INI file
                    if 'Info' in config and selected_game in config['Info']:
                        del config['Info'][selected_game]

                    with open('game_tracker.ini', 'w', encoding='utf-8') as configfile:
                        config.write(configfile)

                    # Remove the game's info from additional_info_dict
                    if selected_game in additional_info_dict:
                        del additional_info_dict[selected_game]

                    save_configuration()  # Save the configuration after removing the game
                    remove_empty_equal_sign('game_tracker.ini')  # Clean up the INI file
            else:
                # If the user cancels the action, stop the loop
                break

# Define global variables
default_backup_dir = ""
default_save_dir = ""

def load_default_directories():
    global default_backup_dir, default_save_dir
    config = configparser.ConfigParser()
    config.read('game_tracker.ini', encoding='utf-8')
    if 'Directories' in config:
        default_backup_dir = config['Directories'].get('backup', '')
        default_save_dir = config['Directories'].get('save', '')

def set_default_backup_directory():
    global default_backup_dir
    initial_dir = os.path.expanduser("~/Desktop")
    default_backup_dir = filedialog.askdirectory(title="Choose Default Backup Directory", initialdir=initial_dir)
    if default_backup_dir:
        save_default_directories()

def set_default_save_directory():
    global default_save_dir
    initial_dir = os.path.expanduser("~/Desktop")
    default_save_dir = filedialog.askdirectory(title="Choose Default Save Directory", initialdir=initial_dir)
    if default_save_dir:
        save_default_directories()

def save_default_directories():
    config = configparser.ConfigParser()
    config.read('game_tracker.ini', encoding='utf-8')
    if 'Directories' not in config:
        config['Directories'] = {}
    config['Directories']['backup'] = default_backup_dir
    config['Directories']['save'] = default_save_dir
    with open('game_tracker.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)

# Load default directories at startup
load_default_directories()

def backup_confirmation(selected_game):
    confirmation = messagebox.askyesno("Backup Confirmation", f"Do you want to backup '{selected_game}' before marking it as complete?")
    return confirmation

def choose_file_to_backup():
    file_to_backup = filedialog.askopenfilename(title="Choose File to Backup", initialdir=default_backup_dir)
    return file_to_backup

def choose_backup_destination(file_to_backup):
    backup_destination = filedialog.asksaveasfilename(title="Choose Backup Destination", defaultextension=os.path.splitext(file_to_backup)[1], initialdir=default_save_dir)
    return backup_destination

def perform_backup(file_to_backup, backup_destination):
    try:
        shutil.copyfile(file_to_backup, backup_destination)
        messagebox.showinfo("Backup Successful", f"Backup of '{file_to_backup}' created successfully at '{backup_destination}'.")
        return True
    except Exception as e:
        messagebox.showerror("Backup Failed", f"An error occurred while creating the backup: {e}")
        return False

def mark_game_as_complete(selected_game):
    global completed_games, config, to_complete_listbox

    # Remove the game from the to-complete games list
    to_complete_games.remove(selected_game)

    # Update the INI file
    if 'Hidden' not in config:
        config['Hidden'] = {}
    config['Hidden']['Completed'] = config['Hidden'].get('Completed', '') + ',' + selected_game
    config['Games']['ToComplete'] = ','.join(to_complete_games)

    # If backup is successful or skipped, move the game to completed
    completed_games.append(selected_game)

    # Save configuration after updating
    save_configuration()

    # Repopulate the to-complete listbox
    to_complete_listbox.delete(0, tk.END)  # Clear the listbox
    for game in to_complete_games:
        to_complete_listbox.insert(tk.END, game)  # Populate the listbox with sorted games

def update_completed_listbox():
    global completed_listbox, completed_games
    
    # Clear the listbox
    completed_listbox.delete(0, tk.END)
    
    # Populate the listbox with updated completed games
    for game in completed_games:
        if game.strip():
            completed_listbox.insert(tk.END, game)

def mark_as_to_complete():
    global completed_games, config, to_complete_listbox, default_backup_dir, default_save_dir

    # Remove empty equal sign lines from the INI file
    remove_empty_equal_sign('game_tracker.ini')
    selected_indices = to_complete_listbox.curselection()
    for i in selected_indices[::-1]:
        selected_game = to_complete_listbox.get(i)
        if selected_game.strip():  # Check if the selected game is not empty
            if selected_game not in completed_games:
                confirmation = backup_confirmation(selected_game)
                if not confirmation:
                    continue_without_backup = messagebox.askyesno("Confirmation", f"Do you still want to mark '{selected_game}' as complete?")
                    if not continue_without_backup:
                        messagebox.showinfo("Action Canceled", f"Marking '{selected_game}' as complete was canceled.")
                        continue  # Skip marking as complete
                else:
                    file_to_backup = choose_file_to_backup()
                    if not file_to_backup:
                        messagebox.showinfo("Action Canceled", "The operation was canceled.")
                        continue  # User canceled the operation

                    backup_destination = choose_backup_destination(file_to_backup)
                    if not backup_destination:
                        messagebox.showinfo("Action Canceled", "The operation was canceled.")
                        continue  # User canceled the operation

                    backup_success = perform_backup(file_to_backup, backup_destination)
                    if not backup_success:
                        messagebox.showerror("Backup Failed", "Failed to perform backup. Marking as complete was canceled.")
                        continue  # Stop if backup fails

                # Mark the game as complete and update the GUI
                mark_game_as_complete(selected_game)
                update_completed_listbox()  # Update the Completed Games listbox

    # Remove empty strings from the completed games list
    completed_games = [game for game in completed_games if game.strip()]

def move_completed_to_to_complete(event):
    global completed_listbox, config, completed_games, to_complete_listbox, to_complete_games

    # Remove empty equal sign lines from the INI file
    remove_empty_equal_sign('game_tracker.ini')

    selected_indices = completed_listbox.curselection()
    for i in selected_indices[::-1]:
        selected_game = completed_listbox.get(i)
        if selected_game.strip():
            to_complete_listbox.insert(tk.END, selected_game)
            to_complete_games.append(selected_game)
            completed_listbox.delete(i)
            completed_games.remove(selected_game)
            config['Games']['ToComplete'] = ','.join(to_complete_games)
            config['Hidden']['Completed'] = ','.join(completed_games)

            # Remove empty equal sign lines from the INI file
            remove_empty_equal_sign('game_tracker.ini')

            # Save the updated configuration
            save_configuration()

# Initialize stats_to_buy_dict as an empty dictionary
stats_to_buy_dict = {}

def remove_spaces_in_stats(stats):
    # Remove spaces around the equal sign
    stats = stats.replace(" =", "=")
    return stats

def save_game_stats(game_name, platform, price):
    global stats_to_buy_dict

    # Remove leading spaces from platform and price strings
    platform = platform.strip()
    price = price.strip() if price else ""

    stats_to_buy_dict[game_name] = (platform, price)

    config = configparser.ConfigParser()
    config.read('game_tracker.ini', encoding='utf-8')

    # Remove spaces between key-value pairs only for StatsToBuy section
    platform_str = platform.replace(" =", "=")
    price_str = price.replace(" =", "=")

    # Store game stats to buy in the [StatsToBuy] section
    if 'StatsToBuy' not in config:
        config['StatsToBuy'] = {}
    config['StatsToBuy'][game_name] = f"Platform={platform_str}, Price={price_str}"

    # Check if the game name is already present in the [Games] section
    if 'Games' not in config:
        config['Games'] = {}
    if 'Buy' not in config['Games']:
        config['Games']['Buy'] = ""  # Initialize as empty string if not already present
    if game_name not in config['Games']['Buy']:
        config['Games']['Buy'] += f",{game_name}"  # Concatenate the new game name if not already present

    with open('game_tracker.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)

def save_to_complete_game_stats(game_name, platform, misc_stats):
    global stats_to_complete_dict

    # Remove leading spaces from platform and misc_stats strings
    platform = platform.strip()
    misc_stats = misc_stats.strip()

    stats_to_complete_dict[game_name] = (platform, misc_stats)

    config = configparser.ConfigParser()
    config.read('game_tracker.ini')

    # Remove spaces between key-value pairs only for StatsToComplete section
    platform_str = platform.replace(" =", "=")
    misc_stats_str = misc_stats.replace(" =", "=")

    # Store game stats to complete in the [StatsToComplete] section
    if 'StatsToComplete' not in config:
        config['StatsToComplete'] = {}
    config['StatsToComplete'][game_name] = f"Platform={platform_str}, Misc={misc_stats_str}"

    with open('game_tracker.ini', 'w') as configfile:
        config.write(configfile)

# Define section as a global variable
section = None

def load_games_from_file(section):
    # Clear the stats_to_buy_dict before importing games
    stats_to_buy_dict.clear()

    # Set the initial directory to the desktop
    initial_dir = os.path.expanduser("~/Desktop")

    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    print("Selected file:", file_path)  # Debugging
    if file_path:
        try:
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    print("Row read:", row)  # Debugging
                    if len(row) >= 3:
                        game_name, platform, price = row[:3]
                        print("Game name:", game_name)  # Debugging
                        print("Platform:", platform)  # Debugging
                        print("Price:", price)  # Debugging
                        if game_name.strip():  # Check if game name is not empty
                            # Save game stats
                            save_game_stats(game_name, platform, price)
                    else:
                        game_name = row[0]
                        print("Game name:", game_name)  # Debugging
                        if game_name.strip():  # Check if game name is not empty
                            # Save game stats
                            save_game_stats(game_name, "", "")

            # Save the configuration after importing games
            save_configuration()
            load_configuration_at_startup()
            print("Configuration saved")  # Debugging

            # Show messagebox to inform the user
            messagebox.showinfo("Success", "Games loaded successfully")
        except Exception as e:
            # Show messagebox to inform the user of the error
            messagebox.showerror("Error", f"Failed to load games: {e}")
            print(f"Failed to load games: {e}")  # Debugging

def load_gamen_from_file(status):
    # Set the initial directory to the desktop
    initial_dir = os.path.expanduser("~/Desktop")

    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        try:
            with open(file_path, 'r') as file:
                games = file.read().splitlines()
                
            game_names_from_file = []
            for game in games:
                game_names = [name.strip() for name in game.split(',')]
                for game_name in game_names:
                    if game_name:
                        game_names_from_file.append(game_name.lower())  # Convert to lowercase for case-insensitive comparison

            # Check for duplicates within the file itself
            if len(set(game_names_from_file)) != len(game_names_from_file):
                messagebox.showerror("Duplicate Games", "The text file contains duplicate game names.")
                return

            for game in games:
                game_names = [name.strip() for name in game.split(',')]
                for game_name in game_names:
                    if status == 'Buy':
                        if game_name and game_name not in buy_games:
                            listbox.insert(tk.END, game_name)
                            buy_games.append(game_name)
                    elif status == 'ToComplete':
                        if game_name and game_name not in to_complete_games:
                            to_complete_listbox.insert(tk.END, game_name)
                            to_complete_games.append(game_name)

            messagebox.showinfo("Success", "Games loaded successfully.")

            # Save the configuration after importing games
            save_configuration()
            print("Configuration saved")  # Debugging

            # Repopulate the listbox after importing games
            if status == 'Buy':
                populate_listbox(listbox, buy_games)
                print("Listbox populated")  # Debugging
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load games: {e}")

def load_to_complete_gamen_from_file(status):
    # Set the initial directory to the desktop
    initial_dir = os.path.expanduser("~/Desktop")

    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        try:
            with open(file_path, 'r') as file:
                games = file.read().splitlines()
                
            game_names_from_file = []
            for game in games:
                game_names = [name.strip() for name in game.split(',')]
                for game_name in game_names:
                    if game_name:
                        game_names_from_file.append(game_name.lower())  # Convert to lowercase for case-insensitive comparison

            # Check for duplicates within the file itself
            if len(set(game_names_from_file)) != len(game_names_from_file):
                messagebox.showerror("Duplicate Games", "The text file contains duplicate game names.")
                return

            for game in games:
                game_names = [name.strip() for name in game.split(',')]
                for game_name in game_names:
                    if status == 'Buy':
                        if game_name and game_name not in buy_games:
                            listbox.insert(tk.END, game_name)
                            buy_games.append(game_name)
                    elif status == 'ToComplete':
                        if game_name and game_name not in to_complete_games:
                            to_complete_listbox.insert(tk.END, game_name)
                            to_complete_games.append(game_name)

                            # Add the game name to [Games] ToComplete section
                            if 'Games' not in config:
                                config['Games'] = {}
                            if 'ToComplete' not in config['Games']:
                                config['Games']['ToComplete'] = ""
                            config['Games']['ToComplete'] += f"{game_name},"
                            
            messagebox.showinfo("Success", "Games loaded successfully.")

            # Save the configuration after importing games
            save_configuration(config)  # Make sure to pass the config object
            print("Configuration saved")  # Debugging

            # Repopulate the listbox after importing games
            if status == 'ToComplete':
                populate_listbox(to_complete_listbox, to_complete_games)
                print("Listbox populated")  # Debugging
        except Exception as e:
            print("An unexpected error occurred:", e)

stats_to_complete_dict = {}

def load_to_complete_games_from_file(section):
    # Clear the stats_to_buy_dict before importing games
    stats_to_buy_dict.clear()

    # Set the initial directory to the desktop
    initial_dir = os.path.expanduser("~/Desktop")

    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    print("Selected file:", file_path)  # Debugging
    if file_path:
        try:
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    print("Row read:", row)  # Debugging
                    if len(row) >= 3:
                        game_name, platform, misc_stats = row[:3]
                        print("Game name:", game_name)  # Debugging
                        print("Platform:", platform)  # Debugging
                        print("Misc stats:", misc_stats)  # Debugging
                        if game_name.strip():  # Check if game name is not empty
                            # Save game stats
                            save_to_complete_game_stats(game_name, platform, misc_stats)
                    else:
                        game_name = row[0]
                        print("Game name:", game_name)  # Debugging
                        if game_name.strip():  # Check if game name is not empty
                            # Save game stats
                            save_to_complete_game_stats(game_name, "", "")

            # Save the configuration after importing games
            save_configuration()
            load_configuration_at_startup()
            messagebox.showinfo("Success", "Games loaded successfully.")  # Display success message
            print("Configuration saved")  # Debugging

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load games: {e}")  # Display error message
            print("Error occurred:", e)  # Debugging

def load_configuration_in_app():
    global config, buy_games, to_complete_games, completed_games, additional_info_dict, stats_to_buy_dict, stats_to_complete_dict
    file_path = 'game_tracker.ini'  # Path to the configuration file

    if file_path and os.path.exists(file_path):
        # Remove empty equal sign lines from the INI file
        remove_empty_equal_sign(file_path)

        config = configparser.ConfigParser()
        try:
            config.read(file_path)

            # Load buy games, games to complete, and completed games
            buy_games = config['Games'].get('Buy', '').split(',')
            to_complete_games = config['Games'].get('ToComplete', '').split(',')
            completed_games = config['Hidden'].get('Completed', '').split(',')

            # Load additional information dictionary
            additional_info_dict = {}
            if 'Info' in config:
                #print("Found 'Info' section in the INI file.")
                for game_name_ini, info_list in config['Info'].items():
                    #print(f"Processing game: {game_name_ini}")
                    # Look for the corresponding game name in the to_complete_games list, with any capitalization
                    matching_game_name = next((game_name for game_name in to_complete_games if game_name.lower() == game_name_ini.lower()), None)
                    if matching_game_name:
                        #print(f"Found matching game name: {matching_game_name}")
                        additional_info_dict[matching_game_name] = info_list.split(',')
                    #else:
                        #print(f"No matching game name found for: {game_name_ini}")
            #else:
                #print("'Info' section not found in the INI file.")

            # Load platform and price information from the [StatsToBuy] section
            stats_to_buy_dict = {}
            if 'StatsToBuy' in config:
                for game_name, info_str in config['StatsToBuy'].items():
                    info = dict(item.split('=') for item in info_str.split(','))
                    platform = info.get('Platform', '')
                    price = info.get('Price', '')
                    stats_to_buy_dict[game_name] = (platform, price)

            # Load platform and misc information from the [StatsToComplete] section
            stats_to_complete_dict = {}
            if 'StatsToComplete' in config:
                for game_name, info_str in config['StatsToComplete'].items():
                    # Split each item into key-value pairs, using the first '=' as the delimiter
                    info_parts = info_str.split('=')
                    if len(info_parts) == 2:
                        platform = info_parts[0]
                        misc = info_parts[1]
                        stats_to_complete_dict[game_name] = (platform, misc)
                    #else:
                        #print(f"Invalid format for '{game_name}' in [StatsToComplete] section.")

            # Update GUI elements with loaded data
            for game in buy_games:
                if game:
                    listbox.insert(tk.END, game)

            for game in to_complete_games:
                if game:
                    to_complete_listbox.insert(tk.END, game)

            # Remove completed games from the "Games to Complete" list
            for game in completed_games:
                if game in to_complete_games:
                    index = to_complete_games.index(game)
                    to_complete_listbox.delete(index)
                    to_complete_games.remove(game)
        except configparser.ParsingError as e:
            print("Error occurred while parsing game_tracker.ini file:", e)

def load_configuration_at_startup():
    global config, buy_games, to_complete_games, completed_games, additional_info_dict, stats_to_buy_dict, stats_to_complete_dict
    file_path = 'game_tracker.ini'  # Path to the configuration file

    if file_path and os.path.exists(file_path):
        # Remove empty equal sign lines from the INI file
        remove_empty_equal_sign(file_path)

        config = configparser.ConfigParser()
        try:
            config.read(file_path)

            # Load buy games, games to complete, and completed games
            buy_games = config['Games'].get('Buy', '').split(',')
            to_complete_games = config['Games'].get('ToComplete', '').split(',')
            completed_games = config['Hidden'].get('Completed', '').split(',')

            # Load additional information dictionary
            additional_info_dict = {}
            if 'Info' in config:
                #print("Found 'Info' section in the INI file.")
                for game_name_ini, info_list in config['Info'].items():
                    #print(f"Processing game: {game_name_ini}")
                    # Look for the corresponding game name in the to_complete_games list, with any capitalization
                    matching_game_name = next((game_name for game_name in to_complete_games if game_name.lower() == game_name_ini.lower()), None)
                    if matching_game_name:
                        #print(f"Found matching game name: {matching_game_name}")
                        additional_info_dict[matching_game_name] = info_list.split(',')
                    #else:
                        #print(f"No matching game name found for: {game_name_ini}")
            #else:
                #print("'Info' section not found in the INI file.")

            # Load platform and price information from the [StatsToBuy] section
            stats_to_buy_dict = {}
            if 'StatsToBuy' in config:
                for game_name, info_str in config['StatsToBuy'].items():
                    info = dict(item.split('=') for item in info_str.split(','))
                    platform = info.get('Platform', '')
                    price = info.get('Price', '')
                    stats_to_buy_dict[game_name] = (platform, price)

            # Load platform and misc information from the [StatsToComplete] section
            stats_to_complete_dict = {}
            if 'StatsToComplete' in config:
                for game_name, info_str in config['StatsToComplete'].items():
                    # Split each item into key-value pairs, using the first '=' as the delimiter
                    info_parts = info_str.split('=')
                    if len(info_parts) == 2:
                        platform = info_parts[0]
                        misc = info_parts[1]
                        stats_to_complete_dict[game_name] = (platform, misc)
                    #else:
                        #print(f"Invalid format for '{game_name}' in [StatsToComplete] section.")

            # Clear existing items from GUI elements
            listbox.delete(0, tk.END)
            to_complete_listbox.delete(0, tk.END)

            # Update GUI elements with loaded data
            for game in buy_games:
                if game:
                    listbox.insert(tk.END, game)

            for game in to_complete_games:
                if game:
                    to_complete_listbox.insert(tk.END, game)

            # Remove completed games from the "Games to Complete" list
            for game in completed_games:
                if game in to_complete_games:
                    index = to_complete_games.index(game)
                    to_complete_listbox.delete(index)
                    to_complete_games.remove(game)
        except configparser.ParsingError as e:
            print("Error occurred while parsing game_tracker.ini file:", e)
            # Handle the parsing error, such as skipping the problematic line or logging it
        except Exception as e:
            print("An unexpected error occurred:", e)
        finally:
            # After loading configuration, remove duplicate paths or URLs
            remove_duplicate_paths_or_urls(file_path)
    else:
        # If the file doesn't exist, initialize variables
        buy_games = []
        to_complete_games = []
        completed_games = []
        additional_info_dict = {}
        stats_to_buy_dict = {}
        stats_to_complete_dict = {}

# Define as a global variable
stats_to_buy_dict = {}

def save_configuration(keep_existing=False):
    global buy_games, to_complete_games, completed_games, additional_info_dict, stats_to_buy_dict, misc_info

    # Print the contents of global variables
    print("Global Variables:")
    print("buy_games:", buy_games)
    print("to_complete_games:", to_complete_games)
    print("completed_games:", completed_games)
    print("misc_info:", misc_info)
    print("additional_info_dict:", additional_info_dict)
    print("stats_to_buy_dict:", stats_to_buy_dict)
    print("stats_to_complete_dict:", stats_to_complete_dict)

    # Load existing configuration to preserve other sections
    existing_config = configparser.ConfigParser()

    # Load existing INI file
    existing_config.read('game_tracker.ini', encoding='utf-8')

    misc_info = ""  # Clear the misc_info variable

    # Store buy games and games to complete
    existing_config['Games'] = {'Buy': ','.join(filter(None, buy_games)),
                                'ToComplete': ','.join(filter(None, to_complete_games))}

    # Store completed games
    existing_config['Hidden'] = {'Completed': ','.join(filter(None, completed_games))}

    # Store additional information for each non-empty game in the [Info] section
    #if additional_info_dict:
        #existing_config['Info'] = {game_name: ','.join(info) for game_name, info in additional_info_dict.items() if game_name.strip()}

    # Update existing game stats to buy in the [StatsToBuy] section
    if 'StatsToBuy' not in existing_config:
        existing_config.add_section('StatsToBuy')

    for game_name, (platform, price) in stats_to_buy_dict.items():
        # Ensure that the price is not empty
        if price:
            existing_config.set('StatsToBuy', game_name, f"Platform={platform}, Price={price}")

    # Ensure that the price value is preserved
    for game_name in existing_config['StatsToBuy']:
        price_value = existing_config['StatsToBuy'].get(game_name).split("Price=")[-1].strip()
        if not price_value:
            # Fetch the existing price value from the stats_to_buy_dict
            existing_price = stats_to_buy_dict.get(game_name, ("", ""))[1]
            # Set the price to the existing value if it's not empty, otherwise set it to 0
            existing_config.set('StatsToBuy', game_name, f"Platform={platform}, Price={existing_price if existing_price else '0'}")

    # Save the updated configuration
    with open('game_tracker.ini', 'w', encoding='utf-8') as configfile:
        existing_config.write(configfile)

    # Remove empty lines with only an equal sign from the INI file
    remove_empty_equal_sign('game_tracker.ini')

    # Print confirmation message
    print("Configuration saved successfully.")

def on_closing():
    # Register the function to be called at exit
    atexit.register(create_ini_if_not_exists)

    # Remove empty lines with only an equal sign from the INI file
    remove_empty_equal_sign('game_tracker.ini')

    # Clear the stats_to_buy_dict dictionary
    stats_to_buy_dict.clear()

    #update_additional_info_in_ini()

    misc_info = ""  # Clear the misc_info variable
    
    # Close the application window
    root.destroy()

def show_completed_stats():
    selected_indices = completed_listbox.curselection()
    if selected_indices:
        for index in selected_indices:
            selected_game = completed_listbox.get(index).strip()  # Strip leading and trailing whitespace
            config = configparser.ConfigParser()
            config.read('game_tracker.ini', encoding='utf-8')

            # Check if the stripped selected game exists in the StatsToComplete section
            if config.has_option('StatsToComplete', selected_game):
                # Retrieve platform and miscellaneous stats information from the INI file
                try:
                    platform_misc_data = config.get('StatsToComplete', selected_game)
                    if platform_misc_data:
                        platform = platform_misc_data.split('Platform=')[-1].split(',')[0].strip()
                        misc_stats = platform_misc_data.split('Misc=')[-1].strip()
                    else:
                        platform = "Unknown"
                        misc_stats = "Unknown"
                except (configparser.NoOptionError, configparser.NoSectionError, IndexError):
                    platform = "Unknown"
                    misc_stats = "Unknown"
                
                # Display the platform and miscellaneous stats information
                messagebox.showinfo("Stats", f"Platform: {platform}\nMisc: {misc_stats}")
            else:
                messagebox.showinfo("Stats", f"No stats found for {selected_game}.")
    else:
        messagebox.showinfo("Stats", "Please select a game to view its stats.")

def show_completed_games():
    global completed_listbox, completed_games
    
    misc_info = ""  # Clear the misc_info variable

    # Check if there are any completed games
    if not completed_games or all(game.strip() == '' for game in completed_games):
        if 'Hidden' in config and 'completed' in config['Hidden'] and config['Hidden']['completed']:
            # Display a message box if the completed section exists but contains no non-empty games
            messagebox.showinfo("No Completed Games", "There are no completed games.")
        else:
            # Display a message box if the completed section doesn't exist or is empty
            messagebox.showinfo("No Completed Games", "There are no completed games.")
        return  # Exit the function if there are no completed games or all games are empty
    
    # If there are completed games, proceed to display them
    completed_games_window = tk.Toplevel(root)
    completed_games_window.title("Completed Games")
    
    # Make the window stay on top
    completed_games_window.attributes('-topmost', 'true')
    
    # Calculate position x and y coordinates for the popup window
    popup_width = 330
    popup_height = 200
    x = root.winfo_x() + (root.winfo_width() // 2) - (popup_width // 2)
    y = root.winfo_y() - popup_height - 50  # Position slightly higher than the main window
    completed_games_window.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
    
    completed_games_window.focus_set()  # Set focus to the completed games window
    
    # Create a frame to contain the Listbox and scrollbar
    frame = tk.Frame(completed_games_window)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Create a Listbox to display completed games
    completed_listbox = tk.Listbox(frame, height=10, width=50)
    completed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Create a Scrollbar and associate it with the Listbox
    scrollbar = tk.Scrollbar(frame, command=completed_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    completed_listbox.config(yscrollcommand=scrollbar.set)
    
    # Populate the Listbox with completed games
    for game in completed_games:
        if game.strip():  # Check if the game name is not empty
            completed_listbox.insert(tk.END, game)
    
    # Bind the <Delete> key to remove completed games
    completed_listbox.bind("<Delete>", lambda event: remove_from_completed(completed_listbox))
    
    # Bind Ctrl + Backspace to move completed games to "Games to Complete"
    completed_listbox.bind("<Control-BackSpace>", move_completed_to_to_complete)
    
    # Add a frame to contain the Info and Stats buttons and pack it at the bottom of the window
    button_frame = tk.Frame(completed_games_window)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Add the "Info" button to the completed games list
    info_button = tk.Button(button_frame, text="Info", command=show_completed_info, cursor="hand2")
    info_button.pack(side=tk.LEFT, padx=55, pady=2)  # Add padding to separate from the listbox
    
    # Add the "Stats" button to the completed games list
    stats_button = tk.Button(button_frame, text="Stats", command=show_completed_stats, cursor="hand2")
    stats_button.pack(side=tk.LEFT, padx=65, pady=2)  # Add padding to separate from the "Info" button

    # Bind mouse wheel events to the Listbox for scrolling
    completed_listbox.bind("<MouseWheel>", lambda event: completed_listbox.yview_scroll(-1 * (event.delta // 120), "units"))
        
def show_mass_import_name_help():
    help_text = """
    To mass import game names from a text file, ensure each game name is on a separate line. 
    Use the 'Import Games to Buy Names' or 'Import Games to Complete Names' options under the 'File' menu.

    IT'S HIGHLY RECOMMENDED TO IMPORT THE NAMES FIRST AND THEN STATS AFTER!
    
    Example text file:
    Halo
    Halo 2
    Halo 3
    """
    messagebox.showinfo("Mass Import Names Help", help_text)

def show_mass_import_stats_help():
    help_text = """
    To mass import game stats from a text file, ensure each game name + it's stats are on a separate line. 
    Use the 'Import Games to Buy Stats' or 'Import Games to Complete Stats' options under the 'File' menu.

    IT'S HIGHLY RECOMMENDED TO IMPORT THE NAMES FIRST AND THEN STATS AFTER!

    The "Games to buy" & "Games to Complete" stats are formatted slightly differently as you'll see here.

    To buy stats txt example: NAME, PLATFORM, PRICE        (Halo, Xbox, 10.99)

    To Complete stats txt example: NAME, PLATFORM, MISC (Halo, Xbox, DLC)

    you can ignore adding price/misc stats by leaving that part blank e.g.

    Price:
    With Price stats = Halo 3, PC, 10.99

    Without Price stats = Halo 3, PC,

    Misc:
    With Misc stats = Halo 3, PC, DLC

    Without Misc stats = Halo 3, PC,

    Example text file:
    Halo, Xbox, DLC
    Halo2, Xbox, 100%
    Halo3, Xbox, 100&
    
    """
    messagebox.showinfo("Mass Import Stats Help", help_text)

def show_save_load_help():
    help_text = """
    Save your progress using 'Save Configuration' under the 'File' menu and load it anytime with 'Load Configuration'.
    
    This feature allows you to keep track of your games across different sessions.
    """
    messagebox.showinfo("Save & Load Help", help_text)

def context_menu_help():
    help_text = """
    Remove Info: Remove additional information (URLs & File Paths).

    Reset Stats: Reset game statistics (Platform, Price & Misc).

    Add Stats: Add or update game statistics (Platform, Price & Misc).
    """
    messagebox.showinfo("Context Menu Help", help_text)

def show_add_game_info_help():
    help_text = """
    1. Add Game Info: Double-click on a game to add additional information.
    2. View Game Info: Select a game and press the "Info" button to see details.
    """
    messagebox.showinfo("Help", help_text)

def get_logo_image(url, size):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    request = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(request) as response:
        image_data = response.read()
        img = Image.open(BytesIO(image_data))
        img = img.resize((size, size))

        # Create a circular mask
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)

        # Apply the circular mask to the image
        circular_img = Image.new("RGBA", img.size, (255, 255, 255, 0))
        circular_img.paste(img, (0, 0), mask)

        return ImageTk.PhotoImage(circular_img)

def reset_configuration():
    confirmation = messagebox.askyesno("Reset Confirmation", "Are you sure you want to reset the configuration?")
    if confirmation:
        # Clear existing lists and GUI elements
        listbox.delete(0, tk.END)
        to_complete_listbox.delete(0, tk.END)
        completed_games.clear()
        buy_games.clear()
        to_complete_games.clear()
        
        # Clear dictionaries
        additional_info_dict.clear()
        stats_to_buy_dict.clear()
        stats_to_complete_dict.clear()
        misc_info = ""
        
        # Clear the configuration file
        with open('game_tracker.ini', 'w', encoding='utf-8') as configfile:
            config = configparser.ConfigParser()
            config.write(configfile)
        
        messagebox.showinfo("Reset", "Configuration has been reset.")

def show_keybinds(font=("Helvetica", 10)):
    import tkinter.scrolledtext as scrolledtext
    
    keybinds_text = """
    Keybinds:
    - Right Click Mouse(in list): View Context Menu
    - Ctrl + S: Save Configuration
    - Ctrl + O: Load Configuration
    - Ctrl + R: Reset Configuration
    - Ctrl + Backspace: Move Completed Games to To Complete
    - Ctrl + C: View Completed Games
    - Delete: Remove Selected Games
    """
    
    keybinds_window = tk.Toplevel(root)
    keybinds_window.title("Keybinds")
    
    # Calculate position x and y coordinates for the popup window
    popup_width = 460
    popup_height = 202
    x = root.winfo_x() + (root.winfo_width() // 2) - (popup_width // 2)
    y = root.winfo_y() - popup_height - 50  # Position slightly higher than the main window
    keybinds_window.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
    
    keybinds_window.focus_set()  # Set focus to the keybinds window
    
    text = scrolledtext.ScrolledText(keybinds_window, wrap=tk.WORD, width=40, height=10, font=font)
    text.insert(tk.INSERT, keybinds_text)
    text.pack(expand=True, fill="both")
    text.config(state=tk.DISABLED)

# Setup GUI
root = tk.Tk()
root.title("Game Tracker")

# Set window icon
icon_url = "https://static.wixstatic.com/media/4db758_a3fcdc0790ae43239044a3889fbbfb7c~mv2.png/v1/fit/w_256,h_256,q_90/4db758_a3fcdc0790ae43239044a3889fbbfb7c~mv2.webp"
icon_data = fetch_image(icon_url)

if icon_data:
    icon_image = Image.open(BytesIO(icon_data))
    root.iconphoto(True, ImageTk.PhotoImage(icon_image))

# Set default width and height
window_width = 800
window_height = 270

# Get screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate position x and y coordinates
x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)

# Set window width and height
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Frames
buy_frame = tk.Frame(root)
buy_frame.pack(side=tk.LEFT, padx=10, pady=10)
to_complete_frame = tk.Frame(root)
to_complete_frame.pack(side=tk.RIGHT, padx=10, pady=10)

# Buy Frame Widgets
tk.Label(buy_frame, text="Games to Buy").pack()
listbox = tk.Listbox(buy_frame, height=10, width=50)
listbox.pack()
buy_game_entry = tk.Entry(buy_frame, width=50)
buy_game_entry.pack()
tk.Button(buy_frame, text="Add", command=add_to_buy, cursor="hand2").pack(side=tk.LEFT)
tk.Button(buy_frame, text="Remove", command=remove_from_buy, cursor="hand2").pack(side=tk.LEFT)  # Remove button for "Games to Buy"
tk.Button(buy_frame, text="Info", command=lambda: show_additional_info(), cursor="hand2").pack(side=tk.LEFT)
tk.Button(buy_frame, text="Mark as Bought", command=mark_as_bought_new, cursor="hand2").pack(side=tk.LEFT)

# To Complete Frame Widgets
tk.Label(to_complete_frame, text="Games to Complete").pack()
to_complete_listbox = tk.Listbox(to_complete_frame, height=10, width=50)
to_complete_listbox.pack()
to_complete_game_entry = tk.Entry(to_complete_frame, width=50)
to_complete_game_entry.pack()
tk.Button(to_complete_frame, text="Add", command=add_to_complete, cursor="hand2").pack(side=tk.LEFT)
tk.Button(to_complete_frame, text="Remove", command=remove_from_complete, cursor="hand2").pack(side=tk.LEFT)  
tk.Button(to_complete_frame, text="Info", command=lambda: show_additional_info(), cursor="hand2").pack(side=tk.LEFT)
tk.Button(to_complete_frame, text="Mark as Complete", command=mark_as_to_complete, cursor="hand2").pack(side=tk.LEFT)

# Watermark
watermark_font = ("Helvetica", 8)  # Set default font size
watermark_label = tk.Label(root, text="Designed & Created by: M0VER", fg="grey", font=watermark_font)
watermark_label.pack(side=tk.BOTTOM)

def show_stats_to_complete():
    selected_indices = to_complete_listbox.curselection()
    if selected_indices:
        for index in selected_indices:
            selected_game = to_complete_listbox.get(index).strip()  # Strip leading and trailing whitespace
            config = configparser.ConfigParser()
            config.read('game_tracker.ini', encoding='utf-8')

            # Check if the stripped selected game exists in the StatsToComplete section
            if config.has_option('StatsToComplete', selected_game):
                # Retrieve platform and miscellaneous stats information from the INI file
                try:
                    platform_misc_data = config.get('StatsToComplete', selected_game)
                    if platform_misc_data:
                        platform = platform_misc_data.split('Platform=')[-1].split(',')[0].strip()
                        misc_stats = platform_misc_data.split('Misc=')[-1].strip()
                    else:
                        platform = "Unknown"
                        misc_stats = "Unknown"
                except (configparser.NoOptionError, configparser.NoSectionError, IndexError):
                    platform = "Unknown"
                    misc_stats = "Unknown"
                
                # Display the platform and miscellaneous stats information
                messagebox.showinfo("Stats", f"Platform: {platform}\nMisc: {misc_stats}")
            else:
                messagebox.showinfo("Stats", f"No stats found for {selected_game}.")
    else:
        messagebox.showinfo("Stats", "Please select a game to view its stats.")

# Add the "Stats" button to the existing GUI layout for games to complete
stats_button = tk.Button(to_complete_frame, text="Stats", command=show_stats_to_complete, cursor="hand2")
stats_button.pack(side=tk.LEFT, padx=10, pady=5)

# Def to handle the "Stats" button click event
def show_stats():
    selected_indices = listbox.curselection()
    if selected_indices:
        for index in selected_indices:
            selected_game = listbox.get(index).strip()  # Strip leading and trailing whitespace
            config = configparser.ConfigParser()
            config.read('game_tracker.ini', encoding='utf-8')

            # Check if the stripped selected game exists in the StatsToBuy section
            if config.has_option('StatsToBuy', selected_game):
                # Retrieve platform and price information from the INI file
                try:
                    platform_misc_data = config.get('StatsToBuy', selected_game)
                    if platform_misc_data:
                        platform = platform_misc_data.split('Platform=')[-1].split(',')[0].strip()
                        price = platform_misc_data.split('Price=')[-1].strip()
                    else:
                        platform = "Unknown"
                        price = "Unknown"
                except (configparser.NoOptionError, configparser.NoSectionError, IndexError):
                    platform = "Unknown"
                    price = "Unknown"
                
                # Display the platform and price information
                currency_sign = "£" if currency_var.get() == "GBP" else "$"
                messagebox.showinfo("Stats", f"Platform: {platform}\nPrice({currency_sign}): {price}")
            else:
                messagebox.showinfo("Stats", f"No stats found for {selected_game}.")
    else:
        messagebox.showinfo("Stats", "Please select a game to view its stats.")

# Add the "Stats" button to the existing GUI layout for games to buy
stats_button = tk.Button(buy_frame, text="Stats", command=show_stats, cursor="hand2")
stats_button.pack(side=tk.LEFT, padx=10, pady=5)

def open_link_circle(event):
    webbrowser.open("https://www.nexusmods.com/users/105540373?tab=user+files")

def change_cursor(event):
    circle_photo_label.config(cursor="hand2")

def reset_cursor(event):
    circle_photo_label.config(cursor="")

circle_photo_url = "https://static.wixstatic.com/media/4db758_14e6d6ac8107470d8136d8fbda34c56e~mv2.png/v1/fit/w_256,h_256,q_90/4db758_14e6d6ac8107470d8136d8fbda34c56e~mv2.webp"
circle_photo_data = fetch_image(circle_photo_url)

if circle_photo_data:
    circle_img = Image.open(BytesIO(circle_photo_data))
    circle_img = circle_img.resize((100, 100))

    # Create a circular mask
    mask = Image.new("L", circle_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, circle_img.size[0], circle_img.size[1]), fill=255)

    # Apply the circular mask to the image
    circular_img = Image.new("RGBA", circle_img.size, (255, 255, 255, 0))
    circular_img.paste(circle_img, (0, 0), mask)

    circle_photo = ImageTk.PhotoImage(circular_img)
    circle_photo_label = tk.Label(root, image=circle_photo)
    circle_photo_label.pack(pady=70)  # Adjust the padding to move the image vertically
    # Bind left mouse click to open link
    circle_photo_label.bind("<Button-1>", open_link_circle)
    # Bind mouse enter event to change cursor
    circle_photo_label.bind("<Enter>", change_cursor)
    # Bind mouse leave event to reset cursor
    circle_photo_label.bind("<Leave>", reset_cursor)

def show_info(game_name):

    misc_info = ""  # Clear the misc_info variable

    info = additional_info_dict.get(game_name)
    if info:
        dialog = tk.Toplevel(root)
        dialog.title(f"Information for {game_name}")

        if info[0].startswith("http"):
            def open_url():
                webbrowser.open(info[0])
                
            url_label = tk.Label(dialog, text=info[0], fg="blue", cursor="hand2")
            url_label.pack(padx=10, pady=5)
            url_label.bind("<Button-1>", lambda e: open_url())  # Bind left mouse click to open URL
        
        else:
            info_label = tk.Label(dialog, text=info[0])
            info_label.pack(padx=10, pady=5)

    else:
        messagebox.showinfo("Information", f"No additional information found for {game_name}.")

def remove_duplicate_paths_or_urls(file_path):
    ## Read the INI file
    config = configparser.ConfigParser()
    config.read(file_path)

    ## Check if the 'Info' section exists in the config
    if 'Info' in config:
        ## Iterate over each item in the 'Info' section
        for game, paths in config['Info'].items():
            ## Split the paths by comma and remove leading/trailing spaces
            unique_paths = list(set([path.strip() for path in paths.split(',')]))

            ## Update the 'Info' section with unique paths
            config['Info'][game] = ','.join(unique_paths)

    ## Write the updated configuration back to the INI file
    with open(file_path, 'w') as configfile:
        config.write(configfile)

# Global variable to store the reference to the "Add Links or Files" window
add_links_or_files_window = None

# Ensure that an item is selected in the listbox before retrieving its value
if listbox.curselection():
    # Get the selected game name from the listbox
    game_name = listbox.get(listbox.curselection())
else:
    # If no item is selected, display a message or handle the situation as needed
    print("No game selected.")

def update_additional_info_in_ini():
    global config, additional_info_dict
    
    # Clear the Info section in the config object
    if 'Info' in config:
        config.remove_section('Info')
    
    # Remove empty values from additional_info_dict and strip leading commas
    additional_info_dict = {game: [info.strip(',') for info in info_list if info.strip()] for game, info_list in additional_info_dict.items()}
    
    # Update the Info section in the config object
    if additional_info_dict:
        if 'Info' not in config:
            config.add_section('Info')
        for game_name, info_list in additional_info_dict.items():
            config.set('Info', game_name, ','.join(info_list))
    
    # Save the updated configuration
    save_configuration()

def add_links_or_files(game_name):
    dialog = AddLinksOrFilesDialog(None, game_name, on_success_callback=repopulate_listboxes)
    dialog.mainloop()

class AddLinksOrFilesDialog(simpledialog.Dialog):
    def __init__(self, parent, game_name, on_success_callback=None):
        self.game_name = game_name
        self.on_success_callback = on_success_callback
        super().__init__(parent)

    def body(self, master):
        self.title(f"Add Links or Files for {self.game_name}")

        file_button = tk.Button(master, text="File", command=self.add_file_and_close)
        file_button.pack(pady=10)

        url_button = tk.Button(master, text="URL", command=self.add_url_and_close)
        url_button.pack(pady=10)

    def buttonbox(self):
        pass

    def add_file_and_close(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.check_and_add(file_path)
            self.destroy()

    def add_url_and_close(self):
        url = simpledialog.askstring("Input", f"Enter URL for {self.game_name}:")
        if url:
            self.check_and_add(url)
            self.destroy()

    def check_and_add(self, item):
        config = configparser.ConfigParser()
        config.read('game_tracker.ini')

        if 'Info' not in config:
            config['Info'] = {}

        info_list = [info.strip() for info in config['Info'].get(self.game_name, '').split(',') if info.strip()]
        if item in info_list:
            messagebox.showwarning("Duplicate", f"The {item} already exists for {self.game_name}.")
        else:
            # Strip the item to remove leading or trailing spaces
            item = item.strip()
            info_list.append(item)
            config['Info'][self.game_name] = ', '.join(info_list)

            with open('game_tracker.ini', 'w') as configfile:
                config.write(configfile)

            messagebox.showinfo("Success", f"{item} added for {self.game_name}.")
            if self.on_success_callback:
                self.on_success_callback()

def repopulate_listboxes():
    # Reload the configuration and repopulate the listboxes here
    load_configuration_at_startup()

def on_game_double_click(event):

    load_configuration_in_app()

    widget = event.widget
    selection = widget.curselection()
    if selection:
        index = selection[0]
        game_name = widget.get(index)
        add_links_or_files(game_name)

# Double-click event binding
listbox.bind("<Double-Button-1>", on_game_double_click)

# Double-click event binding
to_complete_listbox.bind("<Double-Button-1>", on_game_double_click)

def add_platform_and_price():
    # Get the selected game from the listbox
    selected_game_index = listbox.curselection()
    if selected_game_index:
        selected_game = listbox.get(selected_game_index)
        
        # Create a dialog to input platform and price
        platform_price_dialog = tk.Toplevel(root)
        platform_price_dialog.title("Add Platform and Price")
        
        # Label and Entry for Platform
        platform_label = tk.Label(platform_price_dialog, text="Platform:")
        platform_label.grid(row=0, column=0, padx=5, pady=5)
        platform_entry = tk.Entry(platform_price_dialog, width=30)
        platform_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Label and Entry for Price
        price_label = tk.Label(platform_price_dialog, text="Price(£):")
        price_label.grid(row=1, column=0, padx=5, pady=5)
        price_entry = tk.Entry(platform_price_dialog, width=30)
        price_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Function to add platform and price
        def add_platform_price():
            platform = platform_entry.get().strip()
            price = price_entry.get().strip()
            if platform and price:
                # Ensure StatsToBuy section exists
                if 'StatsToBuy' not in config:
                    config['StatsToBuy'] = {}
                
                # Save the platform and price as separate key-value pairs
                config['StatsToBuy'][selected_game] = {'Platform': platform, 'Price': price}
                
                save_configuration()  # Save the updated configuration
                platform_price_dialog.destroy()  # Close the dialog
            
        # Button to add platform and price
        add_button = tk.Button(platform_price_dialog, text="Add", command=add_platform_price)
        add_button.grid(row=2, column=0, columnspan=2, pady=10)

# Menu
menu = tk.Menu(root)
root.config(menu=menu)

file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Save Configuration (Ctrl+S)", command=save_configuration)
file_menu.add_command(label="Load Configuration (Ctrl+O)", command=load_configuration_at_startup)
file_menu.add_command(label="Reset Configuration (Ctrl+R)", command=reset_configuration)
file_menu.add_separator()
file_menu.add_command(label="Set Default Backup Open Directory", command=set_default_backup_directory)
file_menu.add_command(label="Set Default Backup Save Directory", command=set_default_save_directory)
file_menu.add_separator()
file_menu.add_command(label="Import Games to Buy Names", command=lambda: load_gamen_from_file('Buy'))
file_menu.add_command(label="Import Games to Buy Stats", command=lambda: load_games_from_file('Buy'))
file_menu.add_command(label="Import Games to Complete Names", command=lambda: load_to_complete_gamen_from_file('ToComplete'))
file_menu.add_command(label="Import Games to Complete Stats", command=lambda: load_to_complete_games_from_file('ToComplete'))
file_menu.add_separator()
file_menu.add_command(label="Exit", command=on_closing)

completed_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Completed", menu=completed_menu)
completed_menu.add_command(label="View Completed Games (Ctrl+C)", command=show_completed_games)  # Corrected command

currency_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Currency", menu=currency_menu)

# Set the initial currency to GBP
currency_var = tk.StringVar()
currency_var.set("GBP")

config_file = "game_tracker.ini"

def load_currency_configuration():
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
        if 'Currency' in config and 'currency' in config['Currency']:
            return config['Currency']['currency']
    # Default to GBP if currency configuration is not found
    return 'GBP'

    # Remove stats not in sections
    #remove_stats_not_in_sections()

# Function to save currency configuration to the INI file
def save_currency_configuration(currency):
    config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        config['Currency'] = {}
    else:
        config.read(config_file)

    # Create the [Currency] section if it doesn't exist
    if 'Currency' not in config:
        config['Currency'] = {}

    config['Currency']['currency'] = currency
    with open(config_file, 'w') as configfile:
        config.write(configfile)
    print("Currency configuration saved successfully")

    # Remove stats not in sections
    #remove_stats_not_in_sections()

# Function to handle currency selection
def select_currency():
    global currency_symbol
    selected_currency = currency_var.get()
    if selected_currency == "GBP":
        currency_symbol = "GBP£"
    elif selected_currency == "USD":
        currency_symbol = "USD$"
    # Save the currency choice to the INI file
    save_currency_configuration(selected_currency)
    # Update other parts of the program as needed with the new currency symbol
    update_currency_symbol()

    # Remove stats not in sections
    #remove_stats_not_in_sections()

# Function to update other parts of the program with the new currency symbol
def update_currency_symbol():
    # Example of updating a label with the new currency symbol
    stats_label_text = f"Stats for games to buy list ({currency_symbol}):"
    # Update stats_label_text wherever it's being used

# Add options for GBP and USD
currency_menu.add_radiobutton(label="GBP", variable=currency_var, value="GBP", command=select_currency)
currency_menu.add_radiobutton(label="USD", variable=currency_var, value="USD", command=select_currency)

# Create the new menu
sort_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Sort", menu=sort_menu)

# Add options for sorting
sort_menu.add_command(label="Sort Games to Buy (A-Z)", command=lambda: sort_list(listbox, "Games"))
sort_menu.add_command(label="Sort Games to Complete (A-Z)", command=lambda: sort_to_complete_list(to_complete_listbox, "Games"))

# Function to sort a listbox and update the INI file
def sort_list(listbox, section_name):
    items = list(listbox.get(0, tk.END))  # Get all items in the listbox
    items.sort()  # Sort the items alphabetically
    listbox.delete(0, tk.END)  # Clear the listbox
    for item in items:
        listbox.insert(tk.END, item)  # Insert sorted items back into the listbox

    # Update the INI file with the sorted items
    update_ini_with_sorted_items(section_name, items)

# Function to update the INI file with sorted items
def update_ini_with_sorted_items(section_name, items):
    config = configparser.ConfigParser()
    config.read("game_tracker.ini")

    # Update the specified section with sorted items
    if section_name not in config:
        config[section_name] = {}
    config[section_name]['buy'] = ','.join(items)

    # Save the configuration to the INI file
    with open("game_tracker.ini", 'w') as configfile:
        config.write(configfile)

# Function to sort a listbox and update the INI file
def sort_to_complete_list(listbox, section_name):
    items = list(listbox.get(0, tk.END))  # Get all items in the listbox
    items.sort()  # Sort the items alphabetically
    listbox.delete(0, tk.END)  # Clear the listbox
    for item in items:
        listbox.insert(tk.END, item)  # Insert sorted items back into the listbox

    # Update the INI file with the sorted items
    update_ini_with_to_complete_sorted_items(section_name, items)

# Function to update the INI file with sorted items
def update_ini_with_to_complete_sorted_items(section_name, items):
    config = configparser.ConfigParser()
    config.read("game_tracker.ini")

    # Update the specified section with sorted items
    if section_name not in config:
        config[section_name] = {}
    config[section_name]['tocomplete'] = ','.join(items)

    # Save the configuration to the INI file
    with open("game_tracker.ini", 'w') as configfile:
        config.write(configfile)

def reset_stats(game_name):
    confirmation = messagebox.askyesno("Confirmation", f"Are you sure you want to reset stats for '{game_name}'?")
    if confirmation:
        # Normalize the game name to match the format in the INI file
        normalized_game_name = game_name.lower()

        # Remove the game from the respective section in the INI file
        config = configparser.ConfigParser()
        config.read('game_tracker.ini')
        if 'StatsToBuy' in config and normalized_game_name in config['StatsToBuy']:
            del config['StatsToBuy'][normalized_game_name]
            messagebox.showinfo("Info", f"Stats reset for '{game_name}'.")
        elif 'StatsToComplete' in config and normalized_game_name in config['StatsToComplete']:
            del config['StatsToComplete'][normalized_game_name]
            messagebox.showinfo("Info", f"Stats reset for '{game_name}'.")
        else:
            messagebox.showinfo("Info", f"No stats found for '{game_name}'.")

        # Update the INI file with the changes
        with open('game_tracker.ini', 'w') as configfile:
            config.write(configfile)

        # Update the listbox displays
        listbox.delete(0, tk.END)
        to_complete_listbox.delete(0, tk.END)
        load_configuration_at_startup()

def add_stats(game_name):
    # Create a new dialog window for adding stats
    dialog = AddStatsDialog(root, game_name)

    # Wait for the dialog window to close
    #dialog.wait_window(dialog)

class AddStatsDialog(simpledialog.Dialog):
    def __init__(self, parent, game_name):
        self.game_name = game_name
        super().__init__(parent)

    def body(self, master):
        self.title(f"Add Stats for '{self.game_name}'")
        
        # Create labels and entry fields for Platform and Price
        tk.Label(master, text="Platform:").grid(row=0, column=0, sticky="w")
        self.platform_entry = tk.Entry(master)
        self.platform_entry.grid(row=0, column=1)

        # If the game is in the "To Complete" list, include Misc field
        if self.game_name.lower() in [name.lower() for name in to_complete_games]:
            tk.Label(master, text="Misc:").grid(row=1, column=0, sticky="w")
            self.misc_entry = tk.Entry(master)
            self.misc_entry.grid(row=1, column=1)

        # Create label and entry field for Price only if the game is in the "Buy" list
        if self.game_name.lower() in [name.lower() for name in buy_games]:
            tk.Label(master, text="Price:").grid(row=2, column=0, sticky="w")
            self.price_entry = tk.Entry(master)
            self.price_entry.grid(row=2, column=1)

    def apply(self):
        # Get the entered values
        platform = self.platform_entry.get()
        price = self.price_entry.get() if hasattr(self, 'price_entry') else None
        misc = self.misc_entry.get() if hasattr(self, 'misc_entry') else None

        # Update the INI file based on the game category
        config = configparser.ConfigParser()
        config.read('game_tracker.ini')

        normalized_game_name = self.game_name.lower()
        if normalized_game_name in [name.lower() for name in to_complete_games]:
            if 'StatsToComplete' not in config:
                config['StatsToComplete'] = {}
            config['StatsToComplete'][normalized_game_name] = f"Platform={platform}, Misc={misc}"
        elif normalized_game_name in [name.lower() for name in buy_games]:
            if 'StatsToBuy' not in config:
                config['StatsToBuy'] = {}
            config['StatsToBuy'][normalized_game_name] = f"Platform={platform}, Price={price}"

        # Write the updated configuration to the INI file
        with open('game_tracker.ini', 'w') as configfile:
            config.write(configfile)

        # Refresh the configuration
        load_configuration_at_startup()

# Bind the right-click event to the listbox
listbox.bind("<Button-3>", lambda event: add_stats(listbox.get(listbox.nearest(event.y))))
to_complete_listbox.bind("<Button-3>", lambda event: add_stats(to_complete_listbox.get(to_complete_listbox.nearest(event.y))))

def remove_info_popup(event):
    # Determine which listbox triggered the event
    if event.widget == listbox:
        selected_listbox = listbox
    elif event.widget == to_complete_listbox:
        selected_listbox = to_complete_listbox
    else:
        return

    # Get the index of the selected item
    index = selected_listbox.nearest(event.y)

    if index >= 0:
        # Get the name of the selected game
        game_name = selected_listbox.get(index)

        # Create a context menu
        context_menu = tk.Menu(selected_listbox, tearoff=0)
        context_menu.add_command(label="Remove Info", command=lambda: remove_info(game_name))
        context_menu.add_command(label="Reset Stats", command=lambda: reset_stats(game_name))
        context_menu.add_command(label="Add Stats", command=lambda: add_stats(game_name))  # Add this line

        # Display the context menu at the location of the right-click
        context_menu.post(event.x_root, event.y_root)

additional_info_dict = {}  # Define the additional_info_dict globally

def reload_additional_info_dict():
    global additional_info_dict
    # Read the game names and info from the INI file
    config = configparser.ConfigParser()
    config.read('game_tracker.ini')
    additional_info_dict = {}
    if 'Info' in config:
        for game_name, info_list in config['Info'].items():
            additional_info_dict[game_name.lower()] = [info.strip() for info in info_list.split(',')]

def remove_info(game_name):
    # Reload the additional_info_dict from the INI file
    reload_additional_info_dict()

    # Normalize the game name to match the format in additional_info_dict
    game_name_normalized = game_name.lower()

    # Read the game names from the INI file
    config = configparser.ConfigParser()
    config.read('game_tracker.ini')

    # Check if the game name exists in the INI file
    if 'Info' not in config or game_name_normalized not in config['Info']:
        messagebox.showinfo("Info Not Found", f"No info found for '{game_name}'.")
        return

    # Create a new Toplevel window for selecting info to delete
    delete_info_window = tk.Toplevel()
    delete_info_window.title(f"Select Info to Delete for '{game_name}'")

    # Define window size
    window_width = 400
    window_height = 200

    # Get the screen width and height
    screen_width = delete_info_window.winfo_screenwidth()
    screen_height = delete_info_window.winfo_screenheight()

    # Calculate the position of the window to center it on the screen
    x = (screen_width - window_width) // 2

    # Adjust the y-coordinate to position the window slightly higher (north) of the main application window
    app_y = root.winfo_y()  # Assuming 'root' is the main application window
    y = app_y - window_height - 35  # Adjust the offset as needed

    # Set the window position
    delete_info_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Make the window stay on top
    delete_info_window.attributes('-topmost', True)

    # Create a Listbox to display the URLs and file paths
    info_listbox = tk.Listbox(delete_info_window, selectmode=tk.MULTIPLE)
    info_listbox.pack(fill=tk.BOTH, expand=True)

    # Populate the Listbox with the URLs and file paths
    info_items = additional_info_dict.get(game_name_normalized, [])
    for info in info_items:
        info_listbox.insert(tk.END, info.strip())

    def delete_selected_info():
        # Reload the additional_info_dict from the INI file
        reload_additional_info_dict()

        # Get the indices of the selected items
        selected_indices = info_listbox.curselection()

        if selected_indices:
            # Remove the selected URLs and file paths from the INI file
            selected_info = [info_listbox.get(index) for index in selected_indices]
            info_list = additional_info_dict.get(game_name_normalized, [])
            for info in selected_info:
                if info in info_list:
                    info_list.remove(info)
            config['Info'][game_name_normalized] = ', '.join(info_list)
            with open('game_tracker.ini', 'w') as configfile:
                config.write(configfile)

            # Notify the user that the info has been removed
            messagebox.showinfo("Info Removed", f"Selected info for '{game_name}' has been successfully removed.")

            # Close the window
            delete_info_window.destroy()

    # Create a button to delete the selected info
    delete_button = tk.Button(delete_info_window, text="Delete Selected Info", command=delete_selected_info)
    delete_button.pack()

# Bind the right-click event to the listbox
listbox.bind("<Button-3>", remove_info_popup)
to_complete_listbox.bind("<Button-3>", remove_info_popup)

help_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="Mass Import Names Help", command=show_mass_import_name_help)
help_menu.add_command(label="Mass Import Stats Help", command=show_mass_import_stats_help)
help_menu.add_command(label="Save & Load Help", command=show_save_load_help)
help_menu.add_command(label="Game Info Help", command=show_add_game_info_help)
help_menu.add_command(label="Context Menu Help", command=context_menu_help)
help_menu.add_command(label="Keybinds", command=lambda: show_keybinds(font=("Arial", 12)))

# Initial game lists
buy_games = []
to_complete_games = []
completed_games = []

# Call load_configuration_at_startup function at startup
create_ini_if_not_exists()
load_configuration_at_startup()
currency_var.set(load_currency_configuration())

root.protocol("WM_DELETE_WINDOW", on_closing)

# Key bindings
root.bind("<Delete>", lambda event: remove_from_buy() if listbox.curselection() else remove_from_complete())
root.bind("<Control-c>", lambda event: show_completed_games())
root.bind("<Control-s>", lambda event: save_configuration())
root.bind("<Control-o>", lambda event: load_configuration_at_startup())
root.bind("<Control-r>", lambda event: reset_configuration())  # Added key binding for reset
root.bind_all("<Control-BackSpace>", move_completed_to_to_complete)

root.mainloop()
