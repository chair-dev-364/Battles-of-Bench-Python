@echo off
if [%2]==[/d] echo.
chcp 65001>nul


for /f %%a in ('cscript //nologo len.vbs "%1"') do (set length=%%a)
set input=%1

if %length%==1 (goto len1)
if %length%==2 (goto len2)
if %length%==3 (goto len3)
exit /b 1

:len1
set firstchar=%input:~0,1%
if %firstchar%==1 (
	set fc1=    ██  
	set fc2=  ████  
	set fc3=██  ██  
	set fc4=    ██  
	set fc5=  ██████
)

if %firstchar%==2 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=    ██  
	set fc4=  ██    
	set fc5=████████
)

if %firstchar%==3 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=   ███  
	set fc4=██    ██
	set fc5=  ████  
)

if %firstchar%==4 (
	set fc1=██    ██
	set fc2=██    ██
	set fc3=████████
	set fc4=      ██
	set fc5=      ██
)

if %firstchar%==5 (
	set fc1=████████
	set fc2=██      
	set fc3=██████  
	set fc4=      ██
	set fc5=██████  
)

if %firstchar%==6 (
	set fc1=  █████ 
	set fc2=██      
	set fc3=██████  
	set fc4=██    ██
	set fc5=  ████  
)

if %firstchar%==7 (
	set fc1=████████
	set fc2=      ██
	set fc3=    ██  
	set fc4=  ██    
	set fc5=  ██    
)

if %firstchar%==8 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=  ████  
	set fc4=██    ██
	set fc5=  ████  
)

if %firstchar%==9 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=  ██████
	set fc4=      ██
	set fc5= █████  
)

if %firstchar%==0 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=██    ██
	set fc4=██    ██
	set fc5=  ████  
)

if /i [%2]==[/d] echo %fc1%
if /i [%2]==[/d] echo %fc2%
if /i [%2]==[/d] echo %fc3%
if /i [%2]==[/d] echo %fc4%
if /i [%2]==[/d] echo %fc5%
exit /b 0


:len2
set firstchar=%input:~0,1%
set secondchar=%input:~1,1%

if %firstchar%==1 (
	set fc1=    ██  
	set fc2=  ████  
	set fc3=██  ██  
	set fc4=    ██  
	set fc5=  ██████
)

if %firstchar%==2 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=    ██  
	set fc4=  ██    
	set fc5=████████
)

if %firstchar%==3 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=   ███  
	set fc4=██    ██
	set fc5=  ████  
)

if %firstchar%==4 (
	set fc1=██    ██
	set fc2=██    ██
	set fc3=████████
	set fc4=      ██
	set fc5=      ██
)

if %firstchar%==5 (
	set fc1=████████
	set fc2=██      
	set fc3=██████  
	set fc4=      ██
	set fc5=██████  
)

if %firstchar%==6 (
	set fc1=  █████ 
	set fc2=██      
	set fc3=██████  
	set fc4=██    ██
	set fc5=  ████  
)

if %firstchar%==7 (
	set fc1=████████
	set fc2=      ██
	set fc3=    ██  
	set fc4=  ██    
	set fc5=  ██    
)

if %firstchar%==8 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=  ████  
	set fc4=██    ██
	set fc5=  ████  
)

if %firstchar%==9 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=  ██████
	set fc4=      ██
	set fc5= █████  
)

if %firstchar%==0 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=██    ██
	set fc4=██    ██
	set fc5=  ████  
)

if %secondchar%==1 (
	set sc1=    ██  
	set sc2=  ████  
	set sc3=██  ██  
	set sc4=    ██  
	set sc5=  ██████
)

if %secondchar%==2 (
	set sc1=  ████  
	set sc2=██    ██
	set sc3=    ██  
	set sc4=  ██    
	set sc5=████████
)

if %secondchar%==3 (
	set sc1=  ████  
	set sc2=██    ██
	set sc3=   ███  
	set sc4=██    ██
	set sc5=  ████  
)

if %secondchar%==4 (
	set sc1=██    ██
	set sc2=██    ██
	set sc3=████████
	set sc4=      ██
	set sc5=      ██
)

if %secondchar%==5 (
	set sc1=████████
	set sc2=██      
	set sc3=██████  
	set sc4=      ██
	set sc5=██████  
)

if %secondchar%==6 (
	set sc1=  █████ 
	set sc2=██      
	set sc3=██████  
	set sc4=██    ██
	set sc5=  ████  
)

if %secondchar%==7 (
	set sc1=████████
	set sc2=      ██
	set sc3=    ██  
	set sc4=  ██    
	set sc5=  ██    
)

if %secondchar%==8 (
	set sc1=  ████  
	set sc2=██    ██
	set sc3=  ████  
	set sc4=██    ██
	set sc5=  ████  
)

if %secondchar%==9 (
	set sc1=  ████  
	set sc2=██    ██
	set sc3=  ██████
	set sc4=      ██
	set sc5= █████  
)

if %secondchar%==0 (
	set sc1=  ████  
	set sc2=██    ██
	set sc3=██    ██
	set sc4=██    ██
	set sc5=  ████  
)

if /i [%2]==[/d] echo %fc1% %sc1%
if /i [%2]==[/d] echo %fc2% %sc2%
if /i [%2]==[/d] echo %fc3% %sc3%
if /i [%2]==[/d] echo %fc4% %sc4%
if /i [%2]==[/d] echo %fc5% %sc5%


exit /b 0

:len3
set firstchar=%input:~0,1%
set secondchar=%input:~1,1%
set thirdchar=%input:~2,1%

if %firstchar%==1 (
	set fc1=    ██  
	set fc2=  ████  
	set fc3=██  ██  
	set fc4=    ██  
	set fc5=  ██████
)

if %firstchar%==2 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=    ██  
	set fc4=  ██    
	set fc5=████████
)

if %firstchar%==3 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=   ███  
	set fc4=██    ██
	set fc5=  ████  
)

if %firstchar%==4 (
	set fc1=██    ██
	set fc2=██    ██
	set fc3=████████
	set fc4=      ██
	set fc5=      ██
)

if %firstchar%==5 (
	set fc1=████████
	set fc2=██      
	set fc3=██████  
	set fc4=      ██
	set fc5=██████  
)

if %firstchar%==6 (
	set fc1=  █████ 
	set fc2=██      
	set fc3=██████  
	set fc4=██    ██
	set fc5=  ████  
)

if %firstchar%==7 (
	set fc1=████████
	set fc2=      ██
	set fc3=    ██  
	set fc4=  ██    
	set fc5=  ██    
)

if %firstchar%==8 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=  ████  
	set fc4=██    ██
	set fc5=  ████  
)

if %firstchar%==9 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=  ██████
	set fc4=      ██
	set fc5= █████  
)

if %firstchar%==0 (
	set fc1=  ████  
	set fc2=██    ██
	set fc3=██    ██
	set fc4=██    ██
	set fc5=  ████  
)

if %secondchar%==1 (
	set sc1=    ██  
	set sc2=  ████  
	set sc3=██  ██  
	set sc4=    ██  
	set sc5=  ██████
)

if %secondchar%==2 (
	set sc1=  ████  
	set sc2=██    ██
	set sc3=    ██  
	set sc4=  ██    
	set sc5=████████
)

if %secondchar%==3 (
	set sc1=  ████  
	set sc2=██    ██
	set sc3=   ███  
	set sc4=██    ██
	set sc5=  ████  
)

if %secondchar%==4 (
	set sc1=██    ██
	set sc2=██    ██
	set sc3=████████
	set sc4=      ██
	set sc5=      ██
)

if %secondchar%==5 (
	set sc1=████████
	set sc2=██      
	set sc3=██████  
	set sc4=      ██
	set sc5=██████  
)

if %secondchar%==6 (
	set sc1=  █████ 
	set sc2=██      
	set sc3=██████  
	set sc4=██    ██
	set sc5=  ████  
)

if %secondchar%==7 (
	set sc1=████████
	set sc2=      ██
	set sc3=    ██  
	set sc4=  ██    
	set sc5=  ██    
)

if %secondchar%==8 (
	set sc1=  ████  
	set sc2=██    ██
	set sc3=  ████  
	set sc4=██    ██
	set sc5=  ████  
)

if %secondchar%==9 (
	set sc1=  ████  
	set sc2=██    ██
	set sc3=  ██████
	set sc4=      ██
	set sc5= █████  
)

if %secondchar%==0 (
	set sc1=  ████  
	set sc2=██    ██
	set sc3=██    ██
	set sc4=██    ██
	set sc5=  ████  
)

if %thirdchar%==1 (
	set tc1=    ██  
	set tc2=  ████  
	set tc3=██  ██  
	set tc4=    ██  
	set tc5=  ██████
)

if %thirdchar%==2 (
	set tc1=  ████  
	set tc2=██    ██
	set tc3=    ██  
	set tc4=  ██    
	set tc5=████████
)

if %thirdchar%==3 (
	set tc1=  ████  
	set tc2=██    ██
	set tc3=   ███  
	set tc4=██    ██
	set tc5=  ████  
)

if %thirdchar%==4 (
	set tc1=██    ██
	set tc2=██    ██
	set tc3=████████
	set tc4=      ██
	set tc5=      ██
)

if %thirdchar%==5 (
	set tc1=████████
	set tc2=██      
	set tc3=██████  
	set tc4=      ██
	set tc5=██████  
)

if %thirdchar%==6 (
	set tc1=  █████ 
	set tc2=██      
	set tc3=██████  
	set tc4=██    ██
	set tc5=  ████  
)

if %thirdchar%==7 (
	set tc1=████████
	set tc2=      ██
	set tc3=    ██  
	set tc4=  ██    
	set tc5=  ██    
)

if %thirdchar%==8 (
	set tc1=  ████  
	set tc2=██    ██
	set tc3=  ████  
	set tc4=██    ██
	set tc5=  ████  
)

if %thirdchar%==9 (
	set tc1=  ████  
	set tc2=██    ██
	set tc3=  ██████
	set tc4=      ██
	set tc5= █████  
)

if %thirdchar%==0 (
	set tc1=  ████  
	set tc2=██    ██
	set tc3=██    ██
	set tc4=██    ██
	set tc5=  ████  
)


if /i [%2]==[/d] echo %fc1% %sc1% %tc1%
if /i [%2]==[/d] echo %fc2% %sc2% %tc2%
if /i [%2]==[/d] echo %fc3% %sc3% %tc3%
if /i [%2]==[/d] echo %fc4% %sc4% %tc4%
if /i [%2]==[/d] echo %fc5% %sc5% %tc5%
exit /b 0