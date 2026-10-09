# StudySprint AI

**Make your next study session count.**

> **🚀 Live demo: [https://studysprintagent.netlify.app/](https://studysprintagent.netlify.app/)**

StudySprint AI is a beginner-friendly AI study-planning agent that turns a subject, a list of topics, and the time available into a practical study schedule. It is built with Amazon Bedrock, AWS Lambda, and a lightweight HTML/CSS/JavaScript frontend.

Built for the **AWS Builder Center Weekend Challenge**: “Build an agent people actually enjoy using.”

## Try the live demo

Open **[StudySprint AI — Live Website](https://studysprintagent.netlify.app/)**, enter a subject, topics, available study time, and break length, then generate a study plan.

Example:
- **Subject:** Data Structures
- **Topics:** Stacks, Queues, Linked Lists, Trees
- **Available time:** 90 minutes
- **Break length:** 5 minutes

The agent returns a topic-by-topic schedule and a clear next action.

## What it does

1. Accepts a subject and up to eight comma-separated topics.
2. Lets the student choose available study time and break length.
3. Sends the request to an AWS Lambda backend over HTTPS.
4. Uses Amazon Bedrock Converse with tool use to request a schedule from `create_study_schedule`.
5. Returns the study plan for display in the browser.

The schedule tool performs the schedule calculation in Lambda; Bedrock provides the conversational explanation.

## Technology stack

- **Amazon Bedrock Converse** — model response and tool-use flow.
- **AWS Lambda (Python)** — backend request handling and schedule logic.
- **AWS Lambda Function URL** — HTTPS endpoint for the frontend.
- **Boto3** — AWS SDK for Python.
- **HTML, CSS, JavaScript** — responsive single-page frontend.
- **Netlify** — frontend hosting.
- **Amazon CloudWatch Logs** — backend troubleshooting.

## Architecture

```text
Student
  ↓
StudySprint AI frontend (Netlify)
  ↓ HTTPS POST (JSON)
AWS Lambda Function URL
  ↓
AWS Lambda (Python + Boto3)
  ↓
Amazon Bedrock Converse
  ↔ create_study_schedule tool in Lambda
  ↓
Study plan returned to the frontend
```

The current version does not require a database. AWS credentials are not stored in the browser; the Lambda execution role is used for AWS service access.

## Repository structure

```text
StudySprint-AI/
├── README.md
├── .gitignore
├── IAMR.png
├── LAMBDA.png
├── backend/
│   ├── bedrock-invoke-policy.json
│   └── lambda_function.py
└── frontend/
    └── index.html
```

## Run the frontend locally

From the repository root:

```bash
cd frontend
python3 -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000). The frontend's `API_URL` must point to the deployed Lambda Function URL. For local testing, configure the Lambda Function URL CORS policy to allow `http://localhost:8000`.

## AWS deployment overview

1. Create a Python AWS Lambda function and deploy `backend/lambda_function.py`.
2. Configure the model ID using the `MODEL_ID` environment variable and verify that the model is available to your account and region.
3. Give the Lambda execution role only the Bedrock permissions required for the selected model. See `backend/bedrock-invoke-policy.json` as a starting point and adjust it to your account and region.
4. Configure a Lambda Function URL and its CORS policy for the exact frontend origin, `POST`, and `content-type`.
5. Set the frontend `API_URL` in `frontend/index.html` to the Function URL.
6. Deploy the `frontend/` directory to Netlify.

## Testing

Try a variety of inputs, such as a single topic, several topics, missing required fields, and a model/permission error. Review CloudWatch Logs if the backend returns an error. A successful response with `tool_used: true` indicates that the schedule tool was used for that request.

If you add or restore automated tests to this repository, run them from the project root using the test command documented alongside those tests.

## Security and cost notes

- Bedrock invocations and other AWS usage may incur charges. Review current pricing and monitor your AWS billing dashboard.
- Set an AWS Budget alert before running a public demo.
- Never commit AWS access keys, secret keys, tokens, or `.env` files.
- A Lambda Function URL configured with `NONE` authentication is publicly invocable by anyone who has the URL. Consider authentication, throttling, abuse controls, and monitoring before using it for production.
- Keep the Lambda execution role restricted to the actions and model resources actually required.

## Project links

- **Live demo:** https://studysprintagent.netlify.app/
- **GitHub repository:** https://github.com/GunnerJyo/StudySprint-AI

## License

No license has been specified yet. Add a `LICENSE` file if you intend to publish this project as open source.
