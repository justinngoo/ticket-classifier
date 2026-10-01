# Support Ticket Classifier

A Python script that takes unstructured customer support tickets and
classifies them into categories, extracting key fields (priority, summary)
as structured JSON by using the Anthropic API's tool-use feature to force
reliable output instead of parsing freeform text.


## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set your Anthropic API key as an environment variable:

```bash
export ANTHROPIC_API_KEY=sk-ant-...        # Windows PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
```

## Usage

```bash
python classifier.py --input sample_tickets.json --output results.json
```

## Input format

A JSON array of ticket strings:

```json
[
  "I was charged twice for my subscription this month, please refund me.",
  "The app crashes every time I open settings on my phone."
]
```

## Output format

```json
{
  "category": "Billing",
  "priority": "high",
  "summary": "Customer was charged twice and wants a refund.",
  "ticket_text": "I was charged twice for my subscription this month, please refund me."
}
```

## How it works

1. Each ticket is sent to the Anthropic API along with a tool definition
   describing the exact fields and allowed values to extract.
2. `tool_choice` forces the model to fill in that schema rather than reply
   in plain text.
3. The result is validated against a Pydantic model before being saved,
   catching any unexpected or missing fields immediately.
4. Failed requests are retried a few times before being logged as errors,
   so one bad ticket doesn't stop the whole batch.
5. A summary of ticket counts by category and priority prints at the end.

## Possible extensions

- Add more categories or a confidence score per ticket
- Process tickets concurrently instead of one at a time
- Feed `results.json` into a small dashboard
