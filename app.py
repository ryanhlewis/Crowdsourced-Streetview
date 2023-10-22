from flask import Flask, request, send_file, render_template
import cv2
import numpy as np
from PIL import Image
from io import BytesIO


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/overlay', methods=['POST'])
def overlay_images():
    print("Processing")
    # Get the uploaded images
    image1 = Image.open(request.files['image1']).convert('RGB')
    image2 = Image.open(request.files['image2']).convert('RGB')
    
    # Convert PIL images to numpy arrays
    image1 = np.array(image1)
    image2 = np.array(image2)

    # Initialize the SIFT detector
    sift = cv2.SIFT_create()

    # Find keypoints and descriptors for both images
    keypoints1, descriptors1 = sift.detectAndCompute(cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY), None)
    keypoints2, descriptors2 = sift.detectAndCompute(cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY), None)

    # Initialize FLANN matcher
    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    # Perform KNN matching
    matches = flann.knnMatch(descriptors1, descriptors2, k=2)

    # Apply ratio test to filter matches
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    # Extract the coordinates of the matched keypoints
    src_pts = np.float32([keypoints1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # Compute the homography matrix
    H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    # Warp image1 to align with image2
    height, width, _ = image2.shape
    aligned_image1 = cv2.warpPerspective(image1, H, (width, height))

    # Create a mask to identify non-black regions in the aligned image
    mask = np.all(aligned_image1 != [0, 0, 0], axis=-1)

    # Initialize an image to store the overlay
    overlay_image = np.copy(image2)

    # Overlay the aligned image on top of the original image
    overlay_image[mask] = aligned_image1[mask]

    # Convert the final numpy array to a PIL image
    overlay_image_pil = Image.fromarray(overlay_image.astype('uint8'), 'RGB')
    
    # Save to a BytesIO object
    output = BytesIO()
    overlay_image_pil.save(output, format='PNG')
    output.seek(0)
    
    # Send the processed image back as a file
    return send_file(output, as_attachment=True, attachment_filename='overlay.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
