# scripts/seed_question_bank_extended.py
"""
Seed many DSA questions across topics.
Run: python scripts/seed_question_bank_extended.py
"""
import sys, os, datetime

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
sys.path.insert(0, BACKEND_DIR)

from app.db.mongo import db

def upsert(q):
    db.question_bank.update_one(
        {"concept": q["concept"], "difficulty": q["difficulty"], "question": q["question"]},
        {"$setOnInsert": q},
        upsert=True
    )

def seed():
    now = datetime.datetime.utcnow()
    items = []

    # Binary search - non-coding
    items += [
        {"concept":"binary_search","difficulty":"beginner","question":"Given [1,3,5,7], find index of 5 using binary search. Explain steps.","type":"short_answer","answer":"Index 2; compare middle, go right, etc.","created_at":now},
        {"concept":"binary_search","difficulty":"intermediate","question":"Given rotated array [4,5,6,7,0,1,2], how to find 0 using modified binary search?","type":"short_answer","answer":"Use pivot detection then binary search on chosen half","created_at":now},
        {"concept":"binary_search","difficulty":"advanced","question":"Prove binary search time complexity and discuss on infinite streams.","type":"essay","answer":"O(log n) explanation","created_at":now},
    ]

    # BFS / DFS conceptual
    items += [
        {"concept":"bfs","difficulty":"beginner","question":"What is BFS and when is it used?","type":"short_answer","answer":"Layer by layer graph traversal","created_at":now},
        {"concept":"dfs","difficulty":"beginner","question":"What is DFS and how is recursion used in it?","type":"short_answer","answer":"Depth-first traversal using stack/recursion","created_at":now},
        {"concept":"graph_traversal","difficulty":"intermediate","question":"When to use BFS vs DFS? Provide examples.","type":"short_answer","answer":"Shortest path in unweighted -> BFS; topological sort -> DFS","created_at":now},
    ]

    # Sorting
    items += [
        {"concept":"merge_sort","difficulty":"beginner","question":"Explain merge sort steps on [4,2,1,3].","type":"short_answer","answer":"Divide and merge sorted halves","created_at":now},
        {"concept":"quick_sort","difficulty":"intermediate","question":"Explain quicksort partition step.","type":"short_answer","answer":"Choose pivot, partition, recurse","created_at":now},
    ]

    # Stacks / Queues
    items += [
        {"concept":"stack","difficulty":"beginner","question":"Explain stack push/pop semantics with an example.","type":"short_answer","answer":"LIFO operations push/pop","created_at":now},
        {"concept":"queue","difficulty":"beginner","question":"Explain queue enqueue/dequeue semantics.","type":"short_answer","answer":"FIFO operations","created_at":now},
    ]

    # Coding problems (Python) - use language_id=71 for Judge0 default mapping (python3)
    items += [
        {
            "concept":"binary_search",
            "difficulty":"beginner",
            "question":"Implement binary search that reads n and sorted list then a target and prints index or -1.",
            "type":"code",
            "language_id":71,
            "testcases":[
                {"stdin":"5\n1 2 3 4 5\n3\n","expected":"2"},
                {"stdin":"4\n2 4 6 8\n5\n","expected":"-1"}
            ],
            "created_at":now
        },
        {
            "concept":"merge_sort",
            "difficulty":"intermediate",
            "question":"Implement merge sort to sort a list of integers read from stdin and print sorted list.",
            "type":"code",
            "language_id":71,
            "testcases":[
                {"stdin":"5\n5 4 3 2 1\n","expected":"1 2 3 4 5"},
                {"stdin":"3\n2 2 1\n","expected":"1 2 2"}
            ],
            "created_at":now
        },
        {
            "concept":"fibonacci",
            "difficulty":"beginner",
            "question":"Print nth Fibonacci number (0-indexed) for small n.",
            "type":"code",
            "language_id":71,
            "testcases":[
                {"stdin":"5\n","expected":"5"},
                {"stdin":"0\n","expected":"0"}
            ],
            "created_at":now
        }
    ]

    # Add items to DB
    for q in items:
        upsert(q)
    print(f"Seeded {len(items)} questions (upserted).")

if __name__ == "__main__":
    seed()
