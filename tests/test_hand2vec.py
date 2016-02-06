





import hand2vec

hands = hand2vec.get_hands('hands/HH20151008_T1336933522_No_Limit_Holdem_100_+_9.txt')

hand2vec.write_gamestates_to_csv(hands)