import fitz  # PyMuPDF
import base64
from openai import OpenAI
import json
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Token-to-USD conversion rates by model
MODEL_COSTS = {
    "gpt-4.1": 0.0005,        # $0.50 per 1K input tokens
    "gpt-4.1-mini": 0.0001,   # $0.10 per 1K input tokens
    "gpt-4.1-nano": 0.000025  # $0.025 per 1K input tokens
}

def convert_page_to_image(pdf_path, page_num):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    pix = page.get_pixmap()
    img_data = pix.tobytes("png")
    encoded_image = base64.b64encode(img_data).decode("utf-8")
    return encoded_image, pix.width, pix.height

def calculate_image_tokens(width, height):
    patch_size = 32
    width_patches = (width + patch_size - 1) // patch_size
    height_patches = (height + patch_size - 1) // patch_size
    total_patches = width_patches * height_patches
    return min(total_patches, 1536)

def calculate_cost(tokens, model_name):
    rate = MODEL_COSTS.get(model_name, 0.0005)  # Default to gpt-4.1 if unknown
    return round((tokens / 1000) * rate, 6)

def extract_text_from_image(encoded_image, page_num, filename, model="gpt-4.1", detail="high", width=1024, height=1024):
    prompt = """
You are given an image of a single PDF document page. Extract its textual content in clean, structured Markdown format suitable for indexing and embedding into a RAG system.

- Follow the reading order as naturally presented in the page.
- Use proper Markdown syntax for all sections: headings, subheadings, body text, bullet points, numbered lists, etc.
- Detect and extract **all tables**, even if they are embedded within text or mixed with other content. Convert them into valid **CSV format**, and enclose each table in a fenced block marked with ```csv```.
- Ensure merged or multi-row/column cells are flattened in a readable, linear CSV structure.
- If the page contains any **visual elements** (e.g. charts, images, diagrams), briefly describe them **in their actual location in the text**, using fenced blocks labeled ```Visual Description```.
- Do **not** wrap the entire output in a ```markdown``` block. Only tables and visual descriptions should use fenced blocks.
- Do **not** generate layout metadata, visual positions, or bounding-box outputs.
- Ensure consistent, deterministic structure across identical inputs for reliable indexing.
"""

    response = client.responses.create(
        model=model,
        temperature=0.0,
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:image/png;base64,{encoded_image}", "detail": detail}
            ]
        }]
    )

    total_tokens = response.usage.total_tokens
    image_tokens = calculate_image_tokens(width, height)

    # adjust image token multiplier based on model
    if model == "gpt-4.1-mini":
        image_tokens = int(image_tokens * 1.62)
    elif model == "gpt-4.1-nano":
        image_tokens = int(image_tokens * 2.46)

    # estimate $ cost based on input tokens only (image token based)
    dollar_cost = calculate_cost(image_tokens, model)

    return {
        "filename": filename,
        "page_number": page_num + 1,
        "content": response.output_text,
        "response_id": response.id,
        "tokens_used": total_tokens,
        "image_tokens_estimated": image_tokens,
        "usd_estimated": dollar_cost
    }

def pdf_to_markdown(pdf_path, model="gpt-4.1", detail="high"):
    doc = fitz.open(pdf_path)
    results = []

    for page_num in range(len(doc)):
        print(f"Processing page {page_num + 1}/{len(doc)}...")
        encoded_image, width, height = convert_page_to_image(pdf_path, page_num)
        page_data = extract_text_from_image(encoded_image, page_num, os.path.basename(pdf_path), model, detail, width, height)
        results.append(page_data)

    output_path = f"{os.path.splitext(pdf_path)[0]}_output_{model}_{detail}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Completed. Output saved to {output_path}")

if __name__ == "__main__":
    pdf_path = "data/test_FIDIC Red Book Rev02 - SODIC East –  SF09 - Core and Shell Package  -Rev.03_(MALAK).pdf"  # Replace with your PDF file path
    pdf_to_markdown(pdf_path, model="gpt-4.1", detail="high")
