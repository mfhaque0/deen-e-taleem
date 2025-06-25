import os
from PIL import Image

# --- Configuration ---
# Path to your full-size wallpapers
FULL_WALLPAPERS_DIR = 'downloadable_files/wallpapers'
# Path where thumbnails will be saved
THUMBNAILS_DIR = 'static/wallpaper_thumbnails'
# Target size for the longest side of the thumbnail (e.g., 600 pixels)
THUMBNAIL_LONGEST_SIDE = 600
# Quality for JPEG images (0-100, lower for smaller file size)
JPEG_QUALITY = 85 
# --- End Configuration ---

def generate_thumbnails():
    # Ensure the thumbnails directory exists
    if not os.path.exists(THUMBNAILS_DIR):
        os.makedirs(THUMBNAILS_DIR)
        print(f"Created directory: {THUMBNAILS_DIR}")

    processed_count = 0
    for filename in os.listdir(FULL_WALLPAPERS_DIR):
        # Process only image files (you might want to add more extensions)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            full_image_path = os.path.join(FULL_WALLPAPERS_DIR, filename)
            thumbnail_path = os.path.join(THUMBNAILS_DIR, filename)

            try:
                with Image.open(full_image_path) as img:
                    # Calculate new size to maintain aspect ratio
                    width, height = img.size
                    if width > height:
                        new_width = THUMBNAIL_LONGEST_SIDE
                        new_height = int(height * (THUMBNAIL_LONGEST_SIDE / width))
                    else:
                        new_height = THUMBNAIL_LONGEST_SIDE
                        new_width = int(width * (THUMBNAIL_LONGEST_SIDE / height))

                    img = img.resize((new_width, new_height), Image.LANCZOS)

                    # Save with appropriate format and quality
                    if filename.lower().endswith(('.jpg', '.jpeg')):
                        img.save(thumbnail_path, quality=JPEG_QUALITY, optimize=True)
                    else: # For PNG, GIF, WebP
                        img.save(thumbnail_path, optimize=True) # PNG quality is handled differently

                    print(f"Generated thumbnail for: {filename}")
                    processed_count += 1

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print(f"\n--- Thumbnail generation complete. Processed {processed_count} images. ---")

if __name__ == "__main__":
    generate_thumbnails()