import nextra from 'nextra'

const withNextra = nextra({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.jsx',
  defaultShowCopyCode: true,
  codeHighlight: true
})

export default withNextra({
  images: {
    unoptimized: true,
  },
  assetPrefix: '/agentvectordb/',
  basePath: '/agentvectordb',
  output: 'export',
  reactStrictMode: true,
})
