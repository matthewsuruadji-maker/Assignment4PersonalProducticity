# References:
# MCP Python SDK documentation:
# https://github.com/modelcontextprotocol/python-sdk
#
# Python imaplib documentation:
# https://docs.python.org/3/library/imaplib.html
#
# Python email package documentation:
# https://docs.python.org/3/library/email.html
#
# AI assistance was used to help design, debug, and explain this implementation
from mcp.server import MCPServer
from dotenv import load_dotenv
from pathlib import Path

import os
import imaplib
import email

from email.header import decode_header


mcp = MCPServer("Personal Productivity Email Assistant")


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")




def decode_email_header(value: str) -> str:

    if not value:
        return ""

    decoded_parts = decode_header(value)

    result = ""

    for part, encoding in decoded_parts:

        if isinstance(part, bytes):

            result += part.decode(
                encoding or "utf-8",
                errors="replace"
            )

        else:

            result += part

    return result


def extract_email_body(msg) -> str:

    body = ""

    if msg.is_multipart():

        for part in msg.walk():

            content_type = part.get_content_type()

            disposition = str(
                part.get("Content-Disposition")
            )

            if (
                content_type == "text/plain"
                and "attachment" not in disposition
            ):

                payload = part.get_payload(
                    decode=True
                )

                if payload:

                    charset = (
                        part.get_content_charset()
                        or "utf-8"
                    )

                    body = payload.decode(
                        charset,
                        errors="replace"
                    )

                break

    else:

        payload = msg.get_payload(
            decode=True
        )

        if payload:

            charset = (
                msg.get_content_charset()
                or "utf-8"
            )

            body = payload.decode(
                charset,
                errors="replace"
            )

    # Prevent excessively large email content
    return body.strip()[:4000]


def fetch_emails(
    limit: int = 5,
    unread_only: bool = False
) -> dict:

    mail = None

    try:


        if not isinstance(limit, int):

            return {
                "success": False,
                "error": "Email limit must be an integer."
            }

        if limit < 1 or limit > 10:

            return {
                "success": False,
                "error": (
                    "Email limit must be between "
                    "1 and 10."
                )
            }

        if (
            not GMAIL_EMAIL
            or not GMAIL_APP_PASSWORD
        ):

            return {
                "success": False,
                "error": (
                    "Gmail credentials "
                    "are not configured."
                )
            }


        mail = imaplib.IMAP4_SSL(
            "imap.gmail.com",
            993,
            timeout=10
        )

        mail.login(
            GMAIL_EMAIL,
            GMAIL_APP_PASSWORD
        )

        mail.select(
            "INBOX",
            readonly=True
        )


        search_query = (
            "UNSEEN"
            if unread_only
            else "ALL"
        )

        status, message_numbers = mail.search(
            None,
            search_query
        )

        if status != "OK":

            return {
                "success": False,
                "error": (
                    "Unable to retrieve "
                    "the email list."
                )
            }

        ids = message_numbers[0].split()

        recent_ids = ids[-limit:]

        recent_ids.reverse()

        emails = []


        for message_id in recent_ids:

            status, message_data = mail.fetch(
                message_id,
                "(RFC822)"
            )

            if status != "OK":
                continue

            raw_email = message_data[0][1]

            msg = email.message_from_bytes(
                raw_email
            )

            sender = decode_email_header(
                msg.get("From")
            )

            subject = decode_email_header(
                msg.get("Subject")
            )

            date = msg.get(
                "Date",
                ""
            )

            body = extract_email_body(
                msg
            )

            emails.append(
                {
                    "from": sender,
                    "subject": subject,
                    "date": date,
                    "body": body
                }
            )

        return {
            "success": True,
            "count": len(emails),
            "emails": emails
        }


    except imaplib.IMAP4.error:

        return {
            "success": False,
            "error": (
                "Unable to authenticate "
                "with Gmail."
            )
        }

    except Exception:

        return {
            "success": False,
            "error": (
                "Unable to retrieve "
                "Gmail messages."
            )
        }

    finally:

        if mail:

            try:

                mail.logout()

            except Exception:

                pass


@mcp.tool()
def get_recent_emails(
    limit: int = 5
) -> dict:
    """
    Retrieve recent Gmail messages.

    Returns sender, subject, date,
    and email body.
    """

    return fetch_emails(
        limit=limit,
        unread_only=False
    )



@mcp.tool()
def get_unread_emails(
    limit: int = 5
) -> dict:
    """
    Retrieve recent unread Gmail messages.
    """

    return fetch_emails(
        limit=limit,
        unread_only=True
    )




@mcp.prompt()
def recent_email_digest_prompt() -> str:
    """
    Retrieve the five most recent emails
    and create instructions for Claude
    to summarize and prioritize them.
    """

    result = fetch_emails(
        limit=5,
        unread_only=False
    )

    if not result.get("success"):

        return (
            "Unable to retrieve emails. "
            "Please check the Gmail connection."
        )

    email_text = ""

    for index, message in enumerate(
        result["emails"],
        start=1
    ):

        email_text += f"""
EMAIL {index}

FROM:
{message["from"]}

SUBJECT:
{message["subject"]}

DATE:
{message["date"]}

CONTENT:
{message["body"]}

------------------------------
"""

    return f"""
You are a personal productivity assistant.

Analyze the five recent emails below.

For EACH email provide:

EMAIL NUMBER:

SUBJECT:

SUMMARY:
Summarize the email in 1-3 sentences.

EMAIL TYPE:
Choose exactly one:

- Important
- Normal
- Acknowledgment / FYI
- Promotional / Newsletter

IMPORTANCE:
Choose exactly one:

- High
- Medium
- Low

ACTION REQUIRED:
Clearly state what I need to do.

If no action is required, write:

No action required.

DEADLINE:
Identify any deadline, meeting date,
submission date, appointment, or important time.

If none exists, write:

No deadline mentioned.

WHY IT MATTERS:
Briefly explain why the email is or
is not important.

CLASSIFICATION RULES:

IMPORTANT / HIGH:
Use when ignoring the email could have
meaningful consequences, including:

- deadlines
- required action
- academic obligations
- work obligations
- financial matters
- account or security issues
- appointments
- meetings requiring preparation
- urgent requests

ACKNOWLEDGMENT / FYI:
Use when the email mainly:

- says thank you
- confirms receipt
- confirms completion
- acknowledges an earlier message
- provides a simple status update
- requires no further action

PROMOTIONAL / NEWSLETTER:
Use for:

- advertisements
- marketing messages
- newsletters
- promotions
- general event advertisements

NORMAL:
Use for useful communication that should
be read but does not appear urgent.

IMPORTANT:

Do not invent information.

Do not invent deadlines.

Do not assume an email is important
simply because the sender uses words such
as "important" or "urgent."

Judge importance based on the actual content.

After reviewing all emails, finish with:

==============================
EMAIL DIGEST
==============================

MOST IMPORTANT EMAILS:
List only emails classified as High importance.

ACTION ITEMS:
Give me a concise checklist of everything
I need to do.

ACKNOWLEDGMENT / FYI EMAILS:
List emails that need no response or action.

EMAILS I CAN PROBABLY IGNORE:
List promotional or low-priority messages.

Here are the emails:

{email_text}

""".strip()


# =========================================================
# START MCP SERVER
# =========================================================

if __name__ == "__main__":
    mcp.run()