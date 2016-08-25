from Tkinter import *
import os
import time
Path = ""
def printhello():
	global e
	Path = e.get()
	print "Enter PrintHello"
	os.system("python MemoryLeakIssueDetect.py --Logpath "+Path)

root = Tk()
root.title("Memory Leak Find")
root.geometry('400x100')
    

var = StringVar()
e = Entry(root, textvariable = var)
e.pack()
Button(root, text="press", command = printhello).pack()
print "*****************************************************"
root.mainloop()