from src.visualization.image_generator import generate_image


prompt = """
A modern minimalist living room with warm neutral colors,
soft natural lighting, curved furniture, tactile fabrics,
warm wood accents, and a calm premium interior design.
"""


image_path = generate_image(
    prompt,
    "test_minimalist_room.webp"
)

print("Generated image:", image_path)