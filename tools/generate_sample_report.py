from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


MESSAGES = [
    {
        "sent": "03/01/2026 8:15 AM",
        "from": "Alex Rivera",
        "to": "Jordan Lee",
        "viewed": "03/01/2026 8:31 AM",
        "subject": "Weekly schedule",
        "body": [
            "Good morning. I uploaded the school calendar and wanted to confirm the pickup plan for Thursday.",
            "I can arrive at 5:30 PM unless the after-school event runs late. Please let me know what works best.",
        ],
    },
    {
        "sent": "03/01/2026 9:02 AM",
        "from": "Jordan Lee",
        "to": "Alex Rivera",
        "viewed": "03/01/2026 9:05 AM",
        "subject": "Re: Weekly schedule",
        "body": [
            "Thursday at 5:30 PM works. The event should be finished by then, and I will send a note if anything changes.",
            "",
            "Sent: 03/01/2026 8:15 AM",
            "From: Alex Rivera",
            "To: Jordan Lee (First Viewed: 03/01/2026 8:31 AM)",
            "Subject: Weekly schedule",
        ],
    },
    {
        "sent": "03/03/2026 6:40 PM",
        "from": "Alex Rivera",
        "to": "Jordan Lee",
        "viewed": "03/03/2026 7:04 PM",
        "subject": "Appointment reminder",
        "body": [
            "The dental appointment is Friday at 2:00 PM. I added the address and insurance card details to the shared notes.",
            "Please confirm whether you would like me to handle transportation from school.",
        ],
    },
    {
        "sent": "03/03/2026 7:22 PM",
        "from": "Jordan Lee",
        "to": "Alex Rivera",
        "viewed": "03/03/2026 7:25 PM",
        "subject": "Re: Appointment reminder",
        "body": [
            "Thanks for the reminder. Please handle transportation from school, and I will pick up afterward.",
            "",
            "Sent: 03/03/2026 6:40 PM",
            "From: Alex Rivera",
            "To: Jordan Lee (First Viewed: 03/03/2026 7:04 PM)",
            "Subject: Appointment reminder",
        ],
    },
    {
        "sent": "03/04/2026 7:10 AM",
        "from": "Jordan Lee",
        "to": "Alex Rivera",
        "viewed": "03/04/2026 7:15 AM",
        "subject": "School project materials",
        "body": [
            "The project board and markers are in the front pocket of the backpack.",
            "The printed instructions are in the blue folder.",
        ],
    },
    {
        "sent": "03/04/2026 7:46 AM",
        "from": "Alex Rivera",
        "to": "Jordan Lee",
        "viewed": "03/04/2026 7:50 AM",
        "subject": "Re: School project materials",
        "body": [
            "Received, thank you. I will make sure everything gets turned in this morning.",
            "",
            "Sent: 03/04/2026 7:10 AM",
            "From: Jordan Lee",
            "To: Alex Rivera (First Viewed: 03/04/2026 7:15 AM)",
            "Subject: School project materials",
        ],
    },
]


def draw_wrapped_text(pdf, text, x, y, max_chars=95, line_height=15):
    words = text.split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) > max_chars:
            pdf.drawString(x, y, line)
            y -= line_height
            line = word
        else:
            line = candidate
    if line:
        pdf.drawString(x, y, line)
        y -= line_height
    return y


def main():
    output = Path(__file__).resolve().parents[1] / "data" / "sample-ofw-message-report.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)

    pdf = canvas.Canvas(str(output), pagesize=letter)
    width, height = letter

    for index, message in enumerate(MESSAGES, start=1):
        y = height - 54
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(54, y, f"Message {index} of {len(MESSAGES)}")
        y -= 28

        pdf.setFont("Helvetica", 11)
        pdf.drawString(54, y, f"Sent: {message['sent']}")
        y -= 18
        pdf.drawString(54, y, f"From: {message['from']}")
        y -= 18
        pdf.drawString(54, y, f"To: {message['to']} (First Viewed: {message['viewed']})")
        y -= 18
        pdf.drawString(54, y, f"Subject: {message['subject']}")
        y -= 26

        for paragraph in message["body"]:
            if paragraph:
                y = draw_wrapped_text(pdf, paragraph, 54, y)
            y -= 10

        pdf.setFont("Helvetica", 9)
        pdf.drawRightString(width - 54, 32, f"Page {index} of {len(MESSAGES)} |  Message Report")
        pdf.showPage()

    pdf.save()
    print(output)


if __name__ == "__main__":
    main()
