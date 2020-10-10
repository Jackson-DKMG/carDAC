#!/bin/bash

gpio mode 25 out

while true ; 
	do if [ -z "`ps aux | grep audacious | grep -v grep`" ]  
	then sleep 1 
	else 
	gpio write 25 1 && exit 0
	fi
done


