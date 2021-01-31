from espncricinfo.match import Match
from tqdm import tqdm
import json

from bs4 import BeautifulSoup
import pandas as pd
import lxml


import requests

class CricInfoScrape():
    
    # def __init__(self, match_num):
    #     self.match = Match(match_num)

    # load year_matchnum_dict
    def _get_ipl_mathcnum(self):
        with open(
            '/Users/jasonmyers/Documents/Coding_playground/cric/data/ipl_year_match_num.json'
        ) as json_file:
            year_matchnum_dict = json.load(json_file)
        
        return year_matchnum_dict


    def _get_bat_bowl_htmls(self, match_class):
        """
        Gets the html from match number that contains the batsmen in order and bowlers in order
        for each innings.
        """
        
        soup = BeautifulSoup(str(match_class.html), 'lxml')
        
        bat_inn1 = soup.findAll("table", {"class":"table batsman"})[0]
        bat_inn2 = soup.findAll("table", {"class":"table batsman"})[1]

        bowl_inn1 = soup.findAll("table", {"class":"table bowler"})[0]
        bowl_inn2 = soup.findAll("table", {"class":"table bowler"})[1]


        return (
            bat_inn1,
            bat_inn2,
            bowl_inn1,
            bowl_inn2
        )

    
    def _get_player_val_dict(self, html_script):
        """
        Gets the player number and name based on inputted html script
        """
        
        all_players = html_script.findAll("a", {"class":"small"})
        player_dict = []
        for player in all_players:
            try:
                k = player.contents[0].contents[0]
            except AttributeError:
                k = player.contents[0]
            player_num = str(player.get('href')).split('/')[-1].replace('.html', '')
            player_dict.append({k: player_num}) 

        return player_dict
    
    def get_match_summary_info(self, match_num):
        """
        Get summary of match including batsmen, bowlers and totals
        for each innnings
        """
        match = Match(match_num)
        
        innings1 = match.innings[0]
        innings2 = match.innings[1]

        (html_bat_inn1, 
        html_bat_inn2, 
        html_bowl_inn1, 
        html_bowl_inn2) = self._get_bat_bowl_htmls(match)


        return {
            'innings1': {
                'batsmen': self._get_player_val_dict(html_bat_inn1),
                'bowlers': self._get_player_val_dict(html_bowl_inn1),
                'total_runs': innings1['runs'],
                'total_wickets': innings1['wickets']
            },
            'innings2': {
                'batsmen': self._get_player_val_dict(html_bat_inn2),
                'bowlers': self._get_player_val_dict(html_bowl_inn2),
                'total_runs': innings2['runs'],
                'total_wickets': innings2['wickets']
            }
        }
    
    def _get_player_html(self, player_id):
        """
        Get html for given players
        """
        url = "https://www.espncricinfo.com/ci/content/player/{0}.html".format(str(player_id))
        r = requests.get(url)
        if r.status_code == 404:
            print('Player not found')
        else:
            soup = BeautifulSoup(r.text, 'html.parser')
            return soup

    def get_playing_stats(self, player_num):
        """
        Gets player stats of choice based on number
        """

        player_html = self._get_player_html(player_num)
        tables = player_html.findAll('table', class_='engineTable')

        batting = pd.read_html(str(tables[0]))[0]
        bowl = pd.read_html(str(tables[1]))[0]
        batting_stats = batting[['Mat', 'Inns', 'Ave', 'SR', 'BF']]
        batting_stats = batting_stats.rename(
            columns= {
                'Inns': 'bat_inns', 
                'Ave':'bat_ave', 
                'SR': 'bat_SR' ,
                'BF': 'bat_bf'
            }
        )
        T20batting_stats = batting_stats.iloc[-1]

        fielding_stats = batting[['Ct', 'St']]
        T20fielding_stats = fielding_stats.iloc[-1]

        bowling_stats = bowl[['Wkts', 'Ave', 'Econ', 'SR', 'Balls']]
        bowling_stats = bowling_stats.rename(
            columns= {
                'Ave':'bowl_ave', 
                'SR': 'bowl_SR' ,
                'Econ': 'bowl_econ',
                'Balls': 'bowl_balls'
            }
        )
        T20bowling_stats = bowling_stats.iloc[-1]
        
        return pd.concat(
            [T20batting_stats, T20bowling_stats, T20fielding_stats]
        )
    

