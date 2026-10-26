"""StudySprint AI: a small Amazon Bedrock tool-using study planner."""
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MODEL_ID = os.environ.get("MODEL_ID", "amazon.nova-micro-v1:0")

TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "create_study_schedule",
                "description": (
                    "Create a realistic timed study schedule from a subject, "
                    "topics, available time, and break duration."
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
                            "subject",
                            "topics",
                            "total_minutes",
                            "break_minutes",
                        ],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "get_syllabus_from_s3",
                "description": (
                    "Retrieve a requested module from the configured syllabus "
                    "JSON object in private Amazon S3. When syllabus mode is "
                    "enabled, call this first. Never invent topics if retrieval fails."
                ),
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "Subject to retrieve",
                            },
                            "module": {
                                "type": "string",
                                "description": "Requested syllabus module",
                            },
                        },
                        "required": ["subject", "module"],
                    }
                },
            }
        },
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
