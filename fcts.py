import OAI
import json
import pandas as pd
import os, hashlib, glob, io, time, json

import numpy as np
import pandas as pd

from lxml import html
from bs4 import BeautifulSoup
import trafilatura, requests

def h(x):
    return hashlib.md5(str(x).encode('utf-8')).hexdigest()

f = OAI.askFCT("AIf","./cache")
f.GOTOCACHE = "./cache/"

def getFctAIf():
    functions = [
            {
            "name": "get_AIf",
            "description": "If the user asks for a signals review, review the text as a futurist specializing in the future of generative AI in the infrastructure industry. The seeds must be high level changes reflected by the text, not specifics of the text itself, and must not identify private organizations. Identify as many seeds as you can.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "A proper title for this text, as a journalist would write for this text. It must not be longer than 6 words.",
                    },
                    "keywords": {
                        "type": "array",
                        "description": "Extract the main top 5 keywords.",
                        "items": {
                            "type": "string",
                        },   
                    },
                    "themes": {
                        "type": "array",
                        "description": "Extract the main top 3 themes of the text.",
                        "items": {
                            "type": "string",
                        },   
                    },
                    "summary": {
                        "type": "string",
                        "description": "Summary of the text in 4 to 5 sentences.",
                    },
                    "seeds": {
                        "type": 'array',
                        "items": {
                            "type": 'object',
                            "description": "Each is a 'futures seed', which is a way futurists analyse weak signals and changes. It consists in a name, type of change, impact of change, and driving force.",
                            "properties": {
                                "signal" :{
                                    "type": 'string', 
                                    "description": 'A summary of the change.'
                                },
                                "change" :{
                                    "type": 'string', 
                                    "description": "What kind of change is this (from what to what) ?"
                                },
                                "10y impact" :{
                                    "type": 'string', 
                                    "description": "What might be different in 10 years time?"
                                },
                                "driving force" :{
                                    "type": 'string', 
                                    "description": "What’s one driving force, or motivation, behind this change?"
                                }
                            },
                            "required": ['signal',"change","10y impact","driving force"],
                        }
                    },
                },
                "required": ["title","keywords", "themes","summary","seeds"],
            },
        }
    ]
    return functions

def reviewText(txt,modelGPT="gpt-3.5-turbo-1106", ow=False,seed=""):
    fcts = getFctAIf()
    messages, chat_response = f.askFct("You are an expert futurist, specializing in engineering and advisory services in Infrastructure. You review signals that could impact your work sector.","Do signals review of the following text:\n\n"+txt.strip(),fcts,modelGPT=modelGPT, ow=ow,seed=seed) 
    df = pd.DataFrame(json.loads(messages[-1]["function_call"]["arguments"])["seeds"])
    df["title"] = json.loads(messages[-1]["function_call"]["arguments"])["title"]
    df["keywords"] = "\n".join(json.loads(messages[-1]["function_call"]["arguments"])["keywords"])
    df["themes"] = "\n".join(json.loads(messages[-1]["function_call"]["arguments"])["themes"])
    df["summary"] = json.loads(messages[-1]["function_call"]["arguments"])["summary"]
    return df


def getTexts():
    articles = []
    errors = []
    DONE = glob.glob("cache/*.clean")
    #  print(DONE)
    for file_name in glob.glob("cache/*.page"):
        FN = file_name.split(os.sep)[-1].split(".page")[0] 
        #print(FN)
        if not os.path.isfile("cache/"+FN+".clean"):
            with io.open(file_name, mode="r", encoding="utf-8") as f:
                try:
                    mytree = html.fromstring("".join(f.readlines()))
                except Exception as e:
                    print(e)
                    errors.append(file_name)
                    continue
                try:
                    content = trafilatura.extract(mytree)
                    articles.append((FN, content))
                except Exception as e:
                    print(e)
                    errors.append(file_name)
    dfText = pd.DataFrame(articles, columns = ["hash","content"])
    return dfText




def getPages():

    with open("sources.md", "r") as f:
        urls = f.read().split("\n")
        urls = [x.strip() for x in urls if len(x.strip())]
        
    dfURLS = []
    TODO = False
    for url in urls:
        name = h(url)
        dfURLS.append([url,name])
        if not os.path.exists("cache/"+name+".page"):
            TODO = True
    if TODO:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service

        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--enable-javascript")
        #options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)

        dfURLS = []
        for url in urls:
            name = h(url)
            dfURLS.append([url,name])
            if not os.path.exists("cache/"+name+".page"):
                driver.get(url)
                content = BeautifulSoup(driver.page_source, "html.parser")

                with open("cache/"+name+".page", 'w') as f:
                    f.write(str(content))
                #print(name,"saved")
    else:
        print("All pages already there")
