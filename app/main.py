from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
import requests

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


# Pydantic请求模型
class CalculationRequest(BaseModel):
    railwayFee: float
    shortDistanceFee: float


# 获取煤种列表
@app.get("/coal")
def get_coal():
    cursor.execute(
        "SELECT id, name, heat, sulfur, volatile, moisture, base_price FROM coal"
    )
    data = cursor.fetchall()
    return {"coal_types": data}


# 添加煤种（测试用）
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


# AI计算最优配比
@app.post("/calculate")
def calculate(data: CalculationRequest):
    cursor.execute("SELECT * FROM coal")
    coal_list = cursor.fetchall()

    if not coal_list:
        raise HTTPException(status_code=404, detail="无煤种数据")

    # 构建AI提示词
    prompt = f"""
    以下是煤种数据（格式：[name, heat, sulfur, volatile, moisture, base_price]）：
    {coal_list}

    运费信息：
    - 铁路运费：{data.railwayFee} 元/吨
    - 短倒运费：{data.shortDistanceFee} 元/吨

    计算逻辑：
    1. 计算每个煤种的到站价：base_price + railwayFee + shortDistanceFee
    2. 在满足热值不低于5500kcal，硫不超过1%的前提下，给出最优掺配比例，目标为最低成本
    3. 输出：
        - 最优配比（列出各煤种比例）
        - 混合后热值
        - 混合后硫含量
        - 成本（元/吨）
    """

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
        },
        headers={
            "Authorization": "Bearer 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"
        },
    )

    if response.status_code != 200:
        print(response.text)
        raise HTTPException(status_code=500, detail="AI计算失败")

    result = response.json()
    return result


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
