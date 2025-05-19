const config = {
  logo: <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
    <span style={{ fontSize: '24px' }}>🧠</span> 
    <span style={{ fontWeight: 'bold' }}>AgentVectorDB</span>
  </span>,
  project: {
    link: 'https://github.com/superagenticai/agentvectordb'
  },
  docsRepositoryBase: 'https://github.com/superagenticai/agentvectordb/tree/main/docs/pages',
  primaryHue: { dark: 200 },
  nextThemes: {
    defaultTheme: 'dark',
    forcedTheme: 'dark'
  },

  head: () => (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="AgentVectorDB: The Cognitive Core for Your AI Agents" />
      <meta property="og:description" content="A lightweight, embeddable vector database for Agentic AI systems" />
      <style>
        {`
          /* Force black background on all elements */
          :root, html, body, #__next, main, .dark, 
          .dark .nx-bg-white,
          .dark .nx-bg-neutral-50,
          .dark .nx-bg-neutral-100,
          .dark .nx-bg-gray-100,
          .dark .dark\:nx-bg-neutral-900,
          .dark .dark\:nx-bg-dark,
          .dark nav.nextra-nav-container,
          .dark footer.nx-bg-neutral-100,
          .dark header.nx-bg-white,
          .dark .nextra-sidebar-container,
          .dark .nextra-nav-container-blur,
          .dark .nextra-nav-container-blur::before,
          .dark .nextra-nav-container-blur::after,
          .dark .nx-sticky.nx-top-0,
          .dark .nx-sticky-nav,
          .dark aside.nextra-sidebar,
          .dark .nextra-scrollbar,
          .dark .nx-absolute.nx-top-0 {
            background-color: #000000 !important;
            border-color: #000000 !important;
          }

          /* Remove any blur effects */
          .dark .nextra-nav-container-blur::before,
          .dark .nextra-nav-container-blur::after {
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
          }

          /* Remove borders and shadows */
          .dark *,
          .dark .nx-shadow-lg,
          .dark .nx-border,
          .dark .nx-border-b,
          .dark .nx-border-t,
          .dark [class*='nx-border'] {
            border-color: #000000 !important;
            box-shadow: none !important;
          }

          /* Code block styling */
          .dark .nextra-code-block pre {
            background-color: #0a0a0a !important;
            margin: 1rem 0;
            padding: 1.5rem;
            border-radius: 0.375rem;
          }

          .dark .line.highlighted {
            background-color: #1a1a1a !important;
            border-left: 2px solid #0070f3 !important;
          }

          /* Force black on hover states */
          .dark *:hover {
            background-color: #000000 !important;
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
          <span style={{ fontSize: '20px' }}>⭐️</span>
        </a>
      </div>
    )
  }
}

export default config