# author: justin ngo

import anthropic
import argparse
from pydantic import BaseModel
import json
import time
from collections import Counter


class Ticket_Analysis(BaseModel):
    category: str
    priority: str
    summary: str

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="sample_tickets.json")
parser.add_argument("--output", default="results.json")
args = parser.parse_args()

CATEGORY = ["Billing", "Technical Issue", "Account Access", 
                "Feature Request", "Complaint", "General Inquiry"]

PRIORITY = ["low", "medium", "high", "urgent"]


tool = {
    "name" : "record_ticket_analysis",
    "description" : "Record the classification of a customer support ticket.",
    "input_schema" : {
        "type" : "object",
        "properties" : {
            "category" : {
                "type" : "string",
                "enum" : CATEGORY,
            },
            "priority" : {
                "type" : "string",
                "enum" : PRIORITY,
            },
            "summary" : {
                "type" : "string",
                "description" : "One-sentence summary of the issue.",
            },
        },
        "required" : ["category", "priority", "summary"],
    },
}

client = anthropic.Anthropic()  # automatically reads ANTHROPIC_API_KEY

def analyze_ticket(client, ticket_text):
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=500,
        tools=[tool],
        tool_choice={"type" : "tool", "name" : "record_ticket_analysis"},
        messages=[{
            "role": "user",
            "content": f"Classify this support ticket:\n\n{ticket_text}"
        }],
    )
    for block in response.content:
        if block.type == "tool_use":
            result = block.input
            analysis = Ticket_Analysis(**result)
            if analysis.category not in CATEGORY:
                raise ValueError(f"Unexpected category : {analysis.category}")
            return analysis.model_dump() # model_dump() returns a dictionary
    raise RuntimeError("No tool_use block in response")

def analyze_with_retry(client, ticket_text, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        try:
            return analyze_ticket(client, ticket_text)
        except Exception as e:
            if attempt == max_attempts:
                raise
            print(f"Attempt {attempt} failed, retrying...")
            time.sleep(attempt)

# Read file
with open(args.input, "r", encoding="utf-8") as file:
    tickets = json.load(file)

results = []
for i, ticket_text in enumerate(tickets):
    try:
        print(f"Processing ticket {i + 1} of {len(tickets)}")
        analysis = analyze_with_retry(client, ticket_text)
        analysis["ticket_text"] = ticket_text
        results.append(analysis)
    except Exception as e:
        print(f"Ticket {i + 1} failed: {e}")
        results.append({"ticket_text" : ticket_text, "error" : str(e)})

# Write to file
with open(args.output, "w", encoding="utf-8") as file:
    json.dump(results, file, indent=2)

print("Saved results.json")

# print summary:

good = []
for r in results:
    if "error" not in r:
        good.append(r)

print("\n--- Summary ---")
print(f"Processed {len(good)} of {len(results)} tickets successfully")

print("\nBy category:")
for category, count in Counter(r["category"] for r in good).most_common():
    print(f"  {category}: {count}")

print("\nBy priority:")
for priority, count in Counter(r["priority"] for r in good).most_common():
    print(f"  {priority}: {count}")