# This is a guide to learn essentials for AI agents development in langchain.

## Composition
Every agent is made up of following components:
1 - LLM
2 - Tools
3 - Memory/Checkpoint
4 - System prompt
5 - output schemas
6 - Knowledge base and Retriever


### LLM

Language model is the core component of an agent. It is responsible for generating an specific schema based on the given prompt & system prompt. It can be any language model like gpt-5, claude, gemini etc. In langchain you can use any of the supported language models like this.

```python
llm = ChatOllama(model="gpt-5")
```

In JS it looks like this:

```javascript
const llm = new ChatOllama({
  model: "gpt-5",
});
```

Note: In the above example we are using ollama as the llm provider, you can use any other provider like openai, anthropic, google etc. Just make sure to import the correct class and provide the necessary credentials.

### Tools

Tools are the functions that the agent can call to perform specific tasks like searching the web, sending an email, making a call etc. They are defined as python functions or JS functions and can be called by the agent when needed. In langchain you can define tools like this.

```python

def search_web(query: str) -> str:
    # code to search the web and return the results
    return "search results for " + query

def send_email(to: str, subject: str, body: str) -> str:
    # code to send an email and return the status
    return "email sent to " + to + " with subject " + subject

search_web_tool = Tool(
    name="search",
    description="Search the web for information",
    func=search
)
send_email_tool = Tool(
    name="send_email",
    description="Send an email to a contact",
    func=send_email
)
```

In JS it looks like this:

```javascript
function searchWeb(query) {
  // code to search the web and return the results
  return "search results for " + query;
}

function sendEmail(to, subject, body) {
  // code to send an email and return the status
  return "email sent to " + to + " with subject " + subject;
}

const searchWebTool = new Tool({
  name: "search",
  description: "Search the web for information",
  func: searchWeb,
});

const sendEmailTool = new Tool({
  name: "send_email",
  description: "Send an email to a contact",
  func: sendEmail,
});
```

### Memory/Checkpoint

This is the component that allows the agent to remember the previous interactions to make better decisions in the future. It implements a memory mechanism using `MemorySaver` and it looks like this in python:

```python
memory = MemorySaver() # We later pass this memory to the agent
```
In JS it looks like this:

```javascript
const memory = new MemorySaver(); // We later pass this memory to the agent
```

### System prompt

The system prompt is a set of instructions that guides the behavior of the language model. It helps the agent understand its role and how to interact with the user.

In langchain you can define a system prompt like this:

```python
system_prompt = system_prompt.format(format_instructions=parser.get_format_instructions()) # We can use the format instructions from the output schema to guide the llm to generate the output in the desired format. The parser can be the pydantic parser for any output schema, e.g parser = PydanticOutputParser(pydantic_object=LeadResponseList)
```

In JS it looks like this:

```javascript
const systemPrompt = systemPrompt.format({
  format_instructions: parser.getFormatInstructions(), // We can use the format instructions from the output schema to guide the llm to generate the output in the desired format. The parser can be the zod parser for any output schema, e.g const parser = new ZodOutputParser({ zodSchema: LeadResponseList })
});
```

### Output schemas

Output schemas are the pydantic classes that define the structure of the output that the agent will produce. In JS these are defined using zod. They look like this in python:

```python
class LeadResponse(BaseModel):
    company: str
    contact_info: str
    email: str
    summary: str
    outreach_message: str
    tools_used: list[str]

class LeadResponseList(BaseModel):
    leads: list[LeadResponse]
```

In JS they look like this:

```javascript
const LeadResponse = z.object({
  company: z.string(),
  contact_info: z.string(),
  email: z.string(),
  summary: z.string(),
  outreach_message: z.string(),
  tools_used: z.array(z.string()),
});

const LeadResponseList = z.object({
  leads: z.array(LeadResponse),
});
```

### Knowledge base and Retriever

The knowledge base is a collection of information that the agent can use to make informed decisions. It can be a database, a file (md, txt, csv etc.) or any other source of information. The agent can query the knowledge base to get relevant information when needed. It can be a vector database like chroma, weaviate, pinecone etc in most cases. we can retrieve information from the knowledge base using a retriever. The retriever is responsible for fetching relevant information from the knowledge base based on the query provided by the agent. The agent that has works with a knowledge base and retrieve information from it is called a `RAG agent` (Retrieval Augmented Generation agent). In langchain you can define a knowledge base and retriever like this:

```python
# Load and split documents
loader = TextLoader("knowledge_base.txt")
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# Create vector store and retriever tool
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

@tool
def search_kb(query: str) -> str:
    """Search the knowledge base for relevant information."""
    docs = vectorstore.similarity_search(query, k=3)
    return "\n\n".join(doc.page_content for doc in docs)
```
In JS it looks like this:

```javascript
// Load and split documents
const loader = new TextLoader("knowledge_base.txt");
const docs = await loader.load();
const splitter = new RecursiveCharacterTextSplitter({ chunkSize: 500, chunkOverlap: 50 });
const chunks = await splitter.splitDocuments(docs);
// Create vector store and retriever tool
const embeddings = new OpenAIEmbeddings();
const vectorstore = await Chroma.fromDocuments(chunks, embeddings);
function searchKB(query) {
  // Search the knowledge base for relevant information.
  const docs = vectorstore.similaritySearch(query, 3);
  return docs.map((doc) => doc.pageContent).join("\n\n");
}
```



