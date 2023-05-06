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
    return match_words(club1,club2) or match_words(club2,club1)

def get_top_10_foreign_clubs(df, transfer_movement, league_name):
    foreign_clubs = df[df['transfer_movement'] == transfer_movement]
    foreign_clubs = foreign_clubs[foreign_clubs['club_involved_name'].notna()]

    # Filter out clubs from the same league as the club_name
    same_league_clubs = df[df['league_name'] == league_name]['club_name'].unique()
    foreign_clubs = foreign_clubs[~foreign_clubs['club_involved_name'].apply(lambda club: any(match(club, same_league_club) for same_league_club in same_league_clubs))]

    # Calculate the total sum of transfers and get the top 10 clubs
    foreign_clubs_sum = foreign_clubs.groupby('club_involved_name')['fee_cleaned'].sum().nlargest(10)
    return foreign_clubs_sum.reset_index().rename(columns={'club_involved_name': 'Club Name', 'fee_cleaned': 'Total Transfer Amount'})

# Function to get top 10 foreign clubs based on transfer movement
def get_top_10_foreign_clubs3(df, transfer_movement, league_name):
    foreign_clubs = df[df['transfer_movement'] == transfer_movement]
    foreign_clubs = foreign_clubs[foreign_clubs['club_involved_name'].notna()]

    # Filter out clubs from the same league as the club_name
    same_league_clubs = df[df['league_name'] == league_name]['club_name'].unique()
    foreign_clubs = foreign_clubs[~foreign_clubs['club_involved_name'].isin(same_league_clubs)]

    # Calculate the total sum of transfers and get the top 10 clubs
    foreign_clubs_sum = foreign_clubs.groupby('club_involved_name')['fee_cleaned'].sum().nlargest(10)
    return foreign_clubs_sum.reset_index().rename(columns={'club_involved_name': 'Club Name', 'fee_cleaned': 'Total Transfer Amount'})



def display_league_logo(league_csv):
    
    league_logos = {
    '1 Bundesliga': 'https://upload.wikimedia.org/wikipedia/en/thumb/d/df/Bundesliga_logo_(2017).svg/1920px-Bundesliga_logo_(2017).svg.png',
    'Championship': 'https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Premier_League_Logo.svg/1920px-Premier_League_Logo.svg.png',
    'Serie A': 'https://seeklogo.com/images/S/serie-a-logo-23C56FD3AB-seeklogo.com.png',
    'Premier Liga': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Russian_Premier_League_logo.svg/1920px-Russian_Premier_League_logo.svg.png',
    'Primera Division': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/LaLiga_Santander.svg/1280px-LaLiga_Santander.svg.png',
    'Premier League': 'https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Premier_League_Logo.svg/1920px-Premier_League_Logo.svg.png',
    'Eredivisie': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Eredivisie_nieuw_logo_2017-.svg/1920px-Eredivisie_nieuw_logo_2017-.svg.png',
    'Ligue 1': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Ligue_1_Uber_Eats.svg/1280px-Ligue_1_Uber_Eats.svg.png',
    'Liga Nos': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Liga_Portugal_2020.svg/1280px-Liga_Portugal_2020.svg.png',
    }
    


    logos_dir = 'league_logos'
    logo_url = league_logos.get(league_csv)

    if logo_url:
        st.image(logo_url, width=200)
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
        unique_seasons = sorted(df['season'].unique(), reverse=True)
        unique_leagues = df['league_name'].unique()

        # unique_clubs = pd.concat([df['club_name'], df['club_involved_name']]).drop_duplicates().dropna().sort_values().reset_index(drop=True)
        # for club_name in unique_clubs:
        #     print(club_name)


        # Dropdown selectors for 'season' and 'league_name'
        selected_season = st.sidebar.selectbox('Select season', unique_seasons, index=0)
        selected_league = st.sidebar.selectbox('Select league', unique_leagues)

        # Display the selected league's logo
        display_league_logo(selected_league)

        # Display data for the selected 'season' and 'league_name'
        st.header(f'Data for {selected_league} in season {selected_season}')
        league_data = df[(df['season'] == selected_season) & (df['league_name'] == selected_league)]
        st.write(league_data)

        # Display top 10 foreign clubs for incoming and outgoing transfers side by side
        st.header('Top 10 Foreign Clubs')
        col1, col2 = st.columns(2)
        top_incoming_clubs = get_top_10_foreign_clubs(league_data, 'in', selected_league)
        top_outgoing_clubs = get_top_10_foreign_clubs(league_data, 'out', selected_league)

        with col1:
            st.subheader('Incoming Transfers')
            st.write(top_incoming_clubs)

        with col2:
            st.subheader('Outgoing Transfers')
            st.write(top_outgoing_clubs)

    else:
        st.error(f'Data directory "{transfers_data_dir}" not found. Please check the data directory.')

if __name__ == '__main__':
    main()

           
