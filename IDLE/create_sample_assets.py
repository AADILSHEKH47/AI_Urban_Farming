"""
Generates high quality synthetic leaf sample images for offline demonstration
and testing of the AI Urban Farming Assistant.
"""

import os
from PIL import Image, ImageDraw

def generate_samples():
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    os.makedirs(samples_dir, exist_ok=True)
    
    # 1. Tomato Early Blight Sample Leaf Image
    img_blight = Image.new("RGB", (400, 400), color=(240, 245, 240))
    draw = ImageDraw.Draw(img_blight)
    
    # Draw leaf silhouette (rich green)
    draw.polygon([
        (200, 40), (280, 110), (330, 200), (310, 290),
        (260, 350), (200, 370), (140, 350), (90, 290),
        (70, 200), (120, 110)
    ], fill=(46, 125, 50), outline=(27, 94, 32), width=3)
    
    # Draw leaf central vein
    draw.line([(200, 60), (200, 360)], fill=(129, 199, 132), width=4)
    draw.line([(200, 140), (270, 110)], fill=(129, 199, 132), width=2)
    draw.line([(200, 140), (130, 110)], fill=(129, 199, 132), width=2)
    draw.line([(200, 210), (290, 190)], fill=(129, 199, 132), width=2)
    draw.line([(200, 210), (110, 190)], fill=(129, 199, 132), width=2)
    draw.line([(200, 280), (270, 270)], fill=(129, 199, 132), width=2)
    draw.line([(200, 280), (130, 270)], fill=(129, 199, 132), width=2)
    
    # Draw Early Blight concentric circular lesions with yellow halos
    # Lesion 1 (Lower right)
    draw.ellipse([(220, 240), (270, 290)], fill=(255, 235, 59)) # Yellow halo
    draw.ellipse([(228, 248), (262, 282)], fill=(109, 76, 65))  # Dark brown necrotic center
    draw.ellipse([(234, 254), (256, 276)], fill=(62, 39, 35))   # Concentric target ring
    
    # Lesion 2 (Lower left)
    draw.ellipse([(120, 260), (165, 305)], fill=(255, 235, 59)) # Yellow halo
    draw.ellipse([(127, 267), (158, 298)], fill=(93, 64, 55))   # Brown lesion
    
    # Lesion 3 (Mid right)
    draw.ellipse([(250, 170), (285, 205)], fill=(255, 235, 59))
    draw.ellipse([(256, 176), (279, 199)], fill=(78, 52, 46))
    
    # Stem
    draw.line([(200, 370), (200, 395)], fill=(51, 105, 30), width=6)
    
    blight_path = os.path.join(samples_dir, "sample_tomato_early_blight.png")
    img_blight.save(blight_path)
    
    # 2. Healthy Tomato Sample Leaf
    img_healthy = Image.new("RGB", (400, 400), color=(240, 245, 240))
    draw_h = ImageDraw.Draw(img_healthy)
    
    draw_h.polygon([
        (200, 40), (280, 110), (330, 200), (310, 290),
        (260, 350), (200, 370), (140, 350), (90, 290),
        (70, 200), (120, 110)
    ], fill=(46, 125, 50), outline=(27, 94, 32), width=3)
    
    draw_h.line([(200, 60), (200, 360)], fill=(129, 199, 132), width=4)
    draw_h.line([(200, 140), (270, 110)], fill=(129, 199, 132), width=2)
    draw_h.line([(200, 140), (130, 110)], fill=(129, 199, 132), width=2)
    draw_h.line([(200, 210), (290, 190)], fill=(129, 199, 132), width=2)
    draw_h.line([(200, 210), (110, 190)], fill=(129, 199, 132), width=2)
    draw_h.line([(200, 280), (270, 270)], fill=(129, 199, 132), width=2)
    draw_h.line([(200, 280), (130, 270)], fill=(129, 199, 132), width=2)
    draw_h.line([(200, 370), (200, 395)], fill=(51, 105, 30), width=6)
    
    healthy_path = os.path.join(samples_dir, "sample_tomato_healthy.png")
    img_healthy.save(healthy_path)
    
    # 3. Non-plant / Unidentifiable Sample Image (for testing error handling)
    img_non_plant = Image.new("RGB", (400, 400), color=(220, 230, 242))
    draw_np = ImageDraw.Draw(img_non_plant)
    # Draw blue geometric shapes with no plant/chlorophyll features
    draw_np.rectangle([(50, 50), (350, 350)], fill=(33, 150, 243), outline=(13, 71, 161), width=4)
    draw_np.ellipse([(100, 100), (300, 300)], fill=(255, 255, 255), outline=(30, 136, 229), width=3)
    draw_np.rectangle([(160, 160), (240, 240)], fill=(244, 67, 54))
    
    non_plant_path = os.path.join(samples_dir, "sample_non_plant.png")
    img_non_plant.save(non_plant_path)
    
    return blight_path, healthy_path, non_plant_path

if __name__ == "__main__":
    generate_samples()

