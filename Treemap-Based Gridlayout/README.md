### Please creating a separate Python virtual environment for the following operations to prevent errors from occurring!

Setup Environment
----------
You can use pip or other tools to setup environment.

For Example:
```
pip install -r requirements.txt
```



Compile
----------
There are several packages that need to be compiled or installed manually.

\
Linear Assignment Package:
```
cd application
cd data
cd linear_assignment
python setup.py install
```

\
Grid Layout Utils Package:
```
cd application
cd data
cd "c module_now"
python setup.py build_ext --inplace    (For MSVC environment in Windows, please use setup_win.py)
```
Then move the compiled files (such as .pyd or .so) to application/data/.

If you encounter issues while compiling, please try adjusting the line endings to LF or CRLF according to your system environment.

Datasets
----------
Please download datasets from [google drive](https://drive.google.com/drive/folders/1kzhPbK1bI_i9RGlHNMs4MHYsgfIbF5xW?usp=sharing) and move the directory to datasets/.

For example, datasets/infographic/.

Then unzip the .zip files in the folder.

For your dataset, please:
1. prepare the xxx_features.npy and xxx_images folder.
2. Then run get_hier("xxx") in rebuild_gridlayout.py to preprocess like existing datasets.
3. Add your dataset to function "load" of LabelHierarchy in application/data/LabelHierarchy.py.

Run
----------
Modify the "port = Port(xxx)" and "port.load_dataset(xxx)" statements in server.py according to your requirements.
```
cd backend
bash run.sh    (or directly runing server.py)
```