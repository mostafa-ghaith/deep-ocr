# Document Processing Pipeline

This pipeline provides comprehensive document processing capabilities including OCR, table extraction, image analysis, and markdown generation.

## Features

- **Document Processing**: Handles PDF documents with comprehensive extraction capabilities
- **Table Extraction**: Converts tables to structured CSV format with high accuracy
- **Image Analysis**: Extracts and analyzes images using VLM (Vision Language Model)
- **OCR Processing**: Extracts text content from documents
- **Markdown Export**: Generates comprehensive markdown files with all extracted content

## Output Structure

For each processed document, the pipeline creates a dedicated output directory with the following structure:

```
output/
  {document_name}_output.pdf/
    ├── {document_name}-table-1.csv
    ├── {document_name}-picture-1.png
    └── {document_name}.md
```

### Output Files

1. **CSV Files** (`{document_name}-table-{n}.csv`)
   - Each table from the document is exported as a separate CSV file
   - Tables are processed with high accuracy and cell matching
   - Maintains the original table structure and content

2. **Image Files** (`{document_name}-picture-{n}.png`)
   - All images from the document are extracted and saved as PNG files
   - Each image is analyzed using VLM for detailed description
   - Image analysis results are included in the markdown file

3. **Markdown File** (`{document_name}.md`)
   - Contains comprehensive document information including:
     - Document metadata
     - Processing time
     - Full document content
     - Table references with links to CSV files
     - Image references with links to PNG files
     - VLM analysis of images

## Processing Pipeline

1. **Document Input**
   - Accepts PDF documents as input
   - Creates a dedicated output directory for each document

2. **Table Processing**
   - Extracts all tables from the document
   - Processes tables with high accuracy mode
   - Performs cell matching for better structure
   - Exports each table to a separate CSV file

3. **Image Processing**
   - Extracts all images from the document
   - Saves images as PNG files
   - Analyzes images using VLM (if enabled)
   - Captures detailed image descriptions

4. **Content Processing**
   - Performs OCR on the document
   - Extracts and structures all text content
   - Maintains document layout and formatting

5. **Output Generation**
   - Creates CSV files for tables
   - Saves images as PNG files
   - Generates comprehensive markdown file
   - Links all components together in the markdown

## Usage

```python
from pathlib import Path
from comprehensive_pipeline import process_document

# Process a document
process_document(
    input_path=Path("path/to/document.pdf"),
    output_dir=Path("output"),
    enable_remote_services=True  # Set to False to disable VLM analysis
)
```

## Requirements

- Python 3.x
- Required Python packages (specified in requirements.txt)
- OpenAI API key (for VLM analysis, if enabled)

## Configuration

The pipeline can be configured through the following options:

- `enable_remote_services`: Enable/disable VLM analysis
- `generate_page_images`: Enable/disable page image generation
- `do_table_structure`: Enable/disable table extraction
- `do_picture_description`: Enable/disable image analysis

## Notes

- The pipeline uses OpenAI's GPT-4 Vision model for image analysis when enabled
- Table extraction uses high accuracy mode for better results
- All output files are organized in a dedicated directory for each processed document
- The markdown file serves as a comprehensive index of all extracted content 