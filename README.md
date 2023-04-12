# mapmind

Capstone Project for Group 6 in ECE 493 W2023 at the University of Alberta

Website available at https://mapmind.herokuapp.com/

## User Guide
Use this User Guide to walk through all the functional requirements from our SRS.

1. FR#1 - Request.Registration: 
 - Navigate to https://mapmind.herokuapp.com/
 - Click on `Don't have an account?`.
 - Enter a unique username, valid and unique email (will be needed for password resetting later), and a strong password. Click `Submit`. 
2. FR#3 - Request.Log-in: 
 - Enter the username and password that you used in Step 1.
 - Click `login`
3. FR#4 - Change.Password: 
 - Once in the app, click on the gear icon in the upper right corner.
 - Click `Reset Password`. You should expect an email to your provided email address.
 - Go to the email client for the email address you provided in Step 1. (Make sure to check your spam folder) 
 - Follow the instructions in the email and the link.
4. FR#5 - Change.Username: 
 - Go back to the application. 
 - Once in the app, click on the gear icon in the upper right corner.
 - Change the username field and click `Update Username`
5. FR#6 - Change.Email: 
 - Change the email field and click `Update Email`
6. FR#8 - Create.Notebook: 
 - Click on the notebook icon in the upper right corner. (it's the second from the left icon)
 - In the uppermost input, enter a name for a new notebook. Hit `Create`.
7. FR#7 - Upload.Notes: 
 - Scroll down to the Notebooks section. Click on the name of the notebook that you wish to upload to.
 - Click on choose file and choose a .txt, .doc, or .docx file from your file system. 
 - Click 'Upload'. This may take a moment as the new machine learning model is being trained.
8. FR#9 - Edit.Notebook: 
 - First repeat the previous steps to upload another note as we will be deleting it in this step.
 - Once the new note is uploaded, click the `Delete` button to the right of the note file that you wish to delete.
9. FR#10 - Delete.Notebook: 
 - Repeat the Create.Notebook step as we will be deleting the notebook in this step.
 - Click on the name of the notebook that you wish to delete. 
 - At the bottom of the expanded section, click `Delete Notebook`.
10. FR#11 - Merge.Notebook: 
 - Repeat the Create.Notebook step as we will be merging the notebooks in this step.
 - Once several notebooks exist, CTRL + Click on all the notebooks that you wish to merge. 
 - Enter a "New Notebook Name". Click `Merge`.
11. FR#12 - Search.Word: 
 - Click on the home icon in the upper right corner. 
 - Once at the redirected page, enter space separated (alphanumeric character) words.
 - Select `Spellcheck` for spellchecking and `Search Notes Only` to search produce a visualization that contains only words that are either from your search or from your notes. 
 - Select a notebook to search in from the dropdown menu. Click `Search`. The search executes expensive algorithms and computations in the background so might take a while.
12. FR#13 - Update.Search: 
 - Once the visualization renders, repeat the previous step with a new search.
13. FR#14 - Change.Notebook: 
 - Once the visualization renders again, repeat the previous step with a new search and select a new notebook.
14. FR#15 - Visualization.Zoom: 
 - Once the visualization is rendered, you can scroll in zoom to magnify and scroll out to zoom out from the view. The other UI elements will disappear to show a full view of the visualization.
15. FR#16 - Visualization.Rotate: 
 - Once the visualization is rendered, you can press down on the arrow keys to rotate the view up, down, left and right. The other UI elements will disappear to show a full view of the visualization.
16. FR#17 - Inspect.Node: 
 - To inspect a node, click on a word. After some computation and a few seconds, a list of results will appear on the left side of the webpage.
 - Results will only appear if the word exists in your notes. Therefore, if you performed a search without the "search notes only" option, then this function may not work if most results are not from your notes.
17. FR#18 - MachineLearning.Train: 
 - This is a background functional requirement that is only visible in the backend source code. 
18. FR#19 - MachineLearning.Search: 
 - This is a background functional requirement that is only visible in the backend source code. 
19. FR#20 - MachineLearning.Visualize: 
 - This is a background functional requirement that is only visible in the backend source code. 
20. FR#2 - Delete.Account: 
 - Once you are ready to delete your account, click on the gear icon in the upper right corner. 
 - Click on the `Delete Account` button and confirm with the pop up. 

Thank you for checking out our project!
