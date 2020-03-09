# coding: utf-8
import datetime
import time
import ccxt
from datetime import datetime as dt, timedelta
import functions

# 設定 ------------------------------------------------------------------------------#
API_KEY = '96wCZAuaiiCuCwz82ds8ym'
API_SECRET = 'onNARBPBbcElLAr6Nd6WZ4moj5nz3UzADlvLekIH+64='
LIMIT_TIME = 5 # seconds
AMOUNT_MIN = 0.05 # 最小注文単位 BTC
LOT = 0.05 # BTC
SPREAD_DELTA = 249 # 円
COIN = 'BTC'
PAIR = 'FX_BTC_JPY'
bitflyer = ccxt.bitflyer({'apiKey': API_KEY, 'secret': API_SECRET})
MAX_TRADES_COUNT = 150
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
buy_order_finished = False
sell_order_finished = False

buy_fiiled = 0
sell_fiiled = 0
remaining = 0

trade_counts = 0
initial_colla = get_colla()['collateral']
last_colla = None
# 変数 ------------------------------------------------------------------------------#

logger.info('Initial collateral: ')
logger.info(initial_colla)

while True:
  if order_available and buy_order_finished == False and sell_order_finished == False:
    # TODO: bitflyerのAPIの状況が悪い場合は、10秒sleepして次のループへ回す
    logger.info('normal term start!')
    mid_price = get_mid_price()
    buy_price, sell_price = mid_price - SPREAD_DELTA, mid_price + SPREAD_DELTA
    buy_order_info = limit('BUY', LOT, buy_price)
    sell_order_info = limit('SELL', LOT, sell_price)
    sashine_time = datetime.datetime.now()
    order_available = False
  elif order_available and buy_order_finished == False:
    mid_price = get_mid_price()
    buy_price = mid_price - SPREAD_DELTA
    buy_order_info = limit('BUY', LOT, buy_price)
    sashine_time = datetime.datetime.now()
    order_available = False
  elif order_available and sell_order_finished == False:
    mid_price = get_mid_price()
    sell_price = mid_price + SPREAD_DELTA
    sell_order_info = limit('SELL', LOT, sell_price)
    sashine_time = datetime.datetime.now()
    order_available = False

  now = datetime.datetime.now()

  next 

  # 
  if order_available == False and (now - sashine_time).seconds > LIMIT_TIME:
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
        if buy_fiiled > 0:
          buy_order_finished = True
    if sell_order_info != None:
      sell_order_status = get_status(sell_order_info['id'])  
      if sell_order_status != None:
        sell_fiiled = sell_order_status['filled']
        if sell_fiiled > 0:
          sell_order_finished = True

    # TODO: buy_filled, sell_filledが中途半端な数字である場合、次の注文で調整する必要がある
    
    # 制限時間を超えた後の初期化
    order_available = True
    buy_order_info = None
    sell_order_info = None 

    # 一回の注文ループが終わったときの完全初期化
    if buy_order_finished and sell_order_finished:
      # TODO:ポジションと注文をチェックして完全にゼロであることを確認
      # TODO:もし、ポジションや注文が残っていれば、注文はキャンセル。ポジションは成り行きの反対売買で消去

      # トレード回数の記録 
      trade_counts += 1
      logger.info(str(trade_counts) + " trades finished!")

      buy_order_finished = False
      sell_order_finished = False
      buy_fiiled = 0
      sell_filled = 0

      time.sleep(1)
      if trade_counts > MAX_TRADES_COUNT:
        is_done = True        

  # 終了フラッグが立っている場合は終了する
  if is_done:
    last_colla = get_colla()['collateral']
    logger.info("finished!")
    logger.info("Initial:")
    logger.info(initial_colla)
    logger.info("Last:")
    logger.info(last_colla)
    break