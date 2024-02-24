import puppeteer from 'puppeteer';
import { exec } from 'child_process';
import fs from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Helper function to extract latitude and longitude from URL
function extractLatLng(url) {
  const match = url.match(/@([-\d.]+),([-\d.]+)/);
  if (match && match.length >= 3) {
    return `${match[1]}_${match[2]}`;
  } else {
    throw new Error('Unable to extract latitude and longitude from URL');
  }
}

(async () => {
  const browser = await puppeteer.launch({ headless: false, defaultViewport: null,
    args: ['--start-maximized'] });
  const page = await browser.newPage();
  const pendingRequests = new Map(); // Store intercepted requests waiting for tiles

  await page.setRequestInterception(true);

  page.on('request', async (interceptedRequest) => {
    if (interceptedRequest.url().includes('streetviewpixels-pa.googleapis.com')) {
    // wait 1 second
    await new Promise((resolve) => setTimeout(resolve, 1000));
    const url = new URL(interceptedRequest.url());
      const x = url.searchParams.get('x');
      const y = url.searchParams.get('y');
      const zoom = url.searchParams.get('zoom');
      // if zoom is not 5, skip the request
        if (zoom !== '3') {
            console.log(`Skipping request for zoom ${zoom} at x=${x}, y=${y}`);
            interceptedRequest.continue();
            // abort
            // interceptedRequest.abort();
            return;
        }
      const latLng = extractLatLng(page.url()); // Extract latLng from the page URL
      const tileName = `tile_x${x}_y${y}.jpg`;
      const exportFolderName = `3export${latLng}`;
      const imageFilePath = path.join(__dirname, exportFolderName, tileName);

      // If tile image is already available, serve it immediately
      if (fs.existsSync(imageFilePath)) {
        const imageBuffer = fs.readFileSync(imageFilePath);
        interceptedRequest.respond({
          status: 200,
          contentType: 'image/jpeg',
          headers: {
            'Access-Control-Allow-Origin': 'https://www.google.com', // For production, specify the exact origin
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Expose-Headers': 'vary,vary,vary,date,server,content-length',
            'Alt-Svc': 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000',
            'Content-Length': imageBuffer.length.toString(), // Set the correct content length of the image buffer
            'Content-Type': 'image/jpeg',
            'Date': new Date().toUTCString(), // Set the current date in HTTP format
            'Server': 'scaffolding on HTTPServer2',
            'Vary': 'Origin, X-Origin, Referer',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Xss-Protection': '0',
            'customimage': 'true'

            },
          body: imageBuffer
        });
      } else {
        // If the image is not available, check if the Python script is already running
        let execPromise = pendingRequests.get(latLng);
        if (!execPromise) {
          // If not, start the Python script and store the promise
          execPromise = execAsync(`python ./get_streetview.py '${page.url()}'`);
          pendingRequests.set(latLng, execPromise);
        }

        // Wait for the Python script to finish
        execPromise.then(({ stdout }) => {
          if (stdout.includes('okay')) {
            // Once finished, check for the image again and serve if available
            if (fs.existsSync(imageFilePath)) {
              const imageBuffer = fs.readFileSync(imageFilePath);
              interceptedRequest.respond({
                status: 200,
                contentType: 'image/jpeg',
                headers: {
                    'Access-Control-Allow-Origin': 'https://www.google.com', // For production, specify the exact origin
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Expose-Headers': 'vary,vary,vary,date,server,content-length',
                    'Alt-Svc': 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000',
                    'Content-Length': imageBuffer.length.toString(), // Set the correct content length of the image buffer
                    'Content-Type': 'image/jpeg',
                    'Date': new Date().toUTCString(), // Set the current date in HTTP format
                    'Server': 'scaffolding on HTTPServer2',
                    'Vary': 'Origin, X-Origin, Referer',
                    'X-Content-Type-Options': 'nosniff',
                    'X-Frame-Options': 'SAMEORIGIN',
                    'X-Xss-Protection': '0',
                    'customimage': 'true'
                    },
                body: imageBuffer
              });
            } else {
              console.error(`Image file still does not exist after Python script: ${imageFilePath}`);
              interceptedRequest.abort('failed');
            }
          } else {
            console.error(`Python script did not return 'okay': ${stdout}`);
            interceptedRequest.abort('failed');
          }
        }).catch((error) => {
          console.error(`Error with Python script execution: ${error}`);
          interceptedRequest.abort('failed');
        });
      }
    } else {
      interceptedRequest.continue();
    }
  });

  await page.goto('https://www.google.com/maps/@45.4337393,12.339596'); //,3a,90y,11.34h,92.9t/data=!3m6!1e1!3m4!1sbi5_hRKeSCf8EA5IZ2guhA!2e0!7i13312!8i6656?entry=ttu');

  page.on('framenavigated', () => {
    pendingRequests.clear();
  });

  // Uncomment the line below when you're ready to close the browser
  // await browser.close();
})();
