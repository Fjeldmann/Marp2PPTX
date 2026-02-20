import os
import shutil
from dotenv import load_dotenv
import subprocess

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Get credentials from environment variables
    publish_token = os.getenv("UV_PUBLISH_TOKEN")

    if not publish_token:
        raise ValueError("UV_PUBLISH_TOKEN must be set in the .env file")

    # Delete 'dist' folder if it exists
    dist_folder = "dist"
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
        print(f"Deleted existing '{dist_folder}' folder.")

    # Build the package
    print("Building the package...")
    subprocess.run(["uv", "build"], check=True)

    # Publish the package
    print("Publishing the package...")
    subprocess.run(["uv", "publish"], check=True, env={
        **os.environ,
        "UV_PUBLISH_TOKEN": publish_token,
    })

if __name__ == "__main__":
    main()