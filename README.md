# DOCX/Markdown to JATS XML Converter

A Python script that converts academic documents between DOCX, Markdown, and JATS XML formats. Uses pandoc for high-quality conversion with additional post-processing for academic publishing standards.

## Features

### DOCX to Markdown Conversion
- ✅ **Footnotes preservation** - Academic footnotes are maintained in the output
- ✅ **Citation support** - Handles academic citations and references
- ✅ **Table formatting** - Preserves table structure with multiline formatting
- ✅ **Image handling** - Maintains image references and removes dimensions
- ✅ **Content preservation** - Maintains original document structure
- ✅ **Formatting fixes** - Merges split bold segments and consolidates italics
- ✅ **Italics preference** - Converts to underscore format for better compatibility

### Markdown to JATS XML Conversion
- ✅ **JATS compliance** - Generates valid JATS archiving XML
- ✅ **Figure parsing** - Converts figure patterns to proper JATS XML elements
- ✅ **Section wrapping** - Ensures all body content is wrapped in `<sec>` tags
- ✅ **Unique IDs** - Automatically generates unique IDs for each section
- ✅ **Academic structure** - Maintains proper academic document hierarchy

## Prerequisites

### 1. Install pandoc

The script requires pandoc to be installed on your system.

**macOS (using Homebrew):**
```bash
brew install pandoc
```

**macOS (using MacPorts):**
```bash
sudo port install pandoc
```

**Windows:**
Download from [pandoc.org/installing.html](https://pandoc.org/installing.html)

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install pandoc
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install pandoc
```

### 2. Python Requirements

The script uses only Python standard library modules, so no additional Python packages are needed.

## Usage

### Basic Usage

**DOCX to Markdown:**
```bash
python convert-to-md.py article.docx
```

**Markdown to JATS XML:**
```bash
python convert-to-md.py article.md
```

### Custom Output Files

**DOCX to Markdown with custom output:**
```bash
python convert-to-md.py article.docx -o output.md
```

**Markdown to JATS XML with custom output:**
```bash
python convert-to-md.py article.md -o output.xml
```

### Command Line Options

```
positional arguments:
  input                 Input file (DOCX or Markdown)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file (optional)
```

## Examples

### Example 1: DOCX to Markdown
```bash
# Convert DOCX to Markdown
python convert-to-md.py "Articles_Wright - 2nd copyedit done.docx"
# Output: Articles_Wright - 2nd copyedit done.md
```

### Example 2: Markdown to JATS XML
```bash
# Convert Markdown to JATS XML
python convert-to-md.py article.md
# Output: article.xml
```

### Example 3: Custom Output Files
```bash
# DOCX to custom Markdown filename
python convert-to-md.py article.docx -o processed_article.md

# Markdown to custom XML filename
python convert-to-md.py article.md -o final_article.xml
```

## Output Formats

### Markdown Output
The script generates Markdown files with:
- **Footnotes**: Preserved using pandoc's footnote syntax `[^1]`
- **Headings**: Converted to ATX style (`# Heading`)
- **Tables**: Preserved with multiline formatting
- **Images**: Referenced with relative paths (dimensions removed)
- **Italics**: Uses underscores (`_italic_`)
- **Bold formatting**: Merged split segments into cohesive sentences
- **Italics consolidation**: Combined adjacent italicized words

### JATS XML Output
The script generates JATS XML files with:
- **JATS compliance**: Valid JATS archiving format
- **Figure and table elements**: Unique IDs on `<fig>`, `<table-wrap>`, and `<table>`
- **Section structure**: All content wrapped in `<sec>` tags with unique IDs
- **Academic metadata**: Proper front matter and back matter
- **Cross-references**: Maintained footnote and figure references

### Sample JATS XML Structure

```xml
<article xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink" dtd-version="1.2" article-type="other">
  <front>
    <journal-meta>
      <!-- Journal metadata -->
    </journal-meta>
    <article-meta>
      <!-- Article metadata -->
    </article-meta>
  </front>
  <body>
    <sec id="heading-5f290d998d3a167395eeea11b3fbc3ff">
      <p>Content here...</p>
      <fig id="fig-3560fbc17fd54362bc31c72c">
        <object-id id="object-id-c1d33202293748a493463ddb">fig-3560fbc17fd54362bc31c72c</object-id>
        <label>Figure 1</label>
        <caption id="caption-d7d95e70283f4c78b38f7282">
          <title id="title-060e6cb000044787b6c3e1fa"/>
          <p id="p-ea1725f21d5f44a7a4b39ee8">Figure caption text</p>
        </caption>
        <graphic id="graphic-ff70ab9c52f74c9ba31b47ba" mime-subtype="png" mimetype="image" xlink:href="media/image1.png"/>
      </fig>
    </sec>
  </body>
  <back>
    <fn-group>
      <!-- Footnotes -->
    </fn-group>
  </back>
</article>
```

## Processing Details

### DOCX to Markdown Processing
1. **Pandoc conversion** - Converts DOCX to Markdown with academic formatting
2. **Formatting fixes** - Merges split bold segments and consolidates italics
3. **Image cleanup** - Removes pandoc-generated image dimensions
4. **Italics conversion** - Converts asterisk italics to underscore format

### Markdown to JATS XML Processing
1. **Pandoc conversion** - Converts Markdown to JATS archiving XML
2. **Figure parsing** - Converts figure patterns to proper JATS XML elements
3. **Section wrapping** - Ensures all body content is wrapped in `<sec>` tags
4. **ID generation** - Adds unique IDs to sections, figures, table wrappers, and tables; preserves existing unique IDs

## Troubleshooting

### Common Issues

1. **"pandoc is not installed"**
   - Install pandoc following the instructions above
   - Ensure pandoc is in your system PATH

2. **"Input file not found"**
   - Check the file path is correct
   - Use quotes around filenames with spaces

3. **"Unsupported input format"**
   - Only `.docx` and `.md` files are supported
   - Check the file extension

4. **JATS XML validation errors**
   - The script generates JATS archiving format
   - Ensure your XML validator supports JATS DTD

5. **Figure rendering issues**
   - Check that image files referenced in the XML exist
   - Verify image paths are correct relative to the XML file

### Getting Help

Run the script with `--help` to see all available options:
```bash
python convert-to-md.py --help
```

## Versioning

This project uses [Semantic Versioning](https://semver.org/) for version management.

### Current Version
The current version is displayed in the web interface and can be checked programmatically:

```python
from version import get_version, get_version_display
print(get_version())        # "1.0.0"
print(get_version_display()) # "v1.0.0"
```

### Version Management
Use the included version manager script to handle version updates:

```bash
# Show current version
python version_manager.py current

# Bump version (major, minor, or patch)
python version_manager.py bump patch

# Set specific version
python version_manager.py set 1.1.0

# Update version and changelog
python version_manager.py update 1.1.0 minor
```

### Changelog
See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## License

This script is provided as-is for academic document conversion. It uses pandoc which is licensed under the GPL.

## Contributing

Feel free to modify the script for your specific needs. The code is well-documented and modular for easy customization.

When contributing:
1. Update the version using the version manager
2. Add your changes to the CHANGELOG.md
3. Follow semantic versioning principles
