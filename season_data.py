"""Local AFCON edition paths and source-backed overview metadata."""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd


APP_DIR = Path(__file__).resolve().parent
SEASON_YEARS = (2010, 2012, 2013, 2015, 2017, 2019, 2021, 2023, 2025)
COMPETITION_DATASETS = {
    year: (
        APP_DIR / 'AFCON_Seasons' / str(year) / f'AFCON{year} Squads Stats.csv',
        APP_DIR / 'AFCON_Seasons' / str(year) / f'AFCON{year} Players Stats.csv',
    )
    for year in SEASON_YEARS if year not in (2023, 2025)
}
COMPETITION_DATASETS.update({
    2023: (
        APP_DIR / 'Datasets' / 'AFCON Squads Stats.csv',
        APP_DIR / 'Datasets' / 'AFCON Players Stats.csv',
    ),
    2025: (
        APP_DIR / 'AFCON25_Scraping' / 'scrapling' / 'AFCON25 Squads Stats.csv',
        APP_DIR / 'AFCON25_Scraping' / 'scrapling' / 'AFCON25 Players Stats.csv',
    ),
})


def load_overview(year):
    if year == 2023:
        return {
            'goal_timing': {
                'segments': ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90'],
                'goals': [11, 12, 21, 20, 23, 31],
                'percentages': [9.2, 10.1, 17.6, 16.8, 19.3, 26.1],
            },
            'attendance_per_game': 27223,
            'revenue': {'million': 74.75, 'estimated': True},
            'logo_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/6/66/2023_Africa_Cup_of_Nations_logo.svg/500px-2023_Africa_Cup_of_Nations_logo.svg.png',
        }
    path = (APP_DIR / 'Datasets' / 'AFCON2025 Overview.json' if year == 2025
            else APP_DIR / 'AFCON_Seasons' / str(year) / 'overview.json')
    with path.open(encoding='utf-8') as source:
        overview = json.load(source)
    if year == 2025:
        overview['revenue']['million'] = overview['revenue']['estimated_million']
        overview['revenue']['estimated'] = True
        overview['logo_url'] = 'https://i0.wp.com/scissorskick.wordpress.com/wp-content/uploads/2025/12/0africa_cup_of_nations_logo.svg_.png'
    return overview


def competition_summary(year, squads=None):
    if squads is None:
        squads = pd.read_csv(COMPETITION_DATASETS[year][0])
    matches = squads['Matches Played'].sum(min_count=len(squads)) / 2
    # Scorer totals exclude own goals; both count in tournament goals/match.
    goals = (squads['Goals'].sum(min_count=len(squads))
             + squads['Own Goals'].sum(min_count=len(squads)))
    overview = load_overview(year)
    return {
        'goals_per_match': 2.29 if year == 2023 else goals / matches,
        'attendance': overview.get('attendance_per_game'),
        'revenue': overview.get('revenue', {}).get('million'),
    }


def format_goal_average(value):
    # Conventional decimal rounding: 68 / 32 = 2.125 displays as 2.13.
    return str(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
