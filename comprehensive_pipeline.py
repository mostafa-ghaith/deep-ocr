import logging
import os
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from docling_core.types.doc import PictureItem, TableItem
from dotenv import load_dotenv

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    PictureDescriptionApiOptions,
    TableFormerMode,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

_log = logging.getLogger(__name__)

def openai_vlm_options():
    """Configure OpenAI API options for image analysis."""
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    options = PictureDescriptionApiOptions(
        url="https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        params=dict(
            model="gpt-4o-mini",
            max_tokens=300,
        ),
        prompt="Describe the image in detail, including any text, objects, and layout. Be accurate and thorough.",
        timeout=60,
    )
    return options

def process_document(
    input_path: Path,
    output_dir: Path,
    enable_remote_services: bool = True,
) -> None:
    """Process a document with comprehensive extraction and analysis."""
    output_dir.mkdir(parents=True, exist_ok=True)
    doc_filename = input_path.stem

    # Configure pipeline options
    pipeline_options = PdfPipelineOptions(
        enable_remote_services=enable_remote_services,
        generate_page_images=True,
        do_table_structure=True,
        do_picture_description=True,
    )

    # Configure table extraction for high accuracy
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.table_structure_options.do_cell_matching = True

    # Configure OpenAI API for image analysis
    if enable_remote_services:
        pipeline_options.picture_description_options = openai_vlm_options()

    # Initialize document converter
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Process document
    start_time = time.time()
    result = doc_converter.convert(input_path)
    end_time = time.time() - start_time
    _log.info(f"Document processed in {end_time:.2f} seconds")

    # Export tables to CSV
    for table_ix, table in enumerate(result.document.tables):
        table_df = table.export_to_dataframe()
        csv_path = output_dir / f"{doc_filename}-table-{table_ix + 1}.csv"
        _log.info(f"Saving table {table_ix + 1} to {csv_path}")
        table_df.to_csv(csv_path)

    # Export images and get VLM analysis
    picture_counter = 0
    for element, _level in result.document.iterate_items():
        if isinstance(element, PictureItem):
            picture_counter += 1
            # Save image using get_image() method
            img_path = output_dir / f"{doc_filename}-picture-{picture_counter}.png"
            with img_path.open("wb") as fp:
                element.get_image(result.document).save(fp, "PNG")
            
            # Get VLM analysis if available
            if element.annotations:
                _log.info(f"Image {element.self_ref} analysis: {element.annotations}")

    # Export comprehensive markdown
    markdown_path = output_dir / f"{doc_filename}.md"
    with markdown_path.open("w") as f:
        # Write document metadata
        f.write(f"# {doc_filename}\n\n")
        f.write(f"Processing time: {end_time:.2f} seconds\n\n")
        
        # Write document content
        f.write(result.document.export_to_markdown())
        
        # Add table references
        if result.document.tables:
            f.write("\n## Tables\n\n")
            for table_ix, table in enumerate(result.document.tables):
                f.write(f"### Table {table_ix + 1}\n\n")
                f.write(f"See CSV file: {doc_filename}-table-{table_ix + 1}.csv\n\n")
        
        # Add image references and analysis
        f.write("\n## Images\n\n")
        picture_counter = 0
        for element, _level in result.document.iterate_items():
            if isinstance(element, PictureItem):
                picture_counter += 1
                f.write(f"### {element.self_ref}\n\n")
                f.write(f"![{element.self_ref}]({doc_filename}-picture-{picture_counter}.png)\n\n")
                if element.annotations:
                    f.write("**VLM Analysis:**\n\n")
                    f.write(f"{element.annotations}\n\n")

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Load environment variables if needed
    load_dotenv()
    
    # Example usage
    input_path = Path("data/test_FIDIC Red Book Rev02 - SODIC East –  SF09 - Core and Shell Package  -Rev.03_(MALAK).pdf")
    output_dir = Path("output")
    
    process_document(
        input_path=input_path,
        output_dir=output_dir,
        enable_remote_services=True,
    )

if __name__ == "__main__":
    main() 