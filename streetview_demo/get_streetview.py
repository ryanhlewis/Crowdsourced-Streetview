import subprocess
import os
import hashlib
import time
import requests
import shlex  # For safely quoting arguments
import zlib  # For crc32 calculations

def resize_equi(path_src, path_dst, width):
    height = width // 2
    subprocess.run(["magick", "convert", path_src, "-resize", f"{width}x{height}", "-quality", "100", path_dst], check=True)

def get_id_from_url(url):
    fields = url.split("!1s")
    fields2 = fields[1].split("!")
    return fields2[0]

def extract_lat_lng_from_url(url):
    # Extract latitude and longitude from the provided Google Maps URL
    parts = url.split('@')[1].split(',')
    lat, lng = parts[0], parts[1]
    return lat, lng

def add_exif_equi(path, width):
    height = width // 2
    subprocess.run(["exiftool", "-overwrite_original", "-UsePanoramaViewer=True", "-ProjectionType=equirectangular", "-PoseHeadingDegrees=180.0", "-CroppedAreaLeftPixels=0", "-FullPanoWidthPixels={}".format(width), "-CroppedAreaImageHeightPixels={}".format(height), "-FullPanoHeightPixels={}".format(height), "-CroppedAreaImageWidthPixels={}".format(width), "-CroppedAreaTopPixels=0", "-LargestValidInteriorRectLeft=0", "-LargestValidInteriorRectTop=0", "-LargestValidInteriorRectWidth={}".format(width), "-LargestValidInteriorRectHeight={}".format(height), "-Model=github fdd4s streetview-dl", path], check=True)

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

class OpSt:
    def __init__(self, id, latlng):
        self.op_id = OpId(id)
        self.op_url_list = OpUrlList()
        self.latlng = latlng.replace(",", "_")  # Replace comma with underscore for folder naming
        self.export_dir = f"3export{self.latlng}"
        ensure_dir(self.export_dir)

    def download(self):
        # Check if the directory already has images; if so, skip downloading
        if os.listdir(self.export_dir):
            print("Images already downloaded, skipping...")
        else:
            print("Downloading...")
            self.make_img_list()
            self.op_url_list.download_aria2c()

        print("Montage...")
        self.make_montage()
        print("Cleaning temp files...")
        self.op_url_list.remove_files()


    def make_img_list(self):
        self.op_url_list.clear()
        x_ini, x_fin = 0, 6
        y_ini, y_fin = 0, 3
        num_file = 1
        codigo = self.op_id.get_id_src()
        id = self.op_id.get_id_op()

        for y_act in range(y_ini, y_fin + 1):
            for x_act in range(x_ini, x_fin + 1):
                url = f"https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=maps_sv.tactile&panoid={codigo}&x={x_act}&y={y_act}&zoom=3&nbt=1&fover=2"
                file = f"3export{self.latlng}/tile_x{x_act}_y{y_act}.jpg"
                self.op_url_list.add_url(url, file)


    def make_montage(self):
        print("Creating montage...")
        id = self.op_id.get_id_op()
        file_list_data = ""

        # Generating the list of images to include in the montage, ensuring files exist.
        for y in range(13):  # Assuming y goes from 0 to 12
            for x in range(26):  # Assuming x goes from 0 to 25
                tile_name = f"tile_x{x}_y{y}.jpg"
                tile_path = os.path.join(self.export_dir, tile_name)
                if os.path.exists(tile_path):
                    file_list_data += tile_path + "\n"

        # Writing the list of image files to a text file
        file_list_path = os.path.join(self.export_dir, f"tmp-fl{id}.txt")
        with open(file_list_path, 'w') as file:
            file.write(file_list_data)

        # The output image path
        output_path = os.path.join(self.export_dir, f"full{self.latlng}.jpg")

        # Constructing the montage command with the correct paths
        montage_cmd = [
            "montage",
            "-tile", "7x3",
            "-geometry", "512x512+0+0",
            "-quality", "100",
            "@" + file_list_path,  # The '@' indicates to read filenames from the file
            output_path
        ]

        # Running the montage command
        try:
            subprocess.run(montage_cmd, check=True)
            print("Montage created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while creating the montage: {e}")
        finally:
            print("Cleaning up...")
            if os.path.exists(file_list_path):
                os.unlink(file_list_path)



class OpUrlList:
    def __init__(self):
        self.url_list = []

    def clear(self):
        self.url_list.clear()

    def add_url(self, url, file):
        self.url_list.append((url, file))

    def download_aria2c(self):
        path = self.make_tmp_path() + ".txt"
        with open(path, 'w') as file:
            file.write(self.make_aria2c_list())
            print(self.make_aria2c_list())
        subprocess.run(["aria2c", "-i", path], check=True)
        os.unlink(path)

    def make_aria2c_list(self):
        return '\n'.join([f"{item[0]}\n out={item[1]}" for item in self.url_list])

    def make_tmp_path(self):
        return os.path.join(os.getcwd(), "tmp-" + hashlib.new('ripemd160', str(time.time()).encode() + str(os.urandom(16)).encode()).hexdigest())

    def remove_files(self):
        for item in self.url_list:
            try:
                os.unlink(item[1])
            except FileNotFoundError:
                pass  # File might have been moved or deleted manually

class OpId:
    def __init__(self, id):
        self.id_src = id
        self.id_op = self.make_id(id)

    def make_id(self, id):
        id_hash = hashlib.new('ripemd160', id.encode()).hexdigest()
        id_crc = format(zlib.crc32(id_hash.encode()) & 0xFFFFFFFF, 'x')
        return "op" + id_hash + id_crc

    def get_id_src(self):
        return self.id_src

    def get_id_op(self):
        return self.id_op

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Syntax: python ./streetview_dl.py '<url>'\nRemember to put the URL between single quotes")
        sys.exit(0)

    url = sys.argv[1]
    lat, lng = extract_lat_lng_from_url(url)
    latlng = f"{lat},{lng}"

    if "/" in url:
        id = get_id_from_url(url)

    if len(id) < 10 or len(id) > 30:
        print("wrong id")
        sys.exit(0)

    op_st = OpSt(id, latlng)
    op_st.download()

    formatted_latlng = latlng.replace(",", "_")

    name = f"full{formatted_latlng}-0.jpg"

    # Match and overlay
    from image_match_overlay import match_and_overlay

    # Assuming you have the paths set up
    panorama_image_path = f"./3export{formatted_latlng}/{name}"

    # Fetch the first social media post (image) from ./social folder
    social_media_images = [img for img in os.listdir('./social') if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if social_media_images:
        social_media_image_path = os.path.join('./social', social_media_images[0])
        # Proceed with the matching algorithm
    else:
        print("No social media images found.")


    output_path = f"./3export{formatted_latlng}/output.jpg"

    # Perform match and overlay
    match_and_overlay(social_media_image_path, panorama_image_path, output_path)

    # Get social media posts from ./social
    from deconstruct import deconstruct_panorama

    # def deconstruct_panorama(pano_path, output_dir,
    deconstruct_panorama(output_path, f"./3export{formatted_latlng}")

    print(" okay ")
    # Additional steps for resizing and adding EXIF tags can follow here, using the updated naming and directory structure
