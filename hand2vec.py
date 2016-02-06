"""

train to predict own moves and also other players moves as separate models

combine for final model !

give distribution over cards in opponent's hand lol
or ranking of distributions ?

"""

import re
import codecs
import csv


PLAYER = 'jaimestaples'

POSITIONS = ['btn','sb','bb','utg','ep','emp','mp','hjck','co']

CARDS = ['As','Ks','Qs','Js','Ts','9s','8s','7s','6s','5s','4s','3s','2s',
         'Ah','Kh','Qh','Jh','Th','9h','8h','7h','6h','5h','4h','3h','2h',
         'Ad','Kd','Qd','Jd','Td','9d','8d','7d','6d','5d','4d','3d','2d',
         'Ac','Kc','Qc','Jc','Tc','9c','8c','7c','6c','5c','4c','3c','2c',]


def flatten(dictionary, parent_keys=[]):
    """
        http://stackoverflow.com/questions/6027558/flatten-nested-python-dictionaries-compressing-keys
    """
    items = []
    for k,v in dictionary.items():
        if issubclass(v.__class__,dict):
            items.extend(flatten(v,parent_keys+[k]).items())
        else:
            if parent_keys:
                items.append(('{}_{}'.format('_'.join(parent_keys),k),v))
            else:
                items.append((k,v))
    return dict(items)

# class Hand(list):
#     """

#     """

class Gamestate(dict):
    """
        a hand is represented by a series of gamestates

    """

    def __init__(self, **kwargs):

        super(Gamestate, self).__init__()

        self['tournament_id'] = 0
        self['hand_id'] = 0
        self['community_cards'] = Deck()
        self['ante'] = 0
        self['small_blind'] = 0
        self['big_blind'] = 0
        self['pot'] = 0

        for p in POSITIONS:
            self[p] = Seatstate()

        for k in kwargs:
            self[k] = kwargs[k]

class Seatstate(dict):

    def __init__(self, **kwargs):
        """
            seat about a particular seat at the table
        """

        super(Seatstate, self).__init__()

        self['player'] = 0
        self['ante'] = 0
        self['posts'] = 0
        self['folds'] = 0
        self['checks'] = 0
        self['bets'] = 0
        self['calls'] = 0
        self['raises'] = 0
        # self['collected'] = 0
        self['chips'] = 0
        self['cards'] = Deck()

        for k in kwargs:
            self[k] = kwargs[k]

class Deck(dict):

    def __init__(self, **kwargs):

        super(Deck, self).__init__()

        for card in CARDS:
            self[card] = 0

        for k in kwargs:
            self[k] = kwargs[k]

def write_gamestates_to_csv(gamestates, out='out.csv'):

    with open(out, 'wb') as outfile:

        dw = csv.DictWriter(outfile, flatten(Gamestate()).keys())
        dw.writeheader()
        for gs in gamestates:
            dw.writerow(flatten(gs))

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

    gs, player_pos = get_initial_gamestate(lines)
    if not gs:
        return gamestates

## here is the first gamestate we yield
## ante
    if gs['ante']:
        for p in POSITIONS:
            gs[p]['antes'] = gs['ante']            
            # yield gs
            gamestates.append(gs)
            gs[p]['antes'] = 0

## small blind
    gs['sb']['posts'] = gs['small_blind']
    gs['sb']['chips'] -= gs['small_blind']
    # yield gs
    gamestates.append(gs)
    gs['sb']['posts'] = 0

## big blind
    gs['bb']['posts'] = gs['big_blind']
    gs['bb']['chips'] -= gs['big_blind']
    # yield gs
    gamestates.append(gs)
    gs['bb']['posts'] = 0

## skip  a line for the big blind
    line = lines.next().strip()
## hole cards                
    line = lines.next().strip()
    assert line == '*** HOLE CARDS ***'
    line = lines.next().strip()

    player = line.split(' [')[0][len('Dealt to '):]
    card1, card2 = line.split(' [')[-1][:-1].split()
    gs[player_pos[player]]['cards'][card1] = 1
    gs[player_pos[player]]['cards'][card2] = 1
    # yield gs
    gamestates.append(gs)

## preflop action
    line = lines.next().strip()
    while not re.match('\*\*\* FLOP \*\*\*|Uncalled', line):
## e.g.
## H0RRoR_RiVeR: raises 40 to 60
        player, action, amount = get_player_action_amount(line)
        gs[player_pos[player]][action] = amount
        # yield gs
        gamestates.append(gs)
        gs[player_pos[player]][action] = 0

        line = lines.next().strip()

## everybody folded
    if re.match('Uncalled', line):
        end_of_hand(lines)
        return gamestates
## flop
## e.g.
## *** FLOP *** [Td 3d 4d]
    card1, card2, card3 = line.split(' [')[-1][:-1].split()
    gs['community_cards'][card1] = 1
    gs['community_cards'][card2] = 1
    gs['community_cards'][card3] = 1
    # yield gs
    gamestates.append(gs)

## flop action                
    line = lines.next().strip()
    while not re.match('\*\*\* TURN \*\*\*|Uncalled', line):
        player, action, amount = get_player_action_amount(line)
        gs[player_pos[player]][action] = amount
        # yield gs
        gamestates.append(gs)
        gs[player_pos[player]][action] = 0

        line = lines.next().strip()

## everybody folded
    if re.match('Uncalled', line):
        end_of_hand(lines)                  
        return gamestates
## turn
## e.g. 
## *** TURN *** [Td 3d 4d] [Tc]
    gs['community_cards'][line.split('] [')[-1][:-1]] = 1
    # yield gs
    gamestates.append(gs)    

## turn action                
    line = lines.next().strip()
    while not re.match('\*\*\* RIVER \*\*\*|Uncalled', line):
        player, action, amount = get_player_action_amount(line)
        gs[player_pos[player]][action] = amount
        # yield gs
        gamestates.append(gs)
        gs[player_pos[player]][action] = 0

        line = lines.next().strip()

## everybody folded
    if re.match('Uncalled', line):
        end_of_hand(lines)                    
        return gamestates
## river
## e.g. 
##*** RIVER *** [Kd 4s Ts 5h] [Ah]
    gs['community_cards'][line.split('] [')[-1][:-1]] = 1
    # yield gs
    gamestates.append(gs)

## river action                
    line = lines.next().strip()
    while not re.match('\*\*\* SHOW DOWN \*\*\*|Uncalled', line):
        player, action, amount = get_player_action_amount(line)
        gs[player_pos[player]][action] = amount
        # yield gs
        gamestates.append(gs)
        gs[player_pos[player]][action] = 0

        line = lines.next().strip()

    return gamestates


def get_initial_gamestate(lines):

## beginning of a new hand
    for line in lines:
        if re.match('PokerStars Hand #\d+', line):

            line = line.strip()

            gs = Gamestate()

# hand_id = re.search('\d+', line).group()
            gs['hand_id'] = re.search('\d+', line).group()
            gs['tournament_id'] = re.search('Tournament #\d+',line).group()[len('Tournament #'):]

## what does ante look like? this is broken only works for sb bb
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

            line = lines.next().strip()
## get the players and chips for each seat                
## e.g.:
## Seat 1: liudasas (3125 in chips)
            while re.match('Seat',line):

                seat = (int(re.search('\d+', line).group()) - button) % 9
## spaces in player names so have to be careful                    
                gs[POSITIONS[seat]]['player'] = line.split(': ')[1].split(' (')[0]
                gs[POSITIONS[seat]]['chips'] = int(re.search('\d+ in chips', line).group()[:-9])

                player_pos[gs[POSITIONS[seat]]['player']] = POSITIONS[seat]

                line = lines.next().strip()

            return gs, player_pos
## no hands in input            
    return None, None


def get_player_action_amount(line):
    player = line.split(': ')[0]
    action = line.split(': ')[1].split()[0]
    if action not in ['folds', 'checks']:
        amount = int(line.split()[-1])
    else:
        amount = 1

    return player, action, amount


def end_of_hand(lines):
    line = lines.next()
    while line.strip() != '':
        line = lines.next()