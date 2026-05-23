import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader


MESSAGE_HEADING_RE = re.compile(r"^Message\s+(\d+)\s+of\s+(\d+)\s*$")
FIELD_RE = re.compile(r"^(Sent|From|To|Subject):\s*(.*)$")
RE_PREFIX_RE = re.compile(r"^(re:\s*)+", re.IGNORECASE)


def collapse_wrapped_lines(lines):
    paragraphs = []
    current = []

    for line in lines:
        text = line.strip()
        if not text:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if current and current[-1] == text:
            continue
        current.append(text)

    if current:
        paragraphs.append(" ".join(current))

    return repair_text("\n\n".join(paragraphs).strip())


def repair_text(value):
    if not isinstance(value, str):
        return value
    if "â" not in value and "ð" not in value:
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except UnicodeError:
        return value


def parse_date(value):
    try:
        return datetime.strptime(value, "%m/%d/%Y %I:%M %p").isoformat(timespec="minutes")
    except ValueError:
        return ""


def display_date(value):
    try:
        dt = datetime.strptime(value, "%m/%d/%Y %I:%M %p")
        return dt.strftime("%b %-d, %Y, %-I:%M %p")
    except ValueError:
        try:
            dt = datetime.strptime(value, "%m/%d/%Y %I:%M %p")
            return dt.strftime("%b %#d, %Y, %#I:%M %p")
        except ValueError:
            return value


def normalize_subject(subject):
    base = RE_PREFIX_RE.sub("", subject or "").strip() or "(No subject)"
    key = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    return base, key or "no-subject"


def stable_id(*parts):
    digest = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()[:14]
    return f"msg-{digest}"


def parse_recipient(value):
    match = re.match(r"^(.*?)\s*\(First Viewed:\s*(.*?)\)\s*$", value)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return value.strip(), ""


def line_indent(line):
    return len(line) - len(line.lstrip(" "))


def message_match_key(sent_raw, sender, recipient, subject):
    return (
        repair_text(sent_raw or "").strip(),
        repair_text(sender or "").strip(),
        repair_text(recipient or "").strip(),
        repair_text(subject or "").strip(),
    )


def parse_quoted_headers(lines):
    quoted = []
    current = None

    for _, line in lines:
        stripped = line.strip()
        match = FIELD_RE.match(stripped)
        if not match:
            continue

        field = match.group(1).lower()
        value = match.group(2).strip()

        if field == "sent":
            current = {"sent": value}
            continue

        if not current:
            continue

        current[field] = value

        if field == "subject" and {"sent", "from", "to", "subject"}.issubset(current):
            recipient, _ = parse_recipient(current["to"])
            quoted.append(message_match_key(current["sent"], current["from"], recipient, current["subject"]))
            current = None

    return quoted


def extract_blocks(pdf_path):
    reader = PdfReader(str(pdf_path))
    blocks = []
    current = None

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text(extraction_mode="layout") or ""
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped:
                if current:
                    current["lines"].append((page_index, line))
                continue

            heading = MESSAGE_HEADING_RE.match(stripped)
            if heading and line_indent(line) <= 2:
                if current:
                    blocks.append(current)
                current = {
                    "number": int(heading.group(1)),
                    "total": int(heading.group(2)),
                    "startPage": page_index,
                    "endPage": page_index,
                    "lines": [],
                }
                continue

            if current:
                if "|  Message Report" in line or re.search(r"\bPage\s+\d+\s+of\s+\d+\b", line):
                    continue
                current["lines"].append((page_index, line))
                current["endPage"] = page_index

    if current:
        blocks.append(current)

    return blocks


def parse_block(block, report_file, sent_from=""):
    fields = {}
    subject_index = None

    for index, (_, line) in enumerate(block["lines"]):
        stripped = line.strip()
        indent = line_indent(line)
        if indent > 12:
            continue
        match = FIELD_RE.match(stripped)
        if not match:
            continue
        fields[match.group(1).lower()] = match.group(2).strip()
        if match.group(1) == "Subject":
            subject_index = index
            break

    if subject_index is None:
        return None

    body_lines = []
    for _, line in block["lines"][subject_index + 1 :]:
        stripped = line.strip()
        indent = line_indent(line)
        if FIELD_RE.match(stripped):
            break
        if indent <= 12:
            body_lines.append(line)

    recipient, viewed = parse_recipient(fields.get("to", ""))
    subject = repair_text(fields.get("subject", "(No subject)"))
    base_subject, subject_key = normalize_subject(subject)
    body = collapse_wrapped_lines(body_lines)
    sent_raw = fields.get("sent", "")
    sender = repair_text(fields.get("from", ""))
    msg_id = stable_id(sender, recipient, sent_raw, subject, body[:500])

    return {
        "id": msg_id,
        "threadId": f"thread-{subject_key}",
        "threadSubject": repair_text(base_subject),
        "threadRootMessageNumber": block["number"],
        "messageNumber": block["number"],
        "subject": repair_text(subject),
        "from": repair_text(sender),
        "to": [repair_text(recipient)] if recipient else [],
        "sentAt": parse_date(sent_raw),
        "sentAtRaw": repair_text(sent_raw),
        "sentAtDisplay": display_date(sent_raw),
        "viewedAtDisplay": f"Viewed {display_date(viewed)}" if viewed else "",
        "folder": "Sent" if sent_from and sender == sent_from else "Inbox",
        "body": body,
        "attachments": [],
        "quotedMessageKeys": parse_quoted_headers(block["lines"][subject_index + 1 :]),
        "matchKey": message_match_key(sent_raw, sender, recipient, subject),
        "source": {
            "reportFile": report_file,
            "pageStart": block["startPage"],
            "pageEnd": block["endPage"],
            "messageNumber": block["number"],
        },
    }


def assign_threads(messages):
    by_key = {tuple(message["matchKey"]): message for message in messages}
    assigned_threads = {}
    root_counts = {}
    latest_by_subject = {}

    for message in sorted(messages, key=lambda msg: msg["messageNumber"]):
        parent = None
        for quoted_key in message.get("quotedMessageKeys", []):
            candidate = by_key.get(tuple(quoted_key))
            if candidate and candidate["messageNumber"] < message["messageNumber"]:
                parent = candidate
                break

        base_subject, subject_key = normalize_subject(message["subject"])
        is_reply = bool(RE_PREFIX_RE.match(message["subject"] or ""))
        if not parent and is_reply:
            parent = latest_by_subject.get(subject_key)

        if parent and parent["id"] in assigned_threads:
            thread_id = assigned_threads[parent["id"]]
            root_number = parent["threadRootMessageNumber"]
        else:
            root_counts[subject_key] = root_counts.get(subject_key, 0) + 1
            thread_id = f"thread-{subject_key}-{root_counts[subject_key]:03d}"
            root_number = message["messageNumber"]

        message["threadId"] = thread_id
        message["threadSubject"] = repair_text(base_subject)
        message["threadRootMessageNumber"] = root_number
        assigned_threads[message["id"]] = thread_id
        latest_by_subject[subject_key] = message

    for message in messages:
        message.pop("quotedMessageKeys", None)
        message.pop("matchKey", None)


def build_payload(pdf_path, sent_from=""):
    blocks = extract_blocks(pdf_path)
    messages = []
    skipped = []

    for block in blocks:
        parsed = parse_block(block, pdf_path.name, sent_from)
        if parsed:
            messages.append(parsed)
        else:
            skipped.append(block["number"])

    assign_threads(messages)
    messages.sort(key=lambda msg: (msg["sentAt"] or msg["sentAtRaw"], msg["messageNumber"]))
    thread_counts = {}
    for msg in messages:
        thread_counts[msg["threadId"]] = thread_counts.get(msg["threadId"], 0) + 1

    participants = sorted(
        {
            name
            for message in messages
            for name in [message["from"], *message.get("to", [])]
            if name
        }
    )

    return {
        "meta": {
            "sourceFile": pdf_path.name,
            "importedAt": datetime.now().isoformat(timespec="seconds"),
            "messageCount": len(messages),
            "threadCount": len(thread_counts),
            "skippedMessageNumbers": skipped,
            "parser": "tools/import_ofw_report.py",
            "participants": participants,
        },
        "messages": messages,
    }


def write_js(payload, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    output_path.write_text(f"window.OFW_ARCHIVE_DATA = {json_text};\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Import an OurFamilyWizard message report PDF.")
    parser.add_argument("pdf", type=Path, help="Path to the OurFamilyWizard message report PDF")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/messages.js"),
        help="Output JS data file. Defaults to data/messages.js",
    )
    parser.add_argument(
        "--sent-from",
        default="",
        help="Optional exact sender name to classify as Sent. Other messages are classified as Inbox.",
    )
    args = parser.parse_args()

    payload = build_payload(args.pdf, args.sent_from)
    write_js(payload, args.out)

    meta = payload["meta"]
    print(f"Imported {meta['messageCount']} messages into {meta['threadCount']} threads.")
    print(f"Source: {meta['sourceFile']}")
    print(f"Output: {args.out}")
    if meta["skippedMessageNumbers"]:
        print(f"Skipped messages: {', '.join(map(str, meta['skippedMessageNumbers']))}")


if __name__ == "__main__":
    main()
