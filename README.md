# Numworks jpeg viewer
Numworks jpeg viewer is a python script that runs on the [numworks](https://www.numworks.com/) and allows to display full 320x222 rgb images.  
It decodes a jpeg file encoded as [bytes](https://docs.python.org/3/library/stdtypes.html#bytes) into a python file and renders the output with the [kandinsky](https://pypi.org/project/kandinsky/) package.  
The decoder was made for lossy jpeg and does not support lossless compression.

## Installation
You can use [pip](https://pip.pypa.io/en/stable/) to install numworks jpeg viewer with utility scripts to encode images.
```bash
pip install numworks_jpeg_viewer
```
To send the script to your numworks you can go to https://my.numworks.com/python/martin-garel-528/jpeg_viewer  
or https://my.numworks.com/python/martin-garel-528/jpeg_viewer_min to get a smaller version of the script so it takes less space on your calculator.

## Usage
To use the viewer you first have to encode any image as jpeg into a python file. To do that you can run the following command and follow the instructions,
```bash
python3 -m numworks_jpeg_viewer.image_encoder
```
Or use the module in a python file (see documentation for more info on the parameters of `encode_image`)
```python
from numworks_jpeg_viewer.image_encoder import encode_image
encode_image("path/to/your/image.png", "path/to/the/output.py")
```
Once the image is compressed into a python file, you have to send it to your calculator.  
To do that make your own numworks script with the python image file copied into it, and send it to your calculator (see [this page](https://www.numworks.com/support/connect/script/) if you struggle).  
If you want to actually see the image, import the `jpeg_viewer.py` and your image into the numworks python shell and use the `open` function with the variable containing the bytes (`b`):  
![screenshot](https://github.com/user-attachments/assets/b22b8fae-b01e-4aa8-adaf-f30757d2e242)  
On pc, you can do the same in the interpreter or directely run the `viewer.py` file and follow the instructions.
```bash
python3 -m numworks_jpeg_viewer.viewer
```

## Script Performance
Because python is pretty slow, this script takes arount 5 to 10 minutes to display an entire image to the screen. I tried my best to optimize as much the code and I think that is it a pretty good time (it was around 45 minutes at first).

## Memory Limitations
While the numworks has a pretty limited RAM size, it isn't really what's limiting the images to be bigger. One issue is that the images have to be encoded directely in a text file as characters and not in binary, and the script size is what takes most of the space in a numworks calculator.  
Still, even if you have a numworks with good storage, the image can be too big to load into memory and the program might crash, so you have to take this into account when choosing parameters when encoding the image.

## Contributing and Support
I am opened to any contributions or any questions you might have, and I will be pleased to answer them.

## License
[MIT](https://choosealicense.com/licenses/mit/)
