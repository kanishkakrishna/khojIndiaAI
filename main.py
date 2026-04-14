from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# Load environment variables (API Key)
load_dotenv() 

app = FastAPI()

# 🧠 Base LLM Setup (Gemini 2.5 Flash - Fast & Smart)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)


# =====================================================================
# 🛑 PHASE 1: THE AI BOUNCER (Place Approval & Hashtags)
# =====================================================================

# 1. Input/Output Schemas
class PlaceData(BaseModel):
    localName: str
    district: str
    state: str
    description: str

class BouncerDecision(BaseModel):
    isApproved: bool = Field(description="True ONLY if it's a genuine hidden gem. False if it is a globally/nationally famous place (e.g. Taj Mahal, India Gate), gibberish, or abusive.")
    reason: str = Field(description="If rejected, briefly explain why. If approved, leave as empty string.")
    hashtags: List[str] = Field(description="List of 3 to 5 relevant hashtags if approved (e.g. ['#waterfall', '#nature']). Empty list if rejected.")

# 2. Strict LLM Setup for Bouncer
strict_bouncer_llm = llm.with_structured_output(BouncerDecision)

# 3. API Route
@app.post("/api/analyze-place")
async def analyze_place(data: PlaceData):
    print(f"🕵️‍♂️ Strict AI Bouncer scanning: {data.localName}...")
    
    prompt = f"""
    Analyze this submission for 'KhojIndia' (an app for VERY rare, unexplored 'Hidden Gems' in India).
    
    Name: {data.localName}
    Location: {data.district}, {data.state}
    Description: {data.description}
    """
    
    try:
        decision: BouncerDecision = strict_bouncer_llm.invoke(prompt)
        result = decision.model_dump()
        print("🤖 AI Decision:", result)
        return result
        
    except Exception as e:
        print("❌ AI Error:", e)
        # Fallback in case Gemini API is down
        return {"isApproved": True, "reason": "AI System Error Fallback", "hashtags": []}


# =====================================================================
# 🚀 PHASE 2: MISSION A - AI VIBE CHECKER (Review Summarizer)
# =====================================================================

# 1. Input/Output Schemas
class ReviewList(BaseModel):
    reviews: List[str]

class VibeResponse(BaseModel):
    vibe: str

# 2. Strict LLM Setup for Vibe Checker
strict_vibe_llm = llm.with_structured_output(VibeResponse)

# 3. API Route
@app.post("/api/summarize-reviews")
async def summarize_reviews(data: ReviewList):
    try:
        # Agar reviews bohot kam hain toh AI ko pareshan mat karo
        if len(data.reviews) == 0:
            return {"vibe": "No reviews yet. Be the first to share your experience!"}
        
        print(f"🧠 AI Vibe Checker is reading {len(data.reviews)} reviews...")

        prompt = f"""
        You are 'KhojIndia Vibe Checker', an expert travel AI.
        Read the following user reviews about a specific location.
        Generate a catchy, helpful, and highly accurate 2-sentence 'Vibe Summary'.
        Highlight the best aspects and any warnings (e.g., muddy road, crowded).
        Keep the tone friendly and adventurous.
        
        Reviews: {data.reviews}
        """
        
        decision: VibeResponse = strict_vibe_llm.invoke(prompt)
        result = decision.model_dump()
        
        print(f"✨ Vibe Generated: {result['vibe']}")
        return result

    except Exception as e:
        print(f"❌ Vibe Checker Error: {e}")
        return {"vibe": "Yatris are loving this place, but AI is currently taking a nap. Read the reviews below!"}