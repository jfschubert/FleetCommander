// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    'intro',
    {
      type: 'category',
      label: 'Getting started',
      collapsed: false,
      items: ['installation', 'quick-start'],
    },
    {
      type: 'category',
      label: 'Using FleetCommander',
      collapsed: false,
      items: ['web-ui', 'auto-placement', 'hotkeys-appearance', 'previews', 'window-zones'],
    },
    {
      type: 'category',
      label: 'Reference',
      collapsed: false,
      items: ['configuration', 'troubleshooting', 'development', 'translations', 'legal'],
    },
  ],
};

export default sidebars;
