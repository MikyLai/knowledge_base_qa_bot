cd `scaffold/markdown_kb`
`pip install -r requirements.txt --target vendor/`
`uvicorn app.main:app --reload`

`docker build -f scaffold/markdown_kb/Dockerfile -t $tag .`
`docker run -e OPENAI_API_KEY=$OPENAI_API_KEY -p 8000:8000 $tag`



