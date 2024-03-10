# Crowdsourced Streetview

### Streetview Demo
To run the demo, just run 'node server.js', which will open up a controlled Puppeteer browser that navigates to maps.google.com. This controlled browser will proxy the image requests to our Python script, which will attempt to overlay the crowdsourced images onto the current Streetview image based on a current location.

The demo defaults to a slow image overlay for compatibility. If you just want to see it work, run the server and navigate to the location where your image is.

To take advantage of NVIDIA TensorRT SuperPoint, you will need to compile a version of TensorRT SuperPoint that corresponds to your hardware. You can follow the tutorial here: 
https://github.com/yuefanhao/SuperPoint-SuperGlue-TensorRT

Once you have a compiled model, place the onnx and engine weights in the 'superpoint' directory and run 'node server.js' again. This will use the compiled TensorRT SuperPoint to align the images, which is much faster than the normal SuperPoint.

---

### Get Involved
Become a part of an effort that aims to make Streetview more dynamic, accurate, and informative. Contribute code and help us build a better visual world!

For more information, reach out at [rl869@cornell.edu](mailto:rl869@cornell.edu).

---
