# attention_viz.py — visualise attention weights on real text using BertViz
from transformers import AutoTokenizer, AutoModel
from bertviz import head_view, model_view
import torch
import os

def main():
    print("--- Running BertViz Attention Visualiser ---")
    
    model_name = "bert-base-uncased"
    print(f"Loading tokenizer and model: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name, output_attentions=True)
    
    # Example sentences for testing different attention patterns
    # 1. Coreference / Winograd Schema
    sentence_a = "The trophy did not fit in the suitcase because it was too large."
    
    # Tokenize and compute attention weights
    print("Computing attention matrices...")
    inputs = tokenizer(sentence_a, return_tensors="pt", add_special_tokens=True)
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    
    with torch.no_grad():
        outputs = model(**inputs)
        
    # attention is a tuple of 12 tensors, each of shape (batch, heads, seq_len, seq_len)
    attention = outputs.attentions
    
    # Generate interactive HTML representations
    print("Generating Head View visualization...")
    head_view_html = head_view(attention, tokens, html_action='return')
    
    print("Generating Model View visualization...")
    model_view_html = model_view(attention, tokens, html_action='return')
    
    # Save visualizations to files
    head_file = "head_view.html"
    model_file = "model_view.html"
    
    with open(head_file, "w", encoding="utf-8") as f:
        f.write(head_view_html.data)
    print(f"✓ Saved head view to: {os.path.abspath(head_file)}")
    
    with open(model_file, "w", encoding="utf-8") as f:
        f.write(model_view_html.data)
    print(f"✓ Saved model view to: {os.path.abspath(model_file)}")
    
    print("\nLinguistic patterns to observe when opening the HTML files in a browser:")
    print("  - Early layers (0-3): Positional (look for diagonals where tokens attend to neighbors).")
    print("  - Middle layers (4-8): Syntactic (look for nouns attending to verbs).")
    print("  - Late layers (9-12): Coreference (inspect the word 'it' attending strongly to 'trophy').")
    print("--- Done ---")

if __name__ == "__main__":
    main()
