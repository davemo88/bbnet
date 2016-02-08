





import os
import hand2vec
from traceback import print_exc

HAND_DIR = 'hands/'
VEC_DIR = 'vecs/'

# def test_convert_with_unicode_in_file():

#     hands = hand2vec.get_hands(\
#    'hands/HH20150820_T1297824035_No_Limit_Holdem_2647_+_053.txt'))

#     hand2vec.write_gamestates_to_csv(hands,\
#         'vecs/HH20150820_T1297824035_No_Limit_Holdem_2647_+_053.txt')

def test_convert_all_hands():

    for f in os.listdir(HAND_DIR):
        if os.path.exists(VEC_DIR+f):
            continue

        print f
        try:
            hands = hand2vec.get_hands(HAND_DIR+f)
            print 'writing {} to vecs'.format(f)
            hand2vec.write_gamestates_to_csv(hands, VEC_DIR+f)
            # hand2vec.write_gamestates_to_csv(hands, '{}/all.csv'.format(VEC_DIR))
        except Exception as e:
            print_exc()
            break




