export default {
  logo: <span>AgentVector 🧠</span>,
  project: {
    link: 'https://github.com/yourusername/agentvector'
  },
  docsRepositoryBase: 'https://github.com/yourusername/agentvector/tree/main/docs',
  useNextSeoProps() {
    return {
      titleTemplate: '%s – AgentVector'
    }
  },
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="AgentVector: The Cognitive Core for Your AI Agents" />
      <meta property="og:description" content="A lightweight, embeddable vector database for Agentic AI systems" />
    </>
  )
}