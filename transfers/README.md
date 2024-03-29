# transfers

[![summer update](https://github.com/ewenme/transfers/actions/workflows/summer.yml/badge.svg)](https://github.com/ewenme/transfers/actions/workflows/summer.yml)
[![winter update](https://github.com/ewenme/transfers/actions/workflows/winter.yml/badge.svg)](https://github.com/ewenme/transfers/actions/workflows/winter.yml)

Data on European football clubs' player transfers, as found on [Transfermarkt](https://www.transfermarkt.com/), since the 1992/93 season.

**IMPORTANT**: As of July 2022, transfer fees are now in EUR (taken from the .com Transfermarkt site), not GBP (taken from the .co.uk Transfermarkt site) due to a distortion of older fees being converted with a recent exchange rate.

## Contents

### Data

Transfers can be found in the `data/` directory, in .csv format. There's a file for each of these leagues:

- English Premier League (`premier-league.csv`)
- English Championship (`championship.csv`)
- French Ligue 1 (`ligue-1.csv`)
- German 1.Bundesliga (`1-bundesliga.csv`)
- Italian Serie A (`serie-a.csv`)
- Spanish La Liga (`primera-division.csv`)
- Portugese Liga NOS (`liga-nos.csv`)
- Dutch Eredivisie (`eredivisie.csv`)
- Russian Premier Liga (`premier-liga.csv`)

Common variables:

| Header | Description | Data Type |
| --- | --- | --- |
| `club_name` | name of club | text |
| `player_name` | name of player | text |
| `position` | position of player | text |
| `club_involved_name` | name of secondary club involved in transfer | text |
| `fee` | raw transfer fee information | text |
| `transfer_movement` | transfer into club or out of club? | text |
| `transfer_period` | transfer window (summer or winter) | text |
| `fee_cleaned` | numeric transformation of `fee`, in EUR millions| numeric |
| `league_name` | name of league `club_name` belongs to | text |
| `year` | year of transfer | text |
| `season` | season of transfer (interpolated from `year`) | text |
| `country` | country of league | text |

### Config

- `config/league-meta.csv` - leagues to scrape

New leagues can be exported by adding rows to the `config/league-meta.csv` file. Required columns are `league_name`, `league_id` and `country`. To get `league_name` and `league_id`, extract these from the transfermarkt URL for any leagues' transfer history: 

> www.transfermarkt.com/{LEAGUE_NAME}/transfers/wettbewerb/{LEAGUE_ID}/

When scraping new leagues, it is recommended to remove all the leagues that data has already been downloaded from (i.e. only include new leagues). This cuts on processing time and stress on servers.  

### Code

R:

- `src/scrape-summer.R`: retrieves latest summer window's data and appends new observations to CSVs in `data/`
- `scr/scrape-winter.R`: retrieves latest winter window's data and appends new observations to CSVs in `data/`
- `src/scrape-history.R`: retrieves transfer history by league and exports to CSVs in `data/`
- `src/functions.R`: local R functions used elsewhere

## Source

All squad data was scraped from [Transfermarkt](https://www.transfermarkt.com/), in accordance with their [terms of use](https://www.transfermarkt.co.uk/intern/anb).
