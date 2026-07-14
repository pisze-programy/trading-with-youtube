# Trading with YouTube

## TLDR
Finding correlations between YouTube influencers' predictions and real market movements.

## About
In various places on the internet, we encounter investment experts who share their opinions. Let's see how these predictions age over time.

A new episode might appear next week - nobody remembers what happened last week. Gathering data and visualizing it will make it easy to check if an influencer's prediction or suggestion made sense.

What if we add top news from internet newspapers? It might turn out that some influencers are promoting the same popular, incorrect opinions about market direction.

Recently, prediction markets have become popular - people bet their money trying to estimate risk for a given event (predicting the future). If we add daily market movements from Polymarket to our dataset, it may turn out that combining news and prediction markets either contradicts or aligns with influencer opinions. I'm looking for this correlation.

## Project Structure

This project combines multiple data sources to analyze financial trends and predictions:

- Analysis prompts for data processing
- Data analysis agents
- Backend to store the data
- Data visualization in the form of charts and tables showing related data

## How to Use

1. Run the FastAPI server:
   ```
   uvicorn app.main:app --reload
   ```

2. Send a POST request to `/analyze_video` with a YouTube URL:
   ```json
   {
     "url": "https://www.youtube.com/watch?v=example"
   }
   ```

3. Results will be persisted as JSON files under the
`DATA_DIR` directory. Each YouTube channel has its own file named after
the channel name – new analyses are appended to that file.

## Prompt Templates

The application uses template-based prompting where:
- The `prompt` parameter accepts a template string that can include a `{transcript}` placeholder  
- When the analysis runs, the actual transcript content is inserted into this placeholder
- Your custom prompt is used as the base template with transcript content injected as context

Example custom prompts:
```json
{
  "url": "https://www.youtube.com/watch?v=example"
}
```

If no `{transcript}` placeholder is included in your prompt, the transcript will be appended at the end of the prompt as context.

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the project root with the following settings:

```
# Ollama API Configuration
OLLAMA_API_URL=$url
OLLAMA_MODEL=$model

# Data Directory
DATA_DIR=data

# WebshareProxyConfig
# https://dashboard.webshare.io/proxy/settings
PROXY_USERNAME=
PROXY_PASSWORD=
```

## STACK

- FastAPI for the web server
- youtube-transcript-api for fetching transcripts  
- Ollama for AI analysis
- JSON file storage per channel

## TODO
- WebshareProxyConfig Integration

## License

Do whatever you want.