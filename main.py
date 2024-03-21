from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
import re
import requests

app = FastAPI()

# PayPayリンクの形式を確認する簡単な正規表現
PAYPAY_LINK_PATTERN = r"^https://pay\.paypay\.ne\.jp/[a-zA-Z0-9]+$"

@app.post("/submit-form/", response_class=HTMLResponse)
async def submit_form(termsAgree: bool = Form(...), email: EmailStr = Form(...), paypayLink: str = Form(...)):
    if not termsAgree:
        return HTMLResponse(content="<html><body><p>利用規約に同意してください</p></body></html>", status_code=400)
    if not re.match(PAYPAY_LINK_PATTERN, paypayLink):
        return HTMLResponse(content="<html><body><p>PayPayの送金リンクが不正です</p></body></html>", status_code=400)
    
    # Google Apps ScriptのWebアプリケーションURL
    gas_url = 'https://script.google.com/macros/s/AKfycbwwOFtVybl6AbKfm4kBqK1k5FzlubydI02aGOnkWeXp13Qu6wh5RAE90hgVgYybNUBg/exec'

    # リクエストデータ
    data = {
        'paypayLink': paypayLink,
        'email': email
    }

    # GASのWebアプリケーションにPOSTリクエストを送信
    response = requests.post(gas_url, data=data)

    # レスポンスの確認
    if response.status_code == 200:
        # HTML形式で正常なレスポンスを返す
        return HTMLResponse(content="<html><body><p>購入が完了しました</p><p>メールをご確認ください</p></body></html>")
    else:
        # エラーレスポンス
        return HTMLResponse(content="<html><body><p>エラーが発生しました</p></body></html>", status_code=500)