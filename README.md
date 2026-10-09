# StudySprint AI

**Make your next study session count.**

StudySprint AI is a beginner-friendly AI study-planning agent that turns a subject, a list of topics, and the time available into a practical study schedule. It is built with Amazon Bedrock, AWS Lambda, and a lightweight static HTML frontend.

> Built for the AWS Builder Center Weekend Challenge: “Build an agent people actually enjoy using.”

## Live Demo

- **Website:** https://studysprintagent.netlify.app/
- **AWS Lambda Function URL:** configured in the frontend source. Avoid posting this URL publicly if you later add sensitive functionality or leave the endpoint open to unrestricted use.

## What it does

1. Accepts a subject and up to eight comma-separated topics.
2. Lets the student choose available study time and break length.
3. Sends the request to an AWS Lambda backend.
4. Uses Amazon Bedrock Converse with tool use to request a deterministic schedule from `create_study_schedule`.
5. Returns a readable study plan and one immediate next action.

The schedule tool divides study time between the topics and adds short breaks between study blocks when appropriate. Input limits help keep sessions manageable.

## Built with

- **Amazon Bedrock** — generates the conversational explanation and uses tool calling.
- **AWS Lambda** — hosts the Python backend and handles requests from the frontend.
- **AWS Lambda Function URL** — provides an HTTPS endpoint for the browser.
- **Amazon CloudWatch Logs** — helps diagnose backend errors.
- **HTML, CSS, and JavaScript** — responsive single-page frontend.
- **Netlify** — static frontend hosting.
- **Python and Boto3** — backend implementation and Bedrock Converse integration.

## Architecture

```text
Student
  |
  v
StudySprint AI frontend (HTML/CSS/JavaScript on Netlify)
  |
  | HTTPS POST (JSON)
  v
AWS Lambda Function URL
  |
  v
AWS Lambda (Python + Boto3)
  |
  v
Amazon Bedrock Converse
  |
  | tool use: create_study_schedule
  v
Deterministic schedule function in Lambda
  |
  v
Bedrock explains the schedule
  |
  v
JSON response displayed in the frontend
```

No database is required for the current version. AWS credentials are not placed in the browser; the Lambda execution role is used to call Bedrock.

## Repository structure

```text
.
├── frontend/
│   └── index.html
├── backend/
│   ├── lambda_function.py
│   └── bedrock-invoke-policy.json
├── tests/
│   └── test_schedule.py
├── ARTICLE_DRAFT.md
└── README.md
```

If your repository uses different filenames or folders, update this tree to match the files you actually commit.

## Run locally

The frontend is a static page. Open `frontend/index.html` in a browser or serve it with a local HTTP server:

```bash
cd frontend
python -m http.server 8000
```

Then visit http://localhost:8000.

The frontend must contain your deployed Lambda Function URL in the `API_URL` constant. To test locally, add `http://localhost:8000` as an allowed origin in the Lambda Function URL CORS configuration. For a deployed website, allow the exact Netlify origin, such as `https://studysprintagent.netlify.app`.

## Deploy the backend on AWS

### 1. Create the Lambda function

1. Open the AWS Lambda console in a region where your chosen Bedrock model is available.
2. Create a function named `StudySprintAgent` using a supported Python runtime.
3. Copy the contents of `backend/lambda_function.py` into the Lambda code editor, or upload the backend package.
4. Set the function timeout to around 30 seconds.
5. Set the environment variable `MODEL_ID` to a model ID available to your AWS account and region. The starter default is `amazon.nova-micro-v1:0`; verify availability before using it.
6. Attach a least-privilege execution-role policy that permits invoking the selected Bedrock model.
7. Deploy the function.

### 2. Configure the Function URL

1. In the Lambda function, open **Configuration → Function URL** and create a URL if one does not already exist.
2. For a public demo, `NONE` authentication allows requests without AWS IAM signing. Anyone who obtains the URL may be able to invoke the function.
3. Configure CORS to allow the exact frontend origin, the `POST` method, and the `content-type` header.
4. Deploy/save the configuration and copy the generated URL.

The Lambda Function URL's CORS configuration should be the source of CORS headers. If you configure CORS there, avoid also adding conflicting CORS headers in the Lambda response. The current backend may need its `http_response` headers adjusted to match your final deployed configuration.

### 3. Configure the frontend

Set `API_URL` in `frontend/index.html` to your Lambda Function URL:

```javascript
const API_URL = "https://YOUR-FUNCTION-ID.lambda-url.YOUR-REGION.on.aws/";
```

Deploy the `frontend/` directory to Netlify or another static hosting service. Ensure the deployed origin exactly matches the CORS origin configured for the Function URL.

## Test it

Example input:

- **Subject:** Data Structures
- **Topics:** Stacks, Queues, Linked Lists, Trees
- **Available time:** 90 minutes
- **Break length:** 5 minutes

Expected behavior: the agent returns a schedule that allocates study time across the topics, includes breaks when appropriate, and gives a clear first action.

You can also test:
- A single topic with 30 minutes available.
- Missing subject or topics (should return a helpful client/server validation error).
- More than eight topics (the frontend should reject the input).
- A backend/model permission error (the frontend should show an error rather than silently fail).

### Run local unit tests

If the test file is included and Python is installed, run from the repository root:

```bash
python -m unittest discover -s tests -v
```

These tests validate the local schedule logic only. They do not prove that your AWS account permissions, Bedrock model access, CORS configuration, or live deployment work.

## The delightful detail

StudySprint is designed around a small interaction: it asks for only a subject, topics, available time, and break length. It then returns a manageable schedule and one immediate next action instead of overwhelming the student with a long study strategy. The frontend also provides a loading state and readable error messages.

Use your own testing observations in the project article when describing whether this design worked well for users.

## Security and cost notes

- Bedrock invocations and other AWS usage may incur charges. Review current pricing and billing before testing.
- Create an AWS Budget alert and monitor CloudWatch logs.
- Never put AWS access keys or other secrets in frontend JavaScript or commit them to Git.
- A Function URL with `NONE` authentication is publicly invocable. For a public or production service, add appropriate authentication, rate limiting/throttling, abuse controls, and monitoring.
- Restrict the Lambda execution role to the model resource and actions actually required.
- Do not send sensitive personal information to the demo.

## Challenge article checklist

Before publishing the Builder Center article, verify that it:

- Is at least 500 words.
- Explains what the agent does and who it is for.
- Describes how it was built, including AWS services and tools.
- Explains the specific user-experience detail you added and how you tested it.
- Includes a live demo link, screenshot, or short clip as proof.
- Includes the `#agents` tag.
- Is published within the challenge's stated submission window.
- Has a complete Builder Profile with a profile image, country, and About section.

## License

No license has been specified yet. Add a `LICENSE` file before describing this repository as open source.
