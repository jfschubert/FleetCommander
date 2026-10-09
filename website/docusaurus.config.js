// @ts-check
// FleetCommander documentation – Docusaurus 3.
//
// url/baseUrl default to GitHub Pages (https://jfschubert.github.io/FleetCommander/).
// Override for other hosts (e.g. GitLab Pages) with DOCS_URL and DOCS_BASE_URL:
//   DOCS_URL=https://group.gitlab.io DOCS_BASE_URL=/project/ npm run build
import {themes as prismThemes} from 'prism-react-renderer';

const REPO = 'https://github.com/jfschubert/FleetCommander';

function normalizeBaseUrl(value) {
  let b = value || '/FleetCommander/';
  if (!b.startsWith('/')) b = '/' + b;
  if (!b.endsWith('/')) b += '/';
  return b;
}

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'FleetCommander',
  tagline: 'Arrange EVE Online clients on KDE Plasma',
  favicon: 'img/logo.svg',

  url: (process.env.DOCS_URL || 'https://jfschubert.github.io').replace(/\/+$/, ''),
  baseUrl: normalizeBaseUrl(process.env.DOCS_BASE_URL),

  organizationName: 'jfschubert',
  projectName: 'FleetCommander',
  trailingSlash: true,

  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',

  markdown: {
    format: 'detect',
    hooks: {onBrokenMarkdownLinks: 'throw'},
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'de'],
    localeConfigs: {
      en: {label: 'English', htmlLang: 'en'},
      de: {label: 'Deutsch', htmlLang: 'de'},
    },
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: '/',
          sidebarPath: './sidebars.js',
          editUrl: `${REPO}/edit/main/website/`,
        },
        blog: false,
        theme: {customCss: './src/css/custom.css'},
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {respectPrefersColorScheme: true},
      navbar: {
        title: 'FleetCommander',
        logo: {alt: 'FleetCommander', src: 'img/logo.svg'},
        items: [
          {type: 'docSidebar', sidebarId: 'docs', position: 'left', label: 'Documentation'},
          {type: 'localeDropdown', position: 'right'},
          {href: REPO, label: 'GitHub', position: 'right'},
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {label: 'Installation', to: '/installation'},
              {label: 'Configuration', to: '/configuration'},
              {label: 'Troubleshooting', to: '/troubleshooting'},
            ],
          },
          {
            title: 'Project',
            items: [
              {label: 'Source code', href: REPO},
              {label: 'Issues', href: `${REPO}/issues`},
            ],
          },
        ],
        copyright: `FleetCommander is licensed under GPL-3.0. EVE Online® and Fenris Creations™ are trademarks of Fenris Creations (formerly CCP Games); this project is not affiliated with or endorsed by Fenris Creations.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['bash', 'yaml', 'json'],
      },
    }),
};

export default config;
