"""
This script produces NBA Shot Charts
"""
# %% IMPORTS ===========================================================================================================
from nba_api.stats.endpoints import shotchartdetail as scd
import logging
import os
import warnings
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
import pandas as pd
import numpy as np
import time

LOGGER = logging.getLogger(__name__)

warnings.simplefilter(action='ignore')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(name)s:%(levelname)s:%(message)s ')

# %% CONFIG ============================================================================================================

# View a team's (TEAM_NAME) or a player's shot chart (PLAYER_NAME)
target_col = 'PLAYER_NAME'
# Select team or player
target_name = "Pascal Siakam"
# Select season
target_season = '2019-20'
# downloads the data and saves it to the DATA folder, if False will use the file in the DATA folder
extract_data = False

# number of hexagons (row) for shot chart
hexagons = 35


# %% FUNCTION ==========================================================================================================


# function to create shot data
def season_shot_chart(season_year):
    """ Returns a dataframe that contains shot information for a given season
    Args:
        season_year (string): A string in the format of YYYY-YY

    Returns:
        season_shot_data (list): A dataframe which has shot information for selected season
    """
    season_shot_df = scd.ShotChartDetail(team_id=0,
                                         player_id=0,
                                         season_nullable=season_year,
                                         context_measure_simple='FGA').get_data_frames()[0]

    LOGGER.info('Obtained data for {} season'.format(season_year))
    # save data to DATA folder
    season_shot_df.to_csv(os.path.join('DATA', 'nba_shots_detail_' + season_year.replace('-', '_') + '.csv'),
                          index=False)
    LOGGER.info('Saved {} season data to csv'.format(season_year))


# function to draw court
def draw_court(ax=None, color='black', lw=2, outer_lines=False):
    """
    Args:
        ax: axes object to plot onto, if None then select current one
        color (string): colour for court background, default black
        lw (int): line_width
        outer_lines (bool): select if the drawn court will have outer lines

    Returns:
        axes: returns axes object that draws a court
    """
    # If an axes object isn't provided to plot onto, just get current one
    if ax is None:
        ax = plt.gca()

    # Create the various parts of an NBA basketball court

    # Create the basketball hoop
    # Diameter of a hoop is 18" so it has a radius of 9", which is a value
    # 7.5 in our coordinate system
    hoop = Circle((0, 0), radius=7.5, linewidth=lw, color=color, fill=False)

    # Create backboard
    backboard = Rectangle((-30, -7.5), 60, -1, linewidth=lw, color=color)

    # The paint
    # Create the outer box 0f the paint, width=16ft, height=19ft
    outer_box = Rectangle((-80, -47.5), 160, 190, linewidth=lw, color=color,
                          fill=False)
    # Create the inner box of the paint, width=12ft, height=19ft
    # inner_box = Rectangle((-60, -47.5), 120, 190, linewidth=lw, color=color,
    #                       fill=False)

    # Create free throw top arc
    top_free_throw = Arc((0, 142.5), 120, 120, theta1=0, theta2=180,
                         linewidth=lw, color=color, fill=False)
    # Create free throw bottom arc
    bottom_free_throw = Arc((0, 142.5), 120, 120, theta1=180, theta2=0,
                            linewidth=lw, color=color, linestyle='dashed')
    # Restricted Zone, it is an arc with 4ft radius from center of the hoop
    restricted = Arc((0, 0), 80, 80, theta1=0, theta2=180, linewidth=lw,
                     color=color)

    # Three point line
    # Create the side 3pt lines, they are 14ft long before they begin to arc
    corner_three_a = Rectangle((-220, -47.5), 0, 140, linewidth=lw,
                               color=color)
    corner_three_b = Rectangle((220, -47.5), 0, 140, linewidth=lw, color=color)
    # 3pt arc - center of arc will be the hoop, arc is 23'9" away from hoop

    three_arc = Arc((0, 0), 475, 475, theta1=22, theta2=158, linewidth=lw,
                    color=color)

    # List of the court elements to be plotted onto the axes
    court_elements = [hoop, backboard, outer_box,
                      top_free_throw, bottom_free_throw,
                      restricted, corner_three_a,
                      corner_three_b, three_arc]

    if outer_lines:
        # Draw the half court line, baseline and side out bound lines
        outer_lines = Rectangle((-250, -47.5), 500, 470, linewidth=lw,
                                color=color, fill=False)
        court_elements.append(outer_lines)

    # Add the court elements onto the axes
    for element in court_elements:
        ax.add_patch(element)

    return ax


# function to create shot chart
def create_shot_chart(season_df, target_column, target_column_name, season_year, hexagon_width, color_scale='coolwarm'):
    """
    Args:
        season_df (list): data_frame of season
        target_column (string): either PLAYER_NAME or TEAM_NAME
        target_column_name (string): name of player or team name
        season_year (string): YYYY-YY format
        hexagon_width (integer): how many hexagons to have (width) in the plot
        color_scale (str): string representing colour selection of plot, default is 'coolwarm'

    Returns:

    """
    # Create league average data frame
    league_avg = (season_df.groupby(['SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA'], as_index=False)
                  .agg(FGA=('SHOT_ATTEMPTED_FLAG', 'sum'),
                       FGM=('SHOT_MADE_FLAG', 'sum'),
                       FG_PCT=('SHOT_MADE_FLAG', 'mean')))
    LOGGER.info('Created league average data frame')

    # Create data frame for specific team or player corresponding to target_column_name
    target_df = season_df.loc[season_df[target_column] == target_column_name]
    target_avg = (target_df.groupby(['SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA'], as_index=False)
                  .agg(FGA=('SHOT_ATTEMPTED_FLAG', 'sum'),
                       FGM=('SHOT_MADE_FLAG', 'sum'),
                       FG_PCT=('SHOT_MADE_FLAG', 'mean')))
    LOGGER.info('Created {} average data frame'.format(target_column_name))

    # Join dataframes to compute the net difference for each shooting zone between target and league average
    target_avg = pd.merge(target_avg, league_avg, on=['SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA'],
                          how='left', suffixes=('', '_league_avg'))

    target_avg['DIFF'] = target_avg['FG_PCT'] - target_avg['FG_PCT_league_avg']

    # Join net difference to each individual shot
    target_df = pd.merge(target_df,
                         target_avg,
                         on=['SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA'],
                         how='left')

    # Group individual shots into hexagonal bins
    target_shots_hex = plt.hexbin(target_df.LOC_X, target_df.LOC_Y,
                                  C=target_df.SHOT_ATTEMPTED_FLAG,
                                  reduce_C_function=np.sum,
                                  extent=(-250, 250, 422.5, -47.5),
                                  cmap=color_scale,
                                  gridsize=hexagon_width)
    plt.close()

    target_diff_hex = plt.hexbin(target_df.LOC_X, target_df.LOC_Y,
                                 C=target_df.DIFF,
                                 reduce_C_function=np.mean,
                                 extent=(-250, 250, 422.5, -47.5),
                                 cmap=color_scale,
                                 gridsize=hexagon_width)
    plt.close()

    shots_freq_by_hex = target_shots_hex.get_array()
    shots_diff = target_diff_hex.get_array()
    shots_loc = target_shots_hex.get_offsets()

    x = None
    y = None

    for i in range(len(shots_diff)):
        x = [i[0] for i in shots_loc]
        y = [i[1] for i in shots_loc]

    my_df = pd.DataFrame()
    my_df['loc_x'] = x
    my_df['loc_y'] = y
    my_df['difference'] = shots_diff
    my_df['freq'] = shots_freq_by_hex
    my_df['percentile'] = my_df['freq'].rank(pct=True)
    my_df['sizing'] = my_df['percentile'].apply(
        lambda pct: 2 if pct <= 0.4 else (
            40 if pct <= 0.75 else (
                100 if pct <= 0.90 else
                200)))
    LOGGER.info('Final Data for Plot Created')

    plt.figure(figsize=(10, 9.4), facecolor='black')
    plt.scatter(my_df.loc_x,
                my_df.loc_y,
                c=my_df.difference,
                s=my_df.sizing,
                cmap=color_scale,
                marker='h',
                vmin=-0.10,
                vmax=0.10)

    draw_court(outer_lines=True, color='blanchedalmond')
    plt.xlim(-250, 250)
    plt.ylim(422.5, -47.5)
    plt.axis('off')

    plt.text(240, 390, target_column_name, c='white', fontsize=20, horizontalalignment='right', weight='bold')
    plt.text(240, 410, season_year + " (reg. season)", c='dimgrey', fontsize=16, horizontalalignment='right',
             fontstyle='italic')
    plt.text(-245, 415, "@safee.c", fontname="Gabriola", fontsize=30, c='purple', weight='bold')
    LOGGER.info('Plot Created')
    plt.show()


# %% MAIN ==============================================================================================================


if __name__ == "__main__":

    if extract_data:
        # download data
        LOGGER.info('Data extract required for {}'.format(target_season))
        # run script to save season shot data
        shot_df = season_shot_chart(target_season)

    # read csv for season
    league_shot_df = pd.read_csv(os.path.join('DATA', 'nba_shots_detail_' + target_season.replace('-', '_') + '.csv'))

    create_shot_chart(league_shot_df, target_col, target_name, target_season, hexagons)
