import os
import shutil
from pathlib import Path

from gradio_client import Client


# ==========================================
# Hugging Face Image Generator
# ==========================================

HF_SPACE = "joshikeshav9977/aroha-image-generator"

client = Client(HF_SPACE)


# ==========================================
# Generate Image
# ==========================================

def generate_image(
    prompt: str,
    filename: str = "generated_image.webp"
):
    """
    Generate an image using the AROHA
    Hugging Face FLUX image-generation Space
    and save it inside the AROHA project.
    """

    if not prompt:
        raise ValueError("Image prompt cannot be empty.")

    # Generate image through Hugging Face
    result = client.predict(
        prompt=prompt,
        api_name="/generate_image"
    )

    # Always save relative to the AROHA project, not the shell's current directory.
    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "generated_images"
    output_dir = output_dir.resolve()

    output_dir.mkdir(parents=True, exist_ok=True)

    # Final image path
    output_path = output_dir / filename

    # Copy image from temporary Gradio location
    # Gradio normally returns a temporary local filepath.
    # Keep the guard explicit so failures are reported clearly by the API.
    if isinstance(result, (list, tuple)) and result:
        result = result[0]

    if isinstance(result, dict):
        result = result.get("path") or result.get("url")

    if not result:
        raise RuntimeError("FLUX returned no image file path.")

    if str(result).startswith(("http://", "https://")):
        raise RuntimeError(
            "FLUX returned a remote image URL instead of a local file path."
        )

    if not os.path.isfile(result):
        raise RuntimeError(f"FLUX image file was not found: {result}")

    shutil.copy2(str(result), str(output_path))

    return str(output_path)