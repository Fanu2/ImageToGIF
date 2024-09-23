from PIL import Image, ImageDraw, ImageFont
import imageio
import os

# Function to create GIF
def create_gif(image_folder, text, output_gif):
    images = []
    font = ImageFont.load_default()  # You can load a TTF font if desired

    for filename in os.listdir(image_folder):
        if filename.endswith('.png') or filename.endswith('.jpg'):
            img_path = os.path.join(image_folder, filename)
            img = Image.open(img_path)

            # Draw text on the image
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), text, fill="white", font=font)

            # Append the modified image to the list
            images.append(img)

    # Save the images as a GIF
    images[0].save(output_gif, save_all=True, append_images=images[1:], duration=500, loop=0)

# Usage
image_folder = '/home/jasvir/gif.js/python/images/'  # Change this to your images folder
text = 'Love my Jodha'  # Change this to the text you want to add
output_gif = '/home/jasvir/gif.js/python/images/output.gif'  # Name of the output GIF

create_gif(image_folder, text, output_gif)
print(f"GIF saved as {output_gif}")
