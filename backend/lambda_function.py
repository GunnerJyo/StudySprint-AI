"""StudySprint AI: a small Amazon Bedrock tool-using study planner."""
import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MODEL_ID = os.environ.get("MODEL_ID", "amazon.nova-micro-v1:0")

TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "create_study_schedule",
                "description": (
                    "Create a realistic timed study schedule. Always use this "
                    "tool when a student asks for a study plan."
                ),
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string"},
                            "topics": {
                                "type": "string",
                                "description": "Comma-separated study topics",
                            },
                            "total_minutes": {"type": "integer"},
                            "break_minutes": {"type": "integer"},
                        },
                        "required": [
                            "subject", "topics", "total_minutes", "break_minutes"
                        ],
                    }
                },
            }
        }
    ]
}


def create_study_schedule(args):
    """Deterministically divide study time across topics and breaks."""
    subject = str(args.get("subject", "Study session")).strip()[:100]
    subject = subject or "Study session"
    raw_topics = str(args.get("topics", "Revision")).strip()[:800]
    topics = [item.strip()[:100] for item in raw_topics.split(",") if item.strip()]
    topics = topics[:8] or ["Revision"]

    try:
        total_minutes = int(args.get("total_minutes", 90))
    except (TypeError, ValueError):
        total_minutes = 90
    total_minutes = max(20, min(total_minutes, 360))

    try:
        break_minutes = int(args.get("break_minutes", 5))
    except (TypeError, ValueError):
        break_minutes = 5
    break_minutes = max(0, min(break_minutes, 15))

    possible_breaks = max(0, len(topics) - 1)
    # Keep at least five minutes for each topic where possible.
    while possible_breaks * break_minutes + 5 * len(topics) > total_minutes and break_minutes > 0:
        break_minutes -= 1
    study_minutes = total_minutes - possible_breaks * break_minutes
    base = max(1, study_minutes // len(topics))
    remainder = study_minutes - base * len(topics)

    blocks = []
    for index, topic in enumerate(topics):
        duration = base + (1 if index < remainder else 0)
        blocks.append({"type": "study", "topic": topic, "minutes": duration})
        if index < len(topics) - 1 and break_minutes:
            blocks.append({"type": "break", "topic": "Short break", "minutes": break_minutes})

    return {
        "subject": subject,
        "total_minutes": total_minutes,
        "study_minutes": study_minutes,
        "break_minutes": break_minutes,
        "blocks": blocks,
        "tip": "Keep your phone away during each study block and tick off one topic at a time.",
    }


def http_response(status, payload):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "content-type",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(payload, ensure_ascii=False),
    }


def extract_text(response):
    message = response.get("output", {}).get("message", {})
    return "\n".join(
        block["text"] for block in message.get("content", []) if "text" in block
    ).strip()


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "POST")
    if method == "OPTIONS":
        return http_response(204, {})
    if method != "POST":
        return http_response(405, {"error": "Use POST to create a study plan."})

    try:
        raw_body = event.get("body") or "{}"
        if isinstance(raw_body, str) and len(raw_body) > 5000:
            return http_response(413, {"error": "Please shorten your request and try again."})
        payload = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
        if not isinstance(payload, dict):
            return http_response(400, {"error": "Please enter your study details."})

        subject = str(payload.get("subject", "")).strip()[:100]
        topics = str(payload.get("topics", "")).strip()[:800]
        if not subject or not topics:
            return http_response(400, {"error": "Enter a subject and at least one topic."})

        try:
            total_minutes = int(payload.get("total_minutes", 90))
        except (ValueError, TypeError):
            total_minutes = 90
        total_minutes = max(20, min(total_minutes, 360))
        try:
            break_minutes = int(payload.get("break_minutes", 5))
        except (ValueError, TypeError):
            break_minutes = 5
        break_minutes = max(0, min(break_minutes, 15))

        user_prompt = (
            f"Create a study plan for subject: {subject}. Topics: {topics}. "
            f"Total available time: {total_minutes} minutes. "
            f"Preferred break: {break_minutes} minutes.\n"
            "Use create_study_schedule before giving the final answer. "
            "Use the tool's result as the source of truth. Format the result as "
            "a readable schedule with times, then finish with one immediate next action. "
            "Keep the tone friendly and concise. Do not promise exam results."
        )
        messages = [{"role": "user", "content": [{"text": user_prompt}]}]
        client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        response = client.converse(
            modelId=MODEL_ID,
            system=[{"text": "You are StudySprint AI, a friendly study planning assistant. Be realistic, concise, and encouraging without being dramatic. Always use the create_study_schedule tool for a study plan."}],
            messages=messages,
            toolConfig=TOOL_CONFIG,
            inferenceConfig={"maxTokens": 650, "temperature": 0.3},
        )

        tool_used = False
        if response.get("stopReason") == "tool_use":
            assistant_message = response["output"]["message"]
            messages.append(assistant_message)
            tool_results = []
            for block in assistant_message.get("content", []):
                if "toolUse" not in block:
                    continue
                tool_use = block["toolUse"]
                if tool_use.get("name") != "create_study_schedule":
                    continue
                schedule = create_study_schedule(tool_use.get("input", {}))
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use["toolUseId"],
                        "content": [{"text": json.dumps(schedule, ensure_ascii=False)}],
                    }
                })
            if tool_results:
                tool_used = True
                messages.append({"role": "user", "content": tool_results})
                response = client.converse(
                    modelId=MODEL_ID,
                    system=[{"text": "You are StudySprint AI, a friendly study planning assistant. Use the returned schedule exactly; present it clearly with one immediate next action."}],
                    messages=messages,
                    toolConfig=TOOL_CONFIG,
                    inferenceConfig={"maxTokens": 650, "temperature": 0.3},
                )

        answer = extract_text(response)
        if not answer:
            # Deterministic fallback in case the model does not request the tool.
            schedule = create_study_schedule({
                "subject": subject,
                "topics": topics,
                "total_minutes": total_minutes,
                "break_minutes": break_minutes,
            })
            lines = [f"Study plan: {schedule['subject']} ({schedule['total_minutes']} minutes)"]
            counter = 0
            for block in schedule["blocks"]:
                counter += block["minutes"]
                lines.append(f"• {block['topic']}: {block['minutes']} min")
            lines.append("Next step: start the first topic and set a timer.")
            answer = "\n".join(lines)

        return http_response(200, {"answer": answer, "tool_used": tool_used})

    except Exception:
        logger.exception("StudySprint request failed")
        return http_response(500, {
            "error": "StudySprint had a problem. Check the Lambda logs, then try again."
        })
