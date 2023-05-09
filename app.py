import os, re
import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image

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

def get_top_4_incoming_transfers(df, league_name, club_name):
    incoming_transfers = df[(df['Transfer Movement'] == 'in') & (df['League Name'] == league_name) & (df['Club Name'] == club_name)]
    top_4_incoming_transfers = incoming_transfers.nlargest(4, 'Transfer Fee (M)')
    return top_4_incoming_transfers[['Player Name', 'Club Involved', 'Transfer Fee (M)']]

def display_league_logo(league_csv):
    
    league_logos = {
    '1 Bundesliga': 'league_logos/1_Bundesliga.png',
    'Championship': 'league_logos/Premier_League_Logo.svg.png',
    'Serie A': 'league_logos/Logo_Lega_Serie_A.webp',
    'Premier Liga': 'league_logos/premier_liga.png',
    'Primera Division': 'league_logos/la_liga.png',
    'Premier League': 'league_logos/Premier_League_Logo.svg.png',
    'Eredivisie': 'league_logos/ere.jpg',
    'Ligue 1': 'league_logos/ligue-1-logo.png',
    'Liga Nos': 'league_logos/liga_nos.png',
    'all leagues': 'league_logos/all_leagues.png',
    }

    logos_dir =   'league_logos'
    logo_url = league_logos.get(league_csv)

    if logo_url:
        st.image(logo_url, width=128)
    else:
        st.warning(f'Logo not found for {league_csv}. Please check the "league_logos" dictionary.')

def get_club_summary(df):
    summary_df = df.copy()   
    summary_df['Free Transfer'] = summary_df['Transfer Fee'].apply(lambda fee: 1 if 'free' in str(fee).lower() else 0)
    summary_df['Loan Transfer'] = summary_df['Transfer Fee'].apply(lambda fee: 1 if 'loan' in str(fee).lower() else 0)
    summary_df['Transfer Fee'] = summary_df['Transfer Fee (M)']

    club_summary = summary_df.groupby(['Club Name']).agg(
        total_transfer_volume=('Transfer Fee (M)', 'sum'),
        number_of_transfers=('Player Name', 'count'),
        transfer_profit=('Transfer Fee (M)', lambda x: x[df['Transfer Movement'] == 'out'].sum() - x[df['Transfer Movement'] == 'in'].sum()),
        median_transfer_age=('Age', 'median'),
        free_transfers=('Free Transfer', 'sum'),
        loan_transfers=('Loan Transfer', 'sum')
    ).reset_index()

    # Sort the table by total_transfer_volume
    club_summary.sort_values(by='total_transfer_volume', ascending=False, inplace=True)

    # Rename the columns nicely
    nice_column_names = {
        'Club Name': 'Club Name',
        'total_transfer_volume': 'Transfer Volume (M)',
        'number_of_transfers': 'Number of Transfers',
        'transfer_profit': 'Transfer Profit (M)',
        'median_transfer_age': 'Median Transfer Age',
        'free_transfers': 'Free Transfers',
        'loan_transfers': 'Loan Transfers'
    }
    club_summary.rename(columns=nice_column_names, inplace=True)

    return club_summary

def get_net_flow(df):
    # Filter out transfers with no league involved
    df = df[(df['Club Involved'].notna()) & (df['Involved League'].notna())]

    # Create a pivot table with the sum of transfer fees between leagues
    net_flow = df.pivot_table(
        index='League Name',
        columns='Involved League',
        values='Transfer Fee (M)',
        aggfunc='sum',
        fill_value=0
    ).add_prefix('To:').reset_index()
    return net_flow

def get_current_roster(df, club_name, selected_season):
    # Filter transfers for the selected club and seasons up to the selected season
    selected_year = int(selected_season.split('/')[0])
    club_transfers = df[(df['Club Name'] == club_name) & (df['Year'] <= selected_year)]

    # Get all incoming transfers for the club
    incoming_transfers = club_transfers[club_transfers['Transfer Movement'] == 'in']
    
    # Get all outgoing transfers for the club
    outgoing_transfers = club_transfers[club_transfers['Transfer Movement'] == 'out']

    # Get the latest incoming transfer for each player
    latest_incoming_transfers = incoming_transfers.loc[incoming_transfers.groupby('Player Name')['Year'].idxmax()]

    # Get the latest outgoing transfer for each player
    latest_outgoing_transfers = outgoing_transfers.loc[outgoing_transfers.groupby('Player Name')['Year'].idxmax()]

    # Get the current roster by removing the players who have transferred out after their last incoming transfer
    current_roster = pd.merge(latest_incoming_transfers, latest_outgoing_transfers, on='Player Name', how='left', suffixes=('_in', '_out'))
    current_roster = current_roster[current_roster['Year_out'].isnull() | (current_roster['Year_in'] > current_roster['Year_out'])]
    current_roster['Last Transfer Season'] = current_roster['Season_in'].apply(lambda x: str(int(x[:4])))
  
    # Calculate the years stayed at the club
    current_roster['Years Stayed'] = selected_year - current_roster['Year_in']

    # Filter out players who have stayed for more than 24 years (Maldini, Totti, etc.)
    current_roster = current_roster[current_roster['Years Stayed'] <= 24]

    # Select relevant columns and rename them
    current_roster = current_roster[['Player Name', 'Age_in','Position_in', 'Transfer Fee (M)_in', 'Last Transfer Season', 'Club Involved_in']]
    return current_roster

def get_player_history(df, player_name):
    player_history = df[df['Player Name'] == player_name].sort_values('Year', ascending=False)
    
    outgoing_transfers = player_history[player_history['Transfer Movement'] == 'out'].sort_values('Year', ascending=True)
    transfer_fee_differences = outgoing_transfers['Transfer Fee (M)'].diff().dropna()
    net_transfer_volume = transfer_fee_differences.sum()

    player_data = {
        'total_transfer_volume': player_history['Transfer Fee (M)'].sum()/2,
        'net_transfer_volume': "%5.1d M"%net_transfer_volume,
        'number_of_transfers': player_history['Transfer Movement'].count(),
        'average_duration': player_history[player_history['Transfer Window'] == 'Summer']['Year'].diff(-1).sum() + 0.5 * player_history[player_history['Transfer Window'] == 'Winter']['Year'].diff(-1).sum(),
        'number_of_clubs': player_history['Club Name'].nunique(),
        'positions': ', '.join(player_history['Position'].unique()),
        'most_recent_position': player_history.iloc[0]['Position']
    }
    nice_column_names = {
    'total_transfer_volume': 'Total Transfer Volume (M)',
    'net_transfer_volume': 'Net Transfer Volume (M)',
    'number_of_transfers': 'Number of Transfers',
    'average_duration': 'Average Duration (Years)',
    'number_of_clubs': 'Number of Clubs',
    'positions': 'Positions',
    'most_recent_position': 'Most Recent Position'
    }
    #Apply nice_column_names to player_data
    player_data_nice = {nice_column_names[key]: value for key, value in player_data.items()}

    return player_history, player_data_nice

def get_unique_players(df, selected_club='all clubs'):
    if selected_club == 'all clubs':
        return ['all players'] + list(df['Player Name'].unique())
    else:
        return ['all players'] + list(df[df['Club Name'] == selected_club]['Player Name'].unique())

# Main app
def main():
    st.set_page_config(page_title='Soccer Transfer Market', layout='wide')
    st.title('Soccer Transfer Market')

    # Load data
    transfers_data = 'combined_transfers_data.csv.gz'
    if os.path.exists(transfers_data):
        df = pd.read_csv(transfers_data, compression='gzip')
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
            'country': 'Country',
            'club_involved_cleaned': 'Parent Club Involved',
            'involved_league': 'Involved League'
        }
        df.rename(columns=display_columns, inplace=True)
        unique_seasons = sorted(df['Season'].unique(), reverse=True)
        unique_leagues = ['all leagues'] + list(df['League Name'].unique())

         # Dropdown selectors for 'season' and 'league_name'
        selected_season = st.sidebar.selectbox('Select season', unique_seasons, index=0)
        selected_league = st.sidebar.selectbox('Select league', unique_leagues, index=0)

        # Get unique club names based on the selected season and league
        unique_club_names = df[(df['Season'] == selected_season) & (df['League Name'] == selected_league)]['Club Name'].unique()
        selected_club = st.sidebar.selectbox('Select club', ['all clubs'] + list(unique_club_names))
        

         # Filter data for the selected 'season', 'league_name', and 'club_name' if not 'all-clubs'
        league_data = df[(df['Season'] == selected_season) & (df['League Name'] == selected_league)]
        display_league_logo(selected_league)

        unique_player_names = get_unique_players(league_data, selected_club)
        selected_player = st.sidebar.selectbox('Select player', unique_player_names)

        # Lastly, add the following lines inside the main() function after the line "st.write(league_data)":
        if selected_league == 'all leagues':
            st.header('Net Flow between European Leagues')
            net_flow = get_net_flow(df[df['Season'] == selected_season])
            st.write(net_flow)
            return

        if selected_player != 'all players':
            player_history, player_data = get_player_history(df, selected_player)
            selected_club = player_history.iloc[0]['Club Name']
            league_data = league_data[league_data['Club Name'] == selected_club]

            st.header(f'Player History for {selected_player}')
            st.write(player_history.reset_index(drop=True))

            st.header(f'Player Stats for {selected_player}')
            st.write(pd.DataFrame.from_dict(player_data, orient='index', columns=['Value']))



        display_header = selected_league
        if selected_club != 'all clubs':
            display_header = selected_club
            league_data = league_data[league_data['Club Name'] == selected_club]
        
        # Display the top 4 incoming transfers for the selected league and club
        #if selected_club != 'all clubs':
        top_4_incoming_transfers = league_data[league_data['Transfer Movement'] == 'in'].nlargest(4, 'Transfer Fee (M)')
        top_4_outgoing_transfers = league_data[league_data['Transfer Movement'] == 'out'].nlargest(4, 'Transfer Fee (M)')

        # Format the top 4 incoming transfers as a comma-separated string
        top_4_incoming_transfers_str = ', '.join(
            [f'<span style="color:blue">{player}</span> from {club} ({fee}M)' for player, club, fee in
                top_4_incoming_transfers[['Player Name', 'Club Involved', 'Transfer Fee (M)']].itertuples(index=False)])
        top_4_outgoing_transfers_str = ', '.join([f'<span style="color:blue">{player}</span> to {club} ({fee}M)' for player, club, fee in
                top_4_outgoing_transfers[['Player Name', 'Club Involved', 'Transfer Fee (M)']].itertuples(index=False)])


        if selected_club == 'all clubs':
             club_summary = get_club_summary(league_data)
             st.header(f'Club Summary for {selected_league} in season {selected_season}')
             st.write(club_summary)
        else:
            current_roster = get_current_roster(df, selected_club, selected_season)
            total_transfer_fee = current_roster['Transfer Fee (M)_in'].sum()
            st.header(f'Current Roster for {selected_club} (Fees: {total_transfer_fee}M)')
            st.write(current_roster.reset_index(drop=True))
                        


        # Display the top 4 incoming transfers
        st.markdown(f'### Top Transfers:')
        st.markdown(f'In: {top_4_incoming_transfers_str}', unsafe_allow_html=True)
        st.markdown(f'Out: {top_4_outgoing_transfers_str}',unsafe_allow_html=True)
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
        st.error(f'Data file "{transfers_data}" not found. Please check the root directory.')

if __name__ == '__main__':
    main()


