# coding: utf-8
import datetime
import time
import ccxt
from datetime import datetime as dt, timedelta
import functions

# 設定 ------------------------------------------------------------------------------#
API_KEY = '96wCZAuaiiCuCwz82ds8ym'
API_SECRET = 'onNARBPBbcElLAr6Nd6WZ4moj5nz3UzADlvLekIH+64='
LIMIT_TIME = 3 # seconds
LOT = 0.01 # BTC
SPREAD_DELTA = 5000 # 円
COIN = 'BTC'
PAIR = 'FX_BTC_JPY'
bitflyer = ccxt.bitflyer({'apiKey': API_KEY, 'secret': API_SECRET})
# 設定 ------------------------------------------------------------------------------#

# logging ---------------------------------------------------------------------------#
import logging
logger = logging.getLogger('LoggingTest')
logger.setLevel(10)
fh = logging.FileHandler('log/log_mm_bf_' + datetime.datetime.now().strftime('%Y%m%d') + '_' + datetime.datetime.now().strftime('%H%M%S') + '.log')
logger.addHandler(fh)
sh = logging.StreamHandler()
logger.addHandler(sh)
formatter = logging.Formatter('%(asctime)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)
sh.setFormatter(formatter)
# logging ---------------------------------------------------------------------------#

# 関数 ------------------------------------------------------------------------------#
#時間変換
def changetime(date):
    utc_split = dt(
        year=int(date[0:4]),month=int(date[5:7]),day=int(date[8:10]),
        hour=int(date[11:13]),minute=int(date[14:16]),second=int(date[17:19])
    )
    return (utc_split + timedelta(hours=+9))

def get_asset():
    while True:
        try:
            value = bitflyer.fetch_balance()
            break
        except Exception as e:
            logger.info(e)
            time.sleep(1)
    return value

# JPY証拠金を参照する関数
def get_colla():
    while True:
        try:
            value = bitflyer.privateGetGetcollateral()
            break
        except Exception as e:
            logger.info(e)
            time.sleep(1)
    return value

def get_mid_price():
  while True:
    try:
        value = bitflyer.public_get_getboard({ "product_code" : "FX_BTC_JPY" })
        value = value['mid_price']
        break
    except Exception as e:
        logger.info(e)
        time.sleep(1)
  return value

# 指値注文する関数
def limit(side, size, price):
    while True:
        try:
            value = bitflyer.create_order(PAIR, type = 'limit', side = side, amount = size, price = price)
            break
        except Exception as e:
            logger.info(e)
            time.sleep(0.5)
    return value

# 指定した注文idのステータスを参照する関数　例：{'id': 'JRF20200118-090846-009362', 'status': 'open', 'filled': 0.0, 'remaining': 0.01, 'amount': 0.01, 'price': 1001666.0}
def get_status(id):
  if PAIR == 'BTC/JPY':
      PRODUCT = 'BTC_JPY'
  else:
      PRODUCT = PAIR

  while True:
      try:
          value = bitflyer.private_get_getchildorders(params = {'product_code': PRODUCT, 'child_order_acceptance_id': id})[0]
          break
      except Exception as e:
          return None

  # APIで受け取った値を読み換える
  if value['child_order_state'] == 'ACTIVE':
      status = 'open'
  elif value['child_order_state'] == 'COMPLETED':
      status = 'closed'
  else:
      status = value['child_order_state']

  # 未約定量を計算する
  remaining = float(value['size']) - float(value['executed_size'])
  return {'id': value['child_order_acceptance_id'], 'status': status, 'filled': value['executed_size'], 'remaining': remaining, 'amount': value['size'], 'price': value['price']}

# 注文をキャンセルする関数
def cancel(id):
    try:
        value = bitflyer.cancelOrder(symbol = PAIR, id = id)
    except Exception as e:
        logger.info(e)
        # 指値が約定していた(=キャンセルが通らなかった)場合、
        # 注文情報を更新(約定済み)して返す
        value = get_status(id)
    return value
# 関数 ------------------------------------------------------------------------------#

# 変数 ------------------------------------------------------------------------------#
is_done = False # 稼働時にはFalseにする
order_available = True
sashine_time = None
buy_order_info = None # 例：{'info': {'child_order_acceptance_id': 'JRF20200118-084358-809988'}, 'id': 'JRF20200118-084358-809988'}
sell_order_info = None # 例：{'info': {'child_order_acceptance_id': 'JRF20200118-084358-809988'}, 'id': 'JRF20200118-084358-809988'}
buy_order_status = None
sell_order_status = None
buy_fiiled = 0
sell_fiiled = 0
remaining = 0
# 変数 ------------------------------------------------------------------------------#

while True:
  if order_available and buy_order_info == None and sell_order_info == None:
    print('initial')
    mid_price = get_mid_price()
    buy_price, sell_price = mid_price - SPREAD_DELTA, mid_price + SPREAD_DELTA
    buy_order_info = limit('BUY', LOT, buy_price)
    #sell_order_info = limit('SELL', LOT, sell_price)
    sashine_time = datetime.datetime.now()
    order_available = False
  elif order_available and current_position == 'buy':
    print('buy')
  elif order_available and current_position == 'sell':
    print('sell')

  now = datetime.datetime.now()
  if (now - sashine_time).seconds > LIMIT_TIME:
    # キャンセル処理を最初にやる
    if buy_order_info != None:
      cancel(buy_order_info['id'])
    if sell_order_info != None:
      cancel(sell_order_info['id'])

    time.sleep(1)

    # 注文情報の取得　キャンセルしても返ってくる可能性がある
    if buy_order_info != None:
      buy_order_status = get_status(buy_order_info['id'])
      if buy_order_status != None:
        buy_fiiled = buy_order_status['filled']
    if sell_order_info != None:
      sell_order_status = get_status(sell_order_info['id'])  
      if sell_order_status != None:
        sell_fiiled = sell_order_status['filled']

    # 初期化
    order_available = True
    buy_order_info = None
    sell_order_info = None
    buy_fiiled = 0
    sell_filled = 0

  # 終了フラッグが立っている場合は終了する
  if is_done:
    break