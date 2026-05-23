# OurFamilyWizard Archive Viewer

An offline, read-only viewer for OurFamilyWizard message report exports.

This project lets you keep a portable archive of your OurFamilyWizard messages as a simple static web app. It loads a parsed message report from `data/messages.js`, displays messages in an inbox-style thread list, supports search and favorites, and links back to the source PDF used to generate the archive.

The repository ships with a synthetic sample PDF and sample message data only. Do not publish private family, legal, or account data unless you have carefully reviewed what you are sharing.

## Features

- Static HTML/CSS/JavaScript app with no server required.
- Local-only message viewing; no analytics, tracking, or network calls.
- Inbox, Sent, Favorites, and All Messages views.
- Thread detail view with sender, recipient, sent time, viewed time, body, and source PDF page.
- Search across sender, recipient, subject, and message body.
- Favorites saved in your browser with `localStorage`.
- Python importer for regenerating `data/messages.js` from an OurFamilyWizard message report PDF.

## Try The Sample

Open `index.html` in a browser.

The included archive is generated from `data/sample-ofw-message-report.pdf` and contains fictional names and messages for demonstration.

## Generate Your Own Archive

First, export your message report from OurFamilyWizard:

1. Go to the main Inbox in OurFamilyWizard.
2. Use the main report button from the main inbox.
3. Select all messages in the folder.
4. Choose oldest to newest ordering.
5. Check the option to include message replies.
6. Download the generated PDF report.

Then run the importer:

```powershell
python tools\import_ofw_report.py "C:\Path\To\Your_OFW_Message_Report.pdf" --out data\messages.js --sent-from "Your Name"
```

Use `--sent-from` with the exact sender name as it appears in the PDF if you want the Sent folder to be classified. If you omit it, imported messages are still viewable, but they will be classified as Inbox by default.

Copy your PDF into the `data` folder and update the archive link in `index.html` if you want the app to open your original PDF from the sidebar.

## Regenerate The Included Sample

The sample report can be regenerated with:

```powershell
python tools\generate_sample_report.py
python tools\import_ofw_report.py data\sample-ofw-message-report.pdf --out data\messages.js --sent-from "Alex Rivera"
```

The sample generator uses `reportlab`; the archive importer uses `pypdf`.

## Privacy Notes

- The app runs locally in your browser.
- It does not send message contents anywhere.
- Favorite state is stored only in the browser where you use the app.
- Review `data/messages.js` and any PDF files before publishing or sharing a customized archive.

## Development

No build step is required. Edit the files directly and refresh the browser.

```text
index.html
styles.css
app.js
data/messages.js
tools/import_ofw_report.py
```

## License

MIT
