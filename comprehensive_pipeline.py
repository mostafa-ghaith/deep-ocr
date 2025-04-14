import logging
import os
import time
from pathlib import Path
from typing import Optional, Dict, List

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
            model="gpt-4-vision-preview",
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

    # Create mappings for tables and images
    table_mapping: Dict[str, str] = {}
    image_mapping: Dict[str, Dict[str, str]] = {}

    # Export tables to CSV and create mapping
    for table_ix, table in enumerate(result.document.tables):
        table_df = table.export_to_dataframe()
        csv_path = output_dir / f"{doc_filename}-table-{table_ix + 1}.csv"
        _log.info(f"Saving table {table_ix + 1} to {csv_path}")
        table_df.to_csv(csv_path)
        table_mapping[table.self_ref] = f"{doc_filename}-table-{table_ix + 1}.csv"

    # Export images and get VLM analysis
    picture_counter = 0
    for element, _level in result.document.iterate_items():
        if isinstance(element, PictureItem):
            picture_counter += 1
            # Save image using get_image() method
            img_path = output_dir / f"{doc_filename}-picture-{picture_counter}.png"
            with img_path.open("wb") as fp:
                element.get_image(result.document).save(fp, "PNG")
            
            # Get VLM analysis
            if element.annotations:
                description = element.annotations[0].text if element.annotations else "No description available"
                _log.info(f"Image {element.self_ref} analysis: {description}")
            else:
                description = "No description available"
            
            image_mapping[element.self_ref] = {
                "path": f"{doc_filename}-picture-{picture_counter}.png",
                "description": description
            }

    # Export comprehensive markdown with content in correct positions
    markdown_path = output_dir / f"{doc_filename}.md"
    with markdown_path.open("w") as f:
        # Write document metadata
        f.write(f"# {doc_filename}\n\n")
        f.write(f"Processing time: {end_time:.2f} seconds\n\n")
        
        # Process document content and replace placeholders
        content = result.document.export_to_markdown()
        
        # Replace table placeholders with actual table content
        for table_ref, csv_path in table_mapping.items():
            table_df = pd.read_csv(output_dir / csv_path)
            table_md = table_df.to_markdown(index=False)
            content = content.replace(f"<!-- table {table_ref} -->", table_md)
        
        # Replace image placeholders with actual images and descriptions
        for img_ref, img_data in image_mapping.items():
            img_markdown = f"![{img_ref}]({img_data['path']})\n\n**Description:** {img_data['description']}\n\n"
            content = content.replace(f"<!-- image {img_ref} -->", img_markdown)
        
        f.write(content)

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