from nba_api.stats.endpoints import shotchartdetail

season_shots_19_20 = shotchartdetail.ShotChartDetail(team_id=0,
                                             player_id=0,
                                             season_nullable='2019-20',
                                             context_measure_simple='FGA').get_data_frames()[0]

season_shots_20_21 = shotchartdetail.ShotChartDetail(team_id=0,
                                             player_id=0,
                                             season_nullable='2020-21',
                                             context_measure_simple='FGA').get_data_frames()[0]
