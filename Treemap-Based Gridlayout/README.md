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
Please download datasets from [google drive](TODO) and move the directory to datasets/.

For example, datasets/infographic/.

Then unzip the .zip files in the folder, and run calc_conf.py and multiload.py (if they exist) to preprocess.

For your dataset, please:
1. prepare the xxx.json, xxx_features.npy, xxx_labels.npy, xxx_labels_gt.npy, xxx_predict_confs.npy and xxx_images folder, xxx can be the name of your dataset. The details of these files can be seen in README.md in [google drive](TODO). 
2. Then run calc_conf.py to preprocess confidence like existing datasets.
3. For large dataset, please run multiload.py to preprocess incremental loading.
4. Add your dataset to function "load" of LabelHierarchy in application/data/LabelHierarchy.py.

Run
----------
Modify the "port = Port(xxx)" and "port.load_dataset(xxx)" statements in server.py according to your requirements.
```
cd backend
bash run.sh    (or directly runing server.py)
```