import os
import zipfile

def create_release_zip(output_filename="jarvis-v1.0.0.zip"):
    """
    Packages the repository source code and assets into a clean release ZIP
    suitable for attachment to a GitHub release. Excludes virtual environments,
    local user databases, environment keys, and caches.
    """
    # Root directory of the project
    root_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(root_dir, output_filename)
    
    # Items to include in the ZIP (recursive directories and individual files)
    includes = {
        "jarvis": True,        # True means include recursively
        "tests": True,
        ".github": True,       # Include GitHub actions/workflows
        "docs": True,          # Include docs & assets
        "requirements.txt": False,
        "README.md": False,
        "LICENSE": False,
        "RELEASE_SUMMARY.md": False,
        "START_HERE.md": False,
        "start_jarvis.bat": False,
        "COMPLETE_PROJECT_JOURNEY.md": False,
        "JARVIS_Project_Documentation.md": False,
        ".env.example": False,
        ".gitignore": False
    }
    
    print(f"==================================================")
    print(f" J.A.R.V.I.S. Release Packaging Utility")
    print(f"==================================================")
    print(f"Bundling files into: {output_filename}...\n")
    
    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item, is_dir in includes.items():
            item_path = os.path.join(root_dir, item)
            if not os.path.exists(item_path):
                print(f"  [Skip] Missing item: {item}")
                continue
                
            if is_dir:
                # Add folder recursively
                for root, dirs, files in os.walk(item_path):
                    # Skip python compiled/caching folders
                    if "__pycache__" in root or ".pytest_cache" in root:
                        continue
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Compute archive name relative to project root
                        arcname = os.path.relpath(file_path, root_dir)
                        zipf.write(file_path, arcname)
                        count += 1
            else:
                # Add individual file
                arcname = os.path.relpath(item_path, root_dir)
                zipf.write(item_path, arcname)
                count += 1
                
    print(f"\nSuccessfully packaged {count} files!")
    print(f"Output ZIP: {zip_path}")
    print(f"File Size:  {os.path.getsize(zip_path) / (1024 * 1024):.2f} MB")
    print(f"==================================================")

if __name__ == "__main__":
    create_release_zip()
