# ---
# jupyter:
#   jupytext_format_version: '1.2'
#   kernelspec:
#     display_name: Python (weather virtualenv)
#     language: python
#     name: weather
# ---

import pandas as pd
import pandas as pd
import geopandas
from shapely.geometry import Point
import matplotlib.pyplot as plt

try:
    # XXX this still contains stations with very few datapoints for prec_mm
    df2 = pd.read_csv("prepared_data.csv")
except:
    # read in the just data we're interested in 
    df = pd.read_csv("data.csv", usecols=['date', 'lat', 'lon', 'station', 'prec_mm'])
    # we're interested in precipitation; replace "Tr" (trace) with arbitrarily small figure
    df['prec_mm'] = pd.to_numeric(df['prec_mm'].str.replace("Tr", "0.01"))
    df = df.fillna(0)
    # There are summary rows in the data; remove those
    df2 = df[(~pd.isnull(df.lat)) & (df.station != 'Summary')]
    # Allow us to average over years
    df2['month-day'] = df2['date'].str.replace(r".*-(\d+)-(\d+)", r"\1-\2")
    # Skip leap year Feb 29ths for convenience
    df2 = df2[df2['month-day'] != '02-29']
    # Create a categorical variable: did it rain at all?
    df2['rained'] = df2.prec_mm.apply(lambda x: 1 if x > 0 else 0)
    # Prune stations with not-so-many data points
    counts = df2.groupby('station').count()
    total_rained = df2.groupby('station').sum()
    stations_with_data = df2.merge(
        counts[counts.date > 0.85*len(counts)], how='inner', on='station', suffixes=['', '_y'])
    # remove stations where there's never been any rain - presumably they don't measure it
    stations_with_data = stations_with_data.merge(
        total_rained[total_rained.rained > 500], how='inner', on='station', suffixes=['', '_y'])
    # Average across all years of data
    stations_with_data = stations_with_data.groupby(['month-day', 'station']).mean()
    stations_with_data = stations_with_data[['lat','lon','prec_mm','rained']]
    df2 = stations_with_data.reset_index()
    df2.write_csv("prepared_data.csv")

counts.head()

df2.head()

import itertools
def p_no_rain(p_rains, no_more_than=0):
    """Calculate the probability of it raining no more than N days,
    over a series of probabilities that it rains at all.
    
    This is very inefficient, there's certainly a better way of 
    building the permutations...
    """
    final_p = 0
    # The best case outcome
    desired_outcomes = ['no_rain'] * len(p_rains)
    permutations = set((tuple(desired_outcomes),))
    # Plus all the others, up to the worst case outcome
    for n in range(0, no_more_than):
        desired_outcomes[n] = 'rain'
        for p in itertools.permutations(desired_outcomes, len(p_rains)):
            permutations.add(p)
    for permutation in permutations:
        this_p = 1
        for i, outcome in enumerate(permutation):
            if outcome == 'no_rain':
                outcome_p = 1 - p_rains.iloc[i]
            else:
                outcome_p = p_rains.iloc[i]
            this_p = this_p * outcome_p
        final_p += this_p
    return final_p

# +
import datetime
from datetime import date, timedelta

def is_start_day(val, requested_day, year): 
    days = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6}
    day = val.isoweekday()
    return day == days[requested_day]


def nearest_station_name(df, location):
    from shapely.ops import nearest_points
    gdf = df.groupby('station').max()[['lat', 'lon']]
    # Compute vonoroi regions for each point
    gdf['coordinates'] = list(zip(gdf.lon, gdf.lat))
    gdf['coordinates'] = gdf['coordinates'].apply(Point)
    gdf = geopandas.GeoDataFrame(gdf, geometry='coordinates')
    pts = gdf.geometry.unary_union
    return gdf[gdf.geometry == nearest_points(location, pts)[1]].index[0]


def compute_locations(df, starting_day, days_holiday, max_days_rain_acceptable):
    date_parts = [int(x) for x in starting_day.split("-")]
    
    starting_date = date(*date_parts)
    ending_day = (starting_date + timedelta(days=days_holiday-1)).strftime("%m-%d")
    print("Checking dates", starting_date.strftime("%m-%d"), ending_day)
    df2 = df[(df['month-day'] >= starting_date.strftime("%m-%d")) & (df['month-day'] <= ending_day)]
    asd = df2.groupby('station')['rained'].apply(p_no_rain, no_more_than=max_days_rain_acceptable)
    df = pd.DataFrame(asd.sort_values(ascending=False))
    df.columns = ['p_good_weather']
    return df


def compute_dates(df, year, starting_day, days_holiday, max_days_rain_acceptable):
    df = df.copy()
    df['date'] = pd.to_datetime(df['month-day'] + '-' + str(year))
    df['is_start_day'] = df.date.apply(is_start_day, requested_day=starting_day, year=year)
    vals = []
    for row in df[df.is_start_day].iterrows():
        i = df.index.get_loc(row[0])   
        candidates = df.iloc[i:i+days_holiday]
        vals.append({'date': row[1]['date'], 'p':p_no_rain(candidates.rained, no_more_than=max_days_rain_acceptable)})
    return pd.DataFrame(vals).sort_values('p', ascending=False)

# +
# Best location for a given date
starting_day = "2019-07-12"
days_holiday = 3
max_days_rain_acceptable = 0

compute_locations(df2, starting_day, days_holiday, max_days_rain_acceptable).head(20)

# +
# Best date for a given location
starting_day = 'saturday'
days_holiday = 2
max_days_rain_acceptable = 0
year = 2019


stroud = Point(-2.2407643,51.7422478)
llanthony = Point(-3.1069677, 51.944618)
station = nearest_station_name(df2, llanthony)
print(station)
region = df2[df2.station == station]
asd = compute_dates(region, year, starting_day, days_holiday, max_days_rain_acceptable)
asd.head(10)
# -

station = nearest_station_name(df2, stroud)
region = df2[df2.station == station]
asd = compute_dates(region, year, starting_day, days_holiday, max_days_rain_acceptable)
asd.head(10)

asd[asd.date == '2019-06-07']

# # Working out which have too few data points

df3 = pd.read_csv("data.csv", usecols=['date', 'lat', 'lon', 'station', 'prec_mm'])
df3['prec_mm'] = pd.to_numeric(df3['prec_mm'].str.replace("Tr", "0.01"))

df4 = df3[df3.station == 'Jersey Airport']
import numpy as np
len(df4[np.isnan(df4.prec_mm)])/len(df4)

df2.groupby('station')['rained'].describe().sort_values('50%')
 

df2[df2.station == 'Redhill']
