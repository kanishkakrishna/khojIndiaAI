from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import os
import pymongo
from dotenv import load_dotenv

load_dotenv() 

router = APIRouter()

# =====================================================================
# MONGODB SETUP
# =====================================================================
MONGO_URI = os.getenv("MONGO_URI") 
client = pymongo.MongoClient(MONGO_URI)
db = client["khojindia"] 
collection = db["Sthan"] 

# =====================================================================
# AI AND EMBEDDING SETUP
# =====================================================================
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001") 

# Generate embeddings asynchronously to avoid blocking the request loop.
async def generate_place_embedding(name: str, state: str, description: str, photo_tags: list):
    tags_string = ", ".join(photo_tags)
    smart_string = f"Place Name: {name}. Location: {state}. Description: {description}. Visual Vibes: {tags_string}."
    print(f"Generating vector for: {name}...")
    # Use the asynchronous embedding API.
    vector = await embeddings.aembed_query(smart_string)
    return vector

# =====================================================================
# PHASE 1: AI BOUNCER
# =====================================================================
class PlaceData(BaseModel):
    localName: str
    district: str
    state: str
    description: str

class BouncerDecision(BaseModel):
    isApproved: bool
    reason: str
    hashtags: List[str]

strict_bouncer_llm = llm.with_structured_output(BouncerDecision)

@router.post("/api/analyze-place")
async def analyze_place(data: PlaceData):
    print(f"🕵️‍♂️ AI Bouncer scanning: {data.localName}...")
    prompt = f"Analyze this submission for 'KhojIndia' (Hidden Gems): Name: {data.localName}, Location: {data.district}, {data.state}, Description: {data.description}"
    
    try:
        # Invoke the structured-output model asynchronously.
        decision: BouncerDecision = await strict_bouncer_llm.ainvoke(prompt)
        result = decision.model_dump()
        
        # Return a 403 response when the submission is rejected.
        if not result["isApproved"]:
            print(f"🛑 REJECTED: {result['reason']}")
            return JSONResponse(status_code=403, content=result)
            
        print("✅ APPROVED")
        return result
    except Exception as e:
        print("❌ AI Error:", e)
        return {"isApproved": True, "reason": "System Error Fallback", "hashtags": []}

# =====================================================================
# PHASE 2: AI VIBE CHECKER
# =====================================================================
class ReviewList(BaseModel):
    reviews: List[str]

class VibeResponse(BaseModel):
    vibe: str

strict_vibe_llm = llm.with_structured_output(VibeResponse)

@router.post("/api/summarize-reviews")
async def summarize_reviews(data: ReviewList):
    try:
        if not data.reviews:
            return {"vibe": "No reviews yet. Be the first!"}
        
        print(f"🧠 Summarizing {len(data.reviews)} reviews...")
        prompt = f"Generate 2-sentence Vibe Summary for: {data.reviews}"
        
        # Generate the vibe summary asynchronously.
        decision: VibeResponse = await strict_vibe_llm.ainvoke(prompt)
        return decision.model_dump()
    except Exception as e:
        print(f"❌ Summarize Review Error: {str(e)}")
        return {"vibe": "AI is taking a nap. Read reviews below!"}

# =====================================================================
# PHASE 3: CLONE HUNTER
# =====================================================================
class DuplicateCheckData(BaseModel):
    name: str
    state: str
    description: str
    photo_tags: list

@router.post("/api/check-duplicate")
async def check_duplicate(data: DuplicateCheckData):
    try:
        # Generate the candidate embedding asynchronously.
        new_vector = await generate_place_embedding(data.name, data.state, data.description, data.photo_tags)
        
        pipeline = [
            {"$vectorSearch": {"index": "vector_index", "path": "embedding", "queryVector": new_vector, "numCandidates": 10, "limit": 1}},
            # Project both legacy and current name fields for compatibility.
            {"$project": {"name": 1, "localName": 1, "score": {"$meta": "vectorSearchScore"}}}
        ]
        
        results = list(collection.aggregate(pipeline))
        if results and results[0].get('score', 0) > 0.95:
            # Prefer localName, then name, and fall back to a safe label.
            duplicate_name = results[0].get('localName') or results[0].get('name') or "Unknown Place"
            
            return {"status": "REJECT", "message": "Clone Pakda Gaya!", "duplicate_of": duplicate_name}
        
        return {"status": "ACCEPT", "new_vector": new_vector}
    except Exception as e:
        return {"status": "error", "message": str(e)}