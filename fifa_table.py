from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pandas as pd
import pickle


class PlayerStats():
    def __init__(self, name):
        self.name = name
        self.games_played = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.goals_for = 0
        self.goals_against = 0
        
    @property
    def points(self):
        return 3 * self.wins + self.draws
    
    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against

        
# initializes spreadsheet
def intialize_spreadsheet():
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('C:/Users/bshi1_000.BOBBY-PC/Desktop/client_secret.json', scope)
    client = gspread.authorize(creds)

    # Working spreadsheet
    sht = client.open("FIFA SHEET")
    
    return sht

    
# returns object states
def pickle_loader():
    try:
        object_states = pickle.load(open("object_states.pkl", "rb"))
        return object_states
    except (OSError, IOError) as e:
        names = ['Bobby', 'Diego', 'Rohan', 'Toshi', 'Winfred']
        players = [PlayerStats(name) for name in names]
        return players


# reads index of last row of table
def log_reader():
    try:
        fix_len = open('fixtures_log.log', 'r')
        fixtures_len = int(fix_len.read())
        return fixtures_len
        fix_len.close()
    except:
        fixtures_len = 0
        return fixtures_len


# pulls fixtures table from google spreadsheets
def load_fixtures():
    sht = intialize_spreadsheet()

    worksheet = sht.get_worksheet(1)
    array = worksheet.get_all_records()
    fixtures = pd.DataFrame(array)
    fixtures = fixtures[['Player 1', 'Player 1 Score', 'Player 2 Score', 'Player 2']]
    
    return fixtures     
        
        
# returns only the fixtures that have not been seen before
def get_new_fixtures():
    fixtures_len = log_reader()
    fixtures = load_fixtures()
    
    new_fixtures = fixtures[fixtures_len:]
    
    return new_fixtures


# determines winner if score does not match
def determine_winner(player_1, player_2, score_1, score_2):
    if score_1 > score_2:
        return player_1, player_2, score_1, score_2
    
    elif score_2 > score_1:
        return player_2, player_1, score_2, score_1 
    

# math/logic for updating player stats
def match_update(player_1, player_2, score_1, score_2, players):
    if score_1 != score_2:
        winner, loser, winner_score, loser_score = determine_winner(player_1, player_2, score_1, score_2)
        
        for player in players:
            if player.name == winner:
                player.games_played += 1
                player.wins += 1
                player.goals_for += winner_score
                player.goals_against += loser_score
                
            elif player.name == loser:
                player.games_played += 1
                player.losses += 1
                player.goals_for += loser_score
                player.goals_against += winner_score
                
    elif score_1 == score_2:
        
        for player in players:
            if player.name == player_1:
                player.games_played += 1
                player.draws +=1
                player.goals_for += score_1
                player.goals_for += score_2
                
            elif player.name == player_2:
                player.games_played += 1
                player.draws +=1
                player.goals_for += score_2
                player.goals_for += score_1
    
    return players
    
    
# updates objects (player stats in this case)
def update_players():
    new_fixtures = get_new_fixtures()
    players = pickle_loader()
    
    for index, row in new_fixtures.iterrows():
        player_1 = row['Player 1']
        player_2 = row['Player 2']
        score_1 = row['Player 1 Score']
        score_2 = row['Player 2 Score']
        players = match_update(player_1, player_2, score_1, score_2, players)
        
    return players  


# pulls league table from google spreadsheets
def load_table():
    sht = intialize_spreadsheet()
    
    worksheet = sht.get_worksheet(0)
    array = worksheet.get_all_records()
    table = pd.DataFrame(array)
    table = table[['Player', 'Games Played', 'Wins', 'Draws', 'Losses', 'Points', 'Goals For', 'Goals Against', 'Goal Difference']]
    
    return table
    
    
# edits a local league table dataframe
def dataframe_editor():
    players = update_players()
    df = load_table()
    
    for player in players:
        df.loc[(df['Player'] == player.name), 'Games Played'] = player.games_played
        df.loc[(df['Player'] == player.name), 'Wins'] = player.wins
        df.loc[(df['Player'] == player.name), 'Draws'] = player.draws
        df.loc[(df['Player'] == player.name), 'Losses'] = player.losses
        df.loc[(df['Player'] == player.name), 'Points'] = player.points
        df.loc[(df['Player'] == player.name), 'Goals For'] = player.goals_for
        df.loc[(df['Player'] == player.name), 'Goals Against'] = player.goals_against
        df.loc[(df['Player'] == player.name), 'Goal Difference'] = player.goal_difference
    
    return df, players


# updates league table on google spreadsheets using the local table and stores objects
def table_pickle_writer():
    df, players = dataframe_editor()
    sht = intialize_spreadsheet()
    
    worksheet = sht.get_worksheet(0)
    cell_list = worksheet.range('A2:I6')
    
    for cell in cell_list:
        val = df.iloc[cell.row-2,cell.col-1]
        cell.value = val

    worksheet.update_cells(cell_list)
    
    with open('object_states.pkl', 'wb') as output:
        pickle.dump(players, output)


# records index of last row of fixtures table
def log_writer():
    fixtures = load_fixtures()
    
    fix_len = open('fixtures_log.log', 'w+')
    fix_len.write(str(len(fixtures)))
    fix_len.close()
    

# run main function
def main():
    table_pickle_writer()
    log_writer()
    

main()

