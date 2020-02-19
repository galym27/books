# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 17:43:58 2020

@author: MutaGa
"""
from flask import Flask, render_template, jsonify, request
import requests

def main():
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "2aMU57awaj0ro5no3LOIA", "isbns": "9781632168146"})
    data1 = res.json()

    print(data1)
    print(data1['books'][0]['average_rating'])

main()

#if __name__ == '__main__':
#    app.run()
#