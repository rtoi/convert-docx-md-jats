# Changelog

All notable changes to the DOCX to JATS XML Converter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Fixed
- Add an empty `<title/>` to generated or existing `<sec>` elements without a direct title child, while preserving authored section titles.
- Add document-unique IDs to JATS `<fig>`, `<table-wrap>`, and `<table>` elements produced by Markdown conversion.
- Preserve existing unique IDs and replace missing or colliding IDs on those elements.

## [1.2.0] - 2025-12-28

### Added
- Post-processing function `flatten_table_blockquotes()` to handle complex table cell structures in JATS XML output
- Support for converting markdown blockquotes within table cells to OJS-compatible format

### Fixed
- **Table rendering in OJS**: Tables with blockquote content in cells now render correctly
  - Removed nested `<disp-quote>` elements that OJS doesn't support in table cells
  - Removed multiple `<p>` elements per cell that OJS strips during rendering
  - Removed `<break />` and `<br />` elements that OJS sanitizes from table cells
  - Citations in table cells now separated by semicolons for readability
- Table cells now use direct text content without paragraph wrappers for OJS compatibility

### Changed
- Table cell processing in markdown → JATS conversion pipeline:
  1. Detects and removes `<disp-quote>` elements from table cells
  2. Flattens multiple `<p>` elements into single text content
  3. Joins multiple paragraphs with semicolon separators (`; `)
  4. Preserves inline formatting (`<italic>`, etc.)

### Technical Details
**Problem:** Pandoc converts markdown blockquotes (`>`) in table cells to JATS `<disp-quote>` elements wrapped in `<p>` tags. OJS sanitizes these block-level elements from table cells during JATS→HTML rendering, causing content to disappear.

**Solution:** Post-process JATS XML to flatten table cell content by extracting paragraph contents, removing block-level wrapper elements, and concatenating with semicolon separators while maintaining inline formatting.

**Result:** Table cells render properly in OJS with readable, semicolon-separated citations.

## [1.1.0] - 2025-10-17

### Added
- Comprehensive workflow instructions for OJS article preparation
- Step-by-step guide with visual indicators and formatting examples
- Mobile-responsive design for workflow instructions
- Pure CSS framework integration (3.7KB gzipped)

## [1.0.0] - 2025-09-18

### Added
- Initial release of DOCX to JATS XML Converter web application
- DOCX to Markdown conversion with academic formatting support
- Markdown to JATS XML conversion with full JATS compliance
- Web interface with Flask backend
- Production deployment support with Gunicorn
- Semantic versioning implementation

### Technical Details
- Built with Python 3.12+ and Flask 2.0+
- Uses pandoc for high-quality document conversion
- Cross-platform compatibility (macOS, Linux, Windows)

### Dependencies
- Flask >= 2.0.0
- Gunicorn >= 20.0.0
- Werkzeug >= 2.0.0
- pandoc (system dependency)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.2.0 | 2025-12-28 | Fixed OJS table rendering with semicolon-separated citations |
| 1.1.0 | 2025-10-17 | Added workflow instructions and enhanced UI |
| 1.0.0 | 2025-09-18 | Initial release with full conversion capabilities |

## Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/) principles:

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backwards compatible manner
- **PATCH** version when you make backwards compatible bug fixes

## Contributing

When contributing to this project, please update this changelog with your changes following the established format.
