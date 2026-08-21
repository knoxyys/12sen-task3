# Stirling 12SEN Task 3

### commands to run:
pip install opencv-python  
pip install pillow  
pip install pyzbar  
brew install zbar (annoying macos dependancy fix)  

hopefully things dont break! it works for me now but let me know if any issues arise

### HOW IT WORKS!
1. create sample db by running fill_role.py
2. run app.py to start the GUI
3. reset database (by either deleting the db file or using the debug button) to simulate a new period
4. repeat

### ai statement / acknowledgement:
- most simple database queries were made by me, i started giving up on the more complex ones like get_latest_user_states because claude can help me do it so much more efficiently
- most of the python 'framework' was made by me. as the project got more complex, i relied more on ai to keep my logic in check and to help with debugging
- the initial barcode scanning method was entirely ai due to its complexity and its error prone nature. i made an initial script (simple_barcode.py, shown in earlier github commits) that took ages to work properly due to multiple constraints and issues with barcode types, macbook libraries, etc etc. once the initial script (fully ai) was working, i used this script as a base to understand how it works and then implement a version into my app by hand