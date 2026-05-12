import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

# Load env variables
load_dotenv()

ABSOLUTE_PROMPT = PromptTemplate.from_template("""
Evaluate the following answer to the question based on 4 dimensions (1-5 scale):
1. Factual accuracy (1=many errors, 5=fully accurate)
2. Relevance (1=off-topic, 5=directly answers)
3. Conciseness (1=verbose, 5=appropriately brief)
4. Helpfulness (1=useless, 5=highly useful)

Question: {question}
Answer: {answer}

Output JSON ONLY:
{{"accuracy": int, "relevance": int, "conciseness": int, "helpfulness": int, "overall": float}}
""")

def parse_absolute_output(text):
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        return parsed
    except json.JSONDecodeError:
        return {"accuracy": 0, "relevance": 0, "conciseness": 0, "helpfulness": 0, "overall": 0.0}

def absolute_score(question, answer, judge_llm):
    prompt = ABSOLUTE_PROMPT.format(question=question, answer=answer)
    out = judge_llm.invoke(prompt)
    parsed = parse_absolute_output(out.content)
    
    # Calculate overall if not provided properly
    if 'overall' not in parsed or parsed['overall'] == 0.0:
        dims = ['accuracy', 'relevance', 'conciseness', 'helpfulness']
        valid_dims = [parsed.get(d, 0) for d in dims if isinstance(parsed.get(d, 0), (int, float))]
        parsed['overall'] = sum(valid_dims) / len(valid_dims) if valid_dims else 0.0
        
    return parsed

def main():
    print("Loading test data...")
    if os.path.exists("phase-a/ragas_results.csv"):
        testset_path = "phase-a/ragas_results.csv"
    else:
        testset_path = "../phase-a/ragas_results.csv"
        
    if not os.path.exists(testset_path):
        print(f"Warning: {testset_path} not found. Running with placeholder data.")
        df = pd.DataFrame({
            "question": ["What is X?"] * 30,
            "answer": ["Answer prod"] * 30
        })
    else:
        df = pd.read_csv(testset_path)
        
    df = df.head(30)
    judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    results = []
    print("Running absolute judge...")
    for i, row in df.iterrows():
        print(f"  Scoring [{i+1}/30]")
        scores = absolute_score(row['question'], row['answer'], judge_llm)
        scores['question'] = row['question']
        results.append(scores)
        
    res_df = pd.DataFrame(results)
    # Reorder columns
    cols = ['question', 'accuracy', 'relevance', 'conciseness', 'helpfulness', 'overall']
    res_df = res_df[[c for c in cols if c in res_df.columns]]
    res_df.to_csv("absolute_scores.csv", index=False)
    print("Saved absolute_scores.csv")

if __name__ == "__main__":
    main()
