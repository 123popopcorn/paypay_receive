from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
import re

app = FastAPI()

# PayPayリンクの形式を確認する簡単な正規表現
PAYPAY_LINK_PATTERN = r"^https://pay\.paypay\.ne\.jp/[a-zA-Z0-9]+$"

@app.post("/submit-form/", response_class=HTMLResponse)
async def submit_form(termsAgree: bool = Form(...), email: EmailStr = Form(...), paypayLink: str = Form(...)):
    if not termsAgree:
        return HTMLResponse(content="<html><body><p>利用規約に同意してください</p></body></html>", status_code=400)
    if not re.match(PAYPAY_LINK_PATTERN, paypayLink):
        return HTMLResponse(content="<html><body><p>PayPayの送金リンクが不正です</p></body></html>", status_code=400)
    
    # HTML形式で正常なレスポンスを返す
    return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>購入完了</title>
            </head>
            <body>
            <p>購入ありがとうございます</p>
            <span>内容は以下のリンクからご確認ください<br></span>
            <span><b>※リンクは必ず保存してください</b>（メモ、スクショ、Google Driveなど）<br></span>
            <a href="https://docs.google.com/document/d/1Dnlb9-tmgx-8b6yCKlMrlK1gG-qPERRCTAGo5Kmi0rU/edit?usp=sharing">https://docs.google.com/document/d/1Dnlb9-tmgx-8b6yCKlMrlK1gG-qPERRCTAGo5Kmi0rU/edit?usp=sharing</a>
            <p>ご不明点やご質問等ございましたら、X(@wanpooochi)のDMまでご連絡ください</p>
            </body>
        </html>
    """