import os
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings 

load_dotenv()

@tool
def search_hidden_gems(query: str) -> str:
    """
    Searches the MongoDB database for hidden gems, offbeat locations, and places (Sthan) in India based on user preference.
    Use this tool to find destinations, waterfalls, treks, or secret spots matching the user's vibe.
    """
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("DB_NAME")]
        collection = db[os.getenv("COLLECTION_NAME")]

        # HUM TERA WALA TARIQA USE KARENGE YAHAN! 🔥
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001") 
        
        query_vector = embeddings.embed_query(query)

        # Vector Search Pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": os.getenv("VECTOR_INDEX_NAME"),
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": 100,
                    "limit": 3
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "localName": 1,      
                    "description": 1,
                    "district": 1,       
                    "state": 1,          
                    "hashtags": 1,       
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        results = list(collection.aggregate(pipeline))

        if not results:
            return f"Sorry, database mein '{query}' se match karta hua koi hidden gem nahi mila."

        # FORMATTING OUTPUT FOR AGENT
        response_text = "Database se ye top hidden gems mile hain:\n"
        for i, res in enumerate(results, 1):
            name = res.get('localName', 'Unknown Place')
            dist = res.get('district', 'Unknown District')
            state = res.get('state', 'Unknown State')
            desc = res.get('description', 'No description available.')
            tags = ", ".join(res.get('hashtags', [])) 

            response_text += f"{i}. {name} ({dist}, {state}): {desc} | Tags: {tags}\n"

        return response_text

    except Exception as e:
        return f"Database search fail ho gaya: {str(e)}"
    finally:
        client.close()