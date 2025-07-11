#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil


def generate_client():
    """Generate the Python client from OpenAPI spec"""
    print("Generating Immich API client...")

    # Clean up any existing directory
    if os.path.exists("immich_client"):
        shutil.rmtree("immich_client")

    # Ensure output directory exists
    os.makedirs("immich_client")

    # Generate client using openapi-generator
    cmd = [
        "openapi-generator-cli",
        "generate",
        "-i",
        "immich-openapi-specs.json",
        "-g",
        "python",
        "-o",
        "immich_client",
        "--additional-properties=packageName=immich_client,packageVersion=1.0.0,projectName=immich-client",
    ]

    try:
        subprocess.run(cmd, check=True)
        print("Successfully generated client code!")

        # Remove any existing pyproject.toml
        if os.path.exists(os.path.join("immich_client", "pyproject.toml")):
            os.remove(os.path.join("immich_client", "pyproject.toml"))

        # Create minimal setup.py
        create_setup_py()

    except subprocess.CalledProcessError as e:
        print(f"Error generating client: {e}")
        sys.exit(1)


def create_setup_py():
    """Create a minimal setup.py file"""
    setup_content = """
from setuptools import setup, find_packages

setup(
    name="immich_client",
    version="1.0.0",
    packages=find_packages(exclude=["test", "tests"]),
    install_requires=[
        "urllib3>=1.25.3",
        "python-dateutil",
        "aiohttp",
    ],
)
"""

    with open(os.path.join("immich_client", "setup.py"), "w") as f:
        f.write(setup_content.strip())

    print("Created minimal setup.py file")


def setup_client():
    """Install the generated client package"""
    os.chdir("immich_client")
    try:
        # Install in development mode
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("Successfully installed client package!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing client package: {e}")
        sys.exit(1)


if __name__ == "__main__":
    generate_client()
    setup_client()
