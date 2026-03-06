# ws-agent-orchestrator
fast-api-web-sockets-agent-orchestrator

## Use
#### Set up with AWS + Claude:
`source .env`
(make sure to include `export CLAUDE_CODE_USE_BEDROCK=1`)
`aws sso login --profile <aws-profile>`

#### Venv
`source .venv/bin/activate`

#### Start websocket
`uvicorn <path.to.main>:app --reload`
The local agent builds the agent... locally. Just queries AWS for LLM + memory access
Working on the deployed agent. 

#### In second terminal
python <path.to.test.py>

