# exchange.py

import aiohttp
import asyncio
import async_timeout
import json
from aiohttp import WSMsgType
import traceback
import time
from datetime import datetime
import hmac
import hashlib
import urllib

class Exchange():

# ------------------------------------------------------------------------------
# PROPERTY
# ------------------------------------------------------------------------------

    api_key = ''
    api_secret = ''

    product_code = 'FX_BTC_JPY'  # 銘柄 "FX_BTC_JPY"
    minute_to_expire = 43200  # 注文の有効期限(分 43200=30日
    time_in_force = 'GTC'  # 執行条件 "GTC", "IOC", "FOK"
    currency_code = 'JPY'  # 口座で使用している通貨のコード "JPY", "USD"

    # リアルタイムAPI購読チャネル
    channels = ['ticker', 'executions', 'board_snapshot', 'board']

    timeout = 10  # タイムアウト
    session = None  # セッション保持
    requests = []  # リクエストパラメータ

    urls = {'public': 'https://api.bitflyer.com/v1/',
            'private': 'https://api.bitflyer.com/v1/me/',
            'path': '/v1/me/'}

# ------------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------------

    def __init__(self, api_key, api_secret):
        # APIキー・SECRETをセット
        self.api_key = api_key
        self.api_secret = api_secret

# ------------------------------------------------------------------------------
# ASYNC REQUEST FOR REST API
# ------------------------------------------------------------------------------

    def set_request(self, method, access_modifiers, target_path, params):
        if access_modifiers == 'public':
            url = ''.join([self.urls['public'], target_path])
            if method == 'GET':
                headers = ''
                self.requests.append({'method': method,
                                      'access_modifiers': access_modifiers,
                                      'target_path': target_path, 'url': url,
                                      'params': params, 'headers':{}})

            if method == 'POST':
                headers = {'Content-Type': 'application/json'}
                self.requests.append({'method': method,
                                      'access_modifiers': access_modifiers,
                                      'target_path': target_path, 'url': url,
                                      'params': params, 'headers':headers})

        if access_modifiers == 'private':
            url = ''.join([self.urls['private'], target_path])
            path = ''.join([self.urls['path'], target_path])
            timestamp = str(time.time())
            if method == 'GET':
                if len(params) > 0:
                    text = ''.join([timestamp, method, path,
                           '?{}'.format(urllib.parse.urlencode(params))])
                else:
                    text = ''.join([timestamp, method, path])

                sign = self.get_sign(text)
                headers = self.set_headers_for_private(timestamp=timestamp,
                                                       sign=sign)

                self.requests.append({'method': method,
                                      'access_modifiers': access_modifiers,
                                      'target_path': target_path, 'url': url,
                                      'params': params, 'headers': headers})

            if method == 'POST':
                if len(params) > 0:
                    post_data = json.dumps(params)
                else:
                    post_data = params

                text = ''.join([timestamp, method, path, post_data])
                sign = self.get_sign(text)
                headers = self.set_headers_for_private(timestamp=timestamp,
                                                       sign=sign)

                self.requests.append({'method': method,
                                      'access_modifiers': access_modifiers,
                                      'target_path': target_path, 'url': url,
                                      'params': post_data, 'headers': headers})

    def set_headers_for_private(self, timestamp, sign):
        headers = {'Content-Type': 'application/json',
                   'ACCESS-KEY': self.api_key, 'ACCESS-TIMESTAMP': timestamp,
                   'ACCESS-SIGN': sign}
        return headers

    def get_sign(self, text):
        sign = hmac.new(self.api_secret.encode('ascii'),
                        text.encode('ascii'), hashlib.sha256).hexdigest()
        return sign

    async def fetch(self, request):
        status = 0
        content = []

        async with async_timeout.timeout(self.timeout):
            try:
                if self.session is None:
                    self.session = await aiohttp.ClientSession().__aenter__()
                if request['method'] is 'GET':
                    async with self.session.get(url=request['url'],
                                                params=request['params'],
                                                headers=request['headers']) as response:
                        status = response.status
                        content = await response.read()
                        if status != 200:
                            # エラーのログ出力など必要な場合
                            pass

                elif request['method'] is 'POST':
                    async with self.session.post(url=request['url'],
                                                 data=request['params'],
                                                 headers=request['headers']) as response:
                        status = response.status
                        content = await response.read()
                        if status != 200:
                            # エラーのログ出力など必要な場合
                            pass

                if len(content) == 0:
                    result = []

                else:
                    try:
                        result = json.loads(content.decode('utf-8'))
                    except Exception as e:
                        traceback.print_exc()

                return result

            except Exception as e:
                # セッション終了
                if self.session is not None:
                    await self.session.__aexit__(None, None, None)
                    await asyncio.sleep(0)
                    self.session = None

                traceback.print_exc()

    async def send(self):
        promises = [self.fetch(req) for req in self.requests]
        self.requests.clear()
        return await asyncio.gather(*promises)

# ------------------------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------------------------

    # マーケットの一覧を取得
    def getmarkets(self):
        params = {}
        self.set_request(method='GET', access_modifiers='public',
                         target_path='getmarkets', params=params)

    # 板情報を取得
    def getboard(self):
        params = {'product_code': self.product_code}
        self.set_request(method='GET', access_modifiers='public',
                         target_path='getboard', params=params)

    # Tickerを取得
    def getticker(self):
        params = {'product_code': self.product_code}
        self.set_request(method='GET', access_modifiers='public',
                         target_path='getticker', params=params)

    # 約定履歴を取得
    def getexecutions(self):
        params = {'product_code': self.product_code}
        self.set_request(method='GET', access_modifiers='public',
                         target_path='getexecutions', params=params)

    # 板の状態を取得
    def getboardstate(self):
        params = {'product_code': self.product_code}
        self.set_request(method='GET', access_modifiers='public',
                         target_path='getboardstate', params=params)

    # 取引所の状態を取得
    def gethealth(self):
        params = {'product_code': self.product_code}
        self.set_request(method='GET', access_modifiers='public',
                         target_path='gethealth', params=params)

    # チャットを取得
    def getchats(self, from_date=''):
        params = {'from_date': from_date}
        self.set_request(method='GET', access_modifiers='public',
                         target_path='getchats', params=params)

# ------------------------------------------------------------------------------
# PRIVATE API
# ------------------------------------------------------------------------------

    # API キーの権限を取得
    def getpermissions(self):
        params = {}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getpermissions', params=params)

    # 資産残高を取得
    def getbalance(self):
        params = {}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getbalance', params=params)

    # 証拠金の状態を取得
    def getcollateral(self):
        params = {}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getcollateral', params=params)

    # 預入用アドレスを取得
    def getaddresses(self):
        params = {}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getaddresses', params=params)

    # 仮想通貨預入履歴を取得
    def getcoinins(self, count=100, before=0, after=0):
        params = {'count': count, 'before': before, 'after': after}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getcoinins', params=params)

    # 仮想通貨預入履歴を取得
    def getcoinouts(self, count=100, before=0, after=0):
        params = {'count': count, 'before': before, 'after': after}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getcoinouts', params=params)

    # 銀行口座一覧を取得
    def getbankaccounts(self):
        params = {}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getbankaccounts', params=params)

    # 入金履歴を取得
    def getdeposits(self, count=100, before=0, after=0):
        params = {'count': count, 'before': before, 'after': after}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getdeposits', params=params)

    # 出金
    def withdraw(self, currency_code, bank_account_id, amount, code):
        params = {'currency_code': self.currency_code,
                  'bank_account_id': bank_account_id,
                  'amount': amount, 'code': code}
        self.set_request(method='POST', access_modifiers='private',
                         target_path='withdraw', params=params)

    # 出金履歴を取得
    def getwithdrawals(self, count=100, before=0, after=0, message_id=''):
        params = {'count': count, 'before': before, 'after': after,
                  'message_id': message_id}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getwithdrawals', params=params)

    # 新規注文を出す
    def sendchildorder(self, child_order_type, side, price, size):
        params = {'product_code': self.product_code,
                  'child_order_type': child_order_type,
                  'side': side, 'price': price, 'size': size,
                  'minute_to_expire': self.minute_to_expire,
                  'time_in_force': self.time_in_force}
        self.set_request(method='POST', access_modifiers='private',
                         target_path='sendchildorder', params=params)

    # 注文をキャンセルする
    def cancelchildorder(self, child_order_id='',
                         child_order_acceptance_id=''):
        params = {'product_code': self.product_code}
        if len(child_order_id) > 0:
            params['child_order_id'] = child_order_id
        elif len(child_order_acceptance_id) > 0:
            params['child_order_acceptance_id'] = child_order_acceptance_id

        self.set_request(method='POST', access_modifiers='private',
                         target_path='cancelchildorder', params=params)

    # 特殊注文を出す
    def sendparentorder(self, order_method, parameters_1, parameters_2,
                        parameters_3):
        params ={'order_method': order_method,
                 'minute_to_expire': self.minute_to_expire,
                 'time_in_force': self.time_in_force, 'parameters': {}}
        if order_method == 'SIMPLE':
            parameters_1['product_code'] = self.product_code
            params['parameters'] = [parameters_1]
        elif order_method == 'IFD' or order_method == 'OCO':
            parameters_1['product_code'] = self.product_code
            parameters_2['product_code'] = self.product_code
            params['parameters'] = [parameters_1, parameters_2]
        elif order_method == 'IFDOCO':
            parameters_1['product_code'] = self.product_code
            parameters_2['product_code'] = self.product_code
            parameters_3['product_code'] = self.product_code
            params['parameters'] = [parameters_1, parameters_2, parameters_3]

        self.set_request(method='POST', access_modifiers='private',
                         target_path='sendparentorder', params=params)

    # 親注文をキャンセルする
    def cancelparentorder(self, parent_order_id='',
                         parent_order_acceptance_id=''):
        params = {'product_code': self.product_code}
        if len(parent_order_id) > 0:
            params['parent_order_id'] = parent_order_id
        elif len(parent_order_acceptance_id) > 0:
            params['parent_order_acceptance_id'] = parent_order_acceptance_id

        self.set_request(method='POST', access_modifiers='private',
                         target_path='cancelparentorder', params=params)

    # すべての注文をキャンセル
    def cancelallchildorders(self):
        params = {'product_code': self.product_code}
        self.set_request(method='POST', access_modifiers='private',
                         target_path='cancelallchildorders', params=params)

    # 注文の一覧を取得
    def getchildorders(self, count=100, before=0, after=0,
                       child_order_state='', child_order_id='',
                       child_order_acceptance_id='',
                       parent_order_id=''):
        params = {'product_code': self.product_code, 'count': count,
                  'before': before, 'after': after,
                  'child_order_state': child_order_state,
                  'child_order_id': child_order_id,
                  'child_order_acceptance_id': child_order_acceptance_id,
                  'parent_order_id': parent_order_id}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getchildorders', params=params)

    # 親注文の一覧を取得
    def getparentorders(self, count=100, before=0, after=0,
                       parent_order_state=''):
        params = {'product_code': self.product_code, 'count': count,
                  'before': before, 'after': after,
                  'parent_order_state': parent_order_state}

        self.set_request(method='GET', access_modifiers='private',
                         target_path='getparentorders', params=params)

    # 親注文の詳細を取得
    def getparentorder(self, parent_order_id='',
                         parent_order_acceptance_id=''):
        params = {}
        if len(parent_order_id) > 0:
            params = {'parent_order_id': parent_order_id}
        elif len(parent_order_acceptance_id) > 0:
            params = {'parent_order_acceptance_id': parent_order_acceptance_id}

        self.set_request(method='GET', access_modifiers='private',
                         target_path='getparentorder', params=params)

    # 約定の一覧を取得
    def getexecutions(self, child_order_id='', child_order_acceptance_id='',
                      count=100, before=0, after=0):
        params = {}
        if len(child_order_id) > 0:
            params = {'product_code': self.product_code,
                      'child_order_id': child_order_id,
                      'count': count, 'before': before, 'after': after}
        elif len(child_order_acceptance_id) > 0:
            params = {'product_code': self.product_code,
                      'child_order_acceptance_id': child_order_acceptance_id,
                      'count': count, 'before': before, 'after': after}

        self.set_request(method='GET', access_modifiers='private',
                         target_path='getexecutions', params=params)

    # 残高履歴を取得
    def getbalancehistory(self, currency_code='JPY', count=100, before=0,
                          after=0):
        params = {'currency_code': self.currency_code,'count': count,
                  'before': before, 'after': after}

        self.set_request(method='GET', access_modifiers='private',
                         target_path='getbalancehistory', params=params)

    # 建玉の一覧を取得
    def getpositions(self):
        params = {'product_code': self.product_code}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='getpositions', params=params)

    # 証拠金の変動履歴を取得
    def getcollateralhistory(self, count=100, before=0, after=0):
        params = {'count': count, 'before': before, 'after': after}

        self.set_request(method='GET', access_modifiers='private',
                         target_path='getcollateralhistory', params=params)

    # 取引手数料を取得
    def gettradingcommission(self):
        params = {'product_code': self.product_code}
        self.set_request(method='GET', access_modifiers='private',
                         target_path='gettradingcommission', params=params)

# ------------------------------------------------------------------------------
# REALTIME
# ------------------------------------------------------------------------------

    async def subscribe(self, callback):
        if len(self.channels) == 0:
            await asyncio.sleep(0)
            return
        uri = 'wss://ws.lightstream.bitflyer.com/json-rpc'
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(uri,
                                                  receive_timeout=self.timeout) as client:
                        for channel in self.channels:
                            params = {'channel': 'lightning_'\
                                      + channel + '_' + self.product_code}
                            query = {'method': 'subscribe', 'params': params}
                            await asyncio.wait([client.send_str(json.dumps(query))])
                        async for response in client:
                            if response.type != WSMsgType.TEXT:
                                print('response:' + str(response))
                                break
                            data = json.loads(response[1])['params']
                            await self.handler(callback, data)

            except Exception as e:
                traceback.print_exc()

# ------------------------------------------------------------------------------
# UTILS
# ------------------------------------------------------------------------------

    # コールバック、ハンドラー
    async def handler(self, func, *args):
        return await func(*args)