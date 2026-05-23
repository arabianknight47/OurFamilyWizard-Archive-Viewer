# OurFamilyWizard Archive Viewer

An offline, read-only viewer for OurFamilyWizard message report exports. This utalizes HTML/CSS/JS sctirckly and can be published online, although it's highly recommended to password protect this before publishing online through a .htpasswd or similar method. pIt turns a downloaded message report PDF into a searchable, local archive that is easier to browse than a long PDF while still preserving a link back to the original source document.

This project exists because family messages can matter long after the moment they were sent. Sometimes they are needed for court, mediation, parenting coordination, or simply so a parent can preserve a clear record for themselves and for their children in the future. The goal is not to analyze, judge, or reinterpret the messages. The goal is to keep them readable, organized, and close to the original export.

The repository ships with a synthetic sample PDF and sample message data only. Before sharing your own customized archive, review every file in `data/` and decide carefully whether the archive should stay private, password-protected, or local-only.

## Features

- Static HTML/CSS/JavaScript app with no build step required.
- Local-only message viewing; no analytics, tracking, or network calls.
- Inbox, Sent, Favorites, and All Messages views.
- Thread detail view with sender, recipient, sent time, viewed time, body, and source PDF page.
- Search across sender, recipient, subject, and message body.
- Favorites saved in your browser with `localStorage`.
- Python importer for regenerating `data/messages.js` from an OurFamilyWizard message report PDF.

## Try The Sample

Open `index.html` in a browser.

The included archive is generated from `data/sample-ofw-message-report.pdf` and contains fictional names and messages for demonstration. The sample is intentionally small so you can inspect the whole workflow quickly.

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

Copy your PDF into the `data` folder and update the archive link in `index.html` if you want the app to open your original PDF from the sidebar. The footer names and date range are read from `data/messages.js`; they are not hard-coded.

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
- Names are preserved from the imported PDF so the archive remains useful as a record.
- Review `data/messages.js` and any PDF files before publishing or sharing a customized archive.
- Highly recommended to use .htpasswd or similar to password protect if publishing online.

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
