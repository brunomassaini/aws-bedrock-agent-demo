# Product Requirements Document: AWS Bedrock Discord Agent

## Overview
A personal assistant Discord bot powered by AWS Bedrock agent using Amazon Nova Lite model. The assistant helps a single user with daily tasks, maintains context about the user's life, preferences, and ongoing projects, and provides helpful responses based on both recent conversation context and long-term memory.

## Core Requirements

### 1. AWS Bedrock Agent Configuration
- **Model**: `amazon.nova-lite-v1:0`
- **Agent Type**: Personal assistant agent
- **Hosting**: AWS Bedrock Agents service
- **Region**: `us-east-1` (recommended for Bedrock availability)
- **Agent Capabilities**:
  - Task and reminder management
  - Information lookup and research
  - Context-aware conversations
  - Proactive suggestions based on user patterns
  - Note-taking and information organization

### 2. Discord Integration
- **Bot Type**: Discord bot application
- **User Scope**: Single user (1:1 conversation only)
- **Authentication**: Discord bot token + user ID whitelist
- **Interaction Model**: 
  - Responds to direct messages only
  - Slash commands for memory management:
    - `/reset` - Clear current conversation context
    - `/remember <text>` - Manually save something to long-term memory
    - `/recall <query>` - Search long-term memory
    - `/forget <query>` - Remove from long-term memory
    - `/status` - Show context status (time remaining, memory stats)

### 3. Memory System

#### Short-term Memory (Conversation Context)
- **Duration**: 10 minutes from last interaction
- **Storage**: Bedrock Sessions (built-in)
  - Managed automatically by Bedrock
  - No Redis or cache infrastructure needed
  - Session ID: Discord user ID
  - TTL: 600 seconds (10 minutes)
- **Content**: Full conversation history including:
  - User messages
  - Agent responses
  - Timestamps
  - Turn-by-turn context
- **Behavior**: After 10 minutes of inactivity, Bedrock automatically expires session

#### Long-term Memory (Persistent)
- **Storage**: Bedrock Memory (built-in for agents)
  - Automatically managed by Bedrock
  - No DynamoDB setup required
  - Agent-native memory system
  - Semantic search built-in

- **Memory Management**:
  - **Automatic Extraction**: Agent autonomously decides what to remember
    - Analyzes conversations for important information
    - Identifies user preferences, facts, recurring patterns
    - Stores memories with semantic understanding
  - **Manual Storage**: User can explicitly request
    - `/remember <text>` command
    - "Remember that..." in conversation
    - Agent confirms what was stored
  - **Retrieval**: Bedrock automatically surfaces relevant memories
    - Semantic similarity to current conversation
    - Context-aware recall
    - No manual query needed (but `/recall` command available)

- **Content Categories** (Agent learns to organize):
  - **User Profile**: Name, preferences, communication style, timezone
  - **Personal Facts**: Family, interests, habits, important dates
  - **Tasks & Goals**: What user is working on, priorities
  - **Preferences**: How user likes things done
  - **Context**: Past conversations, decisions, reasons

- **Note**: Bedrock Memory is persistent and survives session expiration
  - Memories carry over indefinitely
  - Agent references past conversations naturally
  - No manual memory management infrastructure needed

### 4. Agent Instructions
- **System Prompt**: 
  ```
  You are a personal assistant helping your user with daily tasks, information management, 
  and thoughtful conversation. You are proactive, organized, and maintain context about 
  the user's life, preferences, and ongoing projects.
  
  Personality: Helpful, concise, friendly but professional. Adapt tone to user's style.
  
  Core Responsibilities:
  - Help manage tasks, reminders, and deadlines
  - Remember important information and recall it when relevant
  - Provide information and research assistance
  - Offer proactive suggestions based on patterns and context
  - Organize notes and track projects
  
  Guidelines:
  - Ask clarifying questions when user intent is unclear
  - Proactively suggest relevant information from memory
  - Be concise by default, detailed when requested
  - Respect privacy and never share user information
  - Admit when you don't know something rather than guessing
  ```
- **Context Sources** (in priority order):
  1. Agent base instructions (system prompt)
  2. User profile from long-term memory (always loaded)
  3. Short-term conversation context (if within 10 minutes)
  4. Relevant long-term memories (semantic search based on current query)
  5. Active tasks and reminders (always loaded)

## Architecture Components

### Infrastructure

#### Compute Layer
- **Discord Gateway Handler**: Small Python application with persistent WebSocket connection
  - **Option A (Recommended)**: Run locally on your machine
    - Simple Python script using discord.py
    - Always-on connection to Discord Gateway
    - Calls Lambda function for each message
    - ~50MB RAM, negligible CPU
    - Free (uses your local machine)
  - **Option B**: ECS Fargate container
    - Same Python app, runs in AWS
    - Fargate Spot: ~$5-10/month
    - Better uptime, no local dependency
  - **Option C**: Lambda with Container Image (not recommended for WebSocket)
    - Complex, requires workarounds for persistent connection
  
- **Message Processing**: AWS Lambda (Python 3.12)
  - Function: `process-discord-message`
  - Trigger: Direct invocation from Gateway handler
  - Timeout: 60 seconds
  - Memory: 512 MB
  - Job: Invoke Bedrock agent, handle response

#### Memory & Session Management
- **Bedrock Sessions**: Built-in conversation context management
  - Maintains conversation history automatically
  - Session TTL: 10 minutes (configurable via `sessionTTL`)
  - No Redis needed - Bedrock handles this natively
  - Session ID: Use Discord user ID for consistency

- **Bedrock Memory**: Built-in long-term memory for agents
  - Automatic memory extraction from conversations
  - Agent decides what's important to remember
  - Manual memory via explicit user commands
  - Semantic search built-in
  - No DynamoDB needed - Bedrock stores everything
  - Memory retention: Persistent across sessions

#### Storage
- **Secrets**: AWS Secrets Manager
  - Discord bot token
  - Discord user ID (authorized user whitelist)

#### Optional Components
- **DynamoDB**: Only if you need custom task/reminder storage
  - Not needed for conversational memory (Bedrock handles it)
  - Could use for: task status, reminder schedules, custom metadata
  - Recommendation: Start without it, add only if needed

### AWS Services
- ✅ **Amazon Bedrock** (Agents + Runtime)
  - Model: `amazon.nova-lite-v1:0`
  - Memory: Built-in agent memory (stores long-term context)
  - Sessions: Built-in session management (10-minute context)
  - No embeddings service needed - handled internally
- ✅ **AWS Lambda** (message processing)
- ✅ **Secrets Manager** (Discord credentials)
- ✅ **CloudWatch** (logs, metrics, alarms)
- ✅ **IAM** (roles and policies)
- [ ] **DynamoDB** (optional - only for task/reminder metadata)
- [ ] **EventBridge** (optional - for scheduled reminders)
- [ ] **SNS** (optional - for alerts)

### External Services
- **Discord API**: Using discord.py library (Python)
  - Gateway intents: Direct Messages, Message Content
  - Privileged intents required: Message Content Intent

## Functional Requirements

### FR-1: Message Reception
- Bot receives Discord messages from the authorized user
- Messages are validated and sanitized
- Rate limiting applied [TBD - max messages per minute?]

### FR-2: Context Management
- Bedrock automatically manages session context
- Session ID: Discord user ID (consistent across conversations)
- If < 10 minutes: Bedrock loads existing session context
- If > 10 minutes: Bedrock starts new session, but long-term memory persists
- No manual cache management needed

### FR-3: Agent Invocation
- Lambda calls Bedrock InvokeAgent API with:
  - Agent ID and alias
  - Session ID (Discord user ID)
  - User input (Discord message)
  - Session attributes (optional metadata)
- Bedrock handles:
  - Loading session context (if < 10 min)
  - Loading relevant long-term memories
  - Invoking Nova Lite model
  - Extracting new memories (if important info detected)
  - Storing updated session state
- Lambda receives streaming response
- Response formatted and sent to Discord

### FR-4: Memory Persistence
- **Automatic (Bedrock-managed)**:
  - After each interaction, Bedrock agent autonomously decides what to remember
  - Agent analyzes conversation for important information:
    - Personal facts ("My birthday is...", "I live in...")
    - Preferences ("I prefer...", "I don't like...")
    - Important context ("I'm working on...", "My goal is...")
  - Memories stored in Bedrock Memory with semantic understanding
  - Optional: Agent can ask "Should I remember that [X]?" for confirmation
  
- **Manual (User-triggered)**:
  - User uses `/remember <text>` command or says "remember this"
  - Agent explicitly stores the specified content
  - Confirmation message: "I've remembered: [X]"
  
- **Retrieval (Automatic)**:
  - Bedrock automatically retrieves relevant memories based on current conversation
  - No manual memory injection needed
  - Agent naturally references past conversations and facts

### FR-5: Response Delivery
- Agent response sent back to Discord user
- Handle Discord message length limits (2000 chars):
  - Auto-split long responses into multiple messages
  - Use Discord embeds for structured content (tasks, notes)
- Rich formatting support:
  - Discord embeds for task lists, memory summaries
  - Code blocks for technical content
  - Reactions for quick confirmations (✅, ❌, 🔔 for reminders)
  - Typing indicator while processing

### FR-6: Memory Management Commands
- `/remember <text>` - Explicitly save to long-term memory
- `/recall <query>` - Ask agent to retrieve specific memories
- `/forget <query>` - Ask agent to forget specific information
- `/status` - Show session status (time remaining in session)

### FR-7: Task & Reminder Management
- Create tasks from natural language ("remind me to call John tomorrow at 2pm")
- EventBridge scheduled rules trigger reminder notifications
- Task status tracking (pending, completed, overdue)
- Proactive reminders sent via DM when time arrives

## Non-Functional Requirements

### Performance
- Response time: < 5 seconds for typical queries
- Cache read latency: < 100ms
- Database read latency: < 500ms

### Reliability
- Error handling for:
  - Bedrock API failures
  - Discord API rate limits
  - Cache/database unavailability
- Retry logic with exponential backoff
- Dead letter queue for failed messages

### Security
- Discord bot token stored in Secrets Manager (auto-rotation enabled)
- User ID validation (only authorized user can interact)
- DynamoDB encryption at rest (AWS managed keys)
- ElastiCache encryption in-transit (TLS enabled)
- IAM least-privilege policies:
  - Lambda execution role: Bedrock invoke, DynamoDB read/write, ElastiCache access, Secrets read, CloudWatch logs
  - No internet access required if using VPC endpoints
- VPC isolation (optional but recommended):
  - Lambda in private subnets
  - VPC endpoints for Bedrock, DynamoDB, Secrets Manager
  - NAT Gateway not required
- Input validation and sanitization for all user messages
- Rate limiting per user (10 messages per minute)

### Cost Optimization
- Use serverless architecture (Lambda, Bedrock-managed storage)
- No ElastiCache needed (Bedrock sessions are free)
- No DynamoDB needed (Bedrock memory is included)
- Implement request throttling (10 msg/min = ~300 messages/day max)
- Local Discord Gateway handler (free - runs on your machine)
  - Alternative: Fargate Spot (~$5-10/month if you want it always-on in AWS)
- **Estimated Monthly Cost**:
  - Lambda: ~$1 (minimal invocations, low duration)
  - Bedrock Nova Lite: ~$5-15 (depends on usage)
    - Input: $0.00006 per 1K tokens
    - Output: $0.00024 per 1K tokens
    - Typical conversation: 10-20 messages/day = $5-10/month
  - Bedrock Memory: Included (no additional charge)
  - Bedrock Sessions: Included (no additional charge)
  - Secrets Manager: ~$0.40/month (1 secret)
  - CloudWatch: ~$0.50/month (logs and metrics)
  - **Total: ~$7-17/month** (or ~$12-27/month with Fargate)
- CloudWatch budget alarm at $30/month threshold

### Monitoring & Observability
- CloudWatch Logs for all interactions
  - Structured logging with JSON format
  - Log groups: `/aws/lambda/discord-bot-handler`
  - Retention: 30 days
- **CloudWatch Metrics**:
  - Message count per day
  - Average response time (P50, P95, P99)
  - Error rate (by error type)
  - Cache hit/miss rate
  - Memory operations (create, read, update)
  - Bedrock invocation count and latency
  - Active conversation sessions
- **CloudWatch Alarms** → SNS notifications:
  - Error rate > 10% over 5 minutes
  - Response time P95 > 10 seconds
  - Lambda timeout rate > 5%
  - Monthly cost > $50
  - ElastiCache connection failures
- **CloudWatch Dashboard**: Single-pane view of all key metrics

## Agent Capabilities & Tools

### Core Capabilities
1. **Conversational AI**: Natural language understanding and generation via Nova Lite
2. **Automatic Memory**: Bedrock agent autonomously stores and retrieves relevant information
3. **Context Maintenance**: 10-minute conversation sessions maintained by Bedrock
4. **Personal Assistant Tasks**: Answers questions, helps organize thoughts, provides information

### Bedrock Agent Configuration

#### Memory Configuration
```json
{
  "memoryConfiguration": {
    "enabledMemoryTypes": ["SESSION_SUMMARY"],
    "storageDays": 365
  }
}
```

#### Optional Action Groups (if task management needed)
If you want structured task/reminder management beyond conversational memory, you can add Lambda-based action groups:

**Task Management Action Group** (Optional):
- `create_task(description, due_date, priority)` - Store task in DynamoDB
- `list_tasks(status_filter)` - Retrieve active tasks
- `complete_task(task_id)` - Mark task done
- `set_reminder(task_id, reminder_time)` - Schedule EventBridge notification

**Note**: For MVP, agent can manage tasks conversationally through memory without action groups:
- User: "I need to call Sarah tomorrow at 2pm"
- Agent: "I'll remember that. I'll remind you tomorrow about calling Sarah at 2pm."
- Agent stores this in memory
- User asks next day: "What do I need to do today?"
- Agent: "You mentioned you need to call Sarah at 2pm today."

**Action groups only needed if**:
- You want system-triggered reminders (EventBridge sending DMs at specific times)
- You need structured task tracking outside conversational memory
- You want to integrate with external systems (calendar, task manager APIs)

### Recommended MVP Approach
1. **Start simple**: No action groups, pure conversational agent with Bedrock memory
2. **Test**: See if conversational task tracking meets your needs
3. **Add later**: Implement task action group + EventBridge only if needed

## Deployment

### Environments
- **Development**: Local testing with LocalStack/SAM Local
- **Production**: Single production environment (sufficient for personal use)

### Deployment Method
- **Infrastructure as Code**: AWS CDK (Python)
  - Enables type-safe infrastructure definition
  - Easy local testing and iteration
  - Built-in best practices
- **CI/CD**: GitHub Actions (optional for personal project)
  - Manual deployment with `cdk deploy` is acceptable
  - Or: GitHub Actions workflow on push to `main` branch

### Configuration Management
Environment variables stored in Lambda configuration:
- `DISCORD_BOT_TOKEN_SECRET_ARN` - Secret Manager ARN
- `AUTHORIZED_USER_ID` - Discord user ID (whitelist)
- `CONTEXT_TTL_SECONDS` - 600 (10 minutes)
- `BEDROCK_MODEL_ID` - amazon.nova-lite-v1:0
- `BEDROCK_AGENT_ID` - Generated agent ID
- `BEDROCK_AGENT_ALIAS_ID` - Agent alias
- `AWS_REGION` - us-east-1
- `DYNAMODB_TABLE_NAME` - assistant-memory
- `REDIS_ENDPOINT` - ElastiCache cluster endpoint
- `REDIS_PORT` - 6379
- `LOG_LEVEL` - INFO

### Deployment Steps
1. Create Discord bot application and get token
2. Request Bedrock model access for Nova Lite
3. Deploy infrastructure with CDK: `cdk deploy`
4. Configure Discord bot in developer portal
5. Enable privileged intents (Message Content)
6. Store Discord token in Secrets Manager
7. Test bot with DM to authorized user

## Open Questions & Decisions Needed

### Architecture Decisions
1. **Connection Model**: 
   - Option A: Discord Gateway (WebSocket) - Real-time, requires persistent connection
     - Implementation: Long-running Lambda container or ECS Fargate
     - Pros: Instant message delivery, better for reminders
     - Cons: More complex, higher cost
   - Option B: Discord Interactions (HTTP) - Event-driven, serverless
     - Implementation: Lambda with API Gateway
     - Pros: Simpler, cheaper, true serverless
     - Cons: 3-second response timeout (need to ACK and followup)
   - **Recommendation**: Start with Gateway for better UX, can optimize later

2. **Semantic Search**:
   - Option A: Amazon OpenSearch Serverless (~$700/month)
   - Option B: Pgvector in RDS (~$20/month but more complex)
   - Option C: In-memory FAISS + periodic reindex (free but limited scale)
   - Option D: No semantic search, use DynamoDB scan with keyword matching
   - **Recommendation**: Start without semantic search (Option D), add later if needed

3. **Embeddings Strategy**:
   - If implementing semantic search:
     - Generate embeddings on memory save
     - Store in vector database
     - Query with similarity search
   - If not: Use DynamoDB query with tags and keyword matching

### Feature Scope
4. **Multi-modal Support**: 
   - Should bot handle image uploads? (e.g., "remember this screenshot")
   - Should bot generate images? (probably not needed for assistant)
   - **Recommendation**: Text-only MVP, add multi-modal later if needed

5. **Proactive Reminders**:
   - EventBridge schedules for time-based reminders
   - Lambda function to check upcoming tasks and send DMs
   - Frequency: Every 15 minutes scan for tasks due in next hour
   - **Decision needed**: Should this be included in MVP?

6. **Conversation Summarization**:
   - After 10-minute context expires, should we save a summary?
   - Helps maintain continuity across sessions
   - Stored as `type: pattern` memory
   - **Recommendation**: Include in MVP

### Operations
7. **Backup Strategy**:
   - DynamoDB point-in-time recovery: Enabled
   - Conversation logs in CloudWatch: 30-day retention
   - Manual export capability: Add `/export` command for user data
   - **Decision needed**: How often to backup? Daily? On-demand only?

8. **Maintenance & Updates**:
   - Zero-downtime deployment not critical for personal use
   - Acceptable: 1-2 minute downtime during `cdk deploy`
   - Bot can send "Going offline for maintenance" message
   - **Acceptable**: Yes

9. **Rate Limiting**:
   - Current: 10 messages per minute per user
   - **Decision needed**: Is this sufficient? Too restrictive?

10. **Error Recovery**:
    - If Bedrock fails: Fallback message or retry?
    - If DynamoDB fails: Graceful degradation (no memory) or hard fail?
    - **Recommendation**: Retry 3x with exponential backoff, then friendly error message

## Success Metrics

### Technical Metrics
- Bot uptime > 99.5%
- Average response time < 5 seconds (P95 < 8 seconds)
- Error rate < 1%
- Memory retrieval accuracy (relevant results) > 90%
- Cache hit rate > 60%

### User Experience Metrics
- Context continuity: Successfully maintains conversation within 10-minute window
- Memory recall: Agent proactively mentions relevant memories
- Task completion: Reminders delivered on time (±1 minute)
- Command success rate: `/remember`, `/recall` work as expected

### Business Metrics
- Monthly cost stays under budget ($50)
- Daily active use (engagement with bot)
- Memory database growth rate (healthy usage pattern)

## Timeline & Milestones

### Phase 1: Foundation (Week 1-2)
- Set up AWS account and request Bedrock access
- Create Discord bot application
- Develop CDK infrastructure code:
  - Lambda function skeleton
  - DynamoDB table
  - ElastiCache cluster
  - IAM roles and policies
  - Secrets Manager integration
- Basic bot: Receive DM and echo response
- **Deliverable**: Bot responds to messages

### Phase 2: Bedrock Integration (Week 2-3)
- Create Bedrock agent with Nova Lite
- Define agent instruction set
- Implement agent action groups (Lambda functions):
  - Memory operations
  - Task operations
  - Context operations
- Connect Discord bot to Bedrock agent
- Test conversational flow
- **Deliverable**: Bot has AI-powered conversations

### Phase 3: Memory & Session Configuration (Week 3-4)
- Configure Bedrock Agent memory settings:
  - Enable SESSION_SUMMARY memory type
  - Set storage days (365)
- Update agent instructions for memory behavior:
  - Guidelines for what to remember
  - How to confirm memory storage with user
- Implement `/remember` command handler (explicit memory)
- Test memory persistence:
  - Short conversations (within 10 min session)
  - Long gaps (session expires, memory persists)
  - Memory recall accuracy
- **Deliverable**: Bot remembers user information automatically

### Phase 4: Advanced Features (Optional - Week 4-5)
- **Option A**: Task Management with Action Groups
  - Create DynamoDB table for tasks
  - Implement task action group Lambda functions
  - EventBridge scheduled reminders
  - Proactive reminder DMs
- **Option B**: Keep it simple
  - Rely on conversational memory for task tracking
  - No system-triggered reminders
  - User asks "what do I need to do?" to recall tasks
- **Recommendation**: Start with Option B, add A only if needed
- **Deliverable**: Conversational task tracking via memory

### Phase 5: Polish & Production (Week 4-5)
- Implement slash commands (`/remember`, `/recall`, `/status`)
- Error handling and retry logic (Bedrock failures, rate limits)
- Discord message formatting (embeds, reactions, typing indicator)
- Comprehensive logging and metrics
- CloudWatch dashboard and alarms
- Security hardening (input validation, IAM least privilege)
- Documentation (setup guide, user guide)
- **Deliverable**: Production-ready bot

### Phase 6: Monitoring & Iteration (Ongoing)
- Monitor metrics and costs (CloudWatch dashboard)
- Observe memory effectiveness (is agent remembering right things?)
- Iterate on agent instructions and prompts
- Add features based on real usage:
  - Task action groups if conversational tracking insufficient
  - Additional slash commands
  - Integration with external APIs
- Consider upgrading to more capable model if needed

## Dependencies & Prerequisites

### AWS Setup
- AWS account with admin or sufficient IAM permissions
- Bedrock access in `us-east-1` region
- Model access approval for `amazon.nova-lite-v1:0` (request via Bedrock console)
- Model access for `amazon.titan-embed-text-v1` (if using embeddings)
- AWS CLI configured with credentials
- Python 3.12+ installed locally
- AWS CDK CLI installed: `npm install -g aws-cdk`

### Discord Setup
- Discord Developer account: https://discord.com/developers
- Create new Application
- Create bot user within application
- Copy bot token (will store in Secrets Manager)
- Enable privileged intents in Bot settings:
  - Message Content Intent (required to read DM content)
- Get your Discord user ID (Developer Mode → right-click profile → Copy ID)
- Invite bot to your account (DM access)

### Development Tools
- Python 3.12+
- pip and virtualenv
- AWS CDK
- discord.py library
- boto3 (AWS SDK for Python)
- redis-py
- Git for version control

## Out of Scope (for MVP)
- Multi-user support
- Voice channel integration
- Server moderation features
- Message archival/search interface (beyond 10-minute context)
- Integration with other chat platforms (Slack, Telegram, etc.)
- Semantic/vector search (can add in Phase 6 if needed)
- Integration with external APIs (calendar, email, etc.) - Phase 7+
- Web dashboard for memory management
- Mobile app
- Image/file upload handling
- Voice message transcription

## Technical Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Discord User                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ DM Messages
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Discord Gateway                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ WebSocket Connection
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│         Python Discord Bot (Local or Fargate)                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  - discord.py client                                     │   │
│  │  - Maintains WebSocket connection                        │   │
│  │  - Validates user ID                                     │   │
│  │  - Invokes Lambda for each message                       │   │
│  │  - Sends response back to Discord                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ Lambda.invoke(payload)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              AWS Lambda (Message Processor)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. Receive message payload                              │   │
│  │  2. Call Bedrock InvokeAgent API                         │   │
│  │     - sessionId: Discord user ID                         │   │
│  │     - inputText: user message                            │   │
│  │  3. Bedrock handles:                                     │   │
│  │     - Session context (10 min)                           │   │
│  │     - Memory retrieval & storage                         │   │
│  │     - Model inference (Nova Lite)                        │   │
│  │  4. Return response to Discord bot                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ bedrock_agent_runtime.invoke_agent()
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Amazon Bedrock Agent                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────┐     │   │
│  │  │  Sessions  │  │   Memory    │  │  Nova Lite   │     │   │
│  │  │ (10 min)   │  │ (Long-term) │  │    Model     │     │   │
│  │  │            │  │             │  │              │     │   │
│  │  │ Automatic  │  │  Automatic  │  │  Inference   │     │   │
│  │  │  Context   │  │   Storage   │  │              │     │   │
│  │  │ Management │  │  & Retrieval│  │              │     │   │
│  │  └────────────┘  └─────────────┘  └──────────────┘     │   │
│  │                                                          │   │
│  │  Optional: Action Groups (Lambda functions)             │   │
│  │  - Only if structured task management needed            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Supporting Services                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Secrets    │  │  CloudWatch  │  │     IAM      │          │
│  │   Manager    │  │ Logs/Metrics │  │    Roles     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Example

### Scenario: User says "My birthday is July 15th, remember that"

1. **Discord User** sends DM message
2. **Discord Gateway** delivers event to Python bot
3. **Python Bot** (running locally):
   - Validates user ID matches authorized user
   - Calls Lambda via boto3: `lambda_client.invoke()`
   - Payload: `{"user_id": "123456789", "message": "My birthday is July 15th, remember that"}`
4. **Lambda Function** receives payload:
   - Extracts user_id and message
   - Calls Bedrock Agent Runtime API:
     ```python
     response = bedrock_agent_runtime.invoke_agent(
         agentId="AGENT_ID",
         agentAliasId="ALIAS_ID",
         sessionId="discord_user_123456789",
         inputText="My birthday is July 15th, remember that"
     )
     ```
5. **Bedrock Agent**:
   - Checks session (existing session < 10 min old? Load context)
   - Retrieves relevant memories (semantic search)
   - Nova Lite processes input with full context
   - **Automatically detects**: Important personal fact about birthday
   - **Stores in memory**: "User's birthday is July 15th"
   - Generates response: "I've remembered that your birthday is July 15th!"
6. **Lambda** returns response to Python bot
7. **Python Bot** sends message to Discord
8. **Discord User** sees: "I've remembered that your birthday is July 15th!"

### Later: User asks "When is my birthday?"

1-4. Same flow as above
5. **Bedrock Agent**:
   - Loads session context
   - **Automatically retrieves memory**: Finds "User's birthday is July 15th"
   - Nova Lite generates response using memory
   - Response: "Your birthday is July 15th!"
6-8. Same flow as above

**Key Point**: No manual memory management needed - Bedrock handles everything!

---

## Next Steps to Begin Implementation

### Immediate Actions (Do These First)

#### 1. Create Discord Bot Application
- Go to https://discord.com/developers/applications
- Click "New Application"
- Name it (e.g., "Personal Assistant")
- Go to "Bot" section → "Add Bot"
- Enable privileged intents:
  - ✅ Message Content Intent (required to read DMs)
- Copy bot token (you'll need this later)
- Go to OAuth2 → URL Generator:
  - Scopes: `bot`
  - Bot Permissions: `Send Messages`, `Read Messages/View Channels`
  - Copy generated URL and open it to invite bot to your account
- Get your Discord user ID:
  - Enable Developer Mode in Discord settings
  - Right-click your profile → Copy ID

#### 2. Request Bedrock Model Access
- Open AWS Bedrock console: https://console.aws.amazon.com/bedrock/
- Go to "Model access" (left sidebar)
- Click "Request model access"
- Find `Amazon Nova Lite` → Request access
- Approval is usually instant

#### 3. Set Up Local Development
```bash
# Create project directory
mkdir discord-bedrock-assistant
cd discord-bedrock-assistant

# Set up Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install discord.py boto3 aws-cdk-lib constructs

# Initialize CDK project
cdk init app --language python

# Install CDK dependencies
pip install -r requirements.txt
```

#### 4. Store Discord Credentials in AWS
```bash
# Store bot token
aws secretsmanager create-secret \
  --name discord-bot-token \
  --secret-string "YOUR_BOT_TOKEN_HERE" \
  --region us-east-1

# Store authorized user ID (for validation)
aws secretsmanager create-secret \
  --name discord-authorized-user \
  --secret-string "YOUR_DISCORD_USER_ID" \
  --region us-east-1
```

### Development Sequence

#### Phase 1: Infrastructure (Week 1)
1. Write CDK stack for:
   - Lambda function (message processor)
   - IAM role with Bedrock permissions
   - Secrets Manager access
2. Deploy: `cdk deploy`
3. Create Bedrock Agent in AWS console:
   - Model: Nova Lite
   - Enable memory
   - Set session TTL: 600 seconds
4. Update Lambda with agent ID/alias

#### Phase 2: Discord Bot (Week 1-2)
1. Create `discord_bot.py` (local Python app):
   - Connect to Discord Gateway
   - Validate user ID
   - Call Lambda for each message
   - Send response back to Discord
2. Test locally
3. (Optional) Containerize for Fargate deployment

#### Phase 3-6: Follow timeline in PRD

### Quick Start Commands
```bash
# Deploy infrastructure
cdk deploy

# Run Discord bot locally (after CDK deploy)
python discord_bot.py

# View logs
aws logs tail /aws/lambda/process-discord-message --follow

# Check costs
aws ce get-cost-and-usage --time-period Start=2026-06-01,End=2026-06-30 \
  --granularity MONTHLY --metrics BlendedCost
```

### Architecture Decisions Made ✅
Based on your feedback:
- ✅ **Compute**: Lambda for message processing
- ✅ **Memory**: Bedrock Memory (automatic + manual)
- ✅ **Sessions**: Bedrock Sessions (10-minute context)
- ✅ **Connection**: Discord Gateway (WebSocket) via local Python app
- ✅ **Cost**: ~$7-17/month (very affordable!)

### Remaining Decisions
1. **Discord Bot Hosting**:
   - **Option A (Recommended)**: Run Python bot on your local machine
     - Pros: Free, simple setup, easy debugging
     - Cons: Must keep computer on, bot offline when computer off
   - **Option B**: Run Python bot on ECS Fargate
     - Pros: Always on, no local dependency
     - Cons: +$5-10/month, slightly more complex setup
   - **Your choice**: ?

2. **Task Management**:
   - **Option A**: Conversational only (agent remembers via memory)
   - **Option B**: Structured with action groups + EventBridge reminders
   - **Recommendation**: Start with A, upgrade to B if needed
   - **Your choice**: ?

3. **Memory Confirmation**:
   - Should agent ask "Should I remember that [X]?" or silently store?
   - **Recommendation**: Silent storage, user can say "forget that" if unwanted
   - **Your choice**: ?
