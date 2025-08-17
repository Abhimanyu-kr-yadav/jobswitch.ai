"""
Coding challenges database with data structures and algorithms problems
"""
from app.models.coding_challenge import (
    CodingChallenge, CodingDifficulty, CodingCategory, TestCase, ProgrammingLanguage
)


def get_coding_challenges():
    """Get all predefined coding challenges"""
    challenges = []
    
    # Array challenges
    challenges.append(CodingChallenge(
        id="two-sum",
        title="Two Sum",
        description="""Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.

Example:
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].""",
        difficulty=CodingDifficulty.EASY,
        category=CodingCategory.ARRAYS,
        tags=["hash-table", "array"],
        time_limit=900,  # 15 minutes
        test_cases=[
            TestCase(
                input={"nums": [2, 7, 11, 15], "target": 9},
                expected_output=[0, 1],
                explanation="nums[0] + nums[1] = 2 + 7 = 9"
            ),
            TestCase(
                input={"nums": [3, 2, 4], "target": 6},
                expected_output=[1, 2],
                explanation="nums[1] + nums[2] = 2 + 4 = 6"
            ),
            TestCase(
                input={"nums": [3, 3], "target": 6},
                expected_output=[0, 1],
                explanation="nums[0] + nums[1] = 3 + 3 = 6"
            )
        ],
        starter_code={
            "python": """def two_sum(nums, target):
    \"\"\"
    :type nums: List[int]
    :type target: int
    :rtype: List[int]
    \"\"\"
    pass""",
            "javascript": """/**
 * @param {number[]} nums
 * @param {number} target
 * @return {number[]}
 */
var twoSum = function(nums, target) {
    
};""",
            "java": """class Solution {
    public int[] twoSum(int[] nums, int target) {
        
    }
}"""
        },
        solution={
            "python": """def two_sum(nums, target):
    num_map = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    return []""",
            "javascript": """var twoSum = function(nums, target) {
    const numMap = new Map();
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (numMap.has(complement)) {
            return [numMap.get(complement), i];
        }
        numMap.set(nums[i], i);
    }
    return [];
};"""
        },
        hints=[
            "Try using a hash table to store numbers you've seen",
            "For each number, check if its complement (target - number) exists in the hash table",
            "The time complexity can be O(n) with this approach"
        ],
        companies=["Google", "Amazon", "Microsoft", "Facebook", "Apple"],
        frequency=10
    ))
    
    challenges.append(CodingChallenge(
        id="reverse-linked-list",
        title="Reverse Linked List",
        description="""Given the head of a singly linked list, reverse the list, and return the reversed list.

Example:
Input: head = [1,2,3,4,5]
Output: [5,4,3,2,1]

Example 2:
Input: head = [1,2]
Output: [2,1]

Example 3:
Input: head = []
Output: []""",
        difficulty=CodingDifficulty.EASY,
        category=CodingCategory.LINKED_LISTS,
        tags=["linked-list", "recursion"],
        time_limit=900,
        test_cases=[
            TestCase(
                input={"head": [1, 2, 3, 4, 5]},
                expected_output=[5, 4, 3, 2, 1],
                explanation="Reverse the linked list"
            ),
            TestCase(
                input={"head": [1, 2]},
                expected_output=[2, 1],
                explanation="Reverse two-node list"
            ),
            TestCase(
                input={"head": []},
                expected_output=[],
                explanation="Empty list remains empty"
            )
        ],
        starter_code={
            "python": """# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def reverse_list(head):
    \"\"\"
    :type head: ListNode
    :rtype: ListNode
    \"\"\"
    pass""",
            "javascript": """/**
 * Definition for singly-linked list.
 * function ListNode(val, next) {
 *     this.val = (val===undefined ? 0 : val)
 *     this.next = (next===undefined ? null : next)
 * }
 */
/**
 * @param {ListNode} head
 * @return {ListNode}
 */
var reverseList = function(head) {
    
};"""
        },
        solution={
            "python": """def reverse_list(head):
    prev = None
    current = head
    
    while current:
        next_temp = current.next
        current.next = prev
        prev = current
        current = next_temp
    
    return prev""",
            "javascript": """var reverseList = function(head) {
    let prev = null;
    let current = head;
    
    while (current !== null) {
        let nextTemp = current.next;
        current.next = prev;
        prev = current;
        current = nextTemp;
    }
    
    return prev;
}"""
        },
        hints=[
            "Use three pointers: previous, current, and next",
            "Iterate through the list and reverse the links",
            "Don't forget to handle the edge case of an empty list"
        ],
        companies=["Google", "Amazon", "Microsoft", "Facebook"],
        frequency=9
    ))
    
    challenges.append(CodingChallenge(
        id="valid-parentheses",
        title="Valid Parentheses",
        description="""Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.

Example:
Input: s = "()"
Output: true

Example 2:
Input: s = "()[]{}"
Output: true

Example 3:
Input: s = "(]"
Output: false""",
        difficulty=CodingDifficulty.EASY,
        category=CodingCategory.STACKS_QUEUES,
        tags=["stack", "string"],
        time_limit=900,
        test_cases=[
            TestCase(
                input={"s": "()"},
                expected_output=True,
                explanation="Valid parentheses"
            ),
            TestCase(
                input={"s": "()[]{}"}, 
                expected_output=True,
                explanation="All brackets properly matched"
            ),
            TestCase(
                input={"s": "(]"},
                expected_output=False,
                explanation="Mismatched bracket types"
            ),
            TestCase(
                input={"s": "([)]"},
                expected_output=False,
                explanation="Incorrect order"
            )
        ],
        starter_code={
            "python": """def is_valid(s):
    \"\"\"
    :type s: str
    :rtype: bool
    \"\"\"
    pass""",
            "javascript": """/**
 * @param {string} s
 * @return {boolean}
 */
var isValid = function(s) {
    
};"""
        },
        solution={
            "python": """def is_valid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    
    for char in s:
        if char in mapping:
            if not stack or stack.pop() != mapping[char]:
                return False
        else:
            stack.append(char)
    
    return not stack""",
            "javascript": """var isValid = function(s) {
    const stack = [];
    const mapping = {')': '(', '}': '{', ']': '['};
    
    for (let char of s) {
        if (char in mapping) {
            if (stack.length === 0 || stack.pop() !== mapping[char]) {
                return false;
            }
        } else {
            stack.push(char);
        }
    }
    
    return stack.length === 0;
}"""
        },
        hints=[
            "Use a stack data structure",
            "Push opening brackets onto the stack",
            "When you see a closing bracket, check if it matches the most recent opening bracket"
        ],
        companies=["Google", "Amazon", "Microsoft", "Facebook", "Apple"],
        frequency=8
    ))
    
    challenges.append(CodingChallenge(
        id="maximum-subarray",
        title="Maximum Subarray",
        description="""Given an integer array nums, find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.

A subarray is a contiguous part of an array.

Example:
Input: nums = [-2,1,-3,4,-1,2,1,-5,4]
Output: 6
Explanation: [4,-1,2,1] has the largest sum = 6.

Example 2:
Input: nums = [1]
Output: 1

Example 3:
Input: nums = [5,4,-1,7,8]
Output: 23""",
        difficulty=CodingDifficulty.MEDIUM,
        category=CodingCategory.DYNAMIC_PROGRAMMING,
        tags=["array", "divide-and-conquer", "dynamic-programming"],
        time_limit=1200,  # 20 minutes
        test_cases=[
            TestCase(
                input={"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4]},
                expected_output=6,
                explanation="[4,-1,2,1] has the largest sum = 6"
            ),
            TestCase(
                input={"nums": [1]},
                expected_output=1,
                explanation="Single element"
            ),
            TestCase(
                input={"nums": [5, 4, -1, 7, 8]},
                expected_output=23,
                explanation="All positive numbers"
            ),
            TestCase(
                input={"nums": [-1]},
                expected_output=-1,
                explanation="Single negative number"
            )
        ],
        starter_code={
            "python": """def max_subarray(nums):
    \"\"\"
    :type nums: List[int]
    :rtype: int
    \"\"\"
    pass""",
            "javascript": """/**
 * @param {number[]} nums
 * @return {number}
 */
var maxSubArray = function(nums) {
    
};"""
        },
        solution={
            "python": """def max_subarray(nums):
    max_sum = nums[0]
    current_sum = nums[0]
    
    for i in range(1, len(nums)):
        current_sum = max(nums[i], current_sum + nums[i])
        max_sum = max(max_sum, current_sum)
    
    return max_sum""",
            "javascript": """var maxSubArray = function(nums) {
    let maxSum = nums[0];
    let currentSum = nums[0];
    
    for (let i = 1; i < nums.length; i++) {
        currentSum = Math.max(nums[i], currentSum + nums[i]);
        maxSum = Math.max(maxSum, currentSum);
    }
    
    return maxSum;
}"""
        },
        hints=[
            "This is a classic dynamic programming problem (Kadane's algorithm)",
            "At each position, decide whether to start a new subarray or extend the current one",
            "Keep track of the maximum sum seen so far"
        ],
        companies=["Google", "Amazon", "Microsoft", "Facebook", "Apple"],
        frequency=9
    ))
    
    challenges.append(CodingChallenge(
        id="binary-tree-inorder",
        title="Binary Tree Inorder Traversal",
        description="""Given the root of a binary tree, return the inorder traversal of its nodes' values.

Example:
Input: root = [1,null,2,3]
Output: [1,3,2]

Example 2:
Input: root = []
Output: []

Example 3:
Input: root = [1]
Output: [1]

Follow up: Recursive solution is trivial, could you do it iteratively?""",
        difficulty=CodingDifficulty.EASY,
        category=CodingCategory.TREES,
        tags=["stack", "tree", "depth-first-search", "binary-tree"],
        time_limit=900,
        test_cases=[
            TestCase(
                input={"root": [1, None, 2, 3]},
                expected_output=[1, 3, 2],
                explanation="Inorder: left, root, right"
            ),
            TestCase(
                input={"root": []},
                expected_output=[],
                explanation="Empty tree"
            ),
            TestCase(
                input={"root": [1]},
                expected_output=[1],
                explanation="Single node"
            )
        ],
        starter_code={
            "python": """# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def inorder_traversal(root):
    \"\"\"
    :type root: TreeNode
    :rtype: List[int]
    \"\"\"
    pass""",
            "javascript": """/**
 * Definition for a binary tree node.
 * function TreeNode(val, left, right) {
 *     this.val = (val===undefined ? 0 : val)
 *     this.left = (left===undefined ? null : left)
 *     this.right = (right===undefined ? null : right)
 * }
 */
/**
 * @param {TreeNode} root
 * @return {number[]}
 */
var inorderTraversal = function(root) {
    
};"""
        },
        solution={
            "python": """def inorder_traversal(root):
    result = []
    
    def inorder(node):
        if node:
            inorder(node.left)
            result.append(node.val)
            inorder(node.right)
    
    inorder(root)
    return result""",
            "javascript": """var inorderTraversal = function(root) {
    const result = [];
    
    function inorder(node) {
        if (node !== null) {
            inorder(node.left);
            result.push(node.val);
            inorder(node.right);
        }
    }
    
    inorder(root);
    return result;
}"""
        },
        hints=[
            "Inorder traversal visits nodes in this order: left subtree, root, right subtree",
            "You can solve this recursively or iteratively using a stack",
            "The recursive solution is straightforward - try the iterative approach for a challenge"
        ],
        companies=["Google", "Amazon", "Microsoft", "Facebook"],
        frequency=7
    ))
    
    challenges.append(CodingChallenge(
        id="merge-intervals",
        title="Merge Intervals",
        description="""Given an array of intervals where intervals[i] = [starti, endi], merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.

Example:
Input: intervals = [[1,3],[2,6],[8,10],[15,18]]
Output: [[1,6],[8,10],[15,18]]
Explanation: Since intervals [1,3] and [2,6] overlaps, merge them into [1,6].

Example 2:
Input: intervals = [[1,4],[4,5]]
Output: [[1,5]]
Explanation: Intervals [1,4] and [4,5] are considered overlapping.""",
        difficulty=CodingDifficulty.MEDIUM,
        category=CodingCategory.ARRAYS,
        tags=["array", "sorting"],
        time_limit=1200,
        test_cases=[
            TestCase(
                input={"intervals": [[1, 3], [2, 6], [8, 10], [15, 18]]},
                expected_output=[[1, 6], [8, 10], [15, 18]],
                explanation="Merge overlapping intervals [1,3] and [2,6]"
            ),
            TestCase(
                input={"intervals": [[1, 4], [4, 5]]},
                expected_output=[[1, 5]],
                explanation="Adjacent intervals are merged"
            ),
            TestCase(
                input={"intervals": [[1, 4], [0, 4]]},
                expected_output=[[0, 4]],
                explanation="Completely overlapping intervals"
            )
        ],
        starter_code={
            "python": """def merge(intervals):
    \"\"\"
    :type intervals: List[List[int]]
    :rtype: List[List[int]]
    \"\"\"
    pass""",
            "javascript": """/**
 * @param {number[][]} intervals
 * @return {number[][]}
 */
var merge = function(intervals) {
    
};"""
        },
        solution={
            "python": """def merge(intervals):
    if not intervals:
        return []
    
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    
    for current in intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            last[1] = max(last[1], current[1])
        else:
            merged.append(current)
    
    return merged""",
            "javascript": """var merge = function(intervals) {
    if (intervals.length === 0) return [];
    
    intervals.sort((a, b) => a[0] - b[0]);
    const merged = [intervals[0]];
    
    for (let i = 1; i < intervals.length; i++) {
        const current = intervals[i];
        const last = merged[merged.length - 1];
        
        if (current[0] <= last[1]) {
            last[1] = Math.max(last[1], current[1]);
        } else {
            merged.push(current);
        }
    }
    
    return merged;
}"""
        },
        hints=[
            "First, sort the intervals by their start time",
            "Iterate through sorted intervals and merge overlapping ones",
            "Two intervals overlap if the start of the second is <= end of the first"
        ],
        companies=["Google", "Amazon", "Microsoft", "Facebook", "Apple"],
        frequency=8
    ))
    
    return challenges


def get_challenges_by_category(category: CodingCategory):
    """Get challenges filtered by category"""
    all_challenges = get_coding_challenges()
    return [c for c in all_challenges if c.category == category]


def get_challenges_by_difficulty(difficulty: CodingDifficulty):
    """Get challenges filtered by difficulty"""
    all_challenges = get_coding_challenges()
    return [c for c in all_challenges if c.difficulty == difficulty]


def get_challenge_by_id(challenge_id: str):
    """Get a specific challenge by ID"""
    all_challenges = get_coding_challenges()
    for challenge in all_challenges:
        if challenge.id == challenge_id:
            return challenge
    return None


def get_challenges_for_company(company: str):
    """Get challenges commonly asked by a specific company"""
    all_challenges = get_coding_challenges()
    return [c for c in all_challenges if company.lower() in [comp.lower() for comp in c.companies]]