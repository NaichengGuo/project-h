""" Register rule-based models or pre-trianed models
"""
from rlcard.models.registration import register, load

register(
    model_id='limit-holdem-rule-v1',
    entry_point='rlcard.models.limitholdem_rule_models:LimitholdemRuleModelV1')
