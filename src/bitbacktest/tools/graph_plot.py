import matplotlib.pyplot as plt


def plot_bollinger_bands(df,
                         price_col='Price',
                         timestamp_col='Timestamp',
                         window=20,
                         sigma_levels=[1, 2, 3],
                         save_path='bollinger_bands.png'):
    """
    DataFrameに基づいてボリンジャーバンドをプロットする関数。

    Parameters:
        df (pd.DataFrame): タイムスタンプとビットコイン価格データを含むDataFrame。
        price_col (str): 価格データの列名。デフォルトは 'Price'。
        timestamp_col (str): タイムスタンプデータの列名。デフォルトは 'Timestamp'。
        window (int): 移動平均のウィンドウサイズ。デフォルトは20。
        sigma_levels (list of int): プロットするシグマレベル。デフォルトは [1, 2, 3]。
        save_path (str): plt.show() が失敗した場合に画像を保存するパス。デフォルトは 'bollinger_bands.png'。
    """
    # 移動平均と標準偏差の計算
    df['MA'] = df[price_col].rolling(window=window).mean()
    df['STD'] = df[price_col].rolling(window=window).std()

    # シグマレベルに応じてバンドを計算
    for sigma in sigma_levels:
        df[f'Upper_{sigma}sigma'] = df['MA'] + (df['STD'] * sigma)
        df[f'Lower_{sigma}sigma'] = df['MA'] - (df['STD'] * sigma)

    # プロット
    plt.figure(figsize=(12, 6))
    plt.plot(df[timestamp_col],
             df[price_col],
             label='BTC Price',
             color='black')
    plt.plot(df[timestamp_col],
             df['MA'],
             label=f'Moving Average (window={window})',
             color='blue')

    colors = ['green', 'orange', 'red']
    linestyles = ['--', '-', ':']

    for i, sigma in enumerate(sigma_levels):
        plt.plot(df[timestamp_col],
                 df[f'Upper_{sigma}sigma'],
                 label=f'Upper {sigma}σ',
                 color=colors[i],
                 linestyle=linestyles[i])
        plt.plot(df[timestamp_col],
                 df[f'Lower_{sigma}sigma'],
                 label=f'Lower {sigma}σ',
                 color=colors[i],
                 linestyle=linestyles[i])
        plt.fill_between(df[timestamp_col],
                         df[f'Upper_{sigma}sigma'],
                         df[f'Lower_{sigma}sigma'],
                         color=colors[i],
                         alpha=0.1)

    plt.title('Bitcoin Price with Bollinger Bands')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()

    # plt.show() に失敗した場合に画像を保存
    try:
        plt.show()
    except Exception as e:
        print(
            f"plt.show() failed with error: {e}. Saving the plot as an image.")
        plt.savefig(save_path)
        print(f"Plot saved as {save_path}")


def plot_moving_averages(df,
                         price_col='BTC_Price',
                         timestamp_col='Timestamp',
                         short_window=20,
                         long_window=50,
                         save_path='moving_averages.png'):
    """
    DataFrameに基づいて短期と長期の移動平均線をプロットする関数。

    Parameters:
        df (pd.DataFrame): タイムスタンプとビットコイン価格データを含むDataFrame。
        price_col (str): 価格データの列名。デフォルトは 'BTC_Price'。
        timestamp_col (str): タイムスタンプデータの列名。デフォルトは 'Timestamp'。
        short_window (int): 短期移動平均のウィンドウサイズ。デフォルトは20。
        long_window (int): 長期移動平均のウィンドウサイズ。デフォルトは50。
        save_path (str): plt.show() が失敗した場合に画像を保存するパス。デフォルトは 'moving_averages.png'。
    """
    # 短期移動平均と長期移動平均を計算
    df['Short_SMA'] = df[price_col].rolling(window=short_window).mean()
    df['Long_SMA'] = df[price_col].rolling(window=long_window).mean()

    # プロット
    plt.figure(figsize=(12, 6))
    plt.plot(df[timestamp_col],
             df[price_col],
             label='BTC Price',
             color='black')
    plt.plot(df[timestamp_col],
             df['Short_SMA'],
             label=f'Short SMA (window={short_window})',
             color='blue')
    plt.plot(df[timestamp_col],
             df['Long_SMA'],
             label=f'Long SMA (window={long_window})',
             color='orange')

    plt.title('Bitcoin Price with Short and Long Moving Averages')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()

    # plt.show() に失敗した場合に画像を保存
    try:
        plt.show()
    except Exception as e:
        print(
            f"plt.show() failed with error: {e}. Saving the plot as an image.")
        plt.savefig(save_path)
        print(f"Plot saved as {save_path}")


def plot_macd(df,
              price_col='Price',
              timestamp_col='Timestamp',
              short_window=12,
              long_window=26,
              signal_window=9,
              save_path='price_and_macd.png'):
    """
    上部に価格のグラフ、下部にMACDのグラフをプロットする関数。

    Parameters:
        df (pd.DataFrame): タイムスタンプとビットコイン価格データを含むDataFrame。
        price_col (str): 価格データの列名。デフォルトは 'BTC_Price'。
        timestamp_col (str): タイムスタンプデータの列名。デフォルトは 'Timestamp'。
        short_window (int): 短期移動平均のウィンドウサイズ。デフォルトは12。
        long_window (int): 長期移動平均のウィンドウサイズ。デフォルトは26。
        signal_window (int): シグナル線のウィンドウサイズ。デフォルトは9。
        save_path (str): plt.show() が失敗した場合に画像を保存するパス。デフォルトは 'price_and_macd.png'。
    """
    # 短期および長期の移動平均を計算
    df['Short_MA'] = df[price_col].ewm(span=short_window, adjust=False).mean()
    df['Long_MA'] = df[price_col].ewm(span=long_window, adjust=False).mean()

    # MACDラインとシグナルラインを計算
    df['MACD'] = df['Short_MA'] - df['Long_MA']
    df['Signal'] = df['MACD'].ewm(span=signal_window, adjust=False).mean()

    # プロットのレイアウトを設定
    fig, (ax1, ax2) = plt.subplots(2,
                                   1,
                                   figsize=(12, 8),
                                   gridspec_kw={'height_ratios': [3, 1]})

    # 上部に価格グラフをプロット
    ax1.plot(df[timestamp_col],
             df[price_col],
             label='BTC Price',
             color='black')
    ax1.set_title('Bitcoin Price')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price')
    ax1.legend()

    # 下部にMACDグラフをプロット
    ax2.plot(df[timestamp_col], df['MACD'], label='MACD', color='blue')
    ax2.plot(df[timestamp_col], df['Signal'], label='Signal', color='red')
    ax2.axhline(0, color='gray', linestyle='--', linewidth=1)  # y=0 のラインを引く
    ax2.set_title('MACD')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Value')
    ax2.legend()

    # plt.show() に失敗した場合に画像を保存
    try:
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(
            f"plt.show() failed with error: {e}. Saving the plot as an image.")
        plt.savefig(save_path)
        print(f"Plot saved as {save_path}")
