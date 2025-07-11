# TAER-Core module

TAER-Core is the foundational backend module for the TAER App, providing the essential logic, data handling, and control mechanisms required for Test AER-based sensors. Designed for use by developers, TAER-Core implements the [Model-View-Controller (MVC)](https://wiki.wxpython.org/ModelViewController) architecture using the [wxPython](https://wiki.wxpython.org) framework. 

**Key features:**
- Centralizes all core logic and data models for the TAER ecosystem.
- Separates concerns into Model, View, and Controller components for maintainability and scalability.
- Provides reusable components and utilities for sensor data processing, user interface management, and application control.
- Intended to be extended or integrated by developers building on the TAER platform.

**Module structure:**
- **Model:** Handles data management and business logic ([main_model.py](https://github.com/rafo-og/TAER_Core/blob/main/src/TAER_Core/main_model.py))
- **Controller:** Manages application flow and user interactions ([main_presenter.py](https://github.com/rafo-og/TAER_Core/blob/main/src/TAER_Core/main_presenter.py), [delegates.py](https://github.com/rafo-og/TAER_Core/blob/main/src/TAER_Core/Controllers/delegates.py), [interactors.py](https://github.com/rafo-og/TAER_Core/blob/main/src/TAER_Core/Controllers/interactors.py))
- **View:** Responsible for the graphical user interface ([main_view.py](https://github.com/rafo-og/TAER_Core/blob/main/src/TAER_Core/main_view.py), [Views](https://github.com/rafo-og/TAER_Core/blob/main/src/TAER_Core/Views))

This module is not intended for direct use by end users, but rather as a core library for developers extending or maintaining the TAER App.

## FPGA Interface: `Libs/dev_opal_kelly`

The `Libs/dev_opal_kelly` directory contains the implementation of functions and classes required to interface with the FPGA hardware. This library provides the low-level communication and control mechanisms necessary for interacting with the Opal Kelly FPGA board, including:

- Reading and writing to FPGA registers and memory blocks.
- Managing serial and parallel data transfers.
- Handling control signals, triggers, and wire interfaces.
- Providing abstractions for higher-level operations used throughout the TAER-Core module.

The main classes in this file (`Device`, `DeviceInfo`, `DeviceActions`, etc.) encapsulate all the logic needed to communicate with the FPGA, including device connection management, register and memory access, DAC/ADC operations, and serial communication. These classes are designed to be thread-safe and robust, with error checking and logging built in.

> **Extensibility:**  
> The structure of these classes allows for easy adaptation to other hardware devices. To support a different device, you can implement a new module that keeps the same class and method structure as in `dev_opal_kelly.py`, but adapts the internal logic to the specifics of the new hardware. This ensures compatibility with the rest of the TAER-Core and TAER-App ecosystem, while allowing flexibility for new devices.

This code is essential for enabling the TAER platform to communicate with and control AER-based sensor hardware via the FPGA.

## Deploying new features

To add new features to the TAER-Core module, follow these steps:

1. **Set up your development environment:**
   - Follow the installation instructions for the TAER App as detailed in its repository: [TAER_App](https://github.com/rafo-og/TAER_App).

2. **Clone the TAER-Core repository:**
   ```sh
   git clone https://github.com/rafo-og/TAER_Core.git
   cd TAER_Core
   ```

3. **Create a new branch for your feature:**
   ```sh
   git checkout -b feature/your-feature-name
   ```

4. **Replace the TAER-Core in TAER-App with your local version:**
   - From the TAER App virtual environment, run:
     ```sh
     pip install -e <path/to/cloned/TAER-Core/folder>
     ```
   - At this point, all changes made in TAER-Core will be effective when you launch the TAER App.

5. **Implement your changes:**
   - Add or modify code in the appropriate files.
   - Ensure your code follows the project’s style and guidelines.

6. **Test your changes:**
   - Run the TAER App and verify your new feature works as expected.
   - Add or update unit tests if applicable.

7. **Commit and push your changes:**
   ```sh
   git add .
   git commit -m "Add new feature: your feature description"
   git push origin feature/your-feature-name
   ```

8. **Open a pull request:**
   - Go to the GitHub repository and open a pull request from your branch to the `main` branch.
   - Fill out the pull request template and provide a clear description of your changes.

9. **Wait for review and feedback:**
   - Address any comments or requested changes from reviewers.

Once your pull request is approved and merged, your feature will be included in the next release of TAER-Core.

## Creating a New Release

This project uses GitHub Actions to automate the release process. To create a new release, follow these steps:

1. **Commit and push your changes to the main branch.**
   ```sh
   git add .
   git commit -m "Describe your changes"
   git push origin main
   ```

2. **Check the build process on GitHub Actions.**  
   Go to the "Actions" tab in your GitHub repository and verify that the build workflow is running and finishes without errors.  
   If there are errors, review the output log, fix the issues in your code, and repeat step 1.

3. **Create a new tag for the new version and push the tag.**
   ```sh
   git tag vX.Y.Z   # Replace X.Y.Z with your new version number
   git push origin vX.Y.Z
   ```

4. **Verify the release workflow.**  
   After pushing the tag, a new GitHub Actions job will start. This workflow will build the project and, if successful, create a new release and upload it to the PyPI database.

5. **Update TAER-Core in TAER-App.**  
   Users can now update the TAER-Core module from the TAER-App using:
   ```sh
   pip install --upgrade TAER-Core
   ```
