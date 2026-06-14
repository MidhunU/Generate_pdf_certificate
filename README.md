# PDF Certificate Editor

A Python utility to automatically overlay participant names, custom dates, and transparent signature PNGs onto a PDF certificate template.

## Features

* **Interactive Mode**: Prompts you in the console for template paths, participant names, dates, and signature images.
* **CLI Arguments**: Fully customizable styling, scaling, fonts, colors, and file paths via command line flags.
* **Batch Processing**: Generates multiple certificates in bulk from a text/CSV list of names.
* **Dynamic Coordinate Scaling**: Reads the page size of the input PDF and scales all text positions and sizes proportionally.
* **Google Sans Fonts**: Utilizes the Google Sans font family (`Regular` and `Medium`).

---

## Getting Started

### 1. Install Dependencies

Install the required Python libraries:
```bash
pip install pypdf reportlab
```

### 2. Run Interactively (Console Prompts)

To run the generator and have it prompt you step-by-step, simply run the script with no arguments:
```bash
python generate_pdf_certificates.py
```

---

## Command Line Usage (CLI Mode)

For custom styling, custom colors, or automation, you can run the script with flags:

### Single Certificate Generation
```bash
python generate_pdf_certificates.py \
  --template certificate_template.pdf \
  --name "Alex Morgan" \
  --date "June 15, 2026" \
  --signature mock_signature.png \
  --output certificate_alex_morgan.pdf
```

### Batch/Bulk Generation
Create a file (e.g. `names.txt`) with one participant name per line and run:
```bash
python generate_pdf_certificates.py \
  --template certificate_template.pdf \
  --batch names.txt \
  --signature mock_signature.png \
  --output-dir outputs
```

---

## Styling Options & CLI Flags

| Flag | Description | Default |
| --- | --- | --- |
| `--template` | Path to the template PDF | `certificate_template.pdf` |
| `--name` | Student's name (Single mode) | *None* |
| `--date` | Custom date string | Today's Date (e.g. `June 15, 2026`) |
| `--signature` | Path to signature PNG file | *None* |
| `--output` | Destination path for output PDF | `certificate_<name>.pdf` |
| `--batch` | Path to text or CSV list of names | *None* |
| `--output-dir` | Folder for batch outputs | `outputs` |
| `--name-size` | Font size for the name | `36` |
| `--date-size` | Font size for the date | `16` |
| `--sig-width` | Width to scale signature PNG | `130` |
| `--sig-height` | Height to scale signature PNG | `130` |
| `--text-color`| Hex color code for texts | `#202124` |

---

## Coordinates System

Based on the Google Student Ambassador certificate dimensions (`996 x 721` points):
* **Participant Name**: Centered at `X = 498.0`, `Y = 328.0` (ReportLab's bottom-left origin).
* **Date**: Centered at `X = 182.0`, `Y = 111.0`.
* **Signature**: Centered horizontally at `X = 815.0` and aligned to sit on the line at `Y = 107.0` (extending up to `237.0`).

*Note: All coordinates scale automatically if your template PDF has different dimensions.*
