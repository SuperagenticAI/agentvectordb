import nextra from 'nextra'

const withNextra = require('nextra')({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.jsx',
  defaultShowCopyCode: true,
  codeHighlight: true
})

module.exports = withNextra()

