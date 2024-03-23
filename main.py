from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
import re
import requests
import PayPaython
import datetime
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
    paypay=PayPaython.PayPay(phone=phone,password=password, client_uuid=client_uuid, proxy=proxies)
    check_result, message = check_paypay_link(paypay,paypayLink)
    if check_result:
        # link_idの抽出
        link_id = paypayLink.split('/')[-1]

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
            return HTMLResponse(content="<html><body>購入が完了しました。メールをご確認ください。</body></html>", status_code=200)
        else:
            paypay.reject(link_id)
            raise HTTPException(status_code=400, detail="GASへのPOSTリクエストに失敗しました。")
    else:
        #送金リンクを辞退
        paypay.reject(link_id)
        raise HTTPException(status_code=400, detail=f"受け取り失敗: {message}")

def check_paypay_link_format(url):
    # PayPayリンクの形式を確認する正規表現パターン
    PAYPAY_LINK_PATTERN = r"^https://pay\.paypay\.ne\.jp/[a-zA-Z0-9]+$"
    if not re.match(PAYPAY_LINK_PATTERN, url):
        return False, "PayPayの送金リンクが不正です。"
    return True, "リンク形式が正しいです。"

def check_paypay_link(paypay,url):
    
    # URL形式の確認
    format_check, message = check_paypay_link_format(url,proxy=proxies['http'])
    if not format_check:
        return False, message
    
    # link_idの抽出
    link_id = url.split('/')[-1]
    
    # 送金リンクチェック
    result = paypay.check_link(link_id)
    
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
        return False, "リンクはパスコードが設定されています。"
    
    # 条件3: 有効期限のチェック
    # JSTとUTCの差分
    DIFF_JST_FROM_UTC = 9
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    created_at = datetime.strptime(pending_info['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
    expired_at = datetime.strptime(pending_info['expiredAt'], '%Y-%m-%dT%H:%M:%SZ')
    if not (created_at <= now <= expired_at):
        return False, "リンクの有効期限が切れています。"
    
    # 条件4: リンクのブロック状態
    if pending_info['isLinkBlocked']:
        return False, "リンクはブロックされています。"

    # すべての条件を満たす場合
    return True, "送金リンクは受け取り可能です。"