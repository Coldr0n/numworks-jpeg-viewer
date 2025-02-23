from PIL import Image
from io import BytesIO
from os import path

def encode_image(image_path: str,
                 output_filepath: str,
                 max_kb_buffer_size: float = 15.0,
                 max_kb_file_size: float = 30.0,
                 strech: bool = False,
                 show_image: bool = False) -> None:
    """
    This function takes an image and either strech it or adds black bars to fit into the numworks viewport.
    It will then compress the image to a jpeg file and adjust the quality to meet the appropriate buffer and file size.
    The resulting bytes are then written as bytes() into the output file.
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
        
        quality = 95
        while quality > 0:
            output = BytesIO()
            out_img.save(output, format="JPEG", quality=quality, optimize=True)
            
            buffer_size_kb = output.tell() / 1024 # Convert bytes to kb
            if buffer_size_kb < max_kb_buffer_size:
                with open(output_filepath, "w") as out_file:
                    out_file.write(f"b={output.getvalue()}")
                    
                file_size_kb = path.getsize(output_filepath) / 1024
                if file_size_kb < max_kb_file_size: break

            quality -= 5

        print(f"Image saved successfully at [{output_filepath}]\nQuality: {quality}, buffer size: {buffer_size_kb:.2f}KB; file size: {file_size_kb:.2f}KB")
        if show_image: Image.open(output).show()

if __name__ == '__main__':
    encode_image("images/photo.jpg", "photo.py")