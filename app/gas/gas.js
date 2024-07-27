function getMarketPrice() {
  // 現在の市場価格を取得
  var API_URL = 'https://api.bitflyer.jp';
  var product_code = 'BTC_JPY';

  var ticker_url = API_URL + '/v1/ticker?product_code=' + product_code;
  var response = UrlFetchApp.fetch(ticker_url);
  var data = JSON.parse(response.getContentText());

  var marketPrice = parseFloat(data['ltp']);

  // タイムスタンプを生成
  var timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMddHHmmss');

  // スプレッドシートに追加する処理
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var today = new Date();
  var year = today.getFullYear();
  var month = ('0' + (today.getMonth() + 1)).slice(-2); // 月を2桁の文字列に変換
  var sheetName = year + month;

  var sheet = ss.getSheetByName(sheetName);

  // シートが存在しない場合、新規作成
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  var lastRow = sheet.getLastRow();
  sheet.getRange(lastRow + 1, 1).setValue(timestamp); // タイムスタンプを記録
  sheet.getRange(lastRow + 1, 2).setValue(marketPrice); // 市場価格を記録
}

// 1分ごとに自動実行するトリガーを設定する関数
function setTrigger() {
  ScriptApp.newTrigger('getMarketPrice')
      .timeBased()
      .everyMinutes(1)
      .create();
}
