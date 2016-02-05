"""

"""

import re
import codecs

def to_vectors(hh_file, out_file="out.csv"):
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

    records = {}

    with codecs.open(hh_file, 'r', 'utf-8-sig') as lines:
        with open(out_file,'wb') as out:

            for line in lines:

## beginning of a new hand
                if re.match('^PokerStars Hand #\d+', line):

                    hand_id = re.search('\d+', line).group()

                    records[hand_id] = {}

                    blinds = re.search('Level .+ (\d+/\d+)', line).group()
                    big_blind = re.search('(\d+'), blinds).group()[1:]
                    small_blind = re.search('\d+)'), blinds).group()[:-1]
                    records[hand_id]['big_blind'] = big_blind
                    records[hand_id]['small_blind'] = small_blind

## get the position of the person in the button
                    line = lines.next()
                    button = int(re.search('Seat #\d is the button',
                                           line).group()[7])

                    records[hand_id]['button'] = button

## get the number of seats at the table
                    num_seats = int(re.search('\d+-max', line).group().replace('-max',''))

                    records[hand_id]['num_seats'] = num_seats

                    player_seat = {}
                    seat_chips = {}

                    for i in range(num_seats):
                        line = lines.next()
                        player = line[line.index(':')+1:].split()[0]
                        seat = int(re.search('\d+', line).group()) % button
                        chips = int(re.search('\d+ in chips', line).group()[-9])
                        player_seat[player] = seat
                        seat_chips[seat] = chips

                    for k in starting_chips:

                        records[hand_id][''] = starting_chips[k]


    

