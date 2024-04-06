from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
import re
import requests
import PayPaython
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

app = FastAPI()

kingaku = 5

# 環境変数から値を取得
phone = os.getenv('PHONE')
password = os.getenv('PASSWORD')
client_uuid = os.getenv('CLIENT_UUID')
proxy_user = os.getenv('PROXY_USER')
proxy_pass = os.getenv('PROXY_PASS')
proxy_address = os.getenv('PROXY_ADDRESS')

# プロキシ設定の辞書を作成
proxies = {
    "http": f"http://{proxy_user}:{proxy_pass}@{proxy_address}",
    "https": f"http://{proxy_user}:{proxy_pass}@{proxy_address}",
}

@app.post("/submit-form/", response_class=HTMLResponse)
async def submit_form(termsAgree: bool = Form(...), paypayLink: str = Form(...)):
    # リンクチェック
    check_result, message = check_paypay_link(paypayLink)

    # link_idの抽出
    link_id = paypayLink.split('/')[-1]

    if check_result:

        paypay=PayPaython.PayPay(phone=phone,password=password, client_uuid=client_uuid, proxy=proxies)

        # 受け取り
        order_status = paypay.receive(link_id)['payload']['orderStatus']
        if order_status == 'COMPLETED':
            content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <!-- レスポンシブデザインをサポートするためのビューポートメタタグ -->
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>購入完了</title>
        <!-- Bootstrap CSS -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" crossorigin="anonymous">
        <style>
            /* ここにカスタムスタイルまたはメディアクエリを追加 */
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <!-- 最大幅が異なるデバイスでレスポンシブに対応 -->
            <div class="row">
                <div class="col-12 col-sm-10 col-md-8 col-lg-6 mx-auto">
                    <h1 class="mb-4">ご購入ありがとうございます</h1>
                    <p>内容は以下からご確認ください</p>
                    <br>
                    <a href="https://docs.google.com/document/d/1gJmvtCaFOLZz3SKLWnAihYuRudljqS5tDI2H0337ppw/edit?usp=sharing" target="_blank">商品はこちら</a>
                    <br>
                    <p>ご不明点やご質問等ございましたらX(@_poch3)のDMまでご連絡ください。</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
            return HTMLResponse(content=content, status_code=200)
        else:
            content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <!-- レスポンシブデザインをサポートするためのビューポートメタタグ -->
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>購入失敗</title>
        <!-- Bootstrap CSS -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" crossorigin="anonymous">
        <style>
            /* ここにカスタムスタイルまたはメディアクエリを追加 */
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <!-- 最大幅が異なるデバイスでレスポンシブに対応 -->
            <div class="row">
                <div class="col-12 col-sm-10 col-md-8 col-lg-6 mx-auto">
                    <h1 class="mb-4">購入に失敗しました</h1>
                    <br>
                    <p>最初からやり直してください</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
            return HTMLResponse(content=content, status_code=200)
    else:
        content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <!-- レスポンシブデザインをサポートするためのビューポートメタタグ -->
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>購入失敗</title>
        <!-- Bootstrap CSS -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" crossorigin="anonymous">
        <style>
            /* ここにカスタムスタイルまたはメディアクエリを追加 */
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <!-- 最大幅が異なるデバイスでレスポンシブに対応 -->
            <div class="row">
                <div class="col-12 col-sm-10 col-md-8 col-lg-6 mx-auto">
                    <h1 class="mb-4">購入に失敗しました</h1>
                    <br>
                    <p>考えられる原因</p>
                    <br>
                    <p>・送金URLが間違っている</p>
                    <br>
                    <p>・金額が間違っている</p>
                    <br>
                    <p>・パスコードが設定されている</p>
                    <br>
                    <p>・URLの期限が切れている</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
        return HTMLResponse(content=content, status_code=200)

def check_paypay_link_format(paypayLink):
    # PayPayリンクの形式を確認する正規表現パターン
    PAYPAY_LINK_PATTERN = r"^https://pay\.paypay\.ne\.jp/[a-zA-Z0-9]+$"
    if not re.match(PAYPAY_LINK_PATTERN, paypayLink):
        return False, "PayPayの送金リンクが不正です。"
    return True, "リンク形式が正しいです。"

def check_paypay_link(paypayLink):
    
    # URL形式の確認
    format_check, message = check_paypay_link_format(paypayLink)
    if not format_check:
        return False, message
    
    # link_idの抽出
    link_id = paypayLink.split('/')[-1]
    
    # 送金リンクチェック
    result = PayPaython.Pay2(proxy=proxies).check_link(link_id)
    
    # エラーレスポンスの確認
    if 'error' in result:
        error_info = result['error']['displayErrorResponse']
        return False, error_info['title'] + ": " + error_info['description']
    
    # payload内の情報を取得（エラーがない場合）
    payload = result['payload']
    pending_info = payload['pendingP2PInfo']
    
    # 条件1: 金額チェック
    if pending_info['amount'] != kingaku:
        return False, "金額が間違っています"
    
    # 条件2: パスコードの有無
    if pending_info['isSetPasscode']:
        return False, "パスコードが設定されています"
    
    # 条件3: 有効期限のチェック
    now = datetime.now(timezone.utc)
    created_at = datetime.strptime(pending_info['createdAt'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    expired_at = datetime.strptime(pending_info['expiredAt'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)

    if not (created_at <= now <= expired_at):
        return False, "リンクの有効期限が切れています"
    
    # 条件4: リンクのブロック状態
    if pending_info['isLinkBlocked']:
        return False, "リンクはブロックされています"

    # すべての条件を満たす場合
    return True, "送金リンクは受け取り可能です"