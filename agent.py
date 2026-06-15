import os
import re
import json
from dotenv import load_dotenv
from fastapi import APIRouter
from pydantic import BaseModel,field_validator
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from fastapi.responses import JSONResponse

# Custom tools
from tools.weather_tool import get_weather
from tools.route_tool import get_route_info
from tools.db_tool import search_hidden_gems

load_dotenv()
router = APIRouter()

# 👮‍♂️ Pydantic Schemas
class DayPlan(BaseModel):
    day: int
    activity: str

class TripPlan(BaseModel):
    title: str
    destination: str
    weather: str
    route: str
    itinerary: List[DayPlan]
    tips: List[str]

    # 🛡️ FIX 1: Max 4 Days Limit
    @field_validator('itinerary')
    @classmethod
    def enforce_day_limit(cls, v):
        if len(v) > 4:
            print("⚠️ AI ne 4 din se jyada ka plan diya. Truncating to 4 days.")
            return v[:4] # Sirf pehle 4 din rakh lo
        return v

    # 🛡️ FIX 2: Exactly 3 Tips Limit
    @field_validator('tips')
    @classmethod
    def enforce_tips_limit(cls, v):
        if len(v) > 3:
            print("⚠️ AI ne 3 se jyada tips diye. Keeping only top 3.")
            return v[:3] # Sirf pehli 3 tips rakh lo
        elif len(v) < 3:
            # Agar AI kam de de, toh placeholder daal do taaki UI kharab na ho
            v.extend(["Enjoy your trip!"] * (3 - len(v)))
        return v

def create_khojindia_agent():
    print("🤖 Agent Booting...")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)
    tools = [get_weather, get_route_info, search_hidden_gems]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the 'KhojIndia AI Trip Planner'. 
CRITICAL RULES:
1. GEO-FENCE: Trips must originate and end WITHIN INDIA. 
2. DURATION LIMIT: Maximum trip duration is 4 DAYS. If a user asks for more (e.g., 10 days), ONLY provide a 4-day itinerary.
3. TIPS LIMIT: Provide EXACTLY 3 bullet points in the 'tips' array. No more, no less.
4. You MUST ALWAYS use the 'search_hidden_gems' tool first to find a destination based on the user's query.
5. NEVER suggest globally or nationally famous places (like Bodh Gaya, Taj Mahal) from your own knowledge. 
6. You must ONLY build the itinerary around the places returned by the 'search_hidden_gems' tool.
7. If the database tool returns no results, do NOT make up a trip. Instead, return a JSON with a polite message in the 'tips' or 'destination' saying no hidden gem was found.
8. OUTPUT FORMAT: Return ONLY raw JSON. Do not add markdown backticks.
Schema: {{'title': '...', 'destination': '...', 'weather': '...', 'route': '...', 'itinerary': [{{'day': 1, 'activity': '...'}}], 'tips': ['tip1', 'tip2', 'tip3']}}"""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

agent_executor = create_khojindia_agent()

class UserRequest(BaseModel):
    query: str


@router.post("/api/plan-trip")
async def plan_trip(request: UserRequest):
    print(f"🗺️ Planning trip for: {request.query}")
    try:
        # 1️⃣ Agent se response lo
        response = await agent_executor.ainvoke({"input": request.query})
        output_data = response["output"]

        # 2️⃣ 🧩 TUKDE JODO (Gemini list handling)
        raw_output = ""
        if isinstance(output_data, list):
            for part in output_data:
                if isinstance(part, dict) and "text" in part:
                    raw_output += part["text"]
                elif isinstance(part, str):
                    raw_output += part
        else:
            raw_output = str(output_data)

        # 3️⃣ 🕵️‍♂️ JSON extract
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_output, re.DOTALL)

        if not json_match:
            json_match = re.search(r"\{[\s\S]*\}", raw_output)

        if json_match:
            json_str = json_match.group(1) if json_match.lastindex else json_match.group(0)

            # 4️⃣ ✅ Validate with Pydantic
            try:
                trip = TripPlan.model_validate(json.loads(json_str))
                return {
                    "status": "success",
                    "data": trip.model_dump()
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Invalid JSON format: {str(e)}"
                }

        return {"status": "error", "message": "No valid JSON found"}

    except Exception as e:
        print(f"❌ Planner Error: {str(e)}")
        return {"status": "error", "message": str(e)}