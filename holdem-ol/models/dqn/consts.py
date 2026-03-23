"""
Schema keys
"""
SCHEMA = 'schema'

"""
Sub network keys
"""
COMM_CARD_LSTM = 'comm_cards_lstm'
ACTS_TRANSFORMER = 'acts_transformer'
ACTS_LSTM = 'acts_lstm'
ADVANTAGE_FCL = 'advantage_fcl'
VALUE_FCL = 'value_fcl'

# Player statics field size:
# [
#  bf_bet_mean, bf_bet_std,
#  f_bet_mean, f_bet_std,
#  t_bet_mean, t_bet_std,
#  r_bet_mean, r_bet_std,
#  payoff_mean, payoff_std,
#  bf_fold_rate, f_fold_rate, t_fold_rate, r_fold_rate,
#  ]
USER_STATICS_INFO_SIZE = 14
