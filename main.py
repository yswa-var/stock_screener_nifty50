import pandas as pd
import pandas_datareader as web
from yahoo_fin import stock_info as si
import datetime as dt

tickers = si.tickers_nifty50()
start = dt.datetime.now() - dt.timedelta(days=365)
end = dt.datetime.now()

sp500 = web.DataReader('^GSPC', 'yahoo', start, end)
sp500['Pct Change'] = sp500['Adj Close'].pct_change()
sp500_return = (sp500['Pct Change'] + 1).cumprod()[-1]

return_list = []
final_df = pd.DataFrame(columns=['Ticker', 'Latest_Price', 'Score', "PE_ratio", 'PEG_Ratio','SMA_150','SMA_200','52_Week_Low', '52_Week_high'])

counter =0


for ticker in tickers:
    df = web.DataReader(ticker, 'yahoo', start, end)
    df.to_csv(f'stock_data/{ticker}.csv')

    df['Pct Change'] = df['Adj Close'].pct_change()
    stock_return = (df['Pct Change'] + 1).cumprod()[-1]

    returns_compared = round((stock_return / sp500_return), 2)
    return_list.append(returns_compared)

    counter+=1
    if counter == 30:
        break

best_performer = pd.DataFrame(list(zip(tickers, return_list)), columns=['Ticker', 'Returns Compared'])
best_performer['Score'] = best_performer['Returns Compared'].rank(pct=True) * 100
best_performer = best_performer[best_performer['Score'] >= best_performer['Score'].quantile(0.8)]

for ticker in best_performer['Ticker']:
    try:
        df = pd.read_csv(f'stock_data/{ticker}.csv', index_col=0)
        moving_averages = [150, 200]
        for ma in moving_averages:
            df['SMA_' + str(ma)] = round(df['Adj Close'].rolling(window=ma).mean(), 2)
        latest_price = df['Adj Close'][-1]
        pe_ratio = float(si.get_quote_table(ticker)['PE Ratio (TTm)'])
        peg_ratio = float(si.get_quote_table(ticker)[1][4])
        moving_averages_150 = df['SMA_150'][-1]
        moving_averages_200 = df['SMA_200'][-1]
        low_52week = round(min(df['Low'][-(52 * 5):]), 2)
        high_52week = round(max(df['High'][-(52 * 5):]), 2)
        score = round(best_performer[best_performer['Ticker'] == ticker]['Score'].tolist()(0))

        con01 = latest_price > moving_averages_150 > moving_averages_200
        con02 = latest_price >= (1.3 * low_52week)
        con03 = latest_price >= (0.75 * high_52week)
        con04 = pe_ratio < 40
        con05 = peg_ratio < 2

        if con01 and con02 and con03 and con04 and con05:
            final_df = final_df.append({'Ticker': ticker,
                                        'Latest': latest_price,
                                        'Score': score,
                                        'PE_Ratio': pe_ratio,
                                        'PEG_Ratio': peg_ratio,
                                        'SMA_150': moving_averages_150,
                                        'SMA_200': moving_averages_200,
                                        '52_Week_Low': low_52week,
                                        '52_Week_high': high_52week}, ignore_index=True)
    except Exception as e:
        print(f"{e} from {ticker}")

final_df.sort_values(by='Score', ascending=False)
pd.set_option('display.max_columns',10)

