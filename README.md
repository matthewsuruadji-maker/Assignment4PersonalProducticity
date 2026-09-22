# Personal Productivity Email MCP Server

## Overview

This project implements a local Model Context Protocol (MCP) server in Python for the Personal Productivity domain.

The server connects to Gmail through IMAP and allows an MCP client such as Claude Desktop to retrieve recent email messages. Claude Desktop will use in reading recent emails, summarizing them, identifying important messages, extracting action items and deadlines, and distinguishing acknowledgment/FYI or promotional emails.

## Domain

Personal Productivity

## Main Features

- Retrieve recent Gmail messages
- Retrieve unread Gmail messages
- Summarize recent emails through an MCP prompt
- Use input validation
- Protect internal error details
- Store Gmail credentials securely in a `.env` file

## MCP Components

### Tool 1: `get_recent_emails(limit=5)`

Retrieves recent Gmail messages through IMAP.

The tool returns:

- Sender
- Subject
- Date
- Email body

The `limit` parameter only accepts values between 1 and 10.

### Tool 2: `get_unread_emails(limit=5)`

Retrieves recent unread Gmail messages through IMAP.

This tool uses the same validation and authentication approach as `get_recent_emails()`.

### Prompt: `recent_email_digest_prompt()`

Retrieves the five most recent emails and provides Claude with instructions to:

- Summarize each email
- Classify the email type
- Determine importance
- Identify required actions
- Extract deadlines
- Identify acknowledgment/FYI messages
- Identify promotional or low-priority messages

## Email Classification

The prompt classifies each email into one of the following categories:

- Important
- Normal
- Acknowledgment / FYI
- Promotional / Newsletter

It also assigns an importance level:

- High
- Medium
- Low

## Authentication

The server connects to Gmail through IMAP using a Google App Password.

Credentials are stored in a local `.env` file.

Example:

```env
GMAIL_EMAIL=[your_email@gmail.com]
GMAIL_APP_PASSWORD=[your_app_password]
#the bracket [] is the one that you need to replace with your email and app password (not gmail password)

The `.env` file is excluded from GitHub through `.gitignore`.

## Installation

### Requirements

- Python
- uv
- Claude Desktop
- Gmail account with 2-Step Verification
- Gmail App Password

### Install dependencies

```powershell
uv sync
