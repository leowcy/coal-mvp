from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
import requests
from dotenv import load_dotenv
import os

load_dotenv()  # 加载 .env 文件
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# 允许跨域（便于你未来前端调试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可限制为 http://localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite数据库初始化
conn = sqlite3.connect("coal.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS coal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    heat INTEGER,
    sulfur REAL,
    volatile REAL,
    moisture REAL,
    base_price REAL
)
"""
)
conn.commit()


# 获取煤种列表
@app.get("/coal")
def get_coal():
    cursor.execute(
        "SELECT id, name, heat, sulfur, volatile, moisture, base_price FROM coal"
    )
    data = cursor.fetchall()
    return {"coal_types": data}


@app.post("/coal/add")
def add_coal(
    name: str,
    heat: int,
    sulfur: float,
    volatile: float,
    moisture: float,
    base_price: float,
):
    cursor.execute(
        "INSERT INTO coal (name, heat, sulfur, volatile, moisture, base_price) VALUES (?, ?, ?, ?, ?, ?)",
        (name, heat, sulfur, volatile, moisture, base_price),
    )
    conn.commit()
    return {"msg": "煤种添加成功"}


@app.post("/coal/update")
def update_coal(id: int, base_price: float):
    cursor.execute("UPDATE coal SET base_price = ? WHERE id = ?", (base_price, id))
    conn.commit()
    return {"msg": "煤种更新成功"}


@app.post("/coal/delete")
def delete_coal(id: int):
    cursor.execute("DELETE FROM coal WHERE id = ?", (id,))
    conn.commit()
    return {"msg": "煤种已删除"}


# Pydantic请求模型
class CalculationRequest(BaseModel):
    railwayFee: float
    shortDistanceFee: float
    userPrompt: str  # ✅ 支持自定义问题


@app.post("/calculate")
def calculate(data: CalculationRequest):
    print("收到参数：", data)

    cursor.execute("SELECT * FROM coal")
    coal_list = cursor.fetchall()

    if not coal_list:
        raise HTTPException(status_code=404, detail="无煤种数据")

    # 自动拼接AI提示词 + 用户自定义问题
    prompt = f"""
    你是资深煤炭掺配优化专家，请直接输出最优掺配结果，禁止生成Python或任何编程代码。

    以下是煤种数据（格式：[id, 煤种, 热值, 硫含量, 挥发份, 全水, 基础价格]）：
    {coal_list}

    运费信息：
    - 铁路运费：{data.railwayFee} 元/吨
    - 短倒运费：{data.shortDistanceFee} 元/吨

    用户需求：
    {data.userPrompt}

    计算要求：
    1️⃣ 计算每个煤种的到站价：基础价格 + 铁路运费 + 短倒运费
    2️⃣ 满足用户热值、硫等要求的前提下，给出最优掺配比例，目标为最低成本
    3️⃣ 直接输出最终掺配方案，格式如下：
    - 掺配比例：煤种A：70%，煤种B：30%
    - 混合后热值：XXXX kcal
    - 混合后硫含量：X.X%
    - 成本：XXX 元/吨

    ❌ 禁止输出任何代码或建议代码实现
    ✅ 只输出方案和结果
    """

    print("生成的prompt：", prompt)

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
        },
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json; charset=utf-8",  # ✅ 强制UTF-8
        },
        timeout=120
    )

    print("OpenAI请求响应：", response.status_code, response.text)

    if response.status_code != 200:
        print(response.text)
        raise HTTPException(status_code=500, detail="AI计算失败")

    return response.json()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
