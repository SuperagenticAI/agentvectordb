export default {
  logo: <span>AgentVectorDB 🧠</span>,
  project: {
    link: 'https://github.com/yourusername/agentvectordb'
  },
  docsRepositoryBase: 'https://github.com/yourusername/agentvectordb/tree/main/docs',
  useNextSeoProps() {
    return {
      titleTemplate: '%s – AgentVectorDB'
    }
  },
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="AgentVectorDB: The Cognitive Core for Your AI Agents" />
      <meta property="og:description" content="A lightweight, embeddable vector database for Agentic AI systems" />
    </>
  )
}
