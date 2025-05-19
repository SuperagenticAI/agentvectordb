const config = {
  logo: <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
    <span style={{ fontSize: '24px' }}>🧠</span> 
    <span style={{ fontWeight: 'bold' }}>AgentVectorDB</span>
  </span>,
  project: {
    link: 'https://github.com/superagenticai/agentvectordb'
  },
  docsRepositoryBase: 'https://github.com/superagenticai/agentvectordb/tree/main/docs/pages',
  theme: {
    default: 'dark',
    forced: 'dark'
  },
  docs: {
    editLink: false,
    themeSwitch: false
  },

  head: () => (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="AgentVectorDB: The Cognitive Core for Your AI Agents" />
      <meta property="og:description" content="A lightweight, embeddable vector database for Agentic AI systems" />
      <style>
        {`
          /* Dark theme styling */
          :root, html, body, #__next, main {
            background-color: #000000 !important;
            color: #ffffff !important;
          }
          
          /* Code blocks */
          .dark .nextra-code-block pre {
            background-color:rgb(2, 0, 0) !important;
            margin: 1rem 0;
            padding: 1.5rem;
            border-radius: 0.375rem;
          }

          .dark .line.highlighted {
            background-color: #1a1a1a !important;
            border-left: 2px solid #0070f3 !important;
          }
        `}
      </style>
    </>
  ),
  footer: {
    text: (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center' }}>
        <span>AgentVectorDB by Superagentic AI © {new Date().getFullYear()}</span>
        <a href="https://github.com/superagenticai/agentvectordb" target="_blank" rel="noopener">
          <span style={{ fontSize: '10px' }}>⭐️</span>
        </a>
      </div>
    )
  }
}

export default config