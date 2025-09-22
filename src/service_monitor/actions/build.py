"""Actions the project can perform."""

import os
import shutil


def build() -> None:
    """Build the project.

    Removes the old build directory if it exists and creates a new one.
    """
    # Remove old build directory
    if os.path.exists("build"):
        shutil.rmtree("build")

    # Create new build directory
    os.makedirs("build")

    # Print success message
    print("Project built successfully!")
