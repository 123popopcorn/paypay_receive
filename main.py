from fastapi import FastAPI, Form, HTTPException
from pydantic import BaseModel, EmailStr
import re

app = FastAPI()

# PayPayリンクの形式を確認する簡単な正規表現
PAYPAY_LINK_PATTERN = r"^https://pay\.paypay\.ne\.jp/[a-zA-Z0-9]+$"

@app.post("/submit-form/")
async def submit_form(termsAgree: bool = Form(...), email: EmailStr = Form(...), paypayLink: str = Form(...)):
    if not termsAgree:
        raise HTTPException(status_code=400, detail="利用規約に同意してください")
    if not re.match(PAYPAY_LINK_PATTERN, paypayLink):
        raise HTTPException(status_code=400, detail="PayPayの送金リンクが不正です")
    
    # ここでメール送信などの処理を行う
    return {'購入ありがとうございます。'+ "\n" + "\n" + '内容はこちらからご確認の上、必ずお手元に保存してください' + "\n" + "\n" + 'https://docs.google.com/document/d/1Dnlb9-tmgx-8b6yCKlMrlK1gG-qPERRCTAGo5Kmi0rU/edit?usp=sharing' + "\n" + "\n" + 'ご不明点やご質問等ございましたら、X(@wanpooochi)のDMまでご連絡ください'}
