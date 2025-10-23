# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import sys
sys.path.append('data')
from dataControl_new2 import DataControl

if __name__ == '__main__':
    print("start")
    data_control = DataControl(with_text=True, use_prop=True)
    data_control.load_data("data/datasets/YOUR_DATASET", model="dreamsim")  # TO FILL
    data_control.apply_edit_to_dataset2(save=True)
