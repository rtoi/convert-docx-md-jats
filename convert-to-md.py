#!/usr/bin/env python3
"""
Simple DOCX/Markdown to Markdown/XML Converter

This script automatically detects input format and converts accordingly:
- DOCX → Markdown (with formatting fixes and table preservation)
- Markdown → JATS XML (with figure parsing)

Usage:
    python convert-to-md.py input.docx                    # DOCX → input.md
    python convert-to-md.py input.md                      # Markdown → input.xml
    python convert-to-md.py input.docx -o output.md       # DOCX → output.md
    python convert-to-md.py input.md -o output.xml        # Markdown → output.xml
"""

import argparse
import os
import sys
import subprocess
import re
import uuid
from pathlib import Path
from typing import Optional


def check_pandoc_installed() -> bool:
    """Check if pandoc is installed and available."""
    try:
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_pandoc_version() -> str:
    """Get pandoc version string."""
    try:
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.split('\n')[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "Unknown"


def fix_split_bold_formatting(content: str) -> str:
    """
    Fix split bold formatting by merging adjacent bold segments that should be one sentence.
    
    This addresses the issue where pandoc splits a bold sentence into multiple bold segments
    due to mixed formatting (bold + italics + quotes).
    
    Args:
        content: The markdown content to process
        
    Returns:
        The content with fixed bold formatting
    """
    # Handle cases where we have ***text*** ***text*** (bold+italic adjacent)
    pattern1 = r'\*\*\*([^*]+?)\*\*\*\s*\*\*\*([^*]+?)\*\*\*'
    def merge_bold_italic(match):
        first_text = match.group(1).strip()
        second_text = match.group(2).strip()
        return f'***{first_text} {second_text}***'
    
    content = re.sub(pattern1, merge_bold_italic, content)
    
    # Handle cases where we have ***text*** **text** (bold+italic followed by bold)
    pattern2 = r'\*\*\*([^*]+?)\*\*\*\s*\*\*([^*]+?)\*\*'
    def merge_bold_italic_bold(match):
        first_text = match.group(1).strip()
        second_text = match.group(2).strip()
        return f'***{first_text} {second_text}***'
    
    content = re.sub(pattern2, merge_bold_italic_bold, content)
    
    # Handle cases where we have **text** ***text*** (bold followed by bold+italic)
    pattern3 = r'\*\*([^*]+?)\*\*\s*\*\*\*([^*]+?)\*\*\*'
    def merge_bold_bold_italic(match):
        first_text = match.group(1).strip()
        second_text = match.group(2).strip()
        return f'***{first_text} {second_text}***'
    
    content = re.sub(pattern3, merge_bold_bold_italic, content)
    
    # Handle cases where we have **text** **text** (bold adjacent)
    pattern4 = r'\*\*([^*]+?)\*\*\s*\*\*([^*]+?)\*\*'
    def merge_bold_bold(match):
        first_text = match.group(1).strip()
        second_text = match.group(2).strip()
        return f'**{first_text} {second_text}**'
    
    content = re.sub(pattern4, merge_bold_bold, content)
    
    # Handle cases where we have ***text*** ***text* (bold+italic followed by partial bold+italic)
    pattern5 = r'\*\*\*([^*]+?)\*\*\*\s*\*\*\*([^*]+?)\*'
    def merge_bold_italic_partial(match):
        first_text = match.group(1).strip()
        second_text = match.group(2).strip()
        return f'***{first_text} {second_text}***'
    
    content = re.sub(pattern5, merge_bold_italic_partial, content)
    
    return content


def consolidate_adjacent_italics(content: str) -> str:
    """
    Consolidate adjacent italicized words into single italic blocks.
    
    This addresses the issue where pandoc creates separate italic blocks for each word
    in a phrase that should be italicized as a whole.
    
    Args:
        content: The markdown content to process
        
    Returns:
        The content with consolidated italics
    """
    # Handle both underscore and asterisk italics
    # Pattern to match adjacent italicized words: _word_ _word_ _word_ or *word* *word* *word*
    
    # First, handle underscore italics: _word_ _word_ _word_
    underscore_pattern = r'_([^_]+)_\s+_([^_]+)_'
    
    def merge_underscore_italics(match):
        first_text = match.group(1).strip()
        second_text = match.group(2).strip()
        return f'_{first_text} {second_text}_'
    
    # Apply the consolidation repeatedly until no more changes
    # This handles cases with more than 2 adjacent italicized words
    previous_content = None
    while previous_content != content:
        previous_content = content
        content = re.sub(underscore_pattern, merge_underscore_italics, content)
    
    # Then, handle asterisk italics: *word* *word* *word*
    # But only if they're not part of bold formatting (**text** or ***text***)
    asterisk_pattern = r'(?<!\*)\*([^*]+?)\*(?!\*)\s+(?<!\*)\*([^*]+?)\*(?!\*)'
    
    def merge_asterisk_italics(match):
        first_text = match.group(1).strip()
        second_text = match.group(2).strip()
        return f'*{first_text} {second_text}*'
    
    # Apply the consolidation repeatedly until no more changes
    previous_content = None
    while previous_content != content:
        previous_content = content
        content = re.sub(asterisk_pattern, merge_asterisk_italics, content)
    
    return content


def remove_image_dimensions(content: str) -> str:
    """
    Remove image dimensions from markdown content.
    
    This removes pandoc-generated dimension attributes like {width="6.268055555555556in" height="4.076388888888889in"}
    from image references in markdown.
    
    Args:
        content: The markdown content to process
        
    Returns:
        The content with image dimensions removed
    """
    # Pattern to match image dimensions: {width="..." height="..."} or {width="..."} or {height="..."}
    # This handles various combinations of width and height attributes
    dimension_pattern = r'\s*\{[^}]*width\s*=\s*"[^"]*"[^}]*\}\s*'
    dimension_pattern2 = r'\s*\{[^}]*height\s*=\s*"[^"]*"[^}]*\}\s*'
    
    # Remove width-based dimensions
    content = re.sub(dimension_pattern, '', content)
    # Remove height-based dimensions (in case they appear without width)
    content = re.sub(dimension_pattern2, '', content)
    
    return content


def standardize_image_filename(filename: str) -> str:
    """
    Standardize image filenames by:
    1. Converting extensions to lowercase
    2. Standardizing jpeg to jpg
    
    Args:
        filename: The original filename to standardize
        
    Returns:
        The standardized filename
    """
    # Split filename and extension
    name, ext = os.path.splitext(filename)
    
    # Convert extension to lowercase
    ext = ext.lower()
    
    # Standardize jpeg to jpg
    if ext == '.jpeg':
        ext = '.jpg'
    
    # Handle DOCX image naming pattern (image1, image2, etc.)
    # Match patterns like: image1, image2, image10, etc.
    # image_pattern = r'^image(\d+)$'
    # match = re.match(image_pattern, name, re.IGNORECASE)
    
    # if match:
        # Convert image1 -> figure-1, image2 -> figure-2, etc.
        # number = match.group(1)
        # name = f'figure-{number}'
    
    return f'{name}{ext}'


def process_image_links_to_basename(content: str) -> str:
    """
    Process image links in markdown to use only the basename (filename without path)
    and standardize the filenames.
    
    This converts image references like ![alt](media/image1.png) to ![alt](figure-1.png)
    for OJS compatibility where file paths are handled directly and filenames are standardized.
    
    Args:
        content: The markdown content to process
        
    Returns:
        The content with image links converted to basename only and standardized
    """
    # Pattern to match markdown image links: ![alt text](path/to/image.ext)
    # This captures the alt text and the full path, then extracts just the basename
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image_link(match):
        alt_text = match.group(1)
        image_path = match.group(2)
        
        # Extract just the basename (filename with extension)
        basename = os.path.basename(image_path)
        
        # Standardize the filename
        standardized_basename = standardize_image_filename(basename)
        
        return f'![{alt_text}]({standardized_basename})'
    
    # Apply the image link processing
    content = re.sub(image_pattern, replace_image_link, content)
    
    return content


def parse_figures_for_jats(content: str) -> str:
    """
    Parse figure patterns from JATS XML content and convert them to proper JATS XML figure elements.
    
    This function looks for patterns in the JATS XML where pandoc has converted:
    - Figure labels as bold text
    - Images as inline-graphic elements
    - Captions as text following the image
    
    And converts them to proper JATS XML figure elements.
    
    Args:
        content: The JATS XML content to process
        
    Returns:
        The content with figures converted to proper JATS XML format
    """
    # Patterns to match figure blocks in JATS XML:
    # Pattern 1: Single paragraph structure: <p><bold>Figure X</bold> <inline-graphic ... />caption</p>
    # Handles both self-closing and paired inline-graphic elements
    figure_pattern_single = r'(<p[^>]*>\s*<bold[^>]*>Figure\s+\d+</bold>\s*<inline-graphic[^>]*(?:/>|>.*?</inline-graphic>)\s*(.*?)</p>)'
    
    # Pattern 2: Multi-paragraph structure: <p><bold>Figure X</bold></p>...<p><inline-graphic ... />caption</p>
    # This pattern matches from the figure label paragraph to the paragraph containing the inline-graphic
    # Handles both self-closing and paired inline-graphic elements
    figure_pattern_multi = r'(<p[^>]*>\s*<bold[^>]*>Figure\s+\d+</bold>\s*</p>.*?<p[^>]*>\s*<inline-graphic[^>]*(?:/>|>.*?</inline-graphic>)\s*(.*?)</p>)'
    
    def replace_figure(match):
        full_para = match.group(1)
        caption_text = match.group(2).strip()
        
        # Extract figure number from the label
        label_match = re.search(r'<bold[^>]*>(Figure\s+\d+)</bold>', full_para)
        label = label_match.group(1) if label_match else "Figure"
        
        # Extract image information from inline-graphic element
        href_match = re.search(r'xlink:href="([^"]+)"', full_para)
        mime_subtype_match = re.search(r'mime-subtype="([^"]+)"', full_para)
        
        image_filename = href_match.group(1) if href_match else "image.png"
        # Standardize the filename
        image_filename = standardize_image_filename(image_filename)
        mime_subtype = mime_subtype_match.group(1) if mime_subtype_match else "png"
        
        # Generate unique IDs
        fig_id = f"fig-{uuid.uuid4().hex[:24]}"
        object_id = f"object-id-{uuid.uuid4().hex[:24]}"
        caption_id = f"caption-{uuid.uuid4().hex[:24]}"
        title_id = f"title-{uuid.uuid4().hex[:24]}"
        p_id = f"p-{uuid.uuid4().hex[:24]}"
        graphic_id = f"graphic-{uuid.uuid4().hex[:24]}"
        
        # Build JATS XML figure element
        jats_figure = f'''<fig id="{fig_id}">
        <object-id id="{object_id}">{fig_id}</object-id>
        <label>{label}</label>
        <caption id="{caption_id}">
          <title id="{title_id}" />
          <p id="{p_id}">{caption_text}</p>
        </caption>
        <graphic id="{graphic_id}" mime-subtype="{mime_subtype}" mimetype="image" xlink:href="{image_filename}" />
      </fig>'''
        
        return jats_figure
    
    # Apply the figure conversion - try multi-paragraph pattern first, then single paragraph
    content = re.sub(figure_pattern_multi, replace_figure, content, flags=re.MULTILINE | re.DOTALL)
    content = re.sub(figure_pattern_single, replace_figure, content, flags=re.MULTILINE | re.DOTALL)
    
    return content


def ensure_figure_and_table_ids(content: str) -> str:
    """Give every figure, table wrapper, and table a document-unique ID.

    Keep existing IDs when they are unique. Reserve IDs on other elements too,
    so generated IDs cannot collide with them.
    """
    tag_pattern = re.compile(r'<([A-Za-z][\w:.-]*)\b(?:[^>"\']|"[^"]*"|\'[^\']*\')*>')
    id_pattern = re.compile(r'(?<![\w:.-])id\s*=\s*(["\'])(.*?)\1', re.DOTALL)
    target_names = {'fig', 'table-wrap', 'table'}
    tags = list(tag_pattern.finditer(content))

    # IDs on other elements take priority if the input already contains a collision.
    reserved = set()
    for tag in tags:
        if tag.group(1) not in target_names:
            existing = id_pattern.search(tag.group(0))
            if existing:
                reserved.add(existing.group(2))

    def add_id(tag):
        name = tag.group(1)
        opening_tag = tag.group(0)
        if name not in target_names:
            return opening_tag

        existing = id_pattern.search(opening_tag)
        if existing and existing.group(2) and existing.group(2) not in reserved:
            reserved.add(existing.group(2))
            return opening_tag

        prefix = 'fig' if name == 'fig' else 'table-wrap' if name == 'table-wrap' else 'table'
        new_id = f'{prefix}-{uuid.uuid4().hex}'
        while new_id in reserved:
            new_id = f'{prefix}-{uuid.uuid4().hex}'
        reserved.add(new_id)

        if existing:
            return opening_tag[:existing.start(2)] + new_id + opening_tag[existing.end(2):]
        return opening_tag.replace(f'<{name}', f'<{name} id="{new_id}"', 1)

    # Rebuild from the original spans so existing formatting and the DOCTYPE survive.
    parts = []
    cursor = 0
    for tag in tags:
        parts.append(content[cursor:tag.start()])
        parts.append(add_id(tag))
        cursor = tag.end()
    parts.append(content[cursor:])
    return ''.join(parts)


def flatten_table_blockquotes(content: str) -> str:
    """
    Flatten complex table cell structures to simple, OJS-compatible format.

    This addresses issues where Pandoc converts blockquotes (>) within markdown table
    cells to <disp-quote> elements or creates multiple <p> elements, which don't render
    properly in OJS. We simplify to a single paragraph with line breaks.

    Args:
        content: The JATS XML content to process

    Returns:
        The content with table cells simplified for OJS compatibility
    """
    # Pattern to match table cells
    td_pattern = r'<td([^>]*)>(.*?)</td>'

    def process_table_cell(match):
        td_attrs = match.group(1)
        td_content = match.group(2).strip()

        # If cell is empty or has no paragraph tags, return as-is
        if not td_content or '<p>' not in td_content:
            return match.group(0)

        # Step 1: Remove disp-quote and wrapper paragraphs
        # Pattern: <p specific-use="wrapper"><disp-quote>...</disp-quote></p>
        wrapper_pattern = r'<p\s+specific-use="wrapper"\s*>\s*<disp-quote>(.*?)</disp-quote>\s*</p>'
        td_content = re.sub(wrapper_pattern, r'\1', td_content, flags=re.DOTALL)

        # Step 2: Extract all paragraph contents
        p_pattern = r'<p>(.*?)</p>'
        paragraphs = re.findall(p_pattern, td_content, flags=re.DOTALL)

        if not paragraphs:
            return match.group(0)

        # Step 3: Join paragraphs with semicolon separators
        # OJS sanitizes out all break elements (<p>, <break/>, <br/>) and line break characters
        # from table cells. Use semicolons to separate citations for readability.
        combined_content = paragraphs[0].strip()
        for para in paragraphs[1:]:
            para_stripped = para.strip()
            if para_stripped:
                # Add semicolon separator for readability
                combined_content += f'; {para_stripped}'

        # Don't wrap in <p> - OJS needs direct content in table cells
        processed_td_content = combined_content

        return f'<td{td_attrs}>{processed_td_content}</td>'

    # Apply the table cell processing to all table cells
    content = re.sub(td_pattern, process_table_cell, content, flags=re.DOTALL)

    return content


def wrap_body_content_in_sections(content: str) -> str:
    """
    Ensure all content within the <body> tag is wrapped in <sec> tags.

    This function looks for content directly inside the <body> tag that is not already
    wrapped in <sec> tags and wraps it appropriately. Each section gets a unique ID.

    Args:
        content: The JATS XML content to process

    Returns:
        The content with body content properly wrapped in sec tags with unique IDs
    """
    # Pattern to match the <body> tag and its content
    body_pattern = r'(<body[^>]*>)(.*?)(</body>)'
    
    def wrap_body_content(match):
        body_open = match.group(1)
        body_content = match.group(2)
        body_close = match.group(3)
        
        # If body is empty or only contains whitespace, return as is
        if not body_content.strip():
            return f"{body_open}{body_content}{body_close}"
        
        # Split content into lines to process
        lines = body_content.split('\n')
        result_lines = []
        current_section = []
        in_section = False
        section_counter = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                if current_section:
                    current_section.append(line)
                continue
            
            # Check if this line starts a new section
            if line_stripped.startswith('<sec'):
                # If we have content in current_section, wrap it in a section
                if current_section and not in_section:
                    section_id = f"heading-{uuid.uuid4().hex}"
                    result_lines.append(f'  <sec id="{section_id}">')
                    result_lines.extend(current_section)
                    result_lines.append('  </sec>')
                    current_section = []
                
                # Start new section - check if it already has an ID
                if 'id=' in line_stripped:
                    # Section already has an ID, keep it as is
                    result_lines.append(line)
                else:
                    # Add unique ID to existing section
                    section_id = f"heading-{uuid.uuid4().hex}"
                    # Replace <sec with <sec id="..."
                    new_line = line_stripped.replace('<sec', f'<sec id="{section_id}"')
                    result_lines.append(new_line)
                in_section = True
                current_section = []
                
            elif line_stripped.startswith('</sec>'):
                # End current section
                result_lines.append(line)
                in_section = False
                current_section = []
                
            else:
                # Regular content line
                if in_section:
                    # We're already in a section, just add the line
                    result_lines.append(line)
                else:
                    # We're not in a section, collect content
                    current_section.append(line)
        
        # Handle any remaining content that wasn't wrapped
        if current_section and not in_section:
            section_id = f"heading-{uuid.uuid4().hex}"
            result_lines.append(f'  <sec id="{section_id}">')
            result_lines.extend(current_section)
            result_lines.append('  </sec>')
        
        # Join the processed content
        processed_content = '\n'.join(result_lines)
        
        return f"{body_open}\n{processed_content}\n{body_close}"
    
    # Apply the section wrapping
    content = re.sub(body_pattern, wrap_body_content, content, flags=re.MULTILINE | re.DOTALL)
    
    return content





def convert_docx_to_markdown(input_file: str, output_file: str) -> bool:
    """
    Convert a DOCX file to Markdown using pandoc.
    
    Args:
        input_file: Path to input DOCX file
        output_file: Path to output Markdown file
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return False
    
    # Get the output directory for media extraction
    output_dir = os.path.dirname(output_file) or '.'
    media_dir = os.path.join(output_dir, 'media')
    
    # Create a temporary directory for extraction to avoid nested media/media structure
    temp_extract_dir = os.path.join(output_dir, 'temp_extract')
    
    # Build pandoc command
    cmd = ['pandoc', input_file, '-o', output_file]
    
    # Set output format to markdown with multiline tables (automatic table preservation)
    cmd.extend(['--to', 'markdown+multiline_tables'])
    
    # Add options for better academic document handling
    cmd.extend([
        '--wrap=none',  # Don't wrap lines
        '--markdown-headings=atx',  # Use # style headings
        '--reference-location=document',  # Put references at end
        '--extract-media=' + temp_extract_dir,  # Extract media to temporary directory
    ])
    
    try:
        print(f"Converting '{input_file}' to '{output_file}'...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Move extracted media files from temp directory to final media directory
        if os.path.exists(temp_extract_dir):
            # Create the final media directory if it doesn't exist
            os.makedirs(media_dir, exist_ok=True)
            
            # Move files from temp_extract_dir/media/ to media_dir/
            temp_media_dir = os.path.join(temp_extract_dir, 'media')
            if os.path.exists(temp_media_dir):
                import shutil
                for file in os.listdir(temp_media_dir):
                    src = os.path.join(temp_media_dir, file)
                    # Standardize the filename
                    standardized_filename = standardize_image_filename(file)
                    dst = os.path.join(media_dir, standardized_filename)
                    shutil.move(src, dst)
                
                # Remove the temporary extraction directory
                shutil.rmtree(temp_extract_dir)
                print(f"✓ Extracted media files to '{media_dir}'")
        
        # Post-process the output
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert single asterisk italics to underscore italics
            # This regex matches *text* but not **text** (bold) or ***text*** (bold italic)
            content = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'_\1_', content)
            
            # Fix split bold formatting - merge adjacent bold segments that should be one sentence
            content = fix_split_bold_formatting(content)
            
            # Consolidate adjacent italicized words into single italic blocks
            content = consolidate_adjacent_italics(content)

            # Remove image dimensions
            content = remove_image_dimensions(content)
            
            # Process image links to use basename only (for OJS compatibility)
            content = process_image_links_to_basename(content)
            
            # Write the processed content back
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"✓ Successfully converted '{input_file}' to '{output_file}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error converting '{input_file}': {e}")
        if e.stderr:
            print(f"Pandoc error: {e.stderr}")
        return False


def convert_markdown_to_xml(input_file: str, output_file: str) -> bool:
    """
    Convert a Markdown file to JATS XML using pandoc.
    
    Args:
        input_file: Path to input Markdown file
        output_file: Path to output JATS XML file
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return False
    
    # Build pandoc command
    cmd = ['pandoc', input_file, '-o', output_file]
    
    # Set output format to JATS archiving
    cmd.extend(['--to', 'jats_archiving'])
    
    # Add standalone option
    cmd.append('--standalone')
    
    # Add options for better academic document handling
    cmd.extend([
        '--wrap=none',  # Don't wrap lines
        '--reference-location=document',  # Put references at end
    ])
    
    try:
        print(f"Converting '{input_file}' to '{output_file}'...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Post-process the JATS XML to handle figure parsing
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse and convert figure patterns to proper JATS XML
            content = parse_figures_for_jats(content)

            # Flatten blockquotes in table cells to styled-content elements
            content = flatten_table_blockquotes(content)

            # Wrap body content in sections
            content = wrap_body_content_in_sections(content)

            # Include Pandoc's figures and both levels of each JATS table.
            content = ensure_figure_and_table_ids(content)

            # Write the processed content back
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"✓ Successfully converted '{input_file}' to '{output_file}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error converting '{input_file}' to JATS XML: {e}")
        if e.stderr:
            print(f"Pandoc error: {e.stderr}")
        return False


def main():
    """Main function to handle command line arguments and execute conversion."""
    parser = argparse.ArgumentParser(
        description="Convert DOCX to Markdown or Markdown to JATS XML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.docx                    # DOCX → input.md
  %(prog)s input.md                      # Markdown → input.xml
  %(prog)s input.docx -o output.md       # DOCX → output.md
  %(prog)s input.md -o output.xml        # Markdown → output.xml
        """
    )
    
    parser.add_argument('input', help='Input file (DOCX or Markdown)')
    parser.add_argument('-o', '--output', help='Output file (optional)')
    
    args = parser.parse_args()
    
    # Check if pandoc is installed
    if not check_pandoc_installed():
        print("Error: pandoc is not installed or not found in PATH.")
        print("Please install pandoc from https://pandoc.org/installing.html")
        sys.exit(1)
    
    print(f"Using {get_pandoc_version()}")
    
    # Determine input type and output file
    input_path = Path(args.input)
    input_ext = input_path.suffix.lower()
    
    if input_ext == '.docx':
        # DOCX → Markdown
        if args.output:
            output_file = args.output
        else:
            output_file = input_path.with_suffix('.md')
        
        success = convert_docx_to_markdown(args.input, str(output_file))
        
    elif input_ext == '.md':
        # Markdown → XML
        if args.output:
            output_file = args.output
        else:
            output_file = input_path.with_suffix('.xml')
        
        success = convert_markdown_to_xml(args.input, str(output_file))
        
    else:
        print(f"Error: Unsupported input format '{input_ext}'. Supported formats: .docx, .md")
        sys.exit(1)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
