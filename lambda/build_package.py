import os
import shutil
import subprocess
import sys
import zipfile

def build_lambda_package():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    processor_dir = os.path.join(current_dir, "resume_processor")
    build_dir = os.path.join(processor_dir, "build")
    req_file = os.path.join(processor_dir, "requirements.txt")
    output_zip = os.path.join(processor_dir, "resume_processor.zip")

    print(f"Building AWS Lambda deployment package for resume_processor...")

    # Clean existing build directory or output zip
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    if os.path.exists(output_zip):
        os.remove(output_zip)

    os.makedirs(build_dir, exist_ok=True)

    # Install dependencies targeting manylinux2014_x86_64 for AWS Lambda Python 3.12 runtime
    print("Installing Linux-compatible dependencies for Lambda...")
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--platform", "manylinux2014_x86_64",
        "--target", build_dir,
        "--implementation", "cp",
        "--python-version", "3.12",
        "--only-binary=:all:",
        "-r", req_file
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR installing requirements:\n{result.stderr}")
        sys.exit(1)

    # Copy lambda_function.py into build directory
    source_fn = os.path.join(processor_dir, "lambda_function.py")
    target_fn = os.path.join(build_dir, "lambda_function.py")
    shutil.copyfile(source_fn, target_fn)

    # Create zip package
    print(f"Creating zip file: {output_zip}...")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, build_dir)
                zf.write(abs_path, rel_path)

    # Cleanup build dir
    shutil.rmtree(build_dir)
    zip_size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    print(f"Successfully generated {output_zip} ({zip_size_mb:.2f} MB)")
    print("Ready to upload to AWS Lambda (Runtime: Python 3.12, Architecture: x86_64)")

if __name__ == "__main__":
    build_lambda_package()
