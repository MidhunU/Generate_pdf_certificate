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

# Baseline template size used to discover coordinates (996x721 points)
BASE_WIDTH = 996.0
BASE_HEIGHT = 721.0

# Pillow/original coordinates (from top-left origin)
# To raise any section, DECREASE its Y_PILLOW value.
# To lower any section, INCREASE its Y_PILLOW value.
NAME_BASE_X = 498.0
NAME_BASE_Y_PILLOW = 373.0  # Decreased from 393.0 to raise the name

DATE_BASE_X = 182.0
DATE_BASE_Y_PILLOW = 600.0  # Decreased from 610.0 to raise the date

SIG_BASE_X = 815.0
SIG_BASE_Y_PILLOW = 630.0   # Increased from 614.0 to lower the signature (bottom edge)

def get_current_date_string():
    """Returns today's date formatted like 'June 15, 2026'."""
    now = datetime.datetime.now()
    return now.strftime("%B %d, %Y")

def register_fonts(font_reg_path, font_med_path):
    """Registers Google Sans fonts for ReportLab canvas."""
    font_reg = 'Helvetica'
    font_med = 'Helvetica-Bold'
    
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
        
    return font_reg, font_med

def create_overlay_page(
    page_width,
    page_height,
    name,
    date_str,
    sig_path,
    font_reg,
    font_med,
    name_size=36,
    date_size=16,
    sig_scale_w=130,
    sig_scale_h=130,
    text_color="#202124"
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
    
    # Draw Name
    can.setFont(font_med, s_name_size)
    # Convert hex to rgb tuple for reportlab (expects floats 0-1)
    if text_color.startswith('#'):
        h = text_color.lstrip('#')
        r, g, b = tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))
    else:
        r, g, b = 0.125, 0.129, 0.141 # default #202124
    
    can.setFillColorRGB(r, g, b)
    can.drawCentredString(name_x, name_y, name)
    
    # Draw Date
    can.setFont(font_reg, s_date_size)
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
    name_size=36,
    date_size=16,
    sig_w=130,
    sig_h=100,
    text_color="#202124"
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
        font_reg, font_med = register_fonts(font_reg_path, font_med_path)
        
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
            name_size=name_size,
            date_size=date_size,
            sig_scale_w=sig_w,
            sig_scale_h=sig_h,
            text_color=text_color
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
    default_date = get_current_date_string()
    date_str = input(f"Enter date (press Enter for today: '{default_date}'): ").strip()
    if not date_str:
        date_str = default_date

    # 4. Signature File
    default_sig = "mock_signature.png" if os.path.exists("mock_signature.png") else ""
    sig_prompt = f" (press Enter for '{default_sig}')" if default_sig else ""
    sig_path = input(f"Enter path to signature PNG{sig_prompt}: ").strip()
    if not sig_path:
        sig_path = default_sig
    while sig_path and not os.path.exists(sig_path):
        print(f"File '{sig_path}' not found.")
        sig_path = input("Enter path to signature PNG: ").strip()

    # 5. Output
    if len(names) == 1:
        default_out = f"certificate_{names[0].replace(' ', '_')}.pdf"
        output = input(f"Enter output PDF name (press Enter for '{default_out}'): ").strip()
        if not output:
            output = default_out
            
        # If the input is a directory path, append the default filename to prevent Permission Denied error
        if os.path.isdir(output) or output.endswith('\\') or output.endswith('/') or not os.path.splitext(output)[1]:
            os.makedirs(output, exist_ok=True)
            output = os.path.join(output, default_out)
        
        overlay_pdf_certificate(
            template_pdf_path=template,
            name=names[0],
            date_str=date_str,
            sig_path=sig_path,
            output_pdf_path=output
        )
    else:
        out_dir = input("Enter output directory for certificates (press Enter for 'outputs'): ").strip()
        if not out_dir:
            out_dir = "outputs"
        os.makedirs(out_dir, exist_ok=True)
        
        success_count = 0
        for name in names:
            safe_name = "".join([c if c.isalnum() or c in (" ", "_", "-") else "" for c in name]).strip().replace(" ", "_")
            out_file = os.path.join(out_dir, f"certificate_{safe_name}.pdf")
            success = overlay_pdf_certificate(
                template_pdf_path=template,
                name=name,
                date_str=date_str,
                sig_path=sig_path,
                output_pdf_path=out_file
            )
            if success:
                success_count += 1
        print(f"\nBatch completed: {success_count}/{len(names)} PDF certificates saved in '{out_dir}/'.")

def main():
    parser = argparse.ArgumentParser(
        description="Append participant name, custom date, and signature PNG to a PDF template."
    )
    parser.add_argument("--interactive", action="store_true", help="Run in interactive console prompt mode")
    parser.add_argument("--template", default="certificate_template.pdf", help="Path to the PDF template")
    parser.add_argument("--name", help="Participant name")
    parser.add_argument("--date", help="Date to write on certificate (defaults to current date)")
    parser.add_argument("--signature", help="Path to signature PNG file")
    parser.add_argument("--output", help="Output PDF file path")
    
    # Custom styling parameters
    parser.add_argument("--font-regular", default=DEFAULT_FONT_REGULAR, help="Path to regular font file")
    parser.add_argument("--font-medium", default=DEFAULT_FONT_MEDIUM, help="Path to medium font file")
    parser.add_argument("--name-size", type=int, default=36, help="Font size for participant name")
    parser.add_argument("--date-size", type=int, default=16, help="Font size for date")
    parser.add_argument("--sig-width", type=int, default=130, help="Signature scale width")
    parser.add_argument("--sig-height", type=int, default=130, help="Signature scale height")
    parser.add_argument("--text-color", default="#202124", help="Hex color code for text (e.g. #202124)")

    # Batch option
    parser.add_argument("--batch", help="Path to text/CSV file of names for batch generation")
    parser.add_argument("--output-dir", default="outputs", help="Directory for batch outputs")

    args = parser.parse_args()

    # Determine date
    date_val = args.date if args.date else get_current_date_string()

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
                name_size=args.name_size,
                date_size=args.date_size,
                sig_w=args.sig_width,
                sig_h=args.sig_height,
                text_color=args.text_color
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
            output_val = f"certificate_{args.name.replace(' ', '_')}.pdf"
        
        success = overlay_pdf_certificate(
            template_pdf_path=args.template,
            name=args.name,
            date_str=date_val,
            sig_path=args.signature,
            output_pdf_path=output_val,
            font_reg_path=args.font_regular,
            font_med_path=args.font_medium,
            name_size=args.name_size,
            date_size=args.date_size,
            sig_w=args.sig_width,
            sig_h=args.sig_height,
            text_color=args.text_color
        )
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
