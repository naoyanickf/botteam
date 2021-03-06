## 高頻度取引ボット開発

当面の方針は、下記高頻度取引ボットの分類に従い、シンプルなボットを開発していくプロジェクト。

### 高頻度取引ボットの分類

![Dx7UMroUYAIqPzJ](https://user-images.githubusercontent.com/5179467/72659392-21d25700-3a02-11ea-97ee-f7744003105d.jpeg)

### 開発プロジェクト

#### 1. 価格変動型 - number0
市場参加者による成行注文の執行コストを利益の源泉とするボット。

・基本方針
```
n秒間、最新の板の中央値から、設定したdelta分離れた上下に、売りと買いの指値を供給する
```

・実装方針
```
n秒間で両方約定した場合　→　次の売買処理
n秒間で片方しか約定しない場合　→　注文をキャンセルの後、最新価格にて注文を出し直す。在庫が解消するまで繰り返す。
n秒間で両方約定しない場合　→　注文をキャンセルの後、次の売買処理
```

・実装するもの
```
最新価格取得クラス - websocketで最新価格を常に取得し供給するだけ
売買クラス
```


#### 参考

https://twitter.com/mmbotXXX
