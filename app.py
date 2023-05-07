import os, re
import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image

# Function to load all CSV files in the specified directory
def load_dataframes_from_directory(directory):
    dataframes = []
    for file in os.listdir(directory):
        if file.endswith('.csv'):
            dataframes.append(pd.read_csv(os.path.join(directory, file)))
    return pd.concat(dataframes, ignore_index=True)


#matches club names if all words in club1 are in club2 in the same order
def match_words(club1, club2):
    #words
    club1w = club1.split(" ")
    #if club1 is 1 word only, check if it is in club2
    if len(club1w) == 1:
        return club1w[0] in club2.split(" ")    
    return re.match(club1.replace(" ", ".*?"), club2)

def match(club1, club2):
    return match_words(club1, club2) or match_words(club2, club1)

def get_top_10_foreign_clubs(df, transfer_movement, league_name):
    foreign_clubs = df[df['Transfer Movement'] == transfer_movement]
    foreign_clubs = foreign_clubs[foreign_clubs['Club Involved'].notna()]
    # Filter out clubs from the same league as the club_name
    same_league_clubs = df[df['League Name'] == league_name]['Club Name'].unique()
    foreign_clubs = foreign_clubs[~foreign_clubs['Club Involved'].apply(lambda club: any(match(club, same_league_club) for same_league_club in same_league_clubs))]
    # Calculate the total sum of transfers and get the top 10 clubs
    foreign_clubs_sum = foreign_clubs.groupby('Club Involved')['Transfer Fee (M)'].sum().nlargest(10)
    return foreign_clubs_sum.reset_index().rename(columns={'Club Involved': 'Club Name', 'Fee Cleaned': 'Total Transfer Amount'})

def get_top_10_transfers(df, league_name):
    # Calculate top 10 transfers
    return df.groupby('Player Name')['Transfer Fee (M)'].sum().nlargest(10)

def display_league_logo(league_csv):
    
    league_logos = {
    '1 Bundesliga': 'league_logos/1_Bundesliga.png',
    'Championship': 'league_logos/Premier_League_Logo.svg.png',
    'Serie A': 'league_logos/Logo_Lega_Serie_A.webp',
    'Premier Liga': 'league_logos/la_liga.png',
    'Primera Division': 'league_logos/la_liga.png',
    'Premier League': 'league_logos/Premier_League_Logo.svg.png',
    'Eredivisie': 'league_logos/ere.jpg',
    'Ligue 1': 'league_logos/ligue-1-logo.png',
    'Liga Nos': 'league_logos/liga_nos.png',
    }

    logos_dir = 'league_logos'
    logo_url = league_logos.get(league_csv)

    if logo_url:
        st.image(logo_url, width=128)
    else:
        st.warning(f'Logo not found for {league_csv}. Please check the "league_logos" dictionary.')

# Main app
def main():
    st.set_page_config(page_title='Soccer Transfer Market', layout='wide')
    st.title('Soccer Transfer Market')

    # Load data
    transfers_data_dir = 'transfers/data'
    if os.path.exists(transfers_data_dir):
        df = load_dataframes_from_directory(transfers_data_dir)
        display_columns = {
            'player_name': 'Player Name',
            'age': 'Age',
            'position': 'Position',
            'fee': 'Transfer Fee',
            'transfer_period': 'Transfer Window',
            'club_name': 'Club Name',
            'club_involved_name': 'Club Involved',
            'fee_cleaned': 'Transfer Fee (M)',
            'transfer_movement': 'Transfer Movement',
            'league_name': 'League Name',
            'season': 'Season',
            'year': 'Year',
            'country': 'Country'
        }
        df.rename(columns=display_columns, inplace=True)
        unique_seasons = sorted(df['Season'].unique(), reverse=True)
        unique_leagues = df['League Name'].unique()

        # Dropdown selectors for 'season' and 'league_name'
        selected_season = st.sidebar.selectbox('Select season', unique_seasons, index=0)
        selected_league = st.sidebar.selectbox('Select league', unique_leagues)

        # Get unique club names based on the selected season and league
        unique_club_names = df[(df['Season'] == selected_season) & (df['League Name'] == selected_league)]['Club Name'].unique()
        selected_club = st.sidebar.selectbox('Select club', ['all clubs'] + list(unique_club_names))
        
        # Display the selected league's logo
        display_league_logo(selected_league)

        # Filter data for the selected 'season', 'league_name', and 'club_name' if not 'all-clubs'
        league_data = df[(df['Season'] == selected_season) & (df['League Name'] == selected_league)]
        display_header = selected_league
        if selected_club != 'all clubs':
            display_header = selected_club
            league_data = league_data[league_data['Club Name'] == selected_club]
        
        # Display data for the selected 'season' and 'league_name'
        st.header(f'Transfers for {display_header} in season {selected_season}')
        st.write(league_data)

        # Display top 10 foreign clubs for incoming and outgoing transfers side by side
        st.header(f'Top 10 Foreign Club Transfers for {display_header}')
        col1, col2, col3 = st.columns(3)
        top_incoming_clubs = get_top_10_foreign_clubs(league_data, 'in', selected_league)
        top_outgoing_clubs = get_top_10_foreign_clubs(league_data, 'out', selected_league)
        players = get_top_10_transfers(league_data, selected_league)

        with col1:
            st.subheader('Incoming')
            st.write(top_incoming_clubs)

        with col2:
            st.subheader('Outgoing')
            st.write(top_outgoing_clubs)
        with col3:
            st.subheader('Players')
            st.write(players)

    else:
        st.error(f'Data directory "{transfers_data_dir}" not found. Please check the data directory.')

if __name__ == '__main__':
    main()
