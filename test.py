from app import agent

test_cases = [
    {
        "question": "In what year was the first iPhone introduced?",
        "expected": "2007",
        "category": "factual",
    },
    {
        "question": "How many studio albums did Coldplay release between 2000 and 2010?",
        "expected": "4",
        "category": "counting",
    },
    {
        "question": "What is 17 multiplied by 23?",
        "expected": "391",
        "category": "calculation",
    },
]


def test_agent_evaluation():
    for case in test_cases:
        result = agent.invoke({
            "question": case["question"],
            "findings": [],
            "evidence": [],
            "delegations": 0,
        })

        predicted = str(result.get("answer", "")).strip()
        expected = case["expected"]

        print("\nQuestion:", case["question"])
        print("Category:", case["category"])
        print("Expected:", expected)
        print("Predicted:", predicted)
        print("Correct:", predicted == expected)
        print("Agents used:", [
            finding["agent"]
            for finding in result.get("findings", [])
        ])

        assert predicted == expected, (
            f"Incorrect answer for: {case['question']}"
        )