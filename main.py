from PIL import Image
from io import BytesIO

NUMWORKS_SIZE = 320, 222

def create_webp_pyfile(filepath: str, output_file_name: str) -> bytes:
    """
    This function takes an image path and scale it to the numworks viewport size. It then saves the data as a byte string into a python file
    Returns the bytes saved
    """
    with Image.open(filepath) as img:
        img = img.crop(img.getbbox()) # Crop the image to the actual bounding box

        # Rescale the image so it fits into the calculator but keep the aspect ratio
        scale_factor = min(NUMWORKS_SIZE[1] / img.height, 1) # Take the minimum to not upscale the image
        img = img.convert("RGB").resize((round(img.width * scale_factor),
                                            round(img.height * scale_factor)))
        
        img = img.resize(NUMWORKS_SIZE)
        
        output = BytesIO()
        img.save(output, "WebP",
                 lossless=False,
                 quality=20,
                 alpha_quality=0,
                 method=6)
        
        with open(output_file_name, "w") as out_file:
            out_file.write("buffer = " + str(output.getvalue()))

img_bytes = create_webp_pyfile("images/python.png", "out.py")
from out import buffer

print(buffer)