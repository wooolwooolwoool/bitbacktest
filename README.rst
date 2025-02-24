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

How to use (GUI)
--------
Start panel app

.. code-block:: bash
        $ ./start_panel.sh

Access to http://localhost:5006/main

How to use (CLI)
--------
See example folder. example/bayse_backtest_BB.py

#. Create Class. See src/bitbacktest/signal_generator.py and trade_executor.py

#. Prepare data and params.

        .. code-block:: python

                # Read data for test
                price_data = read_prices_from_sheets(data_path,
                                        datetime_range, data_interval, use_cache=True)

                # Set parameters. Define the parameters you want to optimize using the Integer and Real class.
                target_params = {
                        'window_size': Integer(10, 500),
                        'num_std_dev': Real(1, 4),
                        'buy_count_limit': 5,
                        "one_order_quantity": 0.001
                }
                start_cash = 1e6

                # Prepare Strategy and Backtester
                market = BacktestMarket(price_data, fee_rate=0)
                signal_gene = BollingerBandsSG()
                trade_exec = SpreadOrderExecutor()
                strategy = BacktestStrategy(market, signal_gene, trade_exec)

#. Execute Optimize.

        .. code-block:: python
                # execute optimize
                backtester = BayesianBacktester(strategy)

                # Execute backtest
                best_value, best_param = backtester.backtest(target_params, start_cash, start_coin=0.01, n_calls=10)


#. Execute backtest.

        .. code-block:: python

                strategy.reset_all(best_param, start_cash)
                portfolio_result = strategy.backtest(hold_params=["upper_band", "lower_band"])
                # Plot graph
                strategy.create_backtest_graph(backend="matplotlib")

#. Create yaml file for AWS.

        .. code-block:: bash

                $ python3 app/aws_build/build_all.py -s MACDSG -t NormalExecutor -o CloudFormationBB.yaml

#. Deploy to AWS CloudFormationBB.yaml to CloudFormation

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
