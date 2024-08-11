# Running the Workflow

1. Open a Terminal/command prompt.
2. Navigate to the `Italiano_MK_Analysis` folder using the `cd` command:
   ```sh
   cd path/to/Italiano_MK_Analysis
   ```

## Via Terminal

3. Activate the workflow environment:
   ```sh
   pipenv shell
   ```
4. Run the workflow script:
   ```sh
   python mk "your_image_folder_path"
   ```
   Example:
   ```sh
   python mk /Users/Italiano/Desktop/MK_Images
   ```

## Via Jupyter Notebook

3. Start Jupyter Notebook:
   ```sh
   jupyter notebook
   ```
4. Access the `MK` notebook located in the `jupyter` folder (inside the repo).
5. In the first cell, set the path to your image folder next to the `FOLDER =` variable.
6. To run the entire notebook, click the `>>` under the Widgets tab at the top.
7. Alternatively, progress through the notebook step by step by using `Shift + Enter`.
