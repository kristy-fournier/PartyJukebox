# Self Running Part

To design a self-running app for your Raspberry Pi based on your requirements, here’s a step-by-step plan that you can follow. I'll guide you through the steps without giving the full solution, so you can piece it together.

### Steps to Implement

1. **Automating Raspberry Pi Startup Actions:**
   - **Systemd Service**: Use `systemd` to create a service that will automatically run when the Pi starts. This can manage your app’s startup logic.
   - **Startup Script**: Alternatively, you can create a simple shell script that runs on boot, either placed in `/etc/rc.local` or managed by `cron` with the `@reboot` directive.

2. **Detect USB Flash Drive on Boot:**
   - **Automounting USB**: Set up the Raspberry Pi to automount flash drives when plugged in. Look into editing `/etc/fstab` or using the `usbmount` package.
   - **Checking for MP3s**: Write Python logic that checks the mounted drives for files with `.mp3` extension. Use libraries like `os` or `pathlib` to scan directories.

3. **Copying MP3s to a Directory:**
   - You can use the `shutil` library in Python to handle file copying.
   - Ensure this logic only triggers when new files are found (so you don’t overwrite your existing directory unnecessarily).

4. **Running the Database Generator:**
   - Since you only want the database generator to run when needed, you can add a condition to check whether the MP3s were updated. For example, store a checksum or file modification time, and if there's a change, trigger the generator.

5. **Running the Flask Web Server:**
   - After copying the files and running the database generator (if needed), the script should launch your Flask web server.
   - Flask can be run as part of your startup service as well, once the other tasks are complete.

### Suggested Order of Operations
- On boot, run your startup script.
- Check for connected USB drives.
- If MP3s are found, copy them to the designated folder.
- Run the database generator only if new files are detected.
- Launch the Flask web server.

### Things to Consider:
- **Timing**: If there’s a delay for the USB drive to mount, you might want to add a short wait period or a retry loop when checking for the flash drive.
- **Combining Files**: You can combine the MP3-checking, copying, and database generation logic into a single Python script. Then, it can conditionally call the database generator only when new files are added, before starting the Flask server.

# Raspberry Pi Image

To create a distributable Raspberry Pi image of your project, here's how you can go about it:

### Steps to Create a Distributable Image

1. **Set Up and Configure Your Raspberry Pi:**
   - Start with a clean installation of **Raspberry Pi OS (32-bit)** since you're testing on 32-bit devices.
   - Install and configure your jukebox project (ensure everything works correctly on the hardware).
   - Set up any additional packages or dependencies that your project needs.

2. **Make Your Application Auto-Start:**
   - Ensure your application (including the USB drive detection, MP3 copying, database generation, and Flask server) starts automatically on boot using `systemd` or another method like `cron` or `/etc/rc.local`.
   - Test this setup by rebooting the Pi and checking if your application behaves as expected.

3. **Install Any Required Packages:**
   - Install any third-party libraries or software required by your Python scripts (e.g., Flask, `shutil`, `usbmount`).
   - Use a `requirements.txt` file (if using Python’s `pip`) to track the dependencies.

4. **Prepare the Image for Distribution:**
   - Remove unnecessary files or software to make the image smaller and more efficient.
   - Make sure all scripts, services, and permissions are set up properly for non-root users if required.
   - Disable any development tools or services that shouldn't be included in the final image.

5. **Create a Backup of Your Raspberry Pi SD Card:**
   - **Shutdown the Pi** after everything is set up and working.
   - Remove the SD card and connect it to your PC or Mac using an SD card reader.
   - Use a tool like `Raspberry Pi Imager`, `Win32DiskImager` (on Windows), or `dd` (on Linux/Mac) to create a backup of your SD card. This will allow you to create an image file (`.img`).

6. **Compress the Image:**
   - Since SD card images can be large, compress the `.img` file using a tool like `gzip` or `7zip`. This will make it easier to distribute.

7. **Test the Image:**
   - Flash the `.img` file back onto a new SD card and test it on another Raspberry Pi to ensure it boots up and runs your application properly without requiring additional configuration.
   
8. **Distribute the Image:**
   - Once the image works as expected, you can distribute it by uploading it to a platform like Google Drive or Dropbox, where others can download it and flash it onto their Raspberry Pis.
   
### Things to Keep in Mind:
- **Image Size**: If your image is too large, users might need SD cards with more capacity. Trim down unnecessary files to reduce the size.
- **Updates**: Consider how users will receive future updates. You could include a mechanism in your app to check for updates or distribute new versions of the image as needed.

This should give you a distributable image that can be easily flashed and run on other Raspberry Pi devices!