export default {
  logo: <span>🧠 AgentVectorDB Docs</span>,
  project: {
    link: 'https://github.com/superagenticai/agentvectordb'
  },
  docsRepositoryBase: 'https://github.com/superagenticai/agentvectordb/tree/main/docs/pages',
  footer: {
    text: 'AgentVectorDB Docs © ' + new Date().getFullYear()
  },
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
