import sys, os

# ---------------------------------------------------------
# Setup path to import app.db.mongo
# ---------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BASE_DIR)

try:
    from app.db.mongo import db
    print("Connected to DB.")
except ImportError:
    print("Error: Could not import db. Ensure app.db.mongo is accessible.")
    sys.exit(1)

def scan_and_fix():
    print("Scanning for 'short_answer' questions that look like code...")
    
    # Keywords that suggest a code question
    keywords = ["implement", "write a program", "write code", "function to", "return the index"]
    
    cursor = db.question_bank.find({"type": "short_answer"})
    
    count = 0
    for doc in cursor:
        text = doc.get("question", "").lower()
        
        # Check if text contains any keyword
        if any(k in text for k in keywords):
            print(f"[-] Found candidate: {doc['_id']} | {doc.get('concept')} | {text[:50]}...")
            
            # Update the document
            db.question_bank.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "type": "code", 
                        # Default to Python (71) if not set
                        "language_id": doc.get("language_id", 71),
                        # Ensure testcases list exists (even if empty, to prevent UI crash)
                        "testcases": doc.get("testcases", [])
                    }
                }
            )
            count += 1
            
    print(f"\nSuccessfully converted {count} questions from 'short_answer' to 'code'.")

if __name__ == "__main__":
    scan_and_fix()