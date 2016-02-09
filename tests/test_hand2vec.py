





import os
import hand2vec
from traceback import print_exc

# def test_convert_with_unicode_in_file():

#     hands = hand2vec.get_hands(\
#    'hands/HH20150820_T1297824035_No_Limit_Holdem_2647_+_053.txt'))

#     hand2vec.write_gamestates_to_csv(hands,\
#         'vecs/HH20150820_T1297824035_No_Limit_Holdem_2647_+_053.txt')

def test_convert_all_hands():

    for f in os.listdir('hands/'):
        if os.path.exists('json/'+os.path.splitext(f)[0]+'.json'):
            continue

        print f
        try:
            hands = hand2vec.get_hands('hands/'+f)
            print 'saving', f, 'to json'
            hand2vec.to_json(hands, f)
        except Exception as e:
            print_exc()
            break




