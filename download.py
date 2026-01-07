from huggingface_hub import hf_hub_download

save_dir = "/home/usr/path-where-you-want-the-model-to-be-saved"

model_path = hf_hub_download(
    repo_id="hugging-quants/Llama-3.2-3B-Instruct-Q4_K_M-GGUF",
    filename="llama-3.2-3b-instruct-q4_k_m.gguf",
    local_dir=save_dir
)

print(f"Model saved to: {model_path}")