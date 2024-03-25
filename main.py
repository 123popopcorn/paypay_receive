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
GASWebAppURL = os.getenv('GAS')
# プロキシ設定の辞書を作成
proxies = {
    "http": f"http://{proxy_user}:{proxy_pass}@{proxy_address}",
    "https": f"http://{proxy_user}:{proxy_pass}@{proxy_address}",
}

@app.post("/submit-form/", response_class=HTMLResponse)
async def submit_form(termsAgree: bool = Form(...), email: EmailStr = Form(...), paypayLink: str = Form(...)):
    # ログイン
    check_result, message = check_paypay_link(paypayLink)
    # link_idの抽出
    link_id = paypayLink.split('/')[-1]

    if check_result:

        paypay=PayPaython.PayPay(phone=phone,password=password, client_uuid=client_uuid, proxy=proxies)

        # 受け取り
        paypay.receive(link_id)

        # 受け取りが完了したら、GASにPOSTリクエストを送信
        gas_url = GASWebAppURL
        data = {
            'paypayLink': paypayLink,
            'email': email
        }
        response = requests.post(gas_url, data=data)

        if response.status_code == 200:
            return HTMLResponse(content="<html><body>購入完了<br>メールをご確認ください。</body></html>", status_code=200)
        else:
            return HTMLResponse(content=f"<html><body>GASへのPOSTリクエストに失敗しました<br>エラー詳細: {response.text}</body></html>", status_code=400)
    else:
        return HTMLResponse(content=f"<html><body>購入失敗: {message}</body></html>", status_code=400)

def check_paypay_link_format(url):
    # PayPayリンクの形式を確認する正規表現パターン
    PAYPAY_LINK_PATTERN = r"^https://pay\.paypay\.ne\.jp/[a-zA-Z0-9]+$"
    if not re.match(PAYPAY_LINK_PATTERN, url):
        return False, "PayPayの送金リンクが不正です。"
    return True, "リンク形式が正しいです。"

def check_paypay_link(paypay,url):
    
    # URL形式の確認
    format_check, message = check_paypay_link_format(url)
    if not format_check:
        return False, message
    
    # link_idの抽出
    link_id = url.split('/')[-1]
    
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