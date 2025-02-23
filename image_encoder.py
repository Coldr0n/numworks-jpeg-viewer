from PIL import Image
from io import BytesIO

def create_jpeg_pyfile(image_path: str, output_file_name: str, strech: bool = False) -> bytes:
    """
    This function takes an image path and scale it to the numworks viewport size.
    It then convert and compress the image into a jpeg file and write the image's byte into a python file.
    Returns the bytes saved.
    """
    NUMWORKS_SIZE = 320, 222
    with Image.open(image_path) as img:
        img = img.crop(img.getbbox()).convert("RGB") # Crop the image to the actual bounding box

        if strech: out_img = img.resize(NUMWORKS_SIZE)
        else: # Scale down the image to fit the numworks and add borders to it
            aspect_ratio = img.width / img.height
            if NUMWORKS_SIZE[0] / NUMWORKS_SIZE[1] > aspect_ratio:
                # Fit to height
                new_height = NUMWORKS_SIZE[1]
                new_width = int(aspect_ratio * new_height)
            else:
                # Fit to width
                new_width = NUMWORKS_SIZE[0]
                new_height = int(new_width / aspect_ratio)
            
            img = img.resize((new_width, new_height))
            
            # Create a blank image with the size of the numworks
            out_img = Image.new("RGB", NUMWORKS_SIZE, (0, 0, 0))

            # Paste the resized img onto the blank image at the center
            out_img.paste(img, ((NUMWORKS_SIZE[0] - new_width) // 2,
                                    (NUMWORKS_SIZE[1] - new_height) // 2))
        
        MAX_KB_BUFFER_SIZE = 6.5
        quality = 95
        while quality > 0:
            output = BytesIO()
            out_img.save(output, format="JPEG", quality=quality, optimize=True)
            
            file_size_kb = output.tell() / 1024 # Convert bytes to kb
            if file_size_kb < MAX_KB_BUFFER_SIZE: break

            quality -= 5
        else: print(f"Warning! file size might exceed {MAX_KB_BUFFER_SIZE}KB.")
        
        with open(output_file_name, "w") as out_file:
            out_file.write("buffer = " + str(output.getvalue()))
            print(f"Image saved successfully at [{output_file_name}]\nQuality: {quality}, size: {file_size_kb:.2f}KB")

create_jpeg_pyfile("images/rabelais.jpg", "out.py")