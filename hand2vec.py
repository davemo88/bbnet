"""

train to predict own moves and also other players moves as separate models

combine for final model !

give distribution over cards in opponent's hand lol
or ranking of distributions ?

"""

import re
import os
import codecs
import string
import json
from copy import deepcopy


PLAYER = 'jaimestaples'

STAGES = ['HOLE CARDS', 'FLOP','TURN','RIVER',]#'SHOW DOWN']

POSITIONS = ['btn','sb','bb','utg','ep','emp','mp','hjck','co']

CARDS = ['As','Ks','Qs','Js','Ts','9s','8s','7s','6s','5s','4s','3s','2s',
         'Ah','Kh','Qh','Jh','Th','9h','8h','7h','6h','5h','4h','3h','2h',
         'Ad','Kd','Qd','Jd','Td','9d','8d','7d','6d','5d','4d','3d','2d',
         'Ac','Kc','Qc','Jc','Tc','9c','8c','7c','6c','5c','4c','3c','2c',]

IGNORE_RE = '|'.join(['has timed out',
          'is disconnected',
          'is connected',
          'is sitting out',
          'has returned',
          '.+ said, ".*"',
          're-buys and receives',
          'takes the add-on and receives',
          'collected \d+ from pot',
          'doesn\'t show hand',
          'adds \d+ chips'])

GAMESTATE_DIMESIONS = [
    'tournament_id',
    'hand_id',
    'hole_cards',
    'position',
    'community_cards',
    'ante',
    'small_blind',
    'big_blind',
    'pot'
]

POSITION_DIMENSIONS = [
    'player',
    'folds',
    'posts',
    'checks',
    'calls',
    'bets',
    'raises',
    'chips'
]

def to_json(gamestates, filename):

    dest = 'json/'+os.path.splitext(filename)[0]+'.json'

    with open(dest, 'wb') as taco:
        for g in gamestates:
            json.dump(g,taco)
            taco.write('\n')

def get_hands(hh_file):
    """
        this function will return a dictionary
        keys are the unique hand id
        values are the sequence of gamestate vectors for that hand
        gamestate vectors sparse representation

        gamestate vector encode all data about current gamestate:
        for each seat at the table:
            player
            stack size
            in the hand / folded
            position
            actions - fold binary, raise bet call int
            cards if shown 52
        active player's hole cards 52
        community cards 52
        pot size
        small blind
        big bling
        ante
        total players
        players remaining
        prize structure / bubble <-- might have to use heurustic or estimate this

    """

    gamestates = []

    with codecs.open(hh_file, 'r', 'utf-8-sig') as lines:

        while(True):
            next_hand = get_next_hand(lines)
            if next_hand:
                gamestates.extend(next_hand)
            else:
                break

    return gamestates

def get_next_hand(lines):
    """

    """

    gamestates = []

    gs, player_pos, line = get_initial_gamestate(lines)
    if not gs:
        return gamestates

    print gs['hand_id']

## action preflop and on each street
    for stage in STAGES:
        # print stage
        while(not re.match('\*\*\* {} \*\*\*'.format(stage), line)):
            if re.match('Uncalled bet|\*\*\* SUMMARY \*\*\*', line):
## the hand is over                
                end_of_hand(lines)
                return gamestates
            else:
                if re.search(IGNORE_RE, line):
                    line = lines.next().strip()
                    continue
                player, action, amount = get_player_action_amount(line)
                gs['{}_{}'.format(player_pos[player],action)] = amount
                if action in ['bets','raises','calls','posts']:
                    gs[player_pos[player]+'_chips'] -= amount
                gamestates.append(deepcopy(gs))
                gs.pop('{}_{}'.format(player_pos[player],action))
                line = lines.next().strip()
## we broke out
        if stage == 'HOLE CARDS':
            line = lines.next().strip()
            gs['hole_cards'] = line.split(' [')[-1][:-1]
            gamestates.append(deepcopy(gs))
        if stage == 'FLOP':
                gs['community_cards'] = line.split(' [')[-1][:-1].split()
                gamestates.append(deepcopy(gs))
        elif stage in ['TURN', 'RIVER']:
            gs['community_cards'] += ' '+line.split('] [')[-1][:-1]
            gamestates.append(deepcopy(gs))

        line = lines.next().strip()

    return gamestates

def get_initial_gamestate(lines):

## beginning of a new hand
    for line in lines:
        if re.match('PokerStars Hand #\d+', line):
            line = line.strip()
            gs = dict()
# hand_id = re.search('\d+', line).group()
            gs['hand_id'] = re.search('\d+', line).group()
            gs['tournament_id'] = re.search('Tournament #\d+',line).group()[len('Tournament #'):]
## blind levels
            blinds = re.search('Level .+ \(\d+/\d+\)', line).group()
            gs['small_blind'] = int(re.search('\(\d+', blinds).group()[1:])
            gs['big_blind'] = int(re.search('\d+\)', blinds).group()[:-1])
            line = lines.next().strip()
## get the number of seats at the table
            num_seats = int(re.search('\d+-max', line).group().replace('-max',''))
            if num_seats > 9:
                raise Exception('too many players at the table')
## get the seat that has the button button
            button = int(re.search('Seat #\d is the button',
                                   line).group()[6])
## for convenient access to player positions
            player_pos = {}
## the players and the antes             
## get the players and chips for each seat
## e.g.:
## Seat 1: liudasas (3125 in chips)
            while (True):
                line = lines.next().strip()
                if re.match('Seat', line):
                    seat = (int(re.search('\d+', line).group()) - button) % 9
    ## seemingly no restrictions on player names so have to be careful               
                    gs[POSITIONS[seat]+'_player'] = line[len('Seat N: '):-line[::-1].index('(')-2]
                    gs[POSITIONS[seat]+'_chips'] = int(re.search('\d+ in chips', line).group()[:-9])
                    player_pos[gs[POSITIONS[seat]+'_player']] = POSITIONS[seat]
                    if gs[POSITIONS[seat]+'_player'] == PLAYER:
                        positions = POSITIONS[seat]
                elif re.search(IGNORE_RE,line):
                    continue
                else:
                    break

            return gs, player_pos, line
## no hands in input            
    return [None] * 3

def get_player_action_amount(line):
    """
        given a action containing a player gamestate update,
        return the player, the action, and the amount
    """
    print line
    player = line.split(': ')[0]
    action = line.split(': ')[1].split()[0]
    if action in ['folds', 'checks']:
        amount = 1
    else:
        amount = int(line.replace(' and is all-in','').split()[-1])
    
    return player, action, amount

def end_of_hand(lines):
    """
        go to the next line of whitespace in lines
    """   
    while  lines.next().strip() != '':
        continue