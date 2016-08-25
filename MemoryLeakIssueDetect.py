# -*- coding: utf-8 -*- 
#import xlrd
#import xlwt
import time
import re
#from selenium import webdriver
import pandas as pd
#import numpy as np
import sys
import os
import argparse
import threading

reload(sys)
sys.setdefaultencoding("utf-8") #更改默认编码为utf-8

#CRs=pd.read_excel('CRList.xlsx', 'Sheet1')['CR']
TOP_NUM_PROCRANK = 8 #procrank每次打印读取的进程个数
File_Num_Folder = 3
Content_All_MemoryItem = {}
CurrentFolderPath = ""

def parse_args():
	parser = argparse.ArgumentParser()	
	#parser.add_argument('addresses',nargs = '*')	
	#parser.add_argument('filename')	
	#parser.add_argument('-p','--port', type=int)	
	#parser.add_argument('--iface', default='localhost')	
	#parser.add_argument('--delay', type=float, default=.7)	
	#parser.add_argument('--bytes', type=int, default=10)
	parser.add_argument('--Logpath', nargs = '*',default='c:\\')	
	args = parser.parse_args();
	return args

def Parse_FileDir(RootDir,Current_FolderFile=False,pattern=""):
	global CurrentFolderPath
	for path,subdir,filename in os.walk(RootDir):
		for name in filename:
			#if re.match(pattern,name) and os.path.isfile(os.path.join(path,name)) and (int(hour_line)*3600- (time.time()-os.path.getmtime(os.path.join(path,name)))>0):
			if re.match(pattern,name):# and os.path.isfile(os.path.join(path,name)):
				CurrentFolderPath = path
				yield os.path.join(path,name)
		if Current_FolderFile:
			break

def Parse_ION_Log(Logpath):
	global Content_All_MemoryItem
	file3 = file(Logpath,'r')
	for i in file3:
		if not i.split(): #删除空白行
			continue
		lineList = i.split()
		if len(lineList) != 3:
			continue
		if lineList[1] == "orphaned":
			Content_All_MemoryItem.setdefault(lineList[1],[]).append(int(lineList[-1]))
def Parse_Meminfo_Log(Logpath):
	global Content_All_MemoryItem
	file2 = file(Logpath,'r')
	for i in file2:
		if not i.split(): #删除空白行
			continue
		lineList = i.split()
		if lineList[0] == "MemAvailable:":
			Content_All_MemoryItem.setdefault(lineList[0],[]).append(int(lineList[1]))
def Parse_procrank_Log(Logpath):
	global Content_All_MemoryItem
	Count = 0
	Line = 0
	WorkFlag = 0
	file1 = file(Logpath,'r')
	for i in file1:
		Line = Line +1
		if not i.split(): #删除空白行
			continue
		lineList = i.split()
		######USS_Total&&&&Slab
		if len(lineList) == 3 and lineList[-1]=="TOTAL":
			Content_All_MemoryItem.setdefault("USS_Total",[]).append(int(lineList[-2][0:-2]))
		if lineList[0]=="RAM:" and lineList[-1]=="slab":
			Content_All_MemoryItem.setdefault("Slab",[]).append(int(lineList[-2][0:-2]))			
		######
		if len(lineList) != 6:
			continue
		if lineList[0] == 'PID': #开始检测后面Top5的占用
			WorkFlag = 1;
			Count = 0;
			continue
		if Count == TOP_NUM_PROCRANK and WorkFlag == 1:
			WorkFlag = 0
			continue
		if WorkFlag == 1 and Count < TOP_NUM_PROCRANK:	
			try:
				Content_All_MemoryItem.setdefault(lineList[5],[]).append(int(lineList[4][0:-2]))
			except Exception as e:
				print "[Exception] "+str(e)
				print lineList
		Count = Count + 1
def ExcelGen(GenLocation):
	global Content_All_MemoryItem
	print "Start Generate Excel File @ " + GenLocation
	# for key in Content_All_MemoryItem.keys():
		# print key
	Df = pd.DataFrame(range(len(Content_All_MemoryItem['system_server'])))
	for key in Content_All_MemoryItem.keys():
		Df[key] = pd.Series(Content_All_MemoryItem[key])
	del Df[0]
	Content_All_MemoryItem = {}
	ExcelGenPath = GenLocation+r'\MemoryList.xlsx'
	if os.path.exists(ExcelGenPath):
		os.remove(ExcelGenPath)
	Df.to_excel(ExcelGenPath, sheet_name='Sheet1')	
		
def main():
	global Content_All_MemoryItem
	global CurrentFolderPath
	print "Start----->"+time.ctime()
	#with file('PathConfig.txt','r') as f:
	#	PathConfig = f.readlines()
	#	PathConfig = [path.strip() for path in PathConfig]
	#print PathConfig
	Input_Path = parse_args().Logpath
	PathConfig = [path.strip() for path in Input_Path[0].split(',')]

	for RootDir in PathConfig:
		Count = 0
		print RootDir
		T1Flag = 0
		T2Flag = 0
		T3Flag = 0	
		for loglocation in Parse_FileDir(RootDir,Current_FolderFile = False,pattern="ION|meminfo|procrank"): #默认每个文件夹下只有一组要parse的数据,目前支持三个文件
			#Df = pd.DataFrame()
			######增加同一文件夹下3个文件同时处理,线程公用一个全局字典			
			#print "Parse Log--->"+loglocation		
			if re.search('ION.txt',loglocation):
				print loglocation
				t1 = threading.Thread(target=Parse_ION_Log,args=(loglocation,))
				t1.setDaemon(True)
				t1.start()
				T1Flag = 1
				#Parse_ION_Log(loglocation)
				Count = Count +1
			elif re.search('meminfo.txt',loglocation):
				print loglocation
				t2 = threading.Thread(target=Parse_Meminfo_Log,args=(loglocation,))
				t2.setDaemon(True)
				t2.start()
				T2Flag = 1
				#Parse_Meminfo_Log(loglocation)
				Count = Count +1
			else:
				print loglocation
				t3 = threading.Thread(target=Parse_procrank_Log,args=(loglocation,))
				t3.setDaemon(True)
				t3.start()
				T3Flag = 1
				#Parse_procrank_Log(loglocation)
				Count = Count +1
			if Count == File_Num_Folder:
				if T1Flag:
					t1.join()
				if T2Flag:
					t2.join()
				if T3Flag:
					t3.join()
				ExcelGen(CurrentFolderPath)
				Count = 0
				T1Flag = 0
				T2Flag = 0
				T3Flag = 0					
	print "Finish----->"+time.ctime()
	os.system("pause")
if __name__ == "__main__":
    main()