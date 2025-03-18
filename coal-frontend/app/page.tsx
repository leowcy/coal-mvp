"use client";

import { useEffect, useState } from "react";
import axios from "axios";

export default function Home() {
  const [coalTypes, setCoalTypes] = useState([]);
  const [railwayFee, setRailwayFee] = useState("");
  const [shortDistanceFee, setShortDistanceFee] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [newCoal, setNewCoal] = useState({ name: "", heat: "", sulfur: "", volatile: "", moisture: "", base_price: "" });
  const [userPrompt, setUserPrompt] = useState("我需要两个煤种热值为x kcal以上，硫含量低于y%以内，最低成本参配方案。");

  const loadCoal = () => {
    axios.get("/api/coal").then((res) => setCoalTypes(res.data.coal_types));
  };

  useEffect(() => {
    loadCoal();
  }, []);

  const handleCalculate = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const response = await axios.post("/api/calculate", {
        railwayFee: Number(railwayFee),
        shortDistanceFee: Number(shortDistanceFee),
        userPrompt, // ✅ 传给后端
      });
      setResult(response.data);
    } catch (error) {
      console.error("计算出错", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCoal = async () => {
    const params = new URLSearchParams(newCoal as any).toString();
    await axios.post(`/api/coal/add?${params}`);
    alert("煤种添加成功");
    setNewCoal({ name: "", heat: "", sulfur: "", volatile: "", moisture: "", base_price: "" });
    loadCoal();
  };

  const handleUpdateCoal = async (id: number) => {
    const updated = prompt("请输入更新后的基础价格:");
    if (updated) {
      await axios.post(`/api/coal/update?id=${id}&base_price=${updated}`);
      alert("煤种更新成功");
      loadCoal();
    }
  };

  const handleDeleteCoal = async (id: number) => {
    if (confirm("确定删除该煤种？")) {
      await axios.post(`/api/coal/delete?id=${id}`);
      alert("煤种已删除");
      loadCoal();
    }
  };

  const handleCopy = () => {
    const content = result?.choices?.[0]?.message?.content || "";
    navigator.clipboard.writeText(content);
    alert("结果已复制！");
  };

  const fieldLabels: Record<string, string> = {
    name: "煤种名称",
    heat: "热值 (kcal)",
    sulfur: "硫含量 (%)",
    volatile: "挥发份 (%)",
    moisture: "全水 (%)",
    base_price: "基础价格 (元/吨)"
  };

  return (
    <div className="p-10 bg-gray-50 min-h-screen space-y-8">
      <h1 className="text-3xl font-bold text-center text-gray-800">🚂 煤炭GPT</h1>

      {/* 煤种列表 */}
      <div className="bg-white shadow-lg rounded-xl p-6">
        <h2 className="text-xl font-semibold mb-4 border-b pb-2">📋 当前煤种列表</h2>
        <ul className="space-y-2 text-gray-700">
          {coalTypes.map((coal, index) => (
            <li key={index} className="border-b pb-2 flex justify-between items-center">
              <span>
                🪨 <span className="font-medium">{coal[1]}</span> - 🔥 热值: {coal[2]} kcal - 🌱 硫: {coal[3]}% - 💰 价格: {coal[6]} 元/吨
              </span>
              <span className="space-x-2">
                <button className="bg-yellow-400 hover:bg-yellow-500 text-white px-3 py-1 rounded" onClick={() => handleUpdateCoal(coal[0])}>编辑</button>
                <button className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded" onClick={() => handleDeleteCoal(coal[0])}>删除</button>
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* 添加煤种 */}
      <div className="bg-white shadow-lg rounded-xl p-6 space-y-4">
        <h2 className="text-xl font-semibold border-b pb-2">➕ 添加煤种</h2>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(newCoal).map(([key, value]) => (
            <div key={key}>
              <label className="block mb-1 font-medium">{fieldLabels[key]}</label>
              <input
                className="border rounded-lg p-2 w-full"
                placeholder={`请输入${fieldLabels[key]}`}
                type={key === "name" ? "text" : "number"}
                value={value}
                onChange={(e) => setNewCoal({ ...newCoal, [key]: e.target.value })}
              />
            </div>
          ))}
        </div>
        <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg shadow" onClick={handleAddCoal}>
          ✅ 添加煤种
        </button>
      </div>

      {/* 运费输入 */}
      <div className="bg-white shadow-lg rounded-xl p-6 space-y-4">
        <h2 className="text-xl font-semibold border-b pb-2">🚚 运费参数</h2>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block mb-1 font-medium">🛤️ 铁路运费 (元/吨)</label>
            <input className="border rounded-lg p-2 w-full" type="number" placeholder="如：52" value={railwayFee} onChange={(e) => setRailwayFee(e.target.value)} />
          </div>
          <div>
            <label className="block mb-1 font-medium">🚛 短倒运费 (元/吨)</label>
            <input className="border rounded-lg p-2 w-full" type="number" placeholder="如：10" value={shortDistanceFee} onChange={(e) => setShortDistanceFee(e.target.value)} />
          </div>
          {/* AI 问题提示词 */}
          <div className="mt-6">
            <label className="block mb-2 font-medium">💬 AI 问题提示词（可自定义）</label>
            <textarea
              className="border rounded-lg p-3 w-full"
              rows={3}
              placeholder="请输入你的计算目标或要求"
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
            ></textarea>
          </div>
        </div>

        <button
          className={`px-8 py-3 rounded-lg text-white text-lg mt-4 ${
            loading ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700 cursor-pointer shadow"
          }`}
          onClick={handleCalculate}
          disabled={loading}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin h-5 w-5 mr-2 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              计算中...
            </span>
          ) : "📈 计算最优方案"}
        </button>
      </div>

      {/* 计算结果 */}
      {result?.choices?.[0]?.message?.content && (
        <div className="bg-white shadow-lg rounded-xl p-6 space-y-4">
          <h2 className="text-xl font-semibold border-b pb-2">✅ AI 计算结果</h2>
          <div className="bg-gray-100 p-4 rounded-lg whitespace-pre-wrap leading-relaxed text-sm text-gray-800">
            {result.choices[0].message.content}
          </div>
          <button className="bg-yellow-500 hover:bg-yellow-600 text-white px-6 py-2 rounded-lg shadow" onClick={handleCopy}>
            📋 复制结果
          </button>
        </div>
      )}
    </div>
  );
}