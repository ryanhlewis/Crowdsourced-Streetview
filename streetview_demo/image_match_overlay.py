import cv2
import numpy as np
from PIL import Image

def match_and_overlay(image_path1, image_path2, output_path):
    """
    Matches two images using SIFT and overlays them.

    Args:
    - image_path1: Path to the first image.
    - image_path2: Path to the second image.
    - output_path: Path where the overlay image should be saved.
    """
    # Load images and convert to RGB
    image1 = Image.open(image_path1).convert('RGB')
    image2 = Image.open(image_path2).convert('RGB')
    
    # Convert PIL images to numpy arrays
    image1_np = np.array(image1)
    image2_np = np.array(image2)

    # Initialize the SIFT detector
    sift = cv2.SIFT_create()

    # Find keypoints and descriptors with SIFT
    keypoints1, descriptors1 = sift.detectAndCompute(cv2.cvtColor(image1_np, cv2.COLOR_RGB2GRAY), None)
    keypoints2, descriptors2 = sift.detectAndCompute(cv2.cvtColor(image2_np, cv2.COLOR_RGB2GRAY), None)

    # Initialize FLANN matcher
    index_params = dict(algorithm=1, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    # Perform KNN matching
    matches = flann.knnMatch(descriptors1, descriptors2, k=2)

    # Apply ratio test to filter matches
    good_matches = [m for m, n in matches if m.distance < 0.75 * n.distance]

    # Extract the coordinates of the matched keypoints
    src_pts = np.float32([keypoints1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # Compute the homography matrix
    H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    # Warp image1 to align with image2
    height, width, _ = image2_np.shape
    aligned_image1 = cv2.warpPerspective(image1_np, H, (width, height))

    # Create a mask to identify non-black regions in the aligned image
    mask = np.all(aligned_image1 != [0, 0, 0], axis=-1)

    # Initialize an image to store the overlay
    overlay_image = np.copy(image2_np)

    # Overlay the aligned image on top of the original image
    overlay_image[mask] = aligned_image1[mask]

    # Convert the final numpy array back to a PIL image and save
    overlay_image_pil = Image.fromarray(overlay_image.astype('uint8'), 'RGB')
    overlay_image_pil.save(output_path)

    print(f"Overlay image saved to {output_path}")
