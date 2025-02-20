from PIL import Image
from io import BytesIO

def create_jpeg_pyfile(image_path: str, output_file_name: str) -> bytes:
    """
    This function takes an image path and scale it to the numworks viewport size.
    It then convert and compress the image into a jpeg file and write the image's byte into a python file.
    Returns the bytes saved.
    """
    NUMWORKS_SIZE = 320, 222
    with Image.open(image_path) as img:
        img = img.crop(img.getbbox()) # Crop the image to the actual bounding box

        # Rescale the image so it fits into the calculator but keep the aspect ratio
        scale_factor = min(NUMWORKS_SIZE[1] / img.height, 1) # Take the minimum to not upscale the image
        img = img.convert("RGB").resize((round(img.width * scale_factor),
                                         round(img.height * scale_factor)))
        
        img = img.resize(NUMWORKS_SIZE)
        
        output = BytesIO()
        img.save(output, "Jpeg",
                 quality=50,
                 optimize=True)
        
        #print(output.tell())
        #Image.open(output).show()
        
        with open(output_file_name, "w") as out_file:
            out_file.write("buffer = " + str(output.getvalue()))

create_jpeg_pyfile("images/sunset.png", "out.py")