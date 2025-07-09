
def calculate_kelly_fraction(winrate, reward_risk, conservative_factor=0.5):
    """
    Calculates Kelly position size fraction.

    :param winrate: float (e.g. 0.75 for 75%)
    :param reward_risk: TP% / SL% (e.g. 1.5/7.0 = 0.214)
    :param conservative_factor: fraction of Kelly to use (0.5 = 50%)
    :return: position sizing fraction (0.0 to 1.0)
    """
    loss_rate = 1 - winrate
    b = reward_risk
    try:
        raw_kelly = (b * winrate - loss_rate) / b
        return max(0.0, raw_kelly * conservative_factor)
    except ZeroDivisionError:
        return 0.0
