#!/usr/bin/env python3
import io
import os
import sys
import datetime
import argparse
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Constants
DEFAULT_FONT_REGULAR = os.path.join("fonts", "GoogleSans-Regular.ttf")
DEFAULT_FONT_MEDIUM = os.path.join("fonts", "GoogleSans-Medium.ttf")
DEFAULT_FONT_NAME = None  # Auto-detects Times New Roman TTF or falls back to 'Times-Roman'

# Hardcoded Output Directory (e.g. "." saves directly in the project root, or set to "outputs" / any custom path)
HARDCODED_OUTPUT_DIR = "/home/midhun_u/Downloads/Design_Dojo_certificates"

# Baseline template size used to discover coordinates (996x721 points)
BASE_WIDTH = 996.0
BASE_HEIGHT = 721.0

# Pillow/original coordinates (from top-left origin)
# To raise any section, DECREASE its Y_PILLOW value.
# To lower any section, INCREASE its Y_PILLOW value.
NAME_BASE_X = 498.0
NAME_BASE_Y_PILLOW = 385.0  # Adjusted to 385.0 to bring the name down and center it vertically

DATE_BASE_X = 182.0
DATE_BASE_Y_PILLOW = 600.0  # Decreased from 610.0 to raise the date

SIG_BASE_X = 815.0
SIG_BASE_Y_PILLOW = 630.0   # Increased from 614.0 to lower the signature (bottom edge)

def get_current_date_string():
    """Returns today's date formatted like 'June 15, 2026'."""
    now = datetime.datetime.now()
    return now.strftime("%B %d, %Y")

def register_fonts(font_reg_path=DEFAULT_FONT_REGULAR, font_med_path=DEFAULT_FONT_MEDIUM, font_name_path=None):
    """Registers fonts for ReportLab canvas including Times New Roman for the name."""
    font_reg = 'Helvetica'
    font_med = 'Helvetica-Bold'
    font_name = 'Times-Roman'  # Built-in standard ReportLab font
    
    if os.path.exists(font_reg_path):
        try:
            pdfmetrics.registerFont(TTFont('GoogleSans-Regular', font_reg_path))
            font_reg = 'GoogleSans-Regular'
        except Exception as e:
            print(f"Warning: Failed to register GoogleSans-Regular: {e}")
    else:
        print(f"Warning: regular font file not found at '{font_reg_path}'. Using Helvetica.")
        
    if os.path.exists(font_med_path):
        try:
            pdfmetrics.registerFont(TTFont('GoogleSans-Medium', font_med_path))
            font_med = 'GoogleSans-Medium'
        except Exception as e:
            print(f"Warning: Failed to register GoogleSans-Medium: {e}")
    else:
        print(f"Warning: medium font file not found at '{font_med_path}'. Using Helvetica-Bold.")
        
    # Search for Times New Roman TrueType font
    times_candidates = [
        font_name_path,
        "/usr/share/fonts/msttcore/times.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/times.ttf",
        "/usr/share/fonts/times.ttf",
        "/usr/share/fonts/truetype/times.ttf",
        "/usr/share/fonts/TTF/times.ttf",
        "C:/Windows/Fonts/times.ttf",
        "/Library/Fonts/Times New Roman.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    ]
    for path in times_candidates:
        if path and os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('TimesNewRoman', path))
                font_name = 'TimesNewRoman'
                break
            except Exception:
                pass
        
    return font_reg, font_med, font_name

def parse_hex_color(hex_str, default=(1.0, 1.0, 1.0)):
    """Converts hex color code to RGB float tuple (0.0 to 1.0)."""
    if hex_str and hex_str.startswith('#'):
        h = hex_str.lstrip('#')
        if len(h) == 6:
            try:
                return tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))
            except ValueError:
                pass
    return default

def create_overlay_page(
    page_width,
    page_height,
    name,
    date_str,
    sig_path,
    font_reg,
    font_med,
    font_name='Times-Roman',
    name_size=36,
    date_size=16,
    sig_scale_w=130,
    sig_scale_h=130,
    text_color="#FFFFFF",
    name_color="#FFFFFF"
):
    """Generates a transparent PDF page containing overlays with correct coordinates."""
    # Scale factor calculations
    scale_x = float(page_width) / BASE_WIDTH
    scale_y = float(page_height) / BASE_HEIGHT
    
    # Calculate PDF (bottom-left origin) coordinates
    # X coordinates
    name_x = NAME_BASE_X * scale_x
    date_x = DATE_BASE_X * scale_x
    sig_x_center = SIG_BASE_X * scale_x
    
    # Y coordinates (PDF y = page_height - pillow_y)
    name_y = page_height - (NAME_BASE_Y_PILLOW * scale_y)
    date_y = page_height - (DATE_BASE_Y_PILLOW * scale_y)
    sig_y = page_height - (SIG_BASE_Y_PILLOW * scale_y)
    
    # Scale font sizes and signature sizes
    s_name_size = name_size * scale_y
    s_date_size = date_size * scale_y
    s_sig_w = sig_scale_w * scale_x
    s_sig_h = sig_scale_h * scale_y
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    
    # Draw Name in Times New Roman and white color
    can.setFont(font_name if font_name else 'Times-Roman', s_name_size)
    nr, ng, nb = parse_hex_color(name_color, (1.0, 1.0, 1.0))
    can.setFillColorRGB(nr, ng, nb)
    can.drawCentredString(name_x, name_y, name)
    
    # Draw Date if provided
    if date_str and date_str.lower() != 'none':
        can.setFont(font_reg, s_date_size)
        tr, tg, tb = parse_hex_color(text_color, (1.0, 1.0, 1.0))
        can.setFillColorRGB(tr, tg, tb)
        can.drawCentredString(date_x, date_y, date_str)
    
    # Draw Signature Image
    if sig_path and os.path.exists(sig_path):
        try:
            # Place signature such that it is centered horizontally on X = sig_x_center
            # and bottom edge aligns with Y = sig_y
            sig_left = sig_x_center - (s_sig_w / 2.0)
            can.drawImage(sig_path, sig_left, sig_y, width=s_sig_w, height=s_sig_h, mask='auto')
        except Exception as e:
            print(f"Warning: Failed to draw signature: {e}")
            
    can.save()
    packet.seek(0)
    return packet

def overlay_pdf_certificate(
    template_pdf_path,
    name,
    date_str,
    sig_path,
    output_pdf_path,
    font_reg_path=DEFAULT_FONT_REGULAR,
    font_med_path=DEFAULT_FONT_MEDIUM,
    font_name_path=DEFAULT_FONT_NAME,
    name_size=36,
    date_size=16,
    sig_w=130,
    sig_h=100,
    text_color="#FFFFFF",
    name_color="#FFFFFF"
):
    """Merges a single transparent overlay with the original PDF template."""
    if not os.path.exists(template_pdf_path):
        print(f"Error: PDF template '{template_pdf_path}' not found.")
        return False
        
    try:
        reader = PdfReader(template_pdf_path)
        if len(reader.pages) == 0:
            print("Error: The template PDF has no pages.")
            return False
            
        # Register fonts
        font_reg, font_med, font_name = register_fonts(font_reg_path, font_med_path, font_name_path)
        
        # Get dimensions of first page
        template_page = reader.pages[0]
        page_width = float(template_page.mediabox.width)
        page_height = float(template_page.mediabox.height)
        
        # Create transparent overlay PDF
        overlay_packet = create_overlay_page(
            page_width=page_width,
            page_height=page_height,
            name=name,
            date_str=date_str,
            sig_path=sig_path,
            font_reg=font_reg,
            font_med=font_med,
            font_name=font_name,
            name_size=name_size,
            date_size=date_size,
            sig_scale_w=sig_w,
            sig_scale_h=sig_h,
            text_color=text_color,
            name_color=name_color
        )
        
        # Open the overlay page
        overlay_reader = PdfReader(overlay_packet)
        overlay_page = overlay_reader.pages[0]
        
        # Merge overlay onto the template page
        template_page.merge_page(overlay_page)
        
        # Write to output file
        writer = PdfWriter()
        writer.add_page(template_page)
        
        # If the template had more pages, add them unmodified
        for i in range(1, len(reader.pages)):
            writer.add_page(reader.pages[i])
            
        with open(output_pdf_path, "wb") as f:
            writer.write(f)
            
        print(f"Successfully generated PDF: {output_pdf_path}")
        return True
    except Exception as e:
        print(f"Error generating PDF certificate: {e}")
        return False

def prompt_interactive():
    """Interactively prompts the user for certificate details."""
    print("=== Interactive Certificate Generator ===")
    
    # 1. Template PDF
    default_template = "certificate_template.pdf"
    template = input(f"Enter template PDF path (press Enter for '{default_template}'): ").strip()
    if not template:
        template = default_template
    while not os.path.exists(template):
        print(f"File '{template}' not found.")
        template = input("Enter template PDF path: ").strip()
        if not template:
            template = default_template

    # 2. Participant Names
    names_input = input("Enter participant name(s) (comma-separated for multiple certificates): ").strip()
    while not names_input:
        print("Name cannot be empty.")
        names_input = input("Enter participant name(s): ").strip()
        
    names = [n.strip() for n in names_input.split(",") if n.strip()]

    # 3. Custom Date
    date_str = input("Enter date (press Enter to skip, or enter date e.g. 'October 9, 2026'): ").strip()

    # 4. Signature File
    default_sig = "mock_signature.png" if os.path.exists("mock_signature.png") else ""
    sig_prompt = f" (press Enter for '{default_sig}')" if default_sig else ""
    sig_path = input(f"Enter path to signature PNG{sig_prompt}: ").strip()
    if not sig_path:
        sig_path = default_sig
    while sig_path and not os.path.exists(sig_path):
        print(f"File '{sig_path}' not found.")
        sig_path = input("Enter path to signature PNG: ").strip()

    # 5. Output (Hardcoded)
    os.makedirs(HARDCODED_OUTPUT_DIR, exist_ok=True)
    if len(names) == 1:
        safe_name = "".join([c if c.isalnum() or c in (" ", "_", "-") else "" for c in names[0]]).strip().replace(" ", "_")
        output = os.path.join(HARDCODED_OUTPUT_DIR, f"certificate_{safe_name}.pdf")
        
        overlay_pdf_certificate(
            template_pdf_path=template,
            name=names[0],
            date_str=date_str,
            sig_path=sig_path,
            output_pdf_path=output,
            text_color="#FFFFFF",
            name_color="#FFFFFF"
        )
    else:
        success_count = 0
        for name in names:
            safe_name = "".join([c if c.isalnum() or c in (" ", "_", "-") else "" for c in name]).strip().replace(" ", "_")
            out_file = os.path.join(HARDCODED_OUTPUT_DIR, f"certificate_{safe_name}.pdf")
            success = overlay_pdf_certificate(
                template_pdf_path=template,
                name=name,
                date_str=date_str,
                sig_path=sig_path,
                output_pdf_path=out_file,
                text_color="#FFFFFF",
                name_color="#FFFFFF"
            )
            if success:
                success_count += 1
        print(f"\nBatch completed: {success_count}/{len(names)} PDF certificates saved in '{HARDCODED_OUTPUT_DIR}'.")

def main():
    parser = argparse.ArgumentParser(
        description="Append participant name, custom date, and signature PNG to a PDF template."
    )
    parser.add_argument("--interactive", action="store_true", help="Run in interactive console prompt mode")
    parser.add_argument("--template", default="certificate_template.pdf", help="Path to the PDF template")
    parser.add_argument("--name", help="Participant name")
    parser.add_argument("--date", help="Date to write on certificate (optional, defaults to empty)")
    parser.add_argument("--signature", help="Path to signature PNG file")
    parser.add_argument("--output", help="Output PDF file path")
    
    # Custom styling parameters
    parser.add_argument("--font-regular", default=DEFAULT_FONT_REGULAR, help="Path to regular font file")
    parser.add_argument("--font-medium", default=DEFAULT_FONT_MEDIUM, help="Path to medium font file")
    parser.add_argument("--font-name", default=DEFAULT_FONT_NAME, help="Path to custom font for name (defaults to Times New Roman)")
    parser.add_argument("--name-size", type=int, default=36, help="Font size for participant name")
    parser.add_argument("--date-size", type=int, default=16, help="Font size for date")
    parser.add_argument("--sig-width", type=int, default=130, help="Signature scale width")
    parser.add_argument("--sig-height", type=int, default=130, help="Signature scale height")
    parser.add_argument("--name-color", default="#FFFFFF", help="Hex color code for name (default: #FFFFFF)")
    parser.add_argument("--text-color", default="#FFFFFF", help="Hex color code for date text (default: #FFFFFF)")

    # Batch option
    parser.add_argument("--batch", help="Path to text/CSV file of names for batch generation")
    parser.add_argument("--output-dir", default=HARDCODED_OUTPUT_DIR, help="Directory for batch outputs")

    args = parser.parse_args()

    # Determine date
    date_val = args.date if args.date else ""

    # Force interactive mode if no arguments are passed and script is run directly
    if args.interactive or (len(sys.argv) == 1):
        prompt_interactive()
        return

    # Validate template exists
    if not os.path.exists(args.template):
        print(f"Error: Template PDF '{args.template}' not found. Specify via --template.")
        sys.exit(1)

    if args.batch:
        if not os.path.exists(args.batch):
            print(f"Error: Batch file '{args.batch}' not found.")
            sys.exit(1)

        os.makedirs(args.output_dir, exist_ok=True)
        
        # Read names
        names = []
        try:
            import csv
            with open(args.batch, "r", encoding="utf-8") as f:
                if args.batch.endswith(".csv"):
                    reader = csv.reader(f)
                    for row in reader:
                        if row:
                            names.append(row[0].strip())
                else:
                    for line in f:
                        cleaned = line.strip()
                        if cleaned:
                            names.append(cleaned)
        except Exception as e:
            print(f"Error reading batch file: {e}")
            sys.exit(1)

        print(f"Starting batch generation of {len(names)} PDF certificates...")
        success_count = 0
        for name in names:
            safe_name = "".join([c if c.isalnum() or c in (" ", "_", "-") else "" for c in name]).strip().replace(" ", "_")
            out_file = os.path.join(args.output_dir, f"certificate_{safe_name}.pdf")
            
            success = overlay_pdf_certificate(
                template_pdf_path=args.template,
                name=name,
                date_str=date_val,
                sig_path=args.signature,
                output_pdf_path=out_file,
                font_reg_path=args.font_regular,
                font_med_path=args.font_medium,
                font_name_path=args.font_name,
                name_size=args.name_size,
                date_size=args.date_size,
                sig_w=args.sig_width,
                sig_h=args.sig_height,
                text_color=args.text_color,
                name_color=args.name_color
            )
            if success:
                success_count += 1
        print(f"Batch generation completed: {success_count}/{len(names)} PDF certificates saved in '{args.output_dir}/'.")
        
    else:
        # Single mode
        if not args.name:
            print("Error: Please specify a participant name using --name, or use --interactive / --batch.")
            sys.exit(1)
        if args.output:
            output_val = args.output
            if os.path.isdir(output_val) or output_val.endswith('\\') or output_val.endswith('/') or not os.path.splitext(output_val)[1]:
                os.makedirs(output_val, exist_ok=True)
                output_val = os.path.join(output_val, f"certificate_{args.name.replace(' ', '_')}.pdf")
        else:
            os.makedirs(HARDCODED_OUTPUT_DIR, exist_ok=True)
            output_val = os.path.join(HARDCODED_OUTPUT_DIR, f"certificate_{args.name.replace(' ', '_')}.pdf")
        
        success = overlay_pdf_certificate(
            template_pdf_path=args.template,
            name=args.name,
            date_str=date_val,
            sig_path=args.signature,
            output_pdf_path=output_val,
            font_reg_path=args.font_regular,
            font_med_path=args.font_medium,
            font_name_path=args.font_name,
            name_size=args.name_size,
            date_size=args.date_size,
            sig_w=args.sig_width,
            sig_h=args.sig_height,
            text_color=args.text_color,
            name_color=args.name_color
        )
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
