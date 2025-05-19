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
  assetPrefix: process.env.NODE_ENV === 'production' ? '/' : '',
  basePath: '',
  reactStrictMode: true,
  staticFileDirectories: ['static'],
})
