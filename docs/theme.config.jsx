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
    themeSwitch: false,
    feedback: false,
    sidebar: false
  },

  head: () => (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="AgentVectorDB: The Cognitive Core for Your AI Agents" />
      <meta property="og:description" content="A lightweight, embeddable vector database for Agentic AI systems" />
      <style>
        {`
          /* High-contrast dark theme */
          :root, html, body, #__next, main, footer {
            background-color: #000000 !important;
            color: #ffffff !important;
          }
          
          /* Links */
          a {
            color:rgb(140, 153, 68) !important;
            text-decoration: none !important;
          }
          a:hover {
            color: #0052cc !important;
            text-decoration: underline !important;
          }
          
          /* Code blocks */
          .dark .nextra-code-block pre {
            background-color:rgb(2, 0, 0) !important;
            margin: 1rem 0;
            padding: 1.5rem;
            border-radius: 0.375rem;
            border: 1px solid #333333 !important;
          }
          
          /* Code syntax highlighting */
          .dark .nextra-code-block .token.comment,
          .dark .nextra-code-block .token.prolog,
          .dark .nextra-code-block .token.doctype,
          .dark .nextra-code-block .token.cdata {
            color: #8e908c !important;
          }
          
          .dark .nextra-code-block .token.property,
          .dark .nextra-code-block .token.tag,
          .dark .nextra-code-block .token.constant,
          .dark .nextra-code-block .token.symbol,
          .dark .nextra-code-block .token.deleted {
            color: #e74c3c !important;
          }
          
          .dark .nextra-code-block .token.boolean,
          .dark .nextra-code-block .token.number {
            color: #3598db !important;
          }
          
          .dark .nextra-code-block .token.selector,
          .dark .nextra-code-block .token.attr-name,
          .dark .nextra-code-block .token.string,
          .dark .nextra-code-block .token.char,
          .dark .nextra-code-block .token.builtin,
          .dark .nextra-code-block .token.inserted {
            color: #2ecc71 !important;
          }
          
          .dark .nextra-code-block .token.operator,
          .dark .nextra-code-block .token.entity,
          .dark .nextra-code-block .token.url,
          .dark .nextra-code-block .language-css .token.string,
          .dark .nextra-code-block .style .token.string {
            color: #e74c3c !important;
          }
          
          .dark .nextra-code-block .token.atrule,
          .dark .nextra-code-block .token.attr-value,
          .dark .nextra-code-block .token.keyword {
            color: #3498db !important;
          }
          
          .dark .nextra-code-block .token.regex,
          .dark .nextra-code-block .token.important,
          .dark .nextra-code-block .token.variable {
            color: #f1c40f !important;
          }
          
          .dark .nextra-code-block .token.important,
          .dark .nextra-code-block .token.bold {
            font-weight: bold !important;
          }
          
          .dark .nextra-code-block .token.italic {
            font-style: italic !important;
          }
          
          .dark .nextra-code-block .token.entity {
            cursor: help !important;
          }
          
          /* Highlighted lines */
          .dark .nextra-code-block .line.highlighted {
            background-color: #1a1a1a !important;
            border-left: 2px solid #0070f3 !important;
          }
          
          /* Dark shadow elements */
          [class~=dark] .dark\:nx-shadow,
          [class~=dark] .dark\:nx-shadow-lg,
          [class~=dark] .dark\:nx-shadow-md,
          [class~=dark] .dark\:nx-shadow-sm,
          [class~=dark] .dark\:nx-shadow-xl {
            background-color: #000000 !important;
            box-shadow: none !important;
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
          
       
   
          
          /* Cards and containers */
          .dark .nextra-card,
          .dark .license-box,
          .dark .feature-card,
          .dark .installation-option,
          .dark .quick-start {
            background-color: #1a1a1a !important;
            border: 1px solid #333333 !important;
          }
          
          /* Tables */
          .dark table {
            background-color: #1a1a1a !important;
            border: 1px solid #333333 !important;
          }
          
          /* Scrollbar */
          .dark ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
          }
          
          .dark ::-webkit-scrollbar-track {
            background: #1a1a1a;
          }
          
          .dark ::-webkit-scrollbar-thumb {
            background: #333333;
            border-radius: 4px;
          }
          
          .dark ::-webkit-scrollbar-thumb:hover {
            background: #4d4d4d;
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