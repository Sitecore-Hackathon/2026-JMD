![Hackathon Logo](docs/images/hackathon.png?raw=true "Hackathon Logo")
# Sitecore Hackathon 2026

- MUST READ: **[Submission requirements](SUBMISSION_REQUIREMENTS.md)**
- [Entry form template](ENTRYFORM.md)
  
## Team name
⟹ JMD 

## Category
⟹ 2.	Applied AI Within the Sitecore Execution Pipeline - Demonstrate how AI can be embedded within Sitecore execution flows to improve quality, governance, personalization, or performance.

## Description
⟹ This project explained how we can use the Sitecore Powershell Extension with integration of Open AI using Python. 
⟹ Purpose: This module helps the author and marketer to checking the context fields content - score, textstat, compare and sentiment with the help open ai before to make it live. Suppose context item
having latest 5 version and author or marketer want to check the content score of latest version which is 5 with previous version 4. This module sends/pass the all the content of Type Single-Line, Multiline
and RTE and then fetch output from Python Application (.exe) and displayed on the SPE output in terms of score, readability and suggestion etc. 



## Video link
⟹ Provide a video highlighing your Hackathon module submission and provide a link to the video. You can use any video hosting, file share or even upload the video to this repository. _Just remember to update the link below_

⟹ [Replace this Video link](#video-link)

## Pre-requisites and Dependencies
	
⟹ This module can use any sitecore architechure like XP/XM or XM cloud. We have used XM cloud - Starter project - https://github.com/Sitecore/xmcloud-starter-js with docker cli.

	Dependencies in the XM cloud: 
   a) Clone the repo - https://github.com/Sitecore-Hackathon/2026-JMD.git	  
   b) Make ensure that sitecore powershell extension installed with setting SITECORE_SPE_ELEVATION: "Allow" should be written in the docker-compose.override.yml file if local setup going on
   or added in the environment setting of cm and then redeploy.
   c) Docker desktop or docker cli should be installed on local if checking on locally.
   

   Dependencies in the Python Application:
   a) Open AI- Create a API key of open ai. https://platform.openai.com/api-keys
   b) Install the framework into Python Application
	dotenv, SequenceMatcher ,BeautifulSoup, OpenAI 


## Installation instructions
⟹ Steps on XM cloud Cloud:
1) Install the sitecore XP/XM or XM cloud on local or on cloud.
2) Make ensure that SITECORE_SPE_ELEVATION: "Allow" should be exist before setup.
Commands:
  

⟹ Steps on Python Application:
3) Source Code - \src\Python\PythonApplication1
4) Make ensure that "\authoring\platform\output" contains the output compiled file of (PythonApplication1.exe) application. XM Cloud Starter Code - https://github.com/Sitecore/xmcloud-starter-js
  NOTE - output directory need to create.
5) Rename .env.example to .env file on local and add the Open API key.  If del
5) After ran the below command and then copy paste the .exe into xm cloud platform \authoring\platform\output
   Commands:
    => pyinstaller --onefile PythonApplication1.py
	  (compiled and convert the PythonApplication1.py into .exe into /dist folder)	

After compiled and convert into PythonApplication1.exe redeploy xm cloud.


### Configuration
⟹ a) Remember to add OPENAPI_KEY into environment variable.
   b) Remember to install the SPE module of check Contet Analyer 


## Usage instructions
⟹ Provide documentation about your module, how do the users use your module, where are things located, what do the icons mean, are there any secret shortcuts etc.