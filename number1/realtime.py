import asyncio
import traceback
import time
from exchange import Exchange

# 設定 --------------------------
API_KEY = '96wCZAuaiiCuCwz82ds8ym'
API_SECRET = 'onNARBPBbcElLAr6Nd6WZ4moj5nz3UzADlvLekIH+64='
INTERVAL_SECONDS = 5
# 設定 --------------------------

class Bot():

    # 板情報アップデート用
    board_temp = []
    board = {'mid_price': 0, 'asks': {}, 'bids': {}}
    best_ask = 0
    best_bid = 0

    def __init__(self, api_key, api_secret):
        # 取引所インスタンスへAPIキー・SECRETをセット
        self.exchange = Exchange(api_key=api_key, api_secret=api_secret)
        self.exchange.product_code = 'FX_BTC_JPY'
        self.exchange.minute_to_expire = 1

        # タスクの設定及びイベントループの開始
        loop = asyncio.get_event_loop()
        tasks = asyncio.gather(            
            self.exchange.subscribe(self.realtime),
            self.trade(),
        )
        loop.run_until_complete(tasks)

    async def trade(self):
        while True:
            if self.best_ask > 0:
                print(self.best_ask)
                print('trade!')
            await asyncio.sleep(INTERVAL_SECONDS)

    # リアルタイムデータのコールバック
    async def realtime(self, data):
        if data['channel'] == 'lightning_board_snapshot_FX_BTC_JPY':
            message = data['message']
            self.board_temp = message
            self.best_ask = int(message['asks'][0]['price'])
            self.best_bid = int(message['bids'][0]['price'])
            self.board = self.reformat_board(message)

        if data['channel'] == 'lightning_board_FX_BTC_JPY':
            if len(self.board_temp) > 0:
                message = data['message']
                if len(self.board_temp) > 0:
                    self.board = self.update_board(message, self.board)
                    self.best_bid, self.best_ask = self.update_best_quote(self.board)
                # BEST_BID, BEST_ASK, SPREAD
                # print(self.best_bid, self.best_ask, self.best_ask - self.best_bid)

        await asyncio.sleep(0)

    # ストリーミングデータを板情報更新用の辞書データへ整形
    def reformat_board(self, data):
        board = {'mid_price': 0, 'asks': {}, 'bids': {}}
        for key in data.keys():
            if key == 'mid_price':
                board[key] = int(data[key])
            else:
                board[key] = {int(quote['price']): float(quote['size']) for quote in data[key]}

        return board

    # 板情報を更新
    def update_board(self, data, board):
        for key in data.keys():
            if key == 'mid_price':
                board[key] = int(data[key])
            else:
                for quote in data[key]:
                    price = int(quote['price'])
                    size = float(quote['size'])
                    if price in board[key]:
                        if size == 0.0:
                            # DELETE
                            del board[key][price]
                        else:
                            # UPDATE
                            board[key][price] = size
                    else:
                        if size > 0.0:
                            # INSART
                            board[key].update({price: size})
                # SORT
                if key == 'asks':
                    board[key] = {key: value for key, value in sorted(board[key].items())}
                elif key == 'bids':
                    board[key] = {key: value for key, value in sorted(board[key].items(), key=lambda x: -x[0])}

        return board

    def update_best_quote(self, board):
        if len(self.board) == 0:
            return

        best_ask = 0
        best_bid = 0
        for ask in board['asks'].keys():
            best_ask = ask
            break

        for bid in board['bids'].keys():
            best_bid = bid
            break

        return best_bid, best_ask

if __name__ == '__main__':
    bot = Bot(api_key=API_KEY, api_secret=API_SECRET)