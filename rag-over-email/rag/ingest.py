"""Load emails from various sources into one common format.

Each email becomes a dict: id, thread_id, date, from, to, subject, body.
Supported sources (so the SAME pipeline runs on the sample data, the public
Enron dataset, or your own inbox export):
  - a .json file  (the bundled sample format)
  - a .mbox file  (e.g. a Gmail / Thunderbird export)
  - a folder of .eml files
"""
import json
import os
import email
import mailbox
from email import policy


def load_emails(path):
    """Load emails from a .json file, a .mbox file, or a folder of .eml files."""
    if os.path.isdir(path):
        return _load_eml_folder(path)
    if path.lower().endswith(".mbox"):
        return _load_mbox(path)
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    raise ValueError(f"Unsupported email source: {path}")


def searchable_text(em):
    """The text we index for retrieval: subject + sender + body."""
    return f"Subject: {em.get('subject', '')}\nFrom: {em.get('from', '')}\n\n{em.get('body', '')}"


def _msg_body(msg):
    """Pull the plain-text body out of an email.message.Message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return _decode(part)
        return ""
    return _decode(msg)


def _decode(part):
    try:
        return (part.get_content() or "").strip()
    except Exception:
        payload = part.get_payload(decode=True) or b""
        return payload.decode("utf-8", errors="replace").strip()


def _from_message(msg, idx):
    return {
        "id": msg.get("Message-ID", f"msg-{idx}"),
        "thread_id": msg.get("Thread-Index", "") or msg.get("References", "") or "",
        "date": msg.get("Date", ""),
        "from": msg.get("From", ""),
        "to": msg.get("To", ""),
        "subject": msg.get("Subject", ""),
        "body": _msg_body(msg),
    }


def _load_mbox(path):
    box = mailbox.mbox(
        path, factory=lambda f: email.message_from_binary_file(f, policy=policy.default)
    )
    return [_from_message(msg, i) for i, msg in enumerate(box)]


def _load_eml_folder(path):
    emails = []
    for i, name in enumerate(sorted(os.listdir(path))):
        if not name.lower().endswith(".eml"):
            continue
        with open(os.path.join(path, name), "rb") as f:
            msg = email.message_from_binary_file(f, policy=policy.default)
        emails.append(_from_message(msg, i))
    return emails
