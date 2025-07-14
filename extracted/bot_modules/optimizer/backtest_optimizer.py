
def grid_search_backtest(config_template, param_grid, backtester_func):
    best_result = None
    best_config = None

    for params in param_grid:
        cfg = config_template.copy()
        cfg["entry"]["threshold"] = params["entry_threshold"]
        cfg["exit"]["trailing_ratio"] = params["exit_trailing"]

        result = backtester_func(cfg)

        if not best_result or result["pnl"] > best_result["pnl"]:
            best_result = result
            best_config = cfg

    return best_config, best_result
