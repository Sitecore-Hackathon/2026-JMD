![Hackathon Logo](docs/images/hackathon.png?raw=true "Hackathon Logo")
# Sitecore Hackathon 2026

- MUST READ: **[Submission requirements](SUBMISSION_REQUIREMENTS.md)**
- [Entry form template](ENTRYFORM.md)
  
## Team name
⟹ JMD 

## Category

⟹ 2.Applied AI Within the Sitecore Execution Pipeline

## Description

⟹ This project demonstrates how AI can be integrated into the Sitecore authoring workflow using Sitecore PowerShell Extensions (SPE) and OpenAI through a Python service. 

⟹ Purpose: The solution allows content authors and marketers to analyze the quality of their content before publishing it live.

The module evaluates Sitecore content fields such as:
- Single-Line Text
- Multi-Line Text
- Rich Text (RTE)

The system performs AI-based analysis including:
- Engagement score
- SEO score
- Sentiment analysis
- Version comparison
- AI suggestions for improvement

Example Scenario
If a Sitecore item has multiple versions, the author may want to compare:
Version 5 (current)
Version 4 (previous)


The module collects content from both versions and sends it to the Python AI analysis service.

The AI then analyzes the content and returns results including:
- Field-level engagement score
- Field-level SEO score
- Field-level sentiment
- SEO improvement suggestions
- Content quality suggestions

The results are displayed in Sitecore PowerShell output as a structured grid, allowing authors to immediately evaluate and improve content quality.


## Video link
⟹ https://www.youtube.com/watch?v=GFrXf7qifJw

## How to use :Open a Sitecore item containing text fields such as:

l Title

2 Rich Text

3 Multi-Line Text

4 Run the AI Content Analyzer PowerShell script.

### The script will:

l fetch current values

2 fetch previous version values

3 skip fields where both values are empty

4 call the hosted AI service

5 display results in a single Sitecore grid


### Review the results:

l Field Engagement

2 Field SEO

3 Field Sentiment

4 SEO Suggestions

5 Content Suggestions


## Expected Output

 The final analysis grid shows:

1 Item Name

2 Field Name

3 Current Value

4 Previous Value

5 Field Engagement

6 Field SEO

7 Field Sentiment

8 SEO Suggestions

9 Content Suggestions

l0 This gives authors field-level insights directly inside Sitecore


## Pre-requisites and Dependencies
	
⟹ Sitecore XM Cloud - Installed starter kit
- Sitecore PowerShell Extensions installed - Access to content items with versioned text fields

⟹ Hosted AI API
- The solution uses a Python FastAPI service that performs AI analysis. API KEY - https://content-analyzer-api.onrender.com/analyze API KEY Health - https://content-analyzer-api.onrender.com/health

### External dependencies 

  - OpenAI API is used by the hosted Python service 
  - Render is used for API hosting
    

## Installation instructions
⟹ Steps for setup XM cloud Cloud:

1) Use an existing Sitecore environment where Sitecore PowerShell Extensions is available. This project does not require judges to run Python locally because the AI service is already hosted publicly.

2) Install Sitecore package "Sitecore Content AI analyzer.zip" from path "\src\Sitecore Package\" and install it. 
 Then add the provided PowerShell script into Sitecore PowerShell ISE / Script Library.

The script: 
- reads the current item 
- reads the previous version 
- identifies analyzable fields 
- sends content to the hosted AI API 
- displays the analysis in a single grid
  

3) Update the script
Go to powershell ISE module --> Settings Tab --> Run script of content editor for ribbon

4) Go to Content Editor and Content Analyzer button would be available. Go to any item and click to know the scores and suggestions.

5) Output - This helps authors quickly identify weak content and improve it before publishing.

Architecture

Sitecore Authoring

|

| Sitecore PowerShell Script

v

Hosted FastAPI AI Service

|

v

## Flow

1. Author runs the script from Sitecore
2. Script collects current and previous values
3. Content is sent to the hosted AI API
4. AI analyzes the content
5. Structured results are returned
6. Results are shown in Sitecore


### Notes for Judges

l. No local Python setup is required for evaluation.

2. The AI service is already hosted publicly.

3. Judges only need:

4. Sitecore environment

5. Sitecore PowerShell Extensions

6. the provided PowerShell script

7. the hosted API URL

8. This keeps setup simple and avoids unnecessary installation complexity.

### Future Enhancements

1. Possible future improvements include:
2. Page-level analysis across renderings/components
3. Readability scoring
4. Keyword density analysis
5. AI-assisted rewrite suggestions
6. Editorial workflow gating
7. Marketplace packaging

### Configuration
⟹ 

## Usage instructions
⟹ This module help the author and marketer to increase the lead and save the content which is more appropriate for lead generation with the help of GPT-4.0. Also it help to do such a kind of a/b testing
of content of two versions of item.



![Hackathon Logo](docs/images/hackathon.png?raw=true "Hackathon Logo")

You can embed images of different formats too:

![Deal With It](docs/images/deal-with-it.gif?raw=true "Deal With It")

And you can embed external images too:

![Random](https://thiscatdoesnotexist.com/)

## Comments
This project was built for Sitecore Hackathon 2026 to demonstrate practical AI integration inside the Sitecore execution pipeline.