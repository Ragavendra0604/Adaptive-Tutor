import sys, os, datetime

# ---------------------------------------------------------
# SETUP
# ---------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BASE_DIR)

try:
    from app.db.mongo import db
    print("Connected to DB.")
except ImportError:
    print("Error: Could not import db. Ensure app.db.mongo is accessible.")
    sys.exit(1)

def upsert(q):
    # Upsert based on concept + question text to prevent duplicates
    db.question_bank.update_one(
        {"concept": q["concept"], "question": q["question"]},
        {"$setOnInsert": q},
        upsert=True
    )

def get_massive_dataset(now):
    return [
        # ==============================================================================
        # 1. SEARCHING & SORTING (Linear, Insertion, Selection, Heap, Counting, Radix)
        # ==============================================================================
        {
            "concept": "sorting_stability", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "What does it mean for a sorting algorithm to be 'stable'?",
            "expected_answer": "A stable sort maintains the relative order of records with equal keys (i.e., if A appears before B in input and A==B, A appears before B in output)."
        },
        {
            "concept": "insertion_sort", "difficulty": "beginner", "type": "short_answer", "created_at": now,
            "question": "Why is Insertion Sort efficient for nearly sorted arrays?",
            "expected_answer": "The inner loop terminates early when it finds the correct position. For nearly sorted data, time complexity approaches O(n)."
        },
        {
            "concept": "selection_sort", "difficulty": "beginner", "type": "short_answer", "created_at": now,
            "question": "Does Selection Sort adapt to the data (e.g., run faster if data is sorted)?",
            "expected_answer": "No. Selection sort always performs O(n^2) comparisons regardless of the initial order of elements."
        },
        {
            "concept": "radix_sort", "difficulty": "advanced", "type": "essay", "created_at": now,
            "question": "Explain the difference between LSD (Least Significant Digit) and MSD Radix Sort.",
            "expected_answer": "LSD processes digits from right to left (1s, 10s, 100s), requiring a stable sort at each step. MSD processes left to right and is recursive, often using buckets."
        },
        {
            "concept": "bucket_sort", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "What is the worst-case time complexity of Bucket Sort and when does it happen?",
            "expected_answer": "O(n^2). This happens when all elements are placed into a single bucket, forcing the algorithm to rely on the sorting algorithm used within that bucket (often insertion sort)."
        },
        {   # CODE: BUBBLE SORT
            "concept": "bubble_sort", "difficulty": "beginner", "type": "code", "language_id": 71, "created_at": now,
            "question": "Implement Bubble Sort. Input: N, then N integers. Print sorted list.",
            "testcases": [{"stdin": "4\n4 3 2 1", "expected": "1 2 3 4"}, {"stdin": "3\n1 2 3", "expected": "1 2 3"}]
        },

        # ==============================================================================
        # 2. TREES (BST, AVL, RB, Segment, Fenwick, Trie)
        # ==============================================================================
        {
            "concept": "binary_tree_traversal", "difficulty": "beginner", "type": "short_answer", "created_at": now,
            "question": "List the order of nodes for Inorder traversal.",
            "expected_answer": "Left Subtree -> Root -> Right Subtree."
        },
        {
            "concept": "avl_tree", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "What specific rotations are performed in an AVL tree when a node is inserted into the Right child of a Right subtree (Right-Right Case)?",
            "expected_answer": "A single Left Rotation."
        },
        {
            "concept": "red_black_tree", "difficulty": "advanced", "type": "essay", "created_at": now,
            "question": "State two key properties of a Red-Black Tree regarding node colors.",
            "expected_answer": "1. The root is always black. 2. No two red nodes can be adjacent (a red node cannot have a red parent or red child). 3. Every path from a node to its descendant NULL nodes has the same number of black nodes."
        },
        {
            "concept": "segment_tree", "difficulty": "advanced", "type": "short_answer", "created_at": now,
            "question": "Given array size N=100, what is the approximate size of the array required to build a Segment Tree?",
            "expected_answer": "Approximately 4*N. A safe upper bound is 400."
        },
        {
            "concept": "fenwick_tree", "difficulty": "advanced", "type": "short_answer", "created_at": now,
            "question": "In a Binary Indexed Tree (Fenwick), how do you get the parent index of index 'i'?",
            "expected_answer": "Parent = i - (i & -i). This removes the last set bit."
        },
        {
            "concept": "trie", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "If you insert the word 'apple' into a Trie, how many nodes are created if the Trie was initially empty?",
            "expected_answer": "6 nodes (1 root + 5 nodes for 'a', 'p', 'p', 'l', 'e')."
        },
        {   # CODE: BST INSERT
            "concept": "binary_search_tree", "difficulty": "intermediate", "type": "code", "language_id": 71, "created_at": now,
            "question": "Write a program that accepts N numbers and inserts them into a BST. Print the Inorder traversal.",
            "testcases": [{"stdin": "5\n50 30 20 40 70", "expected": "20 30 40 50 70"}]
        },

        # ==============================================================================
        # 3. GRAPH ALGORITHMS (BFS, DFS, Shortest Paths, MST, Topo)
        # ==============================================================================
        {
            "concept": "graph_cycle_directed", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "How can DFS be used to detect a cycle in a Directed Graph?",
            "expected_answer": "By tracking the recursion stack. If a node is visited that is currently in the recursion stack (a 'back edge'), a cycle exists."
        },
        {
            "concept": "floyd_warshall", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "What is the time complexity of the Floyd-Warshall algorithm?",
            "expected_answer": "O(V^3), where V is the number of vertices."
        },
        {
            "concept": "mst_prim", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "What data structure is crucial for implementing Prim's Algorithm efficiently?",
            "expected_answer": "A Priority Queue (Min-Heap) to efficiently fetch the edge with the minimum weight connected to the visited set."
        },
        {
            "concept": "topological_sort", "difficulty": "beginner", "type": "short_answer", "created_at": now,
            "question": "Can Topological Sort be applied to a graph with a cycle? Explain.",
            "expected_answer": "No. Topological sort requires a Directed Acyclic Graph (DAG). If a cycle exists, there is no valid linear ordering."
        },
        {   # CODE: DFS
            "concept": "dfs", "difficulty": "intermediate", "type": "code", "language_id": 71, "created_at": now,
            "question": "Implement DFS for a graph. Input: V E, then E edges. Print nodes visited starting from node 0.",
            "testcases": [{"stdin": "4 3\n0 1\n0 2\n1 3", "expected": "0 1 3 2"}] # Note: Order depends on implementation, simplified for example
        },

        # ==============================================================================
        # 4. DYNAMIC PROGRAMMING (Classic problems)
        # ==============================================================================
        {
            "concept": "dp_lis", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "What is the time complexity of the standard DP approach for Longest Increasing Subsequence (LIS)?",
            "expected_answer": "O(n^2). (Though it can be improved to O(n log n) with binary search)."
        },
        {
            "concept": "edit_distance", "difficulty": "advanced", "type": "short_answer", "created_at": now,
            "question": "In the Edit Distance problem, what three operations are allowed?",
            "expected_answer": "Insert, Delete, and Replace."
        },
        {
            "concept": "egg_dropping", "difficulty": "advanced", "type": "essay", "created_at": now,
            "question": "Describe the state transition for the Egg Dropping Puzzle with K eggs and N floors.",
            "expected_answer": "dp[k][n] = 1 + min(max(dp[k-1][x-1], dp[k][n-x])) for all x in 1 to n. We minimize the worst case of either the egg breaking (check lower floors) or not breaking (check upper floors)."
        },
        {
            "concept": "matrix_chain_mult", "difficulty": "advanced", "type": "short_answer", "created_at": now,
            "question": "What does Matrix Chain Multiplication DP try to minimize?",
            "expected_answer": "It minimizes the total number of scalar multiplications required to multiply a chain of matrices."
        },
        {   # CODE: FIBONACCI (DP Intro)
            "concept": "dp_fib", "difficulty": "beginner", "type": "code", "language_id": 71, "created_at": now,
            "question": "Calculate the Nth Fibonacci number using DP (tabulation). Input: N. Output: Fib(N).",
            "testcases": [{"stdin": "10", "expected": "55"}, {"stdin": "5", "expected": "5"}]
        },

        # ==============================================================================
        # 5. LINKED LISTS
        # ==============================================================================
        {
            "concept": "linked_list_middle", "difficulty": "beginner", "type": "short_answer", "created_at": now,
            "question": "How do you find the middle of a Linked List in one pass?",
            "expected_answer": "Use two pointers. Move the 'fast' pointer 2 steps and the 'slow' pointer 1 step. When 'fast' reaches the end, 'slow' is at the middle."
        },
        {
            "concept": "circular_linked_list", "difficulty": "beginner", "type": "short_answer", "created_at": now,
            "question": "How do you detect if you have reached the end of a Circular Linked List during traversal?",
            "expected_answer": "Check if the current node's next pointer equals the Head node."
        },
        {   # CODE: DETECT LOOP (Conceptual code)
            "concept": "linked_list_loop", "difficulty": "intermediate", "type": "code", "language_id": 71, "created_at": now,
            "question": "Given a list structure, complete the function `hasCycle(head)` returning 1 or 0.",
            "testcases": [] # Usually requires a specific driver code environment
        },

        # ==============================================================================
        # 6. HASHING
        # ==============================================================================
        {
            "concept": "hashing_probing", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "Explain 'Linear Probing' in open addressing.",
            "expected_answer": "If a collision occurs at index 'i', check 'i+1', then 'i+2', and so on, wrapping around until an empty slot is found."
        },
        {
            "concept": "hashing_load_factor", "difficulty": "beginner", "type": "short_answer", "created_at": now,
            "question": "What is the 'Load Factor' of a hash table?",
            "expected_answer": "Load Factor = (Total elements) / (Size of hash table). High load factor increases collisions."
        },

        # ==============================================================================
        # 7. GREEDY ALGORITHMS
        # ==============================================================================
        {
            "concept": "huffman_coding", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "Why is Huffman Coding considered a 'Prefix Code'?",
            "expected_answer": "No code assigned to a character is the prefix of the code assigned to any other character, ensuring unambiguous decoding."
        },
        {
            "concept": "fractional_knapsack", "difficulty": "intermediate", "type": "short_answer", "created_at": now,
            "question": "Can Greedy strategy solve the Fractional Knapsack problem? Why?",
            "expected_answer": "Yes. We can simply pick items with the highest Value-to-Weight ratio first until the knapsack is full. This does NOT work for 0/1 Knapsack."
        }
    ]

def seed():
    now = datetime.datetime.now()
    items = get_massive_dataset(now)
    
    print(f"Preparing to seed {len(items)} questions...")
    
    count = 0
    for q in items:
        try:
            upsert(q)
            count += 1
            if count % 10 == 0:
                print(f"Seeded {count}...")
        except Exception as e:
            print(f"Failed to seed {q.get('concept')}: {e}")

    print(f"Success! Total questions in bank: {count}")

if __name__ == "__main__":
    seed()