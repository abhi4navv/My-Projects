import os
from flask import Flask,render_template,request
import numpy as np
import cv2
from PIL import Image
import requests
import base64
import re
import PIL.ImageOps
import os
import pandas as pd
from scipy.ndimage.interpolation import zoom
import json
from PIL import ImageEnhance
import time
from pdf2image import convert_from_path
import collections
import io
import pyodbc
import pymssql
from flask_table import Table, Col

class Results(Table):
    id = Col('Id', show=False)
    artist = Col('Artist')
    title = Col('Title')
    release_date = Col('Release Date')
    publisher = Col('Publisher')
    media_type = Col('Media')
def fileupload():
    APP_ROOT=os.path.dirname(os.path.abspath(__file__))
    target=os.path.join(APP_ROOT,"images/")
    if not os.path.isdir(target):
        os.mkdir(target)
    return(target)
def updateAccNo(Pan_No,AccNo):
    conn,cur= create_con()
    sqlstr="UPDATE CustomerInfo SET Account_Number='" + str(AccNo) + "'   WHERE PAN_Num='"+Pan_No+"'"
    cur.execute(sqlstr)
    conn.commit()
def openaccnt(pannum,type):

    if type=='acopen':
        conn,cur= create_con()
        sqlstr="SELECT MAX(Account_Number) FROM CustomerInfo WHERE PAN_Num='"+pannum+"'"
        dt=cur.execute(sqlstr)
        if cur.rowcount==0 :
            Accno='000001'
        else:
            Accno=cur.fetchall()
            if Accno[0][0]=='NULL':
                 Accno=123001
            else:
                Accno=int(Accno[0][0])+1
        cur.close()
    updateAccNo(pannum,Accno)
    conn,cur= create_con()
    sqlstr="SELECT First_Name,Middle_Name,Last_Name,Father_Name,DOB,Address,Aadhar_Num,PAN_Num,Email_Id,Mob_Num,Account_Number FROM CustomerInfo WHERE PAN_Num='"+pannum+"'"
    cur.execute(sqlstr)
    if cur.rowcount==0:
        json_data='0'
    else:
        json_data=cur.fetchall()
        cur.close()
    return json_data
def create_con():
    host = "bankfininfo.database.windows.net"
    username = "abhinav@bankfininfo"
    password = "acad!1234"
    database = "CustomerDetail"
    conn = pymssql.connect(host, username, password, database)
    cur=conn.cursor()
    return conn,cur
def chkAccNo(Pan_No):
    conn,cur= create_con()
    sqlstr="SELECT Account_Number FROM CustomerInfo   WHERE PAN_Num='"+Pan_No+"'"
    cur.execute(sqlstr)
    retval=False
    if cur.rowcount==0 :
            retval=True
    else:
        Accno=cur.fetchall()
        if Accno[0][0]=='NULL':
            retval=True
        else:
            retval=False
    return retval
def openaccnt(pannum,type):
    if type=='acopen':
       chkacc=chkAccNo(pannum)
       if(chkacc==True):
           conn,cur= create_con()
           sqlstr="SELECT MAX(Account_Number) FROM CustomerInfo"
           dt=cur.execute(sqlstr)
           if cur.rowcount==0 :
               Accno=123001
           else:
               Accno=cur.fetchall()
               if Accno[0][0]=='NULL':
                    Accno=123001
               else:
                   Accno=int(Accno[0][0])+1
           cur.close()
           updateAccNo(pannum,Accno)

    conn,cur= create_con()
    sqlstr="SELECT First_Name,Middle_Name,Last_Name,Father_Name,DOB,Address,Aadhar_Num,PAN_Num,Email_Id,Mob_Num,Account_Number FROM CustomerInfo WHERE PAN_Num='"+pannum+"'"
    cur.execute(sqlstr)
    if cur.rowcount==0:
       json_data='0'
    else:
       json_data=cur.fetchall()
    cur.close()
    return json_data

def insertcustinfo (Fname,Mname,Lname,FaName,DOB,PANNum,Address,AadharNum,MobNum,EmailId):

    conn,cur= create_con()
    message=''
    Acc_num=''
    Acc_num='NULL'
    cur.execute("SELECT * FROM CustomerInfo WHERE  Mob_Num='"+MobNum+"' AND First_Name='"+Fname+"' AND DOB='"+DOB+"'")

    if cur.rowcount==0:
        try:
            cur.execute("INSERT INTO CustomerInfo(First_Name,Middle_Name,Last_Name,Father_Name,DOB,Address,Aadhar_Num,PAN_Num,Email_Id,Mob_Num,Account_Number)VALUES (%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d)", (Fname,Mname,Lname,FaName, DOB,Address,AadharNum,PANNum,EmailId,MobNum,Acc_num))
            conn.commit()
            message='Records saved succesfully please confirm if your data are valid and click on your PAN Number below to acknowledge and  open account'
        except:
            message='Error in saving IT please contact customer care'

    else:
        message='The customer info already exist can not open duplicate Account '
    cur.close()
    return message,Fname,Mname,Lname,FaName,DOB,Address,AadharNum,PANNum,MobNum,EmailId
def getdtfromdict(response,doctype):
    if(doctype=='pan'):
        dt=PAN_Module(response)

        PANNum=dt['PAN']
        lstName=list()
        lstName=dt['Name'].split(' ')
        if len(lstName)==3:
            Fname=lstName[0]
            Mname=lstName[1]
            Lname=lstName[2]
        elif(lstName==2):
            if dt['Surname']!='':
                Fname=lstName[0]
                Mname=lstName[1]
                Lname=surname
        else:
            print(len(lstName))
            Fname=lstName[0]
            Mname=''
            Lname=lstName[1]
        FaName=dt['Father Name']
        DOB=dt['DOB']
        return Fname,Mname,Lname,FaName,DOB,PANNum
    elif(doctype=='aadhar'):
        Address=''
        AadharNum=''
        dta=Aadhar_Module(response)
        Address=dta['Address']
        AadharNum=str(dta['Aadhar No'].replace(" ",""))
        return Address,AadharNum

def detect_image_text(image):
    key='AIzaSyBQ9SAccc8w1iZK2B2Wx9FKsx5c0ECIPVo'
    url = 'https://vision.googleapis.com/v1/images:annotate?key=AIzaSyBQ9SAccc8w1iZK2B2Wx9FKsx5c0ECIPVo'
    res = []
    img_base64 = base64.b64encode(image)
    ig = str(img_base64)
    ik=ig.replace('b\'','')
    headers={'Content-Type': 'application/json'}
    data ="""{
        "requests": [
          {
            "image": {
                     "content": '"""+ik[:-1]+"""'

                      },

            "features": [
              {
                "type": "DOCUMENT_TEXT_DETECTION"
              }
            ]
          }
        ]
      }"""
    r = requests.post(url, headers=headers,data=data)
    result = json.loads(r.text)
    return result

    # For PAN Card
    # Step-6:
def Aadhar_Module(json_Aadhar_response):

    type(json_Aadhar_response)

    responses = json_Aadhar_response['responses']
    #responses

    textAnnotations = responses[0]['textAnnotations']
    #textAnnotations

    description = textAnnotations[0]['description']
    #print(description)
    #print(type(description))

    import pandas as pd
    data = description
    df = pd.DataFrame([x.split(';') for x in data.split('\n')])
    adhint=0
    for i,val in df.iterrows():
        if  'Aadhaar No' in str(df.iloc[i][0]):
            adhint=i+1
    en = df.iloc[1][0]
   # en_split = en.split(': ')
    print(en)
    address = df.iloc[8][0] + " " + df.iloc[9][0] + " " + df.iloc[10][0] + " " + df.iloc[11][0] + " " + df.iloc[12][0]
    dob = df.iloc[11][0]
    dob_split = dob.split(':')
    print("DOB: ",dob_split)
    Aadhar_dict = dict({ 'Address':address, 'Aadhar No':df.iloc[adhint][0].replace(' ','')})
    print(address)
    return Aadhar_dict


def PAN_Module(json_PAN_response):

    type(json_PAN_response)

    responses = json_PAN_response['responses'] #responses

    textAnnotations = responses[0]['textAnnotations']
    #textAnnotations
    description = textAnnotations[0]['description']
    #print(description)
    import pandas as pd
    data = description
    df = pd.DataFrame([x.split(';') for x in data.split('\n')])
    PAN=''
    Name=''
    Surname=''
    Fname=''
    Dob=''
    for i,dt in df.iterrows():
        if str(dt[0])=='Permanent Account Number Card':
            PAN=df.iloc[i+1][0]
            if 'Name' in str(df.iloc[i+2][0]):
                Name=df.iloc[i+3][0]
                if "Father" not in str(df.iloc[i+4]):
                    Surname=df.iloc[i+4][0]
            else:
                Name=df.iloc[i+2][0]
        elif 'Father' in str(dt[0]):
            Fname=df.iloc[i+1][0]
        if 'Birth' in str(df.iloc[i][0]):
            Dob=df.iloc[i+1][0]
    PAN_dict = dict({'PAN':PAN, 'Name':Name, 'Surname':Surname, 'Father Name':Fname, 'DOB':Dob})
    return PAN_dict


app=Flask(__name__)

@app.route("/index",methods=["GET","POST"])
def index():
    messages2=''
    messages=''
    filename=''
    destination=''
    MobNum=''
    EmailId=''
    jsondt=''
    Fname=''
    Mname=''
    Lname=''
    FaName=''
    DOB=''
    Address=''
    AadharNum=''
    PANNum=''
    Accno='Account Not Yet Created'
    Dsp=''
    if request.method=='POST':
        if request.form['action'] == 'Upload':
            if len(request.form['text1'])==0:
                messages='Mobile number is mendatory.'
            elif len(request.form['text2'])==0:
                messages=messages+'Email  is mendatory.'
            elif len(request.files.getlist("file"))==0:
                messages=messages+'Please select file for PAN Card.'
            elif len(request.files.getlist("file2"))==0:
                messages=messages+'Please select file for AADHAR Card.'
            else:
                mobno=request.form['text2']
                emailid=request.form['text1']
                for file in request.files.getlist("file"):
                    filename = request.files.getlist("file")
                    filename=file.filename
                    target=fileupload()
                    destination="/".join([target, filename])
                    file.save(destination)
                    new_file_name = destination
                    image_bytes = open(new_file_name,'rb')
                    image_bytes = image_bytes.read()
                    image = np.array(Image.open(io.BytesIO(image_bytes)))
                    image_bytes = cv2.imencode('.jpg',image)[1].tostring()
                    APIResPan = detect_image_text(image_bytes)
                    Fname,Mname,Lname,FaName,DOB,PANNum=getdtfromdict(APIResPan,'pan')


                for file2 in request.files.getlist("file2"):
                    filename2 = request.files.getlist("file2")
                    filename2=file2.filename
                    target2=fileupload()
                    destination2="/".join([target2, filename2])
                    file2.save(destination2)
                    new_file_name2 = destination2
                    image_bytes2 = open(new_file_name2,'rb')
                    image_bytes2 = image_bytes2.read()
                    image2 = np.array(Image.open(io.BytesIO(image_bytes2)))
                    image_bytes2 = cv2.imencode('.jpg',image2)[1].tostring()
                    APIResAdh = detect_image_text(image_bytes2)
                    Address,AadharNum=getdtfromdict(APIResAdh,'aadhar')


                messages,Fname,Mname,Lname,FaName,DOB,Address,AadharNum,PANNum,MobNum,EmailId=insertcustinfo(Fname,Mname,Lname,FaName,DOB,PANNum,Address,AadharNum,mobno,emailid)
        else:

            pannum=request.form['action']
            jsondt=openaccnt(pannum,'acopen')
            Fname=jsondt[0][0]
            Mname=jsondt[0][1]
            Lname=jsondt[0][2]
            FaName=jsondt[0][3]
            DOB=jsondt[0][4]
            Address=jsondt[0][5]
            AadharNum=jsondt[0][6]
            PANNum=jsondt[0][7]
            MobNum=jsondt[0][8]
            EmailId=jsondt[0][9]
            Accno=jsondt[0][10]
            Dsp='display:none'
            messages='Your account has been created succesfully and your Account number is '+Accno
    if request.method=='POST':

        return render_template('uploaded.html',posts=0,messages=messages,messages2=messages2,Fname=Fname,Mname=Mname,Lname=Lname,FaName=FaName,DOB=DOB,Address=Address,AadharNum=AadharNum,PANNum=PANNum,MobNum=MobNum,EmailId=EmailId,Accno=Accno,Dsp=Dsp)

    else:
        return render_template('index.html',posts=0)

if __name__=='__main__':
    app.run(debug=True)
