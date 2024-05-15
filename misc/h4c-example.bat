@echo off
:: This is an example of how to use hub4com (h4c) to share COM5 to various 'A' ports.
:: In this case, it works with an Icom ic-7300 standard baud rate.
:: You need the octs=off to use with physical ports.
:: hub4com is an old program and can be found here: https://sourceforge.net/p/com0com/news/2012/06/hub4com-v2100-released/
:: It is part of the com0com (cnc) null modem emulator project found here: https://com0com.sourceforge.net/
:: 
:: This work is licensed under a BSD license. It is freely distributable.
:: For more details see the license file in the root of the repository.
:: 
cd "C:\Program Files (x86)\com0com"
.\hub4com.exe --octs=off --baud=115200  --bi-route=0:All \\.\COM5 \\.\CNCA10 \\.\CNCA11 \\.\CNCA12 \\.\CNCA13 \\.\CNCA14 