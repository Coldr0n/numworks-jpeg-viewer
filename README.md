# Numworks jpeg viewer
Numworks jpeg viewer is a python script that runs on the [numworks](https://www.numworks.com/) and allows to display full 320x222 rgb images.  
It decodes a jpeg file encoded as [bytes](https://docs.python.org/3/library/stdtypes.html#bytes) into a python file and renders the output with the [kandinsky](https://pypi.org/project/kandinsky/) package.  
The decoder was made for lossy jpeg and does not support lossless compression.

## Installation

### Installing python
To use the viewer you first have to have python installed on your computer. You can dowload the latest version of python here: https://www.python.org/downloads/ 

### Installing the python package
You can use pip to install [numworks jpeg viewer](https://pypi.org/project/numworks-jpeg-viewer) on your pc to encode and preview the images that you want, run the following command on a terminal.
```bash
pip install numworks-jpeg-viewer
```

### Sending the script to the numworks
To send the jpeg viewer script to your numworks you can go to https://my.numworks.com/python/martin-garel-528/jpeg_viewer  
or https://my.numworks.com/python/martin-garel-528/jpeg_viewer_min (smaller version of the script so it takes less space on your calculator).

## Usage
### Encoding an image
To use the viewer you first have to encode an image as jpeg into a python file. To do that you can run the `image_encoder.py` file with various parameters to choose where and how do you want to encode an image.
```bash
python3 -m numworks_viewer.image_encoder [options] [image_path] [output_path]
```
#### Options
For the maximum buffer and file size paramters, the program will reduce the quality of the jpeg image until they are under the provided sizes.
- `-bs`, `--max_kb_buffer_size` (15KB by default): Desired size for the image data, it mostly depend on the RAM of the numworks.
- `-fs`, `--max_kb_file_size` (30KB by default): Desired size for the python file containing the data, it is how much space the image will take on the numworks.
- `-s`, `--strech`: If this flag is present, the output image will be streched to take the entire space on the numworks. Otherwise the image will be scaled down and the aspect ratio will be preserved.
- `-o`, `--open_image`: If this flag is present, it will open the output image.

#### Example
```bash
python3 -m numworks_viewer.image_encoder -bs=10 -fs=25 -s -o images/my_image.png my_image.py
```
You can also use the `encode_image` function from the module in a python file (the parameters of the function are the same as listed before).
```python
from numworks_viewer.image_encoder import encode_image
encode_image("path/to/your/image.png", "path/to/the/output.py")
```

### Viewing the image on the numworks
Once the image is compressed into a python file, you have to send it to your calculator.  
First, make your own numworks script with the python image file copied into it, and send it to your calculator (see [this page](https://www.numworks.com/support/connect/script/) if you struggle).  
Then, to see the image, import the `jpeg_viewer.py` and your image into the numworks python shell and use the `open` function with the variable containing the bytes (`b`):  
![screenshot](https://github.com/user-attachments/assets/b22b8fae-b01e-4aa8-adaf-f30757d2e242)
### Viewing the image on your pc
On pc, you can also import the two python modules on a python interpreter or use this command:
```bash
python3 -m numworks_viewer.viewer [module_name]
```
`[module_name]` is the name of the python file where the image data is located. It is imported in python with the `__import__` function so paths will not work.

## Script Performance
Because python is pretty slow, this script takes arount 5 to 10 minutes to display an entire image to the screen. I tried my best to optimize as much the code and I think that is it a pretty good time (it was around 45 minutes at first).

## Memory Limitations
While the numworks has a pretty limited RAM size, it isn't really what's limiting the images to be bigger. One issue is that the images have to be encoded directely in a text file as characters and not in binary, and the script size is what takes most of the space in a numworks calculator.  
Still, even if you have a numworks with good storage, the image can be too big to load into memory and the program might crash, so you have to take this into account when choosing parameters when encoding the image.

## Contributing and Support
I am opened to any contributions or any questions you might have, and I will be pleased to answer them.

## License
[MIT](https://choosealicense.com/licenses/mit/)
