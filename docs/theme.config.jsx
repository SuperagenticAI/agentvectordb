export default {
  logo: <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
    <span style={{ fontSize: '24px' }}>🧠</span> 
    <span style={{ fontWeight: 'bold' }}>AgentVectorDB</span>
  </span>,
  project: {
    link: 'https://github.com/superagenticai/agentvectordb'
  },
  docsRepositoryBase: 'https://github.com/superagenticai/agentvectordb/tree/main/docs/pages',
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
  ),
  sidebar: {
    defaultMenuCollapseLevel: 1,
    toggleButton: true
  },
  footer: {
    text: (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center' }}>
        <span>Powered by AgentVectorDB © {new Date().getFullYear()}</span>
        <a href="https://github.com/superagenticai/agentvectordb" target="_blank" rel="noopener">
          <span style={{ fontSize: '20px' }}>⭐️</span>
        </a>
      </div>
    )
  },
  darkMode: true,
  nextThemes: {
    defaultTheme: 'dark'
  },
  feedback: {
    content: null
  },
  editLink: {
    text: 'Edit this page on GitHub →'
  }
}
