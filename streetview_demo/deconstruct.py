from PIL import Image
import os 

def deconstruct_panorama(pano_path, output_dir, x_ini=0, x_fin=6, y_ini=0, y_fin=2, tile_size=512):
    """
    Deconstructs a stitched panorama back into its original tiles.
    
    Args:
    - pano_path: Path to the panoramic image.
    - output_dir: Directory to save the deconstructed tiles.
    - x_ini, x_fin, y_ini, y_fin: Tile indices defining the grid.
    - tile_size: The size of each tile in pixels (assuming square tiles).
    """
    # Load the panoramic image
    pano_image = Image.open(pano_path)
    pano_width, pano_height = pano_image.size
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate the expected width and height of each tile
    expected_width = tile_size
    expected_height = tile_size
    
    # Iterate over the grid of tiles
    for y in range(y_ini, y_fin + 1):
        for x in range(x_ini, x_fin + 1):
            # Calculate the pixel coordinates of the tile's top-left corner
            left = x * expected_width
            upper = y * expected_height
            # Ensure the tile does not exceed the panorama's dimensions
            right = min(left + expected_width, pano_width)
            lower = min(upper + expected_height, pano_height)
            
            # Crop the tile from the panorama
            tile = pano_image.crop((left, upper, right, lower))
            
            # Save the tile
            tile_path = os.path.join(output_dir, f"tile_x{x}_y{y}.jpg")
            tile.save(tile_path)
            print(f"Saved tile: {tile_path}")

