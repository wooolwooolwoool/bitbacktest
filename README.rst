===========
BitBacktest
===========


.. image:: https://img.shields.io/pypi/v/bitbacktest.svg
        :target: https://pypi.python.org/pypi/bitbacktest

.. image:: https://img.shields.io/travis/wooolwoool@gmail.com/bitbacktest.svg
        :target: https://travis-ci.com/wooolwoool@gmail.com/bitbacktest

.. image:: https://readthedocs.org/projects/bitbacktest/badge/?version=latest
        :target: https://bitbacktest.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status




A package for backtesting Bitcoin trading strategies.


* Free software: MIT license
* Documentation: https://bitbacktest.readthedocs.io.


Features
--------

* TODO


Install
--------

Please git clone.

How to use
--------
See example folder

#. Create Strategy Class. See src/bitbacktest/strategy.py

#. Tuning parameter. See example/bayse_backtest_BB.py

        .. code-block:: python

                # Read data for test
                price_data = read_prices_from_sheets("my_data/BitCoinPrice_interp.xlsx",
                                        ["202404", "202405", "202406", "202407"], 60, use_cache=True)

                # Set parameters
                target_params = {
                'window_size': Integer(10, 500),  # 移動平均の期間
                'num_std_dev': Real(1, 4),   # 標準偏差の倍率
                'buy_count_limit': 5,
                "one_order_quantity": 0.001
                }
                start_cash = 1e6

                # Prepare Strategy and Backtester
                market = BacktestMarket(price_data)
                strategy = BollingerBandsStrategy(market)
                backtester = BayesianBacktester(strategy)

                # Execute backtest
                best_value, best_param = backtester.backtest(target_params, start_cash, n_calls=50)


#. Execute backtest. See example/backtest_BollingerBands.py

        .. code-block:: python

                # Read data for test
                price_data = read_prices_from_sheets("my_data/BitCoinPrice_interp.xlsx",
                                        ["202405", "202406", "202407", "202408"], 5, use_cache=True)

                # Set parameters
                market = BacktestMarket(price_data)
                strategy = BollingerBandsStrategy(market)
                param = {
                'window_size': 337,  # 移動平均の期間
                'num_std_dev': 1.46,   # 標準偏差の倍率
                'buy_count_limit': 5,
                "one_order_quantity": 0.001
                }
                start_cash = 1e6

                # Prepare Strategy
                strategy.reset_all(param, start_cash)

                # Execute backtest
                portfolio_result = strategy.backtest(hold_params=["upper_band", "lower_band"])
                print(portfolio_result)

                # Plot graph
                strategy.create_backtest_graph(backend="plotly")

        You can get result and graph.

        .. code-block:: bash

                $ python3 example/backtest_BollingerBands.py 
                100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 40320/40320 [00:11<00:00, 3645.49it/s]
                {'trade_count': 1700, 'cash': 281861.24843796133, 'position': 0.07344999999999792, 'total_value': 997966.1305175956}
                save to plot_signal.png

        .. image:: docs/result_plot_signal.png

#. Create yaml file for AWS.

        .. code-block:: bash
                
                $ python3 app/aws_build/build_all.py -d src -s BollingerBandsStrategy -o CloudFormationBB.yaml

#. Deploy to AWS CloudFormationBB.yaml to CloudFormation

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
